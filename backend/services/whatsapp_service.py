from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, time

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, NotFoundError
from backend.models.case import Case
from backend.models.whatsapp import WhatsAppData, WhatsAppImport, WhatsAppMessage
from backend.modules.d5_whatsapp.import_paths import normalize_account, resolve_msgstore_paths
from backend.modules.d5_whatsapp.msgstore_parser import parse_msgstore
from backend.modules.d5_whatsapp.profile_analyzer import analyze_conversation_messages
from backend.modules.d5_whatsapp.search_engine import build_snippet
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d6_operations.case_guards import ensure_case_open
from backend.schemas.whatsapp import (
    ActiveGroupStat,
    CommunicationPatterns,
    DominantContactStat,
    WhatsAppConversationResponse,
    WhatsAppImportRequest,
    WhatsAppImportResponse,
    WhatsAppMessageResponse,
    WhatsAppProfileSummaryResponse,
    WhatsAppSearchHit,
    WhatsAppSearchResponse,
)


class WhatsAppService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def start_import(
        self,
        payload: WhatsAppImportRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> WhatsAppImportResponse:
        case = self.db.get(Case, payload.case_id)
        if not case:
            raise AppError("invalid_case", "Case not found", status_code=422)
        ensure_case_open(case, action="import WhatsApp data")

        account = normalize_account(payload.account)
        # Validate path early so API fails fast before creating a job row.
        resolve_msgstore_paths(
            device_id=payload.device_id,
            account=account,
            source_path=payload.source_path,
        )

        import_job = WhatsAppImport(
            case_id=payload.case_id,
            device_id=payload.device_id,
            account=account,
            source_path=payload.source_path,
            status="queued",
        )
        self.db.add(import_job)
        self.db.flush()
        log_activity(
            self.db,
            user_id=user_id,
            action="whatsapp.import.queued",
            entity_type="whatsapp_import",
            entity_id=import_job.id,
            details={
                "case_id": str(payload.case_id),
                "device_id": payload.device_id,
                "account": account,
            },
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(import_job)

        # Wave 1: process synchronously (Celery worker still empty).
        return self._process_import(import_job.id, user_id=user_id, ip_address=ip_address)

    def get_import(self, import_id: uuid.UUID) -> WhatsAppImportResponse:
        job = self.db.get(WhatsAppImport, import_id)
        if not job:
            raise NotFoundError("WhatsApp import job not found")
        return self._to_response(job)

    def list_conversations(
        self,
        *,
        case_id: uuid.UUID | None = None,
        contact: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        keyword: str | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[WhatsAppConversationResponse]]:
        query = select(WhatsAppData)
        if case_id is not None:
            query = query.where(WhatsAppData.case_id == case_id)
        if contact:
            pattern = f"%{contact.strip()}%"
            query = query.where(
                or_(
                    WhatsAppData.contact.ilike(pattern),
                    WhatsAppData.group_name.ilike(pattern),
                    WhatsAppData.wa_chat_jid.ilike(pattern),
                )
            )
        if start_date is not None:
            query = query.where(
                WhatsAppData.last_message_date >= datetime.combine(start_date, time.min, tzinfo=UTC)
            )
        if end_date is not None:
            query = query.where(
                WhatsAppData.first_message_date
                <= datetime.combine(end_date, time.max, tzinfo=UTC)
            )
        if keyword:
            pattern = f"%{keyword.strip()}%"
            matching_ids = (
                select(WhatsAppMessage.conversation_record_id)
                .where(WhatsAppMessage.content.ilike(pattern))
                .distinct()
            )
            query = query.where(
                or_(
                    WhatsAppData.id.in_(matching_ids),
                    WhatsAppData.contact.ilike(pattern),
                    WhatsAppData.group_name.ilike(pattern),
                    WhatsAppData.wa_chat_jid.ilike(pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(
                    WhatsAppData.last_message_date.desc(),
                    WhatsAppData.created_at.desc(),
                )
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        return total, page, limit, [self._conversation_response(item) for item in items]

    def list_messages(
        self,
        conversation_id: uuid.UUID,
        *,
        keyword: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[WhatsAppMessageResponse]]:
        conversation = self.db.get(WhatsAppData, conversation_id)
        if not conversation:
            raise NotFoundError("WhatsApp conversation not found")

        query = select(WhatsAppMessage).where(
            WhatsAppMessage.conversation_record_id == conversation_id
        )
        if keyword:
            query = query.where(WhatsAppMessage.content.ilike(f"%{keyword.strip()}%"))
        if start_date is not None:
            query = query.where(
                WhatsAppMessage.timestamp >= datetime.combine(start_date, time.min, tzinfo=UTC)
            )
        if end_date is not None:
            query = query.where(
                WhatsAppMessage.timestamp <= datetime.combine(end_date, time.max, tzinfo=UTC)
            )

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0
        items = list(
            self.db.scalars(
                query.order_by(WhatsAppMessage.timestamp.asc(), WhatsAppMessage.created_at.asc())
                .offset((page - 1) * limit)
                .limit(limit)
            )
        )
        return total, page, limit, [self._message_response(item) for item in items]

    def search_messages(
        self,
        *,
        q: str,
        contact: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        content_type: str | None = None,
        case_id: uuid.UUID | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> WhatsAppSearchResponse:
        query_text = q.strip()
        if not query_text:
            raise AppError("validation_error", "Query parameter q is required", status_code=422)

        query = (
            select(WhatsAppMessage, WhatsAppData)
            .join(WhatsAppData, WhatsAppMessage.conversation_record_id == WhatsAppData.id)
            .where(WhatsAppMessage.content.ilike(f"%{query_text}%"))
        )
        if case_id is not None:
            query = query.where(WhatsAppData.case_id == case_id)
        if contact:
            pattern = f"%{contact.strip()}%"
            query = query.where(
                or_(
                    WhatsAppData.contact.ilike(pattern),
                    WhatsAppData.group_name.ilike(pattern),
                    WhatsAppData.wa_chat_jid.ilike(pattern),
                    WhatsAppMessage.sender.ilike(pattern),
                )
            )
        if start_date is not None:
            query = query.where(
                WhatsAppMessage.timestamp >= datetime.combine(start_date, time.min, tzinfo=UTC)
            )
        if end_date is not None:
            query = query.where(
                WhatsAppMessage.timestamp <= datetime.combine(end_date, time.max, tzinfo=UTC)
            )
        if content_type:
            query = query.where(WhatsAppMessage.content_type == content_type.strip().lower())

        count_query = select(func.count()).select_from(query.subquery())
        total = self.db.scalar(count_query) or 0
        rows = list(
            self.db.execute(
                query.order_by(WhatsAppMessage.timestamp.desc(), WhatsAppMessage.created_at.desc())
                .offset((page - 1) * limit)
                .limit(limit)
            ).all()
        )
        hits = [
            WhatsAppSearchHit(
                id=message.id,
                conversation_id=message.conversation_record_id,
                timestamp=message.timestamp,
                sender=message.sender,
                content=message.content,
                snippet=build_snippet(message.content, query_text),
                content_type=message.content_type,
            )
            for message, _conversation in rows
        ]
        return WhatsAppSearchResponse(
            total=total,
            query=query_text,
            page=page,
            limit=limit,
            data=hits,
        )

    def get_profile_summary(self, conversation_id: uuid.UUID) -> WhatsAppProfileSummaryResponse:
        conversation = self.db.get(WhatsAppData, conversation_id)
        if not conversation:
            raise NotFoundError("WhatsApp conversation not found")

        messages = list(
            self.db.scalars(
                select(WhatsAppMessage)
                .where(WhatsAppMessage.conversation_record_id == conversation_id)
                .order_by(WhatsAppMessage.timestamp.asc())
            )
        )
        summary = analyze_conversation_messages(
            messages=[(item.timestamp, item.sender) for item in messages],
            group_name=conversation.group_name,
        )
        return WhatsAppProfileSummaryResponse(
            conversation_id=conversation_id,
            dominant_contacts=[
                DominantContactStat(
                    contact=item.contact,
                    message_count=item.message_count,
                    interaction_frequency=item.interaction_frequency,
                )
                for item in summary.dominant_contacts
            ],
            active_groups=[
                ActiveGroupStat(
                    group_name=item.group_name,
                    message_count=item.message_count,
                    member_count=item.member_count,
                )
                for item in summary.active_groups
            ],
            communication_patterns=CommunicationPatterns(
                peak_hours=summary.communication_patterns.peak_hours,
                average_messages_per_day=summary.communication_patterns.average_messages_per_day,
                most_active_day=summary.communication_patterns.most_active_day,
            ),
        )

    def _process_import(
        self,
        import_id: uuid.UUID,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> WhatsAppImportResponse:
        job = self.db.get(WhatsAppImport, import_id)
        if not job:
            raise NotFoundError("WhatsApp import job not found")

        job.status = "processing"
        self.db.commit()

        try:
            msgstore_path, contacts_path = resolve_msgstore_paths(
                device_id=job.device_id,
                account=job.account,
                source_path=job.source_path,
            )
            conversations = parse_msgstore(msgstore_path, contacts_path)
            conversations_imported, messages_imported = self._persist_conversations(
                case_id=job.case_id,
                conversations=conversations,
            )
            job.status = "completed"
            job.conversations_imported = conversations_imported
            job.messages_imported = messages_imported
            job.error_message = None
            job.completed_at = datetime.now(UTC)
            log_activity(
                self.db,
                user_id=user_id,
                action="whatsapp.import.completed",
                entity_type="whatsapp_import",
                entity_id=job.id,
                details={
                    "case_id": str(job.case_id),
                    "device_id": job.device_id,
                    "account": job.account,
                    "conversations_imported": conversations_imported,
                    "messages_imported": messages_imported,
                    "msgstore_path": str(msgstore_path),
                },
                ip_address=ip_address,
            )
            self.db.commit()
        except Exception as exc:
            self.db.rollback()
            job = self.db.get(WhatsAppImport, import_id)
            if job:
                job.status = "failed"
                job.error_message = str(exc)
                job.completed_at = datetime.now(UTC)
                log_activity(
                    self.db,
                    user_id=user_id,
                    action="whatsapp.import.failed",
                    entity_type="whatsapp_import",
                    entity_id=job.id,
                    details={"error": str(exc)},
                    ip_address=ip_address,
                )
                self.db.commit()
                return self._to_response(job)
            raise

        self.db.refresh(job)
        return self._to_response(job)

    def _persist_conversations(
        self,
        *,
        case_id: uuid.UUID,
        conversations,
    ) -> tuple[int, int]:
        conversations_imported = 0
        messages_imported = 0

        for conversation in conversations:
            if conversation.message_count == 0:
                continue

            existing = self.db.scalar(
                select(WhatsAppData).where(
                    WhatsAppData.case_id == case_id,
                    WhatsAppData.wa_chat_jid == conversation.wa_chat_jid,
                )
            )
            if existing:
                # Replace messages for re-import of the same chat.
                for message in list(existing.messages):
                    self.db.delete(message)
                self.db.flush()
                record = existing
                record.contact = conversation.contact
                record.group_name = conversation.group_name
            else:
                record = WhatsAppData(
                    case_id=case_id,
                    wa_chat_jid=conversation.wa_chat_jid,
                    contact=conversation.contact,
                    group_name=conversation.group_name,
                )
                self.db.add(record)
                self.db.flush()

            for message in conversation.messages:
                self.db.add(
                    WhatsAppMessage(
                        conversation_record_id=record.id,
                        timestamp=message.timestamp,
                        sender=message.sender,
                        receiver=message.receiver,
                        content=message.content,
                        content_type=message.content_type,
                    )
                )
                messages_imported += 1

            record.message_count = conversation.message_count
            record.first_message_date = conversation.first_message_date
            record.last_message_date = conversation.last_message_date
            conversations_imported += 1

        self.db.flush()
        return conversations_imported, messages_imported

    @staticmethod
    def _to_response(job: WhatsAppImport) -> WhatsAppImportResponse:
        return WhatsAppImportResponse(
            import_id=job.id,
            status=job.status,  # type: ignore[arg-type]
            case_id=job.case_id,
            device_id=job.device_id,
            account=job.account,
            conversations_imported=job.conversations_imported,
            messages_imported=job.messages_imported,
            error_message=job.error_message,
            created_at=job.created_at,
            completed_at=job.completed_at,
        )

    @staticmethod
    def _conversation_response(item: WhatsAppData) -> WhatsAppConversationResponse:
        return WhatsAppConversationResponse(
            id=item.id,
            case_id=item.case_id,
            contact=item.contact,
            message_count=item.message_count,
            first_message_date=item.first_message_date,
            last_message_date=item.last_message_date,
            group_name=item.group_name,
            wa_chat_jid=item.wa_chat_jid,
        )

    @staticmethod
    def _message_response(item: WhatsAppMessage) -> WhatsAppMessageResponse:
        return WhatsAppMessageResponse(
            id=item.id,
            conversation_id=item.conversation_record_id,
            timestamp=item.timestamp,
            sender=item.sender,
            receiver=item.receiver,
            content=item.content,
            content_type=item.content_type,
        )

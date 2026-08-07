import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError
from backend.models.audit_log import AuditLog
from backend.models.case import Case
from backend.models.custody import CustodyLog
from backend.models.evidence import Evidence
from backend.models.intelligence import ApkAnalysis, Document, NerEntity
from backend.models.whatsapp import WhatsAppData, WhatsAppMessage
from backend.modules.d6_operations.audit import log_activity
from backend.schemas.intelligence import (
    CaseAnalyzeRequest,
    CaseAnalyzeResponse,
    CaseIntegrationResponse,
    CaseModuleCounts,
    CorrelationResultItem,
    GraphRequest,
    NerRequest,
)
from backend.services.intelligence_service import IntelligenceService


class IntegrationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.intelligence = IntelligenceService(db)

    def get_case_integration(self, case_id: uuid.UUID) -> CaseIntegrationResponse:
        case = self.db.get(Case, case_id)
        if not case:
            raise AppError("not_found", "Case not found", status_code=404)

        whatsapp_conversations = (
            self.db.scalar(
                select(func.count()).select_from(WhatsAppData).where(WhatsAppData.case_id == case_id)
            )
            or 0
        )
        whatsapp_messages = (
            self.db.scalar(
                select(func.count())
                .select_from(WhatsAppMessage)
                .join(WhatsAppData, WhatsAppMessage.conversation_record_id == WhatsAppData.id)
                .where(WhatsAppData.case_id == case_id)
            )
            or 0
        )
        evidence_items = (
            self.db.scalar(select(func.count()).select_from(Evidence).where(Evidence.case_id == case_id))
            or 0
        )
        documents_analyzed = (
            self.db.scalar(select(func.count()).select_from(Document).where(Document.case_id == case_id))
            or 0
        )
        ner_entities = (
            self.db.scalar(
                select(func.count())
                .select_from(NerEntity)
                .join(Document, NerEntity.document_id == Document.id)
                .where(Document.case_id == case_id)
            )
            or 0
        )
        apk_analyses = (
            self.db.scalar(
                select(func.count())
                .select_from(ApkAnalysis)
                .join(Document, ApkAnalysis.document_id == Document.id)
                .where(Document.case_id == case_id)
            )
            or 0
        )
        custody_entries = (
            self.db.scalar(
                select(func.count())
                .select_from(CustodyLog)
                .join(Evidence, CustodyLog.evidence_id == Evidence.id)
                .where(Evidence.case_id == case_id)
            )
            or 0
        )
        graph_analyses = (
            self.db.scalar(
                select(func.count())
                .select_from(AuditLog)
                .where(
                    AuditLog.entity_type == "case",
                    AuditLog.entity_id == case_id,
                    AuditLog.action == "case.intelligence.graph",
                )
            )
            or 0
        )

        intelligence_ready = whatsapp_conversations > 0 or documents_analyzed > 0
        reports_available = ["case_pdf"]
        if evidence_items > 0:
            reports_available.append("bast_pdf")

        latest_correlations = self._latest_case_correlations(case_id)

        return CaseIntegrationResponse(
            case_id=case.id,
            title=case.title,
            status=case.status,
            priority=case.priority,
            modules=CaseModuleCounts(
                whatsapp_conversations=whatsapp_conversations,
                whatsapp_messages=whatsapp_messages,
                evidence_items=evidence_items,
                documents_analyzed=documents_analyzed,
                ner_entities=ner_entities,
                graph_analyses=graph_analyses,
                apk_analyses=apk_analyses,
                custody_entries=custody_entries,
            ),
            intelligence_ready=intelligence_ready,
            reports_available=reports_available,
            latest_correlations=latest_correlations,
        )

    def run_case_analysis(
        self,
        case_id: uuid.UUID,
        payload: CaseAnalyzeRequest,
        *,
        user_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> CaseAnalyzeResponse:
        case = self.db.get(Case, case_id)
        if not case:
            raise AppError("not_found", "Case not found", status_code=404)

        graph_response = None
        ner_response = None

        if payload.run_graph:
            whatsapp_count = (
                self.db.scalar(
                    select(func.count()).select_from(WhatsAppData).where(WhatsAppData.case_id == case_id)
                )
                or 0
            )
            if whatsapp_count == 0:
                raise AppError(
                    "no_whatsapp_data",
                    "No WhatsApp data available for graph analysis on this case",
                    status_code=422,
                )
            graph_response = self.intelligence.run_graph(
                GraphRequest(source="whatsapp", source_id=case_id),
                user_id=user_id,
                ip_address=ip_address,
            )
            log_activity(
                self.db,
                user_id=user_id,
                action="case.intelligence.graph",
                entity_type="case",
                entity_id=case_id,
                details={"graph_id": str(graph_response.graph_id)},
                ip_address=ip_address,
            )
            self.db.commit()

        if payload.document_url and payload.document_type:
            ner_response = self.intelligence.run_ner(
                NerRequest(
                    case_id=case_id,
                    document_url=payload.document_url,
                    document_type=payload.document_type,
                    entity_types=list(payload.entity_types),
                ),
                user_id=user_id,
                ip_address=ip_address,
            )
            log_activity(
                self.db,
                user_id=user_id,
                action="case.intelligence.ner",
                entity_type="case",
                entity_id=case_id,
                details={"document_id": str(ner_response.document_id)},
                ip_address=ip_address,
            )
            self.db.commit()

        if graph_response is None and ner_response is None:
            raise AppError(
                "nothing_to_analyze",
                "Enable graph analysis or provide a document for NER",
                status_code=422,
            )

        log_activity(
            self.db,
            user_id=user_id,
            action="case.analyze",
            entity_type="case",
            entity_id=case_id,
            details={
                "graph": graph_response is not None,
                "ner": ner_response is not None,
            },
            ip_address=ip_address,
        )
        self.db.commit()

        return CaseAnalyzeResponse(
            case_id=case_id,
            graph=graph_response,
            ner=ner_response,
            analyzed_at=datetime.now(UTC),
        )

    def _latest_case_correlations(self, case_id: uuid.UUID) -> list[CorrelationResultItem]:
        items: list[CorrelationResultItem] = []

        for document in self.db.scalars(
            select(Document)
            .where(Document.case_id == case_id)
            .order_by(Document.created_at.desc())
            .limit(5)
        ):
            result_type = "apk" if document.file_type == "apk" else "ner"
            items.append(
                CorrelationResultItem(
                    id=document.id,
                    type=result_type,
                    status="completed",
                    created_at=document.created_at,
                )
            )

        for log in self.db.scalars(
            select(AuditLog)
            .where(
                AuditLog.entity_type == "case",
                AuditLog.entity_id == case_id,
                AuditLog.action == "case.intelligence.graph",
            )
            .order_by(AuditLog.timestamp.desc())
            .limit(3)
        ):
            graph_id = (log.details or {}).get("graph_id")
            if graph_id:
                items.append(
                    CorrelationResultItem(
                        id=uuid.UUID(str(graph_id)),
                        type="graph",
                        status="completed",
                        created_at=log.timestamp,
                    )
                )

        items.sort(key=lambda item: item.created_at, reverse=True)
        return items[:5]

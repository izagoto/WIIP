import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.exceptions import AppError, ForbiddenError, NotFoundError
from backend.models.audit_log import AuditLog
from backend.models.custody import CustodyLog, TransferApproval
from backend.models.evidence import Evidence
from backend.models.user import User
from backend.modules.d6_operations.audit import log_activity
from backend.modules.d7_evidence.custody import (
    create_custody_log,
    get_current_holder_id,
    has_pending_transfer,
)
from backend.modules.d7_evidence.integrity import compute_evidence_hash
from backend.schemas.evidence import (
    CustodyHistoryEntry,
    CustodyHistoryResponse,
    IntegrityHistoryEntry,
    IntegrityResponse,
    TransferApprovalRequest,
    TransferRequest,
    TransferResponse,
)


class CustodyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def _username(self, user_id: uuid.UUID | None) -> str | None:
        if not user_id:
            return None
        user = self.db.get(User, user_id)
        return user.username if user else None

    def record_initial_custody(
        self,
        evidence_id: uuid.UUID,
        *,
        holder_id: uuid.UUID,
        notes: str | None = None,
    ) -> CustodyLog:
        return create_custody_log(
            self.db,
            evidence_id=evidence_id,
            action="received",
            holder_id=holder_id,
            notes=notes or "Initial evidence registration",
            verified=True,
        )

    def get_custody_history(self, evidence_id: uuid.UUID) -> CustodyHistoryResponse:
        if not self.db.get(Evidence, evidence_id):
            raise NotFoundError("Evidence not found")

        logs = list(
            self.db.scalars(
                select(CustodyLog)
                .where(CustodyLog.evidence_id == evidence_id)
                .order_by(CustodyLog.timestamp.asc(), CustodyLog.created_at.asc())
            )
        )
        current_holder_id = get_current_holder_id(self.db, evidence_id)
        return CustodyHistoryResponse(
            evidence_id=evidence_id,
            current_holder=self._username(current_holder_id),
            custody_history=[
                CustodyHistoryEntry(
                    id=log.id,
                    holder=self._username(log.holder_id),
                    action=log.action,
                    from_user=self._username(log.from_user_id),
                    to_user=self._username(log.to_user_id),
                    timestamp=log.timestamp,
                    notes=log.notes,
                    verified=log.verified,
                )
                for log in logs
            ],
        )

    def request_transfer(
        self,
        evidence_id: uuid.UUID,
        payload: TransferRequest,
        *,
        requested_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> TransferResponse:
        evidence = self.db.get(Evidence, evidence_id)
        if not evidence:
            raise NotFoundError("Evidence not found")

        if payload.from_user_id == payload.to_user_id:
            raise AppError("invalid_transfer", "Sender and recipient must be different", status_code=422)

        from_user = self.db.get(User, payload.from_user_id)
        to_user = self.db.get(User, payload.to_user_id)
        if not from_user or not to_user:
            raise AppError("invalid_user", "Transfer user not found", status_code=422)
        if not from_user.is_active or not to_user.is_active:
            raise AppError("inactive_user", "Transfer user is inactive", status_code=422)

        current_holder = get_current_holder_id(self.db, evidence_id)
        if current_holder != payload.from_user_id:
            raise AppError(
                "invalid_holder",
                "Evidence is not currently held by the specified sender",
                status_code=422,
            )

        if has_pending_transfer(self.db, evidence_id):
            raise AppError("pending_transfer", "A transfer is already pending for this evidence", status_code=409)

        transfer = TransferApproval(
            evidence_id=evidence_id,
            from_user_id=payload.from_user_id,
            to_user_id=payload.to_user_id,
            status="pending",
            notes=payload.notes,
        )
        self.db.add(transfer)
        self.db.flush()
        log_activity(
            self.db,
            user_id=requested_by,
            action="evidence.transfer.request",
            entity_type="evidence",
            entity_id=evidence_id,
            details={
                "transfer_id": str(transfer.id),
                "from_user_id": str(payload.from_user_id),
                "to_user_id": str(payload.to_user_id),
            },
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(transfer)
        return TransferResponse.model_validate(transfer)

    def approve_transfer(
        self,
        transfer_id: uuid.UUID,
        payload: TransferApprovalRequest,
        *,
        approver_id: uuid.UUID,
        ip_address: str | None = None,
    ) -> TransferResponse:
        transfer = self.db.get(TransferApproval, transfer_id)
        if not transfer:
            raise NotFoundError("Transfer not found")

        if transfer.status != "pending":
            raise AppError("transfer_closed", "Transfer has already been processed", status_code=409)

        if approver_id != transfer.to_user_id:
            raise ForbiddenError("Only the designated recipient can approve this transfer")

        evidence = self.db.get(Evidence, transfer.evidence_id)
        if not evidence:
            raise NotFoundError("Evidence not found")

        if payload.approved:
            if evidence.sha256_hash:
                current_hash = compute_evidence_hash(evidence)
                if current_hash != evidence.sha256_hash:
                    raise AppError(
                        "integrity_mismatch",
                        "Evidence integrity check failed before transfer",
                        status_code=409,
                    )

            transfer.status = "approved"
            transfer.approved_by = approver_id
            transfer.approved_at = datetime.now(UTC)
            if payload.notes:
                transfer.notes = payload.notes

            create_custody_log(
                self.db,
                evidence_id=transfer.evidence_id,
                action="transferred",
                holder_id=transfer.to_user_id,
                from_user_id=transfer.from_user_id,
                to_user_id=transfer.to_user_id,
                notes=payload.notes or transfer.notes,
                verified=True,
            )
            action = "evidence.transfer.approve"
        else:
            transfer.status = "rejected"
            transfer.approved_by = approver_id
            transfer.approved_at = datetime.now(UTC)
            if payload.notes:
                transfer.notes = payload.notes
            action = "evidence.transfer.reject"

        log_activity(
            self.db,
            user_id=approver_id,
            action=action,
            entity_type="evidence",
            entity_id=transfer.evidence_id,
            details={
                "transfer_id": str(transfer.id),
                "approved": payload.approved,
            },
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(transfer)
        return TransferResponse.model_validate(transfer)

    def get_integrity(self, evidence_id: uuid.UUID) -> IntegrityResponse:
        evidence = self.db.get(Evidence, evidence_id)
        if not evidence:
            raise NotFoundError("Evidence not found")

        history_entries = list(
            self.db.scalars(
                select(AuditLog)
                .where(
                    AuditLog.entity_type == "evidence",
                    AuditLog.entity_id == evidence_id,
                    AuditLog.action == "evidence.verify_integrity",
                )
                .order_by(AuditLog.timestamp.desc())
            )
        )

        history: list[IntegrityHistoryEntry] = []
        last_verified_at: datetime | None = None
        for entry in history_entries:
            details = entry.details or {}
            hash_value = details.get("hash")
            if not hash_value or not entry.user_id:
                continue
            history.append(
                IntegrityHistoryEntry(
                    hash=str(hash_value),
                    verified_at=entry.timestamp,
                    verified_by=entry.user_id,
                )
            )
            if last_verified_at is None:
                last_verified_at = entry.timestamp

        verified = False
        if evidence.sha256_hash:
            verified = compute_evidence_hash(evidence) == evidence.sha256_hash

        return IntegrityResponse(
            evidence_id=evidence_id,
            sha256_hash=evidence.sha256_hash,
            verified=verified,
            last_verified_at=last_verified_at,
            history=history,
        )

    def verify_integrity(
        self,
        evidence_id: uuid.UUID,
        *,
        verified_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> IntegrityResponse:
        evidence = self.db.get(Evidence, evidence_id)
        if not evidence:
            raise NotFoundError("Evidence not found")

        current_hash = compute_evidence_hash(evidence)
        verified = True
        if evidence.sha256_hash and evidence.sha256_hash != current_hash:
            verified = False
        else:
            evidence.sha256_hash = current_hash

        log_activity(
            self.db,
            user_id=verified_by,
            action="evidence.verify_integrity",
            entity_type="evidence",
            entity_id=evidence_id,
            details={"hash": current_hash, "verified": verified},
            ip_address=ip_address,
        )
        self.db.commit()
        self.db.refresh(evidence)
        return self.get_integrity(evidence_id)

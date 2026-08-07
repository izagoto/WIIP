import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.custody import CustodyLog, TransferApproval


def get_current_holder_id(db: Session, evidence_id: uuid.UUID) -> uuid.UUID | None:
    log = db.scalar(
        select(CustodyLog)
        .where(CustodyLog.evidence_id == evidence_id)
        .order_by(CustodyLog.timestamp.desc(), CustodyLog.created_at.desc())
        .limit(1)
    )
    return log.holder_id if log else None


def has_pending_transfer(db: Session, evidence_id: uuid.UUID) -> bool:
    pending = db.scalar(
        select(TransferApproval)
        .where(
            TransferApproval.evidence_id == evidence_id,
            TransferApproval.status == "pending",
        )
        .limit(1)
    )
    return pending is not None


def create_custody_log(
    db: Session,
    *,
    evidence_id: uuid.UUID,
    action: str,
    holder_id: uuid.UUID | None,
    from_user_id: uuid.UUID | None = None,
    to_user_id: uuid.UUID | None = None,
    notes: str | None = None,
    verified: bool = False,
    timestamp: datetime | None = None,
) -> CustodyLog:
    log = CustodyLog(
        evidence_id=evidence_id,
        holder_id=holder_id,
        action=action,
        from_user_id=from_user_id,
        to_user_id=to_user_id,
        timestamp=timestamp or datetime.now(UTC),
        notes=notes,
        verified=verified,
    )
    db.add(log)
    return log

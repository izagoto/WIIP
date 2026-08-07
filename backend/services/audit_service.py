import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def list_logs(
        self,
        *,
        user_id: uuid.UUID | None = None,
        action: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[AuditLog]]:
        query = select(AuditLog)
        if user_id is not None:
            query = query.where(AuditLog.user_id == user_id)
        if action is not None:
            query = query.where(AuditLog.action == action)
        if start_date is not None:
            query = query.where(AuditLog.timestamp >= start_date)
        if end_date is not None:
            query = query.where(AuditLog.timestamp <= end_date)

        count_query = select(func.count()).select_from(AuditLog)
        if user_id is not None:
            count_query = count_query.where(AuditLog.user_id == user_id)
        if action is not None:
            count_query = count_query.where(AuditLog.action == action)
        if start_date is not None:
            count_query = count_query.where(AuditLog.timestamp >= start_date)
        if end_date is not None:
            count_query = count_query.where(AuditLog.timestamp <= end_date)

        total = self.db.scalar(count_query) or 0
        logs = list(
            self.db.scalars(
                query.order_by(AuditLog.timestamp.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return total, page, limit, logs

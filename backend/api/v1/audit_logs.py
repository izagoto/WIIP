import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.deps import CurrentUser, DbSession, require_roles
from backend.modules.d6_operations.rbac import ADMIN_ROLES
from backend.schemas.audit import AuditLogResponse
from backend.schemas.common import PaginatedResponse
from backend.services.audit_service import AuditService

router = APIRouter(prefix="/audit-logs", tags=["Audit Logs"])

AdminUser = Annotated[object, Depends(require_roles(*ADMIN_ROLES))]


@router.get("", response_model=PaginatedResponse[AuditLogResponse])
def list_audit_logs(
    db: DbSession,
    _admin: CurrentUser,
    _auth: AdminUser,
    user_id: uuid.UUID | None = None,
    action: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[AuditLogResponse]:
    service = AuditService(db)
    total, page, limit, logs = service.list_logs(
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        total=total,
        page=page,
        limit=limit,
        data=[AuditLogResponse.model_validate(log) for log in logs],
    )

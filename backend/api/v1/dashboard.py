from typing import Annotated

from fastapi import APIRouter, Depends

from backend.api.deps import CurrentUser, DbSession, require_roles
from backend.modules.d6_operations.rbac import READ_ROLES
from backend.schemas.case import DashboardResponse
from backend.services.case_service import CaseService

router = APIRouter(tags=["Dashboard"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]


@router.get("/dashboard", response_model=DashboardResponse)
def investigation_dashboard(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> DashboardResponse:
    service = CaseService(db)
    return service.get_dashboard()

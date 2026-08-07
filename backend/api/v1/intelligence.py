from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.modules.d6_operations.rbac import READ_ROLES, WRITE_ROLES
from backend.schemas.intelligence import (
    ApkAnalysisRequest,
    ApkAnalysisResponse,
    GraphRequest,
    GraphResponse,
    IntelligenceDashboardResponse,
    NerRequest,
    NerResponse,
)
from backend.services.intelligence_service import IntelligenceService

router = APIRouter(prefix="/intelligence", tags=["Intelligence"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
WriteUser = Annotated[object, Depends(require_roles(*WRITE_ROLES))]


@router.post("/ner", response_model=NerResponse)
def run_ner(
    payload: NerRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> NerResponse:
    return IntelligenceService(db).run_ner(
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.post("/graph", response_model=GraphResponse)
def run_graph_analysis(
    payload: GraphRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> GraphResponse:
    return IntelligenceService(db).run_graph(
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.post("/apk-analysis", response_model=ApkAnalysisResponse)
def run_apk_analysis(
    payload: ApkAnalysisRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> ApkAnalysisResponse:
    return IntelligenceService(db).run_apk_analysis(
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("/dashboard", response_model=IntelligenceDashboardResponse)
def intelligence_dashboard(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> IntelligenceDashboardResponse:
    return IntelligenceService(db).get_dashboard()

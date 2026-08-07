import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import Response

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.models.case import Case
from backend.models.task import Task
from backend.modules.d6_operations.rbac import READ_ROLES, WRITE_ROLES
from backend.schemas.case import (
    CaseCreateRequest,
    CaseResponse,
    CaseStatusUpdateRequest,
    CaseSummaryResponse,
    CaseUpdateRequest,
    KanbanBoardResponse,
    TaskCreateRequest,
    TaskResponse,
)
from backend.schemas.common import PaginatedResponse
from backend.schemas.intelligence import CaseAnalyzeRequest, CaseAnalyzeResponse, CaseIntegrationResponse
from backend.services.case_service import CaseService
from backend.services.integration_service import IntegrationService
from backend.services.report_service import ReportService

router = APIRouter(prefix="/cases", tags=["Cases"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
WriteUser = Annotated[object, Depends(require_roles(*WRITE_ROLES))]


def _case_response(case: Case) -> CaseResponse:
    return CaseResponse(
        id=case.id,
        title=case.title,
        description=case.description,
        priority=case.priority,
        status=case.status,
        assigned_unit=case.assigned_unit,
        assigned_investigator=case.assigned_to,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


def _task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        id=task.id,
        case_id=task.case_id,
        title=task.title,
        description=task.description,
        assignee=task.assignee_id,
        due_date=task.due_date,
        urgency=task.urgency,
        checklist=task.checklist,
        status=task.status,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> CaseResponse:
    service = CaseService(db)
    case = service.create_case(payload, created_by=user.id, ip_address=get_client_ip(request))
    return _case_response(case)


@router.get("", response_model=PaginatedResponse[CaseResponse])
def list_cases(
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
    status: str | None = None,
    priority: str | None = None,
    assigned_to: uuid.UUID | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[CaseResponse]:
    service = CaseService(db)
    total, page, limit, cases = service.list_cases(
        status=status,
        priority=priority,
        assigned_to=assigned_to,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        total=total,
        page=page,
        limit=limit,
        data=[_case_response(case) for case in cases],
    )


@router.get("/{case_id}/integration", response_model=CaseIntegrationResponse)
def get_case_integration(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> CaseIntegrationResponse:
    return IntegrationService(db).get_case_integration(case_id)


@router.post("/{case_id}/analyze", response_model=CaseAnalyzeResponse)
def run_case_analysis(
    case_id: uuid.UUID,
    payload: CaseAnalyzeRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> CaseAnalyzeResponse:
    return IntegrationService(db).run_case_analysis(
        case_id,
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )


@router.get("/{case_id}/report")
def get_case_report(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> Response:
    service = ReportService(db)
    pdf_bytes = service.generate_case_report_pdf(case_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="case-{case_id}-report.pdf"'},
    )


@router.get("/{case_id}", response_model=CaseResponse)
def get_case(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> CaseResponse:
    service = CaseService(db)
    return _case_response(service.get_case(case_id))


@router.put("/{case_id}", response_model=CaseResponse)
def update_case(
    case_id: uuid.UUID,
    payload: CaseUpdateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> CaseResponse:
    service = CaseService(db)
    case = service.update_case(
        case_id,
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )
    return _case_response(case)


@router.patch("/{case_id}/status", response_model=CaseResponse)
def update_case_status(
    case_id: uuid.UUID,
    payload: CaseStatusUpdateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> CaseResponse:
    service = CaseService(db)
    case = service.update_case_status(
        case_id,
        payload.status,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )
    return _case_response(case)


@router.get("/{case_id}/summary", response_model=CaseSummaryResponse)
def get_case_summary(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> CaseSummaryResponse:
    service = CaseService(db)
    return service.get_case_summary(case_id)


@router.get("/{case_id}/tasks", response_model=list[TaskResponse])
def list_case_tasks(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> list[TaskResponse]:
    service = CaseService(db)
    return [_task_response(task) for task in service.list_case_tasks(case_id)]


@router.post("/{case_id}/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_case_task(
    case_id: uuid.UUID,
    payload: TaskCreateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> TaskResponse:
    service = CaseService(db)
    task = service.create_task(
        case_id,
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )
    return _task_response(task)


@router.get("/{case_id}/kanban", response_model=KanbanBoardResponse)
def get_case_kanban(
    case_id: uuid.UUID,
    db: DbSession,
    _user: CurrentUser,
    _auth: ReadUser,
) -> KanbanBoardResponse:
    service = CaseService(db)
    return service.get_kanban_board(case_id)

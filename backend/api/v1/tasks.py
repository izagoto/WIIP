import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Request

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.models.task import Task
from backend.modules.d6_operations.rbac import READ_ROLES, WRITE_ROLES
from backend.schemas.case import TaskMoveRequest, TaskResponse, TaskUpdateRequest
from backend.services.case_service import CaseService

router = APIRouter(prefix="/tasks", tags=["Tasks"])

ReadUser = Annotated[object, Depends(require_roles(*READ_ROLES))]
WriteUser = Annotated[object, Depends(require_roles(*WRITE_ROLES))]


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


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: uuid.UUID,
    payload: TaskUpdateRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> TaskResponse:
    service = CaseService(db)
    task = service.update_task(
        task_id,
        payload,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )
    return _task_response(task)


@router.patch("/{task_id}/move", response_model=TaskResponse)
def move_task(
    task_id: uuid.UUID,
    payload: TaskMoveRequest,
    request: Request,
    db: DbSession,
    user: CurrentUser,
    _auth: WriteUser,
) -> TaskResponse:
    service = CaseService(db)
    task = service.move_task(
        task_id,
        payload.status,
        user_id=user.id,
        ip_address=get_client_ip(request),
    )
    return _task_response(task)

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, status

from backend.api.deps import CurrentUser, DbSession, get_client_ip, require_roles
from backend.modules.d6_operations.rbac import ADMIN_ROLES
from backend.schemas.auth import CreateUserRequest, UpdateUserRequest, UserResponse
from backend.schemas.common import PaginatedResponse
from backend.services.auth_service import AuthService
from backend.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users"])

AdminUser = Annotated[object, Depends(require_roles(*ADMIN_ROLES))]


@router.get("", response_model=PaginatedResponse[UserResponse])
def list_users(
    db: DbSession,
    _admin: CurrentUser,
    _auth: AdminUser,
    role: str | None = None,
    is_active: bool | None = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, ge=1, le=100),
) -> PaginatedResponse[UserResponse]:
    service = UserService(db)
    total, page, limit, users = service.list_users(
        role=role,
        is_active=is_active,
        page=page,
        limit=limit,
    )
    return PaginatedResponse(
        total=total,
        page=page,
        limit=limit,
        data=[UserResponse.model_validate(user) for user in users],
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: CreateUserRequest,
    request: Request,
    db: DbSession,
    admin: CurrentUser,
    _auth: AdminUser,
) -> UserResponse:
    service = AuthService(db)
    user = service.create_user(
        username=payload.username,
        email=str(payload.email),
        password=payload.password,
        role=payload.role,
        created_by=admin.id,
        ip_address=get_client_ip(request),
    )
    return UserResponse.model_validate(user)


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: uuid.UUID,
    db: DbSession,
    _admin: CurrentUser,
    _auth: AdminUser,
) -> UserResponse:
    service = UserService(db)
    user = service.get_user(user_id)
    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: uuid.UUID,
    payload: UpdateUserRequest,
    request: Request,
    db: DbSession,
    admin: CurrentUser,
    _auth: AdminUser,
) -> UserResponse:
    service = UserService(db)
    user = service.update_user(
        user_id,
        payload,
        updated_by=admin.id,
        ip_address=get_client_ip(request),
    )
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", response_model=UserResponse)
def deactivate_user(
    user_id: uuid.UUID,
    request: Request,
    db: DbSession,
    admin: CurrentUser,
    _auth: AdminUser,
) -> UserResponse:
    service = UserService(db)
    user = service.deactivate_user(
        user_id,
        deactivated_by=admin.id,
        ip_address=get_client_ip(request),
    )
    return UserResponse.model_validate(user)

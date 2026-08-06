from fastapi import APIRouter, Request, status

from backend.api.deps import CurrentUser, DbSession, get_client_ip
from backend.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    TokenResponse,
    UserResponse,
)
from backend.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser) -> UserResponse:
    return UserResponse.model_validate(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: DbSession) -> TokenResponse:
    service = AuthService(db)
    access_token, refresh_token, expires_in = service.login(
        username=payload.username,
        password=payload.password,
        ip_address=get_client_ip(request),
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=expires_in,
    )


@router.post("/refresh", response_model=AccessTokenResponse)
def refresh_token(payload: RefreshRequest, db: DbSession) -> AccessTokenResponse:
    service = AuthService(db)
    access_token, expires_in = service.refresh(payload.refresh_token)
    return AccessTokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, request: Request, db: DbSession) -> None:
    service = AuthService(db)
    service.logout(payload.refresh_token, ip_address=get_client_ip(request))

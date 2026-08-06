import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.auth import (
    create_access_token,
    create_refresh_token,
    hash_password,
    revoke_refresh_token,
    validate_refresh_token,
    verify_password,
)
from backend.core.exceptions import ConflictError, ForbiddenError, UnauthorizedError
from backend.models.audit_log import AuditLog
from backend.models.user import User, UserRole


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_user(
        self,
        username: str,
        email: str,
        password: str,
        role: str,
        *,
        created_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        if role not in {UserRole.INVESTIGATOR.value, UserRole.VIEWER.value}:
            raise ForbiddenError("Only investigator and viewer accounts can be created via API")

        if self.db.scalar(select(User).where(User.username == username)):
            raise ConflictError("Username already registered")
        if self.db.scalar(select(User).where(User.email == email)):
            raise ConflictError("Email already registered")

        user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )
        self.db.add(user)
        self.db.flush()
        self._log_action(created_by, "user.create", "user", user.id, ip_address, {"role": role})
        self.db.commit()
        self.db.refresh(user)
        return user

    def login(self, username: str, password: str, ip_address: str | None = None) -> tuple[str, str, int]:
        user = self.db.scalar(select(User).where(User.username == username))
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedError("Invalid username or password")
        if not user.is_active:
            raise UnauthorizedError("User account is inactive")

        subject = str(user.id)
        access_token, expires_in = create_access_token(subject, user.role)
        refresh_token, _ = create_refresh_token(subject, user.role)
        self._log_action(user.id, "user.login", "user", user.id, ip_address)
        self.db.commit()
        return access_token, refresh_token, expires_in

    def refresh(self, refresh_token: str) -> tuple[str, int]:
        try:
            payload = validate_refresh_token(refresh_token)
        except ValueError as exc:
            raise UnauthorizedError(str(exc)) from exc

        user_id = payload.get("sub")
        role = payload.get("role")
        if not user_id or not role:
            raise UnauthorizedError("Invalid refresh token")

        user = self.db.get(User, uuid.UUID(user_id))
        if not user or not user.is_active:
            raise UnauthorizedError("User not found or inactive")

        access_token, expires_in = create_access_token(str(user.id), user.role)
        return access_token, expires_in

    def logout(self, refresh_token: str, ip_address: str | None = None) -> None:
        try:
            payload = validate_refresh_token(refresh_token)
            user_id = payload.get("sub")
            if user_id:
                self._log_action(uuid.UUID(user_id), "user.logout", "user", uuid.UUID(user_id), ip_address)
        except (ValueError, UnauthorizedError):
            pass
        revoke_refresh_token(refresh_token)
        self.db.commit()

    def _log_action(
        self,
        user_id: uuid.UUID,
        action: str,
        entity_type: str,
        entity_id: uuid.UUID,
        ip_address: str | None,
        details: dict | None = None,
    ) -> None:
        self.db.add(
            AuditLog(
                user_id=user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                details=details,
                ip_address=ip_address,
            )
        )

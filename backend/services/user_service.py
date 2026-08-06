import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.core.auth import hash_password
from backend.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from backend.models.audit_log import AuditLog
from backend.models.user import User, UserRole
from backend.schemas.auth import UpdateUserRequest


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_user(self, user_id: uuid.UUID) -> User:
        user = self.db.get(User, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def list_users(
        self,
        *,
        role: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[int, int, int, list[User]]:
        query = select(User)
        if role is not None:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        count_query = select(func.count()).select_from(User)
        if role is not None:
            count_query = count_query.where(User.role == role)
        if is_active is not None:
            count_query = count_query.where(User.is_active == is_active)
        total = self.db.scalar(count_query) or 0
        users = list(
            self.db.scalars(
                query.order_by(User.created_at.desc()).offset((page - 1) * limit).limit(limit)
            )
        )
        return total, page, limit, users

    def update_user(
        self,
        user_id: uuid.UUID,
        payload: UpdateUserRequest,
        *,
        updated_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        user = self.get_user(user_id)
        changes: dict[str, object] = {}

        if payload.email is not None and payload.email != user.email:
            existing = self.db.scalar(select(User).where(User.email == str(payload.email)))
            if existing and existing.id != user.id:
                raise ConflictError("Email already registered")
            user.email = str(payload.email)
            changes["email"] = user.email

        if payload.role is not None:
            self._ensure_role_assignable(user, payload.role)
            user.role = payload.role
            changes["role"] = payload.role

        if payload.is_active is not None:
            if user.id == updated_by and not payload.is_active:
                raise ForbiddenError("You cannot deactivate your own account")
            if not payload.is_active:
                self._ensure_can_deactivate(user)
            user.is_active = payload.is_active
            changes["is_active"] = payload.is_active

        if payload.password is not None:
            user.password_hash = hash_password(payload.password)
            changes["password"] = "updated"

        if not changes:
            return user

        self._log_action(updated_by, "user.update", "user", user.id, ip_address, changes)
        self.db.commit()
        self.db.refresh(user)
        return user

    def deactivate_user(
        self,
        user_id: uuid.UUID,
        *,
        deactivated_by: uuid.UUID,
        ip_address: str | None = None,
    ) -> User:
        user = self.get_user(user_id)
        if user.id == deactivated_by:
            raise ForbiddenError("You cannot deactivate your own account")
        if not user.is_active:
            return user

        self._ensure_can_deactivate(user)
        user.is_active = False
        self._log_action(
            deactivated_by,
            "user.deactivate",
            "user",
            user.id,
            ip_address,
            {"is_active": False},
        )
        self.db.commit()
        self.db.refresh(user)
        return user

    def _ensure_role_assignable(self, user: User, role: str) -> None:
        if role not in {UserRole.INVESTIGATOR.value, UserRole.VIEWER.value}:
            raise ForbiddenError("Only investigator and viewer roles can be assigned via API")
        if user.role == UserRole.ADMIN.value:
            raise ForbiddenError("Admin role cannot be changed via API")

    def _ensure_can_deactivate(self, user: User) -> None:
        if user.role != UserRole.ADMIN.value:
            return

        active_admin_count = self.db.scalar(
            select(func.count())
            .select_from(User)
            .where(User.role == UserRole.ADMIN.value, User.is_active.is_(True))
        )
        if active_admin_count is not None and active_admin_count <= 1:
            raise ForbiddenError("Cannot deactivate the last active admin account")

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

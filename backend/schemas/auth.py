import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

UserRoleType = Literal["admin", "investigator", "viewer"]

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)


def _normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    if "@" not in normalized or normalized.startswith("@") or normalized.endswith("@"):
        raise ValueError("Invalid email format")
    local, domain = normalized.rsplit("@", 1)
    if not local or not domain or "." not in domain:
        raise ValueError("Invalid email format")
    return normalized


AssignableUserRoleType = Literal["investigator", "viewer"]


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=12, max_length=128)
    role: AssignableUserRoleType

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return _normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str, info) -> str:
        username = info.data.get("username", "")
        email = info.data.get("email", "")
        if username and username.lower() in value.lower():
            raise ValueError("Password must not contain username")
        if email and str(email).split("@")[0].lower() in value.lower():
            raise ValueError("Password must not contain email local part")
        if not _PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must be at least 12 characters and include uppercase, "
                "lowercase, digit, and special character"
            )
        return value


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        return _normalize_email(value)


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime


class UpdateUserRequest(BaseModel):
    email: str | None = Field(default=None, min_length=3, max_length=255)
    role: AssignableUserRoleType | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        return _normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str | None) -> str | None:
        if value is None:
            return value
        if not _PASSWORD_PATTERN.match(value):
            raise ValueError(
                "Password must be at least 12 characters and include uppercase, "
                "lowercase, digit, and special character"
            )
        return value


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

UserRoleType = Literal["admin", "investigator", "viewer"]

_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{12,}$"
)


AssignableUserRoleType = Literal["investigator", "viewer"]


class CreateUserRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: AssignableUserRoleType

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
    username: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    role: AssignableUserRoleType | None = None
    is_active: bool | None = None
    password: str | None = Field(default=None, min_length=12, max_length=128)

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

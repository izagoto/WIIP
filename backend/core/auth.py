import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
from jose import ExpiredSignatureError, JWTError, jwt

from backend.core.config import get_settings

_revoked_refresh_jtis: set[str] = set()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> tuple[str, str, int]:
    settings = get_settings()
    jti = str(uuid.uuid4())
    expire = datetime.now(UTC) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "exp": expire,
    }
    if extra_claims:
        payload.update(extra_claims)
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    return token, jti, int(expires_delta.total_seconds())


def create_access_token(subject: str, role: str) -> tuple[str, int]:
    settings = get_settings()
    token, _, expires_in = _create_token(
        subject=subject,
        token_type="access",
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
        extra_claims={"role": role},
    )
    return token, expires_in


def create_refresh_token(subject: str, role: str) -> tuple[str, str]:
    settings = get_settings()
    token, jti, _ = _create_token(
        subject=subject,
        token_type="refresh",
        expires_delta=timedelta(days=settings.jwt_refresh_token_expire_days),
        extra_claims={"role": role},
    )
    return token, jti


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


def normalize_bearer_token(token: str) -> str:
    normalized = token.strip()
    if normalized.lower().startswith("bearer "):
        normalized = normalized[7:].strip()
    return normalized


def validate_access_token(token: str) -> dict[str, Any]:
    token = normalize_bearer_token(token)
    try:
        payload = decode_token(token)
    except ExpiredSignatureError as exc:
        raise ValueError("Access token expired. Login again or call POST /auth/refresh.") from exc
    except JWTError as exc:
        raise ValueError(
            "Invalid access token. Use access_token from login (not refresh_token), "
            "without a 'Bearer ' prefix in Swagger Authorize."
        ) from exc
    if payload.get("type") != "access":
        raise ValueError("Invalid token type")
    return payload


def validate_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = decode_token(token)
    except JWTError as exc:
        raise ValueError("Invalid refresh token") from exc
    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")
    jti = payload.get("jti")
    if not jti or jti in _revoked_refresh_jtis:
        raise ValueError("Refresh token revoked")
    return payload


def revoke_refresh_token(token: str) -> None:
    try:
        payload = decode_token(token)
    except JWTError:
        return
    jti = payload.get("jti")
    if jti:
        _revoked_refresh_jtis.add(jti)

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.core.auth import hash_password
from backend.core.config import Settings, get_settings
from backend.core.database import SessionLocal
from backend.models.user import User, UserRole

logger = logging.getLogger(__name__)


def run_seed(db: Session | None = None, settings: Settings | None = None) -> None:
    app_settings = settings or get_settings()
    if app_settings.environment == "production":
        logger.warning("Skipping database seed in production environment")
        return

    owns_session = db is None
    session = db or SessionLocal()
    try:
        _seed_admin(session, app_settings)
        _seed_investigator(session, app_settings)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        if owns_session:
            session.close()


def _seed_admin(session: Session, settings: Settings) -> User | None:
    credentials = _parse_seed_credentials(
        settings.seed_admin_username,
        settings.seed_admin_email,
        settings.seed_admin_password,
    )
    if credentials is None:
        logger.info(
            "Skipping admin seed: set SEED_ADMIN_USERNAME, SEED_ADMIN_EMAIL, "
            "and SEED_ADMIN_PASSWORD in .env"
        )
        return None

    username, email, password = credentials
    admin = session.scalar(select(User).where(User.username == username))
    if admin is not None:
        return admin

    admin = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.ADMIN.value,
    )
    session.add(admin)
    session.flush()
    logger.info("Created admin user: %s", username)
    return admin


def _seed_investigator(session: Session, settings: Settings) -> User | None:
    credentials = _parse_seed_credentials(
        settings.seed_investigator_username,
        settings.seed_investigator_email,
        settings.seed_investigator_password,
    )
    if credentials is None:
        logger.info(
            "Skipping investigator seed: set SEED_INVESTIGATOR_USERNAME, "
            "SEED_INVESTIGATOR_EMAIL, and SEED_INVESTIGATOR_PASSWORD in .env"
        )
        return None

    username, email, password = credentials
    investigator = session.scalar(select(User).where(User.username == username))
    if investigator is not None:
        return investigator

    investigator = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
        role=UserRole.INVESTIGATOR.value,
    )
    session.add(investigator)
    session.flush()
    logger.info("Created investigator user: %s", username)
    return investigator


def _parse_seed_credentials(
    username: str | None,
    email: str | None,
    password: str | None,
) -> tuple[str, str, str] | None:
    if username and email and password:
        return username, email, password
    return None

import os
import sys

os.environ["SEED_ON_STARTUP"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.api.deps import get_db
from backend.core.auth import hash_password
from backend.main import create_app
from backend.models.base import Base
from backend.models.user import User, UserRole

ADMIN_PASSWORD = "AdminPass123!"


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    app = create_app()

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def admin_user(db_session):
    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password(ADMIN_PASSWORD),
        role=UserRole.ADMIN.value,
    )
    db_session.add(admin)
    db_session.commit()
    return admin


@pytest.fixture
def admin_headers(client, admin_user):
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers(client, admin_headers):
    client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "investigator1",
            "email": "investigator1@example.com",
            "password": "SecurePass123!",
            "role": "investigator",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "investigator1", "password": "SecurePass123!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def viewer_headers(client, admin_headers):
    client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "viewer1",
            "email": "viewer1@example.com",
            "password": "SecurePass123!",
            "role": "viewer",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"username": "viewer1", "password": "SecurePass123!"},
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

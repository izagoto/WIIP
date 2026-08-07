def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"


def test_public_register_removed(client):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "role": "investigator",
        },
    )
    assert response.status_code == 404


def test_admin_creates_user_and_login(client, admin_headers):
    create_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "SecurePass123!",
            "role": "investigator",
        },
    )
    assert create_response.status_code == 201
    assert create_response.json()["username"] == "testuser"
    assert create_response.json()["role"] == "investigator"

    login_response = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    refresh_response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 200
    assert "access_token" in refresh_response.json()

    logout_response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert logout_response.status_code == 204


def test_investigator_cannot_create_user(client, auth_headers):
    response = client.post(
        "/api/v1/users",
        headers=auth_headers,
        json={
            "username": "blocked",
            "email": "blocked@example.com",
            "password": "SecurePass123!",
            "role": "viewer",
        },
    )
    assert response.status_code == 403

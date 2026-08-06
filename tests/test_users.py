def test_get_me(client, auth_headers):
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "investigator1"
    assert payload["role"] == "investigator"
    assert payload["is_active"] is True


def test_list_users_as_admin(client, admin_headers, auth_headers):
    response = client.get("/api/v1/users", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    usernames = {item["username"] for item in payload["data"]}
    assert "admin" in usernames
    assert "investigator1" in usernames


def test_list_users_forbidden_for_investigator(client, auth_headers):
    response = client.get("/api/v1/users", headers=auth_headers)
    assert response.status_code == 403


def test_get_user_by_id(client, admin_headers, auth_headers):
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    response = client.get(f"/api/v1/users/{me['id']}", headers=admin_headers)
    assert response.status_code == 200
    assert response.json()["username"] == "investigator1"


def test_update_user(client, admin_headers):
    create_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "viewer2",
            "email": "viewer2@example.com",
            "password": "SecurePass123!",
            "role": "viewer",
        },
    )
    user_id = create_response.json()["id"]

    update_response = client.patch(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"email": "viewer2-updated@example.com", "role": "investigator"},
    )
    assert update_response.status_code == 200
    payload = update_response.json()
    assert payload["email"] == "viewer2-updated@example.com"
    assert payload["role"] == "investigator"


def test_deactivate_user_is_soft_delete(client, admin_headers):
    create_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "tempuser",
            "email": "tempuser@example.com",
            "password": "SecurePass123!",
            "role": "viewer",
        },
    )
    user_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert delete_response.status_code == 200
    assert delete_response.json()["is_active"] is False

    get_response = client.get(f"/api/v1/users/{user_id}", headers=admin_headers)
    assert get_response.status_code == 200
    assert get_response.json()["is_active"] is False

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "tempuser", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 401


def test_reactivate_user(client, admin_headers):
    create_response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "reactivate",
            "email": "reactivate@example.com",
            "password": "SecurePass123!",
            "role": "viewer",
        },
    )
    user_id = create_response.json()["id"]
    client.delete(f"/api/v1/users/{user_id}", headers=admin_headers)

    update_response = client.patch(
        f"/api/v1/users/{user_id}",
        headers=admin_headers,
        json={"is_active": True},
    )
    assert update_response.status_code == 200
    assert update_response.json()["is_active"] is True

    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": "reactivate", "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200


def test_admin_cannot_deactivate_self(client, admin_headers, admin_user):
    response = client.delete(f"/api/v1/users/{admin_user.id}", headers=admin_headers)
    assert response.status_code == 403

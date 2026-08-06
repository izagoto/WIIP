def test_create_and_get_case(client, auth_headers):
    create_response = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={
            "title": "Kasus Uji Sprint 2",
            "description": "Deskripsi kasus",
            "priority": "high",
            "assigned_unit": "Cyber Unit",
        },
    )
    assert create_response.status_code == 201
    case = create_response.json()
    assert case["title"] == "Kasus Uji Sprint 2"
    assert case["status"] == "open"

    get_response = client.get(f"/api/v1/cases/{case['id']}", headers=auth_headers)
    assert get_response.status_code == 200
    assert get_response.json()["priority"] == "high"


def test_list_cases_pagination(client, auth_headers):
    for index in range(3):
        client.post(
            "/api/v1/cases",
            headers=auth_headers,
            json={"title": f"Kasus {index}", "priority": "medium"},
        )

    response = client.get("/api/v1/cases?page=1&limit=2", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 3
    assert payload["page"] == 1
    assert payload["limit"] == 2
    assert len(payload["data"]) == 2


def test_update_case_status(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Status Test", "priority": "low"},
    ).json()["id"]

    response = client.patch(
        f"/api/v1/cases/{case_id}/status",
        headers=auth_headers,
        json={"status": "in_progress"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_task_lifecycle_and_kanban(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Task Test", "priority": "medium"},
    ).json()["id"]

    task_response = client.post(
        f"/api/v1/cases/{case_id}/tasks",
        headers=auth_headers,
        json={"title": "Analisis WA", "urgency": "high", "checklist": ["pull db", "decrypt"]},
    )
    assert task_response.status_code == 201
    task_id = task_response.json()["id"]
    assert task_response.json()["status"] == "todo"

    move_response = client.patch(
        f"/api/v1/tasks/{task_id}/move",
        headers=auth_headers,
        json={"status": "IN_PROGRESS"},
    )
    assert move_response.status_code == 200
    assert move_response.json()["status"] == "in_progress"

    kanban_response = client.get(f"/api/v1/cases/{case_id}/kanban", headers=auth_headers)
    assert kanban_response.status_code == 200
    columns = kanban_response.json()["columns"]
    assert len(columns["IN_PROGRESS"]) == 1
    assert columns["IN_PROGRESS"][0]["title"] == "Analisis WA"


def test_dashboard_and_case_summary(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Dashboard Test", "priority": "critical"},
    ).json()["id"]

    dashboard = client.get("/api/v1/dashboard", headers=auth_headers)
    assert dashboard.status_code == 200
    dashboard_data = dashboard.json()
    assert dashboard_data["total_cases"] >= 1
    assert "by_priority" in dashboard_data
    assert "task_load" in dashboard_data

    summary = client.get(f"/api/v1/cases/{case_id}/summary", headers=auth_headers)
    assert summary.status_code == 200
    summary_data = summary.json()
    assert summary_data["case_id"] == case_id
    assert summary_data["task_summary"]["total"] == 0


def test_viewer_cannot_create_case(client, viewer_headers):
    response = client.post(
        "/api/v1/cases",
        headers=viewer_headers,
        json={"title": "Forbidden", "priority": "low"},
    )
    assert response.status_code == 403


def test_cases_require_auth(client):
    response = client.get("/api/v1/cases")
    assert response.status_code == 401

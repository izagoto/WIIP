def test_organization_hierarchy(client, admin_headers, auth_headers):
    root = client.post(
        "/api/v1/organization/hierarchy",
        headers=admin_headers,
        json={
            "user_id": client.get("/api/v1/auth/me", headers=admin_headers).json()["id"],
            "name": "Cyber Command",
            "role": "commander",
        },
    )
    assert root.status_code == 201
    root_id = root.json()["id"]

    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    child = client.post(
        "/api/v1/organization/hierarchy",
        headers=admin_headers,
        json={
            "user_id": me["id"],
            "name": "Investigation Unit",
            "role": "investigator",
            "parent_id": root_id,
        },
    )
    assert child.status_code == 201

    response = client.get("/api/v1/organization/hierarchy", headers=auth_headers)
    assert response.status_code == 200
    tree = response.json()
    assert len(tree) == 1
    assert tree[0]["name"] == "Cyber Command"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "Investigation Unit"


def test_audit_logs_admin_only(client, admin_headers, auth_headers):
    denied = client.get("/api/v1/audit-logs", headers=auth_headers)
    assert denied.status_code == 403

    response = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "total" in payload
    assert "data" in payload
    assert payload["total"] >= 1


def test_evidence_crud(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Evidence Case", "priority": "medium"},
    ).json()["id"]

    create_response = client.post(
        "/api/v1/evidence",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "type": "mobile",
            "brand": "Samsung",
            "imei": "123456789012345",
            "serial_number": "SN-001",
            "capacity": "128GB",
            "condition_on_receipt": "Good",
            "storage_location": "Vault A-01",
        },
    )
    assert create_response.status_code == 201
    evidence = create_response.json()
    assert evidence["brand"] == "Samsung"
    assert evidence["type"] == "mobile"

    list_response = client.get(f"/api/v1/evidence?case_id={case_id}", headers=auth_headers)
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 1

    get_response = client.get(f"/api/v1/evidence/{evidence['id']}", headers=auth_headers)
    assert get_response.status_code == 200

    update_response = client.patch(
        f"/api/v1/evidence/{evidence['id']}",
        headers=auth_headers,
        json={"storage_location": "Vault B-02"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["storage_location"] == "Vault B-02"


def test_viewer_cannot_create_evidence(client, viewer_headers, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Viewer Evidence Case", "priority": "low"},
    ).json()["id"]

    response = client.post(
        "/api/v1/evidence",
        headers=viewer_headers,
        json={"case_id": case_id, "type": "document"},
    )
    assert response.status_code == 403


def test_case_pdf_report(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={
            "title": "Report Case",
            "description": "Case for PDF export",
            "priority": "high",
        },
    ).json()["id"]

    response = client.get(f"/api/v1/cases/{case_id}/report", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"

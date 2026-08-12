VALID_TEST_IMEI_SLOT1 = "490154203237518"
VALID_TEST_IMEI_SLOT2 = "359123456789012"
SMARTPHONE_TYPE = "Smartphone"


def _evidence_payload(case_id: str, **extra) -> dict:
    payload = {
        "case_id": case_id,
        "type": SMARTPHONE_TYPE,
        "brand": "Samsung Galaxy A23 5G",
        "imei_slot1": VALID_TEST_IMEI_SLOT1,
        "serial_number": "SN-001",
    }
    payload.update(extra)
    return payload


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
        json=_evidence_payload(
            case_id,
            imei_slot2=VALID_TEST_IMEI_SLOT2,
            capacity="128GB",
            condition_on_receipt="Good",
            storage_location="Vault A-01",
        ),
    )
    assert create_response.status_code == 201
    evidence = create_response.json()
    assert evidence["brand"] == "Samsung Galaxy A23 5G"
    assert evidence["type"] == SMARTPHONE_TYPE
    assert evidence["category"] == "mobile"
    assert evidence["imei_slot1"] == VALID_TEST_IMEI_SLOT1
    assert evidence["registration_number"].startswith("BB-")

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


def test_device_status_endpoint(client, auth_headers):
    response = client.get("/api/v1/evidence/device-status", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "is_cable_connected" in payload
    assert "is_adb_connected" in payload


def test_device_probe_endpoint(client, auth_headers):
    response = client.get("/api/v1/evidence/device-probe", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert "adb_available" in payload
    assert "message" in payload


def test_smartphone_requires_fields(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Smartphone Validation Case", "priority": "medium"},
    ).json()["id"]

    missing_brand = client.post(
        "/api/v1/evidence",
        headers=auth_headers,
        json=_evidence_payload(case_id, brand=None),
    )
    assert missing_brand.status_code == 422
    assert missing_brand.json()["error"]["code"] == "invalid_brand"


def test_invalid_imei_rejected(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "IMEI Validation Case", "priority": "medium"},
    ).json()["id"]

    response = client.post(
        "/api/v1/evidence",
        headers=auth_headers,
        json=_evidence_payload(case_id, imei_slot1="123456789012345"),
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_imei"


def test_duplicate_imei_rejected(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Duplicate IMEI Case", "priority": "medium"},
    ).json()["id"]
    other_case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Other Case", "priority": "low"},
    ).json()["id"]

    first = client.post("/api/v1/evidence", headers=auth_headers, json=_evidence_payload(case_id))
    assert first.status_code == 201

    duplicate = client.post(
        "/api/v1/evidence",
        headers=auth_headers,
        json=_evidence_payload(other_case_id, serial_number="SN-002"),
    )
    assert duplicate.status_code == 409


def test_evidence_on_closed_case_rejected(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Closed Case Evidence", "priority": "medium"},
    ).json()["id"]
    client.patch(
        f"/api/v1/cases/{case_id}/status",
        headers=auth_headers,
        json={"status": "closed"},
    )

    response = client.post(
        "/api/v1/evidence",
        headers=auth_headers,
        json=_evidence_payload(case_id),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "case_closed"


def test_viewer_cannot_create_evidence(client, viewer_headers, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Viewer Evidence Case", "priority": "low"},
    ).json()["id"]

    response = client.post(
        "/api/v1/evidence",
        headers=viewer_headers,
        json={"case_id": case_id, "type": "Dokumen"},
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

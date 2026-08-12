def _create_case(client, headers, title: str = "Sprint 4 Case"):
    return client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": title, "priority": "medium"},
    ).json()["id"]


def _create_evidence(client, headers, case_id: str, **extra):
    evidence_type = extra.get("type", "Smartphone")
    payload = {
        "case_id": case_id,
        "type": evidence_type,
        "storage_location": "Vault A-01",
        **extra,
    }
    if evidence_type == "Smartphone":
        payload.setdefault("brand", "Samsung Galaxy A23 5G")
        payload.setdefault("imei_slot1", "490154203237518")
        payload.setdefault("serial_number", "SN-S4-001")
    response = client.post("/api/v1/evidence", headers=headers, json=payload)
    assert response.status_code == 201
    return response.json()


def _second_investigator_headers(client, admin_headers):
    client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "username": "investigator2",
            "email": "investigator2@example.com",
            "password": "SecurePass123!",
            "role": "investigator",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        json={"email": "investigator2@example.com", "password": "SecurePass123!"},
    )
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


def test_custody_history_on_create(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)

    response = client.get(f"/api/v1/evidence/{evidence['id']}/custody", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["evidence_id"] == evidence["id"]
    assert payload["current_holder"] == "investigator1"
    assert len(payload["custody_history"]) == 1
    assert payload["custody_history"][0]["action"] == "received"
    assert payload["custody_history"][0]["verified"] is True


def test_transfer_approval_workflow(client, auth_headers, admin_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)
    investigator2_headers = _second_investigator_headers(client, admin_headers)

    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    investigator2 = client.get("/api/v1/auth/me", headers=investigator2_headers).json()

    transfer = client.post(
        f"/api/v1/evidence/{evidence['id']}/transfer",
        headers=auth_headers,
        json={
            "from_user_id": me["id"],
            "to_user_id": investigator2["id"],
            "notes": "Handover to second investigator",
        },
    )
    assert transfer.status_code == 201
    transfer_id = transfer.json()["id"]
    assert transfer.json()["status"] == "pending"

    denied = client.patch(
        f"/api/v1/evidence/transfers/{transfer_id}/approve",
        headers=auth_headers,
        json={"approved": True},
    )
    assert denied.status_code == 403

    approved = client.patch(
        f"/api/v1/evidence/transfers/{transfer_id}/approve",
        headers=investigator2_headers,
        json={"approved": True, "notes": "Received in good condition"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    custody = client.get(f"/api/v1/evidence/{evidence['id']}/custody", headers=auth_headers)
    assert custody.status_code == 200
    history = custody.json()["custody_history"]
    assert len(history) == 2
    assert history[-1]["action"] == "transferred"
    assert custody.json()["current_holder"] == "investigator2"


def test_transfer_rejection(client, auth_headers, admin_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)
    investigator2_headers = _second_investigator_headers(client, admin_headers)

    me = client.get("/api/v1/auth/me", headers=auth_headers).json()
    investigator2 = client.get("/api/v1/auth/me", headers=investigator2_headers).json()

    transfer = client.post(
        f"/api/v1/evidence/{evidence['id']}/transfer",
        headers=auth_headers,
        json={"from_user_id": me["id"], "to_user_id": investigator2["id"]},
    ).json()

    rejected = client.patch(
        f"/api/v1/evidence/transfers/{transfer['id']}/approve",
        headers=investigator2_headers,
        json={"approved": False, "notes": "Not available"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    custody = client.get(f"/api/v1/evidence/{evidence['id']}/custody", headers=auth_headers).json()
    assert custody["current_holder"] == "investigator1"


def test_integrity_verification(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)

    before = client.get(f"/api/v1/evidence/{evidence['id']}/integrity", headers=auth_headers)
    assert before.status_code == 200
    assert before.json()["sha256_hash"] is None
    assert before.json()["verified"] is False

    verified = client.post(
        f"/api/v1/evidence/{evidence['id']}/verify-integrity",
        headers=auth_headers,
    )
    assert verified.status_code == 200
    payload = verified.json()
    assert payload["sha256_hash"] is not None
    assert payload["verified"] is True
    assert len(payload["history"]) == 1


def test_vault_registry(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    _create_evidence(client, auth_headers, case_id, storage_location="Vault A-01", type="Smartphone")
    _create_evidence(client, auth_headers, case_id, storage_location="Vault A-01", type="Dokumen", serial_number="SN-DOC-1")
    _create_evidence(
        client,
        auth_headers,
        case_id,
        storage_location="Vault B-02",
        type="Smartphone",
        serial_number="SN-MOB-2",
        imei_slot1="359123456789012",
    )

    response = client.get("/api/v1/evidence/vault", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 3
    assert len(payload["groups"]) == 3

    filtered = client.get("/api/v1/evidence/vault?location=Vault%20A", headers=auth_headers)
    assert filtered.status_code == 200
    assert filtered.json()["total"] == 2


def test_geospatial_tracking(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(
        client,
        auth_headers,
        case_id,
        location_latitude="-6.200000",
        location_longitude="106.816666",
        serial_number="SN-GEO-1",
    )

    response = client.get("/api/v1/evidence/geospatial", headers=auth_headers)
    assert response.status_code == 200
    locations = response.json()["locations"]
    assert len(locations) >= 1
    match = next(item for item in locations if item["evidence_id"] == evidence["id"])
    assert str(match["latitude"]).startswith("-6.2")
    assert match["case_id"] == case_id


def test_custody_report_pdf(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)

    response = client.get(f"/api/v1/evidence/{evidence['id']}/custody-report", headers=auth_headers)
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content[:4] == b"%PDF"


def test_viewer_cannot_request_transfer(client, viewer_headers, auth_headers):
    case_id = _create_case(client, auth_headers)
    evidence = _create_evidence(client, auth_headers, case_id)
    me = client.get("/api/v1/auth/me", headers=auth_headers).json()

    response = client.post(
        f"/api/v1/evidence/{evidence['id']}/transfer",
        headers=viewer_headers,
        json={"from_user_id": me["id"], "to_user_id": me["id"]},
    )
    assert response.status_code == 403

import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.core.cache import get_dashboard_cache
from backend.models.whatsapp import WhatsAppData, WhatsAppMessage
from ml.pipeline.inference import get_inference_pipeline

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_caches():
    get_inference_pipeline().clear_cache()
    get_dashboard_cache().clear()
    yield
    get_inference_pipeline().clear_cache()
    get_dashboard_cache().clear()


def seed_whatsapp_case(db_session, case_id: uuid.UUID) -> None:
    conversation = WhatsAppData(
        case_id=case_id,
        wa_chat_jid="6289999888777@s.whatsapp.net",
        contact="Target Alpha",
        message_count=3,
    )
    db_session.add(conversation)
    db_session.flush()

    db_session.add_all(
        [
            WhatsAppMessage(
                conversation_record_id=conversation.id,
                timestamp=datetime.now(UTC),
                sender="Investigator",
                receiver="Target Alpha",
                content="Apakah transfer ke PT Maju Jaya sudah dilakukan di Jakarta?",
            ),
            WhatsAppMessage(
                conversation_record_id=conversation.id,
                timestamp=datetime.now(UTC),
                sender="Target Alpha",
                receiver="Investigator",
                content="Sudah, tanggal 2024-08-01.",
            ),
            WhatsAppMessage(
                conversation_record_id=conversation.id,
                timestamp=datetime.now(UTC),
                sender="Target Alpha",
                receiver="Kontak Lain",
                content="Koordinasi lanjutan besok.",
            ),
        ]
    )
    db_session.commit()


def _create_case(client, headers, title: str = "E2E Investigation Case"):
    return client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": title, "description": "Full cross-module workflow", "priority": "high"},
    ).json()["id"]


def _create_evidence(client, headers, case_id: str):
    response = client.post(
        "/api/v1/evidence",
        headers=headers,
        json={
            "case_id": case_id,
            "type": "mobile",
            "brand": "Samsung",
            "serial_number": "SN-E2E-001",
            "storage_location": "Vault E2E-01",
            "location_latitude": "-6.200000",
            "location_longitude": "106.816666",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_case_integration_overview(client, auth_headers, db_session):
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))
    evidence = _create_evidence(client, auth_headers, case_id)

    response = client.get(f"/api/v1/cases/{case_id}/integration", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["modules"]["whatsapp_conversations"] == 1
    assert payload["modules"]["whatsapp_messages"] == 3
    assert payload["modules"]["evidence_items"] == 1
    assert payload["modules"]["custody_entries"] == 1
    assert payload["intelligence_ready"] is True
    assert "case_pdf" in payload["reports_available"]
    assert "bast_pdf" in payload["reports_available"]
    assert evidence["id"]


def test_end_to_end_investigation_workflow(client, auth_headers, db_session, tmp_path):
    """WhatsApp → Case → Evidence → Intelligence → Reports."""
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))
    evidence = _create_evidence(client, auth_headers, case_id)

    analyze = client.post(
        f"/api/v1/cases/{case_id}/analyze",
        headers=auth_headers,
        json={
            "run_graph": True,
            "document_url": str(FIXTURES_DIR / "sample_intel.csv"),
            "document_type": "csv",
        },
    )
    assert analyze.status_code == 200
    analysis = analyze.json()
    assert analysis["graph"] is not None
    assert analysis["ner"] is not None
    assert len(analysis["graph"]["nodes"]) >= 2
    assert len(analysis["ner"]["entities"]) >= 1

    integration = client.get(f"/api/v1/cases/{case_id}/integration", headers=auth_headers)
    assert integration.status_code == 200
    modules = integration.json()["modules"]
    assert modules["graph_analyses"] >= 1
    assert modules["documents_analyzed"] >= 1
    assert modules["ner_entities"] >= 1

    case_report = client.get(f"/api/v1/cases/{case_id}/report", headers=auth_headers)
    assert case_report.status_code == 200
    assert case_report.content[:4] == b"%PDF"

    bast_report = client.get(
        f"/api/v1/evidence/{evidence['id']}/custody-report",
        headers=auth_headers,
    )
    assert bast_report.status_code == 200
    assert bast_report.content[:4] == b"%PDF"

    geospatial = client.get("/api/v1/evidence/geospatial", headers=auth_headers)
    assert geospatial.status_code == 200
    assert any(item["evidence_id"] == evidence["id"] for item in geospatial.json()["locations"])


def test_advanced_intelligence_dashboard(client, auth_headers, db_session):
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))
    client.post(
        f"/api/v1/cases/{case_id}/analyze",
        headers=auth_headers,
        json={"run_graph": True},
    )

    first = client.get("/api/v1/intelligence/dashboard", headers=auth_headers)
    second = client.get("/api/v1/intelligence/dashboard", headers=auth_headers)
    assert first.status_code == 200
    assert second.status_code == 200

    payload = first.json()
    assert payload["metrics"]["total_cases"] >= 1
    assert payload["metrics"]["total_whatsapp_conversations"] >= 1
    assert payload["metrics"]["cases_with_intelligence"] >= 0
    assert "generated_at" in payload
    assert second.json()["cached"] is True


def test_dashboard_cache_performance(client, auth_headers, db_session):
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))
    client.post(f"/api/v1/cases/{case_id}/analyze", headers=auth_headers, json={"run_graph": True})

    uncached = client.get("/api/v1/intelligence/dashboard", headers=auth_headers).json()
    get_dashboard_cache().clear()
    cached = client.get("/api/v1/intelligence/dashboard", headers=auth_headers).json()
    cached_again = client.get("/api/v1/intelligence/dashboard", headers=auth_headers).json()

    assert uncached["cached"] is False
    assert cached["cached"] is False
    assert cached_again["cached"] is True


def test_analyze_requires_whatsapp_for_graph(client, auth_headers):
    case_id = _create_case(client, auth_headers)
    response = client.post(
        f"/api/v1/cases/{case_id}/analyze",
        headers=auth_headers,
        json={"run_graph": True},
    )
    assert response.status_code == 422


def test_viewer_cannot_analyze_case(client, viewer_headers, auth_headers, db_session):
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))
    response = client.post(
        f"/api/v1/cases/{case_id}/analyze",
        headers=viewer_headers,
        json={"run_graph": True},
    )
    assert response.status_code == 403

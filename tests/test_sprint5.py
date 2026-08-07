import uuid
import zipfile
from datetime import UTC, datetime
from pathlib import Path

import pytest

from backend.models.whatsapp import WhatsAppData, WhatsAppMessage
from ml.pipeline.inference import get_inference_pipeline

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"


@pytest.fixture(autouse=True)
def reset_inference_pipeline():
    get_inference_pipeline().clear_cache()
    yield
    get_inference_pipeline().clear_cache()


@pytest.fixture
def sample_csv_path() -> str:
    return str(FIXTURES_DIR / "sample_intel.csv")


@pytest.fixture
def sample_apk_path(tmp_path) -> str:
    apk_path = tmp_path / "sample.apk"
    manifest = (
        "android.permission.READ_SMS "
        "android.permission.CAMERA "
        "android.permission.INTERNET"
    )
    with zipfile.ZipFile(apk_path, "w") as archive:
        archive.writestr("AndroidManifest.xml", manifest)
        archive.writestr("classes.dex", b"dex")
    return str(apk_path)


def seed_whatsapp_case(db_session, case_id: uuid.UUID) -> None:
    conversation = WhatsAppData(
        case_id=case_id,
        wa_chat_jid="6281234567890@s.whatsapp.net",
        contact="Ahmad Target",
        message_count=2,
    )
    db_session.add(conversation)
    db_session.flush()

    db_session.add_all(
        [
            WhatsAppMessage(
                conversation_record_id=conversation.id,
                timestamp=datetime.now(UTC),
                sender="Investigator",
                receiver="Ahmad Target",
                content="Apakah transfer sudah dilakukan?",
            ),
            WhatsAppMessage(
                conversation_record_id=conversation.id,
                timestamp=datetime.now(UTC),
                sender="Ahmad Target",
                receiver="Investigator",
                content="Sudah ke Jakarta kemarin.",
            ),
        ]
    )
    db_session.commit()


def _create_case(client, headers, title: str = "Intelligence Case"):
    return client.post(
        "/api/v1/cases",
        headers=headers,
        json={"title": title, "priority": "high"},
    ).json()["id"]


def test_ner_extraction(client, auth_headers, sample_csv_path):
    case_id = _create_case(client, auth_headers)

    response = client.post(
        "/api/v1/intelligence/ner",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "document_url": sample_csv_path,
            "document_type": "csv",
            "entity_types": ["person", "location", "organization", "date"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["document_id"]
    assert len(payload["entities"]) >= 3
    entity_types = {entity["type"] for entity in payload["entities"]}
    assert "location" in entity_types
    assert "organization" in entity_types


def test_ner_pipeline_cache(client, auth_headers, sample_csv_path):
    case_id = _create_case(client, auth_headers)
    body = {
        "case_id": case_id,
        "document_url": sample_csv_path,
        "document_type": "csv",
        "entity_types": ["person", "location"],
    }
    first = client.post("/api/v1/intelligence/ner", headers=auth_headers, json=body)
    second = client.post("/api/v1/intelligence/ner", headers=auth_headers, json=body)
    assert first.status_code == 200
    assert second.status_code == 200


def test_whatsapp_graph_analysis(client, auth_headers, db_session):
    case_id = _create_case(client, auth_headers)
    seed_whatsapp_case(db_session, uuid.UUID(case_id))

    response = client.post(
        "/api/v1/intelligence/graph",
        headers=auth_headers,
        json={
            "source": "whatsapp",
            "source_id": case_id,
            "entity_types": ["person", "contact"],
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["graph_id"]
    assert len(payload["nodes"]) >= 2
    assert len(payload["edges"]) >= 1


def test_document_graph_analysis(client, auth_headers, sample_csv_path):
    case_id = _create_case(client, auth_headers)
    ner = client.post(
        "/api/v1/intelligence/ner",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "document_url": sample_csv_path,
            "document_type": "csv",
            "entity_types": ["person", "location", "organization"],
        },
    ).json()

    response = client.post(
        "/api/v1/intelligence/graph",
        headers=auth_headers,
        json={
            "source": "document",
            "source_id": ner["document_id"],
            "entity_types": ["person", "location", "organization"],
        },
    )
    assert response.status_code == 200
    assert len(response.json()["nodes"]) >= 1


def test_apk_analysis(client, auth_headers, sample_apk_path):
    case_id = _create_case(client, auth_headers)

    response = client.post(
        "/api/v1/intelligence/apk-analysis",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "apk_url": sample_apk_path,
            "apk_filename": "sample.apk",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["analysis_id"]
    assert "android.permission.READ_SMS" in payload["permissions"]
    assert len(payload["threat_indicators"]) >= 1


def test_intelligence_dashboard(client, auth_headers, sample_csv_path):
    case_id = _create_case(client, auth_headers)
    client.post(
        "/api/v1/intelligence/ner",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "document_url": sample_csv_path,
            "document_type": "csv",
        },
    )

    response = client.get("/api/v1/intelligence/dashboard", headers=auth_headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["metrics"]["total_files_processed"] >= 1
    assert payload["metrics"]["total_ner_extractions"] >= 1
    assert "latency" in payload


def test_viewer_cannot_run_ner(client, viewer_headers, sample_csv_path, auth_headers):
    case_id = _create_case(client, auth_headers)
    response = client.post(
        "/api/v1/intelligence/ner",
        headers=viewer_headers,
        json={
            "case_id": case_id,
            "document_url": sample_csv_path,
            "document_type": "csv",
        },
    )
    assert response.status_code == 403

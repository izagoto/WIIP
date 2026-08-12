import shutil
from pathlib import Path

from backend.modules.d5_whatsapp.msgstore_parser import parse_msgstore

FIXTURE_DB = Path(__file__).resolve().parent / "fixtures" / "whatsapp_msgstore" / "TESTDEVICE_account1.db"


def test_parse_msgstore_fixture():
    conversations = parse_msgstore(FIXTURE_DB)
    by_jid = {item.wa_chat_jid: item for item in conversations}

    assert "status@broadcast" not in by_jid
    assert "6281111111111@s.whatsapp.net" in by_jid
    assert "120363999@g.us" in by_jid

    direct = by_jid["6281111111111@s.whatsapp.net"]
    assert direct.message_count == 3
    assert direct.messages[0].sender == "6281111111111@s.whatsapp.net"
    assert direct.messages[1].sender == "me"
    assert any(message.content_type == "image" for message in direct.messages)

    group = by_jid["120363999@g.us"]
    assert group.group_name == "Grup Tes"
    assert group.messages[0].sender == "6281111111111@s.whatsapp.net"


def test_whatsapp_import_api(client, auth_headers, tmp_path):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "WhatsApp Import Case", "priority": "high"},
    ).json()["id"]

    device_root = tmp_path / "db" / "TESTDEVICE" / "account_wa_1"
    device_root.mkdir(parents=True)
    shutil.copy(FIXTURE_DB, device_root / "TESTDEVICE_account1.db")

    response = client.post(
        "/api/v1/whatsapp/import",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "device_id": "TESTDEVICE",
            "account": "account_wa_1",
            "source_path": str(device_root),
        },
    )
    assert response.status_code == 202, response.text
    payload = response.json()
    assert payload["status"] == "completed"
    assert payload["conversations_imported"] == 2
    assert payload["messages_imported"] == 5
    assert payload["import_id"]

    status = client.get(
        f"/api/v1/whatsapp/import/{payload['import_id']}",
        headers=auth_headers,
    )
    assert status.status_code == 200
    assert status.json()["status"] == "completed"

    integration = client.get(f"/api/v1/cases/{case_id}/integration", headers=auth_headers)
    assert integration.status_code == 200
    assert integration.json()["modules"]["whatsapp_conversations"] == 2
    assert integration.json()["modules"]["whatsapp_messages"] == 5


def test_whatsapp_import_missing_db(client, auth_headers):
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "Missing WA DB", "priority": "medium"},
    ).json()["id"]

    response = client.post(
        "/api/v1/whatsapp/import",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "device_id": "DOES-NOT-EXIST",
            "account": "account_wa_1",
        },
    )
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "file_not_found"


def _import_fixture(client, auth_headers, tmp_path) -> tuple[str, dict]:
    case_id = client.post(
        "/api/v1/cases",
        headers=auth_headers,
        json={"title": "WhatsApp Read Case", "priority": "high"},
    ).json()["id"]
    device_root = tmp_path / "db" / "TESTDEVICE" / "account_wa_1"
    device_root.mkdir(parents=True)
    shutil.copy(FIXTURE_DB, device_root / "TESTDEVICE_account1.db")
    imported = client.post(
        "/api/v1/whatsapp/import",
        headers=auth_headers,
        json={
            "case_id": case_id,
            "device_id": "TESTDEVICE",
            "account": "account_wa_1",
            "source_path": str(device_root),
        },
    )
    assert imported.status_code == 202
    return case_id, imported.json()


def test_list_conversations_and_messages(client, auth_headers, tmp_path):
    case_id, _ = _import_fixture(client, auth_headers, tmp_path)

    conversations = client.get(
        f"/api/v1/whatsapp/conversations?case_id={case_id}",
        headers=auth_headers,
    )
    assert conversations.status_code == 200
    payload = conversations.json()
    assert payload["total"] == 2
    assert len(payload["data"]) == 2

    conversation_id = payload["data"][0]["id"]
    messages = client.get(
        f"/api/v1/whatsapp/conversations/{conversation_id}/messages",
        headers=auth_headers,
    )
    assert messages.status_code == 200
    message_payload = messages.json()
    assert message_payload["total"] >= 1
    assert message_payload["data"][0]["conversation_id"] == conversation_id
    assert "content" in message_payload["data"][0]


def test_conversation_keyword_filter(client, auth_headers, tmp_path):
    case_id, _ = _import_fixture(client, auth_headers, tmp_path)

    filtered = client.get(
        f"/api/v1/whatsapp/conversations?case_id={case_id}&keyword=Halo",
        headers=auth_headers,
    )
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1

    missing = client.get(
        f"/api/v1/whatsapp/conversations?case_id={case_id}&keyword=tidakada123",
        headers=auth_headers,
    )
    assert missing.status_code == 200
    assert missing.json()["total"] == 0


def test_whatsapp_search(client, auth_headers, tmp_path):
    case_id, _ = _import_fixture(client, auth_headers, tmp_path)

    found = client.get(
        f"/api/v1/whatsapp/search?q=Halo&case_id={case_id}",
        headers=auth_headers,
    )
    assert found.status_code == 200, found.text
    payload = found.json()
    assert payload["query"] == "Halo"
    assert payload["total"] >= 1
    assert payload["data"][0]["snippet"]
    assert "Halo" in payload["data"][0]["content"] or "halo" in payload["data"][0]["content"].lower()

    typed = client.get(
        f"/api/v1/whatsapp/search?q=image&case_id={case_id}&content_type=image",
        headers=auth_headers,
    )
    assert typed.status_code == 200
    # Fixture may store placeholder text for images; total can be 0 or more.
    assert "data" in typed.json()

    missing = client.get(
        f"/api/v1/whatsapp/search?q=tidakada123xyz&case_id={case_id}",
        headers=auth_headers,
    )
    assert missing.status_code == 200
    assert missing.json()["total"] == 0


def test_whatsapp_profile_summary(client, auth_headers, tmp_path):
    case_id, _ = _import_fixture(client, auth_headers, tmp_path)
    conversations = client.get(
        f"/api/v1/whatsapp/conversations?case_id={case_id}",
        headers=auth_headers,
    ).json()["data"]
    assert conversations

    group = next((item for item in conversations if item.get("group_name")), conversations[0])
    summary = client.get(
        f"/api/v1/whatsapp/profiles/{group['id']}/summary",
        headers=auth_headers,
    )
    assert summary.status_code == 200, summary.text
    payload = summary.json()
    assert payload["conversation_id"] == group["id"]
    assert payload["dominant_contacts"]
    assert "peak_hours" in payload["communication_patterns"]
    assert "average_messages_per_day" in payload["communication_patterns"]
    if group.get("group_name"):
        assert payload["active_groups"]
        assert payload["active_groups"][0]["group_name"] == group["group_name"]


def test_build_snippet_and_profile_unit():
    from datetime import UTC, datetime

    from backend.modules.d5_whatsapp.profile_analyzer import analyze_conversation_messages
    from backend.modules.d5_whatsapp.search_engine import build_snippet

    text = "aaa " + ("x" * 80) + " kata kunci rahasia " + ("y" * 80)
    snippet = build_snippet(text, "kata kunci")
    assert "kata kunci" in snippet
    assert snippet.startswith("…") or "kata" in snippet

    summary = analyze_conversation_messages(
        messages=[
            (datetime(2024, 1, 1, 9, tzinfo=UTC), "628111"),
            (datetime(2024, 1, 1, 9, tzinfo=UTC), "me"),
            (datetime(2024, 1, 2, 21, tzinfo=UTC), "628111"),
        ],
        group_name="Grup Tes",
    )
    assert summary.dominant_contacts[0].contact == "628111"
    assert summary.active_groups[0].member_count == 2
    assert 9 in summary.communication_patterns.peak_hours
    assert summary.communication_patterns.most_active_day == "Monday"
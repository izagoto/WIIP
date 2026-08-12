"""Parse decrypted WhatsApp msgstore SQLite into conversation/message records."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

MESSAGE_TYPE_MAP = {
    0: "text",
    1: "image",
    2: "audio",
    3: "audio",
    4: "document",
    5: "video",
    9: "document",
    13: "document",
    20: "image",
    28: "document",
    90: "document",
}

SKIP_CHAT_JIDS = {"status@broadcast", "0@s.whatsapp.net"}


@dataclass
class ParsedMessage:
    timestamp: datetime
    sender: str
    receiver: str
    content: str
    content_type: str


@dataclass
class ParsedConversation:
    wa_chat_jid: str
    contact: str | None
    group_name: str | None
    messages: list[ParsedMessage] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)

    @property
    def first_message_date(self) -> datetime | None:
        if not self.messages:
            return None
        return min(item.timestamp for item in self.messages)

    @property
    def last_message_date(self) -> datetime | None:
        if not self.messages:
            return None
        return max(item.timestamp for item in self.messages)


def _ms_to_datetime(value: int | None) -> datetime | None:
    if value is None:
        return None
    # WhatsApp stores milliseconds; tolerate seconds.
    seconds = value / 1000 if value > 10_000_000_000 else float(value)
    return datetime.fromtimestamp(seconds, tz=UTC)


def _content_type(message_type: int | None) -> str:
    if message_type is None:
        return "text"
    return MESSAGE_TYPE_MAP.get(message_type, "document")


def _display_contact(chat_jid: str, group_name: str | None, contacts: dict[str, str]) -> str | None:
    if group_name:
        return group_name
    if chat_jid in contacts:
        return contacts[chat_jid]
    user = chat_jid.split("@", 1)[0]
    return user or None


def _load_contacts(contacts_db: Path | None) -> dict[str, str]:
    if contacts_db is None or not contacts_db.exists():
        return {}
    mapping: dict[str, str] = {}
    with sqlite3.connect(str(contacts_db)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "wa_contacts" not in tables:
            return {}
        rows = connection.execute(
            """
            SELECT jid, display_name, wa_name, number
            FROM wa_contacts
            WHERE jid IS NOT NULL AND jid != ''
            """
        ).fetchall()
        for jid, display_name, wa_name, number in rows:
            label = (display_name or wa_name or number or "").strip()
            if label:
                mapping[str(jid)] = label
    return mapping


def _build_lid_map(connection: sqlite3.Connection) -> dict[str, str]:
    tables = {
        row[0]
        for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    }
    if "jid_map" not in tables or "jid" not in tables:
        return {}
    rows = connection.execute(
        """
        SELECT lid.raw_string, phone.raw_string
        FROM jid_map jm
        JOIN jid lid ON lid._id = jm.lid_row_id
        JOIN jid phone ON phone._id = jm.jid_row_id
        """
    ).fetchall()
    return {str(lid): str(phone) for lid, phone in rows if lid and phone}


def parse_msgstore(msgstore_path: Path, contacts_db: Path | None = None) -> list[ParsedConversation]:
    if not msgstore_path.exists():
        raise FileNotFoundError(f"msgstore database not found: {msgstore_path}")

    contacts = _load_contacts(contacts_db)
    conversations: dict[str, ParsedConversation] = {}

    with sqlite3.connect(str(msgstore_path)) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        required = {"chat", "message", "jid"}
        missing = required - tables
        if missing:
            raise ValueError(f"Unsupported WhatsApp database schema; missing tables: {sorted(missing)}")

        lid_map = _build_lid_map(connection)
        rows = connection.execute(
            """
            SELECT
                c._id AS chat_id,
                j.raw_string AS chat_jid,
                c.subject AS group_subject,
                m.from_me,
                m.timestamp,
                m.message_type,
                m.text_data,
                sj.raw_string AS sender_jid
            FROM chat c
            JOIN jid j ON j._id = c.jid_row_id
            JOIN message m ON m.chat_row_id = c._id
            LEFT JOIN jid sj ON sj._id = m.sender_jid_row_id
            WHERE m.timestamp IS NOT NULL
            ORDER BY c._id ASC, m.timestamp ASC, m._id ASC
            """
        ).fetchall()

        for (
            _chat_id,
            chat_jid_raw,
            group_subject,
            from_me,
            timestamp_ms,
            message_type,
            text_data,
            sender_jid_raw,
        ) in rows:
            if not chat_jid_raw:
                continue
            chat_jid = lid_map.get(str(chat_jid_raw), str(chat_jid_raw))
            if chat_jid in SKIP_CHAT_JIDS:
                continue

            content = (text_data or "").strip()
            content_type = _content_type(message_type if message_type is None else int(message_type))
            if not content:
                if content_type == "text":
                    # Skip empty plain-text / system noise.
                    if message_type in {7, None}:
                        continue
                    content = f"[{content_type}]"
                else:
                    content = f"[{content_type}]"

            ts = _ms_to_datetime(int(timestamp_ms))
            if ts is None:
                continue

            is_group = chat_jid.endswith("@g.us") or bool(group_subject)
            peer = chat_jid
            if from_me:
                sender = "me"
                receiver = peer
            else:
                if is_group and sender_jid_raw:
                    sender = lid_map.get(str(sender_jid_raw), str(sender_jid_raw))
                else:
                    sender = peer
                receiver = "me"

            if chat_jid not in conversations:
                conversations[chat_jid] = ParsedConversation(
                    wa_chat_jid=chat_jid,
                    contact=_display_contact(chat_jid, group_subject, contacts),
                    group_name=group_subject if is_group else None,
                )
            conversations[chat_jid].messages.append(
                ParsedMessage(
                    timestamp=ts,
                    sender=sender,
                    receiver=receiver,
                    content=content,
                    content_type=content_type,
                )
            )

    return list(conversations.values())

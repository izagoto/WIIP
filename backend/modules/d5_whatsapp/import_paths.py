from __future__ import annotations

from pathlib import Path

from backend.core.config import get_project_root
from backend.core.exceptions import AppError

ACCOUNT_TO_SUFFIX = {
    "account_wa_1": "_account1",
    "account_wa_2": "_account2",
    "account_wa_business": "_business",
}


def normalize_account(account: str) -> str:
    value = account.strip()
    aliases = {
        "1": "account_wa_1",
        "2": "account_wa_2",
        "business": "account_wa_business",
        "account_wa1": "account_wa_1",
        "account_wa2": "account_wa_2",
    }
    normalized = aliases.get(value, value)
    if normalized not in ACCOUNT_TO_SUFFIX:
        raise AppError(
            "invalid_account",
            "account must be one of: account_wa_1, account_wa_2, account_wa_business",
            status_code=422,
        )
    return normalized


def account_suffix(account: str) -> str:
    return ACCOUNT_TO_SUFFIX[normalize_account(account)]


def whatsapp_data_root() -> Path:
    return get_project_root() / "data" / "raw_whatsapp_data"


def resolve_msgstore_paths(
    *,
    device_id: str,
    account: str,
    source_path: str | None = None,
) -> tuple[Path, Path | None]:
    """
    Return (msgstore_db, contacts_db_or_none).

    Preferred layout:
      data/raw_whatsapp_data/db/{device_id}/account_wa_1/{device_id}_account1.db
      data/raw_whatsapp_data/db/{device_id}/account_wa_1/wa_account1.db

    Legacy layout:
      data/raw_whatsapp_data/db/{device_id}/{device_id}.db
      data/raw_whatsapp_data/db/{device_id}/wa.db
    """
    normalized_account = normalize_account(account)
    suffix = ACCOUNT_TO_SUFFIX[normalized_account]

    if source_path:
        base = Path(source_path).expanduser().resolve()
        if base.is_file():
            return base, None
        if not base.is_dir():
            raise AppError("file_not_found", f"source_path not found: {source_path}", status_code=422)
        msgstore = _first_existing(
            [
                base / f"{device_id}{suffix}.db",
                base / "msgstore.db",
                *sorted(base.glob("*.db")),
            ]
        )
        if msgstore is None:
            raise AppError(
                "file_not_found",
                f"No WhatsApp msgstore database found under {source_path}",
                status_code=422,
            )
        contacts = _first_existing(
            [
                base / f"wa{suffix}.db",
                base / "wa.db",
            ]
        )
        return msgstore, contacts

    device_root = whatsapp_data_root() / "db" / device_id
    account_dir = device_root / normalized_account

    msgstore = _first_existing(
        [
            account_dir / f"{device_id}{suffix}.db",
            account_dir / "msgstore.db",
            device_root / f"{device_id}.db",
            device_root / "msgstore.db",
        ]
    )
    if msgstore is None:
        raise AppError(
            "file_not_found",
            (
                f"Decrypted WhatsApp database not found for device_id={device_id}, "
                f"account={normalized_account}. Expected under "
                f"{account_dir} or {device_root}."
            ),
            status_code=422,
        )

    contacts = _first_existing(
        [
            account_dir / f"wa{suffix}.db",
            account_dir / "wa.db",
            device_root / "wa.db",
        ]
    )
    return msgstore, contacts


def _first_existing(candidates: list[Path]) -> Path | None:
    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        if candidate.is_file():
            return candidate.resolve()
    return None

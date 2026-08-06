import os
import shutil

_EXTRACTOR_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(_EXTRACTOR_DIR, "..", ".."))
WHATSAPP_DATA_ROOT = os.path.join(PROJECT_ROOT, "data", "raw_whatsapp_data")

# Pemetaan suffix internal → label folder
ACCOUNT_SUFFIX_LABELS = {
    "_account1": "1",
    "_account2": "2",
    "_business": "business",
}


def account_label(account_suffix: str) -> str:
    return ACCOUNT_SUFFIX_LABELS.get(account_suffix, account_suffix.lstrip("_"))


def account_folder_name(account_suffix: str, kind: str) -> str:
    """
    kind: 'wa' untuk database, 'key' untuk encryption key
    Contoh: account_wa_1, account_key_1, account_wa_business
    """
    label = account_label(account_suffix)
    prefix = "account_wa" if kind == "wa" else "account_key"
    if label == "business":
        return f"{prefix}_business"
    return f"{prefix}_{label}"


def db_root(device_id: str) -> str:
    return os.path.join(WHATSAPP_DATA_ROOT, "db", device_id)


def pull_root(device_id: str) -> str:
    return os.path.join(WHATSAPP_DATA_ROOT, "pull", device_id)


def account_key_dir(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(pull_root(device_id), account_folder_name(account_suffix, "key"))


def account_db_dir(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(db_root(device_id), account_folder_name(account_suffix, "wa"))


def pull_account_dir(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(pull_root(device_id), account_folder_name(account_suffix, "wa"))


def key_file(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(
        account_key_dir(device_id, account_suffix),
        f"{device_id}{account_suffix}_key.txt",
    )


def pulled_db_file(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(
        pull_account_dir(device_id, account_suffix),
        f"{device_id}{account_suffix}.db",
    )


def pulled_wa_db_file(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(
        pull_account_dir(device_id, account_suffix),
        f"wa{account_suffix}.db.crypt",
    )


def decrypted_db_file(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(
        account_db_dir(device_id, account_suffix),
        f"{device_id}{account_suffix}.db",
    )


def decrypted_wa_db_file(device_id: str, account_suffix: str = "_account1") -> str:
    return os.path.join(
        account_db_dir(device_id, account_suffix),
        f"wa{account_suffix}.db",
    )


def ensure_account_dirs(device_id: str, account_suffix: str) -> None:
    os.makedirs(account_key_dir(device_id, account_suffix), exist_ok=True)
    os.makedirs(account_db_dir(device_id, account_suffix), exist_ok=True)
    os.makedirs(pull_account_dir(device_id, account_suffix), exist_ok=True)


def cleanup_pull_account_dir(device_id: str, account_suffix: str) -> bool:
    """Hapus folder pull/{device_id}/account_wa_* setelah DB berhasil dipindah ke db/."""
    path = pull_account_dir(device_id, account_suffix)
    if not os.path.isdir(path):
        return False
    shutil.rmtree(path)
    return True


# Alias kompatibilitas untuk kode lama
def pull_dir(device_id: str) -> str:
    return pull_root(device_id)


def db_dir(device_id: str) -> str:
    return db_root(device_id)

from backend.models.task import TaskStatus

API_TO_DB_STATUS = {
    "TODO": TaskStatus.TODO.value,
    "IN_PROGRESS": TaskStatus.IN_PROGRESS.value,
    "DONE": TaskStatus.DONE.value,
}

DB_TO_API_STATUS = {value: key for key, value in API_TO_DB_STATUS.items()}

KANBAN_COLUMNS = ("TODO", "IN_PROGRESS", "DONE")


def api_status_to_db(status: str) -> str:
    normalized = status.upper()
    if normalized not in API_TO_DB_STATUS:
        raise ValueError(f"Invalid Kanban status: {status}")
    return API_TO_DB_STATUS[normalized]


def db_status_to_api(status: str) -> str:
    return DB_TO_API_STATUS.get(status, status.upper())

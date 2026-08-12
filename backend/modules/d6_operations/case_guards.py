from backend.core.exceptions import AppError
from backend.models.case import Case, CaseStatus


def ensure_case_open(case: Case, *, action: str) -> None:
    if case.status == CaseStatus.CLOSED.value:
        raise AppError(
            "case_closed",
            f"Cannot {action} on a closed case",
            status_code=409,
        )

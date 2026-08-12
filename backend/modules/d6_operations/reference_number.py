from datetime import UTC, datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def wib_now() -> datetime:
    return datetime.now(WIB)


def initials_from_title(title: str) -> str:
    words = title.strip().upper().split()
    initials = "".join(word[0] for word in words[:3] if word)
    return initials or "CASE"


def format_reference_number(title: str, when: datetime, daily_sequence: int) -> str:
    when_wib = when.astimezone(WIB) if when.tzinfo else when.replace(tzinfo=WIB)
    date_part = when_wib.strftime("%d%m%y")
    return f"{initials_from_title(title)}-{date_part}-{daily_sequence:04d}"


def wib_day_bounds_utc(when: datetime | None = None) -> tuple[datetime, datetime]:
    current = when or wib_now()
    if current.tzinfo is None:
        current = current.replace(tzinfo=WIB)
    else:
        current = current.astimezone(WIB)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)

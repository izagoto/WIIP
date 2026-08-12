from datetime import UTC, datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))


def format_registration_number(when: datetime, daily_sequence: int) -> str:
    when_wib = when.astimezone(WIB) if when.tzinfo else when.replace(tzinfo=WIB)
    date_part = when_wib.strftime("%d%m%y")
    return f"BB-{date_part}-{daily_sequence:04d}"


def wib_day_bounds_utc(when: datetime | None = None) -> tuple[datetime, datetime]:
    current = when or datetime.now(WIB)
    if current.tzinfo is None:
        current = current.replace(tzinfo=WIB)
    else:
        current = current.astimezone(WIB)
    start = current.replace(hour=0, minute=0, second=0, microsecond=0)
    end = start + timedelta(days=1)
    return start.astimezone(UTC), end.astimezone(UTC)

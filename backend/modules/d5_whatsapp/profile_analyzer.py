from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True)
class DominantContact:
    contact: str
    message_count: int
    interaction_frequency: float


@dataclass(frozen=True)
class ActiveGroup:
    group_name: str
    message_count: int
    member_count: int


@dataclass(frozen=True)
class CommunicationPatterns:
    peak_hours: list[int]
    average_messages_per_day: float
    most_active_day: str | None


@dataclass(frozen=True)
class ProfileSummary:
    dominant_contacts: list[DominantContact]
    active_groups: list[ActiveGroup]
    communication_patterns: CommunicationPatterns


_DAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)


def analyze_conversation_messages(
    *,
    messages: list[tuple[datetime, str]],
    group_name: str | None = None,
    top_contacts: int = 10,
    peak_hour_limit: int = 3,
) -> ProfileSummary:
    total = len(messages)
    sender_counts: Counter[str] = Counter()
    hour_counts: Counter[int] = Counter()
    day_counts: Counter[str] = Counter()
    dates: set[date] = set()

    for timestamp, sender in messages:
        label = (sender or "").strip() or "unknown"
        sender_counts[label] += 1
        if timestamp is not None:
            hour_counts[timestamp.hour] += 1
            day_counts[_DAY_NAMES[timestamp.weekday()]] += 1
            dates.add(timestamp.date())

    dominant = [
        DominantContact(
            contact=contact,
            message_count=count,
            interaction_frequency=round(count / total, 4) if total else 0.0,
        )
        for contact, count in sender_counts.most_common(top_contacts)
    ]

    members = {sender for _, sender in messages if (sender or "").strip()}
    active_groups: list[ActiveGroup] = []
    if group_name:
        active_groups.append(
            ActiveGroup(
                group_name=group_name,
                message_count=total,
                member_count=len(members),
            )
        )

    peak_hours = [hour for hour, _ in hour_counts.most_common(peak_hour_limit)]
    day_span = max(len(dates), 1)
    average = round(total / day_span, 2) if total else 0.0
    most_active = day_counts.most_common(1)[0][0] if day_counts else None

    return ProfileSummary(
        dominant_contacts=dominant,
        active_groups=active_groups,
        communication_patterns=CommunicationPatterns(
            peak_hours=peak_hours,
            average_messages_per_day=average,
            most_active_day=most_active,
        ),
    )

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self) -> None:
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if time.monotonic() >= entry.expires_at:
            del self._store[key]
            return None
        return entry.value

    def set(self, key: str, value: Any, *, ttl_seconds: int = 30) -> None:
        self._store[key] = CacheEntry(value=value, expires_at=time.monotonic() + ttl_seconds)

    def clear(self) -> None:
        self._store.clear()


_dashboard_cache = TTLCache()


def get_dashboard_cache() -> TTLCache:
    return _dashboard_cache

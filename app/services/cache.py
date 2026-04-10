import time
from dataclasses import dataclass
from typing import Any


@dataclass
class CacheEntry:
    value: Any
    expires_at: float


class TTLCache:
    def __init__(self, ttl_seconds: int = 3600) -> None:
        self.ttl_seconds = ttl_seconds
        self._store: dict[str, CacheEntry] = {}

    def get(self, key: str) -> Any | None:
        entry = self._store.get(key)
        if entry is None:
            return None

        if entry.expires_at <= time.time():
            del self._store[key]
            return None

        return entry.value

    def set(self, key: str, value: Any) -> None:
        self._store[key] = CacheEntry(
            value=value,
            expires_at=time.time() + self.ttl_seconds,
        )

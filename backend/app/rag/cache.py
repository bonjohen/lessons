"""TTL cache with LRU eviction for RAG components."""

from __future__ import annotations

import os
import time

CACHE_TTL_SECONDS = int(os.environ.get("CACHE_TTL_SECONDS", "300"))
CACHE_MAX_SIZE = int(os.environ.get("CACHE_MAX_SIZE", "128"))


class TTLCache:
    """Simple TTL cache with oldest-entry eviction when at capacity."""

    def __init__(self, ttl: int = CACHE_TTL_SECONDS, max_size: int = CACHE_MAX_SIZE):
        self._ttl = ttl
        self._max_size = max_size
        self._store: dict[str, tuple[float, object]] = {}

    @staticmethod
    def make_key(query: str, filters: dict | None = None) -> str:
        if filters is None:
            return query
        return f"{query}|{sorted(filters.items())}"

    def get(self, key: str):
        """Return cached value or None. Evicts expired entries."""
        entry = self._store.get(key)
        if entry is None:
            return None
        ts, value = entry
        if time.monotonic() - ts < self._ttl:
            return value
        del self._store[key]
        return None

    def put(self, key: str, value: object) -> None:
        """Store a value, evicting the oldest entry if at capacity."""
        if len(self._store) >= self._max_size and key not in self._store:
            oldest_key = min(self._store, key=lambda k: self._store[k][0])
            del self._store[oldest_key]
        self._store[key] = (time.monotonic(), value)

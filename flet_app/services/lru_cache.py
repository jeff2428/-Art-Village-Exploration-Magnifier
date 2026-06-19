"""LRU (Least Recently Used) cache for Art Village Exploration Magnifier.

Provides an in-memory LRU cache with configurable capacity and size limits.
Used to avoid storing large base64 image strings directly in IndexedDB/localStorage.

Usage:
    from services.lru_cache import lru_cache_manager
    await lru_cache_manager.set("img_abc123", base64_data)
    data = await lru_cache_manager.get("img_abc123")
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from typing import Any

logger = logging.getLogger(__name__)


class LRUCacheEntry:
    """Single cache entry with size tracking and TTL."""

    __slots__ = ("value", "size_bytes", "access_order", "expires_at")

    def __init__(self, value: Any, size_bytes: int) -> None:
        self.value = value
        self.size_bytes = size_bytes
        self.access_order: int = 0
        self.expires_at: float = 0.0

    @property
    def is_expired(self) -> bool:
        return self.expires_at > 0 and time.time() >= self.expires_at


class LRUCacheManager:
    """Thread-safe LRU cache with byte-size awareness.

    Evicts least-recently-used entries when capacity or total size is exceeded.
    Designed for storing base64 image data that would otherwise bloat IndexedDB.
    """

    def __init__(self, max_entries: int = 50, max_bytes: int = 10 * 1024 * 1024, expires_in_seconds: float = 3600) -> None:
        """Initialize LRU cache manager.

        Args:
            max_entries: Maximum number of entries in the cache.
            max_bytes: Maximum total size in bytes (default 10MB).
            expires_in_seconds: TTL per entry in seconds (default 3600 = 1 hour, 0 = no expiry).
        """
        self._max_entries = max_entries
        self._max_bytes = max_bytes
        self._expires_in_seconds = expires_in_seconds
        self._cache: OrderedDict[str, LRUCacheEntry] = OrderedDict()
        self._total_size = 0
        self._access_counter = 0
        self._lock = asyncio.Lock()

    def _evict_expired(self) -> None:
        """Remove all expired entries. Must be called while holding the lock."""
        if self._expires_in_seconds <= 0:
            return
        expired_keys = [k for k, v in self._cache.items() if v.is_expired]
        for key in expired_keys:
            entry = self._cache.pop(key)
            self._total_size -= entry.size_bytes

    async def get(self, key: str) -> Any | None:
        """Get a value from the cache. Returns None if not found or expired."""
        async with self._lock:
            self._evict_expired()
            if key not in self._cache:
                return None
            entry = self._cache.pop(key)
            if entry.is_expired:
                self._total_size -= entry.size_bytes
                return None
            self._access_counter += 1
            entry.access_order = self._access_counter
            self._cache[key] = entry  # Move to end (most recently used)
            return entry.value

    async def set(self, key: str, value: Any, size_bytes: int | None = None) -> None:
        """Set a value in the cache, evicting if necessary.

        Args:
            key: Cache key.
            value: Value to store.
            size_bytes: Estimated byte size of the value. If None, uses len(str(value)).
        """
        async with self._lock:
            if size_bytes is None:
                size_bytes = len(str(value).encode("utf-8"))

            # If key already exists, remove old entry first
            if key in self._cache:
                old_entry = self._cache.pop(key)
                self._total_size -= old_entry.size_bytes

            # Evict entries until we have room
            while (self._total_size + size_bytes > self._max_bytes or
                   len(self._cache) >= self._max_entries):
                if not self._cache:
                    break
                _, evicted = self._cache.popitem(last=False)  # Remove oldest
                self._total_size -= evicted.size_bytes

            # Insert new entry
            self._access_counter += 1
            new_entry = LRUCacheEntry(value, size_bytes)
            if self._expires_in_seconds > 0:
                new_entry.expires_at = time.time() + self._expires_in_seconds
            self._cache[key] = new_entry
            self._total_size += size_bytes

    async def delete(self, key: str) -> bool:
        """Delete a specific key from the cache. Returns True if found."""
        async with self._lock:
            if key not in self._cache:
                return False
            entry = self._cache.pop(key)
            self._total_size -= entry.size_bytes
            return True

    async def clear(self) -> None:
        """Clear all entries from the cache."""
        async with self._lock:
            self._cache.clear()
            self._total_size = 0

    async def size_info(self) -> dict[str, Any]:
        """Get current cache statistics."""
        async with self._lock:
            return {
                "entries": len(self._cache),
                "max_entries": self._max_entries,
                "total_bytes": self._total_size,
                "max_bytes": self._max_bytes,
                "utilization_pct": round(
                    (self._total_size / self._max_bytes * 100) if self._max_bytes > 0 else 0, 2
                ),
            }

    async def evict_oldest(self, count: int = 1) -> list[str]:
        """Manually evict the N oldest entries. Returns evicted keys."""
        async with self._lock:
            evicted_keys = []
            for _ in range(min(count, len(self._cache))):
                if not self._cache:
                    break
                key, entry = self._cache.popitem(last=False)
                self._total_size -= entry.size_bytes
                evicted_keys.append(key)
            return evicted_keys


# Module-level singleton
lru_cache_manager = LRUCacheManager(max_entries=50, max_bytes=10 * 1024 * 1024, expires_in_seconds=3600)

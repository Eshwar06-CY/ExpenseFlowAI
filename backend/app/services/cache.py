import time
import logging
import threading
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)

class InMemoryCache:
    """
    A thread-safe, in-memory caching system with support for time-to-live (TTL) expiration,
    locks, and prefix-based cache key invalidation patterns.
    """
    def __init__(self) -> None:
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        """Retrieve a cached value by key if not expired."""
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if entry["expiry"] is None or entry["expiry"] > time.time():
                    logger.debug(f"Cache HIT for key: {key}")
                    return entry["value"]
                else:
                    logger.debug(f"Cache EXPIRED for key: {key}")
                    del self._cache[key]
            else:
                logger.debug(f"Cache MISS for key: {key}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in the cache with an optional Time-To-Live (in seconds)."""
        with self._lock:
            expiry = time.time() + ttl if ttl is not None else None
            self._cache[key] = {
                "value": value,
                "expiry": expiry
            }
            logger.debug(f"Cache SET for key: {key} (TTL: {ttl}s)")

    def delete(self, key: str) -> None:
        """Explicitly delete a cache key."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                logger.debug(f"Cache DELETE for key: {key}")

    def delete_pattern(self, pattern: str) -> None:
        """
        Delete cache keys matching a prefix pattern (e.g. 'user:1:*').
        Converts asterisk pattern to clean prefix check.
        """
        with self._lock:
            prefix = pattern.replace("*", "")
            keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
            for key in keys_to_delete:
                del self._cache[key]
            if keys_to_delete:
                logger.debug(f"Cache INVALIDATE pattern '{pattern}' matching {len(keys_to_delete)} keys")

    def clear(self) -> None:
        """Clear all cache values."""
        with self._lock:
            self._cache.clear()
            logger.info("Central cache completely cleared.")

cache_service = InMemoryCache()

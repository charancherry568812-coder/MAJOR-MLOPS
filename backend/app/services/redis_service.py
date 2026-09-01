"""Redis Client with In-Memory fallback for distributed locking, rate-limiting, and cache."""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional

logger = logging.getLogger("RedisService")

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class InMemoryCache:
    """Fallback in-memory cache when Redis server is not running locally."""

    def __init__(self):
        self._store: Dict[str, Tuple[Any, float]] = {}  # key -> (value, expiry_time)

    def get(self, key: str) -> Optional[str]:
        if key in self._store:
            val, exp = self._store[key]
            if exp == 0 or exp > time.time():
                return val
            else:
                del self._store[key]
        return None

    def set(self, key: str, value: str, ex: Optional[int] = None) -> bool:
        exp = time.time() + ex if ex else 0
        self._store[key] = (value, exp)
        return True

    def delete(self, key: str) -> bool:
        return bool(self._store.pop(key, None))

    def incr(self, key: str) -> int:
        val = int(self.get(key) or 0) + 1
        self.set(key, str(val))
        return val


class RedisService:
    """Unified Cache, Lock, and Distributed State Provider."""

    def __init__(self):
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._client = None
        self._fallback = InMemoryCache()

        if REDIS_AVAILABLE:
            try:
                client = redis.from_url(self.redis_url, socket_timeout=1, decode_responses=True)
                client.ping()
                self._client = client
                logger.info("Connected to Redis server.")
            except Exception:
                logger.info("Redis server not reachable, using local in-memory fallback cache.")
                self._client = None

    def get(self, key: str) -> Optional[str]:
        if self._client:
            try:
                return self._client.get(key)
            except Exception:
                pass
        return self._fallback.get(key)

    def set(self, key: str, value: str, ex: int = 300) -> bool:
        if self._client:
            try:
                return bool(self._client.set(key, value, ex=ex))
            except Exception:
                pass
        return self._fallback.set(key, value, ex=ex)

    def delete(self, key: str) -> bool:
        if self._client:
            try:
                return bool(self._client.delete(key))
            except Exception:
                pass
        return self._fallback.delete(key)

    def is_rate_limited(self, identifier: str, max_requests: int = 60, window_seconds: int = 60) -> bool:
        """Sliding window or fixed bucket rate limiter."""
        key = f"rate_limit:{identifier}:{int(time.time() // window_seconds)}"
        if self._client:
            try:
                current = self._client.incr(key)
                if current == 1:
                    self._client.expire(key, window_seconds)
                return current > max_requests
            except Exception:
                pass
        current = self._fallback.incr(key)
        return current > max_requests


redis_service = RedisService()

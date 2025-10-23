"""Caching service for scan results."""

import hashlib
from typing import Any, Dict, Optional

from cachetools import TTLCache


class ScanCache:
    """In-memory cache for scan results with TTL."""

    def __init__(self, ttl_hours: int = 12, max_size: int = 1000):
        """
        Initialize cache.

        Args:
            ttl_hours: Time-to-live in hours (default 12)
            max_size: Maximum number of cached items (default 1000)
        """
        self.cache = TTLCache(maxsize=max_size, ttl=ttl_hours * 3600)

    def _make_key(self, owner: str, name: str, ref: str, commit_sha: str) -> str:
        """
        Generate cache key for a repository scan.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref
            commit_sha: Commit SHA

        Returns:
            Cache key string
        """
        key_str = f"{owner}/{name}@{ref}#{commit_sha}"
        return hashlib.sha256(key_str.encode()).hexdigest()

    def get(self, owner: str, name: str, ref: str, commit_sha: str) -> Optional[Dict[str, Any]]:
        """
        Get cached scan result.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref
            commit_sha: Commit SHA

        Returns:
            Cached scan result or None if not found/expired
        """
        key = self._make_key(owner, name, ref, commit_sha)
        return self.cache.get(key)

    def set(self, owner: str, name: str, ref: str, commit_sha: str, result: Dict[str, Any]) -> None:
        """
        Cache a scan result.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref
            commit_sha: Commit SHA
            result: Scan result to cache
        """
        key = self._make_key(owner, name, ref, commit_sha)
        self.cache[key] = result

    def invalidate(self, owner: str, name: str, ref: str, commit_sha: str) -> None:
        """
        Invalidate a cached scan result.

        Args:
            owner: Repository owner
            name: Repository name
            ref: Git ref
            commit_sha: Commit SHA
        """
        key = self._make_key(owner, name, ref, commit_sha)
        self.cache.pop(key, None)

    def clear(self) -> None:
        """Clear all cached results."""
        self.cache.clear()


# Global cache instance
_cache_instance: Optional[ScanCache] = None


def get_scan_cache() -> ScanCache:
    """Get or create global cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = ScanCache()
    return _cache_instance

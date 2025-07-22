"""
LLM response caching system for performance optimization.

This module provides intelligent caching for LLM responses to reduce
API calls and improve response times for similar queries.
"""

import hashlib
import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LLMCache:
    """
    Intelligent caching system for LLM responses.

    Features:
    - Memory and disk-based caching
    - TTL-based expiration
    - Cache size management
    - Thread-safe operations
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        ttl_hours: float = 24.0,
        max_size_mb: float = 100.0,
        enabled: bool = True,
    ):
        """
        Initialize LLM cache.

        Args:
            cache_dir: Directory for cache storage
            ttl_hours: Time to live in hours
            max_size_mb: Maximum cache size in MB
            enabled: Whether caching is enabled
        """
        self.enabled = enabled
        self.ttl_hours = ttl_hours
        self.max_size_mb = max_size_mb
        self._lock = Lock()

        if not self.enabled:
            logger.info("LLM cache disabled")
            return

        # Setup cache directory
        if cache_dir is None:
            cache_dir = os.path.join(os.path.expanduser("~"), ".rs_pa", "llm_cache")

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Initialize SQLite database for metadata
        self.db_path = self.cache_dir / "cache_metadata.db"
        self._init_database()

        logger.info(
            f"LLM cache initialized: {self.cache_dir} "
            f"(TTL: {ttl_hours}h, Max: {max_size_mb}MB)"
        )

    def _init_database(self) -> None:
        """Initialize cache metadata database."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS cache_entries (
                        key_hash TEXT PRIMARY KEY,
                        prompt_hash TEXT NOT NULL,
                        created_at TIMESTAMP NOT NULL,
                        accessed_at TIMESTAMP NOT NULL,
                        response_size INTEGER NOT NULL,
                        cache_file TEXT NOT NULL,
                        metadata TEXT
                    )
                """
                )

                # Create indexes
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_created_at "
                    "ON cache_entries(created_at)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_accessed_at "
                    "ON cache_entries(accessed_at)"
                )
                conn.execute(
                    "CREATE INDEX IF NOT EXISTS idx_prompt_hash "
                    "ON cache_entries(prompt_hash)"
                )

                conn.commit()

        except Exception as error:
            logger.error(f"Failed to initialize cache database: {error}")

    def _generate_cache_key(self, prompt: str, model_config: Dict[str, Any]) -> str:
        """
        Generate cache key from prompt and model configuration.

        Args:
            prompt: LLM prompt text
            model_config: Model configuration parameters

        Returns:
            Cache key hash
        """
        # Include relevant model parameters in cache key
        cache_data = {
            "prompt": prompt,
            "model": model_config.get("model", "default"),
            "temperature": model_config.get("temperature", 0.0),
            "max_tokens": model_config.get("max_tokens"),
            "top_p": model_config.get("top_p"),
        }

        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()

    def get(
        self, prompt: str, model_config: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Retrieve cached LLM response.

        Args:
            prompt: LLM prompt text
            model_config: Model configuration parameters

        Returns:
            Cached response or None if not found/expired
        """
        if not self.enabled:
            return None

        model_config = model_config or {}
        cache_key = self._generate_cache_key(prompt, model_config)

        try:
            with self._lock:
                with sqlite3.connect(str(self.db_path)) as conn:
                    cursor = conn.execute(
                        "SELECT cache_file, created_at FROM cache_entries "
                        "WHERE key_hash = ?",
                        (cache_key,),
                    )
                    row = cursor.fetchone()

                    if not row:
                        return None

                    cache_file, created_at = row

                    # Check TTL expiration
                    created_time = datetime.fromisoformat(created_at)
                    if datetime.now() - created_time > timedelta(hours=self.ttl_hours):
                        logger.debug(f"Cache entry expired: {cache_key[:8]}...")
                        self._remove_entry(cache_key)
                        return None

                    # Read cached response
                    cache_file_path = self.cache_dir / cache_file
                    if not cache_file_path.exists():
                        logger.warning(f"Cache file missing: {cache_file}")
                        self._remove_entry(cache_key)
                        return None

                    with open(cache_file_path, "r", encoding="utf-8") as f:
                        response = f.read()

                    # Update access time
                    conn.execute(
                        "UPDATE cache_entries SET accessed_at = ? WHERE key_hash = ?",
                        (datetime.now().isoformat(), cache_key),
                    )
                    conn.commit()

                    logger.debug(f"Cache hit: {cache_key[:8]}...")
                    return response

        except Exception as error:
            logger.error(f"Error retrieving from cache: {error}")
            return None

    def set(
        self, prompt: str, response: str, model_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store LLM response in cache.

        Args:
            prompt: LLM prompt text
            response: LLM response text
            model_config: Model configuration parameters

        Returns:
            True if successfully cached
        """
        if not self.enabled or not response:
            return False

        model_config = model_config or {}
        cache_key = self._generate_cache_key(prompt, model_config)

        try:
            with self._lock:
                # Check cache size and cleanup if needed
                self._cleanup_if_needed()

                # Generate cache file name
                cache_file = f"{cache_key}.txt"
                cache_file_path = self.cache_dir / cache_file

                # Write response to file
                with open(cache_file_path, "w", encoding="utf-8") as f:
                    f.write(response)

                response_size = len(response.encode("utf-8"))
                prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()

                # Store metadata
                with sqlite3.connect(str(self.db_path)) as conn:
                    now = datetime.now().isoformat()
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO cache_entries
                        (key_hash, prompt_hash, created_at, accessed_at,
                         response_size, cache_file, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                        (
                            cache_key,
                            prompt_hash,
                            now,
                            now,
                            response_size,
                            cache_file,
                            json.dumps(model_config),
                        ),
                    )
                    conn.commit()

                logger.debug(
                    f"Cache stored: {cache_key[:8]}... ({response_size} bytes)"
                )
                return True

        except Exception as error:
            logger.error(f"Error storing in cache: {error}")
            return False

    def _cleanup_if_needed(self) -> None:
        """Clean up cache if it exceeds size limit."""
        try:
            current_size_mb = self.get_cache_size_mb()

            if current_size_mb > self.max_size_mb:
                logger.info(
                    f"Cache size ({current_size_mb:.1f}MB) exceeds limit "
                    f"({self.max_size_mb}MB), cleaning up..."
                )
                self._cleanup_old_entries(target_size_mb=self.max_size_mb * 0.8)

        except Exception as error:
            logger.error(f"Error during cache cleanup: {error}")

    def _cleanup_old_entries(self, target_size_mb: float) -> None:
        """Remove old cache entries to reach target size."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                # Get entries ordered by access time (oldest first)
                cursor = conn.execute(
                    """
                    SELECT key_hash, cache_file, response_size
                    FROM cache_entries
                    ORDER BY accessed_at ASC
                """
                )

                removed_count = 0
                removed_size = 0

                for key_hash, cache_file, response_size in cursor:
                    # Remove entry
                    cache_file_path = self.cache_dir / cache_file
                    if cache_file_path.exists():
                        cache_file_path.unlink()

                    conn.execute(
                        "DELETE FROM cache_entries WHERE key_hash = ?", (key_hash,)
                    )

                    removed_count += 1
                    removed_size += response_size

                    # Check if we've reached target size
                    current_size_mb = self.get_cache_size_mb() - (
                        removed_size / 1024 / 1024
                    )
                    if current_size_mb <= target_size_mb:
                        break

                conn.commit()

                logger.info(
                    f"Cleaned up {removed_count} cache entries "
                    f"({removed_size / 1024 / 1024:.1f}MB)"
                )

        except Exception as error:
            logger.error(f"Error cleaning up cache entries: {error}")

    def _remove_entry(self, cache_key: str) -> None:
        """Remove a single cache entry."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT cache_file FROM cache_entries WHERE key_hash = ?",
                    (cache_key,),
                )
                row = cursor.fetchone()

                if row:
                    cache_file = row[0]
                    cache_file_path = self.cache_dir / cache_file

                    if cache_file_path.exists():
                        cache_file_path.unlink()

                    conn.execute(
                        "DELETE FROM cache_entries WHERE key_hash = ?", (cache_key,)
                    )
                    conn.commit()

        except Exception as error:
            logger.error(f"Error removing cache entry: {error}")

    def get_cache_size_mb(self) -> float:
        """Get current cache size in MB."""
        try:
            total_size = 0
            for file_path in self.cache_dir.glob("*.txt"):
                total_size += file_path.stat().st_size
            return total_size / 1024 / 1024
        except Exception as error:
            logger.error(f"Error calculating cache size: {error}")
            return 0.0

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*), SUM(response_size) FROM cache_entries"
                )
                count, total_size = cursor.fetchone()

                cursor = conn.execute(
                    """
                    SELECT COUNT(*) FROM cache_entries
                    WHERE datetime(created_at) > datetime('now', '-1 hour')
                """
                )
                recent_entries = cursor.fetchone()[0]

                return {
                    "enabled": self.enabled,
                    "total_entries": count or 0,
                    "total_size_mb": (total_size or 0) / 1024 / 1024,
                    "recent_entries": recent_entries or 0,
                    "cache_dir": str(self.cache_dir),
                    "ttl_hours": self.ttl_hours,
                    "max_size_mb": self.max_size_mb,
                }

        except Exception as error:
            logger.error(f"Error getting cache stats: {error}")
            return {"enabled": False, "error": str(error)}

    def clear(self) -> None:
        """Clear all cache entries."""
        try:
            with self._lock:
                # Remove all cache files
                for file_path in self.cache_dir.glob("*.txt"):
                    file_path.unlink()

                # Clear database
                with sqlite3.connect(str(self.db_path)) as conn:
                    conn.execute("DELETE FROM cache_entries")
                    conn.commit()

                logger.info("LLM cache cleared")

        except Exception as error:
            logger.error(f"Error clearing cache: {error}")


# Global cache instance
_llm_cache: Optional[LLMCache] = None


def get_llm_cache() -> LLMCache:
    """Get global LLM cache instance."""
    global _llm_cache

    if _llm_cache is None:
        # Load configuration from environment
        enabled = (
            os.environ.get("RSPA_CACHE_ENABLE_LLM_CACHE", "true").lower() == "true"
        )
        ttl_hours = float(os.environ.get("RSPA_CACHE_LLM_CACHE_TTL_HOURS", "24"))
        max_size_mb = float(os.environ.get("RSPA_CACHE_LLM_CACHE_MAX_SIZE_MB", "100"))

        _llm_cache = LLMCache(
            enabled=enabled, ttl_hours=ttl_hours, max_size_mb=max_size_mb
        )

    return _llm_cache


def clear_llm_cache() -> None:
    """Clear the global LLM cache."""
    cache = get_llm_cache()
    cache.clear()

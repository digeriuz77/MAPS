"""
Redis Caching Service for Performance Optimization

Provides caching layer to reduce database load and improve response times.
Designed for 500-1000 concurrent users.
"""
import json
import logging
import hashlib
from typing import Optional, Any, Callable, TypeVar
from functools import wraps
import asyncio

logger = logging.getLogger(__name__)

# Type variable for generic return types
T = TypeVar('T')

# Global Redis client (lazy initialized)
_redis_client = None
_redis_available = None


def get_redis_client():
    """
    Get Redis client instance with lazy initialization.
    Falls back gracefully if Redis is unavailable.
    """
    global _redis_client, _redis_available

    if _redis_available is False:
        return None

    if _redis_client is not None:
        return _redis_client

    try:
        import redis
        from src.config.settings import get_settings
        settings = get_settings()

        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info("✅ Redis cache connected successfully")
        return _redis_client
    except ImportError:
        logger.warning("redis-py not installed, caching disabled")
        _redis_available = False
        return None
    except Exception as e:
        logger.warning(f"Redis connection failed, caching disabled: {e}")
        _redis_available = False
        return None


def cache_key(*args, prefix: str = "maps") -> str:
    """Generate a consistent cache key from arguments."""
    key_data = json.dumps(args, sort_keys=True, default=str)
    key_hash = hashlib.md5(key_data.encode()).hexdigest()[:12]
    return f"{prefix}:{key_hash}"


class CacheService:
    """
    Centralized caching service with TTL management.

    Cache TTL Guidelines:
    - Modules: 1 hour (rarely change)
    - Learning paths: 1 hour (rarely change)
    - Focus areas/metadata: 1 day (static)
    - User progress: 5 minutes (changes after attempts)
    - Dialogue structures: 1 hour (immutable once published)
    """

    # TTL constants (in seconds)
    TTL_SHORT = 300        # 5 minutes - user-specific volatile data
    TTL_MEDIUM = 3600      # 1 hour - module data
    TTL_LONG = 86400       # 1 day - static metadata

    # Cache key prefixes
    PREFIX_MODULE = "mi:mod"
    PREFIX_MODULES_LIST = "mi:mods"
    PREFIX_PATHS = "mi:paths"
    PREFIX_METADATA = "mi:meta"
    PREFIX_PROGRESS = "mi:prog"
    PREFIX_DIALOGUE = "mi:dlg"

    def __init__(self):
        self.redis = get_redis_client()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis:
            return None
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.debug(f"Cache get failed for {key}: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = TTL_MEDIUM) -> bool:
        """Set value in cache with TTL."""
        if not self.redis:
            return False
        try:
            self.redis.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.debug(f"Cache set failed for {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis:
            return False
        try:
            self.redis.delete(key)
            return True
        except Exception as e:
            logger.debug(f"Cache delete failed for {key}: {e}")
            return False

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.redis:
            return 0
        try:
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys)
            return 0
        except Exception as e:
            logger.debug(f"Cache delete pattern failed for {pattern}: {e}")
            return 0

    # ============================================
    # MODULE CACHING
    # ============================================

    def module_key(self, module_id: str) -> str:
        """Generate cache key for a single module."""
        return f"{self.PREFIX_MODULE}:{module_id}"

    def modules_list_key(self, content_type: str = None, focus_area: str = None,
                         difficulty: str = None) -> str:
        """Generate cache key for modules list with filters."""
        filters = f"{content_type or 'all'}:{focus_area or 'all'}:{difficulty or 'all'}"
        return f"{self.PREFIX_MODULES_LIST}:{filters}"

    def dialogue_key(self, module_id: str) -> str:
        """Generate cache key for dialogue structure (large JSON)."""
        return f"{self.PREFIX_DIALOGUE}:{module_id}"

    async def get_module(self, module_id: str) -> Optional[dict]:
        """Get cached module data."""
        return await self.get(self.module_key(module_id))

    async def set_module(self, module_id: str, module_data: dict) -> bool:
        """Cache module data (without dialogue structure)."""
        return await self.set(self.module_key(module_id), module_data, self.TTL_MEDIUM)

    async def get_dialogue_structure(self, module_id: str) -> Optional[dict]:
        """Get cached dialogue structure."""
        return await self.get(self.dialogue_key(module_id))

    async def set_dialogue_structure(self, module_id: str, dialogue: dict) -> bool:
        """Cache dialogue structure separately (large JSON)."""
        return await self.set(self.dialogue_key(module_id), dialogue, self.TTL_MEDIUM)

    async def invalidate_module(self, module_id: str) -> None:
        """Invalidate module and related caches."""
        await self.delete(self.module_key(module_id))
        await self.delete(self.dialogue_key(module_id))
        # Also invalidate list caches
        await self.delete_pattern(f"{self.PREFIX_MODULES_LIST}:*")

    # ============================================
    # METADATA CACHING (focus areas, content types, difficulty levels)
    # ============================================

    def metadata_key(self, metadata_type: str) -> str:
        """Generate cache key for metadata."""
        return f"{self.PREFIX_METADATA}:{metadata_type}"

    async def get_metadata(self, metadata_type: str) -> Optional[list]:
        """Get cached metadata (focus areas, content types, etc.)."""
        return await self.get(self.metadata_key(metadata_type))

    async def set_metadata(self, metadata_type: str, data: list) -> bool:
        """Cache metadata with long TTL (rarely changes)."""
        return await self.set(self.metadata_key(metadata_type), data, self.TTL_LONG)

    # ============================================
    # LEARNING PATHS CACHING
    # ============================================

    def paths_key(self) -> str:
        """Generate cache key for learning paths list."""
        return f"{self.PREFIX_PATHS}:list"

    def path_key(self, path_id: str) -> str:
        """Generate cache key for single learning path."""
        return f"{self.PREFIX_PATHS}:{path_id}"

    async def get_learning_paths(self) -> Optional[list]:
        """Get cached learning paths."""
        return await self.get(self.paths_key())

    async def set_learning_paths(self, paths: list) -> bool:
        """Cache learning paths list."""
        return await self.set(self.paths_key(), paths, self.TTL_MEDIUM)

    async def get_learning_path(self, path_id: str) -> Optional[dict]:
        """Get cached single learning path."""
        return await self.get(self.path_key(path_id))

    async def set_learning_path(self, path_id: str, path_data: dict) -> bool:
        """Cache single learning path."""
        return await self.set(self.path_key(path_id), path_data, self.TTL_MEDIUM)

    # ============================================
    # USER PROGRESS CACHING (short TTL)
    # ============================================

    def progress_key(self, user_id: str) -> str:
        """Generate cache key for user progress."""
        return f"{self.PREFIX_PROGRESS}:{user_id}"

    def batch_progress_key(self, user_id: str) -> str:
        """Generate cache key for user's module progress batch."""
        return f"{self.PREFIX_PROGRESS}:batch:{user_id}"

    async def get_user_progress(self, user_id: str) -> Optional[dict]:
        """Get cached user progress."""
        return await self.get(self.progress_key(user_id))

    async def set_user_progress(self, user_id: str, progress: dict) -> bool:
        """Cache user progress with short TTL."""
        return await self.set(self.progress_key(user_id), progress, self.TTL_SHORT)

    async def invalidate_user_progress(self, user_id: str) -> None:
        """Invalidate user progress cache after attempt completion."""
        await self.delete(self.progress_key(user_id))
        await self.delete(self.batch_progress_key(user_id))

    async def get_batch_module_progress(self, user_id: str) -> Optional[dict]:
        """Get cached batch module progress for user."""
        return await self.get(self.batch_progress_key(user_id))

    async def set_batch_module_progress(self, user_id: str, progress_map: dict) -> bool:
        """Cache batch module progress (module_id -> progress)."""
        return await self.set(self.batch_progress_key(user_id), progress_map, self.TTL_SHORT)


# Global cache service instance
_cache_service = None


def get_cache_service() -> CacheService:
    """Get singleton cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service


def cached(prefix: str, ttl: int = CacheService.TTL_MEDIUM, key_func: Callable = None):
    """
    Decorator for caching async function results.

    Usage:
        @cached("modules", ttl=3600)
        async def get_modules(self, content_type=None):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_service()

            # Generate cache key
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                # Default: use function name and relevant args
                key_parts = [prefix, func.__name__]
                # Skip 'self' argument
                for arg in args[1:]:
                    key_parts.append(str(arg))
                for k, v in sorted(kwargs.items()):
                    if v is not None:
                        key_parts.append(f"{k}={v}")
                cache_key = ":".join(key_parts)

            # Try cache first
            cached_result = await cache.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_result

            # Cache miss - call function
            logger.debug(f"Cache MISS: {cache_key}")
            result = await func(*args, **kwargs)

            # Cache the result
            if result is not None:
                await cache.set(cache_key, result, ttl)

            return result
        return wrapper
    return decorator

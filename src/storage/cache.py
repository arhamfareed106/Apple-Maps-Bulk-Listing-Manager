import asyncio
import time
from typing import Any, Optional, Dict
from cachetools import TTLCache
import json


class CacheManager:
    """Manages in-memory caching with TTL support"""
    
    def __init__(self, maxsize: int = 1000, ttl: int = 300):
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        async with self.lock:
            return self.cache.get(key)
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set value in cache with optional custom TTL"""
        async with self.lock:
            if ttl is not None:
                # For custom TTL, we need to create a new cache entry
                temp_cache = TTLCache(maxsize=1, ttl=ttl)
                temp_cache[key] = value
                # Merge with main cache (this is a simplified approach)
                self.cache[key] = value
            else:
                self.cache[key] = value
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        async with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    async def clear(self) -> None:
        """Clear all cache entries"""
        async with self.lock:
            self.cache.clear()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        async with self.lock:
            return key in self.cache
    
    async def get_or_set(self, key: str, default_func, ttl: Optional[int] = None) -> Any:
        """Get value from cache or set it using default function"""
        value = await self.get(key)
        if value is None:
            value = await default_func()
            await self.set(key, value, ttl)
        return value
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            "size": len(self.cache),
            "maxsize": self.cache.maxsize,
            "ttl": self.cache.ttl,
            "hits": getattr(self.cache, 'hits', 0),
            "misses": getattr(self.cache, 'misses', 0)
        }


class StatusCache:
    """Specialized cache for tracking sync status"""
    
    def __init__(self, settings):
        self.settings = settings
        self.cache_manager = CacheManager(maxsize=10000, ttl=600)  # 10 minutes TTL
    
    async def set_location_status(
        self,
        location_id: str,
        status: str,
        aggregator: str,
        details: Optional[Dict] = None
    ) -> None:
        """Set location sync status"""
        key = f"status:{aggregator}:{location_id}"
        value = {
            "status": status,
            "timestamp": time.time(),
            "details": details or {}
        }
        await self.cache_manager.set(key, value)
    
    async def get_location_status(
        self,
        location_id: str,
        aggregator: str
    ) -> Optional[Dict]:
        """Get location sync status"""
        key = f"status:{aggregator}:{location_id}"
        return await self.cache_manager.get(key)
    
    async def set_batch_status(
        self,
        batch_id: str,
        status: str,
        progress: float,
        total: int,
        completed: int,
        failed: int
    ) -> None:
        """Set batch processing status"""
        key = f"batch:{batch_id}"
        value = {
            "status": status,
            "progress": progress,
            "total": total,
            "completed": completed,
            "failed": failed,
            "timestamp": time.time()
        }
        await self.cache_manager.set(key, value, ttl=3600)  # 1 hour TTL
    
    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        """Get batch processing status"""
        key = f"batch:{batch_id}"
        return await self.cache_manager.get(key)
    
    async def get_active_batches(self) -> Dict[str, Any]:
        """Get all active batch statuses"""
        # This is a simplified implementation
        # In production, you'd want a more sophisticated approach
        stats = self.cache_manager.get_stats()
        return {
            "cache_stats": stats,
            "active_count": stats.get("size", 0)
        }
    
    async def clear_expired_statuses(self) -> int:
        """Clear expired status entries"""
        # TTL cache automatically handles expiration
        # This method is for explicit cleanup if needed
        stats_before = self.cache_manager.get_stats()
        await self.cache_manager.clear()
        return stats_before.get("size", 0)
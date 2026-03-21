"""Caching system for agent responses and case content."""

import time
from typing import Optional, Any, Dict
from dataclasses import dataclass
import logging

logger = logging.getLogger("veritas")


@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""
    
    value: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    
    def is_expired(self) -> bool:
        """Check if this cache entry has expired."""
        return time.time() - self.timestamp > self.ttl


class TTLCache:
    """
    Time-To-Live cache implementation.
    
    Stores key-value pairs with automatic expiration based on TTL.
    Thread-safe for async operations.
    """
    
    def __init__(self, default_ttl: float = 3600):
        """
        Initialize TTL cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 1 hour)
        """
        self.default_ttl = default_ttl
        self._cache: Dict[str, CacheEntry] = {}
        self._hits = 0
        self._misses = 0
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value if exists and not expired, None otherwise
        """
        if key not in self._cache:
            self._misses += 1
            return None
        
        entry = self._cache[key]
        
        # Check if expired
        if entry.is_expired():
            logger.debug(f"Cache entry expired: {key}")
            del self._cache[key]
            self._misses += 1
            return None
        
        self._hits += 1
        logger.debug(f"Cache hit: {key}")
        return entry.value
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        ttl = ttl if ttl is not None else self.default_ttl
        self._cache[key] = CacheEntry(
            value=value,
            timestamp=time.time(),
            ttl=ttl
        )
        logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str):
        """
        Delete entry from cache.
        
        Args:
            key: Cache key to delete
        """
        if key in self._cache:
            del self._cache[key]
            logger.debug(f"Cache deleted: {key}")
    
    def clear(self):
        """Clear all cache entries."""
        self._cache.clear()
        self._hits = 0
        self._misses = 0
        logger.debug("Cache cleared")
    
    def cleanup_expired(self):
        """Remove all expired entries from cache."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats (hits, misses, size, hit_rate)
        """
        total = self._hits + self._misses
        hit_rate = (self._hits / total * 100) if total > 0 else 0
        
        return {
            "hits": self._hits,
            "misses": self._misses,
            "size": len(self._cache),
            "hit_rate": f"{hit_rate:.2f}%"
        }


class ResponseCache:
    """
    Cache for LLM agent responses and fallback responses.
    
    Provides specialized caching for common agent responses
    with appropriate TTL values.
    """
    
    # TTL values for different response types (in seconds)
    FALLBACK_TTL = 86400  # 24 hours - fallback responses rarely change
    CASE_CONTENT_TTL = 3600  # 1 hour - case content is static but may be updated
    AGENT_RESPONSE_TTL = 300  # 5 minutes - agent responses for similar prompts
    
    def __init__(self):
        """Initialize response cache with separate caches for different types."""
        self.fallback_cache = TTLCache(default_ttl=self.FALLBACK_TTL)
        self.case_cache = TTLCache(default_ttl=self.CASE_CONTENT_TTL)
        self.agent_cache = TTLCache(default_ttl=self.AGENT_RESPONSE_TTL)
    
    def get_fallback(self, agent_role: str, stage: str) -> Optional[str]:
        """
        Get cached fallback response for an agent at a specific stage.
        
        Args:
            agent_role: Role of the agent (e.g., "prosecution", "defence")
            stage: Trial stage (e.g., "opening", "closing")
            
        Returns:
            Cached fallback response if exists, None otherwise
        """
        key = f"fallback:{agent_role}:{stage}"
        return self.fallback_cache.get(key)
    
    def set_fallback(self, agent_role: str, stage: str, response: str):
        """
        Cache fallback response for an agent at a specific stage.
        
        Args:
            agent_role: Role of the agent
            stage: Trial stage
            response: Fallback response text
        """
        key = f"fallback:{agent_role}:{stage}"
        self.fallback_cache.set(key, response)
    
    def get_case_content(self, case_id: str) -> Optional[Any]:
        """
        Get cached case content.
        
        Args:
            case_id: Case identifier
            
        Returns:
            Cached case content if exists, None otherwise
        """
        key = f"case:{case_id}"
        return self.case_cache.get(key)
    
    def set_case_content(self, case_id: str, content: Any):
        """
        Cache case content.
        
        Args:
            case_id: Case identifier
            content: Case content object
        """
        key = f"case:{case_id}"
        self.case_cache.set(key, content)
    
    def get_agent_response(self, agent_role: str, prompt_hash: str) -> Optional[str]:
        """
        Get cached agent response for a specific prompt.
        
        Args:
            agent_role: Role of the agent
            prompt_hash: Hash of the prompt (to identify similar prompts)
            
        Returns:
            Cached agent response if exists, None otherwise
        """
        key = f"agent:{agent_role}:{prompt_hash}"
        return self.agent_cache.get(key)
    
    def set_agent_response(self, agent_role: str, prompt_hash: str, response: str):
        """
        Cache agent response for a specific prompt.
        
        Args:
            agent_role: Role of the agent
            prompt_hash: Hash of the prompt
            response: Agent response text
        """
        key = f"agent:{agent_role}:{prompt_hash}"
        self.agent_cache.set(key, response)
    
    def cleanup_all(self):
        """Clean up expired entries from all caches."""
        self.fallback_cache.cleanup_expired()
        self.case_cache.cleanup_expired()
        self.agent_cache.cleanup_expired()
    
    def clear_all(self):
        """Clear all caches."""
        self.fallback_cache.clear()
        self.case_cache.clear()
        self.agent_cache.clear()
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics for all caches.
        
        Returns:
            Dictionary with stats for each cache type
        """
        return {
            "fallback_cache": self.fallback_cache.get_stats(),
            "case_cache": self.case_cache.get_stats(),
            "agent_cache": self.agent_cache.get_stats()
        }


# Global cache instance
_response_cache: Optional[ResponseCache] = None


def get_response_cache() -> ResponseCache:
    """
    Get the global response cache instance.
    
    Returns:
        Global ResponseCache instance
    """
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache()
    return _response_cache



# Background cleanup task
import asyncio


async def cache_cleanup_task(interval: int = 300):
    """
    Background task to periodically clean up expired cache entries.
    
    Args:
        interval: Cleanup interval in seconds (default: 5 minutes)
    """
    cache = get_response_cache()
    
    while True:
        try:
            await asyncio.sleep(interval)
            logger.info("Running scheduled cache cleanup...")
            cache.cleanup_all()
            
            # Log stats after cleanup
            stats = cache.get_all_stats()
            logger.info(f"Cache stats after cleanup: {stats}")
        except asyncio.CancelledError:
            logger.info("Cache cleanup task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in cache cleanup task: {e}")

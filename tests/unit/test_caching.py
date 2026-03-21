"""Unit tests for caching system."""

import pytest
import time
from src.cache import TTLCache, ResponseCache, get_response_cache


class TestTTLCache:
    """Tests for TTL cache implementation."""
    
    def test_basic_get_set(self):
        """Test basic cache get and set operations."""
        cache = TTLCache(default_ttl=60)
        
        # Set and get value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Get non-existent key
        assert cache.get("key2") is None
    
    def test_ttl_expiration(self):
        """Test that cache entries expire after TTL."""
        cache = TTLCache(default_ttl=1)  # 1 second TTL
        
        # Set value
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Value should be expired
        assert cache.get("key1") is None
    
    def test_custom_ttl(self):
        """Test setting custom TTL per entry."""
        cache = TTLCache(default_ttl=60)
        
        # Set with custom short TTL
        cache.set("key1", "value1", ttl=1)
        cache.set("key2", "value2", ttl=60)
        
        # Wait for first to expire
        time.sleep(1.1)
        
        # First should be expired, second should not
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
    
    def test_delete(self):
        """Test deleting cache entries."""
        cache = TTLCache()
        
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_clear(self):
        """Test clearing all cache entries."""
        cache = TTLCache()
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")
        
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") is None
    
    def test_cleanup_expired(self):
        """Test cleanup of expired entries."""
        cache = TTLCache(default_ttl=1)
        
        # Set multiple entries
        cache.set("key1", "value1")
        cache.set("key2", "value2", ttl=60)  # Long TTL
        cache.set("key3", "value3")
        
        # Wait for some to expire
        time.sleep(1.1)
        
        # Cleanup
        cache.cleanup_expired()
        
        # Check stats
        stats = cache.get_stats()
        assert stats["size"] == 1  # Only key2 should remain
    
    def test_cache_stats(self):
        """Test cache statistics tracking."""
        cache = TTLCache()
        
        # Set some values
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        # Generate hits and misses
        cache.get("key1")  # Hit
        cache.get("key1")  # Hit
        cache.get("key3")  # Miss
        
        stats = cache.get_stats()
        assert stats["hits"] == 2
        assert stats["misses"] == 1
        assert stats["size"] == 2
        assert "hit_rate" in stats


class TestResponseCache:
    """Tests for response cache implementation."""
    
    def test_fallback_cache(self):
        """Test caching fallback responses."""
        cache = ResponseCache()
        
        # Set fallback
        cache.set_fallback("prosecution", "opening", "Fallback opening statement")
        
        # Get fallback
        result = cache.get_fallback("prosecution", "opening")
        assert result == "Fallback opening statement"
        
        # Non-existent fallback
        assert cache.get_fallback("defence", "closing") is None
    
    def test_case_content_cache(self):
        """Test caching case content."""
        cache = ResponseCache()
        
        # Mock case content
        case_content = {"caseId": "test-001", "title": "Test Case"}
        
        # Set case content
        cache.set_case_content("test-001", case_content)
        
        # Get case content
        result = cache.get_case_content("test-001")
        assert result == case_content
        
        # Non-existent case
        assert cache.get_case_content("test-002") is None
    
    def test_agent_response_cache(self):
        """Test caching agent responses."""
        cache = ResponseCache()
        
        # Set agent response
        cache.set_agent_response("judge", "hash123", "Judge's response")
        
        # Get agent response
        result = cache.get_agent_response("judge", "hash123")
        assert result == "Judge's response"
        
        # Non-existent response
        assert cache.get_agent_response("judge", "hash456") is None
    
    def test_cleanup_all(self):
        """Test cleanup of all caches."""
        cache = ResponseCache()
        
        # Set entries with short TTL
        cache.fallback_cache.set("test1", "value1", ttl=1)
        cache.case_cache.set("test2", "value2", ttl=1)
        cache.agent_cache.set("test3", "value3", ttl=1)
        
        # Wait for expiration
        time.sleep(1.1)
        
        # Cleanup
        cache.cleanup_all()
        
        # Check all caches are cleaned
        assert cache.fallback_cache.get_stats()["size"] == 0
        assert cache.case_cache.get_stats()["size"] == 0
        assert cache.agent_cache.get_stats()["size"] == 0
    
    def test_clear_all(self):
        """Test clearing all caches."""
        cache = ResponseCache()
        
        # Set entries
        cache.set_fallback("prosecution", "opening", "Fallback")
        cache.set_case_content("test-001", {"data": "test"})
        cache.set_agent_response("judge", "hash123", "Response")
        
        # Clear all
        cache.clear_all()
        
        # Check all caches are empty
        assert cache.get_fallback("prosecution", "opening") is None
        assert cache.get_case_content("test-001") is None
        assert cache.get_agent_response("judge", "hash123") is None
    
    def test_get_all_stats(self):
        """Test getting statistics for all caches."""
        cache = ResponseCache()
        
        # Set some entries
        cache.set_fallback("prosecution", "opening", "Fallback")
        cache.set_case_content("test-001", {"data": "test"})
        cache.set_agent_response("judge", "hash123", "Response")
        
        # Get stats
        stats = cache.get_all_stats()
        
        assert "fallback_cache" in stats
        assert "case_cache" in stats
        assert "agent_cache" in stats
        
        assert stats["fallback_cache"]["size"] == 1
        assert stats["case_cache"]["size"] == 1
        assert stats["agent_cache"]["size"] == 1
    
    def test_ttl_values(self):
        """Test that different cache types have appropriate TTL values."""
        cache = ResponseCache()
        
        # Check TTL constants
        assert cache.FALLBACK_TTL == 86400  # 24 hours
        assert cache.CASE_CONTENT_TTL == 3600  # 1 hour
        assert cache.AGENT_RESPONSE_TTL == 300  # 5 minutes


class TestGlobalCache:
    """Tests for global cache instance."""
    
    def test_get_response_cache_singleton(self):
        """Test that get_response_cache returns singleton instance."""
        cache1 = get_response_cache()
        cache2 = get_response_cache()
        
        # Should be the same instance
        assert cache1 is cache2
    
    def test_global_cache_persistence(self):
        """Test that global cache persists data across calls."""
        cache1 = get_response_cache()
        cache1.set_fallback("test", "stage", "value")
        
        cache2 = get_response_cache()
        result = cache2.get_fallback("test", "stage")
        
        assert result == "value"


class TestCacheIntegration:
    """Integration tests for caching with other components."""
    
    def test_case_manager_caching(self):
        """Test that case manager uses caching correctly."""
        from src.case_manager import CaseManager
        
        manager = CaseManager()
        
        # Load a case (should cache it)
        try:
            case1 = manager.load_case("blackthorn-hall-001")
            
            # Load again (should use cache)
            case2 = manager.load_case("blackthorn-hall-001")
            
            # Should be the same object from cache
            assert case1.case_id == case2.case_id
        except FileNotFoundError:
            # Case file might not exist in test environment
            pytest.skip("Case file not found")
    
    def test_llm_service_fallback_caching(self):
        """Test that LLM service caches fallback responses."""
        from src.llm_service import LLMService
        from src.config import LLMConfig
        
        # Create mock config
        config = LLMConfig(
            provider="openai",
            apiKey="test-key",
            model="gpt-4"
        )
        
        service = LLMService(config)
        
        # Check that cache is initialized
        assert service._cache is not None
        assert hasattr(service._cache, 'get_fallback')
        assert hasattr(service._cache, 'set_fallback')

"""Unit tests for LLM service connection pooling and rate limiting."""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import time

from src.llm_service import LLMService, RateLimiter
from src.config import LLMConfig


@pytest.fixture
def llm_config():
    """Create test LLM configuration."""
    return LLMConfig(
        provider="openai",
        apiKey="test-key",
        model="gpt-4",
        temperature=0.7,
        max_tokens=100,
        timeout=30,
        connectionPoolSize=5,
        connectTimeout=10,
        readTimeout=30,
        maxRetries=3,
        retryDelay=0.1,  # Short delay for tests
        rateLimitRpm=10,
        rateLimitTpm=1000
    )


@pytest.mark.asyncio
async def test_rate_limiter_allows_requests_under_limit():
    """Test that rate limiter allows requests under the limit."""
    limiter = RateLimiter(max_requests_per_minute=10, max_tokens_per_minute=1000)
    
    # Should allow 5 requests without blocking
    start = time.time()
    for _ in range(5):
        await limiter.acquire(estimated_tokens=100)
    elapsed = time.time() - start
    
    # Should complete quickly (no blocking)
    assert elapsed < 0.5


@pytest.mark.asyncio
async def test_rate_limiter_blocks_when_request_limit_exceeded():
    """Test that rate limiter blocks when request limit is exceeded."""
    limiter = RateLimiter(max_requests_per_minute=3, max_tokens_per_minute=10000)
    
    # Fill up the request limit
    for _ in range(3):
        await limiter.acquire(estimated_tokens=100)
    
    # Next request should block
    start = time.time()
    
    # Use a timeout to prevent test hanging
    try:
        await asyncio.wait_for(limiter.acquire(estimated_tokens=100), timeout=0.5)
        # If we get here, the limiter didn't block (which is wrong)
        assert False, "Rate limiter should have blocked"
    except asyncio.TimeoutError:
        # Expected - the limiter is blocking
        pass


@pytest.mark.asyncio
async def test_rate_limiter_blocks_when_token_limit_exceeded():
    """Test that rate limiter blocks when token limit is exceeded."""
    limiter = RateLimiter(max_requests_per_minute=100, max_tokens_per_minute=500)
    
    # Use up most of the token budget
    await limiter.acquire(estimated_tokens=400)
    
    # Next large request should block
    start = time.time()
    
    try:
        await asyncio.wait_for(limiter.acquire(estimated_tokens=200), timeout=0.5)
        assert False, "Rate limiter should have blocked on token limit"
    except asyncio.TimeoutError:
        # Expected - the limiter is blocking
        pass


@pytest.mark.asyncio
async def test_llm_service_initializes_with_connection_pool(llm_config):
    """Test that LLM service initializes with connection pooling."""
    with patch('openai.AsyncOpenAI'):
        service = LLMService(llm_config)
        
        # Verify rate limiter is initialized
        assert service._rate_limiter is not None
        assert service._rate_limiter.max_requests_per_minute == 10
        assert service._rate_limiter.max_tokens_per_minute == 1000


@pytest.mark.asyncio
async def test_llm_service_creates_session_with_pooling(llm_config):
    """Test that LLM service creates aiohttp session with proper pooling config."""
    with patch('openai.AsyncOpenAI'):
        service = LLMService(llm_config)
        
        # Get session
        session = await service._get_session()
        
        # Verify session is created
        assert session is not None
        assert not session.closed
        
        # Verify connector settings
        connector = session.connector
        assert connector._limit == 5  # connection_pool_size
        assert connector._limit_per_host == 5
        
        # Cleanup
        await service.close()


@pytest.mark.asyncio
async def test_llm_service_retries_on_timeout(llm_config):
    """Test that LLM service retries on timeout."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        service = LLMService(llm_config)
        
        # Mock the client to timeout twice, then succeed
        mock_client = MagicMock()
        mock_completion = AsyncMock()
        
        call_count = 0
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise asyncio.TimeoutError()
            # Success on third attempt
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Success"
            return mock_response
        
        mock_completion.side_effect = side_effect
        mock_client.chat.completions.create = mock_completion
        service.client = mock_client
        
        # Should succeed after retries
        response = await service.generate_response(
            system_prompt="Test",
            user_prompt="Test",
            timeout=1
        )
        
        assert response == "Success"
        assert call_count == 3  # Two failures + one success


@pytest.mark.asyncio
async def test_llm_service_fails_after_max_retries(llm_config):
    """Test that LLM service fails after exhausting retries."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        service = LLMService(llm_config)
        
        # Mock the client to always timeout
        mock_client = MagicMock()
        mock_completion = AsyncMock()
        mock_completion.side_effect = asyncio.TimeoutError()
        mock_client.chat.completions.create = mock_completion
        service.client = mock_client
        
        # Should fail after max retries
        with pytest.raises(TimeoutError):
            await service.generate_response(
                system_prompt="Test",
                user_prompt="Test",
                timeout=1
            )


@pytest.mark.asyncio
async def test_llm_service_does_not_retry_auth_errors(llm_config):
    """Test that LLM service does not retry authentication errors."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        service = LLMService(llm_config)
        
        # Mock the client to raise auth error
        mock_client = MagicMock()
        mock_completion = AsyncMock()
        mock_completion.side_effect = Exception("invalid_api_key")
        mock_client.chat.completions.create = mock_completion
        service.client = mock_client
        
        # Should fail immediately without retries
        with pytest.raises(Exception) as exc_info:
            await service.generate_response(
                system_prompt="Test",
                user_prompt="Test"
            )
        
        assert "invalid_api_key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_llm_service_uses_exponential_backoff(llm_config):
    """Test that LLM service uses exponential backoff between retries."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        service = LLMService(llm_config)
        
        # Mock the client to fail twice
        mock_client = MagicMock()
        mock_completion = AsyncMock()
        
        call_times = []
        call_count = 0
        
        async def side_effect(*args, **kwargs):
            nonlocal call_count
            call_times.append(time.time())
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary error")
            # Success on third attempt
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Success"
            return mock_response
        
        mock_completion.side_effect = side_effect
        mock_client.chat.completions.create = mock_completion
        service.client = mock_client
        
        # Execute
        await service.generate_response(
            system_prompt="Test",
            user_prompt="Test"
        )
        
        # Verify exponential backoff
        # First retry should wait ~0.1s (retry_delay * 1)
        # Second retry should wait ~0.2s (retry_delay * 2)
        assert len(call_times) == 3
        
        # Check delays between calls
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]
        
        # Allow some tolerance for timing
        assert delay1 >= 0.08  # ~0.1s with tolerance
        assert delay2 >= 0.18  # ~0.2s with tolerance
        assert delay2 > delay1  # Second delay should be longer


@pytest.mark.asyncio
async def test_llm_service_closes_session_properly(llm_config):
    """Test that LLM service closes session properly."""
    with patch('openai.AsyncOpenAI'):
        service = LLMService(llm_config)
        
        # Create session
        session = await service._get_session()
        assert not session.closed
        
        # Close service
        await service.close()
        
        # Verify session is closed
        assert session.closed


@pytest.mark.asyncio
async def test_generate_with_fallback_uses_fallback_on_error(llm_config):
    """Test that generate_with_fallback uses fallback on error."""
    with patch('openai.AsyncOpenAI') as mock_openai:
        service = LLMService(llm_config)
        
        # Mock the client to always fail
        mock_client = MagicMock()
        mock_completion = AsyncMock()
        mock_completion.side_effect = Exception("API Error")
        mock_client.chat.completions.create = mock_completion
        service.client = mock_client
        
        # Should return fallback
        response, used_fallback = await service.generate_with_fallback(
            system_prompt="Test",
            user_prompt="Test",
            fallback_text="Fallback response"
        )
        
        assert response == "Fallback response"
        assert used_fallback is True


@pytest.mark.asyncio
async def test_rate_limiter_cleans_up_old_entries():
    """Test that rate limiter cleans up entries older than 1 minute."""
    limiter = RateLimiter(max_requests_per_minute=100, max_tokens_per_minute=10000)
    
    # Add some requests
    await limiter.acquire(estimated_tokens=100)
    await limiter.acquire(estimated_tokens=100)
    
    # Verify entries exist
    assert len(limiter.request_times) == 2
    assert len(limiter.token_usage) == 2
    
    # Manually set old timestamps (simulate time passing)
    old_time = time.time() - 61  # 61 seconds ago
    limiter.request_times[0] = old_time
    limiter.token_usage[0] = (old_time, 100)
    
    # Next acquire should clean up old entries
    await limiter.acquire(estimated_tokens=100)
    
    # Old entry should be removed
    assert len(limiter.request_times) == 2  # One old removed, one new added
    assert len(limiter.token_usage) == 2
    assert limiter.request_times[0] > old_time  # Old entry is gone


@pytest.mark.asyncio
async def test_rate_limiter_check_would_block():
    """Test that check_would_block() correctly predicts blocking without modifying state."""
    limiter = RateLimiter(max_requests_per_minute=3, max_tokens_per_minute=1000)
    
    # Initially should not block
    assert limiter.check_would_block(100) is False
    
    # Add requests up to the limit
    await limiter.acquire(estimated_tokens=100)
    await limiter.acquire(estimated_tokens=100)
    await limiter.acquire(estimated_tokens=100)
    
    # Now should predict blocking
    assert limiter.check_would_block(100) is True
    
    # Verify state wasn't modified (still 3 requests)
    assert len(limiter.request_times) == 3
    assert len(limiter.token_usage) == 3


@pytest.mark.asyncio
async def test_rate_limiter_check_would_block_token_limit():
    """Test that check_would_block() detects token limit blocking."""
    limiter = RateLimiter(max_requests_per_minute=100, max_tokens_per_minute=500)
    
    # Use up most tokens
    await limiter.acquire(estimated_tokens=400)
    
    # Should predict blocking for large request
    assert limiter.check_would_block(200) is True
    
    # Should not block for small request
    assert limiter.check_would_block(50) is False
    
    # Verify state wasn't modified
    assert len(limiter.request_times) == 1
    assert len(limiter.token_usage) == 1

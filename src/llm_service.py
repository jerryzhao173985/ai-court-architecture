"""LLM service for generating AI agent responses."""

import asyncio
from typing import Optional, Literal
import logging
import aiohttp
from aiohttp import ClientTimeout, TCPConnector
import time
from collections import deque
import hashlib

from config import LLMConfig
from cache import get_response_cache

logger = logging.getLogger("veritas")


class RateLimiter:
    """
    Token bucket rate limiter for API calls.
    
    Tracks both request count and token usage to prevent
    API quota exhaustion.
    """
    
    def __init__(self, max_requests_per_minute: int, max_tokens_per_minute: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests_per_minute: Maximum API requests per minute
            max_tokens_per_minute: Maximum tokens per minute
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.max_tokens_per_minute = max_tokens_per_minute
        self.request_times: deque = deque()
        self.token_usage: deque = deque()  # (timestamp, token_count) tuples
        self._lock = asyncio.Lock()
    
    async def acquire(self, estimated_tokens: int = 1000):
        """
        Acquire permission to make an API call.

        Blocks until rate limits allow the request.

        Args:
            estimated_tokens: Estimated token count for this request
        """
        while True:
            wait_time = 0.0

            async with self._lock:
                now = time.time()

                # Clean up old entries (older than 1 minute)
                cutoff = now - 60
                while self.request_times and self.request_times[0] < cutoff:
                    self.request_times.popleft()
                while self.token_usage and self.token_usage[0][0] < cutoff:
                    self.token_usage.popleft()

                # Check request rate limit
                if len(self.request_times) >= self.max_requests_per_minute:
                    wait_time = 60 - (now - self.request_times[0])
                    if wait_time > 0:
                        logger.info(f"Rate limit reached, waiting {wait_time:.2f}s")
                    else:
                        wait_time = 0.0

                # Check token rate limit (only if request limit ok)
                if wait_time <= 0:
                    current_tokens = sum(count for _, count in self.token_usage)
                    if current_tokens + estimated_tokens > self.max_tokens_per_minute:
                        wait_time = 60 - (now - self.token_usage[0][0]) if self.token_usage else 0
                        if wait_time > 0:
                            logger.info(f"Token rate limit reached, waiting {wait_time:.2f}s")
                        else:
                            wait_time = 0.0

                # If no waiting needed, record and return
                if wait_time <= 0:
                    self.request_times.append(now)
                    self.token_usage.append((now, estimated_tokens))
                    return

            # Sleep OUTSIDE the lock, then loop to re-check
            await asyncio.sleep(wait_time)
    
    def record_actual_tokens(self, estimated_tokens: int, actual_tokens: int):
        """
        Update token usage with actual count.
        
        Args:
            estimated_tokens: Previously estimated token count
            actual_tokens: Actual token count from API response
        """
        # Find and update the most recent matching estimate
        for i in range(len(self.token_usage) - 1, -1, -1):
            timestamp, count = self.token_usage[i]
            if count == estimated_tokens:
                self.token_usage[i] = (timestamp, actual_tokens)
                break


class LLMService:
    """
    Service for interacting with LLM APIs (OpenAI or Anthropic).
    
    Handles prompt generation, API calls, response parsing,
    and error handling with fallbacks.
    
    Implements connection pooling, rate limiting, and retry logic
    for production-grade performance and reliability.
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize LLM service.
        
        Args:
            config: LLM configuration
        """
        self.config = config
        self.provider = config.provider
        self.client = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = RateLimiter(
            max_requests_per_minute=config.rate_limit_rpm,
            max_tokens_per_minute=config.rate_limit_tpm
        )
        self._cache = get_response_cache()
        
        # Initialize the appropriate client
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the LLM client based on provider."""
        try:
            if self.provider == "openai":
                import openai
                self.client = openai.AsyncOpenAI(api_key=self.config.api_key)
            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.AsyncAnthropic(api_key=self.config.api_key)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except ImportError as e:
            logger.error(f"Failed to import {self.provider} library: {e}")
            raise

    async def _get_session(self) -> aiohttp.ClientSession:
        """
        Get or create aiohttp session with connection pooling.
        
        Returns:
            Configured aiohttp ClientSession
        """
        if self._session is None or self._session.closed:
            # Configure connection pooling
            connector = TCPConnector(
                limit=self.config.connection_pool_size,
                limit_per_host=self.config.connection_pool_size,
                ttl_dns_cache=300,  # Cache DNS for 5 minutes
                enable_cleanup_closed=True
            )
            
            # Configure timeouts
            timeout = ClientTimeout(
                total=self.config.timeout,
                connect=self.config.connect_timeout,
                sock_read=self.config.read_timeout
            )
            
            self._session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                raise_for_status=False  # Handle status codes manually
            )
            
        return self._session

    async def close(self):
        """Close the aiohttp session and cleanup resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            # Wait for connections to close gracefully
            await asyncio.sleep(0.25)
    
    def _generate_prompt_hash(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate a hash for a prompt combination.
        
        Args:
            system_prompt: System/role prompt
            user_prompt: User message/prompt
            
        Returns:
            Hash string for the prompt combination
        """
        combined = f"{system_prompt}|{user_prompt}"
        return hashlib.md5(combined.encode()).hexdigest()

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        model_override: Optional[str] = None,
        response_format: Optional[dict] = None
    ) -> str:
        """
        Generate response from LLM with retry logic.
        
        Args:
            system_prompt: System/role prompt
            user_prompt: User message/prompt
            max_tokens: Maximum tokens to generate (uses config default if None)
            temperature: Temperature for generation (uses config default if None)
            timeout: Timeout in seconds (uses config default if None)
            response_format: Response format (e.g., {"type": "json_object"} for JSON mode)
            
        Returns:
            Generated text response
            
        Raises:
            TimeoutError: If generation exceeds timeout
            Exception: If API call fails after all retries
        """
        max_tokens = self.config.max_tokens if max_tokens is None else max_tokens
        temperature = self.config.temperature if temperature is None else temperature
        timeout = self.config.timeout if timeout is None else timeout
        model = model_override or self.config.model
        
        # Estimate token usage for rate limiting (prompt + completion)
        estimated_tokens = len(system_prompt.split()) + len(user_prompt.split()) + max_tokens
        
        # Acquire rate limit permission
        await self._rate_limiter.acquire(estimated_tokens)
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config.max_retries):
            try:
                if self.provider == "openai":
                    response = await asyncio.wait_for(
                        self._call_openai(system_prompt, user_prompt, max_tokens, temperature, model, response_format),
                        timeout=timeout
                    )
                elif self.provider == "anthropic":
                    if response_format:
                        logger.warning("response_format is not supported by Anthropic API — will be ignored")
                    response = await asyncio.wait_for(
                        self._call_anthropic(system_prompt, user_prompt, max_tokens, temperature, model),
                        timeout=timeout
                    )
                else:
                    raise ValueError(f"Unsupported provider: {self.provider}")
                
                return response
                
            except asyncio.TimeoutError:
                last_exception = TimeoutError(f"LLM generation exceeded {timeout}s timeout")
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries} timed out")
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))  # Exponential backoff
                    
            except Exception as e:
                last_exception = e
                logger.warning(f"Attempt {attempt + 1}/{self.config.max_retries} failed: {e}")
                
                # Don't retry on certain errors
                if "invalid_api_key" in str(e).lower() or "authentication" in str(e).lower():
                    raise
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))  # Exponential backoff
        
        # All retries exhausted
        logger.error(f"LLM generation failed after {self.config.max_retries} attempts")
        raise last_exception

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        model: str,
        response_format: Optional[dict] = None
    ) -> str:
        """Call OpenAI API."""
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        response = await self.client.chat.completions.create(**kwargs)
        
        return response.choices[0].message.content.strip()

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        model: str
    ) -> str:
        """Call Anthropic API."""
        response = await self.client.messages.create(
            model=model,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.content[0].text.strip()

    async def generate_with_fallback(
        self,
        system_prompt: str,
        user_prompt: str,
        fallback_text: str,
        agent_role: Optional[str] = None,
        stage: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        model_override: Optional[str] = None
    ) -> tuple[str, bool]:
        """
        Generate response with fallback on failure.
        
        Args:
            system_prompt: System/role prompt
            user_prompt: User message/prompt
            fallback_text: Text to return if generation fails
            agent_role: Optional agent role for caching fallback
            stage: Optional stage for caching fallback
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (response_text, used_fallback)
        """
        # Cache the fallback response if agent_role and stage provided
        if agent_role and stage:
            self._cache.set_fallback(agent_role, stage, fallback_text)
        
        try:
            response = await self.generate_response(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=timeout,
                model_override=model_override
            )
            return response, False
        except Exception as e:
            logger.warning(f"LLM generation failed, using fallback: {e}")
            
            # Try to get cached fallback if available
            if agent_role and stage:
                cached_fallback = self._cache.get_fallback(agent_role, stage)
                if cached_fallback:
                    logger.debug(f"Using cached fallback for {agent_role} at {stage}")
                    return cached_fallback, True
            
            return fallback_text, True

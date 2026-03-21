"""LLM service for generating AI agent responses."""

import asyncio
from typing import Optional, Literal
import logging

from config import LLMConfig

logger = logging.getLogger("veritas")


class LLMService:
    """
    Service for interacting with LLM APIs (OpenAI or Anthropic).
    
    Handles prompt generation, API calls, response parsing,
    and error handling with fallbacks.
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

    async def generate_response(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        timeout: Optional[int] = None,
        model_override: Optional[str] = None
    ) -> str:
        """
        Generate response from LLM.
        
        Args:
            system_prompt: System/role prompt
            user_prompt: User message/prompt
            max_tokens: Maximum tokens to generate (uses config default if None)
            temperature: Temperature for generation (uses config default if None)
            timeout: Timeout in seconds (uses config default if None)
            
        Returns:
            Generated text response
            
        Raises:
            TimeoutError: If generation exceeds timeout
            Exception: If API call fails
        """
        max_tokens = max_tokens or self.config.max_tokens
        temperature = temperature or self.config.temperature
        timeout = timeout or self.config.timeout
        model = model_override or self.config.model
        
        try:
            if self.provider == "openai":
                response = await asyncio.wait_for(
                    self._call_openai(system_prompt, user_prompt, max_tokens, temperature, model),
                    timeout=timeout
                )
            elif self.provider == "anthropic":
                response = await asyncio.wait_for(
                    self._call_anthropic(system_prompt, user_prompt, max_tokens, temperature),
                    timeout=timeout
                )
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"LLM generation timed out after {timeout}s")
            raise TimeoutError(f"LLM generation exceeded {timeout}s timeout")
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            raise

    async def _call_openai(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float,
        model: str
    ) -> str:
        """Call OpenAI API."""
        response = await self.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        return response.choices[0].message.content.strip()

    async def _call_anthropic(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int,
        temperature: float
    ) -> str:
        """Call Anthropic API."""
        response = await self.client.messages.create(
            model=self.config.model,
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
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (response_text, used_fallback)
        """
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
            return fallback_text, True

"""Configuration management for VERITAS."""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    """Configuration for LLM API."""
    model_config = ConfigDict(populate_by_name=True)
    
    provider: Literal["openai", "anthropic"] = "openai"
    api_key: str = Field(alias="apiKey")
    model: str = "gpt-4"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30  # seconds


class LuffaConfig(BaseModel):
    """Configuration for Luffa Bot API."""
    model_config = ConfigDict(populate_by_name=True)
    
    api_base_url: str = Field(default="https://apibot.luffa.im/robot", alias="apiBaseUrl")
    api_key: str = Field(alias="apiKey")  # Bot secret from robot.luffa.im
    bot_enabled: bool = Field(default=True, alias="botEnabled")
    superbox_enabled: bool = Field(default=False, alias="superboxEnabled")  # Not part of bot API
    channel_enabled: bool = Field(default=False, alias="channelEnabled")  # Not part of bot API


class AppConfig(BaseModel):
    """Main application configuration."""
    model_config = ConfigDict(populate_by_name=True)
    
    llm: LLMConfig
    luffa: LuffaConfig
    session_timeout_hours: int = Field(default=24, alias="sessionTimeoutHours")
    max_experience_minutes: int = Field(default=20, alias="maxExperienceMinutes")


def load_config() -> AppConfig:
    """
    Load configuration from environment variables.
    
    Returns:
        Application configuration
        
    Raises:
        ValueError: If required environment variables are missing
    """
    # LLM configuration
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    
    # Check for API key in multiple locations
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("ANTHROPIC_API_KEY")
    
    if not llm_api_key:
        raise ValueError("API key required: Set LLM_API_KEY, OPENAI_API_KEY, or ANTHROPIC_API_KEY environment variable")
    
    llm_model = os.getenv("LLM_MODEL", "gpt-4o" if llm_provider == "openai" else "claude-3-sonnet-20240229")
    
    # Luffa configuration
    luffa_api_url = os.getenv("LUFFA_API_URL", "https://apibot.luffa.im/robot")
    luffa_bot_secret = os.getenv("LUFFA_BOT_SECRET") or os.getenv("LUFFA_API_KEY", "")
    
    return AppConfig(
        llm=LLMConfig(
            provider=llm_provider,
            apiKey=llm_api_key,
            model=llm_model,
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "2000")),
            timeout=int(os.getenv("LLM_TIMEOUT", "30"))
        ),
        luffa=LuffaConfig(
            apiBaseUrl=luffa_api_url,
            apiKey=luffa_bot_secret,
            botEnabled=os.getenv("LUFFA_BOT_ENABLED", "false").lower() == "true",
            superboxEnabled=os.getenv("LUFFA_SUPERBOX_ENABLED", "false").lower() == "true",
            channelEnabled=os.getenv("LUFFA_CHANNEL_ENABLED", "false").lower() == "true"
        ),
        sessionTimeoutHours=int(os.getenv("SESSION_TIMEOUT_HOURS", "24")),
        maxExperienceMinutes=int(os.getenv("MAX_EXPERIENCE_MINUTES", "20"))
    )

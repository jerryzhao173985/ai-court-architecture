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


class LuffaBotConfig(BaseModel):
    """Configuration for a single Luffa Bot."""
    model_config = ConfigDict(populate_by_name=True)
    
    uid: str
    secret: str
    enabled: bool = True


class LuffaConfig(BaseModel):
    """Configuration for Luffa Bot API - Multi-Bot Architecture."""
    model_config = ConfigDict(populate_by_name=True)
    
    api_base_url: str = Field(default="https://apibot.luffa.im/robot", alias="apiBaseUrl")
    
    # Multi-bot configuration - each trial agent as separate bot
    clerk_bot: Optional[LuffaBotConfig] = Field(default=None, alias="clerkBot")
    prosecution_bot: Optional[LuffaBotConfig] = Field(default=None, alias="prosecutionBot")
    defence_bot: Optional[LuffaBotConfig] = Field(default=None, alias="defenceBot")
    fact_checker_bot: Optional[LuffaBotConfig] = Field(default=None, alias="factCheckerBot")
    judge_bot: Optional[LuffaBotConfig] = Field(default=None, alias="judgeBot")
    
    # Optional: Additional bots for AI jurors
    juror_bots: dict[str, LuffaBotConfig] = Field(default_factory=dict, alias="jurorBots")
    
    # Legacy single-bot support (fallback)
    api_key: Optional[str] = Field(default=None, alias="apiKey")
    
    bot_enabled: bool = Field(default=True, alias="botEnabled")
    superbox_enabled: bool = Field(default=False, alias="superboxEnabled")
    channel_enabled: bool = Field(default=False, alias="channelEnabled")


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
    
    # Luffa configuration - Multi-bot architecture
    luffa_api_url = os.getenv("LUFFA_API_ENDPOINT", "https://apibot.luffa.im/robot")
    
    # Load individual bot configurations
    clerk_bot = None
    if os.getenv("LUFFA_BOT_CLERK_UID") and os.getenv("LUFFA_BOT_CLERK_SECRET"):
        clerk_bot = LuffaBotConfig(
            uid=os.getenv("LUFFA_BOT_CLERK_UID"),
            secret=os.getenv("LUFFA_BOT_CLERK_SECRET"),
            enabled=os.getenv("LUFFA_BOT_CLERK_ENABLED", "true").lower() == "true"
        )
    
    prosecution_bot = None
    if os.getenv("LUFFA_BOT_PROSECUTION_UID") and os.getenv("LUFFA_BOT_PROSECUTION_SECRET"):
        prosecution_bot = LuffaBotConfig(
            uid=os.getenv("LUFFA_BOT_PROSECUTION_UID"),
            secret=os.getenv("LUFFA_BOT_PROSECUTION_SECRET"),
            enabled=os.getenv("LUFFA_BOT_PROSECUTION_ENABLED", "true").lower() == "true"
        )
    
    defence_bot = None
    if os.getenv("LUFFA_BOT_DEFENCE_UID") and os.getenv("LUFFA_BOT_DEFENCE_SECRET"):
        defence_bot = LuffaBotConfig(
            uid=os.getenv("LUFFA_BOT_DEFENCE_UID"),
            secret=os.getenv("LUFFA_BOT_DEFENCE_SECRET"),
            enabled=os.getenv("LUFFA_BOT_DEFENCE_ENABLED", "true").lower() == "true"
        )
    
    fact_checker_bot = None
    if os.getenv("LUFFA_BOT_FACT_CHECKER_UID") and os.getenv("LUFFA_BOT_FACT_CHECKER_SECRET"):
        fact_checker_bot = LuffaBotConfig(
            uid=os.getenv("LUFFA_BOT_FACT_CHECKER_UID"),
            secret=os.getenv("LUFFA_BOT_FACT_CHECKER_SECRET"),
            enabled=os.getenv("LUFFA_BOT_FACT_CHECKER_ENABLED", "true").lower() == "true"
        )
    
    judge_bot = None
    if os.getenv("LUFFA_BOT_JUDGE_UID") and os.getenv("LUFFA_BOT_JUDGE_SECRET"):
        judge_bot = LuffaBotConfig(
            uid=os.getenv("LUFFA_BOT_JUDGE_UID"),
            secret=os.getenv("LUFFA_BOT_JUDGE_SECRET"),
            enabled=os.getenv("LUFFA_BOT_JUDGE_ENABLED", "true").lower() == "true"
        )
    
    # Load optional juror bots
    juror_bots = {}
    for i in range(1, 8):  # Support up to 7 AI juror bots
        uid_key = f"LUFFA_BOT_JUROR_{i}_UID"
        secret_key = f"LUFFA_BOT_JUROR_{i}_SECRET"
        if os.getenv(uid_key) and os.getenv(secret_key):
            juror_bots[f"juror_{i}"] = LuffaBotConfig(
                uid=os.getenv(uid_key),
                secret=os.getenv(secret_key),
                enabled=os.getenv(f"LUFFA_BOT_JUROR_{i}_ENABLED", "true").lower() == "true"
            )
    
    # Legacy single-bot fallback
    legacy_bot_secret = os.getenv("LUFFA_BOT_SECRET")
    
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
            clerkBot=clerk_bot,
            prosecutionBot=prosecution_bot,
            defenceBot=defence_bot,
            factCheckerBot=fact_checker_bot,
            judgeBot=judge_bot,
            jurorBots=juror_bots,
            apiKey=legacy_bot_secret,
            botEnabled=os.getenv("LUFFA_BOT_ENABLED", "false").lower() == "true",
            superboxEnabled=os.getenv("LUFFA_SUPERBOX_ENABLED", "false").lower() == "true",
            channelEnabled=os.getenv("LUFFA_CHANNEL_ENABLED", "false").lower() == "true"
        ),
        sessionTimeoutHours=int(os.getenv("SESSION_TIMEOUT_HOURS", "24")),
        maxExperienceMinutes=int(os.getenv("MAX_EXPERIENCE_MINUTES", "20"))
    )

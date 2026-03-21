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
    
    # Connection pooling settings
    connection_pool_size: int = Field(default=10, alias="connectionPoolSize")
    connect_timeout: int = Field(default=10, alias="connectTimeout")  # seconds
    read_timeout: int = Field(default=30, alias="readTimeout")  # seconds
    
    # Retry settings
    max_retries: int = Field(default=3, alias="maxRetries")
    retry_delay: float = Field(default=1.0, alias="retryDelay")  # seconds, exponential backoff base
    
    # Rate limiting settings
    rate_limit_rpm: int = Field(default=60, alias="rateLimitRpm")  # requests per minute
    rate_limit_tpm: int = Field(default=90000, alias="rateLimitTpm")  # tokens per minute


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


class SessionStorageConfig(BaseModel):
    """Configuration for session storage backend."""
    model_config = ConfigDict(populate_by_name=True)
    
    backend: Literal["file", "postgresql", "mongodb"] = "file"
    
    # File backend settings
    file_storage_dir: str = Field(default="data/sessions", alias="fileStorageDir")
    
    # PostgreSQL settings
    postgresql_dsn: Optional[str] = Field(default=None, alias="postgresqlDsn")
    postgresql_table: str = Field(default="user_sessions", alias="postgresqlTable")
    postgresql_pool_min: int = Field(default=10, alias="postgresqlPoolMin")
    postgresql_pool_max: int = Field(default=20, alias="postgresqlPoolMax")
    
    # MongoDB settings
    mongodb_connection_string: Optional[str] = Field(default=None, alias="mongodbConnectionString")
    mongodb_database: str = Field(default="veritas", alias="mongodbDatabase")
    mongodb_collection: str = Field(default="user_sessions", alias="mongodbCollection")
    mongodb_pool_size: int = Field(default=20, alias="mongodbPoolSize")
    
    # Batching settings
    batch_size: int = Field(default=10, alias="batchSize")
    batch_interval: float = Field(default=1.0, alias="batchInterval")  # seconds


class AppConfig(BaseModel):
    """Main application configuration."""
    model_config = ConfigDict(populate_by_name=True)
    
    llm: LLMConfig
    luffa: LuffaConfig
    session_storage: SessionStorageConfig = Field(default_factory=SessionStorageConfig, alias="sessionStorage")
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
            timeout=int(os.getenv("LLM_TIMEOUT", "30")),
            connectionPoolSize=int(os.getenv("LLM_CONNECTION_POOL_SIZE", "10")),
            connectTimeout=int(os.getenv("LLM_CONNECT_TIMEOUT", "10")),
            readTimeout=int(os.getenv("LLM_READ_TIMEOUT", "30")),
            maxRetries=int(os.getenv("LLM_MAX_RETRIES", "3")),
            retryDelay=float(os.getenv("LLM_RETRY_DELAY", "1.0")),
            rateLimitRpm=int(os.getenv("LLM_RATE_LIMIT_RPM", "60")),
            rateLimitTpm=int(os.getenv("LLM_RATE_LIMIT_TPM", "90000"))
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
        sessionStorage=SessionStorageConfig(
            backend=os.getenv("SESSION_STORAGE_BACKEND", "file"),
            fileStorageDir=os.getenv("SESSION_FILE_STORAGE_DIR", "data/sessions"),
            postgresqlDsn=os.getenv("SESSION_POSTGRESQL_DSN"),
            postgresqlTable=os.getenv("SESSION_POSTGRESQL_TABLE", "user_sessions"),
            postgresqlPoolMin=int(os.getenv("SESSION_POSTGRESQL_POOL_MIN", "10")),
            postgresqlPoolMax=int(os.getenv("SESSION_POSTGRESQL_POOL_MAX", "20")),
            mongodbConnectionString=os.getenv("SESSION_MONGODB_CONNECTION_STRING"),
            mongodbDatabase=os.getenv("SESSION_MONGODB_DATABASE", "veritas"),
            mongodbCollection=os.getenv("SESSION_MONGODB_COLLECTION", "user_sessions"),
            mongodbPoolSize=int(os.getenv("SESSION_MONGODB_POOL_SIZE", "20")),
            batchSize=int(os.getenv("SESSION_BATCH_SIZE", "10")),
            batchInterval=float(os.getenv("SESSION_BATCH_INTERVAL", "1.0"))
        ),
        sessionTimeoutHours=int(os.getenv("SESSION_TIMEOUT_HOURS", "24")),
        maxExperienceMinutes=int(os.getenv("MAX_EXPERIENCE_MINUTES", "20"))
    )

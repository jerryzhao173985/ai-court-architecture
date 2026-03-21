# VERITAS Courtroom Experience - Design Document

## Overview

VERITAS is an interactive 15-minute British Crown Court trial experience that combines narrative immersion with AI-driven courtroom simulation. The system orchestrates a complete trial workflow from atmospheric opening through structured proceedings to jury deliberation, culminating in a dual assessment of both verdict accuracy and reasoning quality.

The architecture integrates Luffa platform components:
- **Luffa Bot** (Production): Multi-bot system with 5 separate bots (Clerk, Prosecution, Defence, Fact Checker, Judge) providing procedural guidance and managing user interaction via polling
- **SuperBox** (Stub): Data models and scene generation exist, but no actual visual rendering — text-only fallbacks used in production
- **Luffa Channel** (Stub): Data models for verdict sharing exist, but no actual channel API integration — sharing functionality is local-only

The system's core innovation lies in its dual-layer evaluation model. Unlike traditional interactive fiction that judges only outcomes, VERITAS assesses the quality of user reasoning independently from verdict correctness. This creates four possible outcomes: sound reasoning with correct verdict, sound reasoning with incorrect verdict, weak reasoning with correct verdict, and weak reasoning with incorrect verdict. This approach rewards logical thinking even when users reach the "wrong" conclusion.

### Key Technical Challenges

1. **State Machine Complexity**: Managing seamless transitions through 8+ trial stages while preserving user progress and enforcing timing constraints
2. **Multi-Agent Orchestration**: Coordinating 5 trial agents (Clerk, Prosecution, Defence, Fact Checker, Judge) with distinct roles and 8 jurors (3 active AI, 4 lightweight AI, 1 human) with varied personas
3. **Real-Time Reasoning Evaluation**: Analyzing user arguments during deliberation to assess logical coherence, evidence citation, and fallacy detection
4. **Evidence Timeline Visualization**: Presenting 5-7 evidence items in an interactive, chronologically organized interface
5. **Anonymous Voting Mechanism**: Collecting simultaneous votes from 8 jurors while maintaining anonymity until reveal
6. **Dual Reveal Orchestration**: Sequencing verdict announcement, truth disclosure, reasoning feedback, and AI juror identity revelation

### Target Experience Flow

```
Hook Scene (90s) 
  → Charge Reading (30s)
  → Prosecution Opening (60s)
  → Defence Opening (60s)
  → Evidence Presentation (120s)
  → Cross-Examination (90s)
  → Prosecution Closing (60s)
  → Defence Closing (60s)
  → Judge Summing Up (105s)
  → Jury Deliberation (300s)
  → Anonymous Vote (30s)
  → Dual Reveal (90s)
Total: ~15 minutes
```

## Architecture

### Advanced Features

**Dynamic Complexity Adaptation**
- Cases are analyzed for complexity based on evidence count, diversity, witness count, timeline complexity, and narrative length
- Complexity levels (simple/moderate/complex) adjust agent character limits and prompt guidance
- Enables appropriate verbosity for different case types without manual configuration
- Scores range from 5-15 points across multiple dimensions

**Intelligent Caching System**
- Three-tier TTL cache: fallback responses (24h), case content (1h), agent responses (5min)
- Reduces API calls and improves response times
- Automatic cleanup of expired entries every 5 minutes
- Cache statistics tracking (hits, misses, hit rate)

**Connection Pooling & Rate Limiting**
- aiohttp connection pool (10 connections default, configurable)
- Token bucket rate limiter tracking both requests (60 RPM) and tokens (90K TPM)
- Automatic backoff when limits approached
- Exponential retry with 3 attempts default

**Multi-Backend Session Persistence**
- File-based storage for development (default)
- PostgreSQL with connection pooling for production
- MongoDB with connection pooling for scalability
- Batched writes (10 per batch, 1s interval) to reduce I/O
- Async operations throughout

**Message Polling Architecture**
- Background asyncio task polling every 1 second
- Message deduplication by msgId
- Command routing (/start, /continue, /vote, /evidence, /status, /help)
- Custom handler registration per user/group
- Graceful error handling with 5s backoff

**Multi-Bot Support**
- Separate Luffa bots for each trial agent (Clerk, Prosecution, Defence, Fact Checker, Judge)
- Optional separate bots for AI jurors
- Distinct personalities and avatars per role
- Bot-specific authentication and message routing
- Fallback to single-bot mode

**Group Broadcasting**
- Stage announcements to groups with visual formatting
- Interactive buttons for user actions (Continue, Vote, View Evidence)
- Button visibility control (public vs private)
- Persistent buttons with "select" dismiss type

**Strategic Prompt Engineering**
- Prosecution prompts identify key strengths (motive, means, opportunity)
- Defence prompts identify doubt-creating opportunities (timeline gaps, missing evidence, alternative explanations)
- Case-specific fallbacks for Blackthorn Hall with detailed arguments
- Complexity-adjusted guidance embedded in prompts

### System Architecture Diagram

```mermaid
graph TB
    User[User] --> LuffaBots[Multi-Bot System<br/>5 Trial Agents + Jurors]
    User --> SuperBox[SuperBox<br/>Visual Interface]
    
    LuffaBots --> MessagePolling[Message Polling Loop<br/>1s intervals]
    MessagePolling --> ExperienceOrchestrator[Experience Orchestrator<br/>Main Controller]
    
    ExperienceOrchestrator --> StateMachine[State Machine]
    ExperienceOrchestrator --> CaseManager[Case Manager]
    ExperienceOrchestrator --> TrialOrchestrator[Trial Orchestrator]
    ExperienceOrchestrator --> JuryOrchestrator[Jury Orchestrator]
    ExperienceOrchestrator --> SessionStore[Session Store<br/>File/PostgreSQL/MongoDB]
    
    CaseManager --> CaseStore[(Case Content<br/>JSON Fixtures)]
    CaseManager --> Cache[TTL Cache<br/>Case Content]
    
    TrialOrchestrator --> ComplexityAnalyzer[Complexity Analyzer<br/>Dynamic Prompts]
    TrialOrchestrator --> LLMService[LLM Service<br/>Connection Pool]
    TrialOrchestrator --> ClerkAgent[Clerk Agent]
    TrialOrchestrator --> ProsecutionAgent[Prosecution Agent]
    TrialOrchestrator --> DefenceAgent[Defence Agent]
    TrialOrchestrator --> FactCheckerAgent[Fact Checker Agent]
    TrialOrchestrator --> JudgeAgent[Judge Agent]
    
    LLMService --> RateLimiter[Rate Limiter<br/>RPM/TPM]
    LLMService --> ConnectionPool[aiohttp Pool<br/>10 connections]
    LLMService --> ResponseCache[Response Cache<br/>Fallbacks]
    
    JuryOrchestrator --> ActiveJurors[3 Active AI Jurors<br/>GPT-4o]
    JuryOrchestrator --> LightweightJurors[4 Lightweight AI Jurors<br/>GPT-4o-mini]
    JuryOrchestrator --> ReasoningEvaluator[Reasoning Evaluator]
    
    ReasoningEvaluator --> EvidenceTracker[Evidence Reference Tracker]
    ReasoningEvaluator --> FallacyDetector[Logical Fallacy Detector]
    
    ExperienceOrchestrator --> DualRevealAssembler[Dual Reveal Assembler]
    ExperienceOrchestrator --> LuffaChannel[Luffa Channel<br/>Community Platform]
    
    SuperBox --> EvidenceBoard[Evidence Board<br/>Timeline UI]
    SuperBox --> VotingUI[Anonymous Voting UI]
    SuperBox --> RevealUI[Dual Reveal UI]
```

### Component Responsibilities

**Experience Orchestrator (Main Controller)**
- Coordinates all VERITAS components and manages complete experience flow
- Initializes and wires together state machine, agents, jury, and platform integrations
- Handles message polling loop for Luffa Bot messages (1-second intervals)
- Routes incoming messages to appropriate command handlers
- Manages user sessions and progress persistence
- Implements error handling and graceful degradation
- Provides unified API for experience operations

**State Machine (Experience Controller)**
- Manages experience flow through all trial stages
- Enforces stage sequencing and timing constraints
- Preserves user progress for 24 hours on disconnection
- Coordinates transitions between Luffa Bot, SuperBox, and backend services
- Implements 20-minute maximum duration enforcement
- Tracks state history and timing for each stage

**Case Manager**
- Loads and validates case content from JSON fixtures
- Provides case context to all AI agents
- Manages evidence item metadata and timeline data
- Validates case structure (5-7 evidence items, required fields)
- Handles case content serialization/deserialization
- Implements TTL caching for loaded cases (1-hour expiration)

**Complexity Analyzer**
- Analyzes case content to determine complexity level (simple/moderate/complex)
- Scores cases based on evidence count, diversity, witness count, timeline complexity
- Adjusts character limits for agent responses based on complexity
- Provides complexity-specific guidance for agent prompts
- Enables dynamic prompt adaptation for different case types

**Trial Orchestrator**
- Coordinates 5 trial layer AI agents
- Enforces Crown Court procedural order
- Manages fact-checking interventions (max 3 per trial)
- Generates agent prompts with case context and complexity guidance
- Implements fallback responses for agent failures
- Identifies prosecution/defence strategic strengths for focused arguments
- Handles agent timeout and retry logic

**LLM Service**
- Manages OpenAI/Anthropic API interactions with async operations
- Implements connection pooling (10 connections default, configurable)
- Enforces rate limiting (60 RPM, 90K TPM default)
- Provides retry logic with exponential backoff (3 retries default)
- Caches fallback responses (24-hour TTL)
- Supports model override (GPT-4o for active jurors, GPT-4o-mini for lightweight)
- Handles timeout management and error recovery

**Jury Orchestrator**
- Manages 8-juror composition (3 active AI, 4 lightweight AI, 1 human)
- Assigns personas to active AI jurors (Evidence Purist, Sympathetic Doubter, Moral Absolutist)
- Coordinates deliberation turn-taking with 15-second response time
- Collects anonymous votes
- Triggers reasoning evaluation
- Uses different LLM models for active vs lightweight jurors

**Reasoning Evaluator**
- Analyzes user statements during deliberation
- Tracks evidence item references
- Detects logical fallacies (ad hominem, appeal to emotion, false dichotomy, etc.)
- Produces four-category assessment (sound/weak × correct/incorrect)
- Completes evaluation within 10 seconds of vote

**Evidence Board**
- Renders chronological timeline of evidence items
- Highlights items as they're presented during trial
- Provides detailed view on item selection
- Remains accessible throughout deliberation
- SuperBox visual rendering is a stub — text-only evidence display used in production

**Session Store**
- Persists user sessions with multiple backend support:
  - File-based storage (default, data/sessions directory)
  - PostgreSQL with connection pooling (10-20 connections)
  - MongoDB with connection pooling (20 connections)
- Implements batching for write operations (10 writes per batch, 1s interval)
- Handles 24-hour session retention and cleanup
- Provides async save/restore operations

**Multi-Bot System**
- Supports separate Luffa bots for each trial agent (Clerk, Prosecution, Defence, Fact Checker, Judge)
- Optional separate bots for AI jurors
- Enables distinct bot personalities and avatars per role
- Handles bot-specific message routing and authentication
- Falls back to single-bot mode if multi-bot not configured

**Message Polling Loop**
- Polls Luffa Bot API every 1 second for new messages
- Implements message deduplication (handled by LuffaAPIClient)
- Routes messages to command handlers or deliberation processing
- Supports custom message handlers per user/group
- Handles errors gracefully with 5-second backoff on failure

### Technology Stack

**Implementation:**
- **Backend**: Python >=3.10 with asyncio for concurrent operations
- **AI Agents**: OpenAI (GPT-4o, GPT-4o-mini) or Anthropic (Claude) with structured prompts
- **Storage**: 
  - Case content: JSON files in fixtures directory
  - Session persistence: File-based (default), PostgreSQL, or MongoDB backends
  - Caching: In-memory TTL cache with configurable expiration
- **Real-time Communication**: Luffa Bot API polling (1-second intervals) with message deduplication
- **HTTP Client**: aiohttp with connection pooling (configurable pool size)
- **Data Validation**: Pydantic models with field validation and serialization
- **Configuration**: Environment variables via python-dotenv
- **Luffa Platform**: Multi-bot architecture with separate bots for each trial agent

### Configuration

The system uses environment variables for configuration:

```bash
# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
LLM_API_KEY=sk-...  # or OPENAI_API_KEY or ANTHROPIC_API_KEY (checked in this order)
LLM_MODEL=gpt-4o  # default: gpt-4o (openai) or claude-3-sonnet-20240229 (anthropic)
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30  # total timeout in seconds
LLM_CONNECTION_POOL_SIZE=10
LLM_CONNECT_TIMEOUT=10  # connection timeout in seconds
LLM_READ_TIMEOUT=30  # read timeout in seconds
LLM_MAX_RETRIES=3  # retry attempts with exponential backoff
LLM_RETRY_DELAY=1.0  # base delay between retries in seconds
LLM_RATE_LIMIT_RPM=60
LLM_RATE_LIMIT_TPM=90000

# Luffa Multi-Bot Configuration (Production)
LUFFA_BOT_CLERK_UID=...
LUFFA_BOT_CLERK_SECRET=...
LUFFA_BOT_PROSECUTION_UID=...
LUFFA_BOT_PROSECUTION_SECRET=...
LUFFA_BOT_DEFENCE_UID=...
LUFFA_BOT_DEFENCE_SECRET=...
LUFFA_BOT_FACT_CHECKER_UID=...
LUFFA_BOT_FACT_CHECKER_SECRET=...
LUFFA_BOT_JUDGE_UID=...
LUFFA_BOT_JUDGE_SECRET=...

# Luffa API Configuration
LUFFA_API_ENDPOINT=https://apibot.luffa.im/robot
LUFFA_BOT_ENABLED=true  # default: false
LUFFA_SUPERBOX_ENABLED=false  # stub, not production-ready
LUFFA_CHANNEL_ENABLED=false  # stub, not production-ready

# Legacy single-bot fallback (optional)
LUFFA_BOT_SECRET=...  # only if multi-bot not configured

# Session Storage Configuration
SESSION_STORAGE_BACKEND=file  # or postgresql, mongodb
SESSION_TIMEOUT_HOURS=24
SESSION_FILE_STORAGE_DIR=data/sessions  # for file backend
SESSION_BATCH_SIZE=10
SESSION_BATCH_INTERVAL=1.0

# PostgreSQL (if using)
SESSION_POSTGRESQL_DSN=postgresql://user:pass@localhost/veritas
SESSION_POSTGRESQL_TABLE=user_sessions
SESSION_POSTGRESQL_POOL_MIN=10
SESSION_POSTGRESQL_POOL_MAX=20

# MongoDB (if using)
SESSION_MONGODB_CONNECTION_STRING=mongodb://localhost:27017
SESSION_MONGODB_DATABASE=veritas
SESSION_MONGODB_COLLECTION=user_sessions
SESSION_MONGODB_POOL_SIZE=20

# Application Settings
MAX_EXPERIENCE_MINUTES=20
```

### Running the System

**Multi-Bot Service** (production, separate bots per agent):
```bash
cd src && python -u multi_bot_service.py
```

**Interactive Demo** (single-user, terminal-based):
```bash
cd src && python -u main.py
```

**API Server** (REST + WebSocket):
```bash
cd src && uvicorn api:app --reload --port 8000
```

**Single-Bot Service** (legacy, single bot for all agents):
```bash
cd src && python -u luffa_bot_service.py
```

## Components and Interfaces

### LLM Service Component

The LLM Service manages all AI agent interactions with production-grade reliability.

**Interface:**
```python
class LLMService:
    """Service for interacting with LLM APIs (OpenAI or Anthropic)."""
    
    def __init__(self, config: LLMConfig):
        """Initialize with configuration including provider, model, rate limits."""
        pass
    
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
        """Generate response with retry logic and rate limiting."""
        pass
    
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
        """Generate response with fallback on failure. Returns (response, used_fallback)."""
        pass
    
    async def close(self):
        """Close connection pool and cleanup resources."""
        pass
```

**Key Features:**
- Connection pooling with configurable size (default 10)
- Rate limiting: 60 RPM, 90K TPM (configurable)
- Retry logic with exponential backoff (3 attempts)
- Timeout management (30s default)
- Response caching for fallbacks (24h TTL)
- Model override support (GPT-4o vs GPT-4o-mini)
- JSON response format support for structured outputs

**Configuration:**
```python
class LLMConfig:
    provider: Literal["openai", "anthropic"]
    api_key: str
    model: str  # "gpt-4o", "gpt-4o-mini", "claude-3-sonnet-20240229"
    temperature: float = 0.7
    max_tokens: int = 2000
    timeout: int = 30
    connection_pool_size: int = 10
    connect_timeout: int = 10
    read_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_rpm: int = 60
    rate_limit_tpm: int = 90000
```

### Complexity Analyzer Component

Analyzes case content to determine complexity and adjust agent behavior.

**Interface:**
```python
class ComplexityLevel:
    level: Literal["simple", "moderate", "complex"]
    verbosity_multiplier: float  # 0.8, 1.0, 1.2
    argumentation_depth: str  # "concise", "balanced", "detailed"

class CaseComplexityAnalyzer:
    def analyze_complexity(self, case_content: CaseContent) -> ComplexityLevel:
        """Analyze case and return complexity level."""
        pass
    
    def get_complexity_guidance(self, complexity: ComplexityLevel) -> str:
        """Get guidance text to append to agent prompts."""
        pass
    
    def adjust_character_limit(self, base_limit: int, complexity: ComplexityLevel) -> int:
        """Adjust character limit based on complexity (200-2500 range)."""
        pass
```

**Scoring Factors:**
- Evidence count (5-7 items): 1-3 points
- Evidence type diversity (physical/testimonial/documentary): 1-3 points
- Witness count: 0-2 points
- Timeline event count: 0-2 points
- Average evidence description length: 0-2 points
- Key facts count: 0-2 points
- Total score: 5-15 points
  - Simple: ≤8 points (0.8x verbosity)
  - Moderate: 9-11 points (1.0x verbosity)
  - Complex: ≥12 points (1.2x verbosity)

### Caching System Component

TTL-based caching for agent responses, case content, and fallbacks.

**Interface:**
```python
class TTLCache:
    """Time-To-Live cache with automatic expiration."""
    
    def __init__(self, default_ttl: float = 3600):
        """Initialize with default TTL in seconds."""
        pass
    
    def get(self, key: str) -> Optional[Any]:
        """Get value if exists and not expired."""
        pass
    
    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """Set value with TTL."""
        pass
    
    def cleanup_expired(self):
        """Remove expired entries."""
        pass
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics (hits, misses, size, hit_rate)."""
        pass

class ResponseCache:
    """Specialized cache for LLM responses."""
    
    FALLBACK_TTL = 86400  # 24 hours
    CASE_CONTENT_TTL = 3600  # 1 hour
    AGENT_RESPONSE_TTL = 300  # 5 minutes
    
    def get_fallback(self, agent_role: str, stage: str) -> Optional[str]:
        """Get cached fallback response."""
        pass
    
    def set_fallback(self, agent_role: str, stage: str, response: str):
        """Cache fallback response."""
        pass
    
    def get_case_content(self, case_id: str) -> Optional[CaseContent]:
        """Get cached case content."""
        pass
    
    def set_case_content(self, case_id: str, content: CaseContent):
        """Cache case content."""
        pass
```

**Background Cleanup:**
- Async task runs every 5 minutes
- Removes expired entries from all caches
- Logs statistics after cleanup

### Session Store Component

Multi-backend session persistence with async operations.

**Interface:**
```python
class SessionStore:
    """Persistent storage for user sessions."""
    
    def __init__(self, storage_dir: str = "data/sessions"):
        """Initialize with storage directory (file backend)."""
        pass
    
    def save_progress(self, session: UserSession) -> None:
        """Save session to persistent storage."""
        pass
    
    def restore_progress(self, session_id: str) -> Optional[UserSession]:
        """Restore session if exists and not expired (24h retention)."""
        pass
    
    def delete_session(self, session_id: str) -> None:
        """Delete session from storage."""
        pass
    
    def cleanup_expired_sessions(self, retention_hours: int = 24) -> int:
        """Remove expired sessions. Returns count cleaned."""
        pass
```

**Backend Support:**
- **File**: JSON files in data/sessions directory (default)
- **PostgreSQL**: Connection pooling (10-20 connections), batched writes
- **MongoDB**: Connection pooling (20 connections), batched writes

**Configuration:**
```python
class SessionStorageConfig:
    backend: Literal["file", "postgresql", "mongodb"] = "file"
    file_storage_dir: str = "data/sessions"
    postgresql_dsn: Optional[str] = None
    postgresql_table: str = "user_sessions"
    postgresql_pool_min: int = 10
    postgresql_pool_max: int = 20
    mongodb_connection_string: Optional[str] = None
    mongodb_database: str = "veritas"
    mongodb_collection: str = "user_sessions"
    mongodb_pool_size: int = 20
    batch_size: int = 10
    batch_interval: float = 1.0  # seconds
```

### Experience Orchestrator Component

Main controller coordinating all VERITAS components.

**Key Methods:**
```python
class ExperienceOrchestrator:
    async def initialize(self) -> dict:
        """Initialize experience by loading case and setting up components."""
        pass
    
    async def start_experience(self) -> dict:
        """Start experience by transitioning to hook scene."""
        pass
    
    async def advance_trial_stage(self) -> dict:
        """Advance to next trial stage and execute agents."""
        pass
    
    async def broadcast_stage_to_group(self, group_id: str) -> dict:
        """Broadcast stage announcement to group with buttons."""
        pass
    
    async def submit_deliberation_statement(self, statement: str, evidence_refs: list[str]) -> dict:
        """Submit user statement and get AI juror responses."""
        pass
    
    async def submit_vote(self, vote: Literal["guilty", "not_guilty"]) -> dict:
        """Submit vote, evaluate reasoning, and assemble dual reveal."""
        pass
    
    async def complete_experience(self, share_verdict: bool) -> dict:
        """Complete experience and optionally share verdict."""
        pass
    
    # Message Polling
    async def start_message_polling(self) -> None:
        """Start background polling loop (1s intervals)."""
        pass
    
    async def stop_message_polling(self) -> None:
        """Stop polling loop."""
        pass
```

**Message Routing:**
- Commands: /start, /continue, /vote, /evidence, /status, /help
- Deliberation: Regular messages during deliberation state
- Custom handlers: Registerable per user/group

### Multi-Bot System Component

Supports separate Luffa bots for each trial agent.

**Configuration:**
```python
class LuffaBotConfig:
    uid: str  # Bot UID
    secret: str  # Bot secret
    enabled: bool = True

class LuffaConfig:
    api_base_url: str = "https://apibot.luffa.im/robot"
    clerk_bot: Optional[LuffaBotConfig] = None
    prosecution_bot: Optional[LuffaBotConfig] = None
    defence_bot: Optional[LuffaBotConfig] = None
    fact_checker_bot: Optional[LuffaBotConfig] = None
    judge_bot: Optional[LuffaBotConfig] = None
    juror_bots: dict[str, LuffaBotConfig] = {}
    api_key: Optional[str] = None  # Legacy single-bot fallback
```

**Environment Variables:**
```
LUFFA_BOT_CLERK_UID=...
LUFFA_BOT_CLERK_SECRET=...
LUFFA_BOT_PROSECUTION_UID=...
LUFFA_BOT_PROSECUTION_SECRET=...
LUFFA_BOT_DEFENCE_UID=...
LUFFA_BOT_DEFENCE_SECRET=...
LUFFA_BOT_FACT_CHECKER_UID=...
LUFFA_BOT_FACT_CHECKER_SECRET=...
LUFFA_BOT_JUDGE_UID=...
LUFFA_BOT_JUDGE_SECRET=...
LUFFA_BOT_JUROR_1_UID=...
LUFFA_BOT_JUROR_1_SECRET=...
```

### Case Manager Component

Handles case content loading, validation, and distribution.

**Interface:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class CharacterProfile(BaseModel):
    """Profile for a character in the case (victim, defendant, witness)."""
    model_config = ConfigDict(populate_by_name=True)
    
    name: str
    role: str
    background: str
    relevant_facts: list[str] = Field(alias="relevantFacts")

class EvidenceItem(BaseModel):
    """Individual piece of case evidence."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    type: Literal["physical", "testimonial", "documentary"]
    title: str
    description: str
    timestamp: str  # ISO 8601 format
    presented_by: Literal["prosecution", "defence"] = Field(alias="presentedBy")
    significance: str

class CaseNarrative(BaseModel):
    """Narrative elements of the case."""
    model_config = ConfigDict(populate_by_name=True)
    
    hook_scene: str = Field(alias="hookScene")
    charge_text: str = Field(alias="chargeText")
    victim_profile: CharacterProfile = Field(alias="victimProfile")
    defendant_profile: CharacterProfile = Field(alias="defendantProfile")
    witness_profiles: list[CharacterProfile] = Field(alias="witnessProfiles")

class CaseContent(BaseModel):
    """Complete case content structure."""
    model_config = ConfigDict(populate_by_name=True)
    
    case_id: str = Field(alias="caseId")
    title: str
    narrative: CaseNarrative
    evidence: list[EvidenceItem]
    timeline: list[TimelineEvent]
    ground_truth: GroundTruth = Field(alias="groundTruth")
```

**Key Methods:**
- `load_case(case_id: str) -> CaseContent` - Loads and validates case
- `validate_case(content: CaseContent) -> ValidationResult` - Checks required fields
- `get_evidence_items() -> list[EvidenceItem]` - Returns all evidence
- `get_evidence_by_timestamp() -> list[EvidenceItem]` - Returns chronologically sorted evidence
- `serialize_case(content: CaseContent) -> str` - Converts to JSON
- `deserialize_case(json: str) -> CaseContent` - Parses from JSON

### Trial Orchestrator Component

Coordinates the 5 trial layer AI agents through Crown Court procedure.

**Agent Configuration:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
from datetime import datetime

class TrialAgent(BaseModel):
    """Configuration for a trial layer AI agent."""
    model_config = ConfigDict(populate_by_name=True)
    
    role: Literal["clerk", "prosecution", "defence", "fact_checker", "judge"]
    system_prompt: str = Field(alias="systemPrompt")
    character_limit: int = Field(alias="characterLimit")
    response_timeout: int = Field(alias="responseTimeout")  # milliseconds

class AgentResponse(BaseModel):
    """Response from a trial agent."""
    model_config = ConfigDict(populate_by_name=True)
    
    agent_role: str = Field(alias="agentRole")
    content: str
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)
```

**Key Methods:**
- `initialize_agents(case_content: CaseContent) -> None` - Sets up agents with case context and complexity analysis
- `execute_stage(stage: ExperienceState) -> list[AgentResponse]` - Runs agents for current stage
- `check_fact_accuracy(statement: str, speaker: str, stage: ExperienceState) -> Optional[FactCheckResult]` - Validates statements against case (LLM-based, returns None if stage/limit disallows)
- `generate_judge_summary() -> str` - Creates judge's summing up (sync fallback version)
- `handle_agent_failure(agent_role: str, stage: ExperienceState) -> AgentResponse` - Returns fallback response for role/stage

**Fact Checking Logic:**
- Monitors prosecution and defence statements during evidence and cross-examination stages
- Compares statements against case content ground truth
- Triggers fact checker agent when contradiction detected
- Limits interventions to 3 per trial
- Excludes opening and closing speeches from fact checking

### Jury Orchestrator Component

Manages the 8-juror deliberation system with 3 active AI, 4 lightweight AI, and 1 human.

**Juror Configuration:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional
from datetime import datetime

class JurorPersona(BaseModel):
    """Configuration for a juror with persona."""
    model_config = ConfigDict(populate_by_name=True)
    
    id: str
    type: Literal["active_ai", "lightweight_ai", "human"]
    persona: Optional[Literal["evidence_purist", "sympathetic_doubter", "moral_absolutist"]] = None
    system_prompt: Optional[str] = Field(default=None, alias="systemPrompt")

class DeliberationTurn(BaseModel):
    """A single turn in jury deliberation."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    statement: str
    timestamp: datetime
    evidence_references: list[str] = Field(default_factory=list, alias="evidenceReferences")
```

**Key Methods:**
- `initialize_jury(case_content: CaseContent) -> None` - Creates 8 jurors (7 AI with personas + 1 human) with complexity analysis
- `start_deliberation() -> str` - Begins deliberation phase, returns initial prompt for user
- `process_user_statement(statement: str, evidence_references: list[str] = None) -> list[DeliberationTurn]` - User speaks, AI jurors respond
- `collect_votes(user_vote: Literal["guilty", "not_guilty"]) -> VoteResult` - Collects user vote + AI votes, returns verdict
- `reveal_jurors(vote_result: VoteResult) -> list[JurorReveal]` - Discloses AI identities and votes from result

**Deliberation Flow:**
- User prompted for initial thoughts
- 3 active AI jurors engage in back-and-forth debate
- 4 lightweight AI jurors contribute brief statements
- User can reference evidence items
- 15-second response time for AI jurors
- 4-6 minute duration, hard cutoff at 6 minutes

### Reasoning Evaluator Component

Analyzes user's deliberation statements to assess reasoning quality.

**Evaluation Criteria:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal

class ReasoningCriteria(BaseModel):
    """Criteria for evaluating reasoning quality."""
    model_config = ConfigDict(populate_by_name=True)
    
    required_evidence_references: list[str] = Field(alias="requiredEvidenceReferences")
    logical_fallacies: list[str] = Field(alias="logicalFallacies")
    coherence_threshold: float = Field(alias="coherenceThreshold")

class ReasoningAssessment(BaseModel):
    """Assessment of user's reasoning quality."""
    model_config = ConfigDict(populate_by_name=True)
    
    category: Literal["sound_correct", "sound_incorrect", "weak_correct", "weak_incorrect"]
    evidence_score: float = Field(alias="evidenceScore")  # 0-1, based on relevant evidence cited
    coherence_score: float = Field(alias="coherenceScore")  # 0-1, based on logical flow
    fallacies_detected: list[str] = Field(alias="fallaciesDetected")
    feedback: str
```

**Key Methods:**
- `analyze_statements(statements: list[DeliberationTurn], user_verdict: Literal["guilty", "not_guilty"]) -> ReasoningAssessment` - Evaluates user's deliberation turns against ground truth
- `track_evidence_references(statements: list[DeliberationTurn]) -> list[str]` - Extracts evidence item IDs from user statements (by ID, title, and key terms)
- `detect_fallacies(statements: list[DeliberationTurn]) -> list[str]` - Identifies logical fallacies (ad_hominem, appeal_to_emotion, false_dichotomy, hasty_generalization, straw_man)
- `calculate_coherence(statements: list[DeliberationTurn]) -> float` - Assesses logical consistency (0-1 score based on length, connectors, repetition)
- `generate_feedback(category: str, evidence_refs: list[str], fallacies: list[str], coherence_score: float) -> str` - Creates user-facing feedback

**Evaluation Process:**
1. Collect all user statements from deliberation
2. Extract evidence item references
3. Detect logical fallacies (ad hominem, appeal to emotion, false dichotomy, etc.)
4. Calculate coherence score based on argument structure
5. Compare user verdict with ground truth
6. Categorize into one of four outcomes
7. Generate specific feedback with examples

### Evidence Board Component

Visual interface for displaying and interacting with case evidence.

**Interface:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class EvidenceBoard:
    """Visual interface for displaying and interacting with case evidence."""
    
    def __init__(self, case_content: CaseContent):
        """Initialize evidence board with case content."""
        self.items = case_content.evidence
        self.timeline = case_content.timeline
        self.highlighted_item_id: Optional[str] = None
    
    def render_timeline(self) -> list[dict]:
        """Render chronological evidence timeline."""
        pass
    
    def highlight_item(self, item_id: str) -> None:
        """Highlight an evidence item during trial presentation."""
        pass
    
    def select_item(self, item_id: str) -> Optional[EvidenceItem]:
        """Select an evidence item for detailed view."""
        pass
    
    def filter_by_type(self, evidence_type: str) -> list[EvidenceItem]:
        """Filter evidence items by type."""
        pass
    
    def search_evidence(self, query: str) -> list[EvidenceItem]:
        """Search evidence items by keyword."""
        pass
```

**Visual Requirements** (SuperBox rendering is stub — text-only in production):
- Chronological timeline with date markers
- Evidence items positioned at appropriate timestamps
- Highlight animation when item presented during trial
- Detailed modal/panel on item selection
- Persistent access during deliberation

### Luffa Platform Integration

**Luffa Bot Interface:**
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Literal

class LuffaBotMessage(BaseModel):
    """Message sent via Luffa Bot."""
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["greeting", "stage_announcement", "prompt", "response"]
    content: str
    metadata: Optional[dict] = None
```

**SuperBox Interface** (STUB — data models exist, no visual rendering API connected):
```python
class SuperBoxScene(BaseModel):
    """SuperBox visual scene configuration."""
    model_config = ConfigDict(populate_by_name=True)
    
    scene_type: Literal["courtroom", "jury_chamber", "evidence_board", "reveal"] = Field(alias="sceneType")
    elements: list[dict]  # SceneElement objects
    active_agent: Optional[str] = Field(default=None, alias="activeAgent")
```

**Luffa Channel Interface** (STUB — data models exist, no channel API connected):
```python
class ChannelAnnouncement(BaseModel):
    """Announcement posted to Luffa Channel."""
    model_config = ConfigDict(populate_by_name=True)
    
    type: Literal["new_case", "verdict_share", "statistics"]
    case_id: str = Field(alias="caseId")
    content: str
    metadata: Optional[dict] = None

class VerdictShare(BaseModel):
    """Verdict shared to Luffa Channel."""
    model_config = ConfigDict(populate_by_name=True)
    
    case_id: str = Field(alias="caseId")
    verdict: Literal["guilty", "not_guilty"]
    anonymous: bool
    timestamp: datetime
```

## Data Models

### Core Data Structures

**Session State:**
```python
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal

class SessionProgress(BaseModel):
    """Progress tracking for a user session."""
    model_config = ConfigDict(populate_by_name=True)

    completed_stages: list[ExperienceState] = Field(default_factory=list, alias="completedStages")
    deliberation_statements: list[DeliberationTurn] = Field(default_factory=list, alias="deliberationStatements")
    vote: Optional[Literal["guilty", "not_guilty"]] = None
    reasoning_assessment: Optional[ReasoningAssessment] = Field(default=None, alias="reasoningAssessment")

class SessionMetadata(BaseModel):
    """Metadata about session activity."""
    model_config = ConfigDict(populate_by_name=True)

    pause_count: int = Field(default=0, alias="pauseCount")
    total_pause_duration: float = Field(default=0.0, alias="totalPauseDuration")
    agent_failures: int = Field(default=0, alias="agentFailures")

class UserSession(BaseModel):
    """User session state."""
    model_config = ConfigDict(populate_by_name=True)

    session_id: str = Field(alias="sessionId")
    user_id: str = Field(alias="userId")
    case_id: str = Field(alias="caseId")
    current_state: ExperienceState = Field(alias="currentState")
    start_time: datetime = Field(alias="startTime")
    last_activity_time: datetime = Field(alias="lastActivityTime")
    state_history: list[StateTiming] = Field(default_factory=list, alias="stateHistory")
    progress: SessionProgress = Field(default_factory=SessionProgress)
    metadata: SessionMetadata = Field(default_factory=SessionMetadata)
```

**Vote Collection:**
```python
class VoteCollection(BaseModel):
    """Collection of votes from all jurors."""
    model_config = ConfigDict(populate_by_name=True)
    
    session_id: str = Field(alias="sessionId")
    votes: list[JurorVote] = Field(default_factory=list)
    collection_start_time: datetime = Field(alias="collectionStartTime")
    collection_end_time: Optional[datetime] = Field(default=None, alias="collectionEndTime")
    result: Optional[VoteResult] = None

class JurorVote(BaseModel):
    """A single juror's vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    vote: Literal["guilty", "not_guilty"]
    timestamp: datetime

class VoteResult(BaseModel):
    """Result of jury voting."""
    model_config = ConfigDict(populate_by_name=True)
    
    verdict: Literal["guilty", "not_guilty"]
    guilty_count: int = Field(alias="guiltyCount")
    not_guilty_count: int = Field(alias="notGuiltyCount")
    juror_breakdown: list[JurorBreakdown] = Field(alias="jurorBreakdown")

class JurorBreakdown(BaseModel):
    """Breakdown of a juror's vote."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    type: Literal["active_ai", "lightweight_ai", "human"]
    vote: Literal["guilty", "not_guilty"]
```

**Dual Reveal Data:**
```python
class GroundTruthReveal(BaseModel):
    """Ground truth information revealed after voting."""
    model_config = ConfigDict(populate_by_name=True)

    actual_verdict: str = Field(alias="actualVerdict")
    explanation: str
    key_evidence: list[str] = Field(alias="keyEvidence")

class DualReveal(BaseModel):
    """Complete dual reveal data structure."""
    model_config = ConfigDict(populate_by_name=True)

    verdict: VoteResult
    ground_truth: GroundTruthReveal = Field(alias="groundTruth")
    reasoning_assessment: ReasoningAssessment = Field(alias="reasoningAssessment")
    juror_reveal: list[JurorReveal] = Field(alias="jurorReveal")

class JurorReveal(BaseModel):
    """Revealed information about a juror."""
    model_config = ConfigDict(populate_by_name=True)
    
    juror_id: str = Field(alias="jurorId")
    type: Literal["active_ai", "lightweight_ai", "human"]
    persona: Optional[str] = None
    vote: Literal["guilty", "not_guilty"]
    key_statements: list[str] = Field(default_factory=list, alias="keyStatements")
```

### Storage Schema

**Case Content Storage (JSON):**
```json
{
  "caseId": "blackthorn-hall-001",
  "title": "The Crown v. Marcus Ashford",
  "narrative": {
    "hookScene": "...",
    "chargeText": "...",
    "victimProfile": {...},
    "defendantProfile": {...},
    "witnessProfiles": [...]
  },
  "evidence": [
    {
      "id": "evidence-001",
      "type": "physical",
      "title": "Forged Will Document",
      "description": "...",
      "timestamp": "2024-01-15T14:30:00Z",
      "presentedBy": "prosecution",
      "significance": "..."
    }
  ],
  "timeline": [...],
  "groundTruth": {
    "actualVerdict": "not_guilty",
    "keyFacts": [...],
    "reasoningCriteria": {...}
  }
}
```

**Session Storage:**
- Sessions stored in memory during active experience
- Persisted to disk/database on state transitions
- 24-hour retention for disconnected sessions
- Cleanup of completed sessions after 7 days

### Data Flow

**Trial Flow:**
```
User starts → Load case content → Initialize state machine
→ Present hook scene → Transition through trial stages
→ Each stage: Generate agent responses → Update SuperBox → Notify Luffa Bot
→ Track timing and enforce constraints
```

**Deliberation Flow:**
```
Judge summing up completes → Initialize jury orchestrator
→ Prompt user for initial thoughts → User statement received
→ Track evidence references → Generate AI juror responses
→ Continue turn-taking for 4-6 minutes → Force transition at 6 minutes
→ Collect anonymous votes → Trigger reasoning evaluation
```

**Reveal Flow:**
```
Votes collected → Calculate verdict → Retrieve ground truth
→ Complete reasoning evaluation → Assemble dual reveal data
→ Display verdict with vote count → Display ground truth
→ Display reasoning assessment → Reveal AI juror identities
→ Offer Luffa Channel sharing
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Case Content Serialization Round-Trip

*For any* valid case content object, serializing to JSON then deserializing back SHALL produce an equivalent object with all fields preserved.

**Validates: Requirements 1.6**

### Property 2: Case Content Validation

*For any* case content object, validation SHALL pass if and only if all required fields are present: narrative (with hookScene, chargeText, victimProfile, defendantProfile, witnessProfiles), evidence array, timeline, groundTruth (with actualVerdict, keyFacts, reasoningCriteria), and character profiles for defendant, victim, and witnesses.

**Validates: Requirements 1.2, 1.4, 1.5**

### Property 3: Trial Stage Sequential Progression

*For any* trial stage, when that stage completes, the state machine SHALL automatically transition to the next stage in the Crown Court procedure order: Charge reading → Prosecution opening → Defence opening → Evidence presentation → Cross-examination → Prosecution closing → Defence closing → Judge summing up → Jury deliberation → Anonymous vote → Dual reveal.

**Validates: Requirements 2.2, 3.4, 5.3, 5.4, 5.5, 7.1, 10.1, 12.1, 18.1**

### Property 4: Stage Skipping Prevention

*For any* trial stage sequence, attempting to transition to a non-adjacent future stage SHALL be rejected, ensuring users cannot skip required stages.

**Validates: Requirements 2.3, 18.4**

### Property 5: Session State Persistence Round-Trip

*For any* user session state, saving the state then restoring it SHALL produce an equivalent session with the same current stage, progress, and user data preserved.

**Validates: Requirements 2.4**

### Property 6: Maximum Duration Enforcement

*For any* user session, the state machine SHALL track elapsed time and enforce a maximum total duration of 20 minutes, automatically transitioning to completion if exceeded.

**Validates: Requirements 2.5**

### Property 7: Hook Scene Content Completeness

*For any* hook scene presentation, the content SHALL include references to the victim, defendant, and central mystery of the case.

**Validates: Requirements 3.3**

### Property 8: Evidence Board Completeness

*For any* case content with N evidence items, the evidence board SHALL display all N items with their descriptions and timestamps, organized chronologically by timestamp.

**Validates: Requirements 4.1, 4.4**

### Property 9: Evidence Highlighting

*For any* evidence item, when that item is presented during trial, the evidence board SHALL update its highlighted item ID to match that evidence item.

**Validates: Requirements 4.2**

### Property 10: Fact Checker Contradiction Detection

*For any* statement made by prosecution or defence during evidence presentation or cross-examination that contradicts case content facts, the fact checker SHALL trigger an intervention citing the specific contradicting evidence item.

**Validates: Requirements 6.1, 6.2**

### Property 11: Fact Checker Intervention Limit

*For any* trial session, the fact checker SHALL intervene a maximum of 3 times, regardless of how many contradictions occur.

**Validates: Requirements 6.3**

### Property 12: Fact Checker Stage Restriction

*For any* statement made during opening speeches or closing speeches, the fact checker SHALL NOT intervene, even if the statement contradicts case content.

**Validates: Requirements 6.4**

### Property 13: Judge Summary Content Requirements

*For any* judge summing up, the content SHALL include: (1) references to key evidence from both prosecution and defence, (2) legal instructions mentioning "burden of proof" and "reasonable doubt", and (3) no explicit opinion on verdict outcome.

**Validates: Requirements 7.2, 7.3, 7.5**

### Property 14: Jury Deliberation User Evidence References

*For any* user statement during jury deliberation that references an evidence item by ID or title, the system SHALL accept and track that reference for reasoning evaluation.

**Validates: Requirements 9.4**

### Property 15: Deliberation Hard Time Limit

*For any* jury deliberation session, when 6 minutes have elapsed, the system SHALL automatically transition to anonymous voting regardless of the current discussion state.

**Validates: Requirements 9.5**

### Property 16: Anonymous Voting Identity Concealment

*For any* voting interface presentation, the interface SHALL display only vote options ("Guilty" and "Not Guilty") without revealing juror identities, and individual votes SHALL NOT be accessible until dual reveal.

**Validates: Requirements 10.2, 10.4, 8.5**

### Property 17: Vote Collection Completeness

*For any* voting session, the system SHALL collect exactly 8 votes (3 active AI + 4 lightweight AI + 1 human) before proceeding to verdict calculation.

**Validates: Requirements 10.3**

### Property 18: Majority Verdict Calculation

*For any* set of 8 votes, the verdict outcome SHALL be "guilty" if 5 or more votes are guilty, and "not guilty" if 5 or more votes are not guilty.

**Validates: Requirements 10.5**

### Property 19: Reasoning Evaluation Four-Category Output

*For any* reasoning evaluation, the output SHALL be exactly one of four categories: "sound_correct", "sound_incorrect", "weak_correct", or "weak_incorrect", determined by combining reasoning quality (sound/weak) with verdict correctness (correct/incorrect).

**Validates: Requirements 11.4**

### Property 20: Reasoning Evaluation Evidence Tracking

*For any* user statement during deliberation that mentions an evidence item, the reasoning evaluator SHALL detect and record that evidence reference for scoring.

**Validates: Requirements 11.2**

### Property 21: Reasoning Evaluation Fallacy Detection

*For any* user statement containing a known logical fallacy (ad hominem, appeal to emotion, false dichotomy, straw man, etc.), the reasoning evaluator SHALL identify and record that fallacy.

**Validates: Requirements 11.3**

### Property 22: Dual Reveal Completeness

*For any* dual reveal presentation, the data SHALL include in sequence: (1) verdict outcome with vote count, (2) ground truth with actual verdict and explanation, (3) user's reasoning evaluation with feedback, and (4) juror identities revealing which were AI with their votes.

**Validates: Requirements 12.2, 12.3, 12.4, 12.5**

### Property 23: Stage Announcement on Transition

*For any* trial stage transition, the Luffa Bot SHALL generate an announcement message containing the new stage name and purpose.

**Validates: Requirements 13.2**

### Property 24: SuperBox Launch Prompts

*For any* trial stage that requires visual content (hook scene, evidence presentation, jury deliberation, dual reveal), the Luffa Bot SHALL prompt the user to launch SuperBox when entering that stage.

**Validates: Requirements 13.3**

### Property 25: New Case Announcement

*For any* new case content added to the system, the Luffa Channel SHALL generate an announcement indicating the case is available.

**Validates: Requirements 15.1**

### Property 26: Completion Share Offer

*For any* user session that reaches the completed state, the system SHALL present an offer to share the verdict outcome to Luffa Channel.

**Validates: Requirements 15.2**

### Property 27: Reasoning Score Privacy

*For any* verdict share to Luffa Channel, the shared data SHALL include verdict outcome but SHALL NOT include the user's reasoning evaluation score or category.

**Validates: Requirements 15.4**

### Property 28: Opt-In Anonymous Sharing

*For any* user who opts in to sharing, the system SHALL post their verdict to Luffa Channel with anonymous attribution (no user ID or name).

**Validates: Requirements 15.5**

### Property 29: Evidence Board Accessibility During Deliberation

*For any* jury deliberation session, the evidence board SHALL remain accessible and return all evidence items when queried.

**Validates: Requirements 4.3**

### Property 30: Pause Duration Limit

*For any* pause between trial stages, the system SHALL allow pausing for up to 2 minutes, then automatically resume or prompt the user to continue.

**Validates: Requirements 18.3**

### Property 31: Progress Indicator Accuracy

*For any* point in the experience, the system SHALL expose the current trial stage in progress indicators, matching the actual state machine state.

**Validates: Requirements 18.5**

### Property 32: Agent Prompt Storage

*For any* trial layer agent (Clerk, Prosecution, Defence, Fact Checker, Judge) and any juror persona (Evidence Purist, Sympathetic Doubter, Moral Absolutist), the system SHALL have a stored system prompt defining their role and constraints.

**Validates: Requirements 19.1, 19.2**

### Property 33: Agent Character Limit Enforcement

*For any* AI agent response, the content length SHALL not exceed the character limit configured for that agent's current trial stage.

**Validates: Requirements 19.3**

### Property 34: Agent Case Context Provision

*For any* AI agent initialization, the agent SHALL receive the complete case content as context before generating any responses.

**Validates: Requirements 19.4**

### Property 35: Agent Information Sequencing

*For any* AI agent response during a trial stage, the content SHALL NOT reference evidence items or facts that have not yet been presented in earlier stages.

**Validates: Requirements 19.5**

### Property 36: Agent Timeout Fallback

*For any* AI agent that fails to respond within 30 seconds, the system SHALL use a predefined fallback response appropriate to that agent's role and current stage.

**Validates: Requirements 20.1**

### Property 37: SuperBox Failure Graceful Degradation

*For any* SuperBox loading failure, the Luffa Bot SHALL provide text-based descriptions of visual content as an alternative.

**Validates: Requirements 20.2**

### Property 38: Reasoning Evaluation Failure Isolation

*For any* reasoning evaluation failure, the system SHALL still proceed to display verdict outcome and truth reveal, omitting only the reasoning assessment portion.

**Validates: Requirements 20.3**

### Property 39: Error Logging Without Interruption

*For any* error that occurs during the experience, the system SHALL log the error details without throwing an exception that interrupts the user's flow.

**Validates: Requirements 20.4**

### Property 40: Critical Failure Recovery Offer

*For any* critical failure that prevents continuation, the system SHALL present the user with an option to restart from the last successfully completed trial stage.

**Validates: Requirements 20.5**

## Error Handling

### Error Categories

**Agent Failures:**
- AI agent timeout (>30 seconds): Use fallback response, log error, continue experience
- AI agent invalid response: Retry once, then use fallback, log error
- AI agent rate limit: Queue request, use fallback if queue exceeds 10 seconds, log error

**Platform Integration Failures:**
- SuperBox load failure: Switch to text-only mode via Luffa Bot, log error
- Luffa Channel unavailable: Disable sharing features, log error, continue experience
- Luffa Bot disconnection: Buffer messages, retry connection, display cached content

**State Management Failures:**
- State persistence failure: Continue in-memory, warn user progress may not save, log error
- State corruption: Attempt recovery from last valid state, offer restart if unrecoverable
- Invalid state transition: Reject transition, log error, maintain current state

**Reasoning Evaluation Failures:**
- Evaluation timeout: Skip reasoning assessment, proceed with verdict and truth reveal
- Evaluation service unavailable: Skip reasoning assessment, log error
- Invalid evaluation result: Use default "evaluation unavailable" message, log error

**Data Validation Failures:**
- Invalid case content: Reject case load, log detailed validation errors, prevent experience start
- Missing evidence items: Log warning, continue with available evidence
- Malformed user input: Sanitize input, log warning, prompt user to rephrase

### Error Recovery Strategies

**Graceful Degradation:**
- Visual content → Text descriptions
- Full reasoning evaluation → Verdict only
- Real-time AI responses → Cached fallback responses
- Multi-agent debate → Single-agent summaries

**State Preservation:**
- Auto-save state every 30 seconds during active stages
- Persist state on every stage transition
- Maintain 24-hour recovery window for disconnected sessions
- Checkpoint before critical operations (voting, evaluation)

**User Communication:**
- Silent recovery for minor errors (agent retries, brief delays)
- Subtle notifications for degraded functionality (text-only mode)
- Clear messages for user-impacting failures (restart offers)
- Never expose technical error details to users

**Fallback Content:**
- Pre-written agent responses for each stage and role
- Generic judge summaries referencing case structure
- Default juror statements for each persona
- Standard procedural announcements

### Logging and Monitoring

**Error Logs:**
- Timestamp, session ID, user ID (anonymized)
- Error type, component, severity level
- Context: current state, recent actions, case ID
- Stack trace for debugging (backend only)

**Metrics to Track:**
- Agent failure rate by role and stage
- Average response times per agent
- State transition success rate
- Reasoning evaluation completion rate
- User session completion rate
- Error recovery success rate

**Alerting Thresholds:**
- Agent failure rate >10% in 5-minute window
- State persistence failure rate >5%
- Critical failures >3 in 1-minute window
- Session completion rate <80% over 1 hour

## Testing Strategy

### Dual Testing Approach

VERITAS requires both unit testing and property-based testing to ensure correctness. Unit tests verify specific examples, edge cases, and integration points, while property-based tests verify universal properties across all inputs. Together, they provide comprehensive coverage: unit tests catch concrete bugs in specific scenarios, while property tests verify general correctness across the input space.

**Note:** The 40 correctness properties defined below remain valid as formal specifications of system behavior. Property-based tests are optional and not yet implemented, but the properties serve as design documentation and can guide future testing efforts.

### Property-Based Testing

**Framework Selection:**
- **Python**: Hypothesis library (chosen for implementation)

**Configuration:**
- Minimum 100 iterations per property test (due to randomization)
- Each test must reference its design document property
- Tag format: `# Feature: veritas-courtroom-experience, Property {number}: {property_text}`

**Property Test Implementation:**

Each of the 40 correctness properties defined above MUST be implemented as a single property-based test. Examples:

**Property 1 (Serialization Round-Trip):**
```python
# Feature: veritas-courtroom-experience, Property 1: Case Content Serialization Round-Trip
from hypothesis import given, strategies as st
import pytest

@given(case_content=case_content_strategy())
def test_case_serialization_round_trip(case_content):
    """For any valid case content, serializing then deserializing produces equivalent object."""
    serialized = case_content.serialize()
    deserialized = CaseContent.deserialize(serialized)
    assert deserialized == case_content
```

**Property 3 (Stage Sequential Progression):**
```python
# Feature: veritas-courtroom-experience, Property 3: Trial Stage Sequential Progression
from hypothesis import given, strategies as st

@given(current_stage=st.sampled_from(list(ExperienceState)))
def test_stage_sequential_progression(current_stage):
    """For any trial stage, completing it transitions to the next stage in Crown Court order."""
    if current_stage == ExperienceState.COMPLETED:
        return  # No next stage
    
    state_machine = StateMachine("test_session", "test_case")
    state_machine.current_state = current_stage
    
    expected_next = STATE_TRANSITIONS.get(current_stage)
    assert state_machine.get_next_state() == expected_next
```

**Property 18 (Majority Verdict Calculation):**
```python
# Feature: veritas-courtroom-experience, Property 18: Majority Verdict Calculation
from hypothesis import given, strategies as st

@given(votes=st.lists(
    st.sampled_from(["guilty", "not_guilty"]),
    min_size=8,
    max_size=8
))
def test_majority_verdict_calculation(votes):
    """For any set of 8 votes, verdict is guilty if ≥5 guilty, else not guilty."""
    jury_orchestrator = JuryOrchestrator()
    
    # Create vote objects
    vote_objects = [
        JurorVote(jurorId=f"juror_{i}", vote=v, timestamp=datetime.now())
        for i, v in enumerate(votes)
    ]
    
    result = jury_orchestrator.calculate_verdict(vote_objects)
    
    guilty_count = sum(1 for v in votes if v == "guilty")
    expected_verdict = "guilty" if guilty_count >= 5 else "not_guilty"
    
    assert result.verdict == expected_verdict
    assert result.guilty_count == guilty_count
    assert result.not_guilty_count == 8 - guilty_count
```

**Generators (Strategies):**

Property tests require Hypothesis strategies for random test data:

```python
from hypothesis import strategies as st
from models import CaseContent, EvidenceItem, CharacterProfile

def character_profile_strategy():
    return st.builds(
        CharacterProfile,
        name=st.text(min_size=1, max_size=50),
        role=st.text(min_size=1, max_size=30),
        background=st.text(min_size=10, max_size=200),
        relevantFacts=st.lists(st.text(min_size=5, max_size=100), min_size=1, max_size=5)
    )

def evidence_item_strategy():
    return st.builds(
        EvidenceItem,
        id=st.text(min_size=1, max_size=20),
        type=st.sampled_from(["physical", "testimonial", "documentary"]),
        title=st.text(min_size=5, max_size=100),
        description=st.text(min_size=10, max_size=500),
        timestamp=st.datetimes().map(lambda dt: dt.isoformat()),
        presentedBy=st.sampled_from(["prosecution", "defence"]),
        significance=st.text(min_size=10, max_size=200)
    )

def case_content_strategy():
    return st.builds(
        CaseContent,
        caseId=st.text(min_size=1, max_size=50),
        title=st.text(min_size=5, max_size=100),
        narrative=narrative_strategy(),
        evidence=st.lists(evidence_item_strategy(), min_size=5, max_size=7),
        timeline=st.lists(timeline_event_strategy(), min_size=3, max_size=10),
        groundTruth=ground_truth_strategy()
    )
```

### Implementation Status

**Completed:**
- Core architecture with all components
- State machine with sequential transitions
- Case manager with validation and caching
- Trial orchestrator with 5 agents and complexity adaptation
- Jury orchestrator with 8 jurors and personas
- Reasoning evaluator with fallacy detection
- LLM service with connection pooling and rate limiting
- Caching system with TTL and cleanup
- Session persistence with multiple backends (file, PostgreSQL, MongoDB)
- Message polling loop with command routing
- Multi-bot architecture support (Phase 28 COMPLETE)
- Group broadcasting with buttons
- Dual reveal assembly and presentation
- Comprehensive unit and integration tests
- Luffa Bot production integration (Phase 22 COMPLETE - all subtasks 22.1-22.5)
- Performance optimizations (Phase 24 COMPLETE - all subtasks 24.1-24.5: connection pooling, caching, session persistence, metrics, load testing)
- Additional case content (Phase 23 COMPLETE - 2 cases: Blackthorn Hall, Digital Deception)
- Performance monitoring (Phase 24.4 COMPLETE - src/metrics.py with MetricsCollector, integrated into orchestrator, trial_orchestrator, state_machine, reasoning_evaluator)
- Load testing (Phase 24.5 COMPLETE - tests/load/ with concurrent user simulation, 500+ ops/sec validated)

**Planned (Not Started):**
- AI jury intelligence (Phase 25 - LLM-based voting replacing deterministic heuristics, evidence-aware deliberation prompts, inter-juror debate dynamics, juror persona identity in messages)
- Case system & replayability (Phase 26 - `/start [case_id]` selection, `/cases` listing, prosecution/defence emphasis variation per run, post-trial aggregate statistics)
- Production hardening (Phase 27 - session timeout auto-cleanup, graceful bot failover, `/metrics` and `/sessions` admin commands, user-visible rate limit feedback)
- Property-based tests for all 40 correctness properties (optional, marked with * in tasks.md)

**Stub Implementations (Interfaces Exist, Not Production-Ready):**
- SuperBox visual rendering: Basic scene models and rendering methods exist in luffa_integration.py, but no actual visual rendering implementation. Text-only fallbacks are used in production.
- Luffa Channel verdict sharing: Interface models exist (ChannelAnnouncement, VerdictShare) with basic methods, but no actual channel API integration. Sharing functionality is not production-ready.
- WebSocket real-time updates: Basic WebSocket endpoint exists in api.py, but multi-bot polling (1-second intervals) is the primary production interface for message delivery.

**Future Enhancements:**
- Web frontend consuming FastAPI backend (React/Vue)
- Witness bots — 2 interactive witness characters users can cross-examine
- LLM-based juror opinion evolution — jurors shift position across deliberation rounds
- Case authoring CLI — guided case creation with automatic complexity scoring
- Multi-language support for prompts and UI text
- Advanced analytics dashboard for trial outcomes

### Unit Testing

**Focus Areas:**

Unit tests should focus on specific examples, edge cases, and integration points that property tests don't cover well:

**Specific Examples:**
- Blackthorn Hall case loads correctly (Requirement 16.1)
- Jury composition is exactly 3 active AI + 4 lightweight AI + 1 human (Requirement 8.1)
- Trial layer has exactly 5 agents with correct roles (Requirement 5.1)
- Evidence board accessible during deliberation state (Requirement 4.3)
- Luffa Bot greeting on experience start (Requirement 13.1)
- User prompted for initial thoughts when deliberation begins (Requirement 9.1)
- Jury personas are Evidence Purist, Sympathetic Doubter, Moral Absolutist (Requirement 8.2)

**Edge Cases:**
- Empty evidence list handling
- Single juror voting (should never happen, but test boundary)
- Zero-length deliberation statements
- Malformed case content JSON
- State machine at final state (no next transition)
- Fact checker at intervention limit (3rd intervention)

**Integration Points:**
- State machine triggers Luffa Bot announcements on transitions
- Evidence board updates when trial orchestrator presents evidence
- Jury orchestrator triggers reasoning evaluator after vote collection
- Case manager provides context to all agents during initialization
- Dual reveal assembles data from vote result, ground truth, and reasoning assessment

**Error Conditions:**
- Agent timeout triggers fallback response
- SuperBox failure triggers text-only mode
- Reasoning evaluation failure still shows verdict
- Invalid state transition is rejected
- Critical failure offers restart

**Timing Constraints:**
- Hook scene duration between 60-90 seconds (Requirement 3.2)
- Judge summing up duration between 90-120 seconds (Requirement 7.4)
- Deliberation duration between 4-6 minutes (Requirement 9.2)
- Total experience targets 15 minutes (Requirement 17.1)

### Test Organization

```
tests/
├── unit/
│   ├── test_state_machine.py
│   ├── test_case_validation.py
│   ├── test_complexity_analyzer.py
│   ├── test_caching.py
│   ├── test_llm_connection_pooling.py
│   ├── test_session.py
│   ├── test_session_async.py
│   ├── test_fact_checker.py
│   ├── test_fact_checker_integration.py
│   ├── test_fact_checker_execution.py
│   ├── test_message_polling.py
│   ├── test_group_broadcasting.py
│   ├── test_metrics.py
│   └── test_integration.py
├── integration/
│   ├── test_e2e_luffa_flow.py
│   ├── test_production.py
│   ├── test_luffa_bot.py
│   ├── test_multi_bot_setup.py
│   ├── test_bot_connectivity.py
│   ├── test_courtroom_group.py
│   ├── test_all_bots_dm.py
│   ├── test_balanced_trial.py
│   ├── test_defence_prompts.py
│   ├── test_defence_multiple_cases.py
│   ├── test_juror_prompts.py
│   ├── test_deliberation_dynamics.py
│   └── validate_fact_checker_integration.py
├── analysis/
│   ├── test_complexity_value.py
│   ├── test_complexity_impact.py
│   ├── test_complexity_progression.py
│   ├── test_complexity_final_assessment.py
│   └── test_juror_comparison.py
├── load/
│   ├── test_metrics_under_load.py
│   └── test_concurrent_users.py
└── property/
    └── (property-based tests to be implemented)

fixtures/  (project root, not under tests/)
├── blackthorn-hall-001.json
├── digital-deception-002.json
└── sample_case.json
```

### Current Test Coverage

**Unit Tests (Implemented):**
- State machine transitions and validation
- Case content loading and validation
- Complexity analyzer scoring and adjustment
- TTL cache operations and expiration
- LLM connection pooling and rate limiting
- Session persistence (file and async backends)
- Fact checker logic and interventions
- Message polling loop and routing
- Group broadcasting with buttons
- Performance metrics collection and aggregation

**Load Tests (Implemented):**
- Metrics system under load (500+ ops/sec)
- Concurrent user simulation (5, 10, 20 sessions)

**Integration Tests (Implemented):**
- End-to-end Luffa Bot flow
- Production environment validation
- Multi-bot setup and coordination
- Bot connectivity and authentication
- Courtroom group interactions
- DM interactions with all bots
- Balanced trial (prosecution vs defence)
- Defence prompt quality across cases
- Juror prompt effectiveness
- Deliberation dynamics and turn-taking
- Fact checker integration

**Analysis Tests (Implemented):**
- Complexity analyzer value validation
- Complexity impact on agent responses
- Complexity progression across cases
- Final complexity assessment
- Juror persona comparison

**Property Tests (To Be Implemented):**
- Case content serialization round-trip (Property 1)
- State machine sequential progression (Property 3)
- Vote collection and verdict calculation (Properties 17, 18)
- Evidence board completeness (Property 8)
- Reasoning evaluation categories (Property 19)
- All 40 correctness properties from design

### Testing Priorities

**Critical Path (Must Test First):**
1. State machine transitions and sequencing (Properties 3, 4, 6)
2. Case content loading and validation (Properties 1, 2)
3. Vote collection and verdict calculation (Properties 17, 18)
4. Dual reveal data assembly (Property 22)

**High Priority:**
5. Fact checker logic (Properties 10, 11, 12)
6. Reasoning evaluation (Properties 19, 20, 21)
7. Evidence board functionality (Properties 8, 9, 29)
8. Error handling and fallbacks (Properties 36-40)

**Medium Priority:**
9. Agent orchestration (Properties 13, 23, 24, 32-35)
10. Timing constraints (Properties 15, 30)
11. Platform integration (Properties 25-28)

**Lower Priority:**
12. Content validation (Properties 7, 31)
13. Privacy and anonymity (Properties 16, 27, 28)

### Manual Testing

Some requirements cannot be fully automated and require manual verification:

- SuperBox visual rendering quality (Requirements 14.1-14.5)
- Luffa Bot tone and style (Requirement 13.5)
- AI agent response quality and believability
- User experience flow and timing feel
- Evidence board usability and clarity
- Dual reveal presentation impact
- Overall 15-minute experience pacing

### Performance Testing

While not covered by correctness properties, performance testing should verify:

- Agent response times under load
- State persistence latency
- Reasoning evaluation completion time
- Concurrent user session handling
- Memory usage during long sessions


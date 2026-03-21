# VERITAS — AI Courtroom Experience

Interactive 15-minute British Crown Court murder trial. Five AI agents perform the trial, you deliberate with 7 AI jurors, vote on a verdict, then a four-part reveal compares your reasoning against the truth.

Runs as a **CLI experience**, **REST/WebSocket API**, or **Luffa group chat bot**.

## Quick Start

```bash
python3 -m venv venv && source venv/bin/activate
pip install -e .
./play.sh
```

Runs in test mode (placeholder responses) without an API key. For real AI responses, copy `.env.example` to `.env`, add your `OPENAI_API_KEY`, and run again. Uses GPT-4o at ~$0.05–0.10 per trial.

## The Case

**The Crown v. Marcus Ashford** — Estate manager accused of poisoning Lord Blackthorn with digoxin. The prosecution builds a compelling narrative (motive, opportunity, confrontation), but the physical evidence favors acquittal: no fingerprints on the glass or medicine cabinet, ambiguous toxicology timeline, and a tight 32-minute window from the security gate log.

7 evidence items across documentary, testimonial, and physical types. Designed so emotional reasoning leads to guilty, analytical reasoning leads to not guilty. Ground truth: **Not Guilty**.

## Experience Flow

```
HOOK SCENE (90s)       Atmospheric opening — the estate, the body, the accused
TRIAL (8 stages)       Charge → Openings → Evidence → Cross-exam → Closings → Judge
DELIBERATION (4-6 min) Discuss with 3 GPT-4o juror personas + 4 GPT-4o-mini jurors
VOTE                   All 8 jurors vote, majority rules (5 of 8)
DUAL REVEAL            Verdict → Truth → Reasoning Assessment → Juror Identities
```

Managed by a 14-state linear FSM with per-stage timing and a 20-minute hard timeout.

## Architecture

```
ExperienceOrchestrator
├── StateMachine             14 sequential states with timing
├── CaseManager              JSON fixture loader, Pydantic validation
├── SessionStore             File-based persistence, 24h retention, auto-save
├── EvidenceBoard            Timeline rendering, filtering, highlighting
├── TrialOrchestrator        5 agents with case-specific prompts and LLM fact checking
├── JuryOrchestrator         3 active AI + 4 lightweight AI + 1 human juror
├── ReasoningEvaluator       Evidence scoring, fallacy detection, coherence
├── ComplexityAnalyzer       Case complexity scoring, adaptive prompt guidance
├── DualRevealAssembler      4-part reveal sequence
├── LLMService               OpenAI/Anthropic async with timeout and fallback
├── MultiBotService          Multi-bot group chat: one Luffa bot per agent
└── ErrorHandler             Graceful degradation, structured logging
```

**Juror personas:** Evidence Purist (demands proof), Sympathetic Doubter (emphasizes doubt), Moral Absolutist (demands justice). Active jurors use GPT-4o; lightweight jurors use GPT-4o-mini.

**Reasoning evaluation:** Tracks which evidence you reference, detects 5 fallacy types (ad hominem, appeal to emotion, false dichotomy, hasty generalization, straw man), and scores logical coherence. Produces one of four outcomes: `sound_correct`, `sound_incorrect`, `weak_correct`, `weak_incorrect`.

## Project Structure

```
src/                             Core source code
├── orchestrator.py              Main coordinator wiring all components
├── state_machine.py             14-state FSM with transitions and timing
├── multi_bot_service.py         Multi-bot Luffa service (main entry point)
├── multi_bot_client_sdk.py      Luffa Bot HTTP client (direct API, multi-bot, auth verification)
├── config.py                    Environment-based config (LLM + Luffa + app settings)
├── trial_orchestrator.py        5 trial agents with stage-specific system prompts
├── jury_orchestrator.py         8-juror deliberation with persona-driven prompts
├── models.py                    Pydantic v2 models (CaseContent, Evidence, Characters)
├── evidence_board.py            Chronological timeline with filtering
├── reasoning_evaluator.py       Evidence tracking, regex fallacy detection, scoring
├── dual_reveal.py               Assembles verdict + truth + assessment + juror reveal
├── llm_service.py               Dual-provider LLM client with connection pooling, rate limiting, retry
├── metrics.py                   Performance monitoring (agent times, session stats, verdict tracking)
├── cache.py                     Three-tier TTL cache (fallback 24h, case 1h, agent 5min)
├── session.py                   UserSession, SessionStore, ReasoningAssessment
├── session_async.py             Async session store with PostgreSQL/MongoDB backends
├── luffa_client.py              Single-bot Luffa HTTP client (legacy)
├── multi_bot_client.py          Per-agent Luffa bot client (legacy)
├── luffa_bot_service.py         Single-bot service runtime (legacy)
├── luffa_integration.py         LuffaBot / SuperBox / LuffaChannel wrappers
├── trial_stages.py              Stage timing configuration and progress tracking
├── complexity_analyzer.py       Case complexity scoring for adaptive prompts
├── error_handling.py            Fallback responses, auto-save, recovery
├── api.py                       FastAPI REST endpoints + WebSocket
├── interactive_demo.py          Terminal-based interactive experience
└── main.py                      Basic automated demo

fixtures/                        Case data
├── blackthorn-hall-001.json     Murder case — Crown v. Marcus Ashford (7 evidence items)
├── digital-deception-002.json   Fraud case — Crown v. Sarah Chen (5 evidence items)
└── sample_case.json             Minimal template for new cases

scripts/                         Utilities
├── verify_system.sh             System health check
├── validate_case.py             Case JSON validator
├── setup/                       Bot registration and configuration
├── debug/                       API connection testing
└── demo/                        Interactive demos

tests/                           244 unit tests + integration + load
├── unit/                        Core logic tests (no API key needed)
├── integration/                 End-to-end Luffa flow, admin commands
├── load/                        Concurrent user simulation
└── analysis/                    Complexity and juror comparison

examples/                        Demo scripts for individual subsystems

docs/                            Reference docs and guides
├── quickstart.md                Setup and first trial walkthrough
├── deployment.md                Production checklist and architecture
├── system-overview.md           Full component and command reference
└── tasks/                       Implementation logs (Phases 21-27)
```

## Running Modes

**CLI Interactive** — full trial in your terminal:
```bash
./play.sh
```

**REST API** — for frontend integration:
```bash
cd src && uvicorn api:app --reload --port 8000
```
Endpoints:
- `POST /api/sessions` — create session
- `POST /api/sessions/{id}/start` — start experience (hook scene)
- `POST /api/sessions/{id}/advance` — advance to next trial stage
- `POST /api/sessions/{id}/statements` — submit deliberation
- `POST /api/sessions/{id}/vote` — submit vote
- `POST /api/sessions/{id}/complete` — complete experience
- `GET /api/sessions/{id}` — get state
- `GET /api/sessions/{id}/evidence` — get evidence board
- `GET /api/cases/{id}` — get case content
- `WS /ws/{id}` — real-time updates
- `GET /health` — health check

API docs at `http://localhost:8000/docs`.

**Luffa Group Chat Bot** — each courtroom agent is a separate bot in a Luffa group:
```bash
# 1. Configure 5 bot UIDs and secrets in .env (see .env.example)
# 2. Create a Luffa group and add all 5 bots
# 3. Start the service
./run_courtroom.sh
```

Commands in the group chat:
- `/start [case_id]` — Begin trial (random case if no ID)
- `/cases` — List available cases with difficulty
- `/continue` — Advance stages (each bot speaks in turn)
- `/evidence` — View evidence board (split by prosecution/defence)
- `/vote guilty` or `/vote not_guilty` — Cast verdict
- `/status` — Check progress
- `/stop` — End current trial
- `/help` — Show commands
- `/metrics` — Performance stats (admin only)
- `/sessions` — Active sessions (admin only)

Prosecution Bot argues for guilt, Defence Bot creates doubt, Judge Bot provides legal instructions. The service polls all 5 bots, deduplicates messages, and filters bot echo to prevent loops.

See `docs/LUFFA_INTEGRATION.md` for API reference and `docs/quickstart.md` for setup.

## Configuration

```bash
# .env
LLM_PROVIDER=openai              # or anthropic
OPENAI_API_KEY=sk-...            # or ANTHROPIC_API_KEY for Claude
LLM_MODEL=gpt-4o                 # lightweight jurors auto-select gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30

LUFFA_BOT_ENABLED=false          # set true for group chat mode
# Multi-bot config: see .env.example for per-agent bot UIDs and secrets

SESSION_TIMEOUT_HOURS=24
MAX_EXPERIENCE_MINUTES=20
```

## Tests

```bash
pytest tests/unit/ -v                    # 244 unit tests, no API key needed
pytest tests/integration/ -v             # Integration tests, requires API keys
scripts/verify_system.sh                       # Full system verification
```

## Cost

| Component | Model | Per Trial |
|-----------|-------|-----------|
| 5 trial agents | GPT-4o | ~$0.03 |
| 3 active jurors | GPT-4o | ~$0.02 |
| 4 lightweight jurors | GPT-4o-mini | ~$0.005 |
| **Total** | | **~$0.05–0.10** |

## Adding Cases

Create a JSON file in `fixtures/` following the structure of `blackthorn-hall-001.json`:

- `caseId`, `title`
- `narrative` — hookScene, chargeText, victim/defendant/witness profiles
- `evidence` — 5–7 items, each with id, type, title, description, timestamp, presentedBy, significance
- `timeline` — chronological events referencing evidence IDs
- `groundTruth` — actualVerdict, keyFacts, reasoningCriteria (required evidence refs, fallacy types, coherence threshold)

## Status

**Working:** 14-state trial flow, 5 AI agents with case-specific prompts, 8-juror deliberation with rich personas, dual-provider LLM (OpenAI + Anthropic), LLM-powered fact checking, complexity-adaptive prompts, reasoning evaluation, dual reveal, REST + WebSocket API, multi-bot Luffa integration (5 bots polling all queues with dedup and echo filtering), evidence board with prosecution/defence split, bot auth verification on startup, file-based session persistence, error handling with fallbacks.

**Recent additions:** LLM-based juror voting (replaces deterministic heuristic), evidence-aware deliberation, juror rotation (2-of-3 per round), juror persona display, `/start [case_id]` case selection with random fallback, `/cases` listing, prosecution/defence emphasis variation, post-trial case statistics, session timeout (30-min warn / 60-min cleanup), bot failover (retry + clerk fallback), `/metrics` and `/sessions` admin commands, rate limit user feedback.

**Planned:** Separate AI juror bots (one per persona), witness bots, more cases, web frontend.

## Documentation

Detailed guides in [`docs/`](docs/):

- **[LUFFA_INTEGRATION.md](docs/LUFFA_INTEGRATION.md)** — Luffa Bot API reference, architecture, bugs fixed
- **[architecture.md](docs/architecture.md)** — Core system components and implementation
- **[multi-bot-architecture.md](docs/multi-bot-architecture.md)** — Multi-bot design: one bot per agent
- **[setup.md](docs/setup.md)** — Installation, configuration, troubleshooting
- **[luffa-guide.md](docs/luffa-guide.md)** — Bot setup, commands, user experience
- **[roadmap.md](docs/roadmap.md)** — Planned refinements and future work

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
├── TrialOrchestrator        5 agents: Clerk, Prosecution, Defence, Fact Checker, Judge
├── JuryOrchestrator         3 active AI + 4 lightweight AI + 1 human juror
├── ReasoningEvaluator       Evidence scoring, fallacy detection, coherence
├── DualRevealAssembler      4-part reveal sequence
├── LLMService               OpenAI/Anthropic async with timeout and fallback
├── LuffaBotService          Group chat bot: polling, commands, session routing
└── ErrorHandler             Graceful degradation, structured logging
```

**Juror personas:** Evidence Purist (demands proof), Sympathetic Doubter (emphasizes doubt), Moral Absolutist (demands justice). Active jurors use GPT-4o; lightweight jurors use GPT-4o-mini.

**Reasoning evaluation:** Tracks which evidence you reference, detects 5 fallacy types (ad hominem, appeal to emotion, false dichotomy, hasty generalization, straw man), and scores logical coherence. Produces one of four outcomes: `sound_correct`, `sound_incorrect`, `weak_correct`, `weak_incorrect`.

## Project Structure

```
src/
├── orchestrator.py         Main coordinator wiring all components
├── state_machine.py        14-state FSM with transitions and timing
├── models.py               Pydantic v2 models (CaseContent, Evidence, Characters)
├── session.py              UserSession, SessionStore, ReasoningAssessment
├── config.py               Environment-based config (LLM + Luffa + app settings)
├── llm_service.py          Dual-provider LLM client (OpenAI / Anthropic)
├── trial_orchestrator.py   5 trial agents with stage-specific system prompts
├── jury_orchestrator.py    8-juror deliberation with persona-driven prompts
├── reasoning_evaluator.py  Evidence tracking, regex fallacy detection, scoring
├── evidence_board.py       Chronological timeline with filtering
├── dual_reveal.py          Assembles verdict + truth + assessment + juror reveal
├── trial_stages.py         Stage timing configuration and progress tracking
├── luffa_client.py         Luffa Bot HTTP client (1s polling, send, buttons)
├── luffa_bot_service.py    Bot runtime: command routing, deliberation, reveal
├── luffa_integration.py    LuffaBot / SuperBox / LuffaChannel wrappers
├── error_handling.py       Fallback responses, auto-save, recovery
├── api.py                  FastAPI REST endpoints + WebSocket
├── interactive_demo.py     Terminal-based interactive experience
└── main.py                 Basic automated demo

fixtures/
├── blackthorn-hall-001.json  Flagship case (murder mystery)
└── sample_case.json          Minimal template for new cases

tests/unit/
├── test_state_machine.py     12 tests — transitions, timing, persistence
├── test_session.py           9 tests — serialization, expiry, cleanup
└── test_integration.py       20 tests — all components end-to-end
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
- `GET /api/sessions/{id}` — get state
- `POST /api/sessions/{id}/statements` — submit deliberation
- `POST /api/sessions/{id}/vote` — submit vote
- `GET /api/cases/{id}` — get case content
- `WS /ws/{id}` — real-time updates
- `GET /health` — health check

API docs at `http://localhost:8000/docs`.

**Luffa Group Chat Bot** — AI agents perform in a group chat:
```bash
# Get bot secret from https://robot.luffa.im, then:
echo "LUFFA_BOT_SECRET=your_secret" >> .env
echo "LUFFA_BOT_ENABLED=true" >> .env
./run_luffa_bot.sh
```
Commands: `/start`, `/continue`, `/vote guilty|not_guilty`, `/evidence`, `/status`, `/help`. During deliberation, type freely — jurors respond to your statements. Each group gets an independent session; concurrent groups supported.

## Configuration

```bash
# .env
LLM_PROVIDER=openai              # or anthropic
OPENAI_API_KEY=sk-...            # or ANTHROPIC_API_KEY for Claude
LLM_MODEL=gpt-4o                 # lightweight jurors auto-select gpt-4o-mini
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000
LLM_TIMEOUT=30

LUFFA_BOT_SECRET=                # from https://robot.luffa.im
LUFFA_BOT_ENABLED=false          # set true for group chat mode

SESSION_TIMEOUT_HOURS=24
MAX_EXPERIENCE_MINUTES=20
```

## Tests

```bash
pytest tests/ -v          # 41 unit tests, no API key needed
python test_production.py # 4 production tests, requires OPENAI_API_KEY
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

## Dependencies

Python 3.10+

| Package | Purpose |
|---------|---------|
| `pydantic>=2.0` | Data models with validation |
| `fastapi>=0.100` | REST API + WebSocket |
| `uvicorn>=0.23` | ASGI server |
| `openai>=1.0` | GPT-4o / GPT-4o-mini |
| `anthropic>=0.18` | Claude (alternative provider) |
| `aiohttp>=3.9` | Async HTTP for Luffa Bot API |
| `python-dotenv>=1.0` | Environment variable loading |
| `pytest>=7.0` | Test framework |
| `hypothesis>=6.0` | Property-based testing |

## Status

**Working:** 14-stage trial flow, 5 AI agents, 8-juror deliberation, dual-provider LLM (OpenAI + Anthropic), reasoning evaluation, dual reveal, REST + WebSocket API, Luffa bot client (awaiting bot secret), file-based session persistence, error handling with fallbacks. 41/41 tests passing.

**Planned:** Character name presentation (named agents vs `[ROLE]` labels), multi-user group voting, auto-advance with pause control, LLM-powered fact checking and AI voting (currently heuristic), web frontend, more cases, property-based tests.

## Documentation

**Setup & Usage**
- `SETUP.md` — Installation, configuration, troubleshooting
- `QUICKSTART.md` — 3-step quick start
- `QUICK_REFERENCE.md` — Commands, status, common issues

**Technical**
- `IMPLEMENTATION_SUMMARY.md` — All components, architecture, experience flow
- `SYSTEM_STATUS.md` — Component status, model config, performance metrics
- `VERIFICATION_REPORT.md` — Test results and production readiness
- `INTEGRATION_COMPLETE.md` — LLM and platform integration details

**Luffa Bot**
- `LUFFA_ARCHITECTURE.md` — System design, message flow, session management
- `LUFFA_DEEP_ANALYSIS.md` — Design decisions: pacing, characters, multi-user, UX
- `LUFFA_INTEGRATION_PLAN.md` — Character system, auto-advance, adaptive story
- `LUFFA_FINAL_PLAN.md` — Implementation timeline and success criteria
- `REFINEMENT_ROADMAP.md` — Prioritized refinement tasks with estimates
- `LUFFA_SETUP.md` — Bot setup guide
- `LUFFA_EXPERIENCE.md` — What users see in group chat
- `GETTING_STARTED_LUFFA.md` — Luffa quick start
- `ACTIVATION_CHECKLIST.md` — Pre-flight checklist for bot launch
- `LUFFA_READY.md` — Activation readiness summary

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**VERITAS** — an interactive British Crown Court trial simulation running on Luffa group chat. Users serve as jurors alongside 7 AI jurors, watch a trial unfold via 5 AI-driven bots (Clerk, Prosecution, Defence, Fact Checker, Judge), deliberate, vote, and receive a dual-layer reveal (verdict + reasoning quality assessment).

- **Language**: Python 3.10+
- **Key deps**: pydantic, fastapi, openai, anthropic, aiohttp, luffa-bot-python-sdk
- **LLM providers**: OpenAI (GPT-4o primary, GPT-4o-mini for lightweight jurors), Anthropic (Claude 3 Sonnet)
- **Platform**: Luffa Bot API at `https://apibot.luffa.im/robot`
- **Luffa group ID**: `Ad1MkyuxDLd`, User UID: `WYspi9HYaHH`

## Commands

### Running the Service

```bash
# Kill any existing instance first (ALWAYS do this before starting)
pkill -f "python.*multi_bot_service"

# Start multi-bot service (primary entry point)
cd src && python -u multi_bot_service.py

# Alternative entry points:
./run_courtroom.sh        # Shell wrapper for multi-bot
./play.sh                 # CLI interactive mode (no API key needed)
cd src && uvicorn api:app --reload --port 8000  # REST API + WebSocket
```

Always use `python -u` for unbuffered output so logs appear in real time.

### Testing

```bash
# All unit tests (no API keys required)
pytest tests/unit/ -v

# Single test file
pytest tests/unit/test_state_machine.py -v

# Single test
pytest tests/unit/test_state_machine.py::TestStateMachine::test_valid_transition -v

# Integration tests (require API keys and bot credentials)
pytest tests/integration/ -v

# System verification script
./verify_system.sh
```

Test config: `asyncio_mode = "auto"` in pyproject.toml — no need for `@pytest.mark.asyncio` on tests.

### Case Validation

```bash
# Validate case JSON files
python scripts/validate_case.py fixtures/blackthorn-hall-001.json
python scripts/validate_case.py fixtures/*.json  # batch
```

## Architecture

### Core Data Flow

```
User sends /start in Luffa group
  → MultiBotService polls ALL 5 bots (1s interval)
  → handle_message() routes commands vs deliberation text
  → ExperienceOrchestrator coordinates all components
  → StateMachine enforces 14-state sequential FSM
  → TrialOrchestrator executes agents via LLMService
  → JuryOrchestrator manages 8-juror deliberation
  → ReasoningEvaluator scores user's logic
  → DualRevealAssembler produces 4-part reveal
  → MultiBotClient sends from appropriate bot
```

### 14-State FSM (Strictly Sequential — No Skipping)

```
NOT_STARTED → HOOK_SCENE → CHARGE_READING → PROSECUTION_OPENING →
DEFENCE_OPENING → EVIDENCE_PRESENTATION → CROSS_EXAMINATION →
PROSECUTION_CLOSING → DEFENCE_CLOSING → JUDGE_SUMMING_UP →
JURY_DELIBERATION → ANONYMOUS_VOTE → DUAL_REVEAL → COMPLETED
```

`submit_vote()` must transition through TWO states: `DELIBERATION → ANONYMOUS_VOTE → DUAL_REVEAL`. The 20-minute hard limit forces completion if exceeded.

### Component Wiring

| Component | File | Responsibility |
|---|---|---|
| **MultiBotService** | `multi_bot_service.py` | Main entry point, polling loop, command routing |
| **MultiBotSDKClient** | `multi_bot_client_sdk.py` | Direct HTTP client for 5 Luffa bots (avoids SDK race condition) |
| **ExperienceOrchestrator** | `orchestrator.py` | Wires all components, manages lifecycle |
| **StateMachine** | `state_machine.py` | 14-state FSM with timing and persistence |
| **TrialOrchestrator** | `trial_orchestrator.py` | 5 trial agents + LLM-powered fact checking (max 3 interventions) |
| **JuryOrchestrator** | `jury_orchestrator.py` | 8 jurors (3 active AI + 4 lightweight + 1 human), deliberation, voting |
| **LLMService** | `llm_service.py` | OpenAI/Anthropic calls with connection pooling, rate limiting, retries |
| **CaseManager** | `case_manager.py` | Loads/validates case JSON from `fixtures/`, caches with 1h TTL |
| **ReasoningEvaluator** | `reasoning_evaluator.py` | Scores evidence references, coherence, fallacy detection |
| **DualRevealAssembler** | `dual_reveal.py` | 4-part reveal: verdict → truth → assessment → juror identities |
| **ResponseCache** | `cache.py` | Multi-level TTL cache (24h fallback, 1h case, 5m agent) |
| **Models** | `models.py` | Pydantic models with camelCase JSON aliases |

### Multi-Bot Architecture

Up to 10 bots with separate UID/secret in `.env`. The `MultiBotSDKClient` uses direct HTTP calls (not the SDK) because the luffa-bot-python-sdk has a global `robot_key` race condition when managing multiple bots.

**Trial agents (5)**: Clerk, Prosecution, Defence, Fact Checker, Judge
**Character bots (3, optional)**: Witness 1, Witness 2 (first 2 witnesses from case data), Defendant
**Juror bots (2, optional)**: Juror 1 (Evidence Purist), Juror 2 (Sympathetic Doubter)

Witnesses testify during EVIDENCE_PRESENTATION and respond under CROSS_EXAMINATION. Defendant testifies and is cross-examined. If character/juror bots not configured, their messages route through clerk.

**Polling**: Every 1 second, polls `/receive` on ALL configured bots — Luffa delivers group messages to each bot independently. Messages deduplicated by `msgId` (max 5000 tracked). Bot-originated messages filtered by `sender_uid` to prevent echo loops.

### Jury System

- **3 Active AI Jurors** with distinct personas (Evidence Purist, Sympathetic Doubter, Moral Absolutist) — use GPT-4o
- **4 Lightweight AI Jurors** — minimal responses via GPT-4o-mini
- **1 Human Juror** — the user
- **Voting**: Majority rule (5+ of 8 = verdict). AI votes use LLM-based analysis of each juror's deliberation statements + case evidence (temperature 0.3, JSON response). Falls back to persona heuristic on LLM failure.
- **Deliberation**: 6-minute hard cutoff. Active jurors respond within 15s per turn.

### Fact Checking

During EVIDENCE_PRESENTATION and CROSS_EXAMINATION only. LLM checks statements against case evidence (temperature 0.1, 10s timeout). Requires 70% confidence to intervene. Max 3 interventions per trial.

## Luffa Bot API — Critical Gotchas

These are hard-won lessons. Violating any will cause subtle bugs:

1. **HTTP 200 on auth failure** — API returns 200 even when auth fails. Real error is in body: `{"code":500,"msg":"Robot verification failed"}`. Always check the `code` field.
2. **Empty body on success** — `/send` and `/sendGroup` may return empty body (not JSON) on success. Handle gracefully.
3. **Group messages go to ALL bots** — Must poll all 5 bots, not just clerk. Each receives every group message independently.
4. **Echo filtering required** — Bot A's messages appear in Bot B's `/receive`. Filter by `sender_uid` matching known bot UIDs.
5. **Type field ambiguity** — `type` may be int or string. Always convert with `int()`.
6. **Slow bots** — Some take up to 20s to respond. Use 30s timeout.
7. **dict.get() with None** — `dict.get("key", default)` returns `None` (not `default`) when key exists with value `None`. Use `(val or default)` pattern.
8. **Bot admin**: https://robot.luffa.im — regenerate secrets here when auth fails.
9. **SDK source**: https://github.com/sabma-labs/luffa-bot-python-sdk

## Case Content Format

Cases are JSON files in `fixtures/`. Two available cases:
- `blackthorn-hall-001.json` — Murder case, Crown v. Marcus Ashford (ground truth: NOT GUILTY)
- `digital-deception-002.json` — Fraud case, Crown v. Sarah Chen (ground truth: NOT GUILTY)

Evidence count constrained to 5-7 items (Pydantic validator). Three evidence types: `physical`, `testimonial`, `documentary`. All Pydantic models use `camelCase` JSON aliases with `populate_by_name=True` — so both `case_id` and `caseId` work in Python, but JSON must use camelCase.

## Environment Variables

Copy `.env.example` to `.env`. Key groups:

- **LLM**: `LLM_PROVIDER`, `OPENAI_API_KEY`/`ANTHROPIC_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `LLM_MAX_TOKENS`, `LLM_TIMEOUT`
- **Connection pooling**: `LLM_CONNECTION_POOL_SIZE` (default 10), `LLM_CONNECT_TIMEOUT`, `LLM_READ_TIMEOUT`
- **Rate limiting**: `LLM_RATE_LIMIT_RPM` (default 60), `LLM_RATE_LIMIT_TPM` (default 90000)
- **Bots**: `LUFFA_BOT_{CLERK|PROSECUTION|DEFENCE|FACT_CHECKER|JUDGE}_{UID|SECRET}`
- **Sessions**: `SESSION_STORAGE_BACKEND` (file/postgresql/mongodb), `SESSION_TIMEOUT_HOURS` (default 24)

## Key Patterns

- **All I/O is async** — `async/await` throughout. Use `asyncio.run()` at entry points.
- **Graceful degradation** — LLMService returns `(text, used_fallback: bool)`. If LLM fails after retries, case-specific fallback text is used so the experience continues.
- **Token bucket rate limiting** — Tracks both requests/minute and tokens/minute with sliding windows.
- **Pydantic everywhere** — All data structures are validated Pydantic models with JSON serialization.
- **Imports from `src/`** — Source files import each other by module name (e.g., `from config import load_config`), not package paths. Must `cd src` before running, or configure `PYTHONPATH`.

## Known Limitations & Planned Work

- No web frontend — planned: React/Vue UI consuming the FastAPI backend
- Witness/defendant bots only speak during evidence presentation and cross-examination (2 of 14 stages)

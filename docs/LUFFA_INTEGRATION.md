# Luffa Bot Integration — Technical Reference

## API Contract

Base URL: `https://apibot.luffa.im/robot`

| Endpoint | Method | Body | Response |
|----------|--------|------|----------|
| `/receive` | POST | `{"secret": "<bot_secret>"}` | `{"code":200, "data":[...]}` or `[]` |
| `/send` | POST | `{"secret": "<bot_secret>", "uid": "<user_id>", "msg": "<json_string>"}` | Empty body on success |
| `/sendGroup` | POST | `{"secret": "<bot_secret>", "uid": "<group_id>", "msg": "<json_string>", "type": "1"\|"2"}` | Empty body on success |

**Message format**: The `msg` field is a JSON-encoded string: `JSON.stringify({"text": "...", "button": [...], ...})`

**Message types**: `"1"` = text only, `"2"` = text with interactive buttons

### Critical API Behaviors

1. **HTTP 200 on auth failure**: The API returns HTTP 200 even when authentication fails. The real error is in the JSON body: `{"code": 500, "msg": "Robot verification failed"}`. Always check the `code` field.

2. **Empty response on send success**: `/send` and `/sendGroup` may return an empty body (not JSON) on success. Handle this gracefully.

3. **Independent message delivery**: Group messages are delivered to ALL bots' receive queues independently. Each bot gets its own copy with the same `msgId`. You must poll ALL bots, not just one.

4. **Bot cross-pollination**: Bot A's sent messages appear in Bot B's `/receive` poll. Filter out messages where `sender_uid` matches any of your bot UIDs.

5. **Type field inconsistency**: The `type` field in received messages may be an integer (`0`, `1`) or a string (`"0"`, `"1"`). Always convert with `int()`.

6. **Variable response times**: Some bots respond in 0.3s, others take up to 20s. Use a 30s timeout.

## Architecture

```
User types in Luffa group
    |
    v
All 5 bots receive the message (independent queues)
    |
    v
Service polls ALL bots each cycle (1s interval)
    |
    v
Dedup by msgId (shared set, max 5000)
    |
    v
Filter out bot-originated messages (by sender_uid)
    |
    v
handle_message() -> command or deliberation
    |
    v
Orchestrator processes -> generates AI responses
    |
    v
Send reply from appropriate bot (clerk/prosecution/defence/judge)
```

## Bot Configuration

5 bots in `.env`, each with UID + secret:

| Role | Env UID | Env Secret | Purpose |
|------|---------|------------|---------|
| Clerk | `LUFFA_BOT_CLERK_UID` | `LUFFA_BOT_CLERK_SECRET` | Orchestration, announcements |
| Prosecution | `LUFFA_BOT_PROSECUTION_UID` | `LUFFA_BOT_PROSECUTION_SECRET` | Prosecution arguments |
| Defence | `LUFFA_BOT_DEFENCE_UID` | `LUFFA_BOT_DEFENCE_SECRET` | Defence arguments |
| Fact Checker | `LUFFA_BOT_FACT_CHECKER_UID` | `LUFFA_BOT_FACT_CHECKER_SECRET` | Contradiction detection |
| Judge | `LUFFA_BOT_JUDGE_UID` | `LUFFA_BOT_JUDGE_SECRET` | Legal instructions, summing up |

Bot admin panel: https://robot.luffa.im

## State Machine

```
NOT_STARTED -> HOOK_SCENE -> CHARGE_READING -> PROSECUTION_OPENING
-> DEFENCE_OPENING -> EVIDENCE_PRESENTATION -> CROSS_EXAMINATION
-> PROSECUTION_CLOSING -> DEFENCE_CLOSING -> JUDGE_SUMMING_UP
-> JURY_DELIBERATION -> ANONYMOUS_VOTE -> DUAL_REVEAL -> COMPLETED
```

Transitions are strictly sequential. `submit_vote()` must transition through ANONYMOUS_VOTE before DUAL_REVEAL.

## Commands

| Command | Stage | Action |
|---------|-------|--------|
| `/start` | Any (no active trial) | Begin new trial |
| `/stop` | Any (active trial) | Clear session, stop trial |
| `/continue` | Trial stages | Advance to next stage |
| `/evidence` | Any (active trial) | Show evidence board |
| `/status` | Any (active trial) | Show current progress |
| `/vote guilty` | Deliberation | Cast guilty verdict |
| `/vote not_guilty` | Deliberation | Cast not guilty verdict |
| `/help` | Any | Show command list |

## Running the Service

```bash
# Start
cd ai-court
source venv/bin/activate
cd src && python -u multi_bot_service.py

# Or use the script
./run_courtroom.sh
```

Always ensure only ONE service instance is running. Multiple instances compete for messages from the same bot queues.

To kill stale instances: `pkill -f "python.*multi_bot_service"`

## Known Limitations

1. **Deterministic AI votes**: AI juror votes are hardcoded by persona (sympathetic_doubter always not_guilty, moral_absolutist always guilty, others by hash). Marked `# TODO` for LLM-based voting.

2. **Single case**: Only `blackthorn-hall-001` case available.

3. **Max duration**: 20-minute hard limit on trial duration. State machine forces completion if exceeded.

## Bugs Fixed in This Session

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| API URL default wrong | `https://api.luffa.im` (doesn't exist) | Changed to `https://apibot.luffa.im/robot` |
| Auth failures silent | API returns HTTP 200 on auth error, code only checked HTTP status | Check `code` field in response body |
| Send crashes on success | `/send` returns empty body, parsed as JSON fails | Handle empty response as success |
| `button=` TypeError | Parameter name mismatch (`button` vs `buttons`) | Fixed all 6 call sites |
| `/evidence` KeyError | Used `timeline` dict (no `description`) instead of `items` | Use `items` with full EvidenceItem data |
| `/status` KeyError | Wrong key `currentStage` vs actual `current_stage` | Use correct snake_case keys |
| `sender_uid` = group ID | `msg["uid"]` is group ID for group messages | Use `msg["sender_uid"]` |
| Vote always fails | `submit_vote()` skips ANONYMOUS_VOTE state | Add intermediate transition |
| Deliberation not saved | Early return bypasses `_save_progress()` | Save before return |
| `persona` None crash | `dict.get("persona", "")` returns None when key exists as null | Use `(... or "")` |
| Only clerk polled | Messages delivered to all bots independently | Poll all 5 bots |
| Bot echo loop risk | Bot messages appear in other bots' polls | Filter by `sender_uid` in `bot_uids` |
| `dismissType` wrong | Vote buttons persisted, continue buttons disappeared | Configurable `dismiss_type` parameter |
| Old SDK crashes on import | `luffa_client_sdk.py` top-level `import luffa_bot` | File deleted |
| Shell scripts fail | Missing PYTHONPATH, wrong secret checks | Fixed paths and checks |
| Vote fallback KeyError | Reasoning failure path returns no `dual_reveal` key | Guard with `if "dual_reveal" in` |
| Type coercion | API may return `"1"` string vs `1` int for type | `int()` with try/except |

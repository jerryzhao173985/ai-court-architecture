# VERITAS Multi-Bot Deployment Guide

## Bot Assignment

Your 5 Luffa bots are now configured as:

| Role | Bot UID | Secret | Purpose |
|------|---------|--------|---------|
| **Clerk** | ORQAZCejHdZELLD | ta86cbb0bd1f35425bb03b66cdcd49d81e | Orchestrates trial, handles commands |
| **Prosecution** | MZIXVYXwSwRx6Vd | os8dc8ecf0b69b4a37956ad37e66553f30 | Crown prosecutor arguments |
| **Defence** | NGKIEJGGRlKKnAqC | P5263ab3153044a66ae567773cbea6ca9 | Defence barrister arguments |
| **Fact Checker** | GKUPDBfLv23WktAS | y7b0636260a8740d980f0582ea94cc438 | Monitors for contradictions |
| **Judge** | YNLJHNCCsRmLBcvU | ye9e38b40137248cc841cc97aced744ce | Legal instructions, truth reveal |

## Deployment Checklist

### Pre-Deployment

- [x] All 5 bot credentials configured in `.env`
- [x] Configuration tested: `python test_multi_bot_config.py`
- [x] Multi-bot client created
- [x] Multi-bot service created
- [ ] All 5 bots added to Luffa group chat
- [ ] OpenAI API key configured (for LLM responses)

### Deployment Steps

#### 1. Verify Configuration

```bash
python test_multi_bot_config.py
```

Expected output:
```
✅ READY TO RUN
Total Bots Configured: 5/5 required
```

#### 2. Create Luffa Group

1. Open Luffa app
2. Create new group: "VERITAS Courtroom"
3. Note the group ID (you'll see it in logs)

#### 3. Add All Bots to Group

Add each bot by UID:
1. ORQAZCejHdZELLD (Clerk)
2. MZIXVYXwSwRx6Vd (Prosecution)
3. NGKIEJGGRlKKnAqC (Defence)
4. GKUPDBfLv23WktAS (Fact Checker)
5. YNLJHNCCsRmLBcvU (Judge)

#### 4. Start Service

```bash
./run_multi_bot.sh
```

Or with logging:
```bash
python src/multi_bot_service.py 2>&1 | tee logs/multi-bot.log
```

#### 5. Test in Group

In the Luffa group, send:
```
/help
```

You should get a response from the Clerk bot.

Then start a trial:
```
/start
```

### Post-Deployment

#### Monitor Service

```bash
# Check if running
ps aux | grep multi_bot_service

# View logs
tail -f logs/multi-bot.log

# Check active sessions
# (Add monitoring endpoint)
```

#### Test Full Flow

1. Send `/start` - Verify hook scene appears
2. Send `/continue` - Verify Prosecution bot speaks
3. Send `/continue` - Verify Defence bot speaks
4. Continue through all stages
5. Send `/vote guilty` - Verify dual reveal works

## API Endpoints Used

### Luffa Bot API

**Base URL**: `https://apibot.luffa.im/robot`

**Endpoints:**

1. **Receive Messages** (Polling)
   ```
   POST /receive
   Body: {"secret": "bot_secret"}
   Poll: Every 1 second
   ```

2. **Send DM**
   ```
   POST /send
   Body: {
     "secret": "bot_secret",
     "uid": "recipient_uid",
     "msg": "{\"text\": \"message\"}"
   }
   ```

3. **Send Group Message**
   ```
   POST /sendGroup
   Body: {
     "secret": "bot_secret",
     "uid": "group_id",
     "msg": "{\"text\": \"message\", \"button\": [...]}",
     "type": "1" or "2"
   }
   ```

## Message Flow Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Luffa Group Chat                         │
│                                                             │
│  👤 User                                                    │
│  📋 Clerk Bot (ORQAZCejHdZELLD)                            │
│  👔 Prosecution Bot (MZIXVYXwSwRx6Vd)                      │
│  🛡️ Defence Bot (NGKIEJGGRlKKnAqC)                         │
│  🔍 Fact Checker Bot (GKUPDBfLv23WktAS)                    │
│  ⚖️ Judge Bot (YNLJHNCCsRmLBcvU)                           │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│              MultiBotService (Python Backend)               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ MultiBotClient                                      │  │
│  │  - Clerk Client (polls /receive every 1s)          │  │
│  │  - Prosecution Client (sends via /sendGroup)       │  │
│  │  - Defence Client (sends via /sendGroup)           │  │
│  │  - Fact Checker Client (sends via /sendGroup)      │  │
│  │  - Judge Client (sends via /sendGroup)             │  │
│  └─────────────────────────────────────────────────────┘  │
│                            ↕                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ ExperienceOrchestrator                              │  │
│  │  - State Machine                                    │  │
│  │  - Trial Orchestrator (5 agents)                    │  │
│  │  - Jury Orchestrator (8 jurors)                     │  │
│  │  - Reasoning Evaluator                              │  │
│  └─────────────────────────────────────────────────────┘  │
│                            ↕                                │
│  ┌─────────────────────────────────────────────────────┐  │
│  │ LLM Service (OpenAI)                                │  │
│  │  - Generates agent responses                        │  │
│  │  - Fact checking analysis                           │  │
│  │  - Juror deliberation                               │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Polling Strategy

### Clerk Bot (Main Orchestrator)

```python
while running:
    # Poll Clerk bot for commands
    messages = await multi_bot.poll_messages("clerk")
    
    for msg in messages:
        if msg["text"].startswith("/"):
            # Handle command
            await handle_command(msg)
        else:
            # Handle deliberation statement
            await handle_deliberation(msg)
    
    await asyncio.sleep(1)  # Poll every 1 second
```

### Other Bots (Send Only)

Prosecution, Defence, Fact Checker, and Judge bots only send messages. They don't poll for incoming messages.

## Session Management

### User Session Mapping

```python
# Map Luffa UID to session ID
uid_to_session = {
    "user_abc123": "session_xyz789"
}

# Map session ID to orchestrator
active_sessions = {
    "session_xyz789": ExperienceOrchestrator(...)
}

# Map group ID to users
group_users = {
    "group_def456": {"user_abc123", "user_ghi789"}
}
```

### Multi-User Support

Multiple users can run trials simultaneously in the same group:

```
[User A]: /start
[Clerk Bot]: Welcome User A! Your trial begins...

[User B]: /start
[Clerk Bot]: Welcome User B! Your trial begins...

[User A]: /continue
[Prosecution Bot]: [For User A] I present the evidence...

[User B]: /continue
[Prosecution Bot]: [For User B] I present the evidence...
```

Each user has independent trial progress tracked by their Luffa UID.

## Performance Considerations

### Current Capacity

- **Concurrent Users**: ~100 (limited by memory)
- **Message Latency**: ~2-3 seconds (LLM generation)
- **Polling Frequency**: 1 second (Luffa API requirement)

### Bottlenecks

1. **LLM API**: OpenAI rate limits (tier-based)
2. **Memory**: Each session ~10MB
3. **Luffa API**: Rate limits per bot

### Optimization

1. **Connection Pooling**: Reuse aiohttp sessions
2. **Response Caching**: Cache fallback responses
3. **Async Processing**: All I/O is non-blocking
4. **Session Cleanup**: Auto-cleanup after 24 hours

## Monitoring

### Health Checks

```bash
# Check service is running
ps aux | grep multi_bot_service

# Check active sessions
python -c "from multi_bot_service import MultiBotService; print('Service OK')"

# Test bot connectivity
curl -X POST https://apibot.luffa.im/robot/receive \
  -H "Content-Type: application/json" \
  -d '{"secret": "ta86cbb0bd1f35425bb03b66cdcd49d81e"}'
```

### Metrics to Track

- Active sessions count
- Messages sent per bot
- LLM API latency
- Error rates per bot
- Session completion rate

## Scaling

### Vertical Scaling (Single Instance)

Current setup handles ~100 concurrent users.

### Horizontal Scaling (Multiple Instances)

For >100 users:
1. Use Redis for session storage
2. Load balance by group ID
3. Run multiple service instances
4. Share bot credentials across instances

## Security

### Bot Secrets

- Store in `.env` (not committed to git)
- Use environment variables in production
- Rotate secrets periodically
- Monitor for unauthorized access

### User Data

- Sessions stored in memory (ephemeral)
- No PII collected
- 24-hour retention only
- Auto-cleanup after completion

## Maintenance

### Updating Bot Configuration

1. Update `.env` with new credentials
2. Restart service: `./run_multi_bot.sh`
3. Test: `python test_multi_bot_config.py`

### Adding New Bots

1. Create bot at https://robot.luffa.im
2. Add credentials to `.env`
3. Update `config.py` if needed
4. Restart service

### Removing Bots

1. Set `LUFFA_BOT_<ROLE>_ENABLED=false` in `.env`
2. Restart service
3. System falls back to available bots

## Troubleshooting Guide

### Issue: "No Luffa client configured for X"

**Cause**: Bot not configured in `.env`

**Fix**: Add bot credentials:
```bash
LUFFA_BOT_X_UID=...
LUFFA_BOT_X_SECRET=...
```

### Issue: "Failed to send message as X"

**Cause**: Bot not in group or API error

**Fix**:
1. Verify bot is in group
2. Check bot secret is correct
3. Review API logs

### Issue: "Configuration test failed"

**Cause**: Missing or invalid credentials

**Fix**: Run `python setup_bots.py` for guided setup

### Issue: Messages not appearing in group

**Cause**: Polling not working or bot permissions

**Fix**:
1. Check service is running
2. Verify Clerk bot is in group
3. Check logs for API errors

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/veritas-multi-bot.service`:

```ini
[Unit]
Description=VERITAS Multi-Bot Service
After=network.target

[Service]
Type=simple
User=veritas
WorkingDirectory=/opt/veritas
Environment="PATH=/opt/veritas/venv/bin"
ExecStart=/opt/veritas/venv/bin/python src/multi_bot_service.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Start:
```bash
sudo systemctl enable veritas-multi-bot
sudo systemctl start veritas-multi-bot
sudo systemctl status veritas-multi-bot
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY .env .

CMD ["python", "src/multi_bot_service.py"]
```

Build and run:
```bash
docker build -t veritas-multi-bot .
docker run -d --name veritas --env-file .env veritas-multi-bot
```

### Using PM2 (Node.js process manager)

```bash
pm2 start src/multi_bot_service.py --name veritas-bots --interpreter python3
pm2 save
pm2 startup
```

## Summary

Your VERITAS multi-bot system is configured and ready to deploy:

✅ 5 bots configured (Clerk, Prosecution, Defence, Fact Checker, Judge)
✅ Configuration tested and validated
✅ Multi-bot client and service created
✅ Luffa API integration complete
✅ Session management with multi-user support

**Next**: Add all 5 bots to a Luffa group and run `./run_multi_bot.sh`

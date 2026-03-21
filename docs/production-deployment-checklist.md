# VERITAS Production Deployment Checklist

## Quick Start

```bash
# 1. Verify configuration
python tests/integration/test_e2e_luffa_flow.py

# 2. Start the service
python src/multi_bot_service.py

# 3. Test in Luffa group
# Send: /start
```

## Pre-Deployment Verification

### ✅ Configuration Check

```bash
# Check all required environment variables
grep -E "LUFFA_BOT_(CLERK|PROSECUTION|DEFENCE|FACT_CHECKER|JUDGE)_(UID|SECRET)" .env

# Should show 10 lines (5 bots × 2 variables each)
```

### ✅ Bot Authentication

```bash
# Run E2E test to verify all bots authenticate
python tests/integration/test_e2e_luffa_flow.py

# Expected: "✅ ALL TESTS PASSED (7/7)"
```

### ✅ Group Setup

1. Open Luffa app
2. Navigate to group: Ad1MkyuxDLd
3. Verify all 5 bots are members:
   - Clerk (MDxaEfAbC8J)
   - Prosecution (2fPGmAnhowc)
   - Defence (JTNTR5vjhSd)
   - Fact Checker (hFawR8U4iX1)
   - Judge (h3xYBbwhx9d)

### ✅ API Keys

```bash
# Verify OpenAI API key is set
echo $OPENAI_API_KEY

# Or check .env
grep OPENAI_API_KEY .env
```

## Deployment

### Option 1: Direct Execution

```bash
# Start service in foreground
python src/multi_bot_service.py

# Press Ctrl+C to stop
```

### Option 2: Background Process

```bash
# Start in background with logging
nohup python src/multi_bot_service.py > logs/multi-bot.log 2>&1 &

# Check process
ps aux | grep multi_bot_service

# View logs
tail -f logs/multi-bot.log

# Stop service
pkill -f multi_bot_service
```

### Option 3: systemd Service (Linux)

```bash
# Create service file
sudo nano /etc/systemd/system/veritas-multi-bot.service

# Add content (see docs/bot-deployment-guide.md)

# Enable and start
sudo systemctl enable veritas-multi-bot
sudo systemctl start veritas-multi-bot

# Check status
sudo systemctl status veritas-multi-bot

# View logs
sudo journalctl -u veritas-multi-bot -f
```

## Post-Deployment Testing

### Test 1: Bot Responds to Commands

In Luffa group, send:
```
/help
```

Expected response from Clerk bot:
```
🎭 VERITAS COURTROOM EXPERIENCE

Commands:
• /start - Begin a new trial
• /continue - Advance to next stage
...
```

### Test 2: Start Trial

In Luffa group, send:
```
/start
```

Expected:
1. Clerk bot greets you
2. Hook scene is presented
3. Prompt to /continue appears

### Test 3: Complete Flow

```
/start
/continue  (repeat through all stages)
/vote guilty
```

Expected:
1. All 5 bots speak in their roles
2. Deliberation with AI jurors
3. Dual reveal with verdict, truth, reasoning

### Test 4: Multi-User

Have 2 users in the group both send:
```
User A: /start
User B: /start
```

Expected:
- Both users get independent trials
- No interference between sessions

## Monitoring

### Health Checks

```bash
# Check service is running
ps aux | grep multi_bot_service

# Check memory usage
ps aux | grep multi_bot_service | awk '{print $4}'

# Check active sessions (add to service)
# curl http://localhost:8000/health
```

### Log Monitoring

```bash
# View real-time logs
tail -f logs/multi-bot.log

# Search for errors
grep ERROR logs/multi-bot.log

# Count active sessions
grep "session created" logs/multi-bot.log | wc -l
```

### Key Metrics

Monitor these in logs:
- Bot authentication success/failure
- Message send success/failure
- LLM API response times
- Session creation/completion
- Error rates

## Troubleshooting

### Issue: Bot Not Responding

**Symptoms**: No response to /help or /start

**Diagnosis**:
```bash
# Check service is running
ps aux | grep multi_bot_service

# Check logs for errors
tail -50 logs/multi-bot.log | grep ERROR
```

**Solutions**:
1. Verify bot is in group
2. Check bot credentials in .env
3. Restart service
4. Run E2E test to verify auth

### Issue: "AUTH FAILED" in Logs

**Symptoms**: Logs show "Robot verification failed"

**Diagnosis**:
```bash
# Check which bot failed
grep "AUTH FAILED" logs/multi-bot.log
```

**Solutions**:
1. Bot secrets may be expired
2. Regenerate at https://robot.luffa.im
3. Update .env with new secrets
4. Restart service

### Issue: LLM Timeout

**Symptoms**: "LLM request timed out" in logs

**Diagnosis**:
```bash
# Check LLM response times
grep "LLM response" logs/multi-bot.log
```

**Solutions**:
1. Check OpenAI API status
2. Increase timeout in .env: LLM_TIMEOUT=60
3. Switch to faster model: LLM_MODEL=gpt-4o-mini
4. Restart service

### Issue: Session Not Found

**Symptoms**: User gets "No active trial" message

**Diagnosis**:
```bash
# Check session storage
ls -la data/sessions/

# Check session expiry
grep "session expired" logs/multi-bot.log
```

**Solutions**:
1. Sessions expire after 24 hours
2. User needs to /start a new trial
3. Check session storage is writable

## Scaling

### Current Capacity

- **Concurrent users**: ~100
- **Memory per session**: ~50MB
- **Bottleneck**: LLM API rate limits

### Scaling Up

For >100 concurrent users:

1. **Vertical Scaling**:
   - Increase server memory
   - Use faster LLM model
   - Optimize session storage

2. **Horizontal Scaling**:
   - Use Redis for session storage
   - Load balance by group ID
   - Run multiple service instances
   - Share bot credentials

## Maintenance

### Daily Tasks

- Check logs for errors
- Monitor active sessions
- Verify bot authentication

### Weekly Tasks

- Review error rates
- Check LLM API usage
- Clean up old sessions
- Update bot secrets if needed

### Monthly Tasks

- Review performance metrics
- Optimize LLM prompts
- Update dependencies
- Test disaster recovery

## Emergency Procedures

### Service Crash

```bash
# Restart service
pkill -f multi_bot_service
python src/multi_bot_service.py &

# Or with systemd
sudo systemctl restart veritas-multi-bot
```

### Bot Credentials Compromised

```bash
# 1. Regenerate all bot secrets at https://robot.luffa.im
# 2. Update .env with new secrets
# 3. Restart service
# 4. Run E2E test to verify
python tests/integration/test_e2e_luffa_flow.py
```

### Database Corruption

```bash
# Sessions are in data/sessions/
# Backup and clear if corrupted
cp -r data/sessions/ data/sessions.backup/
rm data/sessions/*.json

# Service will create new sessions
```

## Performance Optimization

### Reduce LLM Latency

```bash
# Use faster model
LLM_MODEL=gpt-4o-mini

# Reduce max tokens
LLM_MAX_TOKENS=1000

# Increase temperature for faster generation
LLM_TEMPERATURE=0.9
```

### Reduce Memory Usage

```bash
# Limit concurrent sessions
MAX_CONCURRENT_SESSIONS=50

# Reduce session timeout
SESSION_TIMEOUT_HOURS=12

# Clean up completed sessions immediately
AUTO_CLEANUP=true
```

## Security

### Best Practices

1. **Never commit .env to git**
   - Already in .gitignore
   - Use environment variables in production

2. **Rotate bot secrets regularly**
   - Every 90 days recommended
   - Update .env and restart

3. **Monitor for abuse**
   - Track session creation rate
   - Limit sessions per user
   - Block spam commands

4. **Secure API keys**
   - Use environment variables
   - Restrict file permissions: chmod 600 .env
   - Use secrets manager in production

## Backup and Recovery

### Backup Session Data

```bash
# Backup sessions
tar -czf sessions-backup-$(date +%Y%m%d).tar.gz data/sessions/

# Restore sessions
tar -xzf sessions-backup-20260321.tar.gz
```

### Disaster Recovery

1. **Service failure**: Restart service (sessions persist)
2. **Server failure**: Deploy to new server, restore sessions
3. **Bot credentials lost**: Regenerate and update .env
4. **Data corruption**: Restore from backup

## Success Criteria

### Deployment is successful when:

- ✅ All 7 E2E tests pass
- ✅ Service starts without errors
- ✅ Bots respond to /help command
- ✅ Complete trial flow works end-to-end
- ✅ Multiple users can run concurrent trials
- ✅ Sessions persist across restarts
- ✅ Error recovery works gracefully

## Support

### Documentation

- `docs/bot-deployment-guide.md` - Detailed deployment guide
- `docs/multi-bot-architecture.md` - Architecture overview
- `docs/task-22.5-e2e-validation.md` - Test validation results
- `README.md` - Project overview

### Testing

- `tests/integration/test_e2e_luffa_flow.py` - E2E test suite
- `tests/integration/test_bot_connectivity.py` - Bot connectivity test
- `tests/integration/test_production.py` - Production mode test

### Scripts

- `run_luffa_bot.sh` - Start service (legacy single-bot)
- `src/multi_bot_service.py` - Multi-bot service (recommended)

## Conclusion

This checklist ensures a smooth production deployment of VERITAS with the Luffa Bot multi-bot architecture. Follow each step carefully and verify success criteria before proceeding.

**Status**: ✅ Ready for production deployment

**Last Updated**: 2026-03-21

**Validated By**: End-to-end test suite (7/7 tests passing)

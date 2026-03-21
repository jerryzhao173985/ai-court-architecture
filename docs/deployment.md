# 🎭 VERITAS Multi-Bot - DEPLOYMENT READY

## ✅ Status: READY TO DEPLOY

Your VERITAS courtroom experience is fully configured with 5 Luffa bots and ready for production deployment.

## What You Have

### 5 Configured Bots

| Role | Bot UID | Status |
|------|---------|--------|
| 📋 Clerk | ORQAZCejHdZELLD | ✅ Configured |
| 👔 Prosecution | MZIXVYXwSwRx6Vd | ✅ Configured |
| 🛡️ Defence | NGKIEJGGRlKKnAqC | ✅ Configured |
| 🔍 Fact Checker | GKUPDBfLv23WktAS | ✅ Configured |
| ⚖️ Judge | YNLJHNCCsRmLBcvU | ✅ Configured |

### System Components

- ✅ Multi-bot configuration system
- ✅ Multi-bot API client
- ✅ Multi-bot service orchestrator
- ✅ Session management (multi-user support)
- ✅ Command handlers (/start, /continue, /vote, etc.)
- ✅ Stage progression with bot coordination
- ✅ Fact checker LLM integration
- ✅ Dual reveal sequence
- ✅ Interactive buttons (Luffa API format)
- ✅ Error handling and fallbacks
- ✅ Configuration validation
- ✅ Comprehensive documentation

## Deployment Steps

### 1. Verify Configuration ✅

```bash
python test_multi_bot_config.py
```

**Expected**: `✅ READY TO RUN - Total Bots Configured: 5/5`

### 2. Add Bots to Luffa Group ⏳

**Action Required:**
1. Open Luffa app
2. Create new group: "VERITAS Courtroom"
3. Add bots by UID:
   - ORQAZCejHdZELLD (Clerk)
   - MZIXVYXwSwRx6Vd (Prosecution)
   - NGKIEJGGRlKKnAqC (Defence)
   - GKUPDBfLv23WktAS (Fact Checker)
   - YNLJHNCCsRmLBcvU (Judge)

### 3. Start Service ⏳

```bash
./run_multi_bot.sh
```

**Expected Output:**
```
Starting VERITAS Multi-Bot service...
Initialized Clerk bot
Initialized Prosecution bot
Initialized Defence bot
Initialized Fact Checker bot
Initialized Judge bot
Configured roles: clerk, prosecution, defence, fact_checker, judge
```

### 4. Test in Group ⏳

In the Luffa group, send:
```
/start
```

**Expected**: Clerk bot responds with greeting and hook scene.

## How Users Experience It

### Group Chat View

```
👥 VERITAS Courtroom (Group)

Members:
  📋 Clerk Bot
  👔 Prosecution Bot
  🛡️ Defence Bot
  🔍 Fact Checker Bot
  ⚖️ Judge Bot
  👤 You (Human Juror)

Chat:
  [You]: /start

  [Clerk Bot]: 📋 Welcome to the VERITAS Courtroom Experience!
               
               Case: The Crown v. Marcus Ashford
               
               You are Juror #8 in a British Crown Court murder trial.

  [Clerk Bot]: 🎭 THE TRIAL BEGINS
               
               The year is 1923. Blackthorn Hall, a sprawling Victorian
               estate in the Cotswolds, stands silent...
               
               [Continue Button]

  [You]: /continue

  [Clerk Bot]: 📢 PROSECUTION OPENING STATEMENT

  [Prosecution Bot]: 👔 PROSECUTION
                     
                     Ladies and gentlemen of the jury, this is a case
                     about greed and betrayal. Marcus Ashford, the
                     trusted estate manager, poisoned his employer...

  [You]: /continue

  [Defence Bot]: 🛡️ DEFENCE
                 
                 Members of the jury, the prosecution will ask you
                 to fill gaps with assumptions. Where is the proof?

  [You]: /continue

  [Prosecution Bot]: 👔 PROSECUTION
                     
                     I present the forged will, found in the defendant's
                     study, showing a £500,000 bequest...

  [Fact Checker Bot]: 🔍 FACT CHECKER
                      
                      Correction: The will was found in the study desk,
                      not in the defendant's possession.

  [Defence Bot]: 🛡️ DEFENCE
                 
                 Note the security log: my client left at 8:20 PM,
                 giving him only 32 minutes...

  ... (trial continues)

  [You]: I think the timeline is too tight for him to have done it

  [Clerk Bot]: 👤 AI Juror: I agree, 32 minutes seems impossible...

  [Clerk Bot]: 👤 AI Juror: But what about the motive? The forged will...

  [You]: /vote not_guilty

  [Clerk Bot]: 🗳️ Collecting votes from all jurors...

  [Clerk Bot]: ⚖️ THE VERDICT
               
               The jury finds the defendant: NOT GUILTY
               
               Vote: 5 not guilty, 3 guilty

  [Judge Bot]: 🔍 THE TRUTH
               
               Actual verdict: GUILTY
               
               The defendant did poison Lord Ashford...

  [Clerk Bot]: 📊 REASONING ASSESSMENT
               
               Category: Sound Incorrect
               Evidence Score: 0.85/1.0
               Coherence Score: 0.90/1.0
               
               You used strong reasoning and cited relevant evidence,
               but reached the wrong conclusion...

  [Clerk Bot]: 🎭 AI JUROR IDENTITIES
               
               • juror_1: Evidence Purist - Voted Not Guilty
               • juror_2: Sympathetic Doubter - Voted Not Guilty
               • juror_3: Moral Absolutist - Voted Guilty
               ...

  [Clerk Bot]: ✅ Trial complete! Thank you for participating.
               
               [Start New Trial Button]
```

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                    Luffa Group Chat                          │
│                                                              │
│  👤 Human User (Juror)                                       │
│  📋 Clerk Bot        (ORQAZCejHdZELLD)                      │
│  👔 Prosecution Bot  (MZIXVYXwSwRx6Vd)                      │
│  🛡️ Defence Bot      (NGKIEJGGRlKKnAqC)                     │
│  🔍 Fact Checker Bot (GKUPDBfLv23WktAS)                     │
│  ⚖️ Judge Bot        (YNLJHNCCsRmLBcvU)                     │
└──────────────────────────────────────────────────────────────┘
                            ↕ Luffa Bot API
┌──────────────────────────────────────────────────────────────┐
│              MultiBotService (Python Backend)                │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ MultiBotClient                                         │ │
│  │  • Clerk Client (polls /receive)                       │ │
│  │  • Prosecution Client (sends /sendGroup)               │ │
│  │  • Defence Client (sends /sendGroup)                   │ │
│  │  • Fact Checker Client (sends /sendGroup)              │ │
│  │  • Judge Client (sends /sendGroup)                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↕                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ ExperienceOrchestrator                                 │ │
│  │  • State Machine (14 states)                           │ │
│  │  • Trial Orchestrator (5 agents)                       │ │
│  │  • Jury Orchestrator (8 jurors)                        │ │
│  │  • Reasoning Evaluator                                 │ │
│  │  • Dual Reveal Assembler                               │ │
│  └────────────────────────────────────────────────────────┘ │
│                            ↕                                 │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ LLM Service (OpenAI GPT-4o)                            │ │
│  │  • Agent response generation                           │ │
│  │  • Fact checking analysis                              │ │
│  │  • Juror deliberation                                  │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

## Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Begin new trial | `/start` |
| `/continue` | Advance to next stage | `/continue` |
| `/vote <verdict>` | Cast your vote | `/vote guilty` or `/vote not_guilty` |
| `/evidence` | View evidence board | `/evidence` |
| `/status` | Check trial progress | `/status` |
| `/help` | Show help message | `/help` |

## What Makes This Special

### Traditional Chatbot
- One bot posts everything
- Role labels in text
- Less engaging

### VERITAS Multi-Bot
- Five distinct bots
- Each has personality
- Realistic courtroom
- Immersive experience

### Example Comparison

**Single-Bot:**
```
[Bot]: 👔 PROSECUTION: I present the evidence...
[Bot]: 🛡️ DEFENCE: I object to this...
```

**Multi-Bot:**
```
[Prosecution Bot]: I present the evidence...
[Defence Bot]: I object to this...
```

The difference is subtle but powerful. Users feel like they're in a real courtroom with multiple people, not talking to a single bot.

## Technical Highlights

### Correct Luffa API Usage

✅ Polling `/receive` every 1 second
✅ Sending via `/sendGroup` with correct format
✅ Button format: `{"name": "...", "selector": "...", "isHidden": "0"}`
✅ Message deduplication by msgId
✅ Type "1" for plain text, "2" for buttons
✅ dismissType: "select" or "dismiss"

### Session Management

✅ Maps Luffa UID to session ID
✅ Supports multiple users in same group
✅ Independent trial progress per user
✅ 24-hour session recovery
✅ Auto-cleanup after completion

### Error Handling

✅ Bot unavailable → Fallback to Clerk
✅ API failure → Retry with backoff
✅ LLM failure → Use fallback responses
✅ Experience continues despite errors

## Cost Estimate

Per trial (15 minutes):
- 5 trial agents (GPT-4o): ~$0.03
- 3 active jurors (GPT-4o): ~$0.02
- 4 lightweight jurors (GPT-4o-mini): ~$0.005
- Fact checking (GPT-4o): ~$0.01

**Total: ~$0.06-0.10 per trial**

For 100 trials/day: ~$6-10/day

## Monitoring

### Health Check

```bash
# Service running?
ps aux | grep multi_bot_service

# Configuration valid?
python test_multi_bot_config.py

# Logs
tail -f logs/multi-bot.log
```

### Metrics

Track:
- Active sessions count
- Messages sent per bot
- LLM API latency
- Error rates
- Completion rates

## Support & Troubleshooting

### Common Issues

**"No Luffa client configured"**
- Check bot credentials in `.env`
- Run `python test_multi_bot_config.py`

**"Bot not responding"**
- Verify bot is in group
- Check service is running
- Review logs for errors

**"API errors"**
- Verify LUFFA_API_ENDPOINT=https://api.luffa.im
- Check bot secrets are correct
- Ensure bots have group permissions

### Getting Help

1. Check `QUICKSTART.md` for setup
2. Review `docs/multi-bot-architecture.md` for technical details
3. See `docs/bot-deployment-guide.md` for deployment
4. Check logs: `tail -f logs/multi-bot.log`

## Next Actions

### Immediate (Required)

1. ⏳ **Add bots to Luffa group**
   - Create group in Luffa app
   - Add all 5 bots by UID
   - Invite human participants

2. ⏳ **Start service**
   ```bash
   ./run_multi_bot.sh
   ```

3. ⏳ **Test in group**
   ```
   /start
   ```

### Optional (Enhanced Experience)

4. ⏳ **Add 7 more bots for AI jurors**
   - Create 7 additional bots at robot.luffa.im
   - Configure in `.env` as JUROR_1 through JUROR_7
   - Restart service
   - AI jurors become distinct participants

5. ⏳ **Monitor and optimize**
   - Track usage metrics
   - Optimize LLM prompts
   - Add more cases
   - Tune response timing

## Success Criteria

You'll know it's working when:

✅ All 5 bots appear in group
✅ `/start` triggers greeting from Clerk
✅ `/continue` advances stages with different bots speaking
✅ Prosecution and Defence bots present arguments
✅ Fact Checker bot intervenes on contradictions
✅ Judge bot provides summing up
✅ `/vote` triggers dual reveal sequence
✅ Multiple users can run trials simultaneously

## The Experience

Users will see a realistic courtroom unfold in their group chat:

- **Immersive**: 5 distinct AI participants
- **Interactive**: Commands and buttons
- **Educational**: Learn about Crown Court procedure
- **Engaging**: Deliberate with AI jurors
- **Insightful**: Get reasoning assessment

## Documentation

- `QUICKSTART.md` - Quick start with your credentials
- `docs/multi-bot-setup.md` - Detailed setup guide
- `docs/multi-bot-architecture.md` - Technical architecture
- `docs/bot-deployment-guide.md` - Production deployment
- `docs/MULTI_BOT_SUMMARY.md` - Implementation summary
- `README.md` - Project overview

## Final Checklist

- [x] 5 bots configured in `.env`
- [x] Configuration tested and validated
- [x] Multi-bot client created
- [x] Multi-bot service created
- [x] Luffa API integration correct
- [x] Session management implemented
- [x] Command handlers complete
- [x] Fact checker integrated
- [x] Documentation comprehensive
- [x] Startup scripts created
- [ ] Bots added to Luffa group
- [ ] Service started
- [ ] Tested in group chat

## You're Ready!

Your VERITAS multi-bot system is **fully implemented and ready to deploy**. 

**Next step**: Add all 5 bots to a Luffa group and run `./run_multi_bot.sh`

---

**Questions?** Check the documentation or review the code in `src/multi_bot_service.py`

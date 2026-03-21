# VERITAS Multi-Bot Quick Start

## Your Bot Credentials

You have 5 Luffa bots configured:

```
Bot 1 (Clerk):       UID: ORQAZCejHdZELLD, Secret: ta86cbb0bd1f35425bb03b66cdcd49d81e
Bot 2 (Prosecution): UID: MZIXVYXwSwRx6Vd, Secret: os8dc8ecf0b69b4a37956ad37e66553f30
Bot 3 (Defence):     UID: NGKIEJGGRlKKnAqC, Secret: P5263ab3153044a66ae567773cbea6ca9
Bot 4 (Fact Checker):UID: GKUPDBfLv23WktAS, Secret: y7b0636260a8740d980f0582ea94cc438
Bot 5 (Judge):       UID: YNLJHNCCsRmLBcvU, Secret: ye9e38b40137248cc841cc97aced744ce
```

## Setup (3 Steps)

### 1. Verify Configuration

Your `.env` file is already configured with all 5 bots. Test it:

```bash
python test_multi_bot_config.py
```

You should see:
```
✅ READY TO RUN
Total Bots Configured: 5/5 required
```

### 2. Add Bots to Luffa Group

1. Open Luffa app
2. Create a new group chat (or use existing)
3. Add all 5 bots to the group:
   - Search for bot by UID
   - Add: ORQAZCejHdZELLD (Clerk)
   - Add: MZIXVYXwSwRx6Vd (Prosecution)
   - Add: NGKIEJGGRlKKnAqC (Defence)
   - Add: GKUPDBfLv23WktAS (Fact Checker)
   - Add: YNLJHNCCsRmLBcvU (Judge)

### 3. Start the Service

```bash
./run_multi_bot.sh
```

Or directly:
```bash
python src/multi_bot_service.py
```

You should see:
```
Starting VERITAS Multi-Bot service...
Initialized Clerk bot
Initialized Prosecution bot
Initialized Defence bot
Initialized Fact Checker bot
Initialized Judge bot
Configured roles: clerk, prosecution, defence, fact_checker, judge
```

## Usage

### In the Luffa Group Chat

**Start a trial:**
```
/start                         # Random case
/start digital-deception-002   # Specific case
/cases                         # List available cases
```

The Clerk bot will greet you and present the hook scene.

**Continue through stages:**
```
/continue
```

Watch as different bots speak:
- 📋 Clerk announces stages
- 👔 Prosecution presents their case
- 🛡️ Defence creates reasonable doubt
- 🔍 Fact Checker intervenes on contradictions
- ⚖️ Judge provides legal instructions

**View evidence:**
```
/evidence
```

**Cast your vote:**
```
/vote guilty
```
or
```
/vote not_guilty
```

**Check progress:**
```
/status
```

**Get help:**
```
/help
```

## What Happens

### Trial Flow

1. **Hook Scene** (90s) - Atmospheric opening
2. **Charge Reading** (30s) - Clerk reads formal charge
3. **Prosecution Opening** (60s) - Prosecution bot presents case
4. **Defence Opening** (60s) - Defence bot creates doubt
5. **Evidence Presentation** (120s) - Both sides present evidence
   - Fact Checker bot may intervene
6. **Cross-Examination** (90s) - Both sides challenge evidence
   - Fact Checker bot may intervene
7. **Prosecution Closing** (60s) - Final prosecution argument
8. **Defence Closing** (60s) - Final defence argument
9. **Judge Summing Up** (105s) - Judge bot provides legal instructions
10. **Jury Deliberation** (300s) - You deliberate with AI jurors
11. **Anonymous Vote** (30s) - Cast your verdict
12. **Dual Reveal** (90s) - See verdict, truth, reasoning assessment

### Example Interaction

```
[You]: /start

[Clerk Bot]: 📋 Welcome to the VERITAS Courtroom Experience...

[Clerk Bot]: 🎭 THE TRIAL BEGINS

The year is 1923. Blackthorn Hall, a sprawling Victorian estate...

[You]: /continue

[Clerk Bot]: 📢 PROSECUTION OPENING STATEMENT

[Prosecution Bot]: 👔 PROSECUTION

Ladies and gentlemen of the jury, this is a case about greed and betrayal...

[You]: /continue

[Clerk Bot]: 📢 DEFENCE OPENING STATEMENT

[Defence Bot]: 🛡️ DEFENCE

Members of the jury, the prosecution will ask you to fill gaps with assumptions...

[You]: /continue

[Clerk Bot]: 📢 EVIDENCE PRESENTATION

[Prosecution Bot]: 👔 PROSECUTION

I present the forged will, found in the defendant's study...

[Fact Checker Bot]: 🔍 FACT CHECKER

Correction: The will was found in the study desk, not in the defendant's possession.

[Defence Bot]: 🛡️ DEFENCE

Note the security log shows my client left the estate at 8:20 PM...

[You]: /continue

... (trial continues through all stages)

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
You used strong reasoning but reached the wrong conclusion...
```

## Troubleshooting

### Bots Not Responding

1. Check all 5 bots are in the group
2. Verify service is running: `ps aux | grep multi_bot_service`
3. Check logs for errors
4. Ensure LUFFA_BOT_ENABLED=true in .env

### Configuration Errors

```bash
# Test configuration
python test_multi_bot_config.py

# If errors, check .env file has all 5 bot credentials
```

### API Errors

- Verify bot secrets are correct
- Check LUFFA_API_ENDPOINT=https://api.luffa.im
- Ensure bots have permission to post in group

## Architecture Benefits

### Multi-Bot vs Single-Bot

**Multi-Bot (Current):**
- ✅ Each agent is distinct participant
- ✅ Realistic courtroom atmosphere
- ✅ Clear attribution (bot names)
- ✅ Immersive experience
- ✅ Scalable (add more bots easily)

**Single-Bot (Legacy):**
- ⚠️ All messages from one bot
- ⚠️ Requires role labels
- ⚠️ Less immersive
- ✅ Simpler setup

## Next Steps

1. ✅ Configuration complete (.env has all 5 bots)
2. ⏳ Add bots to Luffa group
3. ⏳ Start service: `./run_multi_bot.sh`
4. ⏳ Test in group: `/start`
5. ⏳ Experience full trial flow

## Advanced: Adding Juror Bots

If you create 7 more bots (12 total), you can have separate bots for each AI juror:

```bash
# In .env, add:
LUFFA_BOT_JUROR_1_UID=your_bot_6_uid
LUFFA_BOT_JUROR_1_SECRET=your_bot_6_secret
# ... up to JUROR_7
```

This makes deliberation even more realistic with 7 distinct AI juror participants.

## Support

For issues:
1. Check logs: `tail -f logs/veritas.log`
2. Test config: `python test_multi_bot_config.py`
3. Review docs: `docs/multi-bot-architecture.md`

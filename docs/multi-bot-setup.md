# VERITAS Multi-Bot Setup Guide

## Overview

VERITAS uses a **multi-bot architecture** where each courtroom participant is a separate Luffa bot. This creates a realistic group chat experience where different bots play different roles.

## Bot Architecture

### Required Bots (5 minimum)

1. **Clerk Bot** - Orchestrator and procedural guidance
   - Manages trial flow
   - Sends stage announcements
   - Handles commands (/start, /continue, /help, etc.)
   - Coordinates other bots

2. **Prosecution Bot** - Crown Prosecution barrister
   - Presents prosecution case
   - Argues for guilty verdict
   - Cross-examines defence witnesses

3. **Defence Bot** - Defence barrister
   - Defends the accused
   - Creates reasonable doubt
   - Cross-examines prosecution witnesses

4. **Fact Checker Bot** - Neutral fact checker
   - Monitors statements for contradictions
   - Intervenes when facts are misstated
   - Limited to 3 interventions per trial

5. **Judge Bot** - Presiding judge
   - Provides legal instructions
   - Sums up the case
   - Reveals ground truth in dual reveal

### Optional Bots (7 additional for full experience)

6-12. **Juror Bots** - AI jurors with distinct personas
   - Juror 1: Evidence Purist
   - Juror 2: Sympathetic Doubter
   - Juror 3: Moral Absolutist
   - Jurors 4-7: Lightweight AI jurors

## Your Bot Credentials

From your Luffa robot dashboard:

```
Bot 1: UID: ORQAZCejHdZELLD, Secret: ta86cbb0bd1f35425bb03b66cdcd49d81e
Bot 2: UID: MZIXVYXwSwRx6Vd, Secret: os8dc8ecf0b69b4a37956ad37e66553f30
Bot 3: UID: NGKIEJGGRlKKnAqC, Secret: P5263ab3153044a66ae567773cbea6ca9
Bot 4: UID: GKUPDBfLv23WktAS, Secret: y7b0636260a8740d980f0582ea94cc438
Bot 5: UID: YNLJHNCCsRmLBcvU, Secret: ye9e38b40137248cc841cc97aced744ce
```

## Recommended Mapping

```
Clerk       → Bot 1 (ORQAZCejHdZELLD)
Prosecution → Bot 2 (MZIXVYXwSwRx6Vd)
Defence     → Bot 3 (NGKIEJGGRlKKnAqC)
Fact Checker→ Bot 4 (GKUPDBfLv23WktAS)
Judge       → Bot 5 (YNLJHNCCsRmLBcvU)
```

## Setup Instructions

### Step 1: Configure Environment Variables

Run the setup script:

```bash
python setup_bots.py
```

Or manually update your `.env` file:

```bash
# Luffa Bot Configuration - Multi-Bot Architecture

# Bot 1: Clerk
LUFFA_BOT_CLERK_UID=ORQAZCejHdZELLD
LUFFA_BOT_CLERK_SECRET=ta86cbb0bd1f35425bb03b66cdcd49d81e

# Bot 2: Prosecution
LUFFA_BOT_PROSECUTION_UID=MZIXVYXwSwRx6Vd
LUFFA_BOT_PROSECUTION_SECRET=os8dc8ecf0b69b4a37956ad37e66553f30

# Bot 3: Defence
LUFFA_BOT_DEFENCE_UID=NGKIEJGGRlKKnAqC
LUFFA_BOT_DEFENCE_SECRET=P5263ab3153044a66ae567773cbea6ca9

# Bot 4: Fact Checker
LUFFA_BOT_FACT_CHECKER_UID=GKUPDBfLv23WktAS
LUFFA_BOT_FACT_CHECKER_SECRET=y7b0636260a8740d980f0582ea94cc438

# Bot 5: Judge
LUFFA_BOT_JUDGE_UID=YNLJHNCCsRmLBcvU
LUFFA_BOT_JUDGE_SECRET=ye9e38b40137248cc841cc97aced744ce

# API Configuration
LUFFA_API_ENDPOINT=https://api.luffa.im
LUFFA_BOT_ENABLED=true
```

### Step 2: Add All Bots to Group Chat

1. Create a new Luffa group chat
2. Add all 5 bots to the group:
   - Clerk bot (ORQAZCejHdZELLD)
   - Prosecution bot (MZIXVYXwSwRx6Vd)
   - Defence bot (NGKIEJGGRlKKnAqC)
   - Fact Checker bot (GKUPDBfLv23WktAS)
   - Judge bot (YNLJHNCCsRmLBcvU)

3. Invite human participants (jurors)

### Step 3: Start the Service

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

### Step 4: Start a Trial

In the group chat, send:
```
/start
```

The Clerk bot will greet you and begin the trial.

## How It Works

### Trial Flow in Group Chat

1. **User sends `/start`**
   - Clerk bot welcomes everyone
   - Presents hook scene (atmospheric opening)

2. **User sends `/continue`**
   - Clerk announces next stage
   - Appropriate bot speaks (Prosecution, Defence, Judge)
   - Each bot posts as a separate participant

3. **During Evidence Presentation**
   - Prosecution bot presents evidence
   - Fact Checker bot may intervene if contradiction detected
   - Defence bot presents counter-evidence
   - Fact Checker bot may intervene again

4. **During Deliberation**
   - User shares thoughts in chat
   - AI jurors respond (via Clerk bot or separate juror bots)
   - Evidence board available via `/evidence`

5. **Voting**
   - User sends `/vote guilty` or `/vote not_guilty`
   - Clerk collects votes from AI jurors

6. **Dual Reveal**
   - Clerk announces verdict
   - Judge reveals ground truth
   - Clerk provides reasoning assessment
   - Clerk reveals AI juror identities

### Bot Interaction Example

```
[Clerk Bot]: 📢 PROSECUTION OPENING STATEMENT

[Prosecution Bot]: 👔 PROSECUTION
Ladies and gentlemen of the jury, this is a case about greed...

[User]: /continue

[Clerk Bot]: 📢 DEFENCE OPENING STATEMENT

[Defence Bot]: 🛡️ DEFENCE
Members of the jury, the prosecution will ask you to fill gaps with assumptions...

[User]: /continue

[Clerk Bot]: 📢 EVIDENCE PRESENTATION

[Prosecution Bot]: 👔 PROSECUTION
I present the forged will, found in the defendant's possession...

[Fact Checker Bot]: 🔍 FACT CHECKER
Correction: The will was found in the study, not in the defendant's possession.

[Defence Bot]: 🛡️ DEFENCE
Note the security log shows my client left at 8:20 PM...
```

## Advanced Configuration

### Adding Juror Bots

If you have more than 5 bots, you can configure separate bots for AI jurors:

```bash
# Optional: AI Juror Bots
LUFFA_BOT_JUROR_1_UID=your_bot_6_uid
LUFFA_BOT_JUROR_1_SECRET=your_bot_6_secret

LUFFA_BOT_JUROR_2_UID=your_bot_7_uid
LUFFA_BOT_JUROR_2_SECRET=your_bot_7_secret

LUFFA_BOT_JUROR_3_UID=your_bot_8_uid
LUFFA_BOT_JUROR_3_SECRET=your_bot_8_secret
```

With juror bots configured, AI jurors will post as separate participants during deliberation.

### Fallback Mode

If you only configure the Clerk bot, the system will use **single-bot mode** where the Clerk bot posts all messages with role labels. This is less immersive but still functional.

## Troubleshooting

### Bot Not Responding

1. Check bot is added to group chat
2. Verify UID and Secret in .env
3. Check logs for connection errors
4. Ensure LUFFA_BOT_ENABLED=true

### Messages Not Appearing

1. Verify LUFFA_API_ENDPOINT is correct
2. Check bot has permission to post in group
3. Review logs for API errors

### Multiple Users in Same Group

The system supports multiple concurrent users in the same group. Each user gets their own trial session tracked by their Luffa UID.

## Testing

Test the multi-bot setup:

```bash
# Test configuration loading
python -c "from config import load_config; c = load_config(); print(f'Clerk: {c.luffa.clerk_bot}')"

# Test multi-bot client
python -c "from multi_bot_client import MultiBotClient; from config import load_config; m = MultiBotClient(load_config().luffa); print(m.get_configured_roles())"
```

## Next Steps

1. ✅ Configure .env with your 5 bot credentials
2. ✅ Add all 5 bots to a Luffa group chat
3. ✅ Start the service: `python src/multi_bot_service.py`
4. ✅ In group chat, send: `/start`
5. ✅ Experience the trial with multiple bot participants!

## Benefits of Multi-Bot Architecture

- **Realistic Experience**: Each agent is a distinct participant in the group
- **Clear Attribution**: Users see who is speaking (Prosecution vs Defence)
- **Immersive**: Feels like a real courtroom with multiple people
- **Scalable**: Easy to add more bots for jurors or witnesses
- **Flexible**: Can fall back to single-bot mode if needed

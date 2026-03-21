# VERITAS Luffa Bot Setup Guide

Transform VERITAS into an immersive group chat courtroom experience where AI agents play different roles and users can influence the story outcome.

---

## How It Works

### Group Chat Courtroom
- Create a Luffa group chat
- Invite the VERITAS bot
- AI agents post as different characters:
  - 🎭 **Clerk**: Formal announcements
  - ⚖️ **Prosecution**: Argues for guilt
  - 🛡️ **Defence**: Creates reasonable doubt
  - 👨‍⚖️ **Judge**: Provides legal guidance
  - 👥 **AI Jurors**: 7 AI jurors with distinct personalities

### Interactive Storytelling
- Users participate as the 8th juror
- Share thoughts during deliberation
- AI jurors respond to your statements
- Your input influences the discussion
- Cast your vote to determine the verdict
- See how your reasoning compares to the truth

---

## Setup Steps

### Step 1: Get Your Bot Secret

1. Visit **https://robot.luffa.im**
2. Create a new bot or access existing bot
3. Copy your bot secret (looks like: `abc123xyz...`)

### Step 2: Configure the Bot

Edit `.env` file:

```bash
# Luffa Bot Configuration
LUFFA_API_URL=https://apibot.luffa.im/robot
LUFFA_BOT_SECRET=<paste_your_secret_here>
LUFFA_BOT_ENABLED=true
```

### Step 3: Start the Bot Service

```bash
./run_luffa_bot.sh
```

You should see:
```
✓ Configuration verified
✓ Starting bot service...
✓ Connected to Luffa Bot API
✓ Polling for messages every 1 second...
```

### Step 4: Test in Luffa

1. Create a group chat in Luffa
2. Add your bot to the group
3. Type: `/start`
4. The trial begins!

---

## Bot Commands

### Trial Control
- `/start` - Begin a new trial (group chat only)
- `/continue` - Advance to next stage
- `/status` - Check current progress

### During Trial
- `/evidence` - View evidence board
- `/help` - Show available commands

### Voting
- `/vote guilty` - Vote guilty
- `/vote not_guilty` - Vote not guilty

### Deliberation
- Just type your thoughts in the chat (no command needed)
- AI jurors will respond to your statements
- Reference evidence by name

---

## Experience Flow

### 1. Trial Begins (8 Stages)
```
/start → Hook scene
/continue → Charge reading (Clerk)
/continue → Prosecution opening
/continue → Defence opening
/continue → Evidence presentation
/continue → Cross-examination
/continue → Prosecution closing
/continue → Defence closing
/continue → Judge's summing up
```

Each stage, AI agents post as their characters in the group chat.

### 2. Jury Deliberation
```
/continue → Deliberation begins
<type your thoughts> → AI jurors respond
<continue discussion> → AI jurors engage
/vote guilty or /vote not_guilty → Cast verdict
```

### 3. Dual Reveal
```
Automatic sequence:
1. Verdict reveal (jury vote breakdown)
2. Ground truth (what actually happened)
3. Your reasoning assessment (how well you analyzed)
4. AI juror identities (who they were, how they voted)
```

### 4. Complete
```
Trial ends, session cleaned up
/start → Begin new trial
```

---

## Example Group Chat Session

```
User: /start

Bot: 🎭 Welcome to VERITAS - an interactive courtroom experience.
     You are about to witness the trial of The Crown v. Marcus Ashford...

Bot: 🎭 THE TRIAL BEGINS
     [Hook scene content]
     Type /continue to proceed to the trial.

User: /continue

Bot: 📢 The Clerk will now read the formal charges.

Bot: 🎭 [CLERK]
     Marcus Ashford, you are charged with murder contrary to common law...

User: /continue

Bot: 📢 The Crown Prosecution will present their opening statement.

Bot: 🎭 [PROSECUTION]
     Members of the jury, the Crown will prove beyond reasonable doubt...

[... trial continues through 8 stages ...]

User: /continue

Bot: ⚖️ JURY DELIBERATION
     Members of the jury, you may now begin your deliberations...

User: I think the evidence is circumstantial. We need more proof.

Bot: 👤 AI Juror: I agree. The prosecution hasn't shown direct evidence...

Bot: 👤 AI Juror: But consider the timeline. The defendant had opportunity...

Bot: 👤 AI Juror: We must remember - beyond reasonable doubt is the standard...

User: /vote not_guilty

Bot: 🗳️ Collecting votes from all jurors...

Bot: ⚖️ THE VERDICT
     The jury finds the defendant: NOT GUILTY
     Vote: 3 guilty, 5 not guilty

Bot: 🔍 THE TRUTH
     Actual verdict: GUILTY
     [Explanation of what really happened]

Bot: 📊 REASONING ASSESSMENT
     Category: Evidence-Based Reasoning
     Evidence Score: 0.85/1.0
     [Detailed feedback]

Bot: 🎭 AI JUROR IDENTITIES
     • juror_1: Evidence Purist - Voted Not Guilty
     • juror_2: Sympathetic Doubter - Voted Not Guilty
     [... more jurors ...]

Bot: ✅ Trial complete! Thank you for participating.
     Type /start to begin a new trial.
```

---

## Architecture

### Message Flow
```
Luffa Group Chat
       ↓
   Bot receives message (polling every 1s)
       ↓
   Parse command or deliberation
       ↓
   Orchestrator processes
       ↓
   AI agents generate responses (GPT-4o)
       ↓
   Bot posts responses to group
       ↓
   Users see AI characters speaking
```

### Session Management
- One session per group chat
- Sessions persist until trial completes
- Multiple groups can run trials simultaneously
- Each group has independent state

---

## AI Agent Behavior

### Trial Agents (Post as Characters)
- **Clerk**: Formal, procedural
- **Prosecution**: Persuasive, argues guilt
- **Defence**: Challenges evidence, creates doubt
- **Judge**: Authoritative, impartial

### Jury Agents (Respond to Users)
- **Evidence Purist**: "Show me the concrete proof"
- **Sympathetic Doubter**: "Can we really be certain?"
- **Moral Absolutist**: "Justice must be served"
- **Lightweight Jurors**: Brief, occasional comments

All responses generated in real-time by GPT-4o/GPT-4o-mini.

---

## User Influence

Users can influence the story by:

1. **Deliberation Statements**: AI jurors respond and adapt
2. **Evidence References**: Steer discussion to specific evidence
3. **Voting**: Determines the verdict outcome
4. **Reasoning Quality**: Affects assessment and feedback

The experience is dynamic - AI jurors react to what you say!

---

## Technical Details

### Polling
- Frequency: Every 1 second
- Deduplication: By msgId
- Message parsing: JSON strings

### Message Types
- Type 0: Direct message (DM)
- Type 1: Group message
- Type 2: Group message with buttons

### Response Timing
- Agent responses: 1-2s each
- Jury responses: 3-5s for all jurors
- Paced delivery: 1-2s between messages

---

## Troubleshooting

### Bot Not Responding
1. Check bot service is running: `ps aux | grep luffa_bot_service`
2. Check logs for errors
3. Verify bot secret is correct
4. Ensure bot is added to the group

### Messages Not Appearing
1. Check LUFFA_BOT_ENABLED=true in .env
2. Verify bot has group permissions
3. Check network connectivity

### API Errors
1. Verify bot secret from https://robot.luffa.im
2. Check API endpoint: https://apibot.luffa.im/robot
3. Review logs for specific error messages

---

## Cost Considerations

### OpenAI API Usage
- Trial agents: GPT-4o (~$0.03 per trial)
- Active jurors: GPT-4o (~$0.02 per trial)
- Lightweight jurors: GPT-4o-mini (~$0.005 per trial)

**Total per trial**: ~$0.05-0.10

### Luffa Bot API
- Message polling: Free
- Message sending: Free
- No additional costs

---

## Advanced Configuration

### Adjust AI Behavior

Edit `src/trial_orchestrator.py` and `src/jury_orchestrator.py` to customize:
- Agent personalities
- Response lengths
- Deliberation duration
- Voting logic

### Add More Cases

Create new case JSON in `fixtures/`:
```json
{
  "caseId": "your-case-id",
  "title": "The Crown v. [Defendant]",
  "narrative": { ... },
  "evidence": [ ... ],
  "groundTruth": { ... }
}
```

Update bot service to select cases dynamically.

### Multi-Group Support

The bot automatically handles multiple groups:
- Each group gets independent session
- Sessions don't interfere
- Concurrent trials supported

---

## Next Steps

1. **Get bot secret** from https://robot.luffa.im
2. **Configure .env** with your secret
3. **Run bot service**: `./run_luffa_bot.sh`
4. **Test in group chat**: Add bot and type `/start`
5. **Experience the trial**: Participate as a juror!

---

## Support

**Questions?** Check the logs:
```bash
tail -f veritas.log  # If logging to file
```

**Need help?** Review:
- `QUICK_REFERENCE.md` - System overview
- `SYSTEM_STATUS.md` - Component status
- `INTEGRATION_COMPLETE.md` - Integration details

---

**Ready to bring your courtroom to life in Luffa!** 🎭⚖️

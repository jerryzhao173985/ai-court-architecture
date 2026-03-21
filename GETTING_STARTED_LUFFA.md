# Getting Started with VERITAS on Luffa

## 🎯 Goal
Run VERITAS as an immersive group chat courtroom experience where AI agents play different roles and users can influence the story outcome.

---

## 📋 Prerequisites

✅ System is fully implemented and tested  
✅ OpenAI GPT-4o integration working  
✅ Luffa Bot client ready  
⏸️ Need: Luffa Bot secret  

---

## 🚀 Quick Start (3 Steps)

### Step 1: Get Your Bot Secret

1. Go to **https://robot.luffa.im**
2. Create or access your bot account
3. Copy the bot secret

### Step 2: Configure

Edit `.env`:
```bash
LUFFA_BOT_SECRET=<paste_your_secret>
LUFFA_BOT_ENABLED=true
```

### Step 3: Start the Bot

```bash
./run_luffa_bot.sh
```

That's it! Your bot is now live.

---

## 🎮 How to Use

### In Luffa Group Chat

1. **Create a group** or use existing group
2. **Add your bot** to the group
3. **Type**: `/start`
4. **Watch** AI agents perform the trial
5. **Participate** as a juror
6. **Influence** the story with your input

---

## 🎭 What Happens

### The Courtroom Comes to Life

**AI Characters Post in Chat:**
- 🎭 Clerk reads charges
- ⚖️ Prosecution argues guilt
- 🛡️ Defence creates doubt
- 👨‍⚖️ Judge provides instructions
- 👥 7 AI Jurors discuss with you

**You Participate:**
- Watch the 8-stage trial unfold
- Deliberate with AI jurors
- Share your thoughts
- Cast your vote
- See the truth revealed

---

## 💬 Example Session

```
[Group Chat: Murder Mystery Court]

You: /start

Bot: 🎭 Welcome to VERITAS - an interactive courtroom experience.
     You are about to witness the trial of The Crown v. Marcus Ashford.
     A British country estate. A murdered lord. A trusted employee accused.
     
     Type /continue to begin.

You: /continue

Bot: 🎭 [CLERK]
     Marcus Ashford, you are charged with murder...

You: /continue

Bot: 🎭 [PROSECUTION]
     Members of the jury, the evidence will show...

[... 8 stages of trial ...]

Bot: ⚖️ JURY DELIBERATION
     What are your initial thoughts?

You: The fingerprint evidence is strong but the motive is unclear.

Bot: 👤 AI Juror: I need more than fingerprints. Where's the direct evidence?

Bot: 👤 AI Juror: But he had access and opportunity. That's significant.

Bot: 👤 AI Juror: We must consider - beyond reasonable doubt!

You: /vote not_guilty

Bot: ⚖️ THE VERDICT: NOT GUILTY (3 guilty, 5 not guilty)

Bot: 🔍 THE TRUTH: GUILTY
     [Reveals what actually happened]

Bot: 📊 YOUR REASONING: Evidence-Based (0.75/1.0)
     [Analyzes your thinking]

Bot: 🎭 AI JUROR IDENTITIES
     [Reveals who the AI jurors were]

Bot: ✅ Trial complete!
```

---

## 🎯 Key Features

### Immersive Group Chat
- AI agents post as characters
- Real-time responses
- Paced delivery (feels natural)
- Multiple users can participate

### Dynamic Story
- AI jurors respond to YOUR statements
- Discussion adapts to your input
- Your vote determines verdict
- Multiple possible outcomes

### Educational
- Learn British legal system
- Practice critical thinking
- Understand reasonable doubt
- Recognize logical fallacies

---

## 🔧 Technical Details

### Bot Behavior
- **Polling**: Checks for messages every 1 second
- **Deduplication**: Prevents duplicate processing
- **Session Management**: One trial per group
- **Concurrent**: Multiple groups can run trials

### AI Models
- **Trial Agents**: GPT-4o (Clerk, Prosecution, Defence, Judge)
- **Active Jurors**: GPT-4o (3 jurors with personas)
- **Lightweight Jurors**: GPT-4o-mini (4 jurors)

### Response Times
- Agent posts: 1-2 seconds
- Jury responses: 3-5 seconds
- Paced delivery: 1-2 seconds between messages

---

## 📊 Commands Reference

| Command | Description | When to Use |
|---------|-------------|-------------|
| `/start` | Begin new trial | Start of experience |
| `/continue` | Next stage | After each stage |
| `/vote guilty` | Vote guilty | During voting |
| `/vote not_guilty` | Vote not guilty | During voting |
| `/evidence` | View evidence | Anytime during trial |
| `/status` | Check progress | Anytime |
| `/help` | Show commands | Anytime |

**During deliberation**: Just type your thoughts (no command needed)

---

## 💡 Tips

### For Best Experience
1. **Read carefully**: Evidence details matter
2. **Engage actively**: AI jurors respond to you
3. **Reference evidence**: Mention specific items
4. **Think critically**: Consider both sides
5. **Vote honestly**: Based on your analysis

### For Group Moderators
1. **One trial at a time**: Per group
2. **Pace the experience**: Use /continue when ready
3. **Encourage participation**: During deliberation
4. **Multiple users**: Can all participate

---

## 🔍 Troubleshooting

### Bot Not Responding
```bash
# Check bot service is running
ps aux | grep luffa_bot_service

# Restart if needed
./run_luffa_bot.sh
```

### Bot Not in Group
1. Add bot to group in Luffa
2. Verify bot has permissions
3. Type /help to test

### Commands Not Working
1. Ensure bot service is running
2. Check .env has LUFFA_BOT_ENABLED=true
3. Verify bot secret is correct

---

## 📈 What's Next

### After Setup
1. ✅ Bot is running
2. ✅ Add to group chat
3. ✅ Type `/start`
4. ✅ Experience the trial!

### Future Enhancements
- Multiple case files
- Custom cases
- Visual elements (SuperBox)
- Verdict sharing (Channel)
- Statistics tracking

---

## 🎬 Ready to Start?

### 1. Get Bot Secret
Visit: https://robot.luffa.im

### 2. Configure
```bash
# Edit .env
LUFFA_BOT_SECRET=<your_secret>
LUFFA_BOT_ENABLED=true
```

### 3. Launch
```bash
./run_luffa_bot.sh
```

### 4. Play
In Luffa group chat: `/start`

---

**Your courtroom awaits!** 🎭⚖️

The AI agents are ready to perform. The jury is assembled. The case is prepared. All you need is your bot secret to bring it to life.

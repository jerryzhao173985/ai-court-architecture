# VERITAS Quick Reference

## System Status: ✅ FULLY OPERATIONAL

---

## Quick Start

### Run Interactive Demo
```bash
./play.sh
```

### Run All Tests
```bash
./verify_system.sh
```

### Run Production Tests (OpenAI)
```bash
python test_production.py
```

---

## What's Working

✅ **All 41 unit tests passing**  
✅ **OpenAI GPT-4o integration working**  
✅ **Trial agents generating real responses**  
✅ **Jury system with 8 jurors (3 GPT-4o + 4 GPT-4o-mini + 1 human)**  
✅ **Complete 13-stage trial flow**  
✅ **Evidence board with timeline**  
✅ **Reasoning evaluation system**  
✅ **Dual reveal (verdict + truth + reasoning + jurors)**  
✅ **Session persistence**  
✅ **Error handling with fallbacks**  

---

## Configuration

### Current Setup (.env)
```
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o
OPENAI_API_KEY=<detected from environment>

LUFFA_BOT_ENABLED=false
LUFFA_BOT_SECRET=<not set>
```

### Model Usage
- **Active AI Jurors**: GPT-4o (3 jurors with distinct personas)
- **Lightweight AI Jurors**: GPT-4o-mini (4 jurors, brief responses)
- **Trial Agents**: GPT-4o (Clerk, Prosecution, Defence, Judge, Fact Checker)

---

## Test Results

### Latest Run (March 21, 2026)
```
Unit Tests:        41/41 ✓
Production Tests:   4/4  ✓
OpenAI API:        Working ✓
Jury System:       Working ✓
Trial Agents:      Working ✓
```

---

## Next Steps

### To Play the Experience
```bash
./play.sh
```
You'll go through:
1. Hook scene (dramatic opening)
2. 8 trial stages (charges → evidence → closing speeches → judge's instructions)
3. Jury deliberation (discuss with 7 AI jurors)
4. Anonymous voting
5. Dual reveal (verdict, truth, your reasoning assessment, AI juror identities)

### To Enable Luffa Bot
1. Visit https://robot.luffa.im
2. Get your bot secret
3. Edit `.env`:
   ```
   LUFFA_BOT_SECRET=<your_secret>
   LUFFA_BOT_ENABLED=true
   ```
4. Restart the system

---

## File Structure

```
.
├── src/
│   ├── orchestrator.py          # Main coordinator
│   ├── state_machine.py         # 13-stage flow
│   ├── trial_orchestrator.py    # 5 trial agents
│   ├── jury_orchestrator.py     # 8 jurors
│   ├── llm_service.py           # OpenAI/Anthropic API
│   ├── luffa_client.py          # Luffa Bot API
│   ├── reasoning_evaluator.py   # Reasoning analysis
│   ├── dual_reveal.py           # 4-part reveal
│   └── interactive_demo.py      # User experience
├── fixtures/
│   └── blackthorn-hall-001.json # Murder mystery case
├── tests/
│   └── unit/                    # 41 passing tests
├── .env                         # Configuration
└── play.sh                      # Quick start script
```

---

## Cost Estimates (OpenAI GPT-4o)

- Single experience: ~$0.05-0.10
- 100 users/day: ~$5-10/day
- 1000 users/month: ~$50-100/month

---

## Support

**Issue**: Tests fail  
**Fix**: `source venv/bin/activate && pip install -e .`

**Issue**: No OpenAI responses  
**Fix**: Verify `echo $OPENAI_API_KEY` shows your key

**Issue**: Import errors  
**Fix**: Run from project root, not from `src/` directory

---

**Last Verified**: March 21, 2026 02:51 UTC  
**Status**: Production Ready ✅

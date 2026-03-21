# VERITAS Quick Start

## 🚀 Get Started in 3 Steps

### 1. Install Dependencies
```bash
source venv/bin/activate  # Activate your virtual environment
pip install -e .
```

### 2. Run the Demo
```bash
./run_demo.sh
```

That's it! The demo runs in test mode with placeholder AI responses.

## 🤖 Enable Real AI (Optional)

### Option A: OpenAI (GPT-4)
```bash
echo "LLM_PROVIDER=openai" > .env
echo "LLM_API_KEY=sk-your-key-here" >> .env
echo "LLM_MODEL=gpt-4" >> .env
./run_demo.sh
```

### Option B: Anthropic (Claude)
```bash
echo "LLM_PROVIDER=anthropic" > .env
echo "LLM_API_KEY=sk-ant-your-key-here" >> .env
echo "LLM_MODEL=claude-3-sonnet-20240229" >> .env
./run_demo.sh
```

## 🌐 Start API Server
```bash
./run_server.sh
```
- Server: http://localhost:8000
- Docs: http://localhost:8000/docs

## 🧪 Run Tests
```bash
pytest tests/ -v
```

## 📖 Full Documentation
- `SETUP.md` - Detailed setup instructions
- `INTEGRATION_COMPLETE.md` - Integration details
- `README.md` - Project overview

## 💡 What You Get

**Test Mode (No API Keys):**
- ✅ Complete 15-minute courtroom experience
- ✅ All features working
- ✅ Placeholder AI responses
- ✅ Perfect for development

**Production Mode (With API Keys):**
- ✅ Real AI-generated trial arguments
- ✅ Dynamic jury deliberation
- ✅ Intelligent reasoning evaluation
- ✅ Costs ~$0.21 per experience (GPT-4)

## 🎭 The Experience

1. **Hook Scene** (75s) - Atmospheric opening
2. **Trial** (8 stages) - Prosecution, Defence, Evidence, Judge
3. **Deliberation** (4-6 min) - Discuss with 7 AI jurors
4. **Vote** - Anonymous voting
5. **Dual Reveal** - Verdict, truth, reasoning assessment, juror identities

Total: ~15 minutes

## 🔧 Troubleshooting

**Import errors?** Run from src/: `cd src && python main.py`

**Need API key?** Copy `.env.example` to `.env` and add your key

**Tests failing?** Make sure dependencies installed: `pip install -e .`

## 🎯 Ready to Deploy?

See `INTEGRATION_COMPLETE.md` for production deployment guide.

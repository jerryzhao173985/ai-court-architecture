# VERITAS Setup Guide

## Prerequisites

- Python 3.10 or higher
- pip or uv package manager
- OpenAI or Anthropic API key
- Luffa platform API key (optional for testing)

## Installation

1. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -e .
```

Or with uv (faster):
```bash
uv pip install -e .
```

## Configuration

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. Edit `.env` and add your API keys:

```bash
# Required: LLM API Key
LLM_PROVIDER=openai  # or anthropic
LLM_API_KEY=sk-...   # Your OpenAI or Anthropic API key

# Optional: Luffa Platform (can run without these)
LUFFA_API_KEY=your_luffa_key
LUFFA_BOT_ENABLED=true
LUFFA_SUPERBOX_ENABLED=true
LUFFA_CHANNEL_ENABLED=true
```

### LLM Provider Options

**OpenAI:**
```bash
LLM_PROVIDER=openai
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4  # or gpt-3.5-turbo for faster/cheaper
```

**Anthropic:**
```bash
LLM_PROVIDER=anthropic
LLM_API_KEY=sk-ant-...
LLM_MODEL=claude-3-sonnet-20240229  # or claude-3-opus-20240229
```

## Running the Demo

### Test Mode (No API Keys Required)

The system works in test mode with placeholder responses if no API keys are configured:

```bash
cd src
python main.py
```

### Production Mode (With LLM Integration)

1. Ensure `.env` file has your LLM API key
2. Load environment variables:
```bash
export $(cat .env | xargs)  # On Unix/Mac
```

3. Run the demo:
```bash
cd src
python main.py
```

## Running Tests

```bash
pytest tests/ -v
```

## Starting the API Server

```bash
cd src
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

API documentation: `http://localhost:8000/docs`

## API Endpoints

- `POST /api/sessions` - Start new experience
- `GET /api/sessions/{sessionId}` - Get session state
- `POST /api/sessions/{sessionId}/statements` - Submit deliberation statement
- `POST /api/sessions/{sessionId}/vote` - Submit vote
- `GET /api/cases/{caseId}` - Get case content
- `WS /ws/{sessionId}` - WebSocket for real-time updates

## Architecture

```
src/
├── models.py              # Pydantic data models
├── state_machine.py       # Experience state management
├── session.py             # Session persistence
├── case_manager.py        # Case content loading
├── evidence_board.py      # Evidence timeline
├── trial_orchestrator.py  # 5 trial agents
├── jury_orchestrator.py   # 7 AI + 1 human jurors
├── reasoning_evaluator.py # Reasoning assessment
├── dual_reveal.py         # Verdict reveal system
├── trial_stages.py        # Stage progression
├── luffa_integration.py   # Bot, SuperBox, Channel
├── luffa_client.py        # Luffa API client
├── llm_service.py         # LLM API integration
├── config.py              # Configuration management
├── error_handling.py      # Error handling
├── orchestrator.py        # Main coordinator
├── api.py                 # FastAPI endpoints
└── main.py                # Demo entry point

fixtures/
└── blackthorn-hall-001.json  # Flagship case

tests/
├── unit/
│   ├── test_state_machine.py
│   ├── test_session.py
│   └── test_integration.py
└── property/              # Property-based tests (optional)
```

## Troubleshooting

### Import Errors
If you see `ModuleNotFoundError: No module named 'src'`, make sure you're running from the `src/` directory:
```bash
cd src
python main.py
```

### API Key Errors
If you see `LLM_API_KEY environment variable is required`, either:
1. Set the environment variable: `export LLM_API_KEY=your_key`
2. Or run in test mode (system will use fallback responses)

### Luffa Platform Errors
Luffa platform integration is optional. If you don't have Luffa API access, the system will:
- Skip Bot messages (but still generate them locally)
- Skip SuperBox rendering (use text fallback)
- Skip Channel announcements (use local statistics)

## Next Steps

1. Replace placeholder AI responses with actual LLM calls ✓
2. Connect to Luffa platform APIs ✓
3. Add more case content
4. Implement property-based tests (optional)
5. Deploy to production

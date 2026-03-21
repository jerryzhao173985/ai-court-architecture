#!/bin/bash
# VERITAS System Verification Script

echo "============================================================"
echo "VERITAS SYSTEM VERIFICATION"
echo "============================================================"
echo ""

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "✗ Virtual environment not found. Run: python3 -m venv venv && pip install -e ."
    exit 1
fi

# Check 1: Dependencies
echo "CHECK 1: Dependencies"
echo "------------------------------------------------------------"
python -c "import openai, aiohttp, pydantic; print('✓ All dependencies installed')" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "✗ Missing dependencies - run: pip install -e ."
    exit 1
fi
echo ""

# Check 2: API Keys
echo "CHECK 2: API Keys"
echo "------------------------------------------------------------"
if [ -n "$OPENAI_API_KEY" ]; then
    echo "✓ OPENAI_API_KEY detected in environment"
else
    echo "⚠ OPENAI_API_KEY not set (will use test mode)"
fi

if grep -q "LUFFA_BOT_CLERK_SECRET=." .env 2>/dev/null; then
    echo "✓ Luffa bot secrets configured in .env"
else
    echo "⚠ Luffa bot secrets not set"
fi

if grep -q "LUFFA_BOT_ENABLED=true" .env 2>/dev/null; then
    echo "✓ Luffa Bot enabled"
else
    echo "⚠ Luffa Bot disabled (set LUFFA_BOT_ENABLED=true)"
fi
echo ""

# Check 3: Case Files
echo "CHECK 3: Case Files"
echo "------------------------------------------------------------"
if [ -f "fixtures/blackthorn-hall-001.json" ]; then
    echo "✓ Blackthorn Hall case file exists"
else
    echo "✗ Case file missing"
    exit 1
fi
echo ""

# Check 4: Bot Configuration
echo "CHECK 4: Bot Configuration"
echo "------------------------------------------------------------"
PYTHONPATH=src python -c "
from config import load_config
cfg = load_config()
bots = [r for r, b in [('clerk', cfg.luffa.clerk_bot), ('prosecution', cfg.luffa.prosecution_bot), ('defence', cfg.luffa.defence_bot), ('fact_checker', cfg.luffa.fact_checker_bot), ('judge', cfg.luffa.judge_bot)] if b]
print(f'✓ {len(bots)} bots configured: {chr(44).join(bots)}')
" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ Bot configuration check failed"
fi
echo ""

# Check 5: Unit Tests
echo "CHECK 5: Unit Tests"
echo "------------------------------------------------------------"
python -m pytest tests/unit/ -q --tb=no 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ Unit tests passing"
else
    echo "⚠ Some unit tests failed"
fi
echo ""

# Summary
echo "============================================================"
echo "VERIFICATION COMPLETE"
echo "============================================================"
echo ""
echo "Available commands:"
echo "  ./run_courtroom.sh     - Start multi-bot Luffa trial"
echo "  ./run_luffa_bot.sh     - Start single-bot service"
echo "  ./run_server.sh        - Start API server"
echo "  ./play.sh              - Interactive terminal demo"
echo ""
echo "See docs/LUFFA_INTEGRATION.md for technical reference."
echo ""

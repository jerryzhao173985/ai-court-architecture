#!/bin/bash
# VERITAS System Verification Script

echo "============================================================"
echo "VERITAS SYSTEM VERIFICATION"
echo "============================================================"
echo ""

# Activate virtual environment
source venv/bin/activate

# Check 1: Dependencies
echo "CHECK 1: Dependencies"
echo "------------------------------------------------------------"
python -c "import openai, anthropic, aiohttp, pytest, hypothesis; print('✓ All dependencies installed')" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✓ All Python packages available"
else
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

if grep -q "LUFFA_BOT_SECRET=." .env 2>/dev/null; then
    echo "✓ LUFFA_BOT_SECRET configured in .env"
else
    echo "⚠ LUFFA_BOT_SECRET not set (Luffa Bot disabled)"
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

# Check 4: Unit Tests
echo "CHECK 4: Unit Tests"
echo "------------------------------------------------------------"
python -m pytest tests/ -q --tb=no
if [ $? -eq 0 ]; then
    echo "✓ All unit tests passing"
else
    echo "✗ Some unit tests failed"
    exit 1
fi
echo ""

# Check 5: Production Tests (if API key available)
if [ -n "$OPENAI_API_KEY" ]; then
    echo "CHECK 5: Production Tests (OpenAI Integration)"
    echo "------------------------------------------------------------"
    python test_production.py
    if [ $? -eq 0 ]; then
        echo ""
        echo "✓ Production tests passing"
    else
        echo "✗ Production tests failed"
        exit 1
    fi
else
    echo "CHECK 5: Production Tests"
    echo "------------------------------------------------------------"
    echo "⚠ Skipped (no OPENAI_API_KEY)"
fi
echo ""

# Summary
echo "============================================================"
echo "VERIFICATION COMPLETE"
echo "============================================================"
echo ""
echo "✅ System is fully operational!"
echo ""
echo "Available commands:"
echo "  ./play.sh              - Interactive demo"
echo "  ./run_server.sh        - Start API server"
echo "  python test_production.py - Test with real OpenAI API"
echo ""
echo "To enable Luffa Bot:"
echo "  1. Get bot secret from https://robot.luffa.im"
echo "  2. Set LUFFA_BOT_SECRET in .env"
echo "  3. Set LUFFA_BOT_ENABLED=true in .env"
echo ""

#!/bin/bash

# VERITAS Courtroom Experience - Production Startup
# Group: Courtroom (Hqvqnvzh4mq)

echo "=========================================="
echo "🎭 VERITAS COURTROOM EXPERIENCE"
echo "=========================================="
echo ""
echo "Group: Courtroom (Hqvqnvzh4mq)"
echo "Bots: 5 trial agents"
echo ""

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
else
    echo "⚠️  Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
fi

# Quick configuration check
echo "🔍 Verifying configuration..."
PYTHONPATH=src python -c "from config import load_config; cfg = load_config(); print(f'✅ {len([b for b in [cfg.luffa.clerk_bot, cfg.luffa.prosecution_bot, cfg.luffa.defence_bot, cfg.luffa.fact_checker_bot, cfg.luffa.judge_bot] if b])} bots configured')"

if [ $? -ne 0 ]; then
    echo "❌ Configuration error"
    exit 1
fi

echo ""
echo "🚀 Starting Multi-Bot Service..."
echo "   Polling from Clerk bot"
echo "   Sending from all 5 bots"
echo ""
echo "📱 In your Courtroom group, type:"
echo "   /help - See commands"
echo "   /start - Begin trial"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=========================================="
echo ""

# Start the service
cd src && python multi_bot_service.py

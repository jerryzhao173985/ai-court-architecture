#!/bin/bash
# Start VERITAS multi-bot service for Luffa group chat

echo "================================"
echo "VERITAS Multi-Bot Service"
echo "================================"
echo ""

# Activate virtual environment
if [ -d venv ]; then
    source venv/bin/activate
fi

# Check configuration
echo "Testing configuration..."
PYTHONPATH=src python -c "from config import load_config; cfg = load_config(); roles = [r for r, b in [('clerk', cfg.luffa.clerk_bot), ('prosecution', cfg.luffa.prosecution_bot), ('defence', cfg.luffa.defence_bot), ('fact_checker', cfg.luffa.fact_checker_bot), ('judge', cfg.luffa.judge_bot)] if b]; print(f'✅ {len(roles)} bots configured: {', '.join(roles)}')"

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Configuration test failed"
    exit 1
fi

echo ""
echo "Starting multi-bot service..."
echo "Press Ctrl+C to stop"
echo ""

# Start the service
cd src && python multi_bot_service.py

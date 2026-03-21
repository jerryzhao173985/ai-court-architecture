#!/bin/bash
# Start VERITAS multi-bot service for Luffa group chat

echo "================================"
echo "VERITAS Multi-Bot Service"
echo "================================"
echo ""

# Check configuration
echo "Testing configuration..."
python test_multi_bot_config.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Configuration test failed"
    echo "Please run: python setup_bots.py"
    exit 1
fi

echo ""
echo "✓ Configuration valid"
echo ""
echo "Starting multi-bot service..."
echo "Press Ctrl+C to stop"
echo ""

# Start the service
python src/multi_bot_service.py

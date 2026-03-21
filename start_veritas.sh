#!/bin/bash

# VERITAS Multi-Bot Service Startup Script

echo "=========================================="
echo "VERITAS Courtroom Experience"
echo "Multi-Bot Service"
echo "=========================================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Copy .env.example to .env and configure your bot credentials"
    exit 1
fi

# Check if venv exists
if [ ! -d venv ]; then
    echo "⚠️  Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
else
    source venv/bin/activate
fi

# Verify configuration
echo "🔍 Verifying bot configuration..."
python test_multi_bot_setup.py

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Configuration test failed"
    echo "   Check your .env file and bot credentials"
    exit 1
fi

echo ""
echo "🚀 Starting VERITAS Multi-Bot Service..."
echo "   Press Ctrl+C to stop"
echo ""

# Start the service
python src/multi_bot_service.py

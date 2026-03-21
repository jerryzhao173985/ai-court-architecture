#!/bin/bash

# VERITAS Interactive Experience
# Play the courtroom experience yourself!

set -e

echo ""
echo "🎭 VERITAS - Interactive Courtroom Experience"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo ""
    echo "Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs) 2>/dev/null
    echo "✓ Configuration loaded (LLM enabled)"
else
    echo "ℹ️  Running in test mode (no API keys)"
    echo "   To enable real AI, create .env file with your API key"
fi

echo ""

# Run the interactive demo
cd src && ../venv/bin/python interactive_demo.py


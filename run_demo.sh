#!/bin/bash

# VERITAS Demo Runner
# This script runs the VERITAS courtroom experience demo

set -e

echo "VERITAS Courtroom Experience"
echo "============================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run setup first:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -e ."
    exit 1
fi

# Load environment variables if .env exists
if [ -f ".env" ]; then
    echo "Loading configuration from .env..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✓ Configuration loaded"
else
    echo "Warning: No .env file found. Running in test mode with placeholder responses."
    echo "To use real LLM integration, copy .env.example to .env and add your API keys."
fi

echo ""
echo "Starting demo..."
echo ""

# Run the demo
cd src && ../venv/bin/python main.py

#!/bin/bash

# VERITAS API Server Runner
# This script starts the FastAPI server for VERITAS

set -e

echo "VERITAS API Server"
echo "=================="
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
    echo "Warning: No .env file found. Running in test mode."
    echo "To use real LLM integration, copy .env.example to .env and add your API keys."
fi

echo ""
echo "Starting API server on http://localhost:8000..."
echo "API docs available at http://localhost:8000/docs"
echo ""

# Start the server
cd src && ../venv/bin/uvicorn api:app --reload --host 0.0.0.0 --port 8000

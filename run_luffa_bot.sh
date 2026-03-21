#!/bin/bash
# Start VERITAS Luffa Bot service

echo "Starting VERITAS Luffa Bot service..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ .env file not found"
    echo "Copy .env.example to .env and configure it"
    exit 1
fi

# Check if bot secret is set
if ! grep -q "LUFFA_BOT_SECRET=." .env; then
    echo "❌ LUFFA_BOT_SECRET not set in .env"
    echo ""
    echo "To get your bot secret:"
    echo "  1. Visit https://robot.luffa.im"
    echo "  2. Create or access your bot"
    echo "  3. Copy the bot secret"
    echo "  4. Add to .env: LUFFA_BOT_SECRET=<your_secret>"
    echo "  5. Set LUFFA_BOT_ENABLED=true"
    exit 1
fi

# Check if bot is enabled
if ! grep -q "LUFFA_BOT_ENABLED=true" .env; then
    echo "❌ LUFFA_BOT_ENABLED is not set to true in .env"
    echo "Set LUFFA_BOT_ENABLED=true to enable the bot"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Run the bot service
echo "✓ Configuration verified"
echo "✓ Starting bot service..."
echo ""
echo "The bot will poll for messages every 1 second."
echo "Press Ctrl+C to stop."
echo ""

python src/luffa_bot_service.py

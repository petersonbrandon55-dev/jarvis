#!/bin/bash
# One-command JARVIS setup

set -e

echo "=== JARVIS Setup ==="

# Create .env from example if not already present
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env — fill in your API keys before running JARVIS."
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "=== Setup complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. source .venv/bin/activate"
echo "  3. python main.py --text    (text mode, no mic needed)"
echo "  4. python main.py           (full voice mode)"
echo ""
echo "Required keys:"
echo "  ANTHROPIC_API_KEY  — get from console.anthropic.com"
echo ""
echo "Optional keys (more features):"
echo "  ELEVENLABS_API_KEY  — better JARVIS voice"
echo "  TAVILY_API_KEY      — web search"
echo "  PICOVOICE_ACCESS_KEY — 'Hey Jarvis' wake word"

# JARVIS

Brandon's personal AI assistant. Voice-activated, Claude-powered, with tools for web search, Mac control, Obsidian, and smart home.

## Quick Start

```bash
git clone https://github.com/brandonpeterson/jarvis.git
cd jarvis
chmod +x setup.sh && ./setup.sh
# Fill in .env with your API keys
source .venv/bin/activate
python main.py --text       # text mode to test
python main.py              # full voice mode
```

## Modes

| Mode | Command | Notes |
|------|---------|-------|
| Text | `python main.py --text` | No mic/speaker needed |
| Voice (keyboard) | `python main.py` | Press Enter to speak |
| Voice (wake word) | `python main.py` + `PICOVOICE_ACCESS_KEY` | Say "Hey Jarvis" |

## API Keys

| Key | Required | Where to get |
|-----|----------|--------------|
| `ANTHROPIC_API_KEY` | Yes | [console.anthropic.com](https://console.anthropic.com) |
| `TAVILY_API_KEY` | Recommended | [tavily.com](https://tavily.com) — free tier |
| `ELEVENLABS_API_KEY` | Optional | [elevenlabs.io](https://elevenlabs.io) — better voice |
| `PICOVOICE_ACCESS_KEY` | Optional | [console.picovoice.ai](https://console.picovoice.ai) — wake word |
| `HOME_ASSISTANT_TOKEN` | Optional | HA → Profile → Long-Lived Tokens |

## Capabilities

- **Web search** — current AI news, business strategies, anything
- **Mac control** — open apps, run commands
- **Obsidian** — read/write notes in your vault
- **Smart home** — control lights and devices via Home Assistant
- **Persistent memory** — JARVIS remembers context across the conversation

## Project Structure

```
jarvis/
├── main.py              # Entry point
├── core/
│   ├── brain.py         # Claude API + tool orchestration
│   ├── listener.py      # Wake word detection
│   ├── transcriber.py   # Speech-to-text (Whisper)
│   └── speaker.py       # Text-to-speech (ElevenLabs / pyttsx3)
├── tools/
│   ├── search.py        # Tavily web search
│   ├── mac_control.py   # Mac automation
│   ├── obsidian.py      # Obsidian vault R/W
│   └── home_assistant.py# Smart home
└── config/
    └── settings.py      # All config from .env
```

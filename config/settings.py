import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY", "")

# Home Assistant
HOME_ASSISTANT_URL = os.getenv("HOME_ASSISTANT_URL", "http://homeassistant.local:8123")
HOME_ASSISTANT_TOKEN = os.getenv("HOME_ASSISTANT_TOKEN", "")

# Obsidian
OBSIDIAN_VAULT_PATH = Path(os.getenv("OBSIDIAN_VAULT_PATH", str(Path.home() / "Documents" / "Obsidian")))

# Claude model
CLAUDE_MODEL = "claude-sonnet-4-6"

# Audio settings
SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.01
SILENCE_DURATION = 1.5   # seconds of silence before stopping recording
MAX_RECORD_SECONDS = 30

# Whisper model — "tiny" is fastest, "base"/"small" are more accurate
WHISPER_MODEL = "base"

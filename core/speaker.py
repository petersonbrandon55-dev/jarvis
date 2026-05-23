import io
import os
import tempfile
import subprocess
from config.settings import ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID


class Speaker:
    def __init__(self):
        self.use_elevenlabs = bool(ELEVENLABS_API_KEY and ELEVENLABS_VOICE_ID)
        if self.use_elevenlabs:
            from elevenlabs.client import ElevenLabs
            self.client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            print("[JARVIS] Speaker: ElevenLabs")
        else:
            import pyttsx3
            self.engine = pyttsx3.init()
            self.engine.setProperty("rate", 175)
            self.engine.setProperty("volume", 0.9)
            print("[JARVIS] Speaker: pyttsx3 (set ELEVENLABS_API_KEY for better voice)")

    def speak(self, text: str):
        print(f"[JARVIS] Speaking: {text}")
        if self.use_elevenlabs:
            self._speak_elevenlabs(text)
        else:
            self._speak_pyttsx3(text)

    def _speak_elevenlabs(self, text: str):
        audio = self.client.text_to_speech.convert(
            voice_id=ELEVENLABS_VOICE_ID,
            text=text,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            for chunk in audio:
                f.write(chunk)
            tmp_path = f.name
        subprocess.run(["afplay", tmp_path], check=True)
        os.unlink(tmp_path)

    def _speak_pyttsx3(self, text: str):
        self.engine.say(text)
        self.engine.runAndWait()

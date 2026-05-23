"""
Wake word listener. Priority order:
  1. VAD (voice activity detection) — always-on, no API key, no extra deps
  2. Porcupine (requires PICOVOICE_ACCESS_KEY) — "Hey Jarvis" wake word
  3. Keyboard fallback — press Enter

VAD mode: JARVIS silently monitors the mic. When it hears sustained speech
above a noise threshold it triggers immediately — no button, no wake word.
"""
import time
import numpy as np
import sounddevice as sd
from config.settings import PICOVOICE_ACCESS_KEY, SAMPLE_RATE

# How loud speech needs to be to trigger (0.0–1.0). Raise if it triggers on background noise.
VAD_THRESHOLD = 0.02
# How many consecutive loud chunks needed before triggering (~0.3s at 10 chunks/sec)
VAD_TRIGGER_CHUNKS = 3


class Listener:
    def __init__(self):
        self.mode = None

        # Try Porcupine if key is set
        key_set = bool(PICOVOICE_ACCESS_KEY) and PICOVOICE_ACCESS_KEY != "your_key_here"
        if key_set:
            try:
                self._init_porcupine()
                self.mode = "porcupine"
            except Exception as e:
                print(f"[JARVIS] Porcupine failed ({e})")

        # Default: VAD (always-on, no deps)
        if not self.mode:
            self.mode = "vad"
            print("[JARVIS] Always-on listening active (VAD) — just start speaking")

    def _init_porcupine(self):
        import pvporcupine
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=["jarvis"],
        )
        print("[JARVIS] Wake word: 'Hey Jarvis' (Porcupine)")

    def wait_for_wake(self):
        if self.mode == "porcupine":
            self._wait_porcupine()
        elif self.mode == "vad":
            self._wait_vad()
        else:
            self._wait_keyboard()

    def _wait_vad(self):
        """Trigger as soon as sustained speech is detected."""
        chunk_size = SAMPLE_RATE // 10  # 100ms chunks
        loud_count = 0
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32", blocksize=chunk_size) as stream:
            while True:
                chunk, _ = stream.read(chunk_size)
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                if rms > VAD_THRESHOLD:
                    loud_count += 1
                    if loud_count >= VAD_TRIGGER_CHUNKS:
                        return
                else:
                    loud_count = 0

    def _wait_porcupine(self):
        frame_length = self.porcupine.frame_length
        print("[JARVIS] Waiting for 'Hey Jarvis'...")
        with sd.InputStream(samplerate=self.porcupine.sample_rate, channels=1,
                            dtype="int16", blocksize=frame_length) as stream:
            while True:
                pcm, _ = stream.read(frame_length)
                if self.porcupine.process(pcm.flatten().tolist()) >= 0:
                    print("[JARVIS] Wake word detected!")
                    return

    def _wait_keyboard(self):
        input("\nPress Enter to speak to JARVIS... ")

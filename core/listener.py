"""
Wake word listener. Supports two modes:
  - Porcupine (requires PICOVOICE_ACCESS_KEY) — says "Hey Jarvis" to trigger
  - Keyboard (fallback) — press Enter to trigger
"""
import struct
import numpy as np
import sounddevice as sd
from config.settings import PICOVOICE_ACCESS_KEY, SAMPLE_RATE


class Listener:
    def __init__(self):
        self.use_porcupine = bool(PICOVOICE_ACCESS_KEY)
        if self.use_porcupine:
            self._init_porcupine()
        else:
            print("[JARVIS] Wake word disabled — press Enter to speak (set PICOVOICE_ACCESS_KEY to enable 'Hey Jarvis')")

    def _init_porcupine(self):
        import pvporcupine
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=["jarvis"],
        )
        print("[JARVIS] Wake word: 'Hey Jarvis' (Porcupine)")

    def wait_for_wake(self):
        """Block until wake word is detected (or Enter is pressed in keyboard mode)."""
        if self.use_porcupine:
            self._wait_porcupine()
        else:
            self._wait_keyboard()

    def _wait_porcupine(self):
        frame_length = self.porcupine.frame_length
        with sd.InputStream(
            samplerate=self.porcupine.sample_rate,
            channels=1,
            dtype="int16",
            blocksize=frame_length,
        ) as stream:
            print("[JARVIS] Waiting for 'Hey Jarvis'...")
            while True:
                pcm, _ = stream.read(frame_length)
                pcm_flat = pcm.flatten().tolist()
                result = self.porcupine.process(pcm_flat)
                if result >= 0:
                    print("[JARVIS] Wake word detected!")
                    return

    def _wait_keyboard(self):
        input("\nPress Enter to speak to JARVIS... ")

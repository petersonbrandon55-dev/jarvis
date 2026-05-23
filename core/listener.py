"""
Wake word listener. Priority order:
  1. openwakeword (free, built-in "hey_jarvis" model) — always-on, no API key needed
  2. Porcupine (requires PICOVOICE_ACCESS_KEY)
  3. Keyboard fallback — press Enter
"""
import numpy as np
import sounddevice as sd
from config.settings import PICOVOICE_ACCESS_KEY, SAMPLE_RATE


class Listener:
    def __init__(self):
        self.mode = None

        # Try openwakeword first (free, no key needed)
        try:
            self._init_openwakeword()
            self.mode = "openwakeword"
        except Exception as e:
            print(f"[JARVIS] openwakeword unavailable ({e})")

        # Try Porcupine if openwakeword failed and key is set
        if not self.mode:
            key_set = bool(PICOVOICE_ACCESS_KEY) and PICOVOICE_ACCESS_KEY != "your_key_here"
            if key_set:
                try:
                    self._init_porcupine()
                    self.mode = "porcupine"
                except Exception as e:
                    print(f"[JARVIS] Porcupine failed ({e})")

        if not self.mode:
            self.mode = "keyboard"
            print("[JARVIS] Wake word unavailable — press Enter to speak")

    def _init_openwakeword(self):
        from openwakeword import Model, get_pretrained_model_paths
        paths = get_pretrained_model_paths()
        jarvis_model = next((p for p in paths if "hey_jarvis" in p), None)
        if not jarvis_model:
            raise RuntimeError("hey_jarvis model not found")
        self.oww_model = Model(wakeword_models=[jarvis_model], inference_framework="tflite")
        self.oww_chunk = 1280  # 80ms at 16kHz
        print("[JARVIS] Wake word: 'Hey Jarvis' (openwakeword)")

    def _init_porcupine(self):
        import pvporcupine
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=["jarvis"],
        )
        print("[JARVIS] Wake word: 'Hey Jarvis' (Porcupine)")

    def wait_for_wake(self):
        if self.mode == "openwakeword":
            self._wait_openwakeword()
        elif self.mode == "porcupine":
            self._wait_porcupine()
        else:
            self._wait_keyboard()

    def _wait_openwakeword(self):
        print("[JARVIS] Waiting for 'Hey Jarvis'...")
        with sd.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=self.oww_chunk) as stream:
            while True:
                pcm, _ = stream.read(self.oww_chunk)
                pcm_flat = pcm.flatten()
                self.oww_model.predict(pcm_flat)
                scores = self.oww_model.prediction_buffer
                for name, buf in scores.items():
                    if buf and buf[-1] > 0.5:
                        print("[JARVIS] Wake word detected!")
                        self.oww_model.reset()
                        return

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

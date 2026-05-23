"""
Wake word listener with pre-roll buffer.

VAD mode: continuously buffers the last 2 seconds of audio. When it detects
sustained speech it triggers immediately AND returns the buffered audio so the
transcriber never misses the start of what you said.
"""
import collections
import numpy as np
import sounddevice as sd
from config.settings import PICOVOICE_ACCESS_KEY, SAMPLE_RATE

VAD_THRESHOLD   = 0.015   # RMS level to consider as speech — lower = more sensitive
VAD_TRIGGER_CHUNKS = 2    # consecutive loud chunks before triggering (~200ms)
PRE_ROLL_SECS   = 1.5     # seconds of audio to keep before trigger
CHUNK_SIZE      = SAMPLE_RATE // 10  # 100ms chunks


class Listener:
    def __init__(self):
        self.mode = None

        key_set = bool(PICOVOICE_ACCESS_KEY) and PICOVOICE_ACCESS_KEY != "your_key_here"
        if key_set:
            try:
                self._init_porcupine()
                self.mode = "porcupine"
            except Exception as e:
                print(f"[JARVIS] Porcupine failed ({e})")

        if not self.mode:
            self.mode = "vad"
            print("[JARVIS] Always-on listening active — just start speaking")

    def _init_porcupine(self):
        import pvporcupine
        self.porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=["jarvis"],
        )
        print("[JARVIS] Wake word: 'Hey Jarvis' (Porcupine)")

    def wait_for_wake(self) -> np.ndarray:
        """Block until speech is detected. Returns pre-roll audio so nothing is missed."""
        if self.mode == "porcupine":
            self._wait_porcupine()
            return np.array([], dtype=np.float32)
        elif self.mode == "vad":
            return self._wait_vad()
        else:
            input("\nPress Enter to speak to JARVIS... ")
            return np.array([], dtype=np.float32)

    def _wait_vad(self) -> np.ndarray:
        pre_roll_len = int(PRE_ROLL_SECS * 10)  # in chunks
        ring = collections.deque(maxlen=pre_roll_len)
        loud_count = 0

        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                            blocksize=CHUNK_SIZE) as stream:
            while True:
                chunk, _ = stream.read(CHUNK_SIZE)
                chunk = chunk.copy().flatten()
                ring.append(chunk)
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                if rms > VAD_THRESHOLD:
                    loud_count += 1
                    if loud_count >= VAD_TRIGGER_CHUNKS:
                        # Return everything buffered so transcriber has the full phrase
                        return np.concatenate(list(ring))
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
                    return

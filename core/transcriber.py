import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel
from config.settings import SAMPLE_RATE, SILENCE_THRESHOLD, SILENCE_DURATION, MAX_RECORD_SECONDS, WHISPER_MODEL


class Transcriber:
    def __init__(self):
        print("[JARVIS] Loading Whisper model...")
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        self.sample_rate = SAMPLE_RATE

    def record_until_silence(self, pre_roll: np.ndarray = None) -> np.ndarray:
        """Record from mic until silence, prepending any pre-roll audio from the listener."""
        frames = [pre_roll] if pre_roll is not None and len(pre_roll) > 0 else []
        silent_chunks = 0
        chunks_per_second = 10
        silence_chunks_needed = int(SILENCE_DURATION * chunks_per_second)
        chunk_size = self.sample_rate // chunks_per_second
        max_chunks = MAX_RECORD_SECONDS * chunks_per_second

        with sd.InputStream(samplerate=self.sample_rate, channels=1, dtype="float32") as stream:
            for _ in range(max_chunks):
                chunk, _ = stream.read(chunk_size)
                frames.append(chunk.copy().flatten())
                rms = float(np.sqrt(np.mean(chunk ** 2)))
                if rms < SILENCE_THRESHOLD:
                    silent_chunks += 1
                else:
                    silent_chunks = 0
                if silent_chunks >= silence_chunks_needed and len(frames) > chunks_per_second:
                    break

        return np.concatenate(frames) if frames else np.array([], dtype=np.float32)

    def transcribe(self, audio: np.ndarray) -> str:
        if len(audio) == 0:
            return ""
        segments, _ = self.model.transcribe(audio, language="en", beam_size=5)
        return " ".join(seg.text.strip() for seg in segments).strip()

    def listen_and_transcribe(self, pre_roll: np.ndarray = None) -> str:
        audio = self.record_until_silence(pre_roll=pre_roll)
        text = self.transcribe(audio)
        print(f"[JARVIS] Heard: {text}")
        return text

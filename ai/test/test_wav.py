import asyncio
import math
import wave

import numpy as np
import pyaudio
from scipy.signal import resample_poly

from ai.realtime.session_gemini import GeminiRealtimeSession

# --- AUDIO PLAYBACK SETUP ---
# Gemini Live audio output is 24kHz, 1 channel, 16-bit PCM
SAMPLE_RATE_OUT = 24000
p = pyaudio.PyAudio()
speaker_stream = p.open(
    format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE_OUT, output=True
)


def read_and_resample_wav(file_path: str, target_rate: int = 16000) -> bytes:
    wf = wave.open(file_path, "rb")
    src_rate = wf.getframerate()
    channels = wf.getnchannels()
    raw = wf.readframes(wf.getnframes())
    wf.close()

    samples = np.frombuffer(raw, dtype=np.int16)
    if channels == 2:
        samples = samples[::2]
    if src_rate != target_rate:
        g = math.gcd(target_rate, src_rate)
        samples = resample_poly(samples, target_rate // g, src_rate // g)
        samples = samples.astype(np.int16)

    print(f"📊 Resampled: {src_rate}Hz → {target_rate}Hz | {len(samples)} samples")
    return samples.tobytes()


async def stream_wav(file_path: str):
    print(f"--- 📁 SENDING WAV FILE: {file_path} ---")

    pcm_bytes = read_and_resample_wav(file_path)
    session = GeminiRealtimeSession(
        "wav_test_01", "You are an AI auditor. Listen and summarize.", turns=1
    )
    phase_done = asyncio.Event()

    async def on_audio(chunk: bytes):
        # Play the audio chunk arriving from Gemini
        speaker_stream.write(chunk)
        print(f"🔊 AI streaming audio back ({len(chunk)} bytes)...")

    async def on_phase_complete(history):
        print("\n✅ Phase complete. Transcript:")
        for msg in history:
            print(f"  ({msg['role']}): {msg['content']}")
        phase_done.set()

    session.on_audio_to_frontend = on_audio
    session.on_phase_complete = on_phase_complete

    await session.connect()

    # Stream in 3200-byte chunks
    print("🚀 Streaming resampled audio to Gemini...")
    chunk_size = 3200
    offset = 0
    total = len(pcm_bytes)

    while offset < total:
        chunk = pcm_bytes[offset : offset + chunk_size]
        offset += chunk_size
        is_last = offset >= total

        await session.send_user_audio(chunk, end_of_stream=is_last)
        await asyncio.sleep(0.1)

    print("✅ Finished streaming. Waiting for response...")

    try:
        await asyncio.wait_for(phase_done.wait(), timeout=15)
    except asyncio.TimeoutError:
        print("⚠️ Timeout — no response from Gemini within 15s.")

    # Cleanup
    await session.close()
    speaker_stream.stop_stream()
    speaker_stream.close()
    p.terminate()


if __name__ == "__main__":
    asyncio.run(stream_wav("test_audio.wav"))

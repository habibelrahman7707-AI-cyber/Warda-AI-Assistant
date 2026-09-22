import edge_tts
import asyncio
from faster_whisper import WhisperModel
import os

# Initialize Whisper model for STT
# We use "base" or "small" for speed. For better accuracy, use "medium"
model_size = "base"
model = WhisperModel(model_size, device="cpu", compute_type="int8")

def transcribe_audio(audio_path: str) -> str:
    """
    Transcribes audio using Faster-Whisper.
    """
    try:
        segments, info = model.transcribe(audio_path, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

async def generate_speech_async(text: str, output_path: str):
    """
    Generates speech using Edge TTS.
    """
    # voice options: "ar-EG-SalmaNeural", "en-US-AriaNeural"
    # We can detect language or just use a default
    voice = "ar-EG-SalmaNeural" if any("\u0600" <= c <= "\u06FF" for c in text) else "en-US-AriaNeural"
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)

def generate_speech(text: str, output_path: str):
    """
    Synchronous wrapper for generating speech.
    """
    asyncio.run(generate_speech_async(text, output_path))

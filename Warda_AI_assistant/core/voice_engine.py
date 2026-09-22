import os
import time
import threading
import pygame
import speech_recognition as sr
import edge_tts
import asyncio

# Initialize pygame mixer for audio playback
pygame.mixer.init()

class VoiceEngine:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        
        # We will instantiate the Microphone inside the listen() method 
        # to prevent PyAudio stream collisions and context manager errors.
            
        self.is_speaking = False
        self.interrupted = False
        
    def _generate_audio(self, text: str, output_file: str):
        """Generates TTS using edge-tts. Auto-detects language based on characters."""
        import re
        import asyncio
        
        # Clean markdown symbols so the TTS doesn't say "asterisk", "dash", etc.
        clean_text = re.sub(r'[*#_~`\[\]()-]', '', text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        arabic_chars = len(re.findall(r'[\u0600-\u06FF]', clean_text))
        english_chars = len(re.findall(r'[a-zA-Z]', clean_text))
        
        if arabic_chars >= english_chars:
            voice = "ar-EG-SalmaNeural"
        else:
            voice = "en-US-AriaNeural"
            
        communicate = edge_tts.Communicate(text, voice)
        
        # Safely run asyncio in a separate thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(communicate.save(output_file))
        finally:
            loop.close()
        
    def speak(self, text: str, on_interrupt=None):
        """
        Speaks the given text. 
        If on_interrupt returns True at any point, stops speaking.
        """
        self.is_speaking = True
        self.interrupted = False
        
        import uuid
        unique_id = uuid.uuid4().hex
        output_file = os.path.expanduser(f"~/Desktop/ai-agent/temp_voice_{unique_id}.mp3")
        self._generate_audio(text, output_file)
        
        pygame.mixer.music.load(output_file)
        pygame.mixer.music.play()
        
        # Wait for audio to finish, checking for interruptions
        while pygame.mixer.music.get_busy():
            if on_interrupt and on_interrupt():
                pygame.mixer.music.stop()
                self.interrupted = True
                print("\n[Voice Engine] Speech Interrupted by user!")
                break
            time.sleep(0.05)
            
        self.is_speaking = False
        # Optional: cleanup file
        try:
            if not pygame.mixer.music.get_busy():
                pygame.mixer.music.unload()
                os.remove(output_file)
        except Exception:
            pass

    def start_manual_recording(self, device_index=None):
        """Starts recording audio into a buffer using sr.Microphone for safe audio format negotiation."""
        self.is_recording = True
        self.audio_data = None
        print(f"[Voice Engine] Starting manual recording on device {device_index}...")
        
        def record_thread():
            try:
                with sr.Microphone(device_index=device_index) as source:
                    frames = []
                    print("[Voice Engine] Recording thread started...")
                    while self.is_recording:
                        buffer = source.stream.read(source.CHUNK)
                        frames.append(buffer)
                        
                    if frames:
                        self.audio_data = sr.AudioData(b"".join(frames), source.SAMPLE_RATE, source.SAMPLE_WIDTH)
                        print(f"[Voice Engine] Captured {len(frames)} frames of audio.")
                    else:
                        print("[Voice Engine] No frames captured.")
            except Exception as e:
                print(f"[Voice Engine] Recording failed: {e}")
                
        threading.Thread(target=record_thread, daemon=True).start()

    def stop_manual_recording_and_transcribe(self) -> str:
        """Stops recording and returns the transcribed text using Groq Whisper (auto-detects language)."""
        print("[Voice Engine] Stopping recording and transcribing...")
        self.is_recording = False
        time.sleep(0.3) # Give the thread time to finish saving self.audio_data
        
        if not hasattr(self, 'audio_data') or self.audio_data is None:
            print("[Voice Engine] Transcription Failed: No audio data was captured. Please check your microphone.")
            return ""
            
        try:
            print("[Voice Engine] Transcribing using Groq Whisper...")
            import requests
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"}
            files = {
                'file': ('audio.wav', self.audio_data.get_wav_data(), 'audio/wav'),
            }
            data = {
                'model': 'whisper-large-v3'
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                text = response.json().get('text', '').strip()
                print(f"[Voice Engine] Transcribed: {text}")
                return text
            else:
                print(f"[Voice Engine] Groq API Error: {response.text}")
                return ""
        except Exception as e:
            print(f"[Voice Engine] Transcription Failed: {e}")
            return ""

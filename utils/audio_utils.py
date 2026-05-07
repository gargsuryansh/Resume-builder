import os
import requests
import base64
import io
import streamlit as st
from gtts import gTTS
import tempfile

class AudioUtils:
    """Utility class for speech-to-text and text-to-speech services"""
    
    def __init__(self):
        self.sarvam_api_key = os.getenv("SARVAM_API_KEY")
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        
    def transcribe_audio(self, audio_bytes):
        """Transcribe audio using Groq Whisper model"""
        if not self.groq_api_key:
            return "Groq API key missing. Cannot transcribe."
        
        try:
            # Groq audio transcription endpoint
            url = "https://api.groq.com/openai/v1/audio/transcriptions"
            headers = {
                "Authorization": f"Bearer {self.groq_api_key}"
            }
            
            # Create a temporary file because Groq API expects a file upload
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
                temp_audio.write(audio_bytes)
                temp_audio_path = temp_audio.name
            
            with open(temp_audio_path, "rb") as f:
                files = {
                    "file": (os.path.basename(temp_audio_path), f, "audio/wav"),
                    "model": (None, "whisper-large-v3"),
                    "response_format": (None, "json")
                }
                response = requests.post(url, headers=headers, files=files, timeout=30)
            
            # Cleanup temp file
            os.unlink(temp_audio_path)
            
            response.raise_for_status()
            data = response.json()
            return data.get("text", "")
            
        except Exception as e:
            return f"Transcription error: {str(e)}"

    def text_to_speech(self, text, mode='english'):
        """Convert text to speech using Sarvam AI (fallback to gTTS)"""
        if self.sarvam_api_key:
            try:
                url = "https://api.sarvam.ai/text-to-speech"
                headers = {
                    "api-subscription-key": self.sarvam_api_key,
                    "Content-Type": "application/json"
                }
                
                # Determine language code and speaker based on mode
                lang_code = "en-IN" if mode.lower() == 'english' else "hi-IN"
                speaker = "shubh" if mode.lower() == 'english' else "meera"
                
                payload = {
                    "text": text,
                    "target_language_code": lang_code,
                    "speaker": speaker,
                    "model": "bulbul:v3"
                }
                
                response = requests.post(url, headers=headers, json=payload, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                if 'audios' in data and data['audios']:
                    # Sarvam returns base64 encoded audio
                    audio_base64 = data['audios'][0]
                    return base64.b64decode(audio_base64)
            except Exception as e:
                print(f"Sarvam TTS failed: {str(e)}. Falling back to gTTS.")
        
        # Fallback to gTTS
        try:
            tts = gTTS(text=text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            return fp.getvalue()
        except Exception as e:
            print(f"gTTS failed: {str(e)}")
            return None

    @staticmethod
    def autoplay_audio(audio_bytes, audio_id=None):
        """Helper to autoplay audio in Streamlit with stable re-triggering"""
        if not audio_bytes:
            return
            
        if audio_id is None:
            import time
            audio_id = f"audio_{int(time.time()*1000)}"
            
        b64 = base64.b64encode(audio_bytes).decode()
        
        # Use a more robust HTML5 audio player with a unique key
        audio_html = f"""
            <div id="container_{audio_id}">
                <audio id="{audio_id}" autoplay="true">
                    <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById("{audio_id}");
                    audio.onplay = function() {{
                        console.log("Audio started playing: {audio_id}");
                    }};
                    audio.onended = function() {{
                        console.log("Audio finished: {audio_id}");
                        // Dispatch event for Continuous Mode
                        window.parent.postMessage({{
                            type: 'audio_finished',
                            id: '{audio_id}'
                        }}, '*');
                    }};
                </script>
            </div>
        """
        st.components.v1.html(audio_html, height=0, width=0)

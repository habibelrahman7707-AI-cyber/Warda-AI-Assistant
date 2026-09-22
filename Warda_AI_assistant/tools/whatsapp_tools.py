from crewai.tools import tool
import requests
import os
import json

NODE_API = "http://127.0.0.1:3001"

@tool("get_whatsapp_chats")
def get_whatsapp_chats(search_query: str = "") -> str:
    """
    Searches your WhatsApp contacts for a specific name and returns their Chat ID.
    Args:
        search_query: The name of the person (e.g. 'MUM' or 'Ahmed'). 
    CRITICAL: You MUST use this tool to find the person's `id` (e.g., 201xxxxxx@c.us). 
    NEVER use their name in the send_whatsapp_message tool, ONLY use the `id`!
    """
    try:
        res = requests.get(f"{NODE_API}/chats?q={search_query}")
        if res.status_code == 200:
            return json.dumps(res.json(), ensure_ascii=False, indent=2)
        return f"Error: {res.text}"
    except Exception as e:
        return f"WhatsApp Node service not running: {str(e)}"



@tool("send_whatsapp_message")
def send_whatsapp_message(to: str, message: str) -> str:
    """
    Sends a WhatsApp text message to a specific number or Chat ID.
    Args:
        to: The phone number or chat ID (e.g., '1234567890' or '1234567890@c.us').
        message: The text message to send.
    """
    try:
        res = requests.post(f"{NODE_API}/send", json={"to": to, "message": message})
        if res.status_code == 200:
            return "Message sent successfully!"
        return f"Error: {res.text}"
    except Exception as e:
        return f"WhatsApp Node service not running: {str(e)}"

@tool("read_new_whatsapp_messages")
def read_new_whatsapp_messages(dummy: str = "") -> str:
    """
    Reads the list of all recently received WhatsApp messages, including those with media (Voice Notes, Images).
    This tells you what the user just received (e.g., if the user asks 'what did they just send me?').
    Returns JSON containing the message body, sender, and mediaPath if it has media (like a voice note).
    Args:
        dummy: Unused, pass empty string.
    """
    try:
        save_path = os.path.expanduser('~/Desktop/ai-agent/whatsapp_service/latest_incoming.json')
        if not os.path.exists(save_path):
            return "No new messages received yet."
        with open(save_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading local messages: {str(e)}"

@tool("transcribe_voice_note")
def transcribe_voice_note(media_path: str) -> str:
    """
    Transcribes an audio file (Voice Note) to text using Groq Whisper.
    Args:
        media_path: The absolute path to the audio file (e.g., from read_new_whatsapp_messages).
    Returns:
        The transcribed text, which you can then summarize or translate.
    """
    import os
    import requests
    
    if not os.path.exists(media_path):
        return f"Error: File {media_path} does not exist."
        
    try:
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {"Authorization": f"Bearer {os.environ.get('GROQ_API_KEY')}"}
        
        with open(media_path, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(media_path), audio_file, 'audio/ogg'),
            }
            data = {
                'model': 'whisper-large-v3'
            }
            response = requests.post(url, headers=headers, files=files, data=data)
            
            if response.status_code == 200:
                text = response.json().get('text', '').strip()
                return text
            else:
                return f"Groq API Error: {response.text}"
    except Exception as e:
        return f"Error transcribing audio: {str(e)}"

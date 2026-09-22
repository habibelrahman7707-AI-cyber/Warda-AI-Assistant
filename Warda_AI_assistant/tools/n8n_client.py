from crewai.tools import tool
import requests
import json
import os

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "http://localhost:5678/webhook/ai-agent")

@tool("Send Message via n8n")
def send_n8n_message(message: str, platform: str, recipient: str = "") -> str:
    """
    Sends a message to a recipient via a specific platform using an n8n webhook.
    
    Args:
        message (str): The content of the message to send.
        platform (str): The platform to use (e.g., "whatsapp", "email").
        recipient (str): The phone number or email address of the recipient.
        
    Returns:
        str: Status of the request.
    """
    payload = {
        "message": message,
        "platform": platform,
        "recipient": recipient
    }
    
    try:
        response = requests.post(N8N_WEBHOOK_URL, json=payload, headers={"Content-Type": "application/json"})
        response.raise_for_status()
        return f"Successfully sent message to {platform}. Response: {response.text}"
    except requests.exceptions.ConnectionError:
        return f"Error: The n8n server is not reachable at {N8N_WEBHOOK_URL}. Please ensure n8n is running locally or check your Webhook URL configuration."
    except Exception as e:
        return f"Failed to send message via n8n: {str(e)}"

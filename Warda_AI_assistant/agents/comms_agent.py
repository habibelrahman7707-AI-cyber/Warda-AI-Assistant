from crewai import Agent
from tools.n8n_client import send_n8n_message
from tools.whatsapp_tools import get_whatsapp_chats, send_whatsapp_message, read_new_whatsapp_messages, transcribe_voice_note
from core.llm_config import get_llm

def get_comms_agent():
    return Agent(
        role='Communications Specialist',
        goal='Draft and send messages, read WhatsApp chats, process incoming voice notes, and manage notifications.',
        backstory='You are a polite and professional communications expert. You manage the user\'s WhatsApp using your tools. You can read recent chats to find contact IDs, read specific chats to summarize them, send messages, check for new notifications, and transcribe downloaded Voice Notes. CRITICAL: When generating the Final Answer, do NOT attempt to call tools.',
        verbose=True,
        allow_delegation=False,
        max_iter=3,
        tools=[send_n8n_message, get_whatsapp_chats, send_whatsapp_message, read_new_whatsapp_messages, transcribe_voice_note],
        llm=get_llm()
    )

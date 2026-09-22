import streamlit as st
import os
import tempfile
from core.voice import transcribe_audio, generate_speech
from agents.crew_manager import execute_user_request

st.set_page_config(page_title="My AI Agent", page_icon="🤖", layout="centered")

st.title("🤖 Personal AI Assistant")
st.write("Talk to me or type your request below!")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "audio" in msg:
            st.audio(msg["audio"])

# Audio Input (Streamlit >= 1.39 natively supports st.audio_input)
audio_bytes = None
try:
    audio_bytes = st.audio_input("Record a voice message")
except AttributeError:
    st.info("Update Streamlit to use voice recording: pip install --upgrade streamlit")

user_input = st.chat_input("Or type your message here...")

# Process Audio Input
if audio_bytes:
    # Save audio temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_audio:
        tmp_audio.write(audio_bytes.read())
        audio_path = tmp_audio.name
    
    with st.spinner("Transcribing audio..."):
        user_input = transcribe_audio(audio_path)
    os.remove(audio_path)
    
# Process Text Input or Transcribed Audio
if user_input:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process with CrewAI
    with st.chat_message("assistant"):
        with st.spinner("Thinking & Acting..."):
            # Prepare last 5 messages for context
            chat_context = "\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.messages[-6:-1]])
            
            response_text = str(execute_user_request(user_input, chat_context))
            st.markdown(response_text)
            
            # Generate Audio Response
            tts_audio_path = os.path.join(tempfile.gettempdir(), "response.mp3")
            generate_speech(response_text, tts_audio_path)
            
            st.audio(tts_audio_path)
            
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response_text, "audio": tts_audio_path})

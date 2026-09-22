# Warda AI Assistant (وردة) 🌸

Warda AI is a powerful, fully autonomous desktop assistant capable of orchestrating complex tasks, controlling your system, browsing the web, and seamlessly interacting with WhatsApp. Built with **CrewAI**, **LangChain**, and **CustomTkinter**, Warda provides a beautiful native desktop interface with push-to-talk voice recognition and an intelligent task planner.

## ✨ Features

- **Native Desktop App**: Beautiful, responsive UI built with CustomTkinter.
- **Voice Recognition (Push-to-Talk)**: Speak naturally to Warda using your system's default microphone.
- **WhatsApp Integration**: Read incoming messages, summarize voice notes, and send messages via a robust local Node.js microservice (`whatsapp-web.js`).
- **Autonomous Multi-Agent Crew**:
  - `Comms Agent`: Handles all WhatsApp and communication tasks.
  - `Search Agent`: Browses the internet for real-time information.
  - `File Agent`: Creates, reads, moves files, and downloads media.
  - `System Agent`: Executes local system commands and installs apps via Winget.
  - `Browser Agent`: Navigates complex web structures.
- **Smart API Key Rotation**: Automatically swaps between multiple API keys to bypass rate limits (429 errors) seamlessly.

## 🚀 Installation & Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/Warda-AI-Assistant.git
   cd Warda-AI-Assistant
   ```

2. **Python Dependencies**
   Make sure you have Python 3.10+ installed.
   ```bash
   pip install -r requirements.txt
   ```
   *(Note: Ensure you have `crewai`, `langchain`, `customtkinter`, `speech_recognition`, and `pygame` installed)*

3. **Node.js Dependencies (For WhatsApp)**
   Ensure you have Node.js installed, then install the required packages for the WhatsApp server:
   ```bash
   cd whatsapp_service
   npm install
   cd ..
   ```

4. **API Keys Configuration**
   Create a file named `api_keys.json` in the root directory:
   ```json
   {
     "groq_keys": [
       "YOUR_FIRST_GROQ_API_KEY",
       "YOUR_SECOND_GROQ_API_KEY"
     ]
   }
   ```
   The system will automatically rotate through these keys to avoid rate limiting.

## 🛠️ Usage

1. **Start the WhatsApp Server**
   Run the batch script to start the WhatsApp local microservice:
   ```bash
   start_whatsapp.bat
   ```
   *Scan the QR code with your phone to link your WhatsApp account. Keep this terminal window open in the background.*

2. **Start Warda AI**
   Run the main Python application:
   ```bash
   python main.py
   ```

3. **Interact**
   - Click the **🎙️ Start Recording** button to speak to Warda, or type your request in the chat box.
   - Example prompts:
     - *"Read my latest WhatsApp messages"*
     - *"Send a WhatsApp message to Ali saying hello"*
     - *"Search the web for the latest AI news"*
     - *"Install Google Chrome using Winget"*

## 🛡️ Privacy & Security
This project is designed to run completely locally (except for LLM API calls). Your WhatsApp authentication (`wwebjs_auth`) and API keys (`api_keys.json`) are ignored by Git to ensure your data stays private.

## 📝 License
MIT License

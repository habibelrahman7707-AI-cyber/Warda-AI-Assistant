import customtkinter as ctk
import threading
import sys
import os

# Ensure the root folder is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.voice_engine import VoiceEngine
from agents.crew_manager import execute_user_request

class DesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Warda AI (وردة) - Native Assistant")
        self.geometry("800x600")
        self.minsize(600, 400)
        
        # Appearance
        ctk.set_appearance_mode("System")
        ctk.set_default_color_theme("blue")
        
        self.voice_engine = VoiceEngine()
        self.is_listening = False
        self.context = ""
        self.whatsapp_messages = []
        
        # Start webhook server in background
        self._start_webhook_server()
        
        # Start API Proxy server for auto-swapping keys
        from core.proxy_server import start_proxy_server
        start_proxy_server()
        
        # Grid layout (1 row, 2 columns)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # ==========================================
        # LEFT SIDEBAR (CONTROLS)
        # ==========================================
        self.sidebar_frame = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(3, weight=1) # Spacer to push status to bottom
        
        self.title_label = ctk.CTkLabel(self.sidebar_frame, text="Warda 🌸", font=ctk.CTkFont(size=26, weight="bold"))
        self.title_label.grid(row=0, column=0, padx=20, pady=(30, 20))
        
        import speech_recognition as sr
        raw_mic_list = sr.Microphone.list_microphone_names()
        self.mic_list = ["Default System Microphone"] + raw_mic_list
        self.mic_var = ctk.StringVar(value="Default System Microphone")
        
        # Truncate long microphone names for the UI
        display_mics = [m[:30] + '...' if len(m) > 30 else m for m in self.mic_list]
        self.mic_display_map = dict(zip(display_mics, self.mic_list))
        self.mic_display_var = ctk.StringVar(value=display_mics[0])
        
        self.mic_dropdown = ctk.CTkOptionMenu(self.sidebar_frame, variable=self.mic_display_var, values=display_mics)
        self.mic_dropdown.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        
        self.toggle_btn = ctk.CTkButton(self.sidebar_frame, text="🎙️ Start Recording", command=self.toggle_listening, height=45, font=ctk.CTkFont(size=15, weight="bold"))
        self.toggle_btn.grid(row=2, column=0, padx=20, pady=20, sticky="ew")
        
        self.status_label = ctk.CTkLabel(self.sidebar_frame, text="🟢 Standby", font=ctk.CTkFont(size=14, weight="bold"), text_color="gray")
        self.status_label.grid(row=4, column=0, padx=20, pady=20, sticky="s")
        
        # ==========================================
        # RIGHT MAIN PANEL (CHAT & INPUT)
        # ==========================================
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Chat History
        self.chat_history = ctk.CTkTextbox(self.main_frame, font=ctk.CTkFont(size=15), state="disabled", wrap="word", corner_radius=10)
        self.chat_history.grid(row=0, column=0, columnspan=2, padx=20, pady=(20, 10), sticky="nsew")
        
        # Configure tags for text alignment
        self.chat_history.tag_config("arabic_right", justify="right")
        self.chat_history.tag_config("english_left", justify="left")
        
        # Text Input Area
        self.text_input = ctk.CTkEntry(self.main_frame, placeholder_text="Type a message to Warda...", font=ctk.CTkFont(size=15), height=45)
        self.text_input.grid(row=1, column=0, padx=(20, 10), pady=(0, 20), sticky="ew")
        self.text_input.bind("<Return>", self.send_text)
        
        self.send_btn = ctk.CTkButton(self.main_frame, text="Send 🚀", width=90, height=45, font=ctk.CTkFont(size=15, weight="bold"), command=self.send_text)
        self.send_btn.grid(row=1, column=1, padx=(0, 20), pady=(0, 20), sticky="e")
        
        # Add Right-Click Context Menu for Copy/Paste
        import tkinter as tk
        self.context_menu = tk.Menu(self, tearoff=0, font=("Segoe UI", 11))
        self.context_menu.add_command(label="Copy", command=self.copy_text)
        self.context_menu.add_command(label="Paste", command=self.paste_text)
        
        # Bind right-click to both text areas
        self.chat_history.bind("<Button-3>", self.show_context_menu)
        self.text_input.bind("<Button-3>", self.show_context_menu)
        
        # Add welcome message
        self.log_message("System", "Welcome to Warda AI! You can speak via the microphone or type your message below. 🌸")
        
    def show_context_menu(self, event):
        self.current_widget = event.widget
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            
    def copy_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            try:
                self.current_widget.event_generate("<<Copy>>")
            except Exception:
                pass
                
    def paste_text(self):
        if hasattr(self, 'current_widget') and self.current_widget:
            try:
                self.current_widget.event_generate("<<Paste>>")
            except Exception:
                pass
        
    def log_message(self, role, msg):
        self.chat_history.configure(state="normal")
        
        import re
        is_arabic = len(re.findall(r'[\u0600-\u06FF]', msg)) > 0
        tag = "arabic_right" if is_arabic else "english_left"
        
        if role == "You":
            self.chat_history.insert("end", f"👤 You:\n{msg}\n\n", tag)
        elif role == "Warda":
            self.chat_history.insert("end", f"🌸 Warda:\n{msg}\n\n", tag)
        else:
            self.chat_history.insert("end", f"⚙️ {role}:\n{msg}\n\n", tag)
            
        self.chat_history.see("end")
        self.chat_history.configure(state="disabled")

    def send_text(self, event=None):
        user_text = self.text_input.get().strip()
        if not user_text:
            return
            
        self.text_input.delete(0, "end")
        self.log_message("You", user_text)
        
        # Process request in background thread
        def process():
            self.process_request(user_text)
            self.status_label.configure(text="🟢 Standby", text_color="gray")
            
        threading.Thread(target=process, daemon=True).start()

    def toggle_listening(self):
        if not self.is_listening:
            self.is_listening = True
            self.toggle_btn.configure(text="🛑 Stop Recording", fg_color="#C0392B", hover_color="#922B21")
            self.status_label.configure(text="🔴 Recording...", text_color="#E74C3C")
            
            # Start recording
            selected_display_mic = self.mic_display_var.get()
            selected_mic = self.mic_display_map.get(selected_display_mic, "Default System Microphone")
            
            import speech_recognition as sr
            raw_mics = sr.Microphone.list_microphone_names()
            if selected_mic == "Default System Microphone" or selected_mic not in raw_mics:
                device_index = None
            else:
                device_index = raw_mics.index(selected_mic)
                
            self.voice_engine.start_manual_recording(device_index=device_index)
        else:
            self.is_listening = False
            self.toggle_btn.configure(text="🎙️ Start Recording", fg_color=["#3a7ebf", "#1f538d"], hover_color=["#325882", "#14375e"])
            self.status_label.configure(text="⏳ Transcribing...", text_color="#E67E22")
            self.update_idletasks()
            
            # Stop and transcribe in a separate thread to prevent freezing
            def process():
                text = self.voice_engine.stop_manual_recording_and_transcribe()
                if text:
                    self.log_message("You", text)
                    self.process_request(text)
                else:
                    self.status_label.configure(text="🟢 Standby", text_color="gray")
                    
            threading.Thread(target=process, daemon=True).start()

    def _check_interrupt(self):
        # We want to interrupt the agent's speech ONLY if the user clicks "Start Recording" again.
        # So if is_listening is True, we interrupt.
        return self.is_listening

    def _start_webhook_server(self):
        from flask import Flask, request, jsonify
        import logging
        
        app = Flask(__name__)
        # Disable Flask default logging so it doesn't clutter the terminal
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        
        @app.route('/webhook', methods=['POST'])
        def webhook():
            data = request.json
            if data:
                self.whatsapp_messages.append(data)
                
                # Keep only the latest 20 messages so the AI doesn't get confused by very old notifications
                if len(self.whatsapp_messages) > 20:
                    self.whatsapp_messages.pop(0)
                
                import json, os
                try:
                    save_path = os.path.expanduser('~/Desktop/ai-agent/whatsapp_service/latest_incoming.json')
                    os.makedirs(os.path.dirname(save_path), exist_ok=True)
                    with open(save_path, 'w', encoding='utf-8') as f:
                        json.dump(self.whatsapp_messages, f, ensure_ascii=False, indent=2)
                except Exception:
                    pass
                    
                sender = data.get('author') or data.get('from', 'شخص ما')
                
                # Format the sender's phone number or name for better TTS reading
                if '@c.us' in sender:
                    sender = sender.replace('@c.us', '')
                if '@g.us' in sender:
                    sender = "مجموعة"
                    
                # Just announce the arrival, don't read the content as requested by the user
                announcement = f"لديك رسالة جديدة على واتساب من {sender}."
                
                # Update UI safely
                self.after(0, lambda: self.log_message("System", f"📱 {announcement}"))
                
                # Speak
                def speak_msg():
                    self.voice_engine.speak(announcement, on_interrupt=self._check_interrupt)
                threading.Thread(target=speak_msg, daemon=True).start()
                
            return jsonify({"status": "ok"})
            
        def run_server():
            app.run(host='127.0.0.1', port=3002, use_reloader=False)
            
        threading.Thread(target=run_server, daemon=True).start()

    def process_request(self, user_input):
        self.status_label.configure(text="🧠 Thinking...", text_color="#F1C40F")
        self.update_idletasks()
        
        try:
            # Execute the orchestrator
            response = str(execute_user_request(user_input, self.context))
            
            # Remove markdown symbols so they don't appear in chat and aren't spoken
            import re
            clean_response = re.sub(r'[*#_~`\[\]()-]', '', response)
            clean_response = re.sub(r'\s+', ' ', clean_response).strip()
            
            self.log_message("Warda", clean_response)
            self.context += f"\nUser: {user_input}\nWarda: {clean_response}"
            
            self.status_label.configure(text="🗣️ Speaking...", text_color="#3498DB")
            self.update_idletasks()
            
            # Speak out loud in a separate thread so UI doesn't freeze
            def speak_thread():
                self.voice_engine.speak(clean_response, on_interrupt=self._check_interrupt)
                if self.is_listening:
                    self.status_label.configure(text="🔴 Recording...", text_color="#E74C3C")
                else:
                    self.status_label.configure(text="🟢 Standby", text_color="gray")
                    
            threading.Thread(target=speak_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message("System", f"Error: {e}")
            self.status_label.configure(text="❌ Error", text_color="#E74C3C")
            
if __name__ == "__main__":
    app = DesktopApp()
    app.mainloop()

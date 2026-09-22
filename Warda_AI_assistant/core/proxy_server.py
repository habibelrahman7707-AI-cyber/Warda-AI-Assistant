import threading
from flask import Flask, request, Response
import requests
import logging
import json
import os

app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def get_keys():
    keys_path = os.path.expanduser('~/Desktop/ai-agent/api_keys.json')
    try:
        with open(keys_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('groq_keys', [])
    except Exception:
        # Fallback to the hardcoded key if file doesn't exist
        return ["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"]

@app.route('/v1/chat/completions', methods=['POST'])
def proxy():
    data = request.json
    keys = get_keys()
    
    if not keys:
        return Response(json.dumps({"error": {"message": "No keys configured in api_keys.json"}}), status=500, mimetype='application/json')
        
    last_resp = None
    for key in keys:
        headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        resp = requests.post("https://api.groq.com/openai/v1/chat/completions", json=data, headers=headers)
        last_resp = resp
        
        if resp.status_code == 429:
            print(f"⚠️ [Proxy] API Key {key[:8]}... reached rate limit (429). Switching to the next key...")
            continue # Try next key in the list
            
        # If success (200) or other error (e.g. 400 Bad Request), break and return
        break
        
    return Response(last_resp.content, status=last_resp.status_code, content_type=last_resp.headers.get('content-type'))

def run_server():
    print("🚀 Starting Auto-Swapping API Proxy on port 3003...")
    app.run(host='127.0.0.1', port=3003, use_reloader=False)

def start_proxy_server():
    threading.Thread(target=run_server, daemon=True).start()

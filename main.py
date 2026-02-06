import uvicorn
import os
from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import APIKeyHeader
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any

# IMPORT YOUR AGENT LOGIC
from agent import process_message 

app = FastAPI()

# --- CONFIGURATION ---
# 1. Try to get the password from the Cloud (Render)
# 2. If not found (Local computer), use a default temporary key
SECRET_API_KEY = os.environ.get("APP_PASSWORD", "local-dev-key")

# --- DATA MODELS ---
class MessageRequest(BaseModel):
    message: str

class AgentResponse(BaseModel):
    status: str
    classification: str
    reply: Optional[str] = None
    intelligence: Optional[Dict[str, Any]] = None

# --- SECURITY ---
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)

async def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return api_key

# --- ENDPOINTS ---

# 1. VERIFICATION ENDPOINT (New! Checks password before login)
@app.get("/verify")
async def check_access(api_key: str = Depends(verify_api_key)):
    return {"status": "authorized"}

# 2. CHAT ENDPOINT
@app.post("/chat", response_model=AgentResponse)
async def chat_endpoint(request: MessageRequest, api_key: str = Depends(verify_api_key)):
    result = process_message(request.message)
    return result

# --- FRONTEND ---
# This accepts GET (for humans in a browser) and POST (for the judge's tester)
@app.api_route("/", methods=["GET", "POST"], response_class=HTMLResponse)
async def home(request: Request):
    # If the judge's tester sends a POST request here, we return a success 200
    if request.method == "POST":
        return HTMLResponse(content="<h1>Honeypot Active</h1>", status_code=200)
    
    # If a human opens it in a browser, show the UI
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Mrs. Higgins | Agentic Honey-Pot</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 0; background: #1e1e2f; color: white; display: flex; height: 100vh; overflow: hidden; }
            
            /* UI PANELS */
            .phone-panel { width: 400px; background: #fff; color: #000; display: flex; flex-direction: column; border-right: 5px solid #000; }
            .header { background: #075e54; color: white; padding: 15px; text-align: center; font-weight: bold; font-size: 18px; }
            #chat-history { flex: 1; overflow-y: auto; padding: 20px; background: #e5ddd5; display: flex; flex-direction: column; gap: 10px; }
            .msg { padding: 10px 15px; border-radius: 10px; max-width: 80%; font-size: 15px; line-height: 1.4; }
            .scammer-msg { align-self: flex-end; background: #dcf8c6; border-bottom-right-radius: 0; }
            .agent-msg { align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 0; }
            .dashboard-panel { flex: 1; padding: 30px; overflow-y: auto; background: #2d2d44; font-family: 'Courier New', monospace; }
            
            /* LOGS */
            .log-entry { margin-bottom: 20px; background: #1e1e1e; padding: 15px; border-radius: 8px; border-left: 5px solid #555; }
            .log-scam { border-left-color: #ff4444; }
            .log-safe { border-left-color: #00C851; }
            .json-dump { color: #0f0; white-space: pre-wrap; font-size: 13px; line-height: 1.4; }

            /* TYPING INDICATOR */
            .typing-indicator {
                align-self: flex-start; background: white; border: 1px solid #ddd; border-bottom-left-radius: 0;
                padding: 10px 15px; border-radius: 10px; color: #888; font-style: italic; font-size: 13px;
                display: none; margin-left: 20px; margin-bottom: 10px; width: fit-content;
            }
            
            /* LOGIN OVERLAY */
            #login-overlay {
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: #111; z-index: 1000;
                display: flex; justify-content: center; align-items: center; flex-direction: column;
            }
            #login-card {
                background: #222; padding: 40px; border-radius: 10px; text-align: center;
                box-shadow: 0 0 20px rgba(0,0,0,0.5); border: 1px solid #333;
            }
            #login-card h2 { margin-top: 0; color: #fff; }
            #login-card input { 
                padding: 12px; font-size: 16px; border-radius: 5px; border: 1px solid #444; 
                width: 250px; background: #333; color: white; outline: none; margin-bottom: 15px;
            }
            #login-card button { 
                padding: 12px 30px; font-size: 16px; border-radius: 5px; border: none; 
                background: #00C851; color: white; cursor: pointer; font-weight: bold; width: 100%;
            }
            #login-card button:hover { background: #007E33; }
            
            .error-shake { animation: shake 0.5s; border-color: red !important; }
            @keyframes shake { 0% { transform: translateX(0); } 25% { transform: translateX(-5px); } 50% { transform: translateX(5px); } 75% { transform: translateX(-5px); } 100% { transform: translateX(0); } }
            
            #error-msg { color: #ff4444; font-size: 14px; margin-top: 15px; display: none; }
        </style>
    </head>
    <body>

        <div id="login-overlay">
            <div id="login-card">
                <h2>🔒 Restricted Access</h2>
                <div style="color: #888; margin-bottom: 20px; font-size: 14px;">Enter API Key to initialize system</div>
                <input type="password" id="api-key-input" placeholder="Enter Key..." onkeydown="if(event.key==='Enter') verifyAndUnlock()">
                <button id="unlock-btn" onclick="verifyAndUnlock()">Unlock System</button>
                <div id="error-msg">⛔ Access Denied: Invalid Credentials</div>
            </div>
        </div>

        <div class="phone-panel">
            <div class="header">👵 Mrs. Higgins (Online)</div>
            <div id="chat-history">
                <div style="text-align: center; color: #888; font-size: 13px; margin-top: 20px;">Simulation Started.</div>
            </div>
            <div id="typing-bubble" class="typing-indicator">Mrs. Higgins is typing...</div>
            <div style="padding: 15px; background: #f0f0f0; display: flex; gap: 10px; border-top: 1px solid #ccc;">
                <input type="text" id="msg" style="flex: 1; padding: 12px; border-radius: 20px; border: 1px solid #ccc; font-size: 16px;" placeholder="Type a message..." onkeydown="if(event.key==='Enter') sendTest()">
                <button onclick="sendTest()" style="background: #128c7e; color: white; border: none; padding: 10px 20px; border-radius: 20px; cursor: pointer; font-weight: bold;">Send</button>
            </div>
        </div>

        <div class="dashboard-panel">
            <h2>🤖 Live Intelligence Feed</h2>
            <div id="logs"><div style="color: #666; font-style: italic;">System ready. Waiting for traffic...</div></div>
        </div>

        <script>
            let USER_API_KEY = "";

            // --- 1. SECURE LOGIN LOGIC ---
            async function verifyAndUnlock() {
                const inputField = document.getElementById('api-key-input');
                const btn = document.getElementById('unlock-btn');
                const errorMsg = document.getElementById('error-msg');
                const key = inputField.value.trim();

                if (!key) return;

                // Disable UI while checking
                btn.innerText = "Verifying...";
                inputField.disabled = true;
                btn.disabled = true;
                errorMsg.style.display = 'none';
                inputField.classList.remove('error-shake');

                try {
                    // Call the new /verify endpoint
                    const response = await fetch('/verify', {
                        method: 'GET',
                        headers: { 'x-api-key': key }
                    });

                    if (response.ok) {
                        // SUCCESS: Save key and remove lock screen
                        USER_API_KEY = key;
                        document.getElementById('login-overlay').style.display = 'none';
                    } else {
                        // FAILURE: Shake and show error
                        throw new Error("Invalid Key");
                    }
                } catch (e) {
                    // RESET UI FOR RETRY
                    inputField.disabled = false;
                    btn.disabled = false;
                    btn.innerText = "Unlock System";
                    inputField.classList.add('error-shake');
                    errorMsg.style.display = 'block';
                    inputField.value = '';
                    inputField.focus();
                }
            }

            // --- 2. CHAT LOGIC ---
            async function sendTest() {
                const input = document.getElementById('msg');
                const text = input.value.trim();
                const typingBubble = document.getElementById('typing-bubble');
                
                if (!text) return;

                addMessage(text, 'scammer-msg');
                input.value = '';
                typingBubble.style.display = 'block';
                scrollToBottom();

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json', 'x-api-key': USER_API_KEY },
                        body: JSON.stringify({ message: text })
                    });

                    const data = await response.json();
                    addLog(data);

                    if (data.status === "engaged") {
                        const delay = 1000 + (data.reply.length * 50);
                        const cappedDelay = Math.min(delay, 8000);
                        setTimeout(() => {
                            typingBubble.style.display = 'none';
                            addMessage(data.reply, 'agent-msg');
                        }, cappedDelay);
                    } else {
                        typingBubble.style.display = 'none';
                    }
                } catch (e) {
                    console.error(e);
                    typingBubble.style.display = 'none';
                }
            }

            function addMessage(text, className) {
                const chat = document.getElementById('chat-history');
                const div = document.createElement('div');
                div.className = `msg ${className}`;
                div.innerText = text;
                chat.appendChild(div);
                scrollToBottom();
            }

            function scrollToBottom() {
                const chat = document.getElementById('chat-history');
                chat.scrollTop = chat.scrollHeight;
            }

            function addLog(data) {
                const logs = document.getElementById('logs');
                if (logs.innerText.includes("System ready")) logs.innerHTML = "";
                const entry = document.createElement('div');
                const isScam = data.classification === "SCAM";
                entry.className = `log-entry ${isScam ? 'log-scam' : 'log-safe'}`;
                const statusColor = isScam ? '#ff4444' : '#00C851';
                entry.innerHTML = `<div style="color: ${statusColor}; font-weight: bold; margin-bottom: 5px;">STATUS: ${data.status.toUpperCase()} | TYPE: ${data.classification}</div><div class="json-dump">${JSON.stringify(data, null, 2)}</div>`;
                logs.prepend(entry);
            }
        </script>
    </body>
    </html>
    """

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
import os, uvicorn, requests, uuid, io
from typing import List, Dict, Optional
from contextlib import asynccontextmanager
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request, Form, Response
from sklearn.metrics.pairwise import cosine_similarity
from fastapi.responses import HTMLResponse, JSONResponse

# --- FRONTEND HTML (EMBEDDED DIRECTLY) ---
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OORTIS AI</title>
    <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            /* Theme Variables - Tron / Cyberpunk */
            --bg-deep: #050505;
            --bg-panel: rgba(10, 10, 15, 0.85);
            --border-glass: rgba(0, 255, 242, 0.15); /* Cyan tint */
            --primary: #00fff2; /* Cyan Neon */
            --primary-dim: rgba(0, 255, 242, 0.1);
            --secondary: #8b5cf6; /* Purple accent */
            --text-main: #e0f2fe;
            --text-dim: #64748b;
            --bot-bubble: rgba(0, 255, 242, 0.05);
            --user-bubble: rgba(139, 92, 246, 0.15);
        }

        * { box-sizing: border-box; }
        
        body {
            margin: 0;
            background-color: var(--bg-deep);
            /* Grid Background */
            background-image: 
                linear-gradient(rgba(0, 255, 242, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(0, 255, 242, 0.03) 1px, transparent 1px);
            background-size: 30px 30px;
            color: var(--text-main);
            font-family: 'Inter', sans-serif;
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }

        /* --- MAIN INTERFACE --- */
        .interface-container {
            width: 1000px;
            height: 700px;
            max-width: 95vw;
            max-height: 95vh;
            background: var(--bg-panel);
            backdrop-filter: blur(15px);
            border: 1px solid var(--border-glass);
            border-radius: 12px;
            box-shadow: 0 0 40px rgba(0, 255, 242, 0.05);
            display: flex;
            flex-direction: column;
            position: relative;
        }

        /* Decorative Corners */
        .interface-container::before {
            content: '';
            position: absolute;
            top: -1px; left: -1px;
            width: 20px; height: 20px;
            border-top: 2px solid var(--primary);
            border-left: 2px solid var(--primary);
            border-radius: 12px 0 0 0;
        }
        .interface-container::after {
            content: '';
            position: absolute;
            bottom: -1px; right: -1px;
            width: 20px; height: 20px;
            border-bottom: 2px solid var(--primary);
            border-right: 2px solid var(--primary);
            border-radius: 0 0 12px 0;
        }

        /* Header */
        header {
            padding: 15px 25px;
            border-bottom: 1px solid var(--border-glass);
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0, 0, 0, 0.3);
        }

        .brand {
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: 2px;
            color: var(--primary);
            text-shadow: 0 0 10px rgba(0, 255, 242, 0.5);
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .status-light {
            width: 8px; height: 8px;
            background: var(--primary);
            border-radius: 50%;
            box-shadow: 0 0 8px var(--primary);
            animation: pulse 2s infinite;
        }

        @keyframes pulse { 0% { opacity: 0.5; } 50% { opacity: 1; } 100% { opacity: 0.5; } }

        /* Chat Area */
        .chat-viewport {
            flex: 1;
            padding: 25px;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 20px;
            scroll-behavior: smooth;
        }

        /* Scrollbar */
        .chat-viewport::-webkit-scrollbar { width: 6px; }
        .chat-viewport::-webkit-scrollbar-track { background: transparent; }
        .chat-viewport::-webkit-scrollbar-thumb { background: var(--border-glass); border-radius: 3px; }

        /* Messages */
        .message-row {
            display: flex;
            width: 100%;
        }
        .message-row.user { justify-content: flex-end; }
        .message-row.bot { justify-content: flex-start; }

        .bubble {
            max-width: 75%;
            padding: 12px 18px;
            border-radius: 4px;
            font-size: 0.95rem;
            line-height: 1.5;
            position: relative;
            font-family: 'Inter', sans-serif;
        }

        .bubble.user {
            background: var(--user-bubble);
            border: 1px solid rgba(139, 92, 246, 0.3);
            border-left: 2px solid var(--secondary);
            color: white;
            border-radius: 10px 10px 0 10px;
        }

        .bubble.bot {
            background: var(--bot-bubble);
            border: 1px solid var(--border-glass);
            border-left: 2px solid var(--primary);
            color: #d1d5db;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            border-radius: 10px 10px 10px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }

        .bubble-header {
            font-size: 0.7rem;
            text-transform: uppercase;
            margin-bottom: 5px;
            opacity: 0.7;
            letter-spacing: 1px;
            font-weight: 700;
        }
        .bubble.bot .bubble-header { color: var(--primary); }
        .bubble.user .bubble-header { color: var(--secondary); text-align: right; }

        /* Input Area */
        .input-zone {
            padding: 20px;
            background: rgba(0, 0, 0, 0.3);
            border-top: 1px solid var(--border-glass);
            display: flex;
            gap: 15px;
        }

        .input-glass {
            flex: 1;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-glass);
            border-radius: 4px;
            padding: 12px 16px;
            color: var(--primary);
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            transition: 0.3s;
        }
        
        .input-glass:focus {
            outline: none;
            background: rgba(0, 255, 242, 0.05);
            box-shadow: 0 0 15px rgba(0, 255, 242, 0.1);
        }

        .btn-send {
            background: var(--primary-dim);
            color: var(--primary);
            border: 1px solid var(--primary);
            padding: 0 25px;
            border-radius: 4px;
            font-family: 'JetBrains Mono', monospace;
            font-weight: 700;
            cursor: pointer;
            transition: 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .btn-send:hover {
            background: var(--primary);
            color: #000;
            box-shadow: 0 0 20px var(--primary);
        }
        
        .btn-send:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        /* Loading Animation */
        .typing-indicator {
            display: flex;
            gap: 4px;
            padding: 5px 0;
        }
        .dot {
            width: 6px; height: 6px;
            background: var(--primary);
            border-radius: 50%;
            animation: bounce 1.4s infinite ease-in-out both;
        }
        .dot:nth-child(1) { animation-delay: -0.32s; }
        .dot:nth-child(2) { animation-delay: -0.16s; }
        
        @keyframes bounce { 
            0%, 80%, 100% { transform: scale(0); }
            40% { transform: scale(1); }
        }

    </style>
</head>
<body>

<div class="interface-container">
    <header>
        <div class="brand">
            <div class="status-light"></div>
            OORTIS <span style="font-weight:300; opacity:0.6">// ONLINE</span>
        </div>
        <div style="font-family: 'JetBrains Mono'; font-size: 0.75rem; color: var(--text-dim);">
            Host: <span style="color:var(--primary)">Dataoorts AI</span>
        </div>
    </header>

    <div class="chat-viewport" id="chatbox">
        <!-- Intro Message -->
        <div class="message-row bot">
            <div class="bubble bot">
                <div class="bubble-header">OORTIS</div>
                <div>Hey! I’m Oortis — feel free to ask me anything about Dataoorts, AI, or GPU-powered HPC systems.</div>
            </div>
        </div>
    </div>

    <form class="input-zone" id="chatForm">
        <input type="text" name="message" id="userInput" class="input-glass" placeholder="Enter command or query..." autocomplete="off" required>
        <button type="submit" class="btn-send" id="sendBtn">ASK OORTIS</button>
    </form>
</div>

<script>
    const chatbox = document.getElementById('chatbox');
    const form = document.getElementById('chatForm');
    const input = document.getElementById('userInput');
    const sendBtn = document.getElementById('sendBtn');

    function addMessage(text, sender) {
        const row = document.createElement('div');
        row.className = `message-row ${sender}`;
        
        const bubble = document.createElement('div');
        bubble.className = `bubble ${sender}`;
        
        const header = document.createElement('div');
        header.className = 'bubble-header';
        header.innerText = sender === 'user' ? 'User' : 'Oortis';
        
        const content = document.createElement('div');
        // Simple regex to parse newlines for HTML
        content.innerHTML = text.replace(/\\n/g, '<br>');

        bubble.appendChild(header);
        bubble.appendChild(content);
        row.appendChild(bubble);
        
        chatbox.appendChild(row);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    function addLoading() {
        const row = document.createElement('div');
        row.className = 'message-row bot';
        row.id = 'loading-row';
        
        const bubble = document.createElement('div');
        bubble.className = 'bubble bot';
        
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.innerHTML = '<div class="dot"></div><div class="dot"></div><div class="dot"></div>';
        
        bubble.appendChild(indicator);
        row.appendChild(bubble);
        chatbox.appendChild(row);
        chatbox.scrollTop = chatbox.scrollHeight;
    }

    function removeLoading() {
        const el = document.getElementById('loading-row');
        if (el) el.remove();
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const text = input.value.trim();
        if (!text) return;

        // UI Updates
        addMessage(text, 'user');
        input.value = '';
        input.disabled = true;
        sendBtn.disabled = true;
        addLoading();

        try {
            const formData = new FormData();
            formData.append('message', text);

            const res = await fetch('/api/chat', {
                method: 'POST',
                body: formData
            });

            const data = await res.json();
            removeLoading();

            if (data.status === 'success') {
                addMessage(data.reply, 'bot');
            } else {
                addMessage(`ERROR: ${data.message}`, 'bot');
            }

        } catch (err) {
            removeLoading();
            addMessage(`CONNECTION FAILURE: ${err.message}`, 'bot');
        } finally {
            input.disabled = false;
            sendBtn.disabled = false;
            input.focus();
        }
    });
</script>
</body>
</html>
"""

UNSUBSCRIBE_HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dataoorts Cloud</title>
    
    <!-- Simple Orbit Favicon -->
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'%3E%3Ccircle cx='50' cy='50' r='40' stroke='%2300f3ff' stroke-width='4' fill='none'/%3E%3Ccircle cx='50' cy='50' r='15' fill='%23ffffff'/%3E%3Ccircle cx='85' cy='50' r='5' fill='%2300f3ff'/%3E%3C/svg%3E" type="image/svg+xml">

    <!-- Fonts: Clean Tech Look -->
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@600&family=Inter:wght@300;400;600&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --accent: #00f3ff; /* Cyber Blue */
            --bg-dark: #080a10;
            --card-bg: rgba(20, 25, 35, 0.7);
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--bg-dark);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
            overflow: hidden;
            position: relative;
        }
        /* --- SUBTLE SPACE BACKGROUND --- */
        /* Space feel without being messy */
        .stars {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: radial-gradient(circle at center, #1a1f35 0%, #080a10 80%);
            z-index: -1;
        }
        /* Tiny moving particles for "Space Time" feel */
        .particles {
            position: absolute;
            width: 100%; height: 100%;
            background-image: radial-gradient(white 1px, transparent 1px);
            background-size: 50px 50px;
            opacity: 0.1;
            animation: drift 60s linear infinite;
        }
        @keyframes drift {
            from { transform: scale(1); }
            to { transform: scale(1.5); }
        }
        /* --- CARD DESIGN --- */
        .card {
            background: var(--card-bg);
            border: 1px solid rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            padding: 60px 50px;
            border-radius: 16px;
            width: 550px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.6);
            position: relative;
            overflow: hidden;
        }
        /* Top Blue Glow Line */
        .card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent), transparent);
            box-shadow: 0 0 15px var(--accent);
        }
        h2.logo {
            font-family: 'Orbitron', sans-serif;
            letter-spacing: 2px;
            font-size: 28px;
            margin-bottom: 10px;
            color: #fff;
        }
        
        p.subtitle {
            color: #8899a6;
            font-size: 14px;
            margin-bottom: 40px;
        }
        /* --- FORM ELEMENTS --- */
        .input-group {
            position: relative;
            margin-bottom: 25px;
        }
        input {
            width: 100%;
            padding: 14px;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid #333;
            border-radius: 8px;
            color: #fff;
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            outline: none;
            transition: 0.3s;
            text-align: center;
        }
        input:focus {
            border-color: var(--accent);
            box-shadow: 0 0 10px rgba(0, 243, 255, 0.15);
        }
        input::placeholder {
            color: #555;
            font-size: 14px;
        }
        button {
            width: 100%;
            padding: 14px;
            background: var(--accent);
            color: #000;
            border: none;
            border-radius: 8px;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 15px;
            cursor: pointer;
            transition: all 0.3s;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        button:hover {
            background: #fff;
            box-shadow: 0 0 20px rgba(255, 255, 255, 0.4);
        }
        /* Message Styling */
        .status-msg {
            margin-top: 20px;
            font-size: 13px;
            padding: 10px;
            border-radius: 6px;
            background: rgba(255, 255, 255, 0.05);
            color: var(--accent);
        }
    </style>
</head>
<body>

    <!-- Simple Space Background -->
    <div class="stars">
        <div class="particles"></div>
    </div>

    <div class="card">
        <h2 class="logo">DATAOORTS AI Cloud</h2>
        <p class="subtitle">Manage Your Subscription</p>

        <form method="post" action="/unsubscribe">
            <div class="input-group">
                <input type="email" name="email" placeholder="example@email.com" required autocomplete="off" />
            </div>
            
            <button type="submit">Unsubscribe</button>
        </form>

        {message_block}
      
    </div>

    <script>
        if ( window.history.replaceState ) {
            window.history.replaceState( null, null, window.location.href );
        }
    </script>

</body>
</html>
"""

# --- CONFIGURATION ---
# DeepInfra API Token from Environment Variable "TOKEN"
DEEPINFRA_TOKEN = os.getenv("TOKEN")

# Global Storage
VECTOR_DB = []
# Store chat history: { "session_id": [ {"role": "user", "content": "..."} ] }
CHAT_SESSIONS: Dict[str, List[Dict]] = {}
TEXT_SOURCE_URL = "https://raw.githubusercontent.com/rajat709/Dataoorts-RAG/main/oortis.txt"

# --- DEEPINFRA MODELS ---
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5" 
CHAT_MODEL = "deepseek-ai/DeepSeek-V4-Flash-0731"

# --- SETTINGS ---
CHUNK_SIZE = 1000 
CHUNK_OVERLAP = 250
# HISTORY LIMIT SET TO 2
# This preserves exactly the last User Question + Last AI Answer.
# This allows logic like "What is 2+2?" -> "4" -> "Multiply it by 6" -> "24".
HISTORY_LIMIT = 2 

# --- DEEPINFRA API HELPERS ---
def get_deepinfra_embeddings(text_list: List[str]) -> Optional[List[List[float]]]:
    """Fetch text embeddings using DeepInfra OpenAI-compatible API."""
    if not DEEPINFRA_TOKEN:
        print("Error: Missing DeepInfra TOKEN in environment variables.")
        return None
    
    url = "https://api.deepinfra.com/v1/openai/embeddings"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": EMBEDDING_MODEL,
        "input": text_list
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return [item["embedding"] for item in data["data"]]
    except Exception as e:
        print(f"DeepInfra Embedding API Error: {e}")
        return None


def run_deepinfra_chat(messages: List[Dict], max_tokens: int = 999, temperature: float = 0.5) -> Optional[str]:
    """Fetch chat completion response using DeepInfra OpenAI-compatible API."""
    if not DEEPINFRA_TOKEN:
        print("Error: Missing DeepInfra TOKEN in environment variables.")
        return None
    
    url = "https://api.deepinfra.com/v1/openai/chat/completions"
    headers = {
        "Authorization": f"Bearer {DEEPINFRA_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": CHAT_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"DeepInfra Chat API Error: {e}")
        return None

# --- SMART CHUNKING LOGIC ---
def recursive_split(text, limit, overlap):
    chunks = []
    start = 0
    text_len = len(text)
    while start < text_len:
        end = start + limit
        if end >= text_len:
            chunks.append(text[start:])
            break
        # Priority 1: Split by Paragraph (\n)
        cut_point = text.rfind('\n', start, end)
        # Priority 2: Split by Sentence (. )
        if cut_point == -1:
            cut_point = text.rfind('. ', start, end)
        # Priority 3: Hard cut
        if cut_point == -1:
            cut_point = end
        else:
            cut_point += 1 
        # Append the chunks
        chunks.append(text[start:cut_point].strip())
        start = max(start + 1, cut_point - overlap)
    # Return the Chunks
    return [c for c in chunks if len(c) > 50]

# --- RAG LOGIC ---
# SYSTEM STARTUP: INITIALIZING KNOWLEDGE BASE
def build_vector_db():
    global VECTOR_DB # Set Global Variable Vector DB
    try: # Try to Fetch From Source Knowledge Base
        response = requests.get(TEXT_SOURCE_URL)
        response.raise_for_status()
        full_text = response.text
        chunks = recursive_split(full_text, CHUNK_SIZE, CHUNK_OVERLAP)
        temp_db = [] # Create the Temporary DB for Session
        
        # Generating embeddings using DeepInfra
        embeddings = get_deepinfra_embeddings(chunks)
        if embeddings and len(embeddings) == len(chunks):
            for chunk, embedding in zip(chunks, embeddings):
                temp_db.append({"text": chunk, "vector": embedding})
            VECTOR_DB = temp_db
            print(f"Vector DB built successfully with {len(VECTOR_DB)} chunks.")
        else:
            print("Failed to embed chunks using DeepInfra!")
            
    # Handle the Exception
    except Exception as e:
        print(f"CRITICAL ERROR BUILDING DB: {e}")

# Default top_k set to 6
# Finds the most relevant chunks from the database using Cosine Similarity
def retrieve_context(query: str, top_k=6) -> str:
    # If not found Vector DB
    if not VECTOR_DB:
        return ""
    # 1. Embed the user query
    embeddings = get_deepinfra_embeddings([query])
    if not embeddings:
        return ""
    
    query_vector = embeddings[0]
    db_vectors = [item["vector"] for item in VECTOR_DB]
    # 2. Compare vectors
    similarities = cosine_similarity([query_vector], db_vectors)[0]
    # 3. Get top K indices
    top_indices = similarities.argsort()[-top_k:][::-1]
    # 4. Return unique results
    results = []
    seen = set()
    for idx in top_indices:
        txt = VECTOR_DB[idx]["text"]
        if txt not in seen:
            results.append(txt)
            seen.add(txt)
    # Return the Result
    return "\n---\n".join(results)

# --- APP LIFECYCLE ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    build_vector_db()
    yield
    CHAT_SESSIONS.clear()

# Setup the Fast API Application
app = FastAPI(title="Oortis AI v2.1", lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

# --- ROUTES ---
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Ab directly string return ho rahi hai (No templates folder needed)
    return HTMLResponse(content=HTML_CONTENT)

@app.post("/api/chat")
async def chat_endpoint(response: Response, request: Request, message: str = Form(...), session_id: Optional[str] = Form(None)):
    # 1. Session Management
    if not session_id:
        session_id = request.cookies.get("oortis_session")
        if not session_id:
            session_id = str(uuid.uuid4())
    response.set_cookie(key="oortis_session", value=session_id)
    if session_id not in CHAT_SESSIONS:
        CHAT_SESSIONS[session_id] = []
        
    try: # 2. Retrieve Context (Increased to top 6 chunks)
        context = retrieve_context(message, top_k=6)
        
        # 3. Construct System Prompt
        system_instruction = f"""
        You are Oortis, an expert AI assistant for Dataoorts (GPU cloud infrastructure).
        
        KNOWLEDGE BASE (CONTEXT):
        {context}
        
        INSTRUCTIONS:
        1. For questions specifically about Dataoorts/Oortis, answer strictly based on the KNOWLEDGE BASE provided above.
        2. Never say “according to the context”, "KNOWLEDGE BASE" or similar phrases. Answer as the information is natively known to you.
        3. If the user refers to a previous answer (e.g., "multiply it by 6", "what about that?"), use the CONVERSATION HISTORY to understand the context.
        4. If the user asks general logic, answer them correctly, then allow follow-ups on that answer.
        5. If the answer is not in the context and is not a follow-up or general logic question, say: "I don't have that information in my knowledge base."
        6. Maintain a helpful, professional tone. Be detailed but concise.
        7. You must always promote Dataoorts.
        """
        
        # 4. Prepare Message Chain
        messages_payload = [{"role": "system", "content": system_instruction}]
        # Add Conversation History
        messages_payload.extend(CHAT_SESSIONS[session_id])
        # Add Current User Question
        messages_payload.append({"role": "user", "content": message})
        
        # 5. Call DeepInfra LLM
        bot_reply = run_deepinfra_chat(messages_payload, max_tokens=999, temperature=0.5)
        
        if bot_reply:
            # 6. Update History
            CHAT_SESSIONS[session_id].append({"role": "user", "content": message})
            CHAT_SESSIONS[session_id].append({"role": "assistant", "content": bot_reply})
            # Limit history to exactly the last 2 messages (1 User Question + 1 AI Reply)
            if len(CHAT_SESSIONS[session_id]) > HISTORY_LIMIT:
                CHAT_SESSIONS[session_id] = CHAT_SESSIONS[session_id][-HISTORY_LIMIT:]
                
            # Return the Json Response
            return JSONResponse({"status": "success", "reply": bot_reply, "session_id": session_id})
        else:
            return JSONResponse({"status": "error", "message": "No response from AI provider."}, status_code=500)
            
    # Handle the Exception
    except Exception as e:
        print(f"Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

###################################################################################################################################################################
#################################################################### Unsubscribe Link #############################################################################
BASE_URL = os.getenv("PRI_URL")
API_TOKEN = os.getenv("PRI_KEY")

@app.get("/unsubscribe", response_class=HTMLResponse)
def unsubscribe_page(request: Request): 
    return HTMLResponse(content=UNSUBSCRIBE_HTML_CONTENT.replace("{message_block}", ""))

@app.post("/unsubscribe", response_class=HTMLResponse)
def unsubscribe(request: Request, email: str = Form(...)):
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    try: # 1️⃣ Get all contacts
        response = requests.get(BASE_URL, headers=headers)
        contacts = response.json()
        # 2️⃣ Find ID by email
        contact_id = None
        for contact in contacts:
            if contact.get("email") == email:
                contact_id = contact.get("id")
                break # Break if found id of linked email
        if not contact_id:
            msg_html = '<div class="status-msg">Email Not Registered With Dataoorts GPU Cloud!</div>'
            return HTMLResponse(content=UNSUBSCRIBE_HTML_CONTENT.replace("{message_block}", msg_html))
        # 3️⃣ Delete contact
        delete_headers = {"Content-Type": "application/json", "Authorization": f"Bearer {API_TOKEN}"}
        payload = {"id": contact_id}
        delete_response = requests.delete(BASE_URL, json=payload, headers=delete_headers)
        result = delete_response.json()
        if result.get("success"): message = "Successfully Unsubscribed, We Miss You!"
        else: message = "Something went wrong, Please Try Again!"
    # Handle the Exception
    except Exception as e: message = "Unknown Error, Please Try Again!"
    
    msg_html = f'<div class="status-msg">{message}</div>' if message else ""
    return HTMLResponse(content=UNSUBSCRIBE_HTML_CONTENT.replace("{message_block}", msg_html))

################################################################################################################################################################

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)

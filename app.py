from __future__ import annotations

import os
import time
import logging
from typing import Dict, List, Literal
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from openai import OpenAI

# -----------------------
# Logging (simple + useful)
# -----------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("chatbot")

# -----------------------
# Config
# -----------------------
load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("MODEL", "gpt-4o-mini")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing. Put it in a .env file.")

client = OpenAI(api_key=API_KEY)
app = FastAPI(title="AI Chatbot (FastAPI + UI + History)")

Role = Literal["system", "user", "assistant"]

# In-memory store: session_id -> messages
# NOTE: Resets when server restarts. In production, use Redis/DB.
histories: Dict[str, List[dict]] = {}

SYSTEM_PROMPT = (
    "You are a helpful assistant.\n"
    "Write in clear, friendly.\n"
    "IMPORTANT formatting:\n"
    "- Use plain text only (no Markdown symbols like ###, **, backticks).\n"
    "- Use short paragraphs.\n"
    "- Use bullet points with '-' and put each bullet on a new line.\n"
    "- Add a blank line between sections.\n"
    "- Keep it practical and not too long.\n"
)


# -----------------------
# Schemas
# -----------------------
class ChatRequest(BaseModel):
    session_id: str = Field(default="default", description="Client session id")
    message: str = Field(..., min_length=1, description="User message")
    max_history: int = Field(default=10, ge=0, le=50, description="How many past messages to keep")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    used_model: str
    history_size: int
    latency_ms: int


class ResetRequest(BaseModel):
    session_id: str = Field(default="default")


# -----------------------
# UI
# -----------------------
@app.get("/", response_class=HTMLResponse)
def home():
    html = f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1"/>
  <title>AI Chatbot</title>
  <style>
    body {{ font-family: Arial, sans-serif; background:#0b0f14; color:#e8eef7; margin:0; }}
    .wrap {{ max-width: 900px; margin: 0 auto; padding: 24px; }}
    .card {{ background:#121826; border:1px solid #223047; border-radius:16px; padding:16px; }}
    .row {{ display:flex; gap:12px; margin-top:12px; }}
    input, button {{ border-radius:21px; border:1px solid #223047; padding:12px; font-size:14px; }}
    input {{ flex:1; background:#0f1522; color:#e8eef7; }}
    button {{ background:#2b6cff; color:white; cursor:pointer; }}
    button.secondary {{ background:#1a2333; }}
    button:disabled {{ opacity:0.6; cursor:not-allowed; }}
    .chat {{ height: 420px; overflow:auto; padding: 12px; border-radius: 21px; background:#0f1522; border:1px solid #223047; }}
    .msg {{ margin: 10px 0; line-height:1.4; white-space: pre-wrap; }}
    .me b {{ color:#7dd3fc; }}
    .ai b {{ color:#a7f3d0; }}
    .meta {{ opacity:0.7; font-size:12px; margin-top:10px; }}
    .top {{ display:flex; justify-content:space-between; align-items:center; gap:12px; }}
    .pill {{ font-size:12px; padding:6px 10px; border:1px solid #223047; border-radius:999px; background:#0f1522; }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="top">
      <h2 style="margin:0;">AI Chatbot</h2>
      <div class="pill">Model: <span id="model">{MODEL}</span></div>
    </div>

    <div class="card" style="margin-top:14px;">
      <div style="display:flex; gap:10px; flex-wrap:wrap;">
        <label class="pill">Session ID:
          <input id="session" value="vahag-session" style="margin-left:8px; width:220px;">
        </label>
        <label class="pill">Max history:
          <input id="maxHistory" type="number" min="0" max="50" value="10" style="margin-left:8px; width:80px;">
        </label>
        <a class="pill" href="/docs" target="_blank" style="text-decoration:none;color:#e8eef7;padding-top: 19px;">API Docs</a>
        <a class="pill" href="/health" target="_blank" style="text-decoration:none;color:#e8eef7;padding-top: 19px;">Health</a>
      </div>

      <div id="chat" class="chat" style="margin-top:12px;"></div>

      <div class="row">
        <input id="text" placeholder="Type a message... (Enter to send)" />
        <button id="send">Send</button>
        <button id="reset" class="secondary">Reset</button>
      </div>

      <div id="meta" class="meta"></div>
    </div>
  </div>

<script>
const chatEl = document.getElementById("chat");
const textEl = document.getElementById("text");
const sendBtn = document.getElementById("send");
const resetBtn = document.getElementById("reset");
const metaEl = document.getElementById("meta");
const sessionEl = document.getElementById("session");
const maxHistoryEl = document.getElementById("maxHistory");

function addMsg(who, text) {{
  const div = document.createElement("div");
  div.className = "msg " + (who === "You" ? "me" : "ai");
  div.innerHTML = "<b>" + who + ":</b> " + escapeHtml(text);
  chatEl.appendChild(div);
  chatEl.scrollTop = chatEl.scrollHeight;
}}

function escapeHtml(str) {{
  return str.replace(/[&<>"']/g, (m) => ({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#039;"}})[m]);
}}

async function send() {{
  const msg = textEl.value.trim();
  if (!msg) return;
  textEl.value = "";
  addMsg("You", msg);

  sendBtn.disabled = true;
  metaEl.textContent = "Thinking...";

  try {{
    const res = await fetch("/chat", {{
      method: "POST",
      headers: {{ "Content-Type": "application/json" }},
      body: JSON.stringify({{
        session_id: sessionEl.value.trim() || "default",
        message: msg,
        max_history: Number(maxHistoryEl.value || 10)
      }})
    }});

    const data = await res.json();
    if (!res.ok) throw new Error(data?.detail || "Request failed");

    addMsg("AI", data.reply);
    metaEl.textContent = `History size: ${{data.history_size}} · Model: ${{data.used_model}} · Latency: ${{data.latency_ms}} ms`;
  }} catch (e) {{
    addMsg("AI", "Error: " + e.message);
    metaEl.textContent = "";
  }} finally {{
    sendBtn.disabled = false;
    textEl.focus();
  }}
}}

async function reset() {{
  const session = sessionEl.value.trim() || "default";
  const res = await fetch("/reset", {{
    method: "POST",
    headers: {{ "Content-Type": "application/json" }},
    body: JSON.stringify({{ session_id: session }})
  }});
  const data = await res.json();
  chatEl.innerHTML = "";
  metaEl.textContent = data.message;
  textEl.focus();
}}

sendBtn.addEventListener("click", send);
resetBtn.addEventListener("click", reset);
textEl.addEventListener("keydown", (e) => {{
  if (e.key === "Enter") send();
}});

addMsg("AI", "Hi! Type a message and press Enter. (Session keeps chat history.)");
</script>
</body>
</html>
"""
    return HTMLResponse(html)


# -----------------------
# Helpers
# -----------------------
def get_history(session_id: str) -> List[dict]:
    if session_id not in histories:
        histories[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]
    return histories[session_id]


def map_openai_error_to_http(message: str) -> tuple[int, str]:
    """
    Convert common OpenAI errors into clearer HTTP responses for UI/API.
    """
    msg = message

    # Quota / credits / rate limit cases often surface as 429
    if "insufficient_quota" in msg or "Error code: 429" in msg:
        return 429, "Quota exceeded (no credits). Please check billing/usage on your OpenAI account."

    # Invalid API key is typically 401
    if "Error code: 401" in msg or "invalid_api_key" in msg:
        return 401, "Invalid API key. Please check OPENAI_API_KEY in your .env file."

    # Fallback
    return 400, f"OpenAI API error: {msg}"


# -----------------------
# Endpoints
# -----------------------
@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    start = time.time()
    history = get_history(req.session_id)

    logger.info("Request session=%s max_history=%d msg_len=%d", req.session_id, req.max_history, len(req.message))

    # Add user message
    history.append({"role": "user", "content": req.message})

    # Keep only last N user+assistant messages + system prompt
    if req.max_history == 0:
        # Keep only system + current user message
        history[:] = [history[0], {"role": "user", "content": req.message}]
    else:
        system_msg = history[0]
        tail = history[1:]
        tail = tail[-(req.max_history * 2):]  # approx last N turns
        history[:] = [system_msg] + tail

    # Call model
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=history,
        )
        reply = resp.choices[0].message.content or ""
    except Exception as e:
        status, detail = map_openai_error_to_http(str(e))
        logger.error("OpenAI error session=%s status=%d detail=%s", req.session_id, status, detail)
        return JSONResponse(status_code=status, content={"detail": detail})

    # Add assistant message to history
    history.append({"role": "assistant", "content": reply})

    latency_ms = int((time.time() - start) * 1000)
    logger.info("Reply session=%s history_size=%d latency_ms=%d", req.session_id, len(history) - 1, latency_ms)

    return ChatResponse(
        session_id=req.session_id,
        reply=reply,
        used_model=MODEL,
        history_size=len(history) - 1,  # excluding system
        latency_ms=latency_ms,
    )


@app.post("/reset")
def reset(req: ResetRequest):
    histories.pop(req.session_id, None)
    logger.info("Reset session=%s", req.session_id)
    return {"message": f"History cleared for session '{req.session_id}'."}
"""Nudgely backend: the web chat for judges (/api/chat) and the WhatsApp webhook (/whatsapp).

Run locally:   uvicorn api.main:app --port 8000 --reload
Contract:      docs/V1_ARCHITECTURE.md

Environment (.env locally, host settings in production):
  LLM_PROVIDER, LLM_API_KEY, LLM_MODEL         the AI (see nudgely/llm.py)
  WA_TOKEN, WA_PHONE_NUMBER_ID, WA_VERIFY_TOKEN, WA_APP_SECRET, WA_GRAPH_VERSION   WhatsApp
  SUPABASE_URL, SUPABASE_SERVICE_KEY           optional: mirror turns to Supabase for the dashboard
  ALLOWED_ORIGINS                               comma-separated, e.g. https://nudgely.vercel.app
"""

import html
import io
import os
import re
import sys
import threading
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request, Response  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import HTMLResponse, RedirectResponse  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from nudgely import bot, supabase_sync  # noqa: E402
from nudgely.whatsapp import (WhatsApp, WhatsAppError, parse_webhook, valid_signature,  # noqa: E402
                              verify_subscription)

app = FastAPI(title="Nudgely API", version="1.0")
origins = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                   allow_headers=["Content-Type"])

# ---- web chat --------------------------------------------------------------------------------

MIN_GAP_S = 2.0        # at most one message every 2 seconds per session
MAX_PER_SESSION = 30   # a judge can't run up the AI bill
_sessions = {}         # session_id -> (last_time, count)
_session_lock = threading.Lock()
SESSION_RE = re.compile(r"^[A-Za-z0-9-]{8,64}$")


class ChatIn(BaseModel):
    session_id: str = Field(..., description="random id the browser keeps for this visitor")
    name: str = Field("", max_length=40)
    text: str = Field(..., min_length=1, max_length=500)


class Tag(BaseModel):
    type: str
    value: str
    evidence: str


class ChatOut(BaseModel):
    reply: str | None
    handover: bool
    tags: list[Tag]
    customer_id: str


LIMIT_MSG = "This demo chat has reached its message limit. Thanks for trying Nudgely!"


def _rate_limit(session_id):
    """Best-effort gap per instance; the hard cap is counted in the store (works across instances)."""
    with _session_lock:
        last, count = _sessions.get(session_id, (0.0, 0))
        now = time.monotonic()
        if count >= MAX_PER_SESSION:
            raise HTTPException(429, LIMIT_MSG)
        if now - last < MIN_GAP_S:
            raise HTTPException(429, "Slow down a little: one message every 2 seconds.")
        _sessions[session_id] = (now, count + 1)


@app.post("/api/chat", response_model=ChatOut)
def chat(body: ChatIn):
    if not SESSION_RE.match(body.session_id):
        raise HTTPException(400, "session_id must be 8-64 letters, digits or dashes (a UUID works)")
    _rate_limit(body.session_id)
    name = re.sub(r"[^\w .'-]", "", body.name).strip()[:40]
    out = bot.handle(f"web:{body.session_id}", name, body.text.strip(), prefix="WEB",
                     max_messages=MAX_PER_SESSION)
    if out["limited"]:
        raise HTTPException(429, LIMIT_MSG)
    return ChatOut(reply=out["reply"], handover=out["handover"], customer_id=out["customer_id"],
                   tags=[Tag(**{k: str(t.get(k) or "") for k in ("type", "value", "evidence")})
                         for t in out["new_tags"]])


# ---- WhatsApp webhook --------------------------------------------------------------------------

def _wa():
    try:
        return WhatsApp.from_env()
    except ValueError:
        return None


def _whatsapp_turn(msg):
    out = bot.handle(msg["from"], msg["name"], msg["text"], msg_id=msg["id"], prefix="WA",
                     kind="text" if msg["text"] else (msg["type"] or "unknown"))
    if out["duplicate"] or not out["reply"]:
        return
    wa = _wa()
    if wa is None:
        print("[whatsapp] WA_TOKEN / WA_PHONE_NUMBER_ID not set, reply not sent", flush=True)
        return
    try:
        wa.send_text(msg["from"], out["reply"])
    except WhatsAppError as e:
        print(f"[whatsapp] send failed for {out['customer_id']}: {e}", flush=True)


@app.get("/whatsapp")
def whatsapp_verify(request: Request):
    challenge = verify_subscription(dict(request.query_params), os.getenv("WA_VERIFY_TOKEN", ""))
    if not challenge:
        raise HTTPException(403, "verification failed")
    return Response(challenge, media_type="text/plain")


@app.post("/whatsapp")
async def whatsapp_webhook(request: Request, background: BackgroundTasks):
    raw = await request.body()
    secret = os.getenv("WA_APP_SECRET", "")
    if not secret or not valid_signature(raw, request.headers.get("X-Hub-Signature-256"), secret):
        raise HTTPException(401, "bad signature")
    try:
        data = parse_webhook(await request.json())
    except ValueError:
        return {"ok": True}
    for s in data["statuses"]:
        if s["status"] == "failed":
            print(f"[whatsapp] delivery failed: {s['error']}", flush=True)
    inline = os.getenv("WHATSAPP_INLINE", "") == "1"  # serverless (Vercel): finish before responding
    for m in data["messages"]:
        if inline:
            _whatsapp_turn(m)
        else:
            background.add_task(_whatsapp_turn, m)  # answer Meta at once, reply in the background
    return {"ok": True}


# ---- judge pages: /try (phone chat) and /qr (projector screen) ----------------------------------

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _page(name):
    with open(os.path.join(STATIC, name), encoding="utf-8") as fh:
        return fh.read()


def _try_url(request: Request):
    """Where the QR code points. TRY_URL overrides it (e.g. Dythan's Vercel /try once it's live)."""
    if os.getenv("TRY_URL"):
        return os.getenv("TRY_URL")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host") or "localhost:8000"
    local = host.startswith(("localhost", "127.0.0.1"))
    return f"{'http' if local else 'https'}://{host}/try"


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/try")


@app.get("/try", response_class=HTMLResponse, include_in_schema=False)
def try_page():
    return HTMLResponse(_page("try.html"), headers={"Cache-Control": "no-cache"})


@app.get("/qr", response_class=HTMLResponse, include_in_schema=False)
def qr_page(request: Request):
    return HTMLResponse(_page("qr.html").replace("{{TRY_URL}}", html.escape(_try_url(request))))


@app.get("/qr.svg", include_in_schema=False)
def qr_svg(request: Request):
    import segno

    buf = io.BytesIO()
    segno.make(_try_url(request), error="m").save(buf, kind="svg", scale=10, border=2, dark="#123D35")
    return Response(buf.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "no-cache"})


# ---- health --------------------------------------------------------------------------------

@app.get("/health")
def health():
    from nudgely.llm import available

    from nudgely.conversations import remote

    return {"ok": True, "ai": available(), "whatsapp": _wa() is not None, "supabase": supabase_sync.enabled(),
            "store": "supabase" if remote() else "local"}

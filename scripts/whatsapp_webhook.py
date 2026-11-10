"""Receive WhatsApp messages from Meta's webhook.

  python scripts/whatsapp_webhook.py              # log incoming messages to data/wa_inbox.jsonl
  python scripts/whatsapp_webhook.py --echo       # also reply "Got it: <text>" (end-to-end test)
  python scripts/whatsapp_webhook.py --bot        # tag each message and answer with the reply bot
                                                  # (customers kept in data/wa_customers.json, git-ignored)

Listens on 127.0.0.1:8788. Expose it with a tunnel for Meta to reach it:
  cloudflared tunnel --url http://127.0.0.1:8788
then in Meta (WhatsApp -> Configuration -> Webhook) set:
  Callback URL  https://<tunnel>/whatsapp      Verify token  the WA_VERIFY_TOKEN from .env
and subscribe to the "messages" field.

--bot replies to STOP / START itself and never auto-answers someone who opted out.
"""

import argparse
import json
import os
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

from nudgely import bot  # noqa: E402
from nudgely.whatsapp import (WhatsApp, WhatsAppError, parse_webhook, valid_signature,  # noqa: E402
                              verify_subscription)

load_dotenv(os.path.join(ROOT, ".env"))
INBOX = os.path.join(ROOT, "data", "wa_inbox.jsonl")  # git-ignored: real customer messages
VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("WA_APP_SECRET", "")
ARGS = None


def on_message(wa, msg):
    """Called once per incoming message. msg = {id, from, name, timestamp, type, text}."""
    if ARGS.bot:
        threading.Thread(target=bot_turn, args=(wa, msg), daemon=True).start()
    elif ARGS.echo and msg["text"]:
        try:
            wa.send_text(msg["from"], f"Got it: {msg['text'][:200]}")
            print("  -> echoed", flush=True)
        except WhatsAppError as e:
            print(f"  -> echo failed: {e}", flush=True)


def bot_turn(wa, msg):
    """One turn through the shared bot (nudgely/bot.py), then send the reply on WhatsApp."""
    out = bot.handle(msg["from"], msg["name"], msg["text"], msg_id=msg["id"], prefix="WA",
                     kind="text" if msg["text"] else (msg["type"] or "unknown"))
    if out["duplicate"]:  # Meta retries deliveries; each message is answered once
        return
    tags = ", ".join(f"{t['type']}={t['value']}" for t in out["new_tags"]) or "no new tags"
    print(f"  -> {out['customer_id']} tags: {tags}", flush=True)
    if out["reply"]:
        try:
            wa.send_text(msg["from"], out["reply"])
        except WhatsAppError as e:
            print(f"  -> send failed: {e}", flush=True)
    print(f"  -> {'HANDOVER: ' if out['handover'] else ''}{out['reason'][:100]}", flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # Meta's subscription check
        params = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        challenge = verify_subscription(params, VERIFY_TOKEN)
        self.send_response(200 if challenge else 403)
        self.end_headers()
        self.wfile.write((challenge or "forbidden").encode())
        print(f"[{now()}] verification {'OK' if challenge else 'REJECTED'}", flush=True)

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if APP_SECRET and not valid_signature(raw, self.headers.get("X-Hub-Signature-256"), APP_SECRET):
            self.send_response(401)
            self.end_headers()
            print(f"[{now()}] rejected: bad signature", flush=True)
            return
        self.send_response(200)  # answer fast; Meta retries slow or failed deliveries
        self.end_headers()
        try:
            data = parse_webhook(json.loads(raw or b"{}"))
        except ValueError:
            return
        for s in data["statuses"]:
            print(f"[{now()}] status {s['status']} for ...{str(s['recipient'])[-4:]}"
                  + (f" ({s['error']})" if s["error"] else ""), flush=True)
        for m in data["messages"]:
            os.makedirs(os.path.dirname(INBOX), exist_ok=True)
            with open(INBOX, "a", encoding="utf-8") as f:
                f.write(json.dumps({**m, "received_at": now()}, ensure_ascii=False) + "\n")
            print(f"[{now()}] message from {m['name'] or 'unknown'} (...{str(m['from'])[-4:]}): "
                  f"{m['type']} {len(m['text'])} chars", flush=True)
            on_message(WA, m)

    def log_message(self, *a):
        pass


def now():
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8788)
    p.add_argument("--echo", action="store_true", help="reply to each message (end-to-end test)")
    p.add_argument("--bot", action="store_true", help="tag each message and answer with the reply bot")
    ARGS = p.parse_args()
    if not VERIFY_TOKEN:
        sys.exit("Set WA_VERIFY_TOKEN in .env first (any string you choose).")
    if not APP_SECRET:
        print("WARNING: WA_APP_SECRET not set, so webhook signatures are not checked.", flush=True)
    WA = WhatsApp.from_env()
    print(f"listening on 127.0.0.1:{ARGS.port} (path /whatsapp), inbox -> {INBOX}", flush=True)
    HTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()

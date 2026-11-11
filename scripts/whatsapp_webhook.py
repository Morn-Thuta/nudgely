"""Receive WhatsApp messages from Meta's webhook, tag them and answer them.

  python scripts/whatsapp_webhook.py              # log incoming messages to data/wa_inbox.jsonl
  python scripts/whatsapp_webhook.py --echo       # also reply "Got it: <text>" (pipe test, no AI)
  python scripts/whatsapp_webhook.py --bot        # tag each message and answer with the reply bot
                                                  # (customers kept in data/wa_customers.json, git-ignored)
  python scripts/whatsapp_webhook.py --dry-run    # like --bot, but print the draft reply and send nothing
                                                  # (no WA keys needed)

Listens on 127.0.0.1:8788. Expose it with a tunnel for Meta to reach it:
  cloudflared tunnel --url http://127.0.0.1:8788
then in Meta (WhatsApp -> Configuration -> Webhook) set:
  Callback URL  https://<tunnel>/whatsapp      Verify token  the WA_VERIFY_TOKEN from .env
and subscribe to the "messages" field.

The bot is the shared one in nudgely/bot.py (same as the web chat and the FastAPI backend):
it replies to STOP / START itself and never auto-answers someone who opted out.

The webhook answers Meta at once and hands each message to one background worker.
The AI can take several seconds, Meta retries anything slow, and a retry would
otherwise mean a second reply. One worker also keeps each customer's messages in
order.
"""

import argparse
import json
import os
import queue
import sys
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from dotenv import load_dotenv  # noqa: E402

from nudgely import bot, llm  # noqa: E402
from nudgely.whatsapp import (WhatsApp, WhatsAppError, parse_webhook, valid_signature,  # noqa: E402
                              verify_subscription)

load_dotenv(os.path.join(ROOT, ".env"))
INBOX = os.path.join(ROOT, "data", "wa_inbox.jsonl")  # git-ignored: real customer messages
VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("WA_APP_SECRET", "")
ARGS = None
WA = None
WORK = queue.Queue()


def on_message(wa, msg):
    """Called once per incoming message, on the worker. msg = {id, from, name, timestamp, type, text}."""
    if ARGS.bot or ARGS.dry_run:
        bot_turn(wa, msg)
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
        if ARGS is not None and ARGS.dry_run:
            print(f"     draft (not sent): {out['reply']}", flush=True)
        else:
            try:
                wa.send_text(msg["from"], out["reply"])
                _mark_read(wa, msg)
            except WhatsAppError as e:
                print(f"  -> send failed: {e}", flush=True)
    print(f"  -> {'HANDOVER: ' if out['handover'] else ''}{out['reason'][:100]}", flush=True)


def _mark_read(wa, msg):
    try:
        wa.mark_read(msg["id"])     # blue ticks: the shop has seen it
    except Exception:  # noqa: BLE001 - cosmetic, never worth failing a reply over
        pass


def worker():
    while True:
        msg = WORK.get()
        try:
            on_message(WA, msg)
        except Exception as e:  # noqa: BLE001 - one bad message must not stop the worker
            print(f"  ! failed on message from ...{str(msg.get('from'))[-4:]}: {e}", flush=True)
        finally:
            WORK.task_done()


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
            WORK.put(m)   # answered Meta already; the worker does the slow part

    def log_message(self, *a):
        pass


def now():
    return datetime.now().isoformat(timespec="seconds")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=8788)
    p.add_argument("--echo", action="store_true", help="reply 'Got it' to each message (pipe test, no AI)")
    p.add_argument("--bot", action="store_true", help="tag each message and answer with the reply bot")
    p.add_argument("--dry-run", action="store_true", help="like --bot, but print draft replies and send nothing")
    ARGS = p.parse_args()
    if not VERIFY_TOKEN:
        sys.exit("Set WA_VERIFY_TOKEN in .env first (any string you choose).")
    if not APP_SECRET:
        print("WARNING: WA_APP_SECRET not set, so webhook signatures are not checked.", flush=True)
    if (ARGS.bot or ARGS.dry_run) and not llm.available():
        print("WARNING: no LLM key in .env, so every reply will hand over to a person.", flush=True)
    try:
        WA = WhatsApp.from_env()
    except ValueError:
        if not ARGS.dry_run:
            sys.exit("Set WA_TOKEN and WA_PHONE_NUMBER_ID in .env (ask Thuta), or run with --dry-run.")
        WA = None                    # a dry run never sends, so it can run before the keys arrive
    threading.Thread(target=worker, daemon=True).start()
    mode = ("bot, DRY RUN - nothing sent" if ARGS.dry_run else "bot, replies are sent" if ARGS.bot
            else "echo" if ARGS.echo else "log only")
    print(f"listening on 127.0.0.1:{ARGS.port} (path /whatsapp), {mode}, inbox -> {INBOX}", flush=True)
    HTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()

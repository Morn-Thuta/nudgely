"""Receive WhatsApp messages from Meta's webhook, tag them and answer them.

  python scripts/whatsapp_webhook.py              # tag each message and reply with the AI bot
  python scripts/whatsapp_webhook.py --dry-run    # tag and draft replies, print them, send nothing
  python scripts/whatsapp_webhook.py --echo       # just reply "Got it: <text>" (pipe test, no AI)
  python scripts/whatsapp_webhook.py --clear-handover 6591234567   # let the bot talk to them again

Every message is also appended to data/wa_inbox.jsonl, and each conversation (chat,
tags, handover state) is kept in data/wa_conversations.json. Both are git-ignored:
they hold real customers' messages.

To start a teammate's phone as an existing demo customer (their chat history and
tags), map the number in data/wa_contacts.json (git-ignored): {"6591234567": "C001"}.
Anyone not listed is created as a new customer on their first message.

Listens on 127.0.0.1:8788. Expose it with a tunnel for Meta to reach it:
  cloudflared tunnel --url http://127.0.0.1:8788
then in Meta (WhatsApp -> Configuration -> Webhook) set:
  Callback URL  https://<tunnel>/whatsapp      Verify token  the WA_VERIFY_TOKEN from .env
and subscribe to the "messages" field.

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

from nudgely import conversation, llm, reply  # noqa: E402
from nudgely.whatsapp import (WhatsApp, WhatsAppError, parse_webhook, valid_signature,  # noqa: E402
                              verify_subscription)

load_dotenv(os.path.join(ROOT, ".env"))
DATA = os.path.join(ROOT, "data")
INBOX = os.path.join(DATA, "wa_inbox.jsonl")                 # git-ignored: real customer messages
CONVERSATIONS = os.path.join(DATA, "wa_conversations.json")  # git-ignored: chats, tags, handovers
CONTACTS = os.path.join(DATA, "wa_contacts.json")            # git-ignored: phone -> demo customer id
VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "")
APP_SECRET = os.getenv("WA_APP_SECRET", "")
ARGS = None
STORE = None
WORK = queue.Queue()


def on_message(wa, msg):
    """Called once per incoming message, on the worker. msg = {id, from, name, timestamp, type, text}."""
    if ARGS.echo:
        if msg["text"]:
            try:
                wa.send_text(msg["from"], f"Got it: {msg['text'][:200]}")
                print("  -> echoed", flush=True)
            except WhatsAppError as e:
                print(f"  -> echo failed: {e}", flush=True)
        return

    out = conversation.handle(
        msg, STORE,
        tag=lambda cid, text, date, prior, names: llm.tag_message(cid, text, date=date, prior=prior, names=names),
        answer=lambda customer, chat, text, tags, first: reply.answer(customer, chat, text, tags=tags,
                                                                      first_reply=first),
        send=lambda number, text: (wa.send_text(number, text), _mark_read(wa, msg)),
        known=known_customer, dry_run=ARGS.dry_run)
    who = f"...{str(msg['from'])[-4:]}"
    print(f"  -> {who}: {out['action']}"
          + (f", {out['tags_added']} new tag(s)" if out.get("tags_added") else "")
          + (f" | person needed: {out['reason']}" if out.get("handover") else
             (f" | {out['reason']}" if out.get("reason") else "")), flush=True)
    if ARGS.dry_run and out.get("reply"):
        print(f"     draft: {out['reply']}", flush=True)


def _mark_read(wa, msg):
    try:
        wa.mark_read(msg["id"])     # blue ticks: the shop has seen it
    except Exception:  # noqa: BLE001 - cosmetic, never worth failing a reply over
        pass


def known_customer(number):
    """A teammate's phone mapped to a demo customer starts with that customer's history."""
    try:
        with open(CONTACTS, encoding="utf-8") as f:
            cid = json.load(f).get(str(number))
    except (OSError, ValueError):
        return None
    if not cid:
        return None
    import pandas as pd

    def source(name):
        real = os.path.join(DATA, name)
        return real if os.path.exists(real) else os.path.join(DATA, "examples", name)

    rows = pd.read_csv(source("customers.csv"), dtype=str)
    match = rows[rows.customer_id == cid]
    if match.empty:
        print(f"  ! {CONTACTS} maps a number to {cid}, which is not in customers.csv", flush=True)
        return None
    with open(source("chats.json"), encoding="utf-8") as f:
        chat = json.load(f).get(cid, [])
    with open(source("tags.json"), encoding="utf-8") as f:
        tags = json.load(f).get(cid, {})
    return {"customer_id": cid, "name": match.iloc[0]["name"], "label": match.iloc[0]["label"],
            "chat": chat, "tags": tags}


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
    p.add_argument("--echo", action="store_true", help="just reply 'Got it' (pipe test, no AI)")
    p.add_argument("--dry-run", action="store_true", help="tag and draft replies, print them, send nothing")
    p.add_argument("--clear-handover", metavar="NUMBER", help="let the bot answer this number again, then exit")
    ARGS = p.parse_args()
    STORE = conversation.Store(CONVERSATIONS)
    if ARGS.clear_handover:
        number = "".join(ch for ch in ARGS.clear_handover if ch.isdigit())
        sys.exit(f"cleared ...{number[-4:]}" if STORE.clear_handover(number) else "no conversation with that number")
    if not VERIFY_TOKEN:
        sys.exit("Set WA_VERIFY_TOKEN in .env first (any string you choose).")
    if not APP_SECRET:
        print("WARNING: WA_APP_SECRET not set, so webhook signatures are not checked.", flush=True)
    if not ARGS.echo and not llm.available():
        print("WARNING: no LLM key in .env, so every reply will hand over to a person.", flush=True)
    try:
        WA = WhatsApp.from_env()
    except ValueError:
        if not ARGS.dry_run:
            sys.exit("Set WA_TOKEN and WA_PHONE_NUMBER_ID in .env (ask Thuta), or run with --dry-run.")
        WA = None                    # a dry run never sends, so it can run before the keys arrive
    threading.Thread(target=worker, daemon=True).start()
    mode = "echo" if ARGS.echo else ("bot, DRY RUN - nothing sent" if ARGS.dry_run else "bot, replies are sent")
    print(f"listening on 127.0.0.1:{ARGS.port} (path /whatsapp), {mode}, inbox -> {INBOX}", flush=True)
    HTTPServer(("127.0.0.1", ARGS.port), Handler).serve_forever()

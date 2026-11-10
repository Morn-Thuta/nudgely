"""Who each WhatsApp number is, what they said, and what we remember about them.

Real customer data, so it lives in data/wa_customers.json, which is git-ignored.
One record per WhatsApp number:
  {"customer_id", "name", "label", "chat": [{"from", "text", "date"}], "tags", "replied",
   "opted_out", "handover", "seen_ids"}
"""

import json
import os
import threading
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORE = os.path.join(ROOT, "data", "wa_customers.json")
STOP_WORDS = {"stop", "unsubscribe", "stop all"}
START_WORDS = {"start", "unstop"}
MAX_CHAT = 30  # keep the prompt small; older turns add cost, not much context

_lock = threading.Lock()


def _load():
    if not os.path.exists(STORE):
        return {}
    with open(STORE, encoding="utf-8") as f:
        return json.load(f)


def _save(data):
    os.makedirs(os.path.dirname(STORE), exist_ok=True)
    tmp = STORE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STORE)


def get_or_create(wa_id, name=""):
    """The record for a WhatsApp number, created on first message.

    New people get label "New": not Persuadable, so the reply bot never offers them a discount.
    """
    with _lock:
        data = _load()
        rec = data.get(wa_id)
        if rec is None:
            rec = {"customer_id": f"WA{len(data) + 1:03d}", "name": name or "", "label": "New",
                   "chat": [], "tags": {}, "replied": False, "opted_out": False,
                   "handover": False, "seen_ids": []}
            data[wa_id] = rec
            _save(data)
        elif name and not rec.get("name"):
            rec["name"] = name
            _save(data)
        return dict(rec)


def update(wa_id, rec):
    with _lock:
        data = _load()
        rec["chat"] = rec.get("chat", [])[-MAX_CHAT:]
        rec["seen_ids"] = rec.get("seen_ids", [])[-200:]
        data[wa_id] = rec
        _save(data)


def all_customers():
    with _lock:
        return _load()


def reset():
    """Start the demo clean. Moves the current store to a timestamped backup; returns its path (or None)."""
    with _lock:
        if not os.path.exists(STORE):
            return None
        from datetime import datetime

        backup = STORE.replace(".json", f".backup-{datetime.now():%Y%m%d-%H%M%S}.json")
        os.replace(STORE, backup)
        return backup


def is_stop(text):
    return str(text).strip().lower() in STOP_WORDS


def is_start(text):
    return str(text).strip().lower() in START_WORDS


def today():
    return date.today().isoformat()

"""Conversation state in Supabase, so the backend keeps nothing on disk (Render restarts, Vercel).

Used by nudgely/conversations.py when NUDGELY_STORE=supabase. Needs supabase/migrations/002_backend_state.sql.
A customer is found by key_hash = HMAC-SHA256(KEY_SALT, WhatsApp number or web session). The number itself
is never stored, and the dashboard cannot read key_hash (column grants in 002).
"""

import hashlib
import hmac
import os
from datetime import datetime, timezone

import requests

from nudgely.supabase_sync import _config

FIELDS = "id,name,label,replied,opted_out,handover,memory,seen_ids,msg_count"


class RemoteStoreError(RuntimeError):
    pass


def key_hash(key):
    salt = os.getenv("KEY_SALT", "")
    if not salt:
        raise RemoteStoreError("KEY_SALT is not set; it keeps customer keys unguessable")
    return hmac.new(salt.encode(), str(key).encode(), hashlib.sha256).hexdigest()


def _req(method, path, json=None, prefer="return=representation"):
    url, k = _config()
    if not (url and k):
        raise RemoteStoreError("SUPABASE_URL / SUPABASE_SERVICE_KEY not set")
    r = requests.request(method, f"{url}/rest/v1/{path}", json=json, timeout=10, headers={
        "apikey": k, "Authorization": f"Bearer {k}", "Content-Type": "application/json", "Prefer": prefer})
    if r.status_code == 409:
        return None  # conflict: caller decides
    if r.status_code >= 300:
        raise RemoteStoreError(f"{method} {path.split('?')[0]}: HTTP {r.status_code} {r.text[:200]}")
    return r.json() if r.text else []


def _chat(customer_id, limit):
    rows = _req("GET", f"messages?customer_id=eq.{customer_id}&select=sender,text,created_at"
                       f"&order=created_at.desc&limit={limit}")
    return [{"from": m["sender"], "text": m["text"], "date": m["created_at"][:10]} for m in reversed(rows)]


def _to_rec(row, chat):
    return {"customer_id": row["id"], "name": row.get("name") or "", "label": row.get("label") or "New",
            "chat": chat, "tags": row.get("memory") or {}, "replied": bool(row.get("replied")),
            "opted_out": bool(row.get("opted_out")), "handover": bool(row.get("handover")),
            "seen_ids": list(row.get("seen_ids") or []), "msg_count": int(row.get("msg_count") or 0)}


def get_or_create(key, name="", prefix="WA", max_chat=30):
    h = key_hash(key)
    rows = _req("GET", f"customers?key_hash=eq.{h}&select={FIELDS}")
    if rows:
        row = rows[0]
        if name and not row.get("name"):
            _req("PATCH", f"customers?id=eq.{row['id']}", {"name": name}, "return=minimal")
            row["name"] = name
        return _to_rec(row, _chat(row["id"], max_chat))

    channel = "web" if prefix == "WEB" else "whatsapp"
    taken = _req("GET", f"customers?id=like.{prefix}*&select=id")
    n = len(taken or [])
    for bump in range(1, 20):  # two first messages at once: the loser takes the next id
        cid = f"{prefix}{n + bump:03d}"
        made = _req("POST", "customers", {"id": cid, "channel": channel, "name": name or None,
                                          "key_hash": h, "label": "New"})
        if made:
            return _to_rec(made[0], [])
        again = _req("GET", f"customers?key_hash=eq.{h}&select={FIELDS}")  # same person, other request won
        if again:
            return _to_rec(again[0], _chat(again[0]["id"], max_chat))
    raise RemoteStoreError(f"could not allocate an id for {prefix}")


def update(rec):
    _req("PATCH", f"customers?id=eq.{rec['customer_id']}", {
        "name": rec.get("name") or None, "label": rec.get("label", "New"), "replied": bool(rec.get("replied")),
        "opted_out": bool(rec.get("opted_out")), "handover": bool(rec.get("handover")),
        "memory": rec.get("tags") or {}, "seen_ids": list(rec.get("seen_ids", []))[-200:],
        "msg_count": int(rec.get("msg_count", 0)), "last_seen_at": datetime.now(timezone.utc).isoformat(),
    }, "return=minimal")


def all_customers(limit=50, max_chat=8):
    rows = _req("GET", f"customers?channel=in.(whatsapp,web)&select={FIELDS}&order=last_seen_at.desc&limit={limit}")
    return {r["id"]: _to_rec(r, _chat(r["id"], max_chat)) for r in rows}


def set_handover(customer_id, value):
    _req("PATCH", f"customers?id=eq.{customer_id}", {"handover": bool(value)}, "return=minimal")


def reset():
    """Delete live WhatsApp and web chats (their messages and tags cascade). Demo customers stay."""
    _req("DELETE", "customers?channel=in.(whatsapp,web)", prefer="return=minimal")
    return "supabase (live chats deleted)"

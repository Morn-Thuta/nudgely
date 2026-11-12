"""Mirror each conversation turn into Supabase, for the Next.js dashboard (realtime).

Tables are defined in docs/V1_ARCHITECTURE.md. Writes use PostgREST with the service key, in a
background thread, so a slow or missing database never delays a customer's reply.
Off (a no-op) until SUPABASE_URL and SUPABASE_SERVICE_KEY are set.
Phone numbers are never written: customers are identified by their Nudgely id.
"""

import os
import threading
from datetime import datetime, timezone

import requests


def _config():
    return os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_SERVICE_KEY", "")


def enabled():
    url, key = _config()
    return bool(url and key)


def _channel(customer_id):
    return "web" if str(customer_id).startswith("WEB") else "whatsapp"


_local = threading.local()


def http(method, url, json=None, timeout=10, headers=None):
    """One HTTP call to Supabase on a kept-alive connection (one session per thread).

    A fresh TLS handshake per call was the main cost under load on Render's small CPU.
    """
    s = getattr(_local, "session", None)
    if s is None:
        s = _local.session = requests.Session()
    return s.request(method, url, json=json, timeout=timeout, headers=headers)


def _post(path, rows, prefer):
    url, key = _config()
    r = http("POST", f"{url}/rest/v1/{path}", json=rows, timeout=10, headers={
        "apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json",
        "Prefer": prefer})
    if r.status_code >= 300:
        raise RuntimeError(f"{path}: HTTP {r.status_code} {r.text[:200]}")


def _write(rec, new_messages, new_tags, handover_reply):
    cid = rec["customer_id"]
    now = datetime.now(timezone.utc).isoformat()
    _post("customers", [{"id": cid, "channel": _channel(cid), "name": rec.get("name") or None,
                         "label": rec.get("label", "New"), "handover": bool(rec.get("handover")),
                         "opted_out": bool(rec.get("opted_out")), "last_seen_at": now}],
          "resolution=merge-duplicates,return=minimal")
    if new_messages:
        _post("messages", [{"customer_id": cid, "sender": m["from"], "text": m["text"],
                            "handover": bool(handover_reply and m["from"] == "store")}
                           for m in new_messages], "return=minimal")
    rows = [t for t in new_tags if t.get("type") and t.get("value") and t.get("evidence")]
    if rows:
        _post("tags?on_conflict=customer_id,type,value",
              [{"customer_id": cid, "type": t["type"], "value": str(t["value"]), "evidence": t["evidence"]}
               for t in rows], "resolution=merge-duplicates,return=minimal")


def sync(rec, new_messages, new_tags, handover_reply=False, wait=False):
    """Write one turn. Never raises; logs a line if Supabase rejects it."""
    if not enabled():
        return

    def run():
        try:
            _write(rec, list(new_messages), list(new_tags), handover_reply)
        except Exception as e:  # noqa: BLE001 - the dashboard lagging must not break a reply
            print(f"[supabase] sync failed for {rec.get('customer_id')}: {str(e)[:200]}", flush=True)

    if wait:
        run()
    else:
        threading.Thread(target=run, daemon=True).start()

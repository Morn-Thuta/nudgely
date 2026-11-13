"""Send one reviewed campaign message for real, on WhatsApp, to an opted-in demo phone.

The dashboard's campaign page calls this through POST /api/campaign/send after a team member has
read (and maybe edited) the draft and confirmed. Only customers listed in LIVE_RECIPIENTS can be
sent to, so a real customer can never be messaged from the demo:

    LIVE_RECIPIENTS={"C001": "6591234567"}     # Render env var only; never in git

WhatsApp lets a business send free text only within 24 hours of the customer's last message, so the
demo phone messages the shop first (on finals morning). Outside that window we refuse instead of
pretending: the message would be accepted by Meta and then silently fail.

Sending links the phone to the demo customer (key_hash), so when the phone replies the bot answers
with that customer's chat history and tags (Aisha's oat milk, her son's party).
"""

import json
import os
from datetime import datetime, timedelta, timezone

from nudgely import remote_store
from nudgely.whatsapp import WhatsApp, WhatsAppError, normalise_number

WINDOW = timedelta(hours=24)
MAX_LEN = 600
OPT_OUT = "Reply STOP to opt out"


class SendError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def recipients():
    """{customer_id: phone} from LIVE_RECIPIENTS. Bad JSON means nobody, not a crash."""
    try:
        data = json.loads(os.getenv("LIVE_RECIPIENTS", "") or "{}")
    except ValueError:
        return {}
    return {str(k): str(v) for k, v in data.items() if v} if isinstance(data, dict) else {}


def _last_customer_message(customer_ids):
    ids = ",".join(i for i in customer_ids if i)
    rows = remote_store._req("GET", f"messages?customer_id=in.({ids})&sender=eq.customer"
                                    "&select=created_at&order=created_at.desc&limit=1")
    if not rows:
        return None
    return datetime.fromisoformat(rows[0]["created_at"].replace("Z", "+00:00"))


def _memory_from_tags(customer_id):
    rows = remote_store._req("GET", f"tags?customer_id=eq.{customer_id}&select=type,value,evidence,created_at")
    return {"customer_id": customer_id,
            "tags": [{"type": r["type"], "value": r["value"], "evidence": r["evidence"],
                      "date": (r.get("created_at") or "")[:10]} for r in rows]}


def send(customer_id, message, wa=None, now=None):
    """Send `message` to the phone mapped to `customer_id`. Returns {"sent", "customer_id", "message_id"}."""
    phone = recipients().get(customer_id)
    if not phone:
        raise SendError(403, f"{customer_id} is not an opted-in demo phone, so it can't be sent to for real.")
    text = str(message or "").strip()
    if not text:
        raise SendError(400, "The message is empty.")
    if len(text) > MAX_LEN:
        raise SendError(400, f"The message is over {MAX_LEN} characters.")
    if OPT_OUT.lower() not in text.lower():
        text = f"{text.rstrip()} {OPT_OUT}"

    rows = remote_store._req("GET", f"customers?id=eq.{customer_id}&select={remote_store.FIELDS}")
    if not rows:
        raise SendError(404, f"No customer {customer_id}.")
    row = rows[0]
    if row.get("opted_out"):
        raise SendError(409, f"{customer_id} has opted out. Nothing was sent.")

    h = remote_store.key_hash(normalise_number(phone))
    holder = remote_store._req("GET", f"customers?key_hash=eq.{h}&select=id") or []
    other = holder[0]["id"] if holder and holder[0]["id"] != customer_id else None
    last = _last_customer_message([customer_id, other])
    now = now or datetime.now(timezone.utc)
    if not last or now - last > WINDOW:
        raise SendError(409, "WhatsApp only allows this message within 24 hours of the customer's last message. "
                             "Send any message from the demo phone to the shop's WhatsApp, then try again. Nothing was sent.")

    wa = wa or WhatsApp.from_env()
    try:
        result = wa.send_text(phone, text)
    except WhatsAppError as e:
        raise SendError(502, f"WhatsApp refused the message: {e}") from e

    # Link the phone to this customer so the reply carries their history and tags.
    if other:
        remote_store._req("PATCH", f"customers?id=eq.{other}", {"key_hash": None}, "return=minimal")
    # channel "whatsapp": the live inbox hides seeded demo customers, so without this the nudge
    # stays invisible until the first reply.
    patch = {"key_hash": h, "channel": "whatsapp", "replied": True, "last_seen_at": now.isoformat()}
    if not (row.get("memory") or {}).get("tags"):
        patch["memory"] = _memory_from_tags(customer_id)
    remote_store._req("PATCH", f"customers?id=eq.{customer_id}", patch, "return=minimal")
    remote_store._req("POST", "messages", {"customer_id": customer_id, "sender": "store", "text": text},
                      "return=minimal")
    msg_id = ((result or {}).get("messages") or [{}])[0].get("id", "")
    print(f"[campaign] live send to {customer_id} ({msg_id})", flush=True)
    return {"sent": True, "customer_id": customer_id, "message_id": msg_id, "text": text}

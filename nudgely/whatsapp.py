"""WhatsApp Cloud API (Meta), called directly: send messages and read incoming ones.

Why not through MantaGO: on our MantaGO link, broadcasts never leave "Unsent" and no API,
webhook or export gives incoming chat text (see docs/MANTAGO_API.md). Meta's Cloud API does
both: a webhook with the full message text, and free-text replies within 24 hours of the
customer's last message. Outside that window only approved templates can be sent.

Setup (developers.facebook.com -> your app -> WhatsApp -> API Setup), values go in .env:
  WA_TOKEN            access token (temporary 24h token, or a system user token)
  WA_PHONE_NUMBER_ID  "Phone number ID" (not the phone number itself)
  WA_VERIFY_TOKEN     any string you choose; type the same one when you register the webhook
  WA_APP_SECRET       App settings -> Basic -> App secret (to check webhook signatures)
  WA_GRAPH_VERSION    optional, default below
"""

import hashlib
import hmac
import os

import requests

GRAPH = "https://graph.facebook.com"
DEFAULT_VERSION = "v25.0"  # Meta forwards calls on a retired version to the oldest live one


class WhatsAppError(Exception):
    def __init__(self, status, code, message, body=None):
        super().__init__(f"HTTP {status}, code {code}: {message}")
        self.status = status
        self.code = code
        self.body = body


class WhatsApp:
    def __init__(self, token, phone_number_id, version=DEFAULT_VERSION, timeout=20):
        if not (token and phone_number_id):
            raise ValueError("token and phone_number_id are required")
        self.token = token
        self.phone_number_id = phone_number_id
        self.version = version or DEFAULT_VERSION
        self.timeout = timeout

    @classmethod
    def from_env(cls):
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except ImportError:
            pass
        return cls(os.getenv("WA_TOKEN", ""), os.getenv("WA_PHONE_NUMBER_ID", ""),
                   os.getenv("WA_GRAPH_VERSION", DEFAULT_VERSION))

    @classmethod
    def from_streamlit(cls, st):
        s = st.secrets["whatsapp"]
        return cls(s["token"], s["phone_number_id"], s.get("graph_version", DEFAULT_VERSION))

    # ---- sending -----------------------------------------------------------

    def _send(self, payload):
        url = f"{GRAPH}/{self.version}/{self.phone_number_id}/messages"
        headers = {"Authorization": f"Bearer {self.token}"}
        r = requests.post(url, json={"messaging_product": "whatsapp", **payload}, headers=headers,
                          timeout=self.timeout)
        try:
            data = r.json()
        except ValueError:
            data = {"error": {"message": r.text[:300]}}
        if r.ok and "error" not in data:
            return data
        err = data.get("error") or {}
        raise WhatsAppError(r.status_code, err.get("code"), err.get("message", r.reason), data)

    def send_text(self, to, body, preview_url=False):
        """Free text. Delivers only within 24h of the customer's last message to us."""
        return self._send({"to": normalise_number(to), "type": "text",
                           "text": {"body": body, "preview_url": preview_url}})

    def send_template(self, to, name, language="en_US", params=None):
        """An approved template; works any time. params fill {{1}}, {{2}}... of the body."""
        template = {"name": name, "language": {"code": language}}
        if params:
            template["components"] = [{"type": "body", "parameters": [
                {"type": "text", "text": str(p)} for p in params]}]
        return self._send({"to": normalise_number(to), "type": "template", "template": template})

    def mark_read(self, message_id):
        return self._send({"status": "read", "message_id": message_id})


# ---- receiving ---------------------------------------------------------------

def normalise_number(number):
    """'+65 9123 4567' -> '6591234567' (the format the API uses)."""
    return "".join(ch for ch in str(number) if ch.isdigit())


def verify_subscription(params, verify_token):
    """Meta's one-time GET check when you register the webhook. Returns the challenge or None."""
    if params.get("hub.mode") == "subscribe" and params.get("hub.verify_token") == verify_token:
        return params.get("hub.challenge")
    return None


def valid_signature(raw_body, signature_header, app_secret):
    """Check X-Hub-Signature-256 so only Meta can post to the webhook."""
    if not (app_secret and signature_header and signature_header.startswith("sha256=")):
        return False
    expected = hmac.new(app_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature_header[len("sha256="):])


def parse_webhook(payload):
    """Flatten a webhook POST into incoming messages and delivery statuses.

    Returns {"messages": [...], "statuses": [...]}. Each message:
      {"id", "from" (digits), "name", "timestamp", "type", "text"}  text is "" for non-text types
    Each status: {"id", "recipient", "status" (sent/delivered/read/failed), "timestamp", "error"}
    """
    out = {"messages": [], "statuses": []}
    for entry in (payload or {}).get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            names = {c.get("wa_id"): (c.get("profile") or {}).get("name", "")
                     for c in value.get("contacts", [])}
            for m in value.get("messages", []):
                kind = m.get("type", "")
                if kind == "text":
                    text = (m.get("text") or {}).get("body", "")
                elif kind == "button":
                    text = (m.get("button") or {}).get("text", "")
                elif kind == "interactive":
                    i = m.get("interactive") or {}
                    text = (i.get("button_reply") or i.get("list_reply") or {}).get("title", "")
                else:
                    text = ""
                out["messages"].append({"id": m.get("id"), "from": m.get("from"),
                                        "name": names.get(m.get("from"), ""),
                                        "timestamp": m.get("timestamp"), "type": kind, "text": text})
            for s in value.get("statuses", []):
                errors = s.get("errors") or []
                out["statuses"].append({"id": s.get("id"), "recipient": s.get("recipient_id"),
                                        "status": s.get("status"), "timestamp": s.get("timestamp"),
                                        "error": errors[0].get("title") if errors else None})
    return out

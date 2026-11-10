"""One incoming WhatsApp message in, at most one reply out: remember it, tag it, answer it.

Used by scripts/whatsapp_webhook.py now and meant for the FastAPI backend later, so
it holds no web server or Meta code. Everything it calls (tagger, reply writer,
sender) is passed in, which is how the tests run it without an LLM or a phone.

What it guarantees, in order:

1. The same message is never handled twice. Meta retries deliveries it thinks
   failed, and a customer should not get two replies to one question.
2. STOP is honoured before anything else, without asking a model. After it the
   customer is not tagged and gets no replies until they send START.
3. Once a conversation is handed to a person, the bot stays quiet for
   QUIET_HOURS, so the customer is not told "someone will follow up" on every
   message while that someone is typing.
4. A message the tagger or the model cannot handle still gets a safe reply:
   reply.answer always returns something sendable, and a voice note or photo
   hands over rather than being ignored.
"""

import hashlib
import json
import os
import tempfile
from datetime import datetime, timedelta

from nudgely.reply import HOLDING

QUIET_HOURS = 12
KEEP_SEEN = 200          # message ids remembered per conversation, for retries
STOP_WORDS = {"stop", "stop all", "unsubscribe", "cancel", "opt out", "optout"}
START_WORDS = {"start", "unstop", "subscribe"}
STOPPED = "Done - you won't get any more messages from us. Reply START if you change your mind."
RESTARTED = "Welcome back! You'll hear from us again. Reply STOP anytime to opt out."


class Store:
    """Conversations keyed by WhatsApp number, kept in one JSON file.

    The file holds real customers' messages, so it is git-ignored. Writes go to a
    temporary file first, so a crash mid-write cannot leave half a file behind.
    """

    def __init__(self, path):
        self.path = path
        self.data = {}
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)

    def get(self, number):
        return self.data.get(number)

    def put(self, number, conversation):
        self.data[number] = conversation
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(self.path) or ".", suffix=".tmp")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, self.path)

    def clear_handover(self, number):
        conversation = self.get(number)
        if not conversation:
            return False
        conversation["handover_until"] = ""
        conversation["handover_reason"] = ""
        self.put(number, conversation)
        return True


def customer_id_for(number):
    """A stable id that does not put the phone number in front of the LLM."""
    return "WA-" + hashlib.sha256(str(number).encode()).hexdigest()[:8]


def new_conversation(number, name, seed=None):
    """A first-time sender. `seed` is a known customer (name, label, chat, tags) to start from."""
    seed = seed or {}
    return {
        "customer": {"customer_id": seed.get("customer_id") or customer_id_for(number),
                     "name": seed.get("name") or name or "",
                     "label": seed.get("label", "")},       # unknown label: no discounts offered
        "chat": list(seed.get("chat", [])),
        "tags": seed.get("tags") or {},
        "replied": False,
        "opted_out": False,
        "handover_until": "",
        "handover_reason": "",
        "seen": [],
        "log": [],
    }


def handle(msg, store, tag, answer, send, known=None, now=None, dry_run=False):
    """Process one parsed webhook message. Returns a summary for the console.

    tag(customer_id, text, date, prior, names) -> extraction   (llm.tag_message)
    answer(customer, chat, text, tags, first_reply) -> {reply, handover, reason}   (reply.answer)
    send(number, text) -> anything; raises on failure
    known(number) -> seed dict or None, for numbers mapped to an existing customer
    """
    now = now or datetime.now()
    number = str(msg.get("from") or "")
    text = str(msg.get("text") or "").strip()
    when = _when(msg.get("timestamp"), now)

    conversation = store.get(number) or new_conversation(number, msg.get("name"), known(number) if known else None)
    if msg.get("id") and msg["id"] in conversation["seen"]:
        return {"action": "duplicate, ignored"}
    conversation["seen"] = (conversation["seen"] + [msg.get("id")])[-KEEP_SEEN:]
    if msg.get("name") and not conversation["customer"]["name"]:
        conversation["customer"]["name"] = msg["name"]

    history = list(conversation["chat"])
    conversation["chat"].append({"date": when, "from": "customer",
                                 "text": text or f"[{msg.get('type') or 'message'} with no text]"})
    customer = conversation["customer"]
    result = {"action": "", "handover": False, "reason": "", "reply": "", "tags_added": 0}

    def finish(action, reply="", handover=False, reason=""):
        reason = "; ".join(r for r in (reason, result["reason"]) if r)   # keep a tagging failure visible
        result.update(action=action, reply=reply, handover=handover, reason=reason)
        if reply:
            if dry_run:
                result["action"] += " (dry run, not sent)"
            else:
                try:
                    send(number, reply)
                    conversation["chat"].append({"date": when, "from": "store", "text": reply})
                    conversation["replied"] = True
                except Exception as e:  # noqa: BLE001 - keep the record, report the failure
                    result["action"] = f"send failed: {str(e)[:160]}"
        if handover:
            conversation["handover_until"] = (now + timedelta(hours=QUIET_HOURS)).isoformat(timespec="seconds")
            conversation["handover_reason"] = reason
        conversation["log"] = (conversation["log"] + [{"at": now.isoformat(timespec="seconds"),
                                                       "action": result["action"], "reason": reason}])[-50:]
        store.put(number, conversation)
        return result

    words = text.lower().strip(" .!")
    if words in STOP_WORDS:
        conversation["opted_out"] = True
        return finish("opted out", STOPPED)
    if words in START_WORDS and conversation["opted_out"]:
        conversation["opted_out"] = False
        return finish("opted back in", RESTARTED)
    if conversation["opted_out"]:
        return finish("opted out earlier, no reply")

    if text:
        try:
            new = tag(customer["customer_id"], text, when, conversation["tags"], [customer["name"]])
            before = len(conversation["tags"].get("tags", []))
            conversation["tags"] = tag_and_merge(conversation["tags"], new)
            result["tags_added"] = len(conversation["tags"]["tags"]) - before
        except Exception as e:  # noqa: BLE001 - a missed tag must not cost the customer a reply
            result["reason"] = f"tagging failed: {str(e)[:120]}"

    if conversation["handover_until"] and conversation["handover_until"] > now.isoformat(timespec="seconds"):
        return finish("with a person, bot quiet", reason=conversation["handover_reason"])

    if not text:
        return finish("handed over", HOLDING, True,
                      f"Customer sent a {msg.get('type') or 'message'} the bot cannot read.")

    out = answer(customer, history, text, conversation["tags"], not conversation["replied"])
    return finish("handed over" if out.get("handover") else "replied", out.get("reply", ""),
                  bool(out.get("handover")), out.get("reason", ""))


def tag_and_merge(prior, new):
    from nudgely.llm import merge_tags
    return merge_tags(prior, new)


def _when(timestamp, now):
    try:
        return datetime.fromtimestamp(int(timestamp)).date().isoformat()
    except (TypeError, ValueError, OSError):
        return now.date().isoformat()

"""One conversation turn, the same for WhatsApp and the web chat.

`handle()` remembers the message, tags it, decides the reply (or a handover to a person), and
returns what to send. It never sends anything itself: the WhatsApp webhook sends with the Cloud
API, the web chat returns the reply in the HTTP response.

Rules (same on every channel):
- STOP / START opt out and back in; nothing is answered automatically while opted out
- photos, stickers and voice notes go to a person
- the reply bot never invents stock, prices or offers, and hands over when unsure (see reply.py)
- a repeated message id (Meta retries) is answered once
"""

from nudgely import conversations, supabase_sync

STOP_REPLY = "You won't get any more messages from us. Reply START if you change your mind."
START_REPLY = "Welcome back! You'll hear from us again. Reply STOP anytime to opt out."


def handle(key, name, text, msg_id=None, prefix="WA", kind="text", max_messages=None):
    """Process one incoming message. Returns a dict:

    {"customer_id", "reply" (str or None = send nothing), "handover", "opted_out",
     "new_tags" [{"type", "value", "evidence"}], "duplicate", "limited", "reason"}

    `max_messages` caps how many messages one visitor can send (the judges' web chat);
    over the cap nothing is stored or answered and "limited" is True.
    """
    from nudgely import reply as replybot
    from nudgely.llm import merge_tags, tag_message

    rec = conversations.get_or_create(key, name, prefix=prefix)
    out = {"customer_id": rec["customer_id"], "reply": None, "handover": False,
           "opted_out": rec.get("opted_out", False), "new_tags": [], "duplicate": False,
           "limited": False, "reason": ""}
    if max_messages is not None and rec.get("msg_count", 0) >= max_messages:
        out["limited"] = True
        return out
    rec["msg_count"] = rec.get("msg_count", 0) + 1
    if msg_id:
        if msg_id in rec["seen_ids"]:
            out["duplicate"] = True
            return out
        rec["seen_ids"].append(msg_id)
    today = conversations.today()
    before = len(rec["chat"])

    def finish():
        if out["reply"]:
            rec["chat"].append({"from": "store", "text": out["reply"], "date": today})
        conversations.update(key, rec)
        # In Supabase mode the database *is* the history, so write before the next message can arrive.
        supabase_sync.sync(rec, rec["chat"][before:], out["new_tags"], handover_reply=out["handover"],
                           wait=conversations.remote())
        out["opted_out"] = rec.get("opted_out", False)
        return out

    if kind != "text" or not text:
        rec["chat"].append({"from": "customer", "text": f"[{kind}]", "date": today})
        rec["handover"] = out["handover"] = True
        out["reason"] = f"{kind} message, flagged for a person"
        return finish()

    rec["chat"].append({"from": "customer", "text": text, "date": today})

    if conversations.is_stop(text):
        rec["opted_out"] = True
        out["reply"], out["reason"] = STOP_REPLY, "opted out"
        return finish()
    if conversations.is_start(text):
        rec["opted_out"] = False
        out["reply"], out["reason"] = START_REPLY, "opted back in"
        return finish()
    if rec.get("opted_out"):  # said STOP: keep what they sent, never answer automatically
        out["reason"] = "opted out, not answered"
        return finish()

    first = rec["name"].split()[0] if rec.get("name") else ""
    try:
        new = tag_message(rec["customer_id"], text, date=today, prior=rec.get("tags"),
                          names=[rec.get("name", "")])
        rec["tags"] = merge_tags(rec.get("tags"), new)
        out["new_tags"] = [{k: t.get(k) for k in ("type", "value", "evidence")} for t in new.get("tags", [])]
    except Exception as e:  # noqa: BLE001 - tagging failing must not stop the reply
        out["reason"] = f"tagging failed: {str(e)[:80]}; "

    customer = {"customer_id": rec["customer_id"], "name": first, "label": rec.get("label", "New")}
    answer = replybot.answer(customer, rec["chat"][:-1], text, tags=rec.get("tags"),
                             first_reply=not rec.get("replied"))
    out["reply"] = answer["reply"]
    out["handover"] = bool(answer.get("handover"))
    out["reason"] += answer.get("reason", "")
    rec["replied"] = True
    if out["handover"]:
        rec["handover"] = True
    return finish()

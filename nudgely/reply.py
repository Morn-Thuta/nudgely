"""The reply bot: answer a customer's incoming message, or hand it to a person.

Nudgely's outbound messages start conversations. This answers them. Different
job, so it gets its own instructions: an outbound draft is reviewed by the owner
before it sends, while a reply goes out on its own, and the shop carries whatever
it says.

Two layers of safety, because the first one is not reliable on its own:

1. The prompt tells the model to hand over when it is unsure.
2. `review_reply` checks what came back and hands over anyway when the reply
   invents something, breaks a rule, or does not engage with what was asked.

An LLM producing nonsense is in no position to notice it is producing nonsense,
so step 2 is what actually holds. Call `answer` and send `reply`; when it returns
`handover: True`, route the conversation to a person as well.

`reply` is always safe to send. On handover it is replaced with a neutral holding
line and the model's untrusted attempt is moved to `draft` for the owner to read,
so a caller that forgets to check `handover` cannot leak an invented price.
"""

import json
import re
from difflib import SequenceMatcher

from nudgely.llm import STORE_INFO, complete_json, scrub
from nudgely.verify import verify_message

MAX_CHARS = 300
OPT_OUT = "Reply STOP to opt out"

# What a customer gets whenever we hand over. The untrusted draft is kept under
# `draft` for the shop owner to read, never under `reply`, so a caller that sends
# `reply` without checking `handover` still cannot send invented information.
HOLDING = "Thanks for your message - someone from the shop will follow up shortly."

# The advertised way to reach a person. A keyword is checked exactly, so it cannot
# be missed the way a phrase can; the phrases stay as a safety net for customers
# who never saw the instruction.
HUMAN_KEYWORD = "HUMAN"
HUMAN_HINT = f"Reply {HUMAN_KEYWORD} anytime to talk to someone"
HUMAN_PHRASES = ["speak to a", "speak with a", "talk to a", "talk to someone", "real person",
                 "a human", "someone real", "your manager", "the owner", "call me",
                 "customer service", "是真人", "找人"]

REPLY_SYSTEM = f"""You are the assistant for {STORE_INFO['name']}, a {STORE_INFO['type']}.
A customer has replied to a message from the shop. Write ONE short reply, or hand over to a person.

WHAT YOU MAY USE
- The customer's chat history, given below.
- The shop information given below: stock, delivery terms, current offers.
- Nothing else. If you do not know, do not guess.
- Customers often misspell or run words together ("durain", "oakmilk", "instock"). If a word
  clearly means an item in the stock list, treat it as that item and use the correct name.
- If asked what is in stock, list items from the stock list.

NEVER
- Name a product, price, offer or delivery term that is not in the shop information.
- Promise a date, a reservation, a refund or a stock arrival.
- Offer a discount above 10%, or any discount to a customer not labelled Persuadable.
- Argue with a complaint or explain why the shop was right.

HAND OVER TO A PERSON (set handover true) WHEN
- The customer asks to speak to a person. Always, immediately. Do not try to handle it yourself.
- You do not have the information to answer.
- You are not confident the answer is correct. Hand over rather than guess.
- The customer is angry, asks for a refund, or reports a problem with an order.
- The customer asks to be removed from the list.
When you hand over, the reply should be one short line saying a person from the shop will follow
up. Do not answer the question as well.

TONE
Warm and plain, like a shop that knows them. Singapore English is fine; heavy slang is not.
Under {MAX_CHARS} characters. At most one emoji. No hashtags. Do not open with a headline.

Return ONLY a JSON object:
{{"reply": "...", "handover": true or false, "reason": "one line for the shop owner"}}"""


def answer(customer, chat, incoming, tags=None, first_reply=True):
    """Draft a reply to `incoming`. Returns the reply dict with `handover` decided.

    `first_reply` adds the opt-out line, which belongs on the first reply in a
    conversation and becomes noise if repeated on every turn.
    """
    names = [str(customer.get("name", ""))]
    history = [f"[{m.get('date', '')}] {m['from']}: {scrub(m['text'], names)}" for m in chat]
    user = json.dumps({
        "first_name": str(customer.get("name", "")).split()[0] if customer.get("name") else "",
        "label": customer.get("label", ""),
        "chat_history": history,
        "their_new_message": scrub(incoming, names),
        "what_we_remembered": tags or {},
        "STORE_INFO": STORE_INFO,
    }, default=str)

    if asked_for_a_person(incoming):  # never leave this to the model's judgement
        return {"reply": f"Of course - someone from {STORE_INFO['name']} will get back to you shortly.",
                "handover": True, "reason": "Customer asked to speak to a person."}

    try:
        out = complete_json(REPLY_SYSTEM, user)
    except Exception as e:  # noqa: BLE001 - no reply is better than a broken one
        return {"reply": "Thanks for your message - someone from the shop will follow up shortly.",
                "handover": True, "reason": f"Could not generate a reply: {str(e)[:120]}"}

    return review_reply(out, customer, chat, incoming, tags, first_reply)


def asked_for_a_person(text):
    """The keyword on its own line or as the whole message, or a phrase asking for one."""
    raw = str(text).strip()
    words = re.findall(r"[a-z]+", raw.lower())
    if HUMAN_KEYWORD.lower() in words and len(words) <= 4:
        return True
    return any(phrase in raw.lower() for phrase in HUMAN_PHRASES)


def review_reply(out, customer, chat, incoming, tags=None, first_reply=True):
    """Check the model's reply and hand over if it cannot be trusted to send."""
    reply = str(out.get("reply", "")).strip()
    out["reply"] = reply
    out.setdefault("reason", "")

    def hand_over(why):
        out["handover"] = True
        out["reason"] = why
        if reply and reply != HOLDING:
            out["draft"] = reply  # for the owner to read, not to send
        out["reply"] = HOLDING
        return out

    if out.get("handover"):
        # The model handed over of its own accord. Its line is usually a clean
        # "someone will follow up", but it is unreviewed, so it gets the same
        # checks as any other reply before a customer can see it.
        out["handover"] = True
        if not reply or len(reply) > MAX_CHARS or _invents(reply, chat, tags):
            return hand_over(out["reason"] or "Handed over with a reply that could not be sent.")
        return out
    if not reply:
        return hand_over("Model returned an empty reply.")
    if len(reply) > MAX_CHARS:
        return hand_over(f"Reply was {len(reply)} characters, over the {MAX_CHARS} limit.")
    if "#" in reply:
        return hand_over("Reply contained a hashtag.")

    percentages = [int(p) for p in re.findall(r"(\d+)\s*%", reply)]
    if percentages and customer.get("label") != "Persuadable":
        return hand_over("Offered a discount to a customer who is not Persuadable.")
    if any(p > 10 for p in percentages):
        return hand_over("Offered a discount above 10%.")

    invented = _invents(reply, chat, tags)
    if invented:
        return hand_over("Reply claims something the chat and shop info do not support: " + invented)

    if not _engages_with(reply, incoming):
        return hand_over("Reply does not pick up anything the customer actually said.")

    out["handover"] = False
    if first_reply:
        tail = [t for t in (HUMAN_HINT, OPT_OUT) if t.lower() not in reply.lower()]
        while tail and len(reply) + sum(len(t) + 2 for t in tail) > MAX_CHARS:
            tail.pop(0)  # the opt-out line is the one that must survive
        if tail:
            out["reply"] = reply + " " + ". ".join(tail)
    return out


def _invents(reply, chat, tags):
    """The first thing the reply claims that the chat and shop info do not support.

    The grounding check compares against extracted evidence, which is about the
    outbound message rather than this reply, so only the invention checks apply.
    """
    warnings = [w for w in verify_message(reply, chat, tags or {})
                if "shares no wording" not in w]
    return warnings[0] if warnings else None


def _engages_with(reply, incoming):
    """A reply that shares no meaningful word with the question is usually drift.

    Customers misspell and run words together ("durain", "oakmilk", "instock"), so a word
    counts as shared when it is the same, a near spelling, or contains / is contained in a
    word of 4+ letters from the other side.
    """
    stop = {"the", "and", "you", "your", "for", "are", "can", "have", "this", "that", "with",
            "what", "when", "how", "any", "got", "will", "our", "please", "thanks", "hello",
            # chatty filler that names no topic ("so what do you guys have?")
            "guys", "guy", "lah", "leh", "lor", "hey", "okay", "still", "now", "today", "just",
            "want", "need", "also", "there", "here", "they", "yeah", "yes", "sell",
            "available", "anything", "else", "other", "things",
            # follow-ups that point back at the last message ("is it really available now?")
            "really", "actually", "sure", "true", "right", "confirm", "real", "seriously"}
    asked = {w for w in re.findall(r"[a-z]{3,}", str(incoming).lower())} - stop
    said = {w for w in re.findall(r"[a-z]{3,}", reply.lower())} - stop
    if not asked:
        return True
    asked |= {w[:-1] for w in asked if w.endswith("s")}
    said |= {w[:-1] for w in said if w.endswith("s")}
    return any(_same_word(a, s) for a in asked for s in said)


def _same_word(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) >= 4 and (a in b or b in a):  # "instock" ~ "stock", "oakmilk" ~ "milk"
        return True
    return min(len(a), len(b)) >= 5 and SequenceMatcher(None, a, b).ratio() >= 0.8  # "durain" ~ "durian"

"""WhatsApp templates: six fixed sentences, and filling their blanks safely.

WhatsApp will not let a business start a conversation with free text. Meta
approves a fixed sentence with numbered blanks, and only the blanks may change:

    Hi {{1}}, good news - the {{2}} you asked about is back in stock. ...

So the outbound message cannot be written the way `llm.write_message` writes it.
The model's job shrinks to filling blanks, and `render` substitutes them
mechanically, which means the approved words are not something the model can
alter even if it tries.

That shrinking is the point. The model can still invent a product in a blank, so
`review_fill` runs the same evidence checks as the rest of the pipeline, and a
template whose blanks cannot be filled safely is simply not sent.

Replies are not affected. Once a customer answers, WhatsApp allows 24 hours of
free text, which is what `nudgely.reply` handles.

One template per tag type, so a customer's strongest tag decides which is used.
Each shop submits its own copies, because the fixed text names the shop.
"""

import json
import re

from nudgely.llm import STORE_INFO, TAG_TYPES, check_message, complete_json, scrub
from nudgely.verify import verify_message

MAX_CHARS = 300
OPT_OUT = "Reply STOP to opt out"
BLANK = re.compile(r"\{\{(\d+)\}\}")

SHOP = STORE_INFO["name"]

# A blank's description is what the model is told to put there, so it is written
# as an instruction rather than a label.
NAME_BLANK = "the customer's first name, exactly as given, nothing else"
CLOSE_BLANK = ("one short sentence in the shop's voice that ends with a question inviting a reply. "
               "It must follow from the chat. No prices, dates or offers that are not in STORE_INFO")

TEMPLATES = {
    "restock": {
        "tag": "restock_request",
        "text": f"Hi {{{{1}}}}, good news - the {{{{2}}}} you asked about is back in stock at {SHOP}. {{{{3}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": "the item they asked about, named as the chat or STORE_INFO names it",
            "3": CLOSE_BLANK,
        },
    },
    "delivery_complaint": {
        "tag": "complaint_delivery",
        "text": f"Hi {{{{1}}}}, we're sorry about {{{{2}}}}. {{{{3}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": "what actually went wrong, in a few words, taken from the chat. No excuses, no blame",
            "3": ("one short sentence putting it right or asking how to, ending in a question. "
                  "Do not argue, do not explain why the shop was right, do not push a sale"),
        },
    },
    "price_complaint": {
        "tag": "complaint_price",
        "text": f"Hi {{{{1}}}}, thanks for the honest feedback on our prices. {{{{2}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": ("one short sentence that takes the feedback seriously and ends in a question. "
                  "Only mention an offer if it is in STORE_INFO current_offers and the label allows it"),
        },
    },
    "event": {
        "tag": "upcoming_event",
        "text": f"Hi {{{{1}}}}, you mentioned {{{{2}}}} coming up. {{{{3}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": "the event they mentioned, in a few words, as the chat describes it",
            "3": CLOSE_BLANK + ". Offer help with the event rather than a general promotion",
        },
    },
    "product_interest": {
        "tag": "product_interest",
        "text": f"Hi {{{{1}}}}, we've got {{{{2}}}} in today. {{{{3}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": "an item from STORE_INFO in_stock_now that they have shown interest in",
            "3": CLOSE_BLANK,
        },
    },
    "regular": {
        "tag": "loyal_regular",
        "text": f"Hi {{{{1}}}}, time for your usual {{{{2}}}}? {{{{3}}}} {OPT_OUT}",
        "blanks": {
            "1": NAME_BLANK,
            "2": "what they usually buy, from the chat or their tags",
            "3": CLOSE_BLANK,
        },
    },
}

# Which template wins when a customer has several tags. A complaint outranks
# everything: answering a complaint with a promotion is the worst thing we can
# send, and the PRD already forbids it for free-text messages.
PRIORITY = ["delivery_complaint", "price_complaint", "restock", "event",
            "product_interest", "regular"]

TAG_TO_TEMPLATE = {spec["tag"]: name for name, spec in TEMPLATES.items()}

FILL_SYSTEM = """You fill the blanks in an approved WhatsApp template for a Singapore grocery store.

You are NOT writing the message. The sentence is fixed and already approved; you only supply the
blanks. You will be given the template, what each blank must contain, the customer's chat history,
their remembered tags, and the shop's information.

RULES
- Use only the chat history and STORE_INFO. If you do not know, say so by returning "skip".
- Never name a product, price, delivery term or offer that is not in STORE_INFO or the chat.
- Never promise a date, a reservation, a refund or a stock arrival.
- A discount may only be mentioned if the label is "Persuadable", and never above 10%.
- Each blank is plain text on one line: no newlines, no tabs, no "{{" or "}}", no emoji in blank 1.
- Keep blanks short. The whole filled message must stay under 300 characters.
- Do not repeat the shop name or the opt-out line; they are already in the fixed text.

If the chat does not support this template, return {"skip": "one line saying why"} instead.

Return ONLY a JSON object:
{"values": {"1": "...", "2": "..."}, "reason": "one short line for the shop owner"}"""


def choose(tags, available=None):
    """Which template to use for a customer's tags, or None if none fits.

    `tags` is either an extraction dict or a list of tag dicts. `available`
    optionally limits the choice to templates Meta has actually approved.
    """
    types = {t.get("type") for t in _tag_list(tags)}
    allowed = set(available) if available else set(TEMPLATES)
    for name in PRIORITY:
        if name in allowed and TEMPLATES[name]["tag"] in types:
            return name
    return None


def _tag_list(tags):
    if isinstance(tags, dict):
        return tags.get("tags", []) or []
    return list(tags or [])


def blanks_in(template_id):
    """The blank numbers the template actually uses, in order."""
    return BLANK.findall(TEMPLATES[template_id]["text"])


def render(template_id, values):
    """Substitute blanks into the fixed text.

    Mechanical on purpose: the approved words are copied from TEMPLATES, never
    from anything the model returned, so the fixed part cannot be altered.
    """
    text = TEMPLATES[template_id]["text"]
    missing = [n for n in blanks_in(template_id) if not str(values.get(n, "")).strip()]
    if missing:
        raise ValueError(f"{template_id} needs blanks {missing}")
    for number in blanks_in(template_id):
        text = text.replace("{{%s}}" % number, str(values[number]).strip())
    return re.sub(r"\s+", " ", text).strip()


def fill(customer, extraction, template_id=None, available=None):
    """Pick a template and fill it for one customer.

    Returns {customer_id, template, message, values, tags_used, reason, ok,
    problems}. `ok` is False when nothing safe could be produced, and then
    `message` is empty: there is no partial result worth sending.
    """
    cid = customer.get("customer_id", "")
    template_id = template_id or choose(extraction, available)
    if not template_id:
        return _failed(cid, None, "No tag matches an approved template.")

    name = str(customer.get("name", ""))
    first_name = name.split()[0] if name else ""
    spec = TEMPLATES[template_id]
    chat = customer.get("chat", []) or []
    history = [f"[{m.get('date', '')}] {m['from']}: {scrub(m['text'], [name])}" for m in chat]

    user = json.dumps({
        "template": spec["text"],
        "what_each_blank_must_contain": spec["blanks"],
        "first_name": first_name,
        "label": customer.get("label", ""),
        "chat_history": history,
        "what_we_remembered": extraction,
        "STORE_INFO": STORE_INFO,
    }, default=str)

    try:
        out = complete_json(FILL_SYSTEM, user)
    except Exception as e:  # noqa: BLE001 - no message is better than a wrong one
        return _failed(cid, template_id, f"Could not reach the LLM: {str(e)[:120]}")

    return review_fill(out, customer, extraction, template_id)


def review_fill(out, customer, extraction, template_id):
    """Check the blanks the model returned, then render. Rejects rather than repairs."""
    cid = customer.get("customer_id", "")
    tag = TEMPLATES[template_id]["tag"]
    reason = str(out.get("reason", "")).strip()

    if out.get("skip"):
        return _failed(cid, template_id, f"Model skipped: {str(out['skip'])[:160]}")

    values = out.get("values") or {}
    if not isinstance(values, dict):
        return _failed(cid, template_id, "Model did not return a values object.")
    values = {str(k): str(v) for k, v in values.items()}

    problems = _check_blanks(template_id, values, customer)
    if problems:
        return _failed(cid, template_id, "; ".join(problems), values=values, reason=reason)

    try:
        text = render(template_id, values)
    except ValueError as e:
        return _failed(cid, template_id, str(e), values=values, reason=reason)

    # The template is chosen by one tag, and that is the tag the message rests on.
    message = {"customer_id": cid, "message": text, "tags_used": [tag], "reason": reason}

    problems = check_message(message, customer.get("label", ""))
    if "?" not in text:
        # Every template asks something. A message with nothing to answer tells us
        # nothing about whether the customer is coming back, which is the point.
        problems.append("asks the customer nothing")
    invented = [w for w in verify_message(text, customer.get("chat", []) or [], extraction)
                if "shares no wording" not in w]
    problems += invented
    if problems:
        return _failed(cid, template_id, "; ".join(problems), values=values, reason=reason)

    message.update(template=template_id, values=values, ok=True, problems=[])
    return message


def _check_blanks(template_id, values, customer):
    """Rules about the blanks themselves, before anything is rendered."""
    problems = []
    expected = blanks_in(template_id)
    extra = sorted(set(values) - set(expected))
    if extra:
        problems.append(f"returned blanks the template does not have: {extra}")

    for number in expected:
        value = values.get(number, "").strip()
        if not value:
            problems.append(f"blank {number} is empty")
            continue
        if BLANK.search(value) or "{{" in value or "}}" in value:
            problems.append(f"blank {number} contains template syntax")
        if any(ch in value for ch in "\n\r\t"):
            problems.append(f"blank {number} contains a line break")
        if len(value) > 140:
            problems.append(f"blank {number} is {len(value)} characters, too long for a variable")
        if OPT_OUT.lower() in value.lower():
            problems.append(f"blank {number} repeats the opt-out line")

    name = str(customer.get("name", ""))
    first_name = name.split()[0] if name else ""
    if "1" in expected and first_name and values.get("1", "").strip() != first_name:
        problems.append(f"blank 1 is '{values.get('1', '')}', not the customer's first name")

    filled = " ".join(values.get(n, "") for n in expected)

    # Shouting is how a model pads a blank it has nothing to put in, and it is the
    # opposite of the tone the shop agreed to. SHOP is allowed; it is the shop's name.
    shouted = [w for w in re.findall(r"\b[A-Z]{3,}\b", filled)
               if w not in {"SHOP", OPT_OUT.upper()} and w.lower() not in SHOP.lower()]
    if shouted:
        problems.append(f"blank text shouts in capitals: {shouted}")

    # "Free" anything is a promise the shop has to keep, so it must already be a
    # term the shop offers. Catches "FREE DURIAN", allows "free delivery".
    store_low = (STORE_INFO["delivery"] + " " + " ".join(STORE_INFO["in_stock_now"])
                 + " " + " ".join(STORE_INFO["current_offers"])).lower()
    for phrase in re.findall(r"free[\s-]+(\w+)", filled.lower()):
        if f"free {phrase}" not in store_low and f"free-{phrase}" not in store_low:
            problems.append(f"offers 'free {phrase}', which is not one of the shop's terms")

    percentages = [int(p) for p in re.findall(r"(\d+)\s*%", " ".join(values.values()))]
    if percentages and customer.get("label") != "Persuadable":
        problems.append("offers a discount to a customer who is not Persuadable")
    if any(p > 10 for p in percentages):
        problems.append("offers a discount above 10%")
    return problems


def _failed(cid, template_id, why, values=None, reason=""):
    return {"customer_id": cid, "template": template_id, "message": "", "values": values or {},
            "tags_used": [], "reason": reason, "ok": False, "problems": [why]}


def approved_sentences():
    """The six sentences to submit to Meta, in the order they appear above."""
    return [{"name": name, "tag": spec["tag"], "text": spec["text"]}
            for name, spec in TEMPLATES.items()]

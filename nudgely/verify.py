"""Check a drafted message against the evidence it is allowed to use.

`check_message` in llm.py covers the hard rules (length, opt-out, discount cap).
This goes one level deeper: every concrete claim in the message must trace back
to that customer's own chat or to STORE_INFO. The LLM writes fluently whether or
not it has grounds, so these are the mistakes a human reviewer actually catches.

Returns a list of warnings. Empty means nothing suspicious; a warning is a
prompt to look, not proof of a mistake.
"""

import re

from nudgely.llm import STORE_INFO

# Phrases that assert a live order exists. The chats are past conversations, so
# a draft can offer to pack an order but cannot announce one is already waiting.
STATE_CLAIMS = [
    "is ready", "are ready", "ready for pickup", "ready for collection",
    "is reserved", "we have reserved", "is packed", "we have packed",
    "confirming your", "on the way", "out for delivery", "has shipped",
]

STOCK_PHRASES = ["in stock", "back in stock", "just arrived", "came in", "is in", "are in", "restocked"]

MONTHS = "jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec"


def _store_text():
    parts = [STORE_INFO["name"], STORE_INFO["type"], STORE_INFO["delivery"]]
    parts += STORE_INFO["in_stock_now"] + STORE_INFO["current_offers"]
    return " ".join(parts).lower()


def _chat_text(chat):
    return " ".join(m["text"] for m in chat).lower()


def _amounts(text):
    """Money and percentages, normalised: '$12' -> '$12', '10 %' -> '10%'."""
    return {m.replace(" ", "") for m in re.findall(r"\$\s?\d+(?:\.\d+)?|\d+\s?%", text)}


VAGUE = {"fresh", "seasonal", "now", "our", "own", "and", "the", "packs"}


def _names_a_stocked_item(low):
    """True if the message names something from the shop's stock list."""
    for item in STORE_INFO["in_stock_now"]:
        words = {w for w in re.findall(r"[a-z]{3,}", item.split("(")[0].lower())} - VAGUE
        if words and words <= set(re.findall(r"[a-z]{3,}", low)):
            return True
    return False


def verify_message(message, chat, tags):
    """Warnings about claims the chat and STORE_INFO do not support."""
    text = message if isinstance(message, str) else message.get("message", "")
    low = text.lower()
    chat_low = _chat_text(chat)
    store_low = _store_text()
    allowed = chat_low + " " + store_low
    warnings = []

    # 1. Money and percentages must come from the shop's terms or the chat.
    for amount in _amounts(text):
        if amount.replace("$", "").replace("%", "") in ("",):
            continue
        if amount not in _amounts(allowed):
            warnings.append(f"amount {amount} appears in neither the chat nor STORE_INFO")

    # 2. A date in the message must be a date the chat actually carries.
    chat_dates = {m.get("date", "") for m in chat}
    months_in_chat = {d[5:7] for d in chat_dates if len(d) >= 7}
    for month, day in re.findall(rf"({MONTHS})[a-z]*\s+(\d{{1,2}})", low):
        num = {"jan": "01", "feb": "02", "mar": "03", "apr": "04", "may": "05", "jun": "06",
               "jul": "07", "aug": "08", "sep": "09", "oct": "10", "nov": "11", "dec": "12"}[month]
        if num not in months_in_chat:
            warnings.append(f"date '{month} {day}' is not a date in this chat")
        elif not any(d.endswith(f"-{int(day):02d}") for d in chat_dates):
            warnings.append(f"day '{month} {day}' does not match any chat date ({sorted(chat_dates)})")

    # 3. Claims that an order is already packed, reserved or on its way.
    for phrase in STATE_CLAIMS:
        if phrase in low:
            warnings.append(f"claims a live order ('{phrase}') - the chat is a past conversation")

    # 4. Anything described as in stock should be something the shop stocks.
    if any(p in low for p in STOCK_PHRASES) and not _names_a_stocked_item(low):
        warnings.append("says something is in stock but names nothing from STORE_INFO")

    # 5. The shop's two delivery terms are separate: same-day needs orders before
    # 2pm, free needs orders above $50. Merging them invents an offer.
    if re.search(r"same[- ]day\s+delivery\s+(?:applies\s+)?(?:to|for|on)?\s*(?:orders?\s+)?"
                 r"(?:above|over|more than)\s*\$", low):
        warnings.append("ties same-day delivery to a dollar threshold - same-day is 'before 2pm', "
                        "the threshold is for free delivery")

    # 6. The message should actually use the evidence that was extracted.
    evidence = " ".join(t.get("evidence", "") for t in tags.get("tags", [])).lower()
    if evidence:
        words = {w for w in re.findall(r"[a-z]{3,}", evidence)} - {
            "that", "this", "with", "have", "when", "your", "they", "them", "from", "here", "been", "what"}
        if words and not (words & set(re.findall(r"[a-z]{3,}", low))):
            warnings.append("shares no wording with the quoted evidence - may not be grounded in the chat")

    return warnings

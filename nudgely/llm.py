"""One tiny LLM wrapper + the two Nudgely prompts (PRD "LLM spec").

Provider is picked by LLM_PROVIDER = openrouter | anthropic | openai | gemini, key in LLM_API_KEY,
model in LLM_MODEL. openrouter needs no SDK; the others need theirs (anthropic / openai / google-genai).
"""

import json
import os
import re

TAG_TYPES = ["restock_request", "complaint_delivery", "complaint_price",
             "upcoming_event", "product_interest", "loyal_regular"]

STORE_INFO = {
    "name": "Kampung Fresh",
    "type": "neighbourhood grocer in Tampines, Singapore",
    "delivery": "same-day delivery for orders before 2pm, free above $50",
    "in_stock_now": ["oat milk", "free-range eggs", "durian (seasonal)", "Thai jasmine rice", "fresh kai lan",
                     "Pokka green tea", "Gardenia bread", "frozen dumplings", "party snack packs ($12 and $20)",
                     "Deepavali ghee and spice packs"],
    "current_offers": ["up to 10% off next order (Persuadable customers only)",
                       "free delivery this week for orders above $30"],
}

EXTRACT_SYSTEM = f"""You read a grocery store's chat history with one customer and extract memory tags.
Return ONLY a JSON object with keys:
customer_id, tags (list of {{type, value, evidence, date}}), sentiment (positive|neutral|negative),
open_promise (string, "" if none), best_hook (short string), avoid (string, "" if none).
Allowed tag types: {", ".join(TAG_TYPES)}.
Every tag MUST quote evidence copied word-for-word from a customer or store message. Drop any tag without evidence.
Do not invent anything not in the chat."""

WRITE_SYSTEM = """You write ONE short WhatsApp message from a Singapore grocery store to a customer.
Rules:
- Max 300 characters in total, friendly Singapore tone, at most one emoji.
- Lead with best_hook. Use at least one tag. Never invent stock, prices or offers not in STORE_INFO.
- Respect "avoid". If there is a complaint tag, apologise first and do not push a sale.
- Offer a discount ONLY if label is "Persuadable", and never above 10%.
- End with exactly: "Reply STOP to opt out"
Return ONLY a JSON object: {"customer_id", "message", "tags_used": [tag types], "reason": one short line for the owner}."""


def _config():
    cfg = {"provider": os.getenv("LLM_PROVIDER", ""), "api_key": os.getenv("LLM_API_KEY", ""),
           "model": os.getenv("LLM_MODEL", "")}
    try:
        import streamlit as st

        s = st.secrets.get("llm", {})
        cfg = {k: s.get(k) or v for k, v in cfg.items()}
    except Exception:
        pass
    return cfg


def available():
    c = _config()
    return bool(c["provider"] and c["api_key"])


def _parse_json(text):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0) if m else text)


def complete_json(system, user):
    c = _config()
    provider, key, model = c["provider"].lower(), c["api_key"], c["model"]
    if not (provider and key):
        raise RuntimeError("LLM not configured: set LLM_PROVIDER and LLM_API_KEY")

    if provider == "anthropic":
        import anthropic

        r = anthropic.Anthropic(api_key=key).messages.create(
            model=model or "claude-haiku-5-5", max_tokens=800, system=system,
            messages=[{"role": "user", "content": user}])
        return _parse_json(r.content[0].text)

    if provider == "openai":
        from openai import OpenAI

        r = OpenAI(api_key=key).chat.completions.create(
            model=model or "gpt-4o-mini", response_format={"type": "json_object"},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return _parse_json(r.choices[0].message.content)

    if provider == "gemini":
        from google import genai
        from google.genai import types

        r = genai.Client(api_key=key).models.generate_content(
            model=model or "gemini-2.5-flash", contents=user,
            config=types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json"))
        return _parse_json(r.text)

    if provider == "openrouter":
        return _openrouter(system, user, key, model)

    raise RuntimeError(f"Unknown LLM_PROVIDER '{provider}'")


# Free models change often: list them with GET https://openrouter.ai/api/v1/models (ids ending ":free")
OPENROUTER_FALLBACKS = ["google/gemma-4-31b-it:free", "minimax/minimax-m3.1-flash:free",
                        "nvidia/nemotron-3-super-120b-a12b:free"]


def _openrouter(system, user, key, model):
    import time

    import requests

    models = [model] if model else []
    models += [m for m in OPENROUTER_FALLBACKS if m not in models]
    last = None
    for m in models:
        for wait in (0, 5, 15):  # free tier rate-limits often
            time.sleep(wait)
            r = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "X-Title": "Nudgely"},
                json={"model": m, "response_format": {"type": "json_object"}, "temperature": 0.4,
                      "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
                timeout=90)
            if r.status_code == 429 or r.status_code >= 500:
                last = f"{m}: HTTP {r.status_code}"
                continue
            if not r.ok:
                last = f"{m}: HTTP {r.status_code} {r.text[:200]}"
                break  # try the next model
            try:
                return _parse_json(r.json()["choices"][0]["message"]["content"])
            except (KeyError, IndexError, ValueError, TypeError) as e:
                last = f"{m}: bad output ({e})"
                break
    raise RuntimeError(f"OpenRouter failed on all models. Last error: {last}")


# ---- privacy: strip names and phone numbers before text goes to the LLM -----

PHONE = re.compile(r"(\+?65[\s-]?)?\b[3689]\d{3}[\s-]?\d{4}\b")


def scrub(text, names=()):
    text = PHONE.sub("[phone]", text)
    for n in names:
        for part in str(n).split():
            if len(part) > 1:
                text = re.sub(rf"\b{re.escape(part)}\b", "[name]", text, flags=re.I)
    return text


def extract_tags(customer_id, chat, names=()):
    lines = [f"[{m['date']}] {m['from']}: {scrub(m['text'], names)}" for m in chat]
    user = f"customer_id: {customer_id}\nChat history:\n" + "\n".join(lines)
    out = complete_json(EXTRACT_SYSTEM, user)
    out["customer_id"] = customer_id
    out["tags"] = [t for t in out.get("tags", []) if t.get("type") in TAG_TYPES and t.get("evidence")]
    return out


def write_message(customer, extraction):
    first_name = str(customer["name"]).split()[0]
    user = json.dumps({
        "customer_id": customer["customer_id"],
        "first_name": first_name,
        "label": customer["label"],
        "features": {k: customer.get(k) for k in ("visits_per_month", "avg_spend_sgd", "days_since_last_visit")},
        "extraction": extraction,
        "STORE_INFO": STORE_INFO,
    }, default=str)
    out = complete_json(WRITE_SYSTEM, user)
    out["customer_id"] = customer["customer_id"]
    return out


def check_message(msg, label):
    """Hard rules from the PRD. Returns a list of problems ([] = ok)."""
    text = msg.get("message", "")
    problems = []
    if len(text) > 300:
        problems.append(f"too long ({len(text)} chars)")
    if not text.rstrip().endswith("Reply STOP to opt out"):
        problems.append("missing opt-out line")
    if not msg.get("tags_used"):
        problems.append("uses no tag")
    pcts = [int(p) for p in re.findall(r"(\d+)\s*%", text)]
    if pcts and label != "Persuadable":
        problems.append("discount offered to non-Persuadable")
    if any(p > 10 for p in pcts):
        problems.append("discount above 10%")
    return problems

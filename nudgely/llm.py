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
Every tag MUST quote evidence copied word-for-word from a message the CUSTOMER sent. Drop any tag
without evidence. The store's own messages are context: never tag something only the store said.
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


# Each provider's own key, if one is set, so a dead provider can hand over to another.
PROVIDER_KEY_ENV = {"gemini": "GEMINI_API_KEY", "openai": "OPENAI_API_KEY",
                    "anthropic": "ANTHROPIC_API_KEY", "openrouter": "OPENROUTER_API_KEY"}

# Free tiers are counted per model per day, so a second model on the same key is
# a real fallback, not a formality. This is what the 20/day Gemini cap needs.
MODEL_FALLBACKS = {"gemini": ["gemini-2.5-flash", "gemini-2.5-flash-lite"],
                   "anthropic": ["claude-haiku-5-5"],
                   "openai": ["gpt-4o-mini"],
                   "openrouter": []}  # _openrouter already walks its own model list

RETRYABLE = ("quota", "rate limit", "rate_limit", "resource_exhausted", "429", "500", "502",
             "503", "overloaded", "unavailable", "timeout", "temporarily")


def _retryable(exc):
    """Worth trying the next model or provider, rather than a mistake in our request."""
    text = str(exc).lower()
    return any(sign in text for sign in RETRYABLE)


def _chain():
    """Where to try, in order: the configured provider and model, then its other
    models, then any other provider that has a key of its own in the environment."""
    c = _config()
    provider, key, model = c["provider"].lower(), c["api_key"], c["model"]
    if not (provider and key):
        raise RuntimeError("LLM not configured: set LLM_PROVIDER and LLM_API_KEY")

    steps = [(provider, key, model)]
    for alt in MODEL_FALLBACKS.get(provider, []):
        if alt != model:
            steps.append((provider, key, alt))
    for other, env in PROVIDER_KEY_ENV.items():
        other_key = os.getenv(env, "")
        if other != provider and other_key:
            steps.append((other, other_key, ""))
    return steps


GEMINI_TIMEOUT_MS = 30_000
CHAIN_DEADLINE = 75  # seconds for the whole chain; a reply bot must answer or give up


def complete_json(system, user, on_fallback=None, deadline=CHAIN_DEADLINE):
    """Ask the LLM for JSON, moving down the chain when a provider is rate-limited.

    `on_fallback(provider, model, error)` is called each time a step fails, so the
    caller can log which provider actually answered.
    """
    import time

    started = time.monotonic()
    problems = []
    for provider, key, model in _chain():
        if deadline and time.monotonic() - started > deadline:
            problems.append(f"gave up after {deadline}s")
            break
        try:
            return _call(provider, key, model, system, user)
        except Exception as e:  # noqa: BLE001 - any provider error should fall through
            problems.append(f"{provider}/{model or 'default'}: {str(e)[:120]}")
            if on_fallback:
                on_fallback(provider, model, e)
            if not _retryable(e):
                raise
    raise RuntimeError("Every provider failed. " + " | ".join(problems))


def _call(provider, key, model, system, user):
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

        client = genai.Client(api_key=key,
                              http_options=types.HttpOptions(timeout=GEMINI_TIMEOUT_MS,
                                                             retry_options=types.HttpRetryOptions(attempts=1)))
        r = client.models.generate_content(
            model=model or "gemini-2.5-flash", contents=user,
            config=types.GenerateContentConfig(system_instruction=system, response_mime_type="application/json"))
        return _parse_json(r.text)

    if provider == "openrouter":
        return _openrouter(system, user, key, model)

    raise RuntimeError(f"Unknown LLM_PROVIDER '{provider}'")


# Free models change often: list them with GET https://openrouter.ai/api/v1/models (ids ending ":free")
OPENROUTER_FALLBACKS = ["nvidia/nemotron-3.5-lightning:free", "google/gemma-4-31b-it:free",
                        "google/gemma-4-26b-a4b-it:free", "nvidia/nemotron-3-ultra-550b-a55b:free"]


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
    # Evidence must be quoted from something the CUSTOMER said. The store's own
    # messages are context: a shop announcing a Deepavali promotion is not evidence
    # that this customer has Deepavali coming up, and a tag sourced that way puts a
    # fact on their record they never gave us.
    chat_text = " ".join(f"{m['from']}: {scrub(m['text'], names)}"
                         for m in chat if m.get("from") == "customer").lower()
    out["tags"] = [t for t in out.get("tags", []) if t.get("type") in TAG_TYPES and t.get("evidence")
                   and t["evidence"].strip(" .\"'“”").lower() in chat_text]
    return out


TAG_ONE_SYSTEM = f"""You read ONE new message a customer just sent a grocery store, and extract memory tags from it.
Return ONLY a JSON object with keys:
tags (list of {{type, value, evidence, date}}), sentiment (positive|neutral|negative),
open_promise (string, "" if none), best_hook (short string), avoid (string, "" if none).
Allowed tag types: {", ".join(TAG_TYPES)}.
Every tag MUST quote evidence copied word-for-word from the new message. Drop any tag without evidence.
Earlier tags are given for context only: do NOT repeat them, and do not tag anything the new message
does not itself say. Return an empty tags list when the message carries nothing worth remembering.
Do not invent anything."""


def tag_message(customer_id, text, date="", prior=None, names=()):
    """Tag ONE incoming message, for the API to call as each message arrives.

    `extract_tags` re-reads a whole chat, which suits the nightly batch and is
    wasteful per message: it costs more every time the conversation grows and it
    re-decides tags that were already settled. This looks at the new message
    only, with `prior` passed as context so the model does not repeat itself.

    Returns the same shape as `extract_tags`. Merge it into what you already hold
    with `merge_tags`.
    """
    user = json.dumps({
        "customer_id": customer_id,
        "new_message": {"date": date, "from": "customer", "text": scrub(text, names)},
        "tags_we_already_have": [
            {k: t.get(k) for k in ("type", "value")} for t in (prior or {}).get("tags", [])],
    }, default=str)
    out = complete_json(TAG_ONE_SYSTEM, user)
    out["customer_id"] = customer_id

    # Evidence must be quoted from this message, not from the conversation at large.
    low = scrub(text, names).lower()
    out["tags"] = [t for t in out.get("tags", [])
                   if t.get("type") in TAG_TYPES and t.get("evidence")
                   and t["evidence"].strip(" .\"'“”").lower() in low]
    for tag in out["tags"]:
        tag.setdefault("date", date)
    return out


def merge_tags(prior, new):
    """Fold a single message's tags into what we already remember.

    Same type and same value is the same fact mentioned twice, so the newer one
    wins and carries the newer evidence. Everything else accumulates, because a
    customer who asked about oat milk in September and durian in October wants
    both remembered.

    `sentiment`, `best_hook` and `avoid` come from the newest message that has
    them: they describe where the customer stands now, not where they stood.
    """
    prior = prior or {}
    merged = {t.get("type", "") + "|" + str(t.get("value", "")).strip().lower(): t
              for t in prior.get("tags", [])}
    for tag in new.get("tags", []):
        merged[tag.get("type", "") + "|" + str(tag.get("value", "")).strip().lower()] = tag

    out = dict(prior)
    out["customer_id"] = new.get("customer_id") or prior.get("customer_id", "")
    out["tags"] = list(merged.values())
    for key in ("sentiment", "best_hook", "avoid", "open_promise"):
        if str(new.get(key, "")).strip():
            out[key] = new[key]
        else:
            out.setdefault(key, prior.get(key, ""))
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

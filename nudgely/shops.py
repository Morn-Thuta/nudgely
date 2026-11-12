"""Shops: a real shop signs up, uploads its sales, and runs its own campaign.

Until now everything ran on one fictional shop. This module is the multi-shop version of the
whole loop, kept free of web code so the API, the tests and any script share it:

    create_shop      one shop per owner account
    save_sales       score the shop's sales export with Model 2 and keep the scores
    plan_campaign    top Persuadables by uplift, with a random kept-back group
    write_messages   fill the shop's approved win-back template, one blank written by the AI
    send_campaign    rehearsal (nothing leaves) or live through the shop's own WhatsApp number
    record_returns   a later sales export marks who came back, messaged and kept back alike
    results          messaged vs kept back, with the range the difference could really be

Storage is the five tables in supabase/migrations/004_shops.sql. With SUPABASE_URL and
SUPABASE_SERVICE_KEY set it uses Supabase; otherwise a local JSON file, for laptops and tests.
Everything goes through the backend with the service key: the dashboard never reads these
tables directly, so a shop's customers and phone numbers are only ever served to its owner.
"""

import json
import os
import random
import re
import threading
import time
import uuid
from datetime import date, datetime, timezone
from urllib.parse import quote

import pandas as pd

from nudgely import returns, shop_scores, supabase_sync

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCAL_PATH = os.path.join(ROOT, "data", "shops.json")   # git-ignored: real shops' customers

OPT_OUT = "Reply STOP to opt out"
MAX_CHARS = 300
BLANK_MAX = 140
WRITE_BATCH = 6        # messages written per request, in parallel; the page asks again for the rest
AI_DEADLINE_S = 25     # one AI call slower than this gets the plain sentence instead
HOLD_DEFAULT = 10

# The win-back template a shop submits to Meta. Fixed words, two blanks:
#   {{1}} how long since their last visit (calculated, never written by the AI)
#   {{2}} one short sentence, written by the AI from facts the owner typed
WIN_BACK = "Hi from {shop}! It's been {{{{1}}}} since your last visit and we'd love to see you again. {{{{2}}}} " + OPT_OUT


class ShopError(ValueError):
    """Something the owner can fix. The message says how. `status` is the HTTP code to use."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ---- storage -------------------------------------------------------------------------------

class LocalStore:
    """The five tables in one JSON file. Same calls as SupabaseStore."""

    def __init__(self, path=LOCAL_PATH):
        self.path = path
        self.lock = threading.Lock()
        self.data = {}
        if path and os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                self.data = json.load(f)

    def _save(self):
        if not self.path:
            return
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False)
        # Windows briefly refuses the swap while a virus scanner or the indexer has the file open.
        for attempt in range(20):
            try:
                os.replace(tmp, self.path)
                return
            except PermissionError:
                if attempt == 19:
                    raise
                time.sleep(0.05)

    def select(self, table, **eq):
        with self.lock:
            return [dict(r) for r in self.data.get(table, []) if all(r.get(k) == v for k, v in eq.items())]

    def insert(self, table, rows):
        with self.lock:
            out = []
            for r in rows:
                r = dict(r)
                r.setdefault("id", uuid.uuid4().hex)
                self.data.setdefault(table, []).append(r)
                out.append(dict(r))
            self._save()
            return out

    def update(self, table, match, patch):
        with self.lock:
            n = 0
            for r in self.data.get(table, []):
                if all(r.get(k) == v for k, v in match.items()):
                    r.update(patch)
                    n += 1
            self._save()
            return n

    def upsert(self, table, rows, keys):
        with self.lock:
            existing = self.data.setdefault(table, [])
            for r in rows:
                hit = next((e for e in existing if all(e.get(k) == r.get(k) for k in keys)), None)
                if hit:
                    hit.update(r)
                else:
                    existing.append({"id": uuid.uuid4().hex, **r})
            self._save()


class SupabaseStore:
    """The same calls over Supabase's REST API, with the service key (the backend only)."""

    def _req(self, method, path, json=None, prefer=None):
        url, key = supabase_sync._config()
        headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        if prefer:
            headers["Prefer"] = prefer
        r = supabase_sync.http(method, f"{url}/rest/v1/{path}", json=json, timeout=15, headers=headers)
        if r.status_code >= 300:
            raise RuntimeError(f"{method} {path.split('?')[0]}: HTTP {r.status_code} {r.text[:200]}")
        return r.json() if r.text else None

    @staticmethod
    def _filters(eq):
        return "&".join(f"{k}=eq.{quote(str(v), safe='')}" for k, v in eq.items())

    def select(self, table, **eq):
        return self._req("GET", f"{table}?select=*&{self._filters(eq)}") or []

    def insert(self, table, rows):
        return self._req("POST", table, json=rows, prefer="return=representation") or []

    def update(self, table, match, patch):
        out = self._req("PATCH", f"{table}?{self._filters(match)}", json=patch, prefer="return=representation")
        return len(out or [])

    def upsert(self, table, rows, keys):
        if rows:
            self._req("POST", f"{table}?on_conflict={','.join(keys)}", json=rows,
                      prefer="resolution=merge-duplicates,return=minimal")


_store = None


def store():
    global _store
    if _store is None:
        _store = SupabaseStore() if supabase_sync.enabled() else LocalStore()
    return _store


# ---- shops ---------------------------------------------------------------------------------

def _public_shop(shop, db):
    secret = (db.select("shop_secrets", shop_id=shop["id"]) or [{}])[0]
    return {"id": shop["id"], "name": shop["name"], "offer": shop.get("offer") or "",
            "note": shop.get("note") or "", "template_name": shop.get("template_name") or "",
            "template_language": shop.get("template_language") or "en",
            "whatsapp_connected": bool(secret.get("wa_token") and secret.get("wa_phone_number_id")),
            "template_text": WIN_BACK.format(shop=shop["name"])}


def get_shop(owner, db=None):
    db = db or store()
    rows = db.select("shops", owner=owner)
    return rows[0] if rows else None


def require_shop(owner, db=None):
    shop = get_shop(owner, db)
    if not shop:
        raise ShopError("Create your shop first.", 404)
    return shop


def create_shop(owner, name, db=None):
    db = db or store()
    name = " ".join(str(name or "").split())
    if not 2 <= len(name) <= 40:
        raise ShopError("Give your shop a name of 2 to 40 characters.")
    if get_shop(owner, db):
        raise ShopError("This account already has a shop.", 409)
    shop = db.insert("shops", [{"owner": owner, "name": name, "offer": "", "note": "",
                                "template_language": "en", "created_at": _now()}])[0]
    return _public_shop(shop, db)


def shop_view(owner, db=None):
    db = db or store()
    shop = get_shop(owner, db)
    if not shop:
        return None
    customers = db.select("shop_customers", shop_id=shop["id"])
    view = _public_shop(shop, db)
    view["customers"] = len(customers)
    view["persuadable"] = sum(1 for c in customers if c.get("label") == "Persuadable")
    view["scored_up_to"] = max((c.get("as_of") or "" for c in customers), default="") or None
    return view


def update_settings(owner, offer=None, note=None, whatsapp=None, db=None):
    """Offer and note feed the AI's sentence; WhatsApp details are only needed for live sends."""
    db = db or store()
    shop = require_shop(owner, db)
    patch = {}
    if offer is not None:
        offer = " ".join(str(offer).split())
        if len(offer) > 60:
            raise ShopError("Keep the offer under 60 characters.")
        if any(int(p) > 10 for p in re.findall(r"(\d+)\s*%", offer)):
            raise ShopError("Discounts are capped at 10%.")
        patch["offer"] = offer
    if note is not None:
        note = " ".join(str(note).split())
        if len(note) > BLANK_MAX:
            raise ShopError(f"Keep the note under {BLANK_MAX} characters.")
        patch["note"] = note
    if whatsapp:
        for field, limit in (("template_name", 80), ("template_language", 10)):
            if field in whatsapp:
                value = str(whatsapp[field] or "").strip()
                if len(value) > limit or (value and not re.fullmatch(r"[A-Za-z0-9_\-]+", value)):
                    raise ShopError(f"{field.replace('_', ' ').capitalize()} should look like win_back or en.")
                patch[field] = value
        secret = {k: str(whatsapp[k]).strip() for k in ("wa_token", "wa_phone_number_id") if whatsapp.get(k)}
        if secret:
            db.upsert("shop_secrets", [{"shop_id": shop["id"], **secret}], ("shop_id",))
    if patch:
        db.update("shops", {"id": shop["id"]}, patch)
    return shop_view(owner, db)


# ---- customers: the sales upload, kept --------------------------------------------------------

def _mask(phone):
    return f"•••• {phone[-4:]}" if re.fullmatch(r"\d{7,}", phone) else phone


def _public_customer(c):
    return {k: c.get(k) for k in ("id", "ref", "label", "uplift", "p_no_msg", "p_msg", "purchases", "avg_spend",
                                   "months_as_customer", "days_since_last", "opted_out")}


def save_sales(owner, data, filename, db=None):
    """Score the upload with Model 2 and keep every customer's score. Re-uploading updates them."""
    db = db or store()
    shop = require_shop(owner, db)
    try:
        scored = shop_scores.score_upload(data, filename)
    except shop_scores.ScoreError as e:
        raise ShopError(str(e))
    now = _now()
    db.upsert("shop_customers", [{
        "shop_id": shop["id"], "phone": c["id"], "ref": _mask(c["id"]), "label": c["label"],
        "uplift": c["uplift"], "p_no_msg": c["p_no_msg"], "p_msg": c["p_msg"], "purchases": c["purchases"],
        "avg_spend": c["avg_spend"], "months_as_customer": c["months_as_customer"],
        "days_since_last": c["days_since_last"], "as_of": scored["as_of"], "scored_at": now,
    } for c in scored["customers"]], ("shop_id", "phone"))
    out = {k: v for k, v in scored.items() if k != "customers"}
    out["saved"] = len(scored["customers"])
    return out


def list_customers(owner, db=None):
    db = db or store()
    shop = require_shop(owner, db)
    rows = sorted(db.select("shop_customers", shop_id=shop["id"]), key=lambda c: -(c.get("uplift") or 0))
    return [_public_customer(c) for c in rows]


# ---- campaigns -----------------------------------------------------------------------------

def _since(days):
    """How long since their last visit, as the template's {{1}} says it."""
    days = int(days or 0)
    if days < 7:
        return "a few days"
    if days < 14:
        return "a week"
    if days < 60:
        return f"{round(days / 7)} weeks"
    months = round(days / 30.4)
    return "a month" if months <= 1 else f"{months} months"


def render(shop_name, since, blank):
    return WIN_BACK.format(shop=shop_name).replace("{{1}}", since).replace("{{2}}", blank)


def _public_row(r):
    return {k: r.get(k) for k in ("id", "ref", "label", "uplift", "group", "since", "blank", "message",
                                   "source", "problems", "approved", "status", "error", "returned", "returned_at")}


def _campaign(cid, shop, db):
    rows = db.select("shop_campaigns", id=cid, shop_id=shop["id"])
    if not rows:
        raise ShopError("No such campaign.", 404)
    return rows[0]


def campaign_view(owner, cid, db=None):
    db = db or store()
    shop = require_shop(owner, db)
    camp = _campaign(cid, shop, db)
    rows = db.select("campaign_rows", campaign_id=cid)
    rows.sort(key=lambda r: (r["group"] != "messaged", -(r.get("uplift") or 0)))
    view = {k: camp.get(k) for k in ("id", "created_at", "size", "holdout_pct", "status", "mode", "sent_at",
                                      "expected_extra_visits")}
    view["rows"] = [_public_row(r) for r in rows]
    view["results"] = results(rows)
    return view


def list_campaigns(owner, db=None):
    db = db or store()
    shop = require_shop(owner, db)
    camps = sorted(db.select("shop_campaigns", shop_id=shop["id"]), key=lambda c: c["created_at"], reverse=True)
    return [{k: c.get(k) for k in ("id", "created_at", "size", "holdout_pct", "status", "mode", "sent_at")}
            for c in camps]


def plan_campaign(owner, size=None, holdout_pct=HOLD_DEFAULT, db=None):
    """Top Persuadables by uplift; a random share of them is kept back, so the result can be measured."""
    db = db or store()
    shop = require_shop(owner, db)
    holdout_pct = int(holdout_pct if holdout_pct is not None else HOLD_DEFAULT)
    if not 0 <= holdout_pct <= 50:
        raise ShopError("Keep back between 0% and 50%.")
    pool = [c for c in db.select("shop_customers", shop_id=shop["id"])
            if c.get("label") == "Persuadable" and (c.get("uplift") or 0) > 0 and not c.get("opted_out")]
    if not pool:
        raise ShopError("No customers to message yet. Upload your sales on Your customers first.")
    pool.sort(key=lambda c: -c["uplift"])
    size = len(pool) if not size else max(1, min(int(size), len(pool)))
    chosen = pool[:size]

    cid = uuid.uuid4().hex
    n_hold = round(size * holdout_pct / 100)
    if holdout_pct and size >= 2:
        n_hold = max(n_hold, 1)
    held = set(random.Random(cid).sample([c["phone"] for c in chosen], n_hold)) if n_hold else set()
    messaged = [c for c in chosen if c["phone"] not in held]

    db.insert("shop_campaigns", [{
        "id": cid, "shop_id": shop["id"], "created_at": _now(), "size": size, "holdout_pct": holdout_pct,
        "status": "draft", "mode": None, "sent_at": None,
        "expected_extra_visits": round(sum(c["uplift"] for c in messaged), 2),
    }])
    db.insert("campaign_rows", [{
        "campaign_id": cid, "shop_id": shop["id"], "phone": c["phone"], "ref": c["ref"], "label": c["label"],
        "uplift": c["uplift"], "group": "holdout" if c["phone"] in held else "messaged",
        "since": _since(c.get("days_since_last")), "blank": "", "message": "", "source": None, "problems": [],
        "approved": False, "status": "not messaged" if c["phone"] in held else "draft",
        "error": None, "returned": None, "returned_at": None,
    } for c in chosen])
    return campaign_view(owner, cid, db)


# ---- step 5: one AI sentence per customer, checked -----------------------------------------

BLANK_SYSTEM = """You write ONE short sentence for a WhatsApp message from a small Singapore shop to a customer
who hasn't visited for a while. It fills a blank in this approved template:

  "{template}"

Rules:
- One sentence, under 120 characters, friendly and plain, ending with a question.
- Use ONLY the facts given: the shop's offer and the shop's note. Never name a product, price, date
  or event that is not in them. If both are empty, ask a simple warm question about coming back.
- Mention the offer only if offer_allowed is true. Never invent a discount.
- No greeting (the template already says hi), no sign-off, no emoji, no hashtags.

Return JSON: {{"blank": "..."}}"""


def check_blank(blank, label, offer, note):
    """Problems with a blank ([] = fine). Numbers, prices and discounts must come from the owner's text."""
    problems = []
    text = str(blank or "").strip()
    if not text:
        return ["empty"]
    if len(text) > BLANK_MAX:
        problems.append(f"too long ({len(text)} characters)")
    if not text.endswith("?"):
        problems.append("should end with a question")
    allowed = f"{offer} {note}"
    for number in re.findall(r"\d+(?:\.\d+)?", text):
        if number not in allowed:
            problems.append(f"mentions {number}, which isn't in your offer or note")
    pcts = re.findall(r"(\d+)\s*%", text)
    if pcts and label != "Persuadable":
        problems.append("offers a discount to a customer who isn't Persuadable")
    if any(int(p) > 10 for p in pcts):
        problems.append("discount above 10%")
    if "$" in text and "$" not in allowed:
        problems.append("mentions a price that isn't in your offer or note")
    if re.search(r"https?://|www\.", text):
        problems.append("contains a link")
    return problems


def fallback_blank(label, offer):
    if label == "Persuadable" and offer:
        return f"{offer[0].upper()}{offer[1:].rstrip('.!')} - shall we set something aside for you?"
    return "Is there anything we can set aside for you?"


def _ai_blank(shop, row, offer_allowed):
    from nudgely import llm

    if not llm.available():
        return None
    user = json.dumps({"shop": shop["name"], "offer": shop.get("offer") or "", "note": shop.get("note") or "",
                       "offer_allowed": offer_allowed, "weeks_since_last_visit_text": row["since"],
                       "customer_type": row["label"]})
    try:
        out = llm.complete_json(BLANK_SYSTEM.format(template=WIN_BACK.format(shop=shop["name"])), user,
                                deadline=AI_DEADLINE_S)
    except Exception:  # noqa: BLE001 - a failed or slow call falls back to the safe sentence
        return None
    return " ".join(str(out.get("blank", "")).split()) or None


def write_messages(owner, cid, db=None, ai=None, batch=None):
    """Fill {{2}} for the next batch of messaged customers without a message. AI first, several at once;
    if what it writes breaks a rule, or it's too slow, the plain sentence is used, never patched.

    One batch per call keeps every request well inside the website's time limit, however big the shop:
    the page calls again until nothing is left to write.
    """
    from concurrent.futures import ThreadPoolExecutor, wait

    db = db or store()
    ai = ai or _ai_blank
    shop = require_shop(owner, db)
    camp = _campaign(cid, shop, db)
    if camp["status"] != "draft":
        raise ShopError("This campaign has been sent; its messages can't change.", 409)
    todo = [r for r in db.select("campaign_rows", campaign_id=cid) if r["group"] == "messaged" and not r["message"]]
    todo = todo[:batch or WRITE_BATCH]
    offer, note = shop.get("offer") or "", shop.get("note") or ""

    def one(r):
        allowed = r["label"] == "Persuadable" and bool(offer)
        try:
            blank = ai(shop, r, allowed)
        except Exception:  # noqa: BLE001 - never lose a row to one bad call
            blank = None
        if not blank or check_blank(blank, r["label"], offer if allowed else "", note):
            return r, fallback_blank(r["label"], offer if allowed else ""), "template"
        return r, blank, "ai"

    # A hard time limit: whatever hasn't come back gets the plain sentence, and the slow call is
    # abandoned (its answer is never used). One provider call can otherwise hang for a minute.
    pool = ThreadPoolExecutor(max_workers=max(1, len(todo)))
    futures = {pool.submit(one, r): r for r in todo}
    finished, late = wait(futures, timeout=AI_DEADLINE_S + 3)
    for f in finished:
        _set_blank(db, shop, *f.result())
    for f in late:
        r = futures[f]
        allowed = r["label"] == "Persuadable" and bool(offer)
        _set_blank(db, shop, r, fallback_blank(r["label"], offer if allowed else ""), "template")
    pool.shutdown(wait=False, cancel_futures=True)
    return campaign_view(owner, cid, db)


def _set_blank(db, shop, row, blank, source):
    message = render(shop["name"], row["since"], blank)
    problems = check_blank(blank, row["label"], shop.get("offer") or "", shop.get("note") or "")
    if len(message) > MAX_CHARS:
        problems.append(f"whole message is {len(message)} characters, over {MAX_CHARS}")
    db.update("campaign_rows", {"id": row["id"]},
              {"blank": blank, "message": message, "source": source, "problems": problems, "approved": False})


def edit_row(owner, cid, row_id, blank=None, approved=None, db=None):
    db = db or store()
    shop = require_shop(owner, db)
    camp = _campaign(cid, shop, db)
    if camp["status"] != "draft":
        raise ShopError("This campaign has been sent; its messages can't change.", 409)
    rows = db.select("campaign_rows", campaign_id=cid, id=row_id)
    if not rows or rows[0]["group"] != "messaged":
        raise ShopError("No such message.", 404)
    row = rows[0]
    if blank is not None:
        _set_blank(db, shop, row, " ".join(str(blank).split()), "edited")
        row = db.select("campaign_rows", campaign_id=cid, id=row_id)[0]
    if approved is not None:
        if approved and (not row["message"] or row["problems"]):
            raise ShopError("Fix the problems with this message before approving it.")
        db.update("campaign_rows", {"id": row_id}, {"approved": bool(approved)})
    return campaign_view(owner, cid, db)


def approve_all(owner, cid, db=None):
    db = db or store()
    shop = require_shop(owner, db)
    if _campaign(cid, shop, db)["status"] != "draft":
        raise ShopError("This campaign has been sent.", 409)
    for r in db.select("campaign_rows", campaign_id=cid):
        if r["group"] == "messaged" and r["message"] and not r["problems"]:
            db.update("campaign_rows", {"id": r["id"]}, {"approved": True})
    return campaign_view(owner, cid, db)


# ---- step 6: sending ---------------------------------------------------------------------

def _whatsapp(shop, db):
    from nudgely.whatsapp import WhatsApp

    secret = (db.select("shop_secrets", shop_id=shop["id"]) or [{}])[0]
    if not (secret.get("wa_token") and secret.get("wa_phone_number_id") and shop.get("template_name")):
        return None
    return WhatsApp(secret["wa_token"], secret["wa_phone_number_id"])


def send_campaign(owner, cid, live=False, db=None, client=None):
    """Rehearsal marks approved messages 'simulated' and sends nothing. Live sends each approved message
    through the shop's own WhatsApp number as its approved win-back template. Unapproved ones stay drafts."""
    db = db or store()
    shop = require_shop(owner, db)
    camp = _campaign(cid, shop, db)
    if camp["status"] != "draft":
        raise ShopError("This campaign has already been sent.", 409)
    rows = db.select("campaign_rows", campaign_id=cid)
    ready = [r for r in rows if r["group"] == "messaged" and r["approved"] and r["message"] and not r["problems"]]
    if not ready:
        raise ShopError("Approve at least one message first.")
    if live:
        client = client or _whatsapp(shop, db)
        if client is None:
            raise ShopError("Connect your WhatsApp number and approved template in Settings to send for real. "
                            "Or run a rehearsal.")
        opted_out = {c["phone"] for c in db.select("shop_customers", shop_id=shop["id"]) if c.get("opted_out")}
    now = _now()
    for r in ready:
        if not live:
            status, error = "simulated", None
        elif r["phone"] in opted_out:
            status, error = "skipped", "opted out"
        else:
            try:
                client.send_template(r["phone"], shop["template_name"], shop.get("template_language") or "en",
                                     params=[r["since"], r["blank"]])
                status, error = "sent", None
            except Exception as e:  # noqa: BLE001 - one failure must not stop the rest
                status, error = "failed", str(e)[:200]
        db.update("campaign_rows", {"id": r["id"]}, {"status": status, "error": error, "sent_at": now})
    db.update("shop_campaigns", {"id": cid}, {"status": "sent", "mode": "live" if live else "rehearsal",
                                               "sent_at": now})
    return campaign_view(owner, cid, db)


# ---- step 7: who came back -----------------------------------------------------------------

def record_returns(owner, cid, data, filename, db=None):
    """A later sales export: everyone in the campaign, messaged or kept back, is marked the same way."""
    db = db or store()
    shop = require_shop(owner, db)
    camp = _campaign(cid, shop, db)
    if camp["status"] != "sent":
        raise ShopError("Send (or rehearse) the campaign first, then upload the sales that came after it.")
    if len(data) > shop_scores.MAX_BYTES:
        raise ShopError("Keep the file under 2 MB.")
    try:
        frame = next(iter(returns.read_file(data, filename or "sales.csv").values()))
    except Exception as e:  # noqa: BLE001
        raise ShopError(f"Couldn't read the file: {e}. Save it as CSV or Excel.")
    who = returns.guess_column(list(frame.columns), ("phone", "mobile", "contact", "hp", "customer", "member"))
    when = returns.guess_column(list(frame.columns), returns.WHEN_HINTS)
    if who is None or when is None:
        raise ShopError("Couldn't find the phone and date columns. Name them phone and date.")
    purchases, problems = returns.read_purchases(frame, who, when)

    rows = [r for r in db.select("campaign_rows", campaign_id=cid) if r["group"] == "holdout" or r["status"] in
            ("sent", "simulated")]
    # Stored in UTC; a till's dates are local and carry no zone, so compare in Singapore time.
    sent_local = pd.Timestamp(camp["sent_at"]).tz_convert("Asia/Singapore").tz_localize(None).isoformat()
    log = pd.DataFrame([{"campaign_id": cid, "sent_at": sent_local, "customer_id": r["phone"],
                         "name": r["ref"], "group": r["group"], "returned": "" if r.get("returned") is None
                         else r["returned"], "returned_at": r.get("returned_at") or "", "row_id": r["id"]}
                        for r in rows])
    matched, _ = returns.match_returns(log, purchases)
    updated, changed = returns.apply_to_log(log, matched)
    for _, r in updated.iterrows():
        value = pd.to_numeric(r["returned"], errors="coerce")
        db.update("campaign_rows", {"id": r["row_id"]},
                  {"returned": None if pd.isna(value) else int(value), "returned_at": r["returned_at"] or None})
    view = campaign_view(owner, cid, db)
    view["upload"] = {"purchases": len(purchases), "unreadable_rows": len(problems), "updated": changed}
    return view


def results(rows):
    """Messaged vs kept back, counting only customers whose 30 days are settled."""
    m = [r for r in rows if r["group"] == "messaged" and r.get("status") in ("sent", "simulated")
         and r.get("returned") in (0, 1)]
    h = [r for r in rows if r["group"] == "holdout" and r.get("returned") in (0, 1)]
    back_m, back_h = sum(r["returned"] for r in m), sum(r["returned"] for r in h)
    out = {"messaged": len(m), "messaged_back": back_m, "kept_back": len(h), "kept_back_back": back_h,
           "waiting": sum(1 for r in rows if r.get("returned") is None and (r["group"] == "holdout" or
                                                                           r.get("status") in ("sent", "simulated")))}
    if not m or not h:
        out.update(difference=None, low=None, high=None, verdict="waiting")
        return out
    rate_m, rate_h = back_m / len(m), back_h / len(h)
    low, high = returns.lift_range(back_m, len(m), back_h, len(h))
    out.update(rate_messaged=round(rate_m, 4), rate_kept_back=round(rate_h, 4),
               difference=round(rate_m - rate_h, 4), low=round(low, 4), high=round(high, 4),
               verdict="worked" if low > 0 else "did not help" if high < 0 else "too early to call")
    return out

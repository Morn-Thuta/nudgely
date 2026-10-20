"""Shared helpers for the Streamlit app: data loading, campaign planning, sending."""

import json
import os
import sys
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from nudgely.mantago import MantaGO, MantaGOError  # noqa: E402

DATA = os.path.join(ROOT, "data")
EXAMPLES = os.path.join(DATA, "examples")
SEND_LOG = os.path.join(DATA, "send_log.csv")
SEED = 42
REGEN_LIMIT = 3

BRAND = "#0E9F6E"
LABEL_COLORS = {"Persuadable": "#0E9F6E", "Sure Thing": "#3B82F6", "Lost Cause": "#9CA3AF"}
LABEL_HELP = {
    "Persuadable": "A message makes them much more likely to come back.",
    "Sure Thing": "Likely to come back anyway. A message (or discount) is wasted.",
    "Lost Cause": "Unlikely to come back, message or not.",
}

# Hillstrom figures computed by the team with scikit-uplift (see docs/PRD.md)
HILLSTROM = {"visit_no_msg": 0.106, "visit_msg": 0.183, "buy_no_msg": 0.0057, "buy_msg": 0.0125,
             "visit_lift": 0.72, "buy_ratio": 2.2}  # lift/ratio from unrounded rates


def _path(name):
    real = os.path.join(DATA, name)
    return real if os.path.exists(real) else os.path.join(EXAMPLES, name)


def using_examples(name):
    return not os.path.exists(os.path.join(DATA, name))


@st.cache_data
def load_customers():
    df = pd.read_csv(_path("customers.csv"), dtype={"mantago_client_id": str})
    accounts = test_accounts()
    df["mantago_client_id"] = df["customer_id"].map(accounts).fillna(df["mantago_client_id"]).fillna("")
    return df.sort_values("uplift", ascending=False).reset_index(drop=True)


def test_accounts():
    """Team phones mapped to demo customers: {"C001": "<clientId>"}. Kept out of git (may be phone numbers).
    Cloud: [test_accounts] in Streamlit secrets. Local: data/test_accounts.json."""
    try:
        if "test_accounts" in st.secrets:
            return dict(st.secrets["test_accounts"])
    except Exception:
        pass
    p = os.path.join(DATA, "test_accounts.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return json.load(f)
    return {}


@st.cache_data
def load_json(name, default=None):
    p = _path(name)
    if not os.path.exists(p):
        return default if default is not None else {}
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def chats():
    return load_json("chats.json")


def tags():
    return load_json("tags.json")


def messages():
    msgs = dict(load_json("messages.json"))
    msgs.update(st.session_state.get("regenerated", {}))
    return msgs


def summary():
    return load_json("uplift_summary.json", default=None) or None


@st.cache_data
def load_scored_test():
    p = os.path.join(DATA, "lenta_scored_test.csv")
    return pd.read_csv(p) if os.path.exists(p) else None


def top_tag(cid):
    t = tags().get(cid, {}).get("tags", [])
    return f"{t[0]['type'].replace('_', ' ')}: {t[0]['value']}" if t else ""


# ---- campaign --------------------------------------------------------------

def plan_campaign(customers, budget, holdout_pct):
    """Top `budget` by uplift are chosen; a random holdout_pct of them is held out (fixed seed)."""
    ranked = customers.sort_values("uplift", ascending=False).reset_index(drop=True)
    chosen = ranked.head(budget)
    n_hold = int(round(len(chosen) * holdout_pct / 100))
    if holdout_pct > 0 and len(chosen) >= 2:
        n_hold = max(n_hold, 1)
    rng = np.random.default_rng(SEED)
    hold_ids = set(rng.choice(chosen["customer_id"], size=n_hold, replace=False)) if n_hold else set()

    rows = []
    for i, r in ranked.iterrows():
        if i < budget and r.customer_id in hold_ids:
            group, reason = "Held out", "Random comparison group: not messaged, so we can measure the real lift"
        elif i < budget:
            group, reason = "Will message", f"Rank #{i + 1} by uplift (+{r.uplift:.1%} chance to return if messaged)"
        elif r.label == "Sure Thing":
            group, reason = "Skipped", f"Sure Thing: {r.p_no_msg:.0%} likely to come back anyway"
        elif r.label == "Lost Cause":
            group, reason = "Skipped", "Lost Cause: a message barely changes their chance to return"
        else:
            group, reason = "Skipped", "Outside budget: lower uplift than the chosen customers"
        rows.append({**r.to_dict(), "group": group, "reason": reason})
    return pd.DataFrame(rows)


def mantago_client():
    try:
        return MantaGO.from_streamlit(st)
    except Exception:
        try:
            return MantaGO.from_env()
        except Exception:
            return None


def mantago_platform():
    try:
        return st.secrets["mantago"].get("platform", "whatsapp")
    except Exception:
        return os.getenv("MANTAGO_PLATFORM", "whatsapp")


def send_campaign(plan, msgs):
    """Real send for customers mapped to a MantaGO test account, simulated for the rest."""
    client = mantago_client()
    platform = mantago_platform()
    results = []
    for _, r in plan[plan.group == "Will message"].iterrows():
        text = msgs.get(r.customer_id, {}).get("message", "")
        if not text:
            status, resp = "failed", "no message drafted"
        elif r.mantago_client_id and client:
            try:
                status, resp = "sent", json.dumps(client.send(platform, [r.mantago_client_id], text, name="Nudgely campaign"))
            except (MantaGOError, Exception) as e:  # keep going on one failure
                status, resp = "failed", str(e)[:300]
        elif r.mantago_client_id:
            status, resp = "ready (no API key)", "MantaGO keys not configured"
        else:
            status, resp = "sent (simulated)", "demo customer, not mapped to a real account"
        results.append({"timestamp": datetime.now().isoformat(timespec="seconds"),
                        "customer_id": r.customer_id, "name": r["name"], "status": status, "mantago_response": resp})
    log = pd.DataFrame(results)
    try:
        log.to_csv(SEND_LOG, mode="a", header=not os.path.exists(SEND_LOG), index=False)
    except OSError:
        pass
    return log


# ---- ui bits ---------------------------------------------------------------

def badge(label):
    c = LABEL_COLORS.get(label, "#6B7280")
    return (f"<span style='background:{c}1A;color:{c};border:1px solid {c}55;"
            f"padding:2px 10px;border-radius:999px;font-size:0.85em;font-weight:600'>{label}</span>")


def header(title, subtitle=None):
    st.markdown(f"## {title}")
    if subtitle:
        st.caption(subtitle)


def example_data_note(*names):
    if any(using_examples(n) for n in names):
        st.warning("Showing example data. Real files in `data/` will replace it automatically.", icon="🧪")

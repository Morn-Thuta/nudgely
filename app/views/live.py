"""Live WhatsApp: real conversations with the Kampung Fresh bot, refreshing by itself.

Reads data/wa_customers.json, written by `python scripts/whatsapp_webhook.py --bot`.
Only has data on the machine running the bot, so on stage run this app locally.
Phone numbers are never shown: names and Nudgely ids only.
"""

import html
from datetime import datetime

import streamlit as st

from lib import header
from nudgely import conversations

header("Live on WhatsApp.", "Real customers messaging Kampung Fresh right now: what they said, what the AI remembered, and how it replied.")

TAG_ICON = {"restock_request": "📦", "complaint_delivery": "🚚", "complaint_price": "💸",
            "upcoming_event": "🎉", "product_interest": "🛒", "loyal_regular": "⭐"}


def bubble(m, first_name):
    mine = m["from"] == "store"
    bg, align, who = ("#DCF8C6", "flex-end", "Kampung Fresh") if mine else ("#FFFFFF", "flex-start", first_name or "Customer")
    return (f"<div style='display:flex;justify-content:{align};margin:3px 0'>"
            f"<div style='background:{bg};color:#111;padding:7px 11px;border-radius:12px;max-width:85%;"
            f"box-shadow:0 1px 1px rgba(0,0,0,.08);font-size:0.92em'>"
            f"<div style='font-size:0.72em;color:#6B7280'>{html.escape(who)}</div>{html.escape(m['text'])}</div></div>")


def status_chips(rec):
    chips = []
    if rec.get("opted_out"):
        chips.append(("Opted out", "#FDE9E7", "#8F2A1E"))
    if rec.get("handover"):
        chips.append(("Needs a person", "#FFF4DC", "#7A5200"))
    if not chips:
        chips.append(("AI handling", "#E3F4E8", "#1D6B3A"))
    return " ".join(f"<span style='background:{b};color:{c};padding:2px 9px;border-radius:999px;"
                    f"font-size:0.78em;font-weight:600'>{t}</span>" for t, b, c in chips)


@st.fragment(run_every=3)
def live_board():
    data = conversations.all_customers()
    if not data:
        st.info("No WhatsApp conversations yet. Message the Kampung Fresh test number, and they'll appear here "
                "within a few seconds (the bot must be running: `python scripts/whatsapp_webhook.py --bot`).")
        return

    recs = sorted(data.values(), key=lambda r: len(r.get("seen_ids", [])), reverse=True)
    msgs = sum(1 for r in recs for m in r.get("chat", []) if m["from"] == "customer")
    a, b, c, d = st.columns(4)
    a.metric("Chats", len(recs))
    b.metric("Messages", msgs, help="Messages from customers")
    c.metric("Need a person", sum(1 for r in recs if r.get("handover")), help="Handed over by the AI, not yet resolved")
    d.metric("Opted out", sum(1 for r in recs if r.get("opted_out")))
    st.caption(f"Updated {datetime.now():%H:%M:%S} · refreshes every 3 seconds")

    cols = st.columns(2, gap="medium")
    numbers = {r["customer_id"]: wa for wa, r in data.items()}
    for i, rec in enumerate(recs):
        first = (rec.get("name") or "").split()[0] if rec.get("name") else ""
        with cols[i % 2], st.container(border=True):
            st.markdown(f"**{html.escape(rec.get('name') or 'Unknown')}** &nbsp;"
                        f"<span style='opacity:.55;font-size:0.85em'>{rec['customer_id']}</span> &nbsp; {status_chips(rec)}",
                        unsafe_allow_html=True)
            tags = (rec.get("tags") or {}).get("tags", [])
            if tags:
                st.markdown(" ".join(
                    f"<span title='“{html.escape(t.get('evidence', ''))}”' style='background:#EAF2EC;color:#123D35;"
                    f"padding:2px 8px;border-radius:6px;font-size:0.8em;margin-right:4px'>"
                    f"{TAG_ICON.get(t.get('type'), '🏷️')} {html.escape(str(t.get('value', '')))}</span>"
                    for t in tags), unsafe_allow_html=True)
                st.caption("What the AI remembered. Hover a tag to see the customer's own words.")
            chat = rec.get("chat", [])[-8:]
            st.markdown("<div style='background:#EFEAE2;padding:8px;border-radius:10px'>"
                        + "".join(bubble(m, first) for m in chat) + "</div>", unsafe_allow_html=True)
            if rec.get("handover") and st.button("Mark resolved", key=f"resolve_{rec['customer_id']}"):
                conversations.set_handover(numbers[rec["customer_id"]], False)
                st.rerun(scope="fragment")


live_board()

with st.expander("Demo controls"):
    st.caption("Clear all WhatsApp conversations so the next rehearsal starts clean. The current ones are "
               "moved to a backup file, not deleted. The bot keeps running.")
    sure = st.checkbox("I want to clear the live conversations")
    if st.button("Reset demo", disabled=not sure):
        backup = conversations.reset()
        st.success(f"Cleared. Backup: {backup}" if backup else "Nothing to clear.")

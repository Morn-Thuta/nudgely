import html

import streamlit as st

from lib import REGEN_LIMIT, badge, chats, example_data_note, load_customers, messages, tags
from nudgely import llm

customers = load_customers()
ids = list(customers.customer_id)
names = dict(zip(customers.customer_id, customers.name))

cid = st.session_state.get("customer_id", ids[0])
cid = st.selectbox("Customer", ids, index=ids.index(cid) if cid in ids else 0, format_func=lambda i: names[i])
st.session_state["customer_id"] = cid
c = customers[customers.customer_id == cid].iloc[0]

example_data_note("customers.csv", "chats.json", "tags.json", "messages.json")
st.markdown(f"## {c['name']} &nbsp; {badge(c.label)}", unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Uplift if messaged", f"+{c.uplift:.1%}")
m2.metric("Return anyway", f"{c.p_no_msg:.0%}")
m3.metric("Visits / month", c.get("visits_per_month", "-"))
m4.metric("Days since last visit", c.get("days_since_last_visit", "-"))

left, right = st.columns([1.1, 1])

with left:
    st.markdown("#### Chat history")
    chat = chats().get(cid, [])
    if not chat:
        st.caption("No chats for this customer.")
    for m in chat:
        mine = m["from"] == "store"
        bg, align = ("#DCF8C6", "flex-end") if mine else ("#F3F4F6", "flex-start")
        who = "Kampung Fresh" if mine else c["name"].split()[0]
        st.markdown(
            f"<div style='display:flex;justify-content:{align};margin:4px 0'>"
            f"<div style='background:{bg};color:#111;padding:8px 12px;border-radius:12px;max-width:80%'>"
            f"<div style='font-size:0.75em;color:#6B7280'>{who} · {m['date']}</div>{html.escape(m['text'])}</div></div>",
            unsafe_allow_html=True)

with right:
    st.markdown("#### What the AI remembered")
    t = tags().get(cid)
    if not t:
        st.caption("No tags extracted yet.")
    else:
        for tag in t.get("tags", []):
            st.markdown(f"**{tag['type'].replace('_', ' ')}**: {tag['value']}  \n> “{tag['evidence']}”")
        st.caption(f"Sentiment: {t.get('sentiment', '-')} · Best hook: {t.get('best_hook', '-')}"
                   + (f" · Avoid: {t['avoid']}" if t.get("avoid") else ""))
        if t.get("open_promise"):
            st.caption(f"Open promise: {t['open_promise']}")

    st.markdown("#### Draft message")
    msg = messages().get(cid)
    if msg:
        st.success(msg["message"])
        st.caption(f"Why: {msg.get('reason', '')} · Tags used: {', '.join(msg.get('tags_used', []))} · "
                   f"{len(msg['message'])}/300 chars")
        problems = llm.check_message(msg, c.label)
        if problems:
            st.error("Rule check failed: " + "; ".join(problems))
    else:
        st.caption("No draft yet.")

    used = st.session_state.get("regen_count", 0)
    can = llm.available() and t and used < REGEN_LIMIT
    if st.button(f"🔄 Regenerate message ({REGEN_LIMIT - used} left)", disabled=not can,
                 help=None if llm.available() else "LLM key not configured"):
        with st.spinner("Writing a new message..."):
            try:
                new = llm.write_message(c.to_dict(), t)
                st.session_state.setdefault("regenerated", {})[cid] = new
                st.session_state["regen_count"] = used + 1
                st.rerun()
            except Exception as e:
                st.error(f"Could not regenerate: {e}")

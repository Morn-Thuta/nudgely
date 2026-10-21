import streamlit as st

from lib import badge, campaign_id, draft_problems, example_data_note, header, load_customers, mantago_client, messages, plan_campaign, send_campaign
from nudgely import llm

header("Campaign", "Choose an audience, including its no-message comparison group, then review the drafts.")
example_data_note("customers.csv", "messages.json")

customers = load_customers()
n = len(customers)

c1, c2 = st.columns(2)
budget = c1.slider("Audience size (includes holdout)", 1, n, min(10, n))
holdout = c2.slider("Holdout % (comparison group, not messaged)", 0, 50, 10, step=5)

plan = plan_campaign(customers, budget, holdout)
msgs = messages()
to_msg = plan[plan.group == "Will message"]
held = plan[plan.group == "Held out"]
skipped = plan[plan.group == "Skipped"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Will message", len(to_msg))
m2.metric("Held out", len(held))
m3.metric("Skipped", len(skipped), help="Messages saved vs “message everyone”")
m4.metric("Expected extra visits", f"{to_msg.uplift.sum():.1f}",
          help="Sum of each messaged customer's uplift: visits we expect *because* of the message")

tab_msg, tab_hold, tab_skip = st.tabs([f"📤 Will message ({len(to_msg)})", f"⏸ Held out ({len(held)})",
                                       f"⏭ Skipped ({len(skipped)})"])

with tab_msg:
    for _, r in to_msg.iterrows():
        m = msgs.get(r.customer_id, {})
        problems = llm.check_message(m, r.label) if m else ["no draft"]
        with st.container(border=True):
            st.markdown(f"**{r['name']}** &nbsp; {badge(r.label)} &nbsp; "
                        f"<span style='color:#6B7280;font-size:0.85em'>{r.reason}</span>", unsafe_allow_html=True)
            if m:
                st.write(m["message"])
                st.caption(f"Why: {m.get('reason', '')}")
            if problems:
                st.error("Rule check: " + "; ".join(problems))
            if r.mantago_client_id:
                st.caption("📱 Mapped to a real MantaGO test account: this one will really be sent.")

with tab_hold:
    st.caption("These customers would have been messaged, but are randomly held back. "
               "Comparing them with the messaged group shows the true lift.")
    st.dataframe(held[["name", "label", "reason"]], hide_index=True, width="stretch")

with tab_skip:
    st.dataframe(skipped[["name", "label", "reason"]], hide_index=True, width="stretch")

st.divider()
real = int((to_msg.mantago_client_id != "").sum())
simulate = st.toggle("Rehearsal mode — simulate all messages", value=True)
live = False if simulate else mantago_client() is not None
st.markdown(f"**{len(to_msg)} selected recipients.** {real} are mapped to MantaGO test phones"
            + ("" if live else " (MantaGO keys not set, so they'll be marked ready)")
            + f", {len(to_msg) - real} are simulated demo customers.")

if simulate:
    st.info("Rehearsal mode: no messages leave the app, including mapped test accounts.")
problems = draft_problems(plan, msgs)
if problems:
    st.warning(f"{len(problems)} selected customers have missing or invalid drafts. Complete them or reduce the audience before continuing.")
if not simulate and real:
    st.caption("Only use mapped team test accounts that have opted in and are eligible for channel messaging.")
key = campaign_id(plan, msgs, simulate)
confirm = st.checkbox("I've previewed every message; any live test recipients have opted in", key=f"review_{key}")
completed = key in st.session_state.get("completed_campaigns", [])
if st.button("Simulate campaign" if simulate else "Send campaign", type="primary", disabled=not confirm or completed or bool(problems) or to_msg.empty):
    with st.spinner("Sending through MantaGO..."):
        st.session_state["send_log"] = send_campaign(plan, msgs, simulate=simulate)
        st.session_state.setdefault("completed_campaigns", []).append(key)
        st.session_state["last_plan"] = plan
        st.rerun()

log = st.session_state.get("send_log")
if log is not None:
    st.info("Last campaign finished processing. Check each status; simulated and failed rows are not live deliveries.")
    st.dataframe(log[["name", "status", "mantago_response"]], hide_index=True, width="stretch")
    st.download_button("Download campaign log", log[["timestamp", "customer_id", "name", "status"]].to_csv(index=False),
                       "nudgely-campaign.csv", "text/csv")
if completed:
    st.caption("This exact campaign has already run in this session. Change the audience or drafts for a new campaign.")

import streamlit as st

from lib import badge, md, campaign_id, draft_problems, example_data_note, header, load_customers, mantago_client, messages, plan_campaign, send_campaign
from nudgely import llm

header("A thoughtful nudge, ready to go.", "Build your audience, review each message and choose how to send.")
st.markdown('<div class="section-label">01 / Choose your audience</div>', unsafe_allow_html=True)
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

st.markdown('<div class="section-label">02 / Review your messages</div>', unsafe_allow_html=True)
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
                st.markdown(md(m["message"]))
                st.caption(f"Why: {md(m.get('reason', ''))}")
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
st.markdown('<div class="section-label">03 / Review & launch</div>', unsafe_allow_html=True)
real = int((to_msg.mantago_client_id != "").sum())

mode_col, confirm_col = st.columns([1, 1.4], vertical_alignment="center")
simulate = mode_col.toggle("Rehearsal mode - simulate all messages", value=True)
missing_keys = not simulate and real and mantago_client() is None  # never touch MantaGO in rehearsal
key = campaign_id(plan, msgs, simulate)
confirm = confirm_col.checkbox("I've previewed every message; any live test recipients have opted in",
                               key=f"review_{key}")

st.caption(f"{len(to_msg)} recipients - {real} mapped to MantaGO test phones"
           + (" (MantaGO keys not set, so they'll be marked ready)" if missing_keys else "")
           + f", {len(to_msg) - real} simulated demo customers."
           + (" Rehearsal mode: nothing leaves the app." if simulate else ""))

problems = draft_problems(plan, msgs)
if problems:
    st.warning(f"{len(problems)} selected customers have missing or invalid drafts. Complete them or reduce the audience before continuing.")
if not simulate and real:
    st.caption("Only use mapped team test accounts that have opted in and are eligible for channel messaging.")

completed = key in st.session_state.get("completed_campaigns", [])
if st.button("Simulate campaign" if simulate else "Send campaign", type="primary",
             disabled=not confirm or completed or bool(problems) or to_msg.empty):
    with st.spinner("Sending through MantaGO..."):
        st.session_state["send_log"] = send_campaign(plan, msgs, simulate=simulate)
        st.session_state.setdefault("completed_campaigns", []).append(key)
        st.session_state["last_plan"] = plan
        st.session_state["just_sent"] = (len(to_msg), simulate)
        st.rerun()

# One clear answer to "did that do anything?", right where the button was.
sent = st.session_state.pop("just_sent", None)
if sent:
    count, was_simulated = sent
    st.success(f"Done - {count} messages {'simulated' if was_simulated else 'sent'}. "
               f"{'Nothing left the app.' if was_simulated else 'Check each status on Results.'} "
               "The full log is on the Results page.")
elif completed:
    st.caption("This exact campaign has already run in this session. Change the audience or drafts for a new campaign.")

if st.session_state.get("send_log") is not None and st.button("Open Results →"):
    st.switch_page("views/results.py")

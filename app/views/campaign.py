import streamlit as st

from lib import badge, md, campaign_id, draft_problems, example_data_note, header, load_customers, mantago_client, messages, plan_campaign, send_campaign
from nudgely import llm

header("Plan your campaign.",
       "Choose how many people to reach, read what each of them will get, then send.")
st.caption("Every customer has already been scored by the model, and their message is already written. "
           "Nothing leaves the app until you press the button in step 3.")

st.markdown('<div class="section-label">Step 1 &middot; Who gets a message</div>', unsafe_allow_html=True)
example_data_note("customers.csv", "messages.json")

customers = load_customers()
n = len(customers)

c1, c2 = st.columns(2)
budget = c1.slider("How many customers to reach", 1, n, min(10, n),
                   help="Customers are ranked by how much a message would change them. This takes the top few.")
holdout = c2.slider("Keep this share back as a comparison group (%)", 0, 50, 10, step=5,
                    help="These people get nothing on purpose. Comparing them with the messaged group later "
                         "is the only way to know the campaign actually worked.")

plan = plan_campaign(customers, budget, holdout)
msgs = messages()
to_msg = plan[plan.group == "Will message"]
held = plan[plan.group == "Held out"]
skipped = plan[plan.group == "Skipped"]

m1, m2, m3, m4 = st.columns(4)
m1.metric("Getting a message", len(to_msg))
m2.metric("Kept back to compare", len(held))
m3.metric("Not worth messaging", len(skipped),
          help="People a message would barely change - either they're coming back anyway, or nothing will bring them back. Skipping them saves messages.")
m4.metric("Extra visits expected", f"{to_msg.uplift.sum():.1f}",
          help="Visits we expect to get *because* of these messages, on top of who would have come back anyway. A model estimate, not a measurement.")

st.markdown('<div class="section-label">Step 2 &middot; Read what they will get</div>', unsafe_allow_html=True)
with st.expander(f"Show the {len(to_msg)} messages, and who is left out", expanded=True):
    tab_msg, tab_hold, tab_skip = st.tabs([f"📤 Getting a message ({len(to_msg)})", f"⏸ Kept back ({len(held)})",
                                           f"⏭ Not messaged ({len(skipped)})"])

    with tab_msg:
        st.caption("Written for each person from their own chat history. Read them - you are signing off on these.")
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
        st.caption("These people would have been messaged, but are held back at random. "
                   "Comparing them with the messaged group is what proves the campaign worked.")
        st.dataframe(held[["name", "label", "reason"]], hide_index=True, width="stretch")

    with tab_skip:
        st.caption("Everyone the campaign leaves alone, and why.")
        st.dataframe(skipped[["name", "label", "reason"]], hide_index=True, width="stretch")

st.divider()
st.markdown('<div class="section-label">Step 3 &middot; Send it</div>', unsafe_allow_html=True)
real = int((to_msg.mantago_client_id != "").sum())

mode_col, confirm_col = st.columns([1, 1.4], vertical_alignment="center")
simulate = mode_col.toggle("Practice run - nothing is actually sent", value=True)
missing_keys = not simulate and real and mantago_client() is None  # never touch MantaGO in rehearsal
key = campaign_id(plan, msgs, simulate)
confirm = confirm_col.checkbox("I've read every message, and any real test recipients have opted in",
                               key=f"review_{key}")

st.caption(f"{len(to_msg)} people will be messaged. {real} of them are real MantaGO test phones"
           + (" (no MantaGO keys set, so they'll just be marked ready)" if missing_keys else "")
           + f"; the other {len(to_msg) - real} are demo customers and are always simulated."
           + (" Practice run is on, so nothing leaves the app." if simulate else ""))

problems = draft_problems(plan, msgs)
if problems:
    st.warning(f"{len(problems)} of the chosen customers have a missing or invalid message. Fix those drafts, or reach fewer people, before sending.")
if not simulate and real:
    st.caption("Only use team test accounts that have opted in and are eligible for channel messaging.")

completed = key in st.session_state.get("completed_campaigns", [])
if st.button("Run the practice campaign" if simulate else "Send the campaign for real", type="primary",
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
               f"{'Nothing left the app.' if was_simulated else 'Check each one on Results.'} "
               "The full log is on the Results page.")
elif completed:
    st.caption("This exact campaign has already run in this session. Change who you're reaching, or the messages, for a new one.")

if st.session_state.get("send_log") is not None and st.button("See the results →"):
    st.switch_page("views/results.py")

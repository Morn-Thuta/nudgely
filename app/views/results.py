import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from lib import BRAND, header, summary

header("Know what made the difference.", "Explore historical evidence, campaign delivery and the outcomes still to measure.")

s = summary()
if not s:
    st.warning("Model results not found. Run `python notebooks/train_uplift.py` to create data/uplift_summary.json.")
    st.stop()

st.caption(f"Dataset: {s['dataset']}. Test set: {s['n_test']:,} customers the model never saw in training.")

c1, c2, c3 = st.columns(3)
c1.metric("Visit rate, no message", f"{s['visit_rate_no_msg']:.1%}")
c2.metric("Visit rate, got message", f"{s['visit_rate_msg']:.1%}",
          f"+{s['visit_rate_msg'] / s['visit_rate_no_msg'] - 1:.0%}")
ci = s.get("top30_capture_ci90")
c3.metric("Extra visits captured by our top 30%", f"{s['top30_capture_share']:.0%}",
          f"{s['top30_capture_share'] / 0.3:.1f}x vs random 30%",
          help=f"90% bootstrap interval: {ci[0]:.0%} to {ci[1]:.0%}. Lift is small (under 1 point), so this is noisy."
          if ci else None)

left, right = st.columns(2)

with left:
    st.markdown("#### Message vs no message")
    fig = go.Figure()
    fig.add_bar(x=["No message", "Got message"], y=[s["visit_rate_no_msg"], s["visit_rate_msg"]],
                marker_color=["#9CA3AF", BRAND],
                text=[f"{s['visit_rate_no_msg']:.1%}", f"{s['visit_rate_msg']:.1%}"], textposition="outside")
    fig.update_layout(yaxis_tickformat=".0%", height=340, margin=dict(t=20, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

with right:
    st.markdown("#### Top 30% by model vs random 30%")
    fig = go.Figure()
    fig.add_bar(x=["Random 30%", "Nudgely top 30%"], y=[0.30, s["top30_capture_share"]],
                marker_color=["#9CA3AF", BRAND],
                text=["30%", f"{s['top30_capture_share']:.0%}"], textposition="outside")
    fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Share of all extra visits", height=340,
                      margin=dict(t=20, b=10), showlegend=False)
    st.plotly_chart(fig, width="stretch")

st.markdown("#### Lift by decile")
st.caption("Customers sorted by the model's uplift score into 10 groups. Real visit rate with message minus without, "
           "measured on the randomised test. The left groups should show the biggest lift.")
dec = pd.DataFrame(s["deciles"])
fig = go.Figure()
fig.add_bar(x=dec.decile.astype(str), y=dec.observed_uplift,
            marker_color=[BRAND if d <= 3 else "#9CA3AF" for d in dec.decile])
fig.update_layout(xaxis_title="Decile (1 = highest predicted uplift)", yaxis_title="Observed lift in visit rate",
                  yaxis_tickformat=".1%", height=340, margin=dict(t=20, b=10))
st.plotly_chart(fig, width="stretch")

plan = st.session_state.get("last_plan")
if plan is not None:
    msg = plan[plan.group == "Will message"]
    st.markdown("#### This campaign")
    a, b, c = st.columns(3)
    log = st.session_state.get("send_log")
    a.metric("Confirmed live sends", int((log.status == "sent").sum()) if log is not None else 0)
    b.metric("Expected extra visits", f"{msg.uplift.sum():.1f}")
    c.metric("Messages saved vs message-everyone", int((plan.group == "Skipped").sum()))
    st.caption("Expected visits are model estimates for the planned recipients, not measured campaign outcomes. Public-dataset charts above are separate from this campaign.")
    if log is not None:
        st.dataframe(log[["name", "status"]], hide_index=True, width="stretch")
        st.download_button("Download campaign log", log[["timestamp", "customer_id", "name", "status"]].to_csv(index=False), "nudgely-campaign.csv", "text/csv")

st.markdown("#### Limitations")
st.markdown(
    "- Results come from public datasets (Lenta, Hillstrom), not a live Kampung Fresh test yet.  \n"
    "- Customers and chats in this demo are fictional.  \n"
    f"- Targeting uses behaviour only: {', '.join(s['features_dropped'])} are excluded from the model.  \n"
    "- A real pilot needs 2 to 4 weeks, with the holdout group measured the same way."
)

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from field import customer_field
from lib import BRAND, campaign_results, header, load_customers, summary

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

st.markdown("#### Your customers, in one picture")
st.caption("The charts above are how well the model separates customers in general. This is what "
           "it decided about yours: every customer placed by how recently they visited, what they "
           "spend, and how much a message would change them.")
customers = load_customers()
field_cols = st.columns(4)
field_cols[0].metric("Customers scored", len(customers))
for field_col, field_label in zip(field_cols[1:], ["Persuadable", "Sure Thing", "Lost Cause"]):
    field_col.metric(field_label, int((customers.label == field_label).sum()))
customer_field(customers)

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

st.markdown("### Your campaigns")
st.caption("Measured from your own sends: everyone messaged, against the holdout who were not. "
           "Blank outcomes are customers whose window has not closed yet.")

runs = campaign_results()
if runs is None:
    st.info("No campaign has been sent yet. Once you send one, every recipient and every held-out "
            "customer is written to data/campaign_log.csv, and the real return rates appear here.")
else:
    done = runs[runs.returned.isin([0, 1])]
    if done.empty:
        st.info(f"{len(runs)} customers logged across {runs.campaign_id.nunique()} campaign(s), but no "
                "outcomes recorded yet. Run `python scripts/record_returns.py --close` once the "
                "30-day window has passed.")
    else:
        messaged = done[done.group == "messaged"]
        holdout = done[done.group == "holdout"]
        back_m, n_m = int(messaged.returned.sum()), len(messaged)
        back_h, n_h = int(holdout.returned.sum()), len(holdout)
        rate_m = back_m / n_m if n_m else 0.0
        rate_h = back_h / n_h if n_h else 0.0

        a, b, c = st.columns(3)
        a.metric("Messaged who came back", f"{back_m} of {n_m}", f"{rate_m:.0%}")
        b.metric("Holdout who came back", f"{back_h} of {n_h}", f"{rate_h:.0%}" if n_h else "no holdout yet")
        if n_h:
            c.metric("Measured lift", f"{rate_m - rate_h:+.1%}",
                     help="Return rate of messaged customers minus the holdout. This is the number "
                          "that says the campaign worked.")
        else:
            c.metric("Measured lift", "-", help="Needs a holdout to compare against.")

        left, right = st.columns(2)
        with left:
            st.markdown("#### Came back: messaged vs holdout")
            fig = go.Figure()
            fig.add_bar(x=["Holdout", "Messaged"], y=[rate_h, rate_m],
                        marker_color=["#9AA8A0", BRAND], text=[f"{back_h}/{n_h}", f"{back_m}/{n_m}"],
                        textposition="outside")
            fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Came back", height=340,
                              margin=dict(t=20, b=10), showlegend=False)
            st.plotly_chart(fig, width="stretch")

        with right:
            st.markdown("#### By month")
            by = done.copy()
            by["month"] = pd.to_datetime(by.sent_at, errors="coerce").dt.to_period("M").astype(str)
            grouped = by.groupby(["month", "group"]).returned.agg(["sum", "count"]).reset_index()
            grouped["rate"] = grouped["sum"] / grouped["count"]
            fig = go.Figure()
            for name, colour in (("messaged", BRAND), ("holdout", "#9AA8A0")):
                part = grouped[grouped.group == name]
                fig.add_bar(x=part.month, y=part.rate, name=name.title(), marker_color=colour)
            fig.update_layout(barmode="group", yaxis_tickformat=".0%", yaxis_title="Came back",
                              xaxis_type="category", height=340, margin=dict(t=20, b=10))
            st.plotly_chart(fig, width="stretch")

        st.caption(f"{len(runs) - len(done)} of {len(runs)} logged customers are still inside their window.")

st.markdown("#### Limitations")
st.markdown(
    "- Results come from public datasets (Lenta, Hillstrom), not a live Kampung Fresh test yet.  \n"
    "- Customers and chats in this demo are fictional.  \n"
    f"- Targeting uses behaviour only: {', '.join(s['features_dropped'])} are excluded from the model.  \n"
    "- A real pilot needs 2 to 4 weeks, with the holdout group measured the same way."
)

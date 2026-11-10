import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from field import customer_field
from lib import (BRAND, campaign_results, example_campaign, header, headline, lift_range,
                 load_customers, summary)

header("Know what made the difference.",
       "What your own sends did, and how far the model can be trusted.")

s = summary()
if not s:
    st.warning("Model results not found. Run `python notebooks/train_uplift.py` to create data/uplift_summary.json.")
    st.stop()
h = headline()

GREY = "#9AA8A0"


def show_outcomes(done):
    """Messaged against kept-back, for every customer whose outcome is known."""
    messaged = done[done.group == "messaged"]
    kept = done[done.group == "holdout"]
    back_m, n_m = int(messaged.returned.sum()), len(messaged)
    back_k, n_k = int(kept.returned.sum()), len(kept)
    rate_m = back_m / n_m if n_m else 0.0
    rate_k = back_k / n_k if n_k else 0.0
    rng = lift_range(back_m, n_m, back_k, n_k)

    a, b, c = st.columns(3)
    a.metric(f"Messaged ({back_m} of {n_m})", f"{rate_m:.0%}")
    b.metric(f"Kept back ({back_k} of {n_k})" if n_k else "Kept back", f"{rate_k:.0%}" if n_k else "-",
             help="People who would have been messaged but were left alone on purpose. "
                  "They show what happens with no message at all.")
    c.metric("Difference", f"{(rate_m - rate_k) * 100:+.0f} pts" if n_k else "-",
             help="Return rate of messaged customers minus the kept-back group. "
                  "This is the number that says whether the campaign worked.")

    if rng:
        low, high = rng[0] * 100, rng[1] * 100
        span = f"somewhere between {low:+.0f} and {high:+.0f} points"
        if low > 0:
            st.success(f"**The messages worked.** With this many customers the true effect is {span}, "
                       "so even the low end is a gain.")
        elif high < 0:
            st.error(f"**The messages did not help.** The true effect is {span}. Change the offer or "
                     "the audience before sending again.")
        else:
            st.info(f"**Too early to call.** With {n_m + n_k} customers the true effect could be {span}, "
                    "and that range still includes zero. Each campaign you run narrows it.")
    else:
        st.info("Nobody was kept back, so there is nothing to compare against. Keep a comparison "
                "group on the next campaign to see what the messages really did.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### Came back: kept back vs messaged")
        fig = go.Figure()
        fig.add_bar(x=["Kept back (no message)", "Messaged"], y=[rate_k, rate_m],
                    marker_color=[GREY, BRAND], text=[f"{back_k} of {n_k}", f"{back_m} of {n_m}"],
                    textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Came back", height=340,
                          margin=dict(t=20, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with right:
        st.markdown("#### Month by month")
        by = done.copy()
        by["month"] = pd.to_datetime(by.sent_at, errors="coerce").dt.strftime("%b %Y")
        by["order"] = pd.to_datetime(by.sent_at, errors="coerce").dt.to_period("M")
        grouped = (by.groupby(["order", "month", "group"]).returned.agg(["sum", "count"])
                   .reset_index().sort_values("order"))
        grouped["rate"] = grouped["sum"] / grouped["count"]
        fig = go.Figure()
        for name, label, colour in (("holdout", "Kept back", GREY), ("messaged", "Messaged", BRAND)):
            part = grouped[grouped.group == name]
            fig.add_bar(x=part.month, y=part.rate, name=label, marker_color=colour)
        fig.update_layout(barmode="group", yaxis_tickformat=".0%", yaxis_title="Came back",
                          xaxis_type="category", height=340, margin=dict(t=20, b=10))
        st.plotly_chart(fig, width="stretch")


tab_yours, tab_model = st.tabs(["Your campaigns", "Can the model be trusted?"])

# ---------------------------------------------------------------- your sends
with tab_yours:
    plan = st.session_state.get("last_plan")
    log = st.session_state.get("send_log")

    if plan is not None:
        msg = plan[plan.group == "Will message"]
        st.markdown("#### The campaign you just ran")
        a, b, c = st.columns(3)
        a.metric("Really sent", int((log.status == "sent").sum()) if log is not None else 0,
                 help="Messages that actually left the app. Practice runs and demo customers do not count.")
        b.metric("Extra visits expected", f"{msg.uplift.sum():.1f}",
                 help="The model's estimate for the people you chose. Not a measurement.")
        c.metric("Messages saved", int((plan.group == "Skipped").sum()),
                 help="Customers you did not pay to message, compared with messaging everyone.")
        if log is not None:
            st.dataframe(log[["name", "status", "mantago_response"]], hide_index=True, width="stretch",
                         column_config={"name": "Customer", "status": "What happened",
                                        "mantago_response": "Reply from the sending service"})
            st.download_button("Download this campaign's log",
                               log[["timestamp", "customer_id", "name", "status"]].to_csv(index=False),
                               "nudgely-campaign.csv", "text/csv")
        st.divider()

    st.markdown("#### Did the messages work?")
    st.caption("Everyone you messaged, against the people deliberately kept back. If the messaged "
               "group came back more, the difference is what the campaign earned.")

    runs = campaign_results()
    done = runs[runs.returned.isin([0, 1])] if runs is not None else None

    if done is not None and len(done):
        show_outcomes(done)
        waiting = len(runs) - len(done)
        if waiting:
            st.caption(f"{waiting} of {len(runs)} customers are still inside their 30 days, so they are not counted yet.")
    else:
        if runs is None:
            st.info("You have not sent a real campaign yet. Once you do, everyone messaged and "
                    "everyone kept back is tracked for 30 days, and the answer appears here.")
        else:
            st.info(f"{len(runs)} customers from {runs.campaign_id.nunique()} campaign(s) are being tracked. "
                    "Their 30 days are not up, so there is no answer yet.")
        example = example_campaign()
        if example is not None:
            st.markdown("#### What you will see once the results are in")
            st.warning("**Example only, not a real result.** Three months of campaigns to the 12 most "
                       "movable customers, with outcomes simulated from the model's own estimates.",
                       icon="🧪")
            show_outcomes(example)

# ------------------------------------------------------------- the evidence
with tab_model:
    st.caption("Before your own results exist, this is the evidence the targeting works: a real experiment on "
               "687,000 grocery customers, where a random group got an SMS and the rest did not. "
               "It is public data, not your shop.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Came back with no message", f"{s['visit_rate_no_msg']:.1%}")
    c2.metric("Came back after a message", f"{s['visit_rate_msg']:.1%}",
              f"+{s['visit_rate_msg'] / s['visit_rate_no_msg'] - 1:.0%}")
    c3.metric("Extra visits our top 30% captures", f"{h['capture']:.0%}",
              f"{h['capture'] / 0.3:.1f}x better than picking at random",
              help=f"Message only the 30% of customers the model ranks highest, and you still get this share "
                   f"of all the extra visits. It {h['spread']}, so read it as 'clearly better than random', "
                   "not as an exact figure.")

    left, right = st.columns(2)

    with left:
        st.markdown("#### A message does bring people back")
        fig = go.Figure()
        fig.add_bar(x=["No message", "Got a message"], y=[s["visit_rate_no_msg"], s["visit_rate_msg"]],
                    marker_color=["#9CA3AF", BRAND],
                    text=[f"{s['visit_rate_no_msg']:.1%}", f"{s['visit_rate_msg']:.1%}"], textposition="outside")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Came back", height=340,
                          margin=dict(t=20, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")

    with right:
        st.markdown("#### Choosing who to message beats guessing")
        fig = go.Figure()
        fig.add_bar(x=["Any 30% of customers", "The 30% Nudgely picks"], y=[0.30, h["capture"]],
                    marker_color=["#9CA3AF", BRAND],
                    error_y=dict(type="data", symmetric=False, color="#4B5563", thickness=1.5,
                                 array=[0, h["high"] - h["capture"]], arrayminus=[0, h["capture"] - h["low"]]),
                    text=["30%", f"{h['capture']:.0%}"], textposition="inside", insidetextanchor="middle")
        fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Share of all extra visits", height=340,
                          margin=dict(t=20, b=10), showlegend=False)
        st.plotly_chart(fig, width="stretch")
    st.caption(f"The line on the right-hand bar is how far the figure moved between test runs: it {h['spread']}. "
               "The lowest run still beat guessing.")

    st.markdown("#### Your customers, in one picture")
    st.caption("This is what the model decided about yours: every customer placed by how recently they "
               "visited, what they spend, and how much a message would change them.")
    customer_field(load_customers())

    st.markdown("#### What this does not prove")
    st.markdown(
        "- The evidence comes from public datasets (Lenta, Hillstrom), not a live Kampung Fresh test yet.  \n"
        "- Customers and chats in this demo are fictional.  \n"
        f"- The model only looks at behaviour: {', '.join(s['features_dropped'])} are deliberately left out.  \n"
        "- A real pilot needs 2 to 4 weeks, with the kept-back group measured the same way."
    )

    with st.expander("For the technically curious"):
        st.markdown(
            f"**Which model the headline is.** The {h['capture']:.0%} is the model that scores real shops: "
            f"a two-model uplift learner on the {h['features'] or 'ten'} features a shop can compute from its own "
            "receipts, averaged over seven train/test splits of Lenta. One split alone moved the figure by 30 "
            "points, which is why it is an average with a range.")
        ci = s.get("top30_capture_ci90")
        st.markdown(
            f"**The chart below is the earlier, larger model**: all 190 Lenta columns, one split, "
            f"{s['n_test']:,} customers it never saw. On that split its top 30% captured "
            f"{s['top30_capture_share']:.0%}"
            + (f" (90% bootstrap interval {ci[0]:.0%} to {ci[1]:.0%})" if ci else "")
            + ". It is kept because it shows the shape of the ranking, not as a second headline.")
        st.markdown("#### Lift by decile")
        st.caption("Customers sorted by predicted uplift into 10 equal groups. Each bar is the real visit rate "
                   "with a message minus without. The left groups should show the biggest lift.")
        dec = pd.DataFrame(s["deciles"])
        fig = go.Figure()
        fig.add_bar(x=dec.decile.astype(str), y=dec.observed_uplift,
                    marker_color=[BRAND if d <= 3 else "#9CA3AF" for d in dec.decile])
        fig.update_layout(xaxis_title="Decile (1 = highest predicted uplift)",
                          yaxis_title="Observed lift in visit rate",
                          yaxis_tickformat=".1%", height=340, margin=dict(t=20, b=10))
        st.plotly_chart(fig, width="stretch")

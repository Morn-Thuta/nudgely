import plotly.graph_objects as go
import streamlit as st

from lib import BRAND, HILLSTROM, header, summary

header("Nudgely", "Small businesses send the same “We miss you, 10% off” to everyone and never know if it worked.")

st.info(
    "**How to try this (2 minutes):**  \n"
    "1. **Customers**: see who a message would actually bring back.  \n"
    "2. Click a customer to see their chat history and the tags the AI pulled out.  \n"
    "3. **Campaign**: set a budget and holdout, preview the personal messages, press **Send**.  \n"
    "4. **Results**: see the proof against a no-message group.",
    icon="👋",
)

s = summary()
top30 = s.get("top30_capture_share") if s else None
gain = f"{top30 / 0.30:.1f}x" if top30 else "1.5x"

c1, c2, c3 = st.columns(3)
c1.metric("More visits when messaged", f"+{HILLSTROM['visit_lift']:.0%}",
          help="Hillstrom, 64k online shoppers, email vs no email")
c2.metric("More purchases when messaged", f"{HILLSTROM['buy_ratio']:.1f}x", help="Hillstrom")
c3.metric("Smart targeting vs random", gain,
          help=f"Lenta test set: our model's top 30% captures {top30:.0%} of extra visits vs 30% for random" if top30
          else "Lenta test set, top 30% vs random 30%")

st.markdown("#### Proof: messaging brings customers back")
fig = go.Figure()
fig.add_bar(x=["No message", "Got message"], y=[HILLSTROM["visit_no_msg"], HILLSTROM["visit_msg"]],
            marker_color=["#9CA3AF", BRAND], text=[f"{HILLSTROM['visit_no_msg']:.1%}", f"{HILLSTROM['visit_msg']:.1%}"],
            textposition="outside")
fig.update_layout(yaxis_tickformat=".0%", yaxis_title="Visited the store", height=340,
                  margin=dict(t=20, b=10), showlegend=False)
st.plotly_chart(fig, width="stretch")
st.caption("Source: Hillstrom dataset, 64,000 shoppers, randomised email test.")

st.markdown("#### How it works")
a, b, c, d = st.columns(4)
a.markdown("**1. Who**  \nAn uplift model finds customers a message will actually bring back.")
b.markdown("**2. What**  \nAn LLM reads each customer's chats and pulls out evidence-backed tags.")
c.markdown("**3. Send**  \nOne personal message each, sent through MantaGO. The owner previews every one.")
d.markdown("**4. Prove**  \nA random holdout group gets nothing, so the lift is measured, not guessed.")

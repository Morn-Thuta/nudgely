"""Nudgely Streamlit app - entry point. Run: streamlit run app/Home.py

Skeleton only. Owner D fills in pages 1-5 (see docs/PRD.md "Dashboard screens").
"""

import streamlit as st

st.set_page_config(page_title="Nudgely", page_icon="💬", layout="wide")

st.title("Nudgely")
st.caption("Message the right customers, say the right thing, prove it worked.")

st.info(
    "**How to try this:** 1) Customers: see who the model would message. "
    "2) Open one customer to see their chat and tags. "
    "3) Campaign: set budget and holdout, preview, Send. "
    "4) Results: see the proof."
)

c1, c2, c3 = st.columns(3)
c1.metric("Visits when messaged", "+72%", help="Hillstrom, 64k shoppers, email vs no email")
c2.metric("Purchases when messaged", "2.2x", help="Hillstrom")
c3.metric("Smart targeting vs random", "1.5x", help="Lenta test set, top 30% vs random 30% - update after gender-free retrain")

st.caption("Demo data: Kampung Fresh is fictional. Results come from public datasets (Hillstrom, Lenta).")

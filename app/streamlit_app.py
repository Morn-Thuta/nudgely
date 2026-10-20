"""Nudgely app entry point. Run: streamlit run app/streamlit_app.py"""

import streamlit as st

st.set_page_config(page_title="Nudgely", page_icon="💬", layout="wide")

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/customers.py", title="Customers", icon="👥"),
    st.Page("views/customer_detail.py", title="Customer detail", icon="💬"),
    st.Page("views/campaign.py", title="Campaign", icon="📤"),
    st.Page("views/results.py", title="Results", icon="📈"),
]

with st.sidebar:
    st.markdown("### 💬 Nudgely")
    st.caption("Message the right customers, say the right thing, prove it worked.")
    st.caption("Demo store: **Kampung Fresh** (fictional Singapore grocer)")

st.navigation(pages).run()

st.sidebar.divider()
st.sidebar.caption("Names and chats are fictional. Model results come from public datasets (Lenta, Hillstrom).")

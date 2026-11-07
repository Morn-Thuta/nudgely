"""Nudgely app entry point. Run: streamlit run app/streamlit_app.py"""

import streamlit as st
from design import apply_design
from gate import require_access, sidebar_account

st.set_page_config(page_title="Nudgely", page_icon="💬", layout="wide")
apply_design()

# The landing page stands in front of everything. Nothing below runs until
# someone has signed in or opened the demo.
require_access()

pages = [
    st.Page("views/overview.py", title="Overview", icon="🏠", default=True),
    st.Page("views/customers.py", title="Customers", icon="👥"),
    st.Page("views/customer_detail.py", title="Customer detail", icon="💬"),
    st.Page("views/campaign.py", title="Campaign", icon="📤"),
    st.Page("views/results.py", title="Results", icon="📈"),
]

with st.sidebar:
    st.markdown('<div class="brandmark">nudgely<span>↗</span></div>', unsafe_allow_html=True)
    st.caption("A little nudge. A lasting connection.")
    # Who you are and the way out live at the top, where you look for them,
    # rather than under the fold of whichever page you happen to be on.
    sidebar_account()
    st.markdown('<div class="store-card"><small>YOUR WORKSPACE</small><br><strong>Kampung Fresh</strong><br><small>Singapore · Grocery · Demo</small></div>', unsafe_allow_html=True)

st.navigation(pages).run()

st.sidebar.divider()
st.sidebar.caption("Names and chats are fictional. Model results come from public datasets (Lenta, Hillstrom).")

"""Shared presentation for the customer retention workspace."""
import html
import streamlit as st

def apply_design():
    st.markdown('''<style>
    .stApp{background:#F5F7F5;color:#183B36}.block-container{max-width:1440px;padding-top:2.5rem;padding-bottom:3rem}
    h1,h2,h3{letter-spacing:-.04em!important;color:#163D37}h2{font-size:2rem!important}
    [data-testid="stSidebar"]{background:#123D35}[data-testid="stSidebar"] *{color:#E8F3EE}
    [data-testid="stSidebarNavLink"]{border-radius:10px;margin:5px 0;padding:9px 12px!important}
    [data-testid="stSidebar"] [aria-current="page"]{background:#28574B!important}
    [data-testid="stMetric"]{background:white;border:1px solid #E1EAE5;border-radius:16px;padding:22px 24px;box-shadow:0 3px 10px #153B3504}
    [data-testid="stMetricLabel"]{color:#667D75;font-size:.85rem}[data-testid="stMetricValue"]{color:#173E35;font-weight:650;letter-spacing:-.05em}
    [data-testid="stVerticalBlockBorderWrapper"]>div{border-radius:16px!important;border-color:#DEE7E1!important}
    [data-testid="stDataFrame"]{border:1px solid #E1EAE5;border-radius:14px;overflow:hidden}
    .stButton button,.stDownloadButton button{border-radius:10px;min-height:42px;font-weight:600}
    [role="tablist"]{gap:22px;border-bottom:1px solid #DBE6DF}[role="tab"]{padding:12px 4px;font-weight:600}
    .eyebrow{font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;color:#66877D;margin-bottom:12px}
    .page-heading{padding:4px 0 20px}.page-heading h2{margin:0 0 8px;padding:0}.page-heading p{color:#71837C;margin:0}
    .hero{background:#153F36;border-radius:22px;padding:34px 38px;display:flex;gap:32px;align-items:center;margin:5px 0 26px}
    .hero h1{color:#F5FAF4!important;font-size:2.8rem!important;line-height:1.13;margin:12px 0 16px}
    .hero p{color:#BFCEC5;font-size:15px;line-height:1.7;max-width:520px}.hero .eyebrow{color:#D4EF9B}
    .hero-side{min-width:250px;flex:1;background:#FFFFFF0B;border:1px solid #FFFFFF20;border-radius:18px;padding:24px;transform:rotate(-2deg)}
    .bubble{background:#DDEEC4;border-radius:14px 14px 3px 14px;padding:16px;color:#1B493D;font-size:14px;line-height:1.65;margin:12px 0}
    .pill{display:inline-block;border-radius:99px;padding:5px 10px;background:#ECF4E7;color:#3A6350;font-size:11px;font-weight:600}
    .feature{background:white;border:1px solid #E1EAE5;border-radius:16px;padding:24px;min-height:195px}.feature .num{color:#087F73;font-size:12px;font-weight:700;letter-spacing:.1em}.feature h3{font-size:1.1rem;margin:16px 0 8px}.feature p{font-size:14px;color:#74847D;line-height:1.6}
    .customer-row{display:flex;align-items:center;gap:13px;padding:13px 0;border-bottom:1px solid #EEF2EE}.avatar{width:42px;height:42px;border-radius:13px;background:#E8F0D9;color:#356449;display:flex;align-items:center;justify-content:center;font-weight:700;flex-shrink:0}
    .customer-row .name{font-weight:650;font-size:14px}.customer-row .meta{font-size:12px;color:#7B8B82}.customer-row .score{margin-left:auto;font-size:14px;color:#087F73;font-weight:700}
    .brandmark{font-size:30px;font-weight:750;letter-spacing:-1.2px;padding:12px 0 3px}.brandmark span{color:#D2EF9B!important}
    .store-card{background:#FFFFFF0A;border:1px solid #FFFFFF20;border-radius:12px;padding:16px;margin:22px 0}.store-card small{color:#B1C9BC!important;font-size:11px}
    .section-label{margin:24px 0 14px;font-size:11px;letter-spacing:.13em;font-weight:700;color:#798D82;text-transform:uppercase}
    @media(max-width:800px){.hero{padding:25px;flex-direction:column;align-items:stretch}.hero h1{font-size:2rem!important}.hero-side{transform:none;min-width:0}.block-container{padding-top:1.5rem}.feature{min-height:0}}
    </style>''', unsafe_allow_html=True)

def page_heading(title, subtitle=''):
    st.markdown(f'<div class="page-heading"><div class="eyebrow">Kampung Fresh / Retention workspace</div><h2>{html.escape(title)}</h2><p>{html.escape(subtitle or "")}</p></div>', unsafe_allow_html=True)

def customer_row(name, label, uplift):
    initials = ''.join(part[0] for part in name.split()[:2])
    st.markdown(f'<div class="customer-row"><div class="avatar">{html.escape(initials)}</div><div><div class="name">{html.escape(name)}</div><div class="meta">{html.escape(label)}</div></div><div class="score">+{uplift:.1%}</div></div>', unsafe_allow_html=True)

"""The front door: the landing page, and the sign-in that stands in front of the app.

Nobody reaches a page of the app without passing through here. `require_access`
is called once from streamlit_app.py before the navigation is built; until it
returns, there is no sidebar and no pages.

**This is a demo gate, not production authentication.** Passwords are salted and
hashed properly (PBKDF2-HMAC-SHA256, 240k iterations, compared in constant time)
so no plaintext is ever stored, but everything around that is missing: no email
verification, no password reset, no lockout after repeated guesses, and the user
file sits on whatever machine runs the app. The real thing is Jayden's Supabase
auth in the new web app; when that lands, `_load_users` and `_verify` are the two
functions it replaces.

A demo entrance is deliberate. At finals a judge should be able to open the app
and look around without being handed a password, and a locked door is a worse
demo than an open one.
"""

import binascii
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone

import streamlit as st
from hero import render_hero
from lib import DATA, load_customers, summary

USERS = os.path.join(DATA, "users.json")
ITERATIONS = 240_000
MIN_PASSWORD = 8
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# The landing page is its own world: dark, full bleed, the customer field running
# edge to edge behind the words. The app's light theme resumes once you are
# through the door, so every override here is scoped to this page only.
#
# The field is a Streamlit component, which means an iframe in the normal flow.
# Pinning its container to the viewport puts it behind everything, and because
# the text and form sit above it on z-index, clicks reach the form while drags on
# bare background still reach the canvas.
BG = "#09120E"
HIDE_CHROME = f"""
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{{display:none !important}}
[data-testid="stHeader"]{{background:transparent}}
.stApp{{background:{BG} !important}}
[data-testid="stAppViewContainer"] .block-container{{
  max-width:1320px; padding-top:3.2rem !important; padding-bottom:1rem !important;
  position:relative; z-index:1}}

/* the field, pinned behind the page */
.st-key-fieldbg{{position:fixed; inset:0; z-index:0; pointer-events:auto}}
.st-key-fieldbg iframe{{width:100vw !important; height:100vh !important}}

.gate-brand{{display:flex;align-items:center;gap:11px;margin-bottom:26px}}
.gate-brand i{{width:13px;height:13px;border-radius:50%;background:#3FD79A;
  box-shadow:0 0 0 5px #3FD79A26;flex:none}}
.gate-brand b{{font-size:21px;font-weight:800;letter-spacing:-.02em;color:#EAF3ED}}
.gate-head{{font-size:clamp(2rem,4.4vw,3.6rem);line-height:1.04;letter-spacing:-.04em;
  font-weight:800;color:#F2F8F3;margin:0 0 22px;max-width:15ch;text-wrap:balance}}
.gate-head em{{font-style:normal;color:#3FD79A}}
.gate-sub{{color:#A8BEB1;font-size:16px;line-height:1.65;margin:0;max-width:46ch}}
.gate-pills{{display:flex;gap:8px;flex-wrap:wrap;margin-top:24px}}
.gate-pills span{{border-radius:99px;padding:6px 12px;background:#FFFFFF0F;
  border:1px solid #FFFFFF1F;color:#BCD2C4;font-size:11.5px;
  font-family:ui-monospace,"Consolas",monospace}}
.gate-foot{{color:#7E9488;font-size:11.5px;line-height:1.55;padding-top:8px}}

/* the sign-in card, and the controls inside it.
   Selectors checked against the running DOM: this Streamlit names the bordered
   container stVerticalBlock and the input shell stTextInputRootElement. */
.st-key-signincard{{
  background:#0E1B16F2 !important; border:1px solid #2A463A !important;
  border-radius:16px !important; backdrop-filter:blur(8px); padding:4px 4px 0}}
[data-testid="stTextInput"] label p, [data-testid="stTab"] p{{color:#C7D9CD !important}}
[data-testid="stTextInputRootElement"]{{
  background:#14241D !important; border-color:#2E4A3D !important}}
[data-testid="stTextInputField"]{{
  background:transparent !important; color:#EAF3ED !important; -webkit-text-fill-color:#EAF3ED}}
[data-testid="stTextInputField"]::placeholder{{color:#6C8578 !important}}
[data-testid="stTextInputRootElement"] svg{{fill:#8AA396}}
[data-testid="stTabs"] [role="tablist"]{{border-bottom-color:#2A463A !important}}
[data-testid="stTab"][aria-selected="true"] p{{color:#3FD79A !important}}
[data-testid="stForm"]{{border:0 !important; padding:0 !important; background:transparent}}
.stButton button[kind="secondary"]{{
  background:#FFFFFF0D !important; border:1px solid #FFFFFF26 !important; color:#EAF3ED !important}}
.stButton button[kind="secondary"]:hover{{border-color:#3FD79A !important}}

/* the "explore more" sections, dark to match */
.more-label{{font-size:11px;letter-spacing:.14em;text-transform:uppercase;font-weight:700;
  color:#7E9488;margin:34px 0 14px}}
.more-grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px}}
.more-grid.three{{grid-template-columns:repeat(auto-fit,minmax(250px,1fr))}}
.more-grid.two{{grid-template-columns:repeat(auto-fit,minmax(310px,1fr))}}
.more-card{{background:#0E1B16CC;border:1px solid #27413688;border-radius:14px;padding:20px;
  min-width:0;backdrop-filter:blur(6px)}}
.more-card .n{{font-family:ui-monospace,"Consolas",monospace;font-size:11.5px;color:#3FD79A}}
.more-card h3{{font-size:16px;font-weight:700;color:#EAF3ED;margin:10px 0 8px;
  display:flex;align-items:center;gap:9px}}
.more-card h3 i{{width:8px;height:8px;border-radius:50%;flex:none}}
.more-card p{{font-size:13.5px;line-height:1.6;color:#A8BEB1;margin:0}}
.more-card .big{{display:block;font-size:34px;font-weight:800;letter-spacing:-.03em;
  color:#F2F8F3;line-height:1;margin-bottom:10px}}
.more-card .spread{{display:block;font-family:ui-monospace,"Consolas",monospace;font-size:11px;
  color:#E0A341;margin-top:10px}}
.more-card ul{{margin:0;padding-left:18px;display:flex;flex-direction:column;gap:7px}}
.more-card li{{font-size:13.5px;line-height:1.55;color:#A8BEB1}}
.more-card li b{{color:#EAF3ED;font-weight:600}}
</style>
"""


# ---- storage -----------------------------------------------------------------

def _load_users():
    if not os.path.exists(USERS):
        return {}
    try:
        with open(USERS, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {}


def _save_users(users):
    os.makedirs(os.path.dirname(USERS), exist_ok=True)
    with open(USERS, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)


def _hash(password, salt):
    return binascii.hexlify(
        hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)).decode()


def _verify(password, record):
    """Constant-time check, so a wrong password cannot be found by timing."""
    try:
        salt = binascii.unhexlify(record["salt"])
    except (KeyError, binascii.Error):
        return False
    return hmac.compare_digest(_hash(password, salt), record.get("hash", ""))


def _create(users, email, name, password):
    salt = os.urandom(16)
    users[email] = {
        "name": name,
        "salt": binascii.hexlify(salt).decode(),
        "hash": _hash(password, salt),
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _save_users(users)


# ---- session -----------------------------------------------------------------

def current_user():
    return st.session_state.get("user")


def sign_out():
    for key in ("user", "demo"):
        st.session_state.pop(key, None)


def _enter(name, demo=False):
    st.session_state["user"] = name
    st.session_state["demo"] = demo
    st.rerun()


# ---- the door ----------------------------------------------------------------

def require_access():
    """Show the landing page until someone signs in. Returns once they have."""
    if current_user():
        return

    st.markdown(HIDE_CHROME, unsafe_allow_html=True)

    df = load_customers()
    movable = int((df.label == "Persuadable").sum())

    with st.container(key="fieldbg"):
        render_hero(df, height=900, background=True, bg_color=BG)

    words, door = st.columns([1.25, 1], gap="large")

    with words:
        st.markdown(
            '<div class="gate-brand"><i></i><b>Nudgely</b></div>'
            '<h1 class="gate-head">Message the people a message would '
            '<em>actually change</em>.</h1>'
            f'<p class="gate-sub">Every shop blasts the same promotion to everyone. Nudgely '
            f'reads your WhatsApp chats, works out which {movable} of your {len(df)} customers '
            f'are genuinely movable, writes each message from that customer\'s own history, and '
            f'proves the lift against a group it deliberately left alone.</p>'
            '<div class="gate-pills"><span>AI-GNITION 2026 · top ten</span>'
            '<span>Finals 14 Nov 2026</span></div>',
            unsafe_allow_html=True)

    with door:
        with st.container(border=True, key="signincard"):
            tab_in, tab_up = st.tabs(["Sign in", "Create an account"])
            with tab_in:
                _sign_in_form()
            with tab_up:
                _sign_up_form()

        st.markdown(
            '<div class="gate-foot">Just looking? Open the demo — everything works, '
            'on fictional customers.</div>', unsafe_allow_html=True)
        if st.button("Explore the demo", width="stretch"):
            _enter("Demo visitor", demo=True)

        open_more = st.session_state.get("gate_more", False)
        if st.button("Hide the details ↑" if open_more else "Explore more ↓", width="stretch"):
            st.session_state["gate_more"] = not open_more
            st.rerun()

    if st.session_state.get("gate_more"):
        _more()

    st.stop()


def _more():
    """The rest of the pitch, revealed on request so the landing stays one screen."""
    st.markdown('<div style="height:30px"></div>', unsafe_allow_html=True)
    st.markdown('<div class="more-label">How it works</div>', unsafe_allow_html=True)
    steps = [
        ("01 · Listen", "Read the chats",
         "Every message a customer sends is tagged as it arrives: a restock they asked for, a "
         "delivery that went wrong, a party coming up. Evidence has to be quoted from something "
         "the customer actually said."),
        ("02 · Score", "Find who is movable",
         "An uplift model predicts the difference a message makes, not whether someone returns. "
         "Someone returning anyway is a wasted discount; someone gone for good is a wasted "
         "message."),
        ("03 · Write", "Fill an approved template",
         "WhatsApp forbids free text to open a conversation, so one of six approved sentences is "
         "chosen by the customer's strongest tag and its blanks filled. Invent a price and the "
         "message is thrown away, not patched."),
        ("04 · Prove", "Keep a holdout",
         "Some customers are deliberately not messaged. Without them you cannot tell a good "
         "message from a customer who was returning regardless."),
    ]
    cards = "".join(
        f'<div class="more-card"><span class="n">{n}</span><h3>{t}</h3><p>{b}</p></div>'
        for n, t, b in steps)
    st.markdown(f'<div class="more-grid">{cards}</div>', unsafe_allow_html=True)

    s = summary()
    capture = s["top30_capture_share"] if s else None
    ci = s.get("top30_capture_ci90") if s else None
    facts = [
        (f"{capture:.0%}" if capture else "—",
         "of the extra visits captured by messaging the top 30%, against 30% for picking at random",
         f"90% interval {ci[0]:.0%}–{ci[1]:.0%} · the spread is as much the finding as the number"
         if ci else "historical Lenta experiment"),
        ("97%",
         "of tags found across 32 hand-written chats — recall, the number that matters when a "
         "missed complaint becomes a promotion",
         "86% precision · exactly right on 72%"),
        ("3",
         "columns a shop has to hand over: phone, date and amount. Everything the model uses is "
         "derived from those",
         "down from 190 no local grocer records"),
    ]
    st.markdown('<div class="more-label">Where it stands</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="more-grid three">' + "".join(
            f'<div class="more-card"><span class="big">{big}</span><p>{sub}</p>'
            f'<span class="spread">{spread}</span></div>' for big, sub, spread in facts)
        + "</div>", unsafe_allow_html=True)

    st.markdown('<div class="more-label">Honest state</div>', unsafe_allow_html=True)
    working = ["Scoring a real shop from a purchase export",
               "Tagging one message at a time, fast enough for a live webhook",
               "Six approved templates, filled and checked, rejected rather than repaired",
               "A reply bot that answers or hands to a person",
               "Campaign measurement with a holdout and a measured lift"]
    broken = ["<b>No inbound webhook.</b> MantaGO's documented API only sends",
              "<b>No recency feature.</b> Every lapsed customer scores Lost Cause",
              "<b>Sarcasm reads as satisfied</b>, the one tag the test set still misses",
              "<b>Nothing sent to a real customer</b> without approved templates on a "
              "business number"]
    st.markdown(
        '<div class="more-grid two">'
        '<div class="more-card"><h3><i style="background:#3FD79A"></i>Working</h3><ul>'
        + "".join(f"<li>{w}</li>" for w in working) + "</ul></div>"
        '<div class="more-card"><h3><i style="background:#E0A341"></i>Not working yet</h3><ul>'
        + "".join(f"<li>{b}</li>" for b in broken) + "</ul></div></div>",
        unsafe_allow_html=True)

    st.markdown(
        '<div class="gate-foot" style="padding-bottom:24px">Fictional identities and chats · '
        'Lenta and Hillstrom model scores · no live campaign has been sent · accounts are '
        'stored on this machine only</div>', unsafe_allow_html=True)


def _sign_in_form():
    with st.form("sign_in"):
        email = st.text_input("Email", key="in_email", autocomplete="username")
        password = st.text_input("Password", type="password", key="in_pw",
                                 autocomplete="current-password")
        submitted = st.form_submit_button("Sign in", type="primary", width="stretch")

    if not submitted:
        return
    users = _load_users()
    record = users.get(email.strip().lower())
    # One message for both cases, so it does not reveal which emails exist.
    if record and _verify(password, record):
        _enter(record.get("name") or email)
    else:
        st.error("That email and password do not match an account.")


def _sign_up_form():
    with st.form("sign_up"):
        name = st.text_input("Your name", key="up_name")
        email = st.text_input("Email", key="up_email", autocomplete="username")
        password = st.text_input("Password", type="password", key="up_pw",
                                 autocomplete="new-password",
                                 help=f"At least {MIN_PASSWORD} characters.")
        again = st.text_input("Password again", type="password", key="up_pw2",
                              autocomplete="new-password")
        submitted = st.form_submit_button("Create account", type="primary", width="stretch")

    if not submitted:
        return

    email = email.strip().lower()
    users = _load_users()
    problems = []
    if not name.strip():
        problems.append("Enter your name.")
    if not EMAIL.match(email):
        problems.append("That does not look like an email address.")
    elif email in users:
        problems.append("An account already exists for that email.")
    if len(password) < MIN_PASSWORD:
        problems.append(f"Use at least {MIN_PASSWORD} characters for the password.")
    if password != again:
        problems.append("The two passwords do not match.")

    if problems:
        for problem in problems:
            st.error(problem)
        return

    _create(users, email, name.strip(), password)
    _enter(name.strip())


ACCOUNT_CSS = """
<style>
.st-key-accountrow{border:1px solid #FFFFFF1F;border-radius:12px;padding:10px 12px 4px;
  background:#FFFFFF0D;margin-bottom:14px}
.st-key-accountrow .who{font-size:12px;color:#CFE3D7;line-height:1.35;margin-bottom:8px}
.st-key-accountrow .who b{color:#F2F8F3;font-weight:650}
.st-key-accountrow .who span{color:#9FBDAE}
.st-key-accountrow button{background:#FFFFFF12 !important;border:1px solid #FFFFFF2E !important;
  color:#EAF3ED !important;font-size:12.5px !important;padding:5px 10px !important}
.st-key-accountrow button:hover{border-color:#6FE3AC !important;color:#9CF0C8 !important}
</style>
"""


def sidebar_account():
    """Who is signed in, and the way out. Sits at the top of the sidebar."""
    name = current_user()
    if not name:
        return
    st.markdown(ACCOUNT_CSS, unsafe_allow_html=True)
    with st.container(key="accountrow"):
        tail = " <span>· demo</span>" if st.session_state.get("demo") else ""
        st.markdown(f'<div class="who">Signed in as <b>{name}</b>{tail}</div>',
                    unsafe_allow_html=True)
        if st.button("Sign out", width="stretch"):
            sign_out()
            st.rerun()

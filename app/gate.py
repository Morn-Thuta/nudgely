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
from lib import DATA, load_customers

USERS = os.path.join(DATA, "users.json")
ITERATIONS = 240_000
MIN_PASSWORD = 8
EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

# The landing page has to fit one screen without scrolling, so the app's normal
# chrome and generous page padding are pulled in tight for this page only.
HIDE_CHROME = """
<style>
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"]{display:none !important}
[data-testid="stAppViewContainer"] .block-container{
  max-width:1280px; padding-top:1.1rem !important; padding-bottom:0 !important}
[data-testid="stHeader"]{height:0}
.gate-brand{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.gate-brand i{width:11px;height:11px;border-radius:50%;background:#0E9F6E;
  box-shadow:0 0 0 5px #0E9F6E24;flex:none}
.gate-brand b{font-size:17px;font-weight:800;letter-spacing:-.02em;color:#153F36}
.gate-head{font-size:clamp(1.5rem,2.5vw,2.1rem);line-height:1.12;letter-spacing:-.035em;
  font-weight:700;color:#153F36;margin:0 0 8px;text-wrap:balance}
.gate-head em{font-style:normal;color:#0E9F6E}
.gate-sub{color:#5C7268;font-size:14px;line-height:1.6;margin:0 0 4px;max-width:60ch}
.gate-foot{color:#7B8B82;font-size:11.5px;line-height:1.5;padding-top:4px}
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

    field, door = st.columns([1.45, 1], gap="large")

    with field:
        st.markdown(
            '<div class="gate-brand"><i></i><b>Nudgely</b></div>'
            '<h1 class="gate-head">Message the people a message would '
            '<em>actually change</em>.</h1>'
            f'<p class="gate-sub">That is your customer book turning below — height is uplift, '
            f'and the darts fly to the {movable} of {len(df)} customers a nudge would actually '
            f'move. Everyone else is a wasted discount or a wasted message.</p>',
            unsafe_allow_html=True)
        render_hero(df, height=430)

    with door:
        with st.container(border=True):
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

        st.markdown(
            '<div class="gate-foot">AI-GNITION 2026 · top ten · finals 14 Nov<br>'
            'Fictional identities · Lenta and Hillstrom scores · no live campaign sent<br>'
            'Accounts are stored on this machine only</div>', unsafe_allow_html=True)

    st.stop()


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


def sidebar_account():
    """The signed-in footer for the sidebar."""
    name = current_user()
    if not name:
        return
    st.caption(f"Signed in as **{name}**" + ("  ·  demo" if st.session_state.get("demo") else ""))
    if st.button("Sign out", width="stretch"):
        sign_out()
        st.rerun()

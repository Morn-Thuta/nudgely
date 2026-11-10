"""Quick WhatsApp Cloud API test. Run from the repo root.

  python scripts/test_whatsapp.py template --to 6591234567 --yes          # hello_world, works any time
  python scripts/test_whatsapp.py text --to 6591234567 --message "Hi" --yes # needs them to have messaged in 24h

On Meta's free test number, --to must be one of the (max 5) numbers added under
WhatsApp -> API Setup -> "To". Leave out --yes for a dry run.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nudgely.whatsapp import WhatsApp, WhatsAppError  # noqa: E402

HINTS = {
    131030: "Recipient not in the test number's allowed list. Add it under WhatsApp -> API Setup -> To.",
    131047: "Outside the 24-hour window. Ask them to message the number first, or send a template.",
    132001: "Template name or language not found. hello_world uses language en_US.",
    190: "Access token expired or invalid. Temporary tokens last 24 hours; generate a new one.",
    100: "Bad parameter, often a wrong WA_PHONE_NUMBER_ID (use the ID, not the phone number).",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["template", "text"])
    p.add_argument("--to", required=True)
    p.add_argument("--message", default="Hi from Nudgely test. Reply STOP to opt out")
    p.add_argument("--template", default="hello_world")
    p.add_argument("--language", default="en_US")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args()

    try:
        wa = WhatsApp.from_env()
    except ValueError:
        sys.exit("Missing WA_TOKEN / WA_PHONE_NUMBER_ID in .env.")
    what = f"template '{a.template}'" if a.cmd == "template" else f"text: {a.message}"
    if not a.yes:
        sys.exit(f"Dry run. Would send {what} to ...{a.to[-4:]}. Add --yes to send.")
    try:
        r = wa.send_template(a.to, a.template, a.language) if a.cmd == "template" else wa.send_text(a.to, a.message)
        print("Accepted by WhatsApp, message id:", (r.get("messages") or [{}])[0].get("id"))
        print("Check the phone. Delivery status arrives on the webhook if it's running.")
    except WhatsAppError as e:
        print("WhatsApp error:", e)
        if e.code in HINTS:
            print("Hint:", HINTS[e.code])
        sys.exit(1)


if __name__ == "__main__":
    main()

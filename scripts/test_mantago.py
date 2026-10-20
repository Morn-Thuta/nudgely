"""Quick MantaGO smoke test. Run from the repo root.

  python scripts/test_mantago.py members                 # who has messaged the bot (read only)
  python scripts/test_mantago.py tags                    # list manual tags (read only)
  python scripts/test_mantago.py send --to <clientId> --platform whatsapp --yes
  python scripts/test_mantago.py tag --to <clientId> --tag nudgely_test --yes

Needs MANTAGO_BOT_ID, MANTAGO_TOKEN, MANTAGO_SECRET in .env (copy .env.example).
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from nudgely.mantago import MantaGO, MantaGOError  # noqa: E402

DEFAULT_MSG = "Hi from Nudgely test! If you got this, the MantaGO API works. Reply STOP to opt out"

HINTS = {
    1002: "Wrong token/secret, or your plan does not include Open API (ask Eslitec).",
    1004: "Token expired and refresh failed. Get a new one in MantaGO: Settings > Advanced Settings > API.",
    5001: "Wrong botId. Copy it from the URL mantago.cc/chatbot/<botId>.",
    36000: "Broadcast failed. Is the bot published? On WhatsApp, did this person message the bot in the last 24h?",
    37011: "No member matches. Has this person messaged the bot yet?",
    110000: "A required field is missing in the request.",
    120000: "Old token used after it was regenerated. Copy the newest token + secret.",
}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["members", "tags", "send", "tag"])
    p.add_argument("--platform", default=None, help="line / facebook / instagram / whatsapp")
    p.add_argument("--to", help="clientId to send to or tag")
    p.add_argument("--message", default=DEFAULT_MSG)
    p.add_argument("--tag", default="nudgely_test")
    p.add_argument("--fb-tag", default=None)
    p.add_argument("--yes", action="store_true", help="confirm a real send or write")
    a = p.parse_args()

    try:
        m = MantaGO.from_env()
    except ValueError:
        sys.exit("Missing MANTAGO_BOT_ID / MANTAGO_TOKEN / MANTAGO_SECRET. Copy .env.example to .env and fill it in.")

    try:
        if a.cmd == "members":
            clients = m.list_clients(platform=a.platform)
            if not clients:
                print("No members yet. Message the bot from your phone first, then run again.")
            for c in clients:
                print(f"{c.get('platform', ''):10} {c.get('clientId', ''):40} "
                      f"{str(c.get('clientName', '')):25} last: {c.get('lastInteractAt', '')}")
            print(f"\n{len(clients)} member(s). Map teammates to demo customers in data/test_accounts.json, "
                  "e.g. {\"C001\": \"<clientId>\"} (git-ignored).")

        elif a.cmd == "tags":
            for t in m.list_tags():
                print(f"{t.get('id', ''):40} {t.get('name', '')}")

        elif a.cmd == "send":
            if not (a.to and a.platform):
                sys.exit("send needs --to <clientId> and --platform")
            if not a.yes:
                sys.exit(f"Dry run. Would send to {a.to} on {a.platform}:\n  {a.message}\nAdd --yes to really send.")
            print(m.send(a.platform, [a.to], a.message, name="Nudgely smoke test", fb_tag=a.fb_tag))
            print("Sent. Check the phone.")

        elif a.cmd == "tag":
            if not a.to:
                sys.exit("tag needs --to <clientId>")
            if not a.yes:
                sys.exit(f"Dry run. Would tag {a.to} with '{a.tag}'. Add --yes to really write.")
            tag_id = m.get_or_create_tag_id(a.tag)
            print(m.assign_tag(tag_id, a.to))
            print(f"Tagged {a.to} with '{a.tag}' ({tag_id}).")

    except MantaGOError as e:
        print(f"MantaGO error: {e}")
        if e.code in HINTS:
            print("Hint:", HINTS[e.code])
        sys.exit(1)


if __name__ == "__main__":
    main()

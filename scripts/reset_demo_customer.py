"""Put a demo customer (Aisha, C001) back to her seeded state between rehearsals.

Deletes only her messages and tags from on/after --since (seed data is Sep-Oct 2026), and clears the
flags a run sets: opted out (STOP), handover, replied, memory, and the phone link (key_hash).

    python scripts/reset_demo_customer.py            # dry run: shows what would go
    python scripts/reset_demo_customer.py --yes      # do it

Needs SUPABASE_URL and SUPABASE_SERVICE_KEY in .env. After a reset, the Aisha phone must message the
bot again before the next live send (that also re-opens WhatsApp's 24-hour window).
"""

import argparse
import os
import sys

import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--customer", default="C001")
    p.add_argument("--since", default="2026-11-01", help="delete messages/tags created on or after this date")
    p.add_argument("--yes", action="store_true")
    a = p.parse_args()
    if not a.customer.startswith("C"):
        sys.exit("Only seeded demo customers (C...) can be reset.")
    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        sys.exit("SUPABASE_URL / SUPABASE_SERVICE_KEY not set")
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    base = f"{url}/rest/v1"
    q = f"customer_id=eq.{a.customer}&created_at=gte.{a.since}"
    msgs = requests.get(f"{base}/messages?{q}&select=sender,text,created_at&order=created_at", headers=h).json()
    tags = requests.get(f"{base}/tags?{q}&select=type,value", headers=h).json()
    print(f"{a.customer}: {len(msgs)} messages and {len(tags)} tags since {a.since}")
    for m in msgs:
        print(f"  {m['created_at'][:16]} {m['sender']:8} {m['text'][:60]}")
    if not a.yes:
        print("Dry run. Add --yes to reset.")
        return
    for table in ("messages", "tags"):
        requests.delete(f"{base}/{table}?{q}", headers=h).raise_for_status()
    requests.patch(f"{base}/customers?id=eq.{a.customer}", headers=h, json={
        "channel": "demo", "opted_out": False, "handover": False, "replied": False, "memory": {},
        "msg_count": 0, "seen_ids": [], "key_hash": None}).raise_for_status()
    print("Reset. The Aisha phone must message the bot again before the next live send.")


if __name__ == "__main__":
    main()

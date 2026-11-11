"""Load the 30 Kampung Fresh demo customers into Supabase (after supabase/migrations/001_init.sql).

  python scripts/seed_supabase.py          # dry run: shows what would be written
  python scripts/seed_supabase.py --yes    # write

Needs SUPABASE_URL and SUPABASE_SERVICE_KEY in .env. Safe to run again: customers and tags are
upserted, and the demo customers' chat history is replaced, not duplicated.
"""

import argparse
import json
import os
import sys

import pandas as pd
import requests
from dotenv import load_dotenv

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(ROOT, ".env"))
DATA = os.path.join(ROOT, "data")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--yes", action="store_true")
    a = p.parse_args()

    customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
    tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8"))
    chats = json.load(open(os.path.join(DATA, "chats.json"), encoding="utf-8"))

    cust_rows = [{"id": r.customer_id, "channel": "demo", "name": r["name"], "label": r.label,
                  "uplift": round(float(r.uplift), 4), "p_no_msg": round(float(r.p_no_msg), 4)}
                 for _, r in customers.iterrows()]
    ids = {r["id"] for r in cust_rows}
    tag_rows = [{"customer_id": cid, "type": t["type"], "value": str(t["value"]), "evidence": t["evidence"]}
                for cid, t_all in tags.items() if cid in ids
                for t in t_all.get("tags", []) if t.get("type") and t.get("value") and t.get("evidence")]
    tag_rows = list({(t["customer_id"], t["type"], t["value"]): t for t in tag_rows}.values())
    msg_rows = [{"customer_id": cid, "sender": m["from"], "text": m["text"],
                 "created_at": f"{m['date']}T12:00:00+08:00" if m.get("date") else None}
                for cid, chat in chats.items() if cid in ids for m in chat]
    msg_rows = [{k: v for k, v in m.items() if v is not None} for m in msg_rows]

    print(f"{len(cust_rows)} customers, {len(tag_rows)} tags, {len(msg_rows)} chat messages")
    if not a.yes:
        sys.exit("Dry run. Add --yes to write to Supabase.")

    url, key = os.getenv("SUPABASE_URL", "").rstrip("/"), os.getenv("SUPABASE_SERVICE_KEY", "")
    if not (url and key):
        sys.exit("Set SUPABASE_URL and SUPABASE_SERVICE_KEY in .env first.")
    h = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}

    def call(method, path, rows=None, prefer="return=minimal"):
        r = requests.request(method, f"{url}/rest/v1/{path}", json=rows, timeout=30, headers={**h, "Prefer": prefer})
        if r.status_code >= 300:
            sys.exit(f"{method} {path}: HTTP {r.status_code} {r.text[:300]}")

    call("POST", "customers", cust_rows, "resolution=merge-duplicates,return=minimal")
    in_list = ",".join(sorted(ids))
    call("DELETE", f"messages?customer_id=in.({in_list})")
    call("POST", "messages", msg_rows)
    call("POST", "tags?on_conflict=customer_id,type,value", tag_rows, "resolution=merge-duplicates,return=minimal")
    print("Seeded.")


if __name__ == "__main__":
    main()

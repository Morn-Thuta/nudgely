"""Fill an approved WhatsApp template for every customer who has tags.

Run from repo root:
  python scripts/fill_templates.py                          # everyone with tags
  python scripts/fill_templates.py --only C001,C004
  python scripts/fill_templates.py --approved restock,event # only templates Meta has cleared
  python scripts/fill_templates.py --out data/template_messages.json

This is the outbound path once WhatsApp is involved. `write_messages.py` writes
free text, which WhatsApp only allows inside a 24-hour reply window; this fills a
fixed approved sentence, which is what a business may send to start one.

A customer whose blanks cannot be filled safely is skipped and listed at the end.
That is the intended outcome, not a failure: no message is better than one that
promises something the shop never said.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from nudgely import templates  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))
DATA = os.path.join(ROOT, "data")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--only", default="")
    p.add_argument("--approved", default="", help="template names Meta has approved, comma separated")
    p.add_argument("--out", default=os.path.join(DATA, "template_messages.json"))
    p.add_argument("--force", action="store_true", help="redo customers already in the output file")
    a = p.parse_args()

    customers = pd.read_csv(os.path.join(DATA, "customers.csv")).set_index("customer_id")
    chats = json.load(open(os.path.join(DATA, "chats.json"), encoding="utf-8"))
    tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8"))
    consent_path = os.path.join(DATA, "consent.json")
    consent = json.load(open(consent_path, encoding="utf-8")) if os.path.exists(consent_path) else {}

    out = json.load(open(a.out, encoding="utf-8")) if os.path.exists(a.out) else {}
    only = set(filter(None, a.only.split(",")))
    approved = [t.strip() for t in a.approved.split(",") if t.strip()] or None
    if approved:
        unknown = [t for t in approved if t not in templates.TEMPLATES]
        if unknown:
            sys.exit(f"Unknown template name(s): {unknown}. Known: {sorted(templates.TEMPLATES)}")

    skipped = []
    for cid, extraction in tags.items():
        if (only and cid not in only) or (cid in out and not a.force):
            continue
        if cid not in customers.index:
            skipped.append((cid, "not in customers.csv"))
            continue
        if consent.get(cid) is False:
            skipped.append((cid, "opted out"))
            continue

        row = customers.loc[cid]
        customer = {"customer_id": cid, "name": row["name"], "label": row["label"],
                    "chat": chats.get(cid, [])}
        result = templates.fill(customer, extraction, available=approved)

        if result["ok"]:
            out[cid] = result
            print(f"{cid} [{result['template']}] {result['message']}")
        else:
            skipped.append((cid, result["problems"][0]))
            print(f"{cid} skipped: {result['problems'][0]}")

        with open(a.out, "w", encoding="utf-8") as f:  # save as we go
            json.dump(out, f, indent=2, ensure_ascii=False)

    print(f"\n{len(out)} filled messages in {a.out}")
    if skipped:
        print(f"{len(skipped)} skipped:")
        for cid, why in skipped:
            print(f"  {cid}: {why}")


if __name__ == "__main__":
    main()

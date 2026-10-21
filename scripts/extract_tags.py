"""F3 Chat Memory: run prompt 1 on every customer's chats, cache to data/tags.json.

Run from repo root: python scripts/extract_tags.py [--only C001,C002] [--force]
Needs LLM_PROVIDER + LLM_API_KEY in .env. Names and phone numbers are stripped before text goes to the LLM.
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if hasattr(sys.stdout, "reconfigure"):  # Windows consoles are cp1252 and choke on emoji
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from nudgely import llm  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "tags.json")

p = argparse.ArgumentParser()
p.add_argument("--only", default="")
p.add_argument("--force", action="store_true", help="re-run customers already in tags.json")
a = p.parse_args()

customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
names = dict(zip(customers.customer_id, customers.name))
chats = json.load(open(os.path.join(DATA, "chats.json"), encoding="utf-8"))
out = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
only = set(filter(None, a.only.split(",")))

for cid, chat in chats.items():
    if (only and cid not in only) or (cid in out and not a.force):
        continue
    try:
        out[cid] = llm.extract_tags(cid, chat, names=[names.get(cid, "")])
        tags = ", ".join(f"{t['type']}={t['value']}" for t in out[cid]["tags"]) or "(no tags)"
        print(f"{cid} ok: {tags}")
    except Exception as e:
        print(f"{cid} FAILED: {e}")
    with open(OUT, "w", encoding="utf-8") as f:  # save after each so a crash loses nothing
        json.dump(out, f, indent=2, ensure_ascii=False)

print(f"\n{len(out)} customers in {OUT}. Hand-check every tag's evidence against the chat.")

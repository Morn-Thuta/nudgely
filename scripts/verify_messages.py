"""Check every drafted message against the chat it came from.

Run from repo root: python scripts/verify_messages.py [--only C001,C002] [--file data/messages.json]

Uses no LLM and no API key, so it costs nothing and can run on every commit.
Exit code 1 if anything is flagged, so CI can fail on it.
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

from nudgely import llm, verify  # noqa: E402

DATA = os.path.join(ROOT, "data")

p = argparse.ArgumentParser()
p.add_argument("--only", default="")
p.add_argument("--file", default=os.path.join(DATA, "messages.json"))
a = p.parse_args()

customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
labels = dict(zip(customers.customer_id, customers.label))
messages = json.load(open(a.file, encoding="utf-8"))
tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8"))
chats = json.load(open(os.path.join(DATA, "chats.json"), encoding="utf-8"))
only = set(filter(None, a.only.split(",")))

flagged = 0
for cid in sorted(messages):
    if only and cid not in only:
        continue
    problems = llm.check_message(messages[cid], labels.get(cid, ""))
    problems += verify.verify_message(messages[cid], chats.get(cid, []), tags.get(cid, {}))
    if problems:
        flagged += 1
        print(f"\n{cid} ({labels.get(cid, '?')})")
        print(f"  {messages[cid]['message']}")
        for problem in problems:
            print(f"  -> {problem}")

checked = len(only or messages)
print(f"\n{checked - flagged}/{checked} clean, {flagged} to look at.")
sys.exit(1 if flagged else 0)

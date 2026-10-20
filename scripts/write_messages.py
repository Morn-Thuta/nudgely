"""F4 Message writer: run prompt 2 for every customer, cache to data/messages.json.

Run from repo root: python scripts/write_messages.py [--only C001,C002] [--force]
Retries up to 2 times when a message breaks the hard rules (length, opt-out, discount cap).
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pandas as pd  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

from nudgely import llm  # noqa: E402

load_dotenv(os.path.join(ROOT, ".env"))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "messages.json")

p = argparse.ArgumentParser()
p.add_argument("--only", default="")
p.add_argument("--force", action="store_true")
a = p.parse_args()

customers = pd.read_csv(os.path.join(DATA, "customers.csv"))
tags = json.load(open(os.path.join(DATA, "tags.json"), encoding="utf-8"))
out = json.load(open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
only = set(filter(None, a.only.split(",")))

for _, c in customers.iterrows():
    cid = c.customer_id
    if (only and cid not in only) or (cid in out and not a.force) or cid not in tags:
        continue
    for attempt in range(3):
        try:
            msg = llm.write_message(c.to_dict(), tags[cid])
        except Exception as e:
            print(f"{cid} FAILED: {e}")
            break
        problems = llm.check_message(msg, c.label)
        if not problems:
            out[cid] = msg
            print(f"{cid} ok ({len(msg['message'])} chars): {msg['message']}")
            break
        print(f"{cid} retry {attempt + 1}: {'; '.join(problems)}")
    else:
        out[cid] = msg  # keep the last try; the app flags it red
        print(f"{cid} KEPT WITH PROBLEMS - fix by hand")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2, ensure_ascii=False)

print(f"\n{len(out)} messages in {OUT}. Hand-check all of them before the demo.")

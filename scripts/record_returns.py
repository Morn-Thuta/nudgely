"""Mark who came back after a campaign, so the Results page can show real outcomes.

Run from repo root:
  python scripts/record_returns.py --returned C003,C007        # these customers came back
  python scripts/record_returns.py --from-visits visits.csv    # csv with customer_id,visit_date
  python scripts/record_returns.py --window 30 --close         # rows past the window with no
                                                               # visit are marked 0

A row stays blank until you decide it. Blank means "not observed yet", 0 means
"observed, did not come back" - they are not the same thing, and the second is
what the model learns from.
"""

import argparse
import os
import sys
from datetime import datetime, timedelta

import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

LOG = os.path.join(ROOT, "data", "campaign_log.csv")

p = argparse.ArgumentParser()
p.add_argument("--returned", default="", help="comma-separated customer ids that came back")
p.add_argument("--from-visits", default="", help="csv with customer_id and visit_date columns")
p.add_argument("--window", type=int, default=30, help="days a customer has to come back")
p.add_argument("--close", action="store_true", help="mark 0 for rows past the window with no visit")
a = p.parse_args()

if not os.path.exists(LOG):
    sys.exit(f"No campaign log yet at {LOG}. It is written the first time a campaign sends for real.")

log = pd.read_csv(LOG)
log["returned"] = log["returned"].astype("object")
log["returned_at"] = log["returned_at"].astype("object")
now = datetime.now()


def mark(mask, when):
    """Set returned=1 on rows that are still blank."""
    blank = log["returned"].isna() | (log["returned"].astype(str).str.strip() == "")
    rows = mask & blank
    log.loc[rows, "returned"] = 1
    log.loc[rows, "returned_at"] = when
    return int(rows.sum())


marked = 0
if a.returned:
    ids = [c.strip() for c in a.returned.split(",") if c.strip()]
    marked += mark(log.customer_id.isin(ids), now.date().isoformat())

if a.from_visits:
    visits = pd.read_csv(a.from_visits, parse_dates=["visit_date"])
    for _, v in visits.iterrows():
        sent = pd.to_datetime(log.sent_at, errors="coerce")
        within = (log.customer_id == v.customer_id) & (sent <= v.visit_date) & \
                 (v.visit_date <= sent + timedelta(days=a.window))
        marked += mark(within, v.visit_date.date().isoformat())

closed = 0
if a.close:
    sent = pd.to_datetime(log.sent_at, errors="coerce")
    blank = log["returned"].isna() | (log["returned"].astype(str).str.strip() == "")
    expired = blank & (sent < now - timedelta(days=a.window))
    log.loc[expired, "returned"] = 0
    closed = int(expired.sum())

log.to_csv(LOG, index=False)
done = log["returned"].astype(str).str.strip().isin(["0", "1", "0.0", "1.0"]).sum()
print(f"marked {marked} as returned, closed {closed} as not returned.")
print(f"{done}/{len(log)} rows now have an outcome; {len(log) - done} still waiting.")

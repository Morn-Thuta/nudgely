"""Write data/examples/campaign_log.csv: three finished campaigns with SIMULATED outcomes.

The Results page shows it, labelled as an example, until the shop has measured
outcomes of its own. Nothing here is a real result. Each outcome is one draw from
the model's own estimate for that customer: p_msg if they were messaged, p_no_msg
if they were kept back. So it shows what the model expects a quarter to look
like, including how noisy 30 customers are.

Run from repo root:
  python scripts/make_example_campaign.py
"""

import json
import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(DATA, "examples", "campaign_log.csv")
SEED = 42            # same seed the app uses; not tuned for a flattering result
REACH, KEEP_BACK = 12, 4
MONTHS = ["2026-08-03", "2026-09-01", "2026-10-01"]


def source(name):
    real = os.path.join(DATA, name)
    return real if os.path.exists(real) else os.path.join(DATA, "examples", name)


customers = pd.read_csv(source("customers.csv"))
consent = {}
if os.path.exists(source("consent.json")):
    with open(source("consent.json"), encoding="utf-8") as f:
        consent = json.load(f)
opted_out = {cid for cid, v in consent.items() if v.get("opted_in") is False}

chosen = (customers[~customers.customer_id.isin(opted_out)]
          .sort_values(["uplift", "customer_id"], ascending=[False, True]).head(REACH))
rng = np.random.default_rng(SEED)

rows = []
for day in MONTHS:
    sent = pd.Timestamp(day + "T10:00:00")
    kept = set(rng.choice(chosen.customer_id, size=KEEP_BACK, replace=False))
    for _, c in chosen.iterrows():
        messaged = c.customer_id not in kept
        came_back = rng.random() < (c.p_msg if messaged else c.p_no_msg)
        rows.append({
            "campaign_id": "example_" + sent.strftime("%Y%m"),
            "sent_at": sent.isoformat(),
            "customer_id": c.customer_id,
            "name": c["name"],
            "group": "messaged" if messaged else "holdout",
            "platform": "whatsapp" if messaged else "",
            "status": "example" if messaged else "not messaged",
            "returned": int(came_back),
            "returned_at": (sent + pd.Timedelta(days=int(rng.integers(2, 29)))).date().isoformat() if came_back else "",
        })

log = pd.DataFrame(rows)
log.to_csv(OUT, index=False)
for group, part in log.groupby("group"):
    print(f"{group:9s} {int(part.returned.sum())} of {len(part)} came back ({part.returned.mean():.0%})")
print("written", OUT)

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

# ---- a messy sales file that reproduces those outcomes -----------------------
# For the "who came back" upload on Results. Uploading it gives exactly the
# outcomes above, plus a few broken rows so the fix-it report has something in it.
# Separate random stream, so changing this never changes the outcomes above.
SALES = os.path.join(DATA, "examples", "returns_sample.csv")
r2 = np.random.default_rng(7)
in_campaign = set(chosen.customer_id)
others = [c for c in customers.customer_id if c not in in_campaign]
buys = []                                   # (customer_id, date)
for cid in customers.customer_id:           # history before the first send
    for _ in range(int(r2.integers(1, 4))):
        buys.append((cid, pd.Timestamp("2026-06-01") + pd.Timedelta(days=int(r2.integers(0, 61)))))
for _, row in log[log.returned == 1].iterrows():
    buys.append((row.customer_id, pd.Timestamp(row.returned_at)))
for cid in others:                          # the rest of the shop keeps shopping
    for _ in range(int(r2.integers(2, 6))):
        buys.append((cid, pd.Timestamp("2026-08-01") + pd.Timedelta(days=int(r2.integers(0, 96)))))
buys.append((others[0], pd.Timestamp("2026-11-05")))   # file runs past the last window

styles = ["{:%Y-%m-%d}", "{:%d/%m/%Y}", "{:%d %b %Y}", "{d.day}-{d.month}-{d.year}"]


def messy_date(d):
    style = styles[int(r2.integers(0, len(styles)))]
    return style.format(d, d=d) if "{d." in style else style.format(d)


def messy_id(cid):
    return [cid, " " + cid.lower(), cid.lower() + " ", cid][int(r2.integers(0, 4))]


sales = pd.DataFrame(sorted(buys, key=lambda b: b[1]), columns=["cid", "date"])
sales = pd.DataFrame({
    "Receipt no": [f"KF{10421 + i}" for i in range(len(sales))],
    "Customer": sales.cid.map(messy_id),
    "Date of purchase": sales.date.map(messy_date),
    "Amount (SGD)": [f"${a:.2f}" for a in r2.uniform(6, 120, len(sales))],
})
returner = log[log.returned == 1].iloc[0]
broken = pd.DataFrame({
    "Receipt no": ["KF19901", "KF19902", "KF19903", "KF19904"],
    "Customer": ["", others[1], others[2], returner.customer_id.replace("0", "O", 1)],  # last: letter O typo
    "Date of purchase": ["2026-09-14", "32/13/2026", "next Tuesday", f"{pd.Timestamp(returner.returned_at):%d/%m/%Y}"],
    "Amount (SGD)": ["$18.40", "$22.10", "$9.90", "$31.00"],
})
pd.concat([sales, broken]).sample(frac=1, random_state=3).to_csv(SALES, index=False)
print("written", SALES, f"({len(sales) + len(broken)} rows, {len(broken)} broken on purpose)")

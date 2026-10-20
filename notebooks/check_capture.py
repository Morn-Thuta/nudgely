"""How stable is the "top 30% captures X% of extra visits" number? Bootstrap the test set.

Run from repo root: python notebooks/check_capture.py
"""

import json

import numpy as np
import pandas as pd

df = pd.read_csv("data/lenta_scored_test.csv")
rng = np.random.default_rng(0)
cut = df.uplift.quantile(0.7)


def share(d):
    top = d[d.uplift >= cut]
    lift = lambda g: g.loc[g.treatment == 1, "visit"].mean() - g.loc[g.treatment == 0, "visit"].mean()
    return lift(top) * len(top) / (lift(d) * len(d))


point = share(df)
boots = [share(df.iloc[rng.integers(0, len(df), len(df))]) for _ in range(300)]
lo, hi = np.percentile(boots, [5, 95])
print(f"top-30% capture share: {point:.1%}  (90% interval {lo:.1%} to {hi:.1%})")

with open("data/uplift_summary.json") as f:
    s = json.load(f)
s.setdefault("top30_capture_share_deciles", s["top30_capture_share"])
s["top30_capture_share"] = float(point)  # pooled estimate, the more conservative one
s["top30_capture_ci90"] = [float(lo), float(hi)]
with open("data/uplift_summary.json", "w") as f:
    json.dump(s, f, indent=2)

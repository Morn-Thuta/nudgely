"""F1 + F2: train the two-model uplift on Lenta, score the test set, pick 30 demo customers.

Run from repo root (after fetch_lenta.py):  python notebooks/train_uplift.py
Outputs (small, committed):
  data/lenta_scored_test.csv   treatment, visit, p_no_msg, p_msg, uplift, decile
  data/uplift_summary.json     visit rates, decile table, top-30% capture share, label thresholds
  data/demo_pool.csv           30 real test rows (10 per label) for the demo customers
"""

import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklift.metrics import qini_auc_score, uplift_at_k
from sklift.models import TwoModels

SEED = 42
SAMPLE = 0.5
# Fairness: behaviour features only - no gender, age or family status
DROP = ["gender", "age", "children"]

t0 = time.time()
df = pd.read_parquet(os.path.join("data", "raw", "lenta.parquet"))
full_rates = df.groupby("treatment")["visit"].mean()

df = df.sample(frac=SAMPLE, random_state=SEED)
y, w = df.pop("visit").to_numpy(), df.pop("treatment").to_numpy()
X = df.drop(columns=[c for c in DROP if c in df.columns]).astype("float32")
print(f"sample {X.shape}, features dropped: {DROP}")

strat = w * 2 + y
X_tr, X_te, y_tr, y_te, w_tr, w_te = train_test_split(X, y, w, test_size=0.3, stratify=strat, random_state=SEED)


def hgb():
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                          early_stopping=True, validation_fraction=0.1, random_state=SEED)


model = TwoModels(estimator_trmnt=hgb(), estimator_ctrl=hgb(), method="vanilla")
model.fit(X_tr, y_tr, w_tr)
uplift = model.predict(X_te)
p_msg, p_no_msg = model.trmnt_preds_, model.ctrl_preds_
print(f"trained in {time.time() - t0:.0f}s")

# ---- evaluation on the test set ------------------------------------------
scored = pd.DataFrame({"lenta_row": X_te.index, "treatment": w_te, "visit": y_te,
                       "p_no_msg": p_no_msg, "p_msg": p_msg, "uplift": uplift})
scored = scored.sort_values("uplift", ascending=False).reset_index(drop=True)
scored["decile"] = (np.arange(len(scored)) * 10 // len(scored)) + 1

deciles = []
for d, g in scored.groupby("decile"):
    rt = g.loc[g.treatment == 1, "visit"].mean()
    rc = g.loc[g.treatment == 0, "visit"].mean()
    deciles.append({"decile": int(d), "n": int(len(g)), "visit_rate_msg": float(rt), "visit_rate_no_msg": float(rc),
                    "observed_uplift": float(rt - rc), "mean_predicted_uplift": float(g.uplift.mean())})
dec = pd.DataFrame(deciles)
extra = dec.observed_uplift * dec.n
top30_share = float(extra.head(3).sum() / extra.sum())

# ---- labels (F2) ----------------------------------------------------------
up_cut = float(scored.uplift.quantile(0.7))
base_cut = float(scored.p_no_msg.quantile(0.7))
scored["label"] = np.where(scored.uplift >= up_cut, "Persuadable",
                           np.where(scored.p_no_msg >= base_cut, "Sure Thing", "Lost Cause"))

summary = {
    "dataset": "Lenta (687k grocery customers, SMS test)",
    "features_dropped": DROP,
    "train_sample": SAMPLE,
    "n_test": int(len(scored)),
    "visit_rate_no_msg": float(full_rates[0]),
    "visit_rate_msg": float(full_rates[1]),
    "uplift_at_30": float(uplift_at_k(y_te, uplift, w_te, strategy="overall", k=0.3)),
    "qini_auc": float(qini_auc_score(y_te, uplift, w_te)),
    "top30_capture_share": top30_share,
    "label_thresholds": {"uplift_top30": up_cut, "p_no_msg_top30": base_cut},
    "label_counts": scored.label.value_counts().to_dict(),
    "deciles": deciles,
}

os.makedirs("data", exist_ok=True)
scored[["treatment", "visit", "p_no_msg", "p_msg", "uplift", "decile", "label"]].round(5).to_csv(
    os.path.join("data", "lenta_scored_test.csv"), index=False)
with open(os.path.join("data", "uplift_summary.json"), "w") as f:
    json.dump(summary, f, indent=2)

# ---- 30 demo customers: 10 real test rows per label -----------------------
rng = np.random.default_rng(SEED)
picks = []
for label in ["Persuadable", "Sure Thing", "Lost Cause"]:
    pool = scored[scored.label == label]
    if label == "Persuadable":  # take clear cases so the demo reads well
        pool = pool[pool.uplift >= pool.uplift.quantile(0.5)]
    picks.append(pool.iloc[rng.choice(len(pool), 10, replace=False)])
demo = pd.concat(picks).sort_values("uplift", ascending=False).reset_index(drop=True)
demo.insert(0, "customer_id", [f"C{i:03d}" for i in range(1, len(demo) + 1)])
demo[["customer_id", "lenta_row", "label", "p_no_msg", "p_msg", "uplift"]].round(4).to_csv(
    os.path.join("data", "demo_pool.csv"), index=False)

print(json.dumps({k: v for k, v in summary.items() if k != "deciles"}, indent=2))
print(dec.round(4).to_string(index=False))
print(f"done in {time.time() - t0:.0f}s")

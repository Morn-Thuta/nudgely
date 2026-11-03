"""Train an uplift model a real shop can actually use.

train_uplift.py uses all 190 Lenta columns, which is fine for the Lenta test set
and useless anywhere else: no Singapore grocer records "share of purchases in
product group 42". This trains on the handful of features any shop can compute
from a purchase export of phone, date and amount, so the same model can score
real customers.

Run from repo root (after fetch_lenta.py):
  python notebooks/train_transferable.py

Writes:
  data/uplift_transferable.json   the comparison, honestly reported
  data/model_transferable.pkl     the model, for scoring a real shop
"""

import json
import os
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklift.metrics import qini_auc_score
from sklift.models import TwoModels

SEED = 42
SAMPLE = 0.5
RAW = os.path.join("data", "raw", "lenta.parquet")
DATA = "data"

# Every one of these is computable from a shop's own purchase history:
# when each customer first bought, how regular their visits are, how much their
# basket varies, and whether they have responded to a message before.
TRANSFERABLE = {
    "months_from_register": "days since first purchase",
    "k_var_days_between_visits_15d": "how irregular their visits are (15d)",
    "k_var_days_between_visits_1m": "how irregular their visits are (1m)",
    "k_var_days_between_visits_3m": "how irregular their visits are (3m)",
    "stdev_days_between_visits_15d": "spread of gaps between visits",
    "perdelta_days_between_visits_15_30d": "are their visits speeding up or slowing down",
    "k_var_cheque_15d": "how much their basket value varies (15d)",
    "k_var_cheque_3m": "how much their basket value varies (3m)",
    "response_sms": "responded to an SMS before",
    "response_viber": "responded to a Viber message before",
}


def hgb(seed=SEED):
    return HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
                                          early_stopping=True, validation_fraction=0.1, random_state=seed)


def capture_share(uplift, y, w, k=0.3):
    """Share of all extra visits that land in the top k by predicted uplift."""
    order = np.argsort(-uplift)
    top = order[: int(len(order) * k)]

    def lift(idx):
        t, c = w[idx] == 1, w[idx] == 0
        if t.sum() == 0 or c.sum() == 0:
            return 0.0
        return y[idx][t].mean() - y[idx][c].mean()

    total_extra = lift(np.arange(len(y))) * len(y)
    top_extra = lift(top) * len(top)
    return float(top_extra / total_extra) if total_extra else 0.0


def train_once(X, y, w, seed):
    strat = w * 2 + y
    X_tr, X_te, y_tr, y_te, w_tr, w_te = train_test_split(
        X, y, w, test_size=0.3, stratify=strat, random_state=seed)
    model = TwoModels(estimator_trmnt=hgb(seed), estimator_ctrl=hgb(seed), method="vanilla")
    model.fit(X_tr, y_tr, w_tr)
    pred = model.predict(X_te)
    return model, capture_share(pred, y_te, w_te), float(qini_auc_score(y_te, pred, w_te))


def evaluate(X, y, w, label, seeds):
    """One split is not an answer: capture share moved 30 points between splits when
    this was first run, so every number here is a mean over several."""
    captures, qinis, last = [], [], None
    t0 = time.time()
    for seed in seeds:
        last, capture, qini = train_once(X, y, w, seed)
        captures.append(capture)
        qinis.append(qini)
    result = {
        "features": int(X.shape[1]),
        "seeds": list(seeds),
        "capture_mean": float(np.mean(captures)),
        "capture_sd": float(np.std(captures)),
        "capture_min": float(np.min(captures)),
        "capture_max": float(np.max(captures)),
        "qini_mean": float(np.mean(qinis)),
        "seconds": round(time.time() - t0, 1),
    }
    print(f"{label:16} {result['features']:>4} features  "
          f"top30 captures {result['capture_mean']:.1%} +/- {result['capture_sd']:.1%} "
          f"(range {result['capture_min']:.0%}-{result['capture_max']:.0%})  "
          f"qini {result['qini_mean']:.4f}  ({result['seconds']}s)")
    return last, result


def main():
    seeds = (1, 2, 3, 4, 5, 6, 7)
    df = pd.read_parquet(RAW).sample(frac=SAMPLE, random_state=SEED)
    y, w = df.pop("visit").to_numpy(), df.pop("treatment").to_numpy()

    missing = [c for c in TRANSFERABLE if c not in df.columns]
    if missing:
        raise SystemExit(f"Lenta is missing expected columns: {missing}")

    print(f"{len(df):,} customers, treatment share {w.mean():.1%}, {len(seeds)} seeds each\n")

    full = df.drop(columns=[c for c in ("gender", "age", "children") if c in df.columns]).astype("float32")
    small = df[list(TRANSFERABLE)].astype("float32")

    _, full_result = evaluate(full, y, w, "all Lenta", seeds)
    model, small_result = evaluate(small, y, w, "transferable", seeds)

    gain = small_result["capture_mean"] - full_result["capture_mean"]
    beats_random = small_result["capture_mean"] - small_result["capture_sd"] > 0.30
    verdict = ("usable on a real shop: better than random even one standard deviation down"
               if beats_random else
               "not demonstrably better than random once the spread is taken into account")
    print("\nrandom targeting captures 30.0% by definition")
    print(f"dropping to {small_result['features']} features: {gain:+.1%} vs all of Lenta -> {verdict}")

    joblib.dump({"model": model, "features": list(TRANSFERABLE)},
                os.path.join(DATA, "model_transferable.pkl"))
    out = {
        "dataset": "Lenta (687k grocery customers, SMS test)",
        "random_baseline": 0.30,
        "all_features": full_result,
        "transferable": small_result,
        "transferable_features": TRANSFERABLE,
        "capture_gain_vs_all_features": gain,
        "verdict": verdict,
        "note": ("Means over several random splits, because a single split moved the capture "
                 "share by 30 points. Trained on Lenta but using only features a shop can "
                 "compute from its own purchase history, so the model can score real "
                 "customers. Retrain on the shop's own campaign outcomes once there are enough."),
    }
    with open(os.path.join(DATA, "uplift_transferable.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print("wrote data/uplift_transferable.json and data/model_transferable.pkl")


if __name__ == "__main__":
    main()

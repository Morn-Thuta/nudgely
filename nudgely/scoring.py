"""Turn a shop's sales export into uplift scores.

The model in data/model_transferable.pkl wants ten numbers per customer. A shop
has a list of purchases: phone, date, amount. This is the bridge.

Every feature is computed the way Lenta's equivalent was, because the model
learned on that scale: months since first purchase, how irregular the gaps
between visits are, how much the basket value varies, and whether the customer
has responded to a message before.

Where a window holds fewer than two visits the variation is undefined, and that
is left as NaN rather than filled with zero. Lenta has the same gaps - 77k
customers have no 15-day variation - so the model learned on data shaped this
way, and a zero would be a lie about a customer who simply did not visit.
"""

import os

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(ROOT, "data", "model_transferable.pkl")

WINDOWS = {"15d": 15, "1m": 30, "3m": 91}
DAYS_PER_MONTH = 30.4


def _cv(values):
    """Coefficient of variation: how much something varies, relative to its size.

    Undefined for fewer than two values, or when the mean is zero.
    """
    values = np.asarray(values, dtype="float64")
    if len(values) < 2:
        return np.nan
    mean = values.mean()
    return float(values.std(ddof=0) / mean) if mean else np.nan


def _gaps(dates):
    """Days between consecutive visits."""
    if len(dates) < 2:
        return np.array([])
    ordered = np.sort(np.asarray(dates, dtype="datetime64[D]"))
    return np.diff(ordered).astype("float64")


def features_for_customer(purchases, today):
    """The ten model features for one customer's purchase history."""
    purchases = purchases.sort_values("date")
    dates, amounts = purchases["date"].to_numpy(), purchases["amount"].to_numpy()
    first = pd.Timestamp(dates.min())

    row = {"months_from_register": (today - first).days / DAYS_PER_MONTH}

    window_gaps = {}
    for name, days in WINDOWS.items():
        cutoff = today - pd.Timedelta(days=days)
        inside = purchases[purchases["date"] >= cutoff]
        gaps = _gaps(inside["date"].to_numpy())
        window_gaps[name] = gaps
        row[f"k_var_days_between_visits_{name}"] = _cv(gaps)
        if name in ("15d", "3m"):
            row[f"k_var_cheque_{name}"] = _cv(inside["amount"].to_numpy())

    row["stdev_days_between_visits_15d"] = (
        float(window_gaps["15d"].std(ddof=0)) if len(window_gaps["15d"]) >= 2 else np.nan)

    # Are their visits speeding up or slowing down: the recent gap against the wider one.
    recent, wider = window_gaps["15d"], window_gaps["1m"]
    if len(recent) >= 1 and len(wider) >= 1 and wider.mean():
        row["perdelta_days_between_visits_15_30d"] = float(
            (recent.mean() - wider.mean()) / wider.mean())
    else:
        row["perdelta_days_between_visits_15_30d"] = 0.0  # Lenta has no nulls here either

    return row


def features_from_sales(sales, today=None, responses=None):
    """One row of model features per customer.

    `sales` needs phone, date and amount columns, one row per purchase.
    `responses` optionally maps phone -> {"response_sms": 0..1, "response_viber": 0..1}
    from past campaigns. A shop with no campaign history has neither, which is a
    genuine unknown rather than a zero, so it stays NaN.
    """
    sales = sales.copy()
    sales["date"] = pd.to_datetime(sales["date"], errors="coerce")
    sales["amount"] = pd.to_numeric(sales["amount"], errors="coerce")
    sales = sales.dropna(subset=["phone", "date", "amount"])
    if sales.empty:
        raise ValueError("No usable rows: need phone, date and amount.")

    today = pd.Timestamp(today) if today is not None else pd.Timestamp(sales["date"].max())
    responses = responses or {}

    rows = {}
    for phone, purchases in sales.groupby("phone"):
        row = features_for_customer(purchases, today)
        seen = responses.get(phone, {})
        row["response_sms"] = seen.get("response_sms", np.nan)
        row["response_viber"] = seen.get("response_viber", np.nan)
        rows[phone] = row

    frame = pd.DataFrame.from_dict(rows, orient="index")
    frame.index.name = "phone"
    return frame


def load_model(path=MODEL_PATH):
    import joblib

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{path} not found. Build it with: python notebooks/train_transferable.py")
    bundle = joblib.load(path)
    return bundle["model"], bundle["features"]


def score_sales(sales, today=None, responses=None, model_path=MODEL_PATH, persuadable_top=0.3):
    """Rank a shop's customers by how much a message would change their behaviour.

    Returns phone, the ten features, p_no_msg, p_msg, uplift and a label.
    `persuadable_top` is the share labelled Persuadable, matching how the demo
    data was labelled.
    """
    model, feature_names = load_model(model_path)
    features = features_from_sales(sales, today=today, responses=responses)
    X = features.reindex(columns=feature_names).astype("float32")

    uplift = model.predict(X)
    p_no_msg = model.estimator_ctrl.predict_proba(X)[:, 1]
    p_msg = model.estimator_trmnt.predict_proba(X)[:, 1]

    out = features.copy()
    out["p_no_msg"] = p_no_msg
    out["p_msg"] = p_msg
    out["uplift"] = uplift
    out = out.sort_values("uplift", ascending=False)

    cut = out["uplift"].quantile(1 - persuadable_top)
    likely_anyway = out["p_no_msg"].quantile(0.7)
    out["label"] = np.where(out["uplift"] >= cut, "Persuadable",
                            np.where(out["p_no_msg"] >= likely_anyway, "Sure Thing", "Lost Cause"))
    return out.reset_index()

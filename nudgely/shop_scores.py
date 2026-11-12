"""Score a shop from its own sales file: the upload behind the website's "Your sales" page.

A shop sends the export from its till: one row per purchase with who bought (phone or
member id), when, and how much. This module reads it however messy it is, turns each
customer's purchases into the ten numbers Model 2 was trained on (nudgely/scoring.py),
and returns every customer ranked by how much a message would change their chance of
coming back.

Nothing is stored. The file is read, scored and dropped; the response goes back to the
browser that sent it.
"""

import re

import numpy as np
import pandas as pd

from nudgely import returns, scoring

MAX_BYTES = 2_000_000     # about 50k purchase rows as CSV; keeps the free server responsive
MAX_ROWS = 100_000
MIN_CUSTOMERS = 5         # labels are relative to the shop, so a handful is not a ranking
AMOUNT_HINTS = ("amount", "total", "spend", "spent", "price", "value", "sgd", "paid", "sales", "$")


class ScoreError(ValueError):
    """A problem with the upload that the shop owner can fix. The message says how."""


def parse_amount(value):
    """'$12.50', 'S$1,204.00', 'SGD 9' -> float. NaN when there is no number."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return np.nan
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value)
    text = re.sub(r"[^\d.\-]", "", str(value).replace(",", ""))
    try:
        return float(text) if text not in ("", ".", "-") else np.nan
    except ValueError:
        return np.nan


def read_sales(data, filename):
    """The upload as clean purchases (customer, date, amount), plus what was dropped and why."""
    if len(data) > MAX_BYTES:
        raise ScoreError(f"The file is {len(data) / 1e6:.1f} MB. Keep it under {MAX_BYTES / 1e6:.0f} MB "
                         "by exporting a shorter period (3 to 6 months is plenty).")
    try:
        sheets = returns.read_file(data, filename or "sales.csv")
    except Exception as e:  # noqa: BLE001 - any parse failure is the owner's to fix, said plainly
        raise ScoreError(f"Couldn't read the file: {e}. Save it as CSV or Excel (.xlsx).")
    frame = next(iter(sheets.values())) if sheets else pd.DataFrame()
    if frame.empty:
        raise ScoreError("The file has no rows.")
    if len(frame) > MAX_ROWS:
        raise ScoreError(f"The file has {len(frame):,} rows. Keep it under {MAX_ROWS:,}.")

    cols = list(frame.columns)
    who = returns.guess_column(cols, ("phone", "mobile", "contact", "hp", "customer", "member", "client"))
    when = returns.guess_column(cols, returns.WHEN_HINTS)
    much = returns.guess_column([c for c in cols if c not in (who, when)], AMOUNT_HINTS)
    missing = [name for name, col in (("who bought (phone or member id)", who), ("date", when),
                                      ("amount", much)) if col is None]
    if missing:
        raise ScoreError("Couldn't find a column for " + " or ".join(missing) + ". The file's columns are: "
                         + ", ".join(str(c) for c in cols) + ". Rename them to phone, date and amount.")

    sales = pd.DataFrame({
        "phone": frame[who].map(returns.clean_id),
        "date": frame[when].map(returns.parse_date),
        "amount": frame[much].map(parse_amount),
    })
    reasons = pd.Series("", index=sales.index)
    reasons[sales["amount"].isna()] = "amount not a number"
    reasons[sales["date"].isna()] = "date not readable"
    reasons[sales["phone"] == ""] = "no phone or member id"
    dropped = reasons[reasons != ""].value_counts().to_dict()
    sales = sales[reasons == ""].copy()
    sales["date"] = pd.to_datetime(sales["date"]).dt.normalize()
    return sales, {"phone": str(who), "date": str(when), "amount": str(much)}, dropped, len(frame)


def score_upload(data, filename, model_path=scoring.MODEL_PATH):
    """Read, score and summarise. Returns a JSON-ready dict for the website."""
    sales, columns, dropped, rows_read = read_sales(data, filename)
    customers = sales["phone"].nunique()
    if customers < MIN_CUSTOMERS:
        raise ScoreError(f"Only {customers} customer(s) could be read. Scoring ranks customers against "
                         f"each other, so it needs at least {MIN_CUSTOMERS}.")

    as_of = sales["date"].max()
    scored = scoring.score_sales(sales, today=as_of, model_path=model_path)

    stats = sales.groupby("phone").agg(purchases=("amount", "size"), avg_spend=("amount", "mean"),
                                       first=("date", "min"), last=("date", "max"))
    rows = []
    for r in scored.itertuples(index=False):
        s = stats.loc[r.phone]
        rows.append({
            "id": str(r.phone),
            "label": r.label,
            "p_no_msg": round(float(r.p_no_msg), 4),
            "p_msg": round(float(r.p_msg), 4),
            "uplift": round(float(r.uplift), 4),
            "purchases": int(s.purchases),
            "avg_spend": round(float(s.avg_spend), 2),
            "months_as_customer": round((as_of - s["first"]).days / scoring.DAYS_PER_MONTH, 1),
            "days_since_last": int((as_of - s["last"]).days),
        })

    labels = scored["label"].value_counts().to_dict()
    persuadable = scored[scored["label"] == "Persuadable"]
    return {
        "as_of": as_of.date().isoformat(),
        "columns": columns,
        "rows_read": int(rows_read),
        "rows_used": int(len(sales)),
        "dropped": {k: int(v) for k, v in dropped.items()},
        "summary": {
            "customers": int(len(scored)),
            "persuadable": int(labels.get("Persuadable", 0)),
            "sure_thing": int(labels.get("Sure Thing", 0)),
            "lost_cause": int(labels.get("Lost Cause", 0)),
            # visits the shop can expect *because* of messaging its Persuadables, model estimate
            "extra_visits_if_persuadables_messaged": round(float(persuadable["uplift"].clip(lower=0).sum()), 1),
        },
        "customers": rows,
    }

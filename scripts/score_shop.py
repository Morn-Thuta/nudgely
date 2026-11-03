"""Score a shop's customers from its sales export.

Run from repo root:
  python scripts/score_shop.py --sales data/examples/sales_sample.csv
  python scripts/score_shop.py --sales mysales.csv --out data/shop_scores.csv --top 15

The sales file needs phone, date and amount, one row per purchase. Column names
can be remapped with --columns if the shop's export calls them something else,
for example: --columns "mobile=phone,txn_date=date,total=amount"
"""

import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd  # noqa: E402

from nudgely.scoring import score_sales  # noqa: E402


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--sales", required=True)
    p.add_argument("--out", default="")
    p.add_argument("--top", type=int, default=10, help="how many to print")
    p.add_argument("--columns", default="", help="their_name=our_name pairs, comma separated")
    p.add_argument("--today", default="", help="score as at this date (default: last purchase)")
    a = p.parse_args()

    sales = pd.read_csv(a.sales)
    if a.columns:
        mapping = dict(pair.split("=", 1) for pair in a.columns.split(","))
        sales = sales.rename(columns={k.strip(): v.strip() for k, v in mapping.items()})

    missing = [c for c in ("phone", "date", "amount") if c not in sales.columns]
    if missing:
        sys.exit(f"{a.sales} has no {', '.join(missing)} column. Columns found: "
                 f"{list(sales.columns)}. Use --columns to remap.")

    scores = score_sales(sales, today=a.today or None)

    counts = scores.label.value_counts()
    print(f"{len(sales):,} purchases from {len(scores)} customers in {a.sales}")
    print("  " + "  ".join(f"{label}: {n}" for label, n in counts.items()))
    print()
    show = scores.head(a.top)
    print(f"Top {len(show)} by uplift - message these first:")
    print(f"  {'phone':<12} {'uplift':>8} {'if msg':>8} {'if not':>8}  label")
    for _, r in show.iterrows():
        print(f"  {r.phone:<12} {r.uplift:>+7.1%} {r.p_msg:>8.0%} {r.p_no_msg:>8.0%}  {r.label}")

    if a.out:
        scores.to_csv(a.out, index=False)
        print(f"\nwrote {a.out}")


if __name__ == "__main__":
    main()

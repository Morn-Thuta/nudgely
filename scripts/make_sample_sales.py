"""Write a sample sales export, the kind a small shop's POS or spreadsheet produces.

Run from repo root: python scripts/make_sample_sales.py [--out data/examples/sales_sample.csv]

Three columns and nothing else, because that is what a shop can realistically give you:
phone, date, amount. One row per purchase, not per customer.

The shoppers are drawn so the file is worth testing against: regulars with a steady
weekly rhythm, people who buy in bursts, someone who stopped three months ago, a
one-time visitor. If a scorer cannot tell those apart its features are not working.
"""

import argparse
import os
import random
from datetime import date, timedelta

OUT_DEFAULT = os.path.join("data", "examples", "sales_sample.csv")

# how many customers of each kind, and how they behave
KINDS = {
    "weekly regular":  dict(n=12, gap=(6, 9),   spend=(18, 45),  months=14, stopped=0),
    "fortnightly":     dict(n=10, gap=(12, 18), spend=(25, 70),  months=12, stopped=0),
    "bursty":          dict(n=8,  gap=(2, 40),  spend=(8, 90),   months=10, stopped=0),
    "lapsed":          dict(n=7,  gap=(7, 12),  spend=(20, 50),  months=11, stopped=95),
    "new this month":  dict(n=6,  gap=(5, 12),  spend=(15, 40),  months=1,  stopped=0),
    "one-off":         dict(n=5,  gap=(0, 0),   spend=(6, 25),   months=0,  stopped=0),
}


def phone(rng):
    return "9" + "".join(str(rng.randint(0, 9)) for _ in range(7))


def rows_for(rng, kind, spec, today):
    """Purchases for one customer, oldest first."""
    first = today - timedelta(days=int(spec["months"] * 30.4))
    last_allowed = today - timedelta(days=spec["stopped"])
    number = phone(rng)
    out, when = [], first
    if spec["gap"] == (0, 0):  # a single visit, somewhere in the last half year
        when = today - timedelta(days=rng.randint(20, 180))
        return [(number, when, round(rng.uniform(*spec["spend"]), 2))]
    while when <= last_allowed:
        out.append((number, when, round(rng.uniform(*spec["spend"]), 2)))
        when += timedelta(days=rng.randint(*spec["gap"]))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=OUT_DEFAULT)
    p.add_argument("--seed", type=int, default=7)
    a = p.parse_args()

    rng = random.Random(a.seed)
    today = date.today()
    rows = []
    for kind, spec in KINDS.items():
        for _ in range(spec["n"]):
            rows.extend(rows_for(rng, kind, spec, today))
    rows.sort(key=lambda r: r[1])

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        f.write("phone,date,amount\n")
        for number, when, amount in rows:
            f.write(f"{number},{when.isoformat()},{amount:.2f}\n")

    customers = len({r[0] for r in rows})
    print(f"wrote {a.out}")
    print(f"{len(rows)} purchases from {customers} customers, "
          f"{rows[0][1]} to {rows[-1][1]}")
    for kind, spec in KINDS.items():
        print(f"  {spec['n']:>3} {kind}")


if __name__ == "__main__":
    main()

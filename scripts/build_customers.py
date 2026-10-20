"""Build data/customers.csv from data/demo_pool.csv (30 real Lenta test rows).

Adds fake names and illustrative readable features (derived from the scores so they stay consistent).
mantago_client_id stays empty here: the app merges team phones at runtime from data/test_accounts.json
or Streamlit secrets [test_accounts], so clientIds (possibly phone numbers) never go into git.

Run from repo root: python scripts/build_customers.py
"""

import os

import numpy as np
import pandas as pd

# Fictional Kampung Fresh customers, one per customer_id in order C001..C030
NAMES = [
    "Aisha Rahman", "Marcus Lim", "Priya Nair", "Daniel Tan", "Siti Nurhaliza Osman", "Kelvin Ong", "Meera Pillai",
    "Jason Goh", "Nurul Huda", "Cheryl Teo", "Ravi Kumar", "Grace Chua", "Farid Ismail", "Wei Ling Ng", "Arjun Menon",
    "Hui Min Koh", "Zainal Abidin", "Rachel Seah", "Vikram Singh", "Joanne Lee", "Hafiz Rahim", "Michelle Yeo",
    "Suresh Raman", "Emily Wong", "Iskandar Yusof", "Pei Shan Lau", "Lakshmi Devi", "Benjamin Ho", "Amirah Salleh",
    "Terence Quek",
]

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

demo = pd.read_csv(os.path.join(DATA, "demo_pool.csv"))
assert len(demo) <= len(NAMES), "add more names"

rng = np.random.default_rng(7)
visits = np.clip(0.4 + 14 * demo.p_no_msg + rng.normal(0, 0.6, len(demo)), 0.2, 12).round(1)
days = np.clip(45 / visits + np.abs(rng.normal(0, 5, len(demo))), 2, 120).round().astype(int)
spend = rng.uniform(15, 90, len(demo)).round(2)

out = pd.DataFrame({
    "customer_id": demo.customer_id,
    "name": NAMES[: len(demo)],
    "channel": "whatsapp",
    "mantago_client_id": "",
    "p_no_msg": demo.p_no_msg,
    "p_msg": demo.p_msg,
    "uplift": demo.uplift,
    "label": demo.label,
    "visits_per_month": visits,
    "avg_spend_sgd": spend,
    "days_since_last_visit": days,
    "lenta_row": demo.lenta_row,
})
out.to_csv(os.path.join(DATA, "customers.csv"), index=False)
print(out[["customer_id", "name", "label", "uplift", "p_no_msg", "visits_per_month", "days_since_last_visit",
           "mantago_client_id"]].to_string(index=False))

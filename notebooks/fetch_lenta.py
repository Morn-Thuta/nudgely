"""Download Lenta once and cache it as parquet in data/raw/ (git-ignored).

Run from repo root: python notebooks/fetch_lenta.py
"""

import os

from sklift.datasets import fetch_lenta

RAW = os.path.join("data", "raw")
os.makedirs(RAW, exist_ok=True)

ds = fetch_lenta(data_home=RAW)
df = ds.data.copy()
df["visit"] = ds.target.astype("int8")
df["treatment"] = (ds.treatment == "test").astype("int8")
df.to_parquet(os.path.join(RAW, "lenta.parquet"))

print(df.shape)
print("treatment share:", df["treatment"].mean().round(3))
print("visit rate control/test:", df.groupby("treatment")["visit"].mean().round(4).to_dict())
print("columns:", list(df.columns))

"""Aggregated, Tableau-ready extract: one row per score x 10-point score bucket x vintage x segment.

No loan-level data leaves this script; buckets with fewer than 20 loans are dropped.
"""
import pandas as pd

from common import OUT, SCORES, HEAD, load_cohort

df = load_cohort(2018, 2024)
df["fthb"] = df.first_time_buyer.map({"Y": "First-time buyer", "N": "Repeat buyer"}).fillna("Unknown")
df["ltv_band"] = pd.cut(df.ltv, [0, 80, 90, 95, 200], labels=["<=80", "80-90", "90-95", ">95"])
df["purpose"] = df.loan_purpose.map({"P": "Purchase", "C": "Cash-out refi", "N": "No cash-out refi"}).fillna("Other")

frames = []
for label in HEAD:
    col = SCORES[label]
    t = df.assign(score_name=label, score_bucket=(df[col] // 10 * 10).astype(int))
    g = (t.groupby(["score_name", "score_bucket", "vintage", "fthb", "ltv_band", "purpose"], observed=True)
         .agg(loans=("loan_id", "size"), defaults_24m=("bad", "sum"), orig_upb=("orig_upb", "sum"))
         .reset_index())
    frames.append(g[g.loans >= 20])
out = pd.concat(frames)
out["vintage_complete_24m"] = out.vintage <= 2023
out.to_csv(OUT / "tableau_extract.csv", index=False)
print(f"{len(out):,} rows -> {OUT / 'tableau_extract.csv'}")

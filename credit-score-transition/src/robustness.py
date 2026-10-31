"""Robustness checks for the three main limitations.

1. Selection effect: every loan was approved on Classic FICO. Does FICO 10T / VS4 carry
   information Classic FICO lacks (incremental model test, within-band Gini)?
2. Archive timing: is the new scores' advantage concentrated in very early defaults?
3. Outcome definition: does the ranking hold for a 60+ day delinquency definition?
"""
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict

from common import OUT, SCORES, HEAD, HEADLINE_VINTAGES, load_cohort, gini

h = load_cohort(*HEADLINE_VINTAGES)
h = h.dropna(subset=["ltv", "dti"]).reset_index(drop=True)
y = h["bad"].to_numpy()

MODELS = {
    "Classic FICO": ["fico"],
    "FICO 10T": ["fico10t_current_method"],
    "VantageScore 4.0": ["vs4_current_method"],
    "Classic FICO + FICO 10T": ["fico", "fico10t_current_method"],
    "Classic FICO + VantageScore 4.0": ["fico", "vs4_current_method"],
    "Classic FICO + LTV + DTI": ["fico", "ltv", "dti"],
    "Classic FICO + LTV + DTI + FICO 10T": ["fico", "ltv", "dti", "fico10t_current_method"],
    "Classic FICO + LTV + DTI + VantageScore 4.0": ["fico", "ltv", "dti", "vs4_current_method"],
}
inc_rows = []
for name, cols in MODELS.items():
    X = (h[cols] - h[cols].mean()) / h[cols].std()
    p = cross_val_predict(LogisticRegression(max_iter=1000), X, y, cv=5, method="predict_proba")[:, 1]
    inc_rows.append({"model": name, "features": " + ".join(cols), "cv_gini": 2 * roc_auc_score(y, p) - 1})
inc = pd.DataFrame(inc_rows)
inc.to_csv(OUT / "robustness_incremental_models.csv", index=False)
print(inc.round(4).to_string(index=False))

band_rows = []
for lo in range(660, 800, 20):
    b = h[(h.fico >= lo) & (h.fico < lo + 20)]
    r = {"classic_fico_band": f"{lo}-{lo + 19}", "loans": len(b), "defaults": int(b.bad.sum()),
         "default_rate": b.bad.mean()}
    for label in HEAD:
        r[f"gini_{label}"] = gini(b.bad, b[SCORES[label]])
    band_rows.append(r)
bands = pd.DataFrame(band_rows)
bands.to_csv(OUT / "robustness_within_band_gini.csv", index=False)
print()
print(bands.round(4).to_string(index=False))

age = h["age_first_d90"].fillna(999)
timing_rows = []
for name, lo, hi in [("Early default (months 1-12)", 0, 12), ("Later default (months 13-24)", 13, 24)]:
    keep = (age > 24) | ((age >= lo) & (age <= hi))
    yy = ((age >= lo) & (age <= hi))[keep].astype(int)
    r = {"outcome": name, "defaults": int(yy.sum())}
    for label in HEAD:
        r[f"gini_{label}"] = gini(yy, h.loc[keep, SCORES[label]])
    timing_rows.append(r)

import duckdb
from common import DB
con = duckdb.connect(str(DB), read_only=True)
d60 = con.execute("SELECT loan_id, COALESCE(age_first_d60 <= 24, false)::INT AS bad60 FROM perf_loan").df()
h60 = h.merge(d60, on="loan_id")
r = {"outcome": "60+ days delinquent within 24 months", "defaults": int(h60.bad60.sum())}
for label in HEAD:
    r[f"gini_{label}"] = gini(h60.bad60, h60[SCORES[label]])
timing_rows.append(r)
timing = pd.DataFrame(timing_rows)
timing.to_csv(OUT / "robustness_outcome_timing.csv", index=False)
print()
print(timing.round(4).to_string(index=False))

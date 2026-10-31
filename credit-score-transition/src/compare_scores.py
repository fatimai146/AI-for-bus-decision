"""Head-to-head rank-ordering comparison of Classic FICO, FICO 10T and VantageScore 4.0.

Outcome: 90+ days delinquent (or a credit-loss termination) within 24 months of first payment.
Writes aggregate-only CSVs to outputs/.
"""
import pathlib
import duckdb
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
OUT.mkdir(exist_ok=True)
con = duckdb.connect(str(ROOT / "data" / "sflld.duckdb"), read_only=True)

SCORES = {
    "Classic FICO": "fico",
    "FICO 10T": "fico10t_current_method",
    "VantageScore 4.0": "vs4_current_method",
    "FICO 10T (tri-merge avg)": "fico10t_trimerge",
    "VS4 (tri-merge avg)": "vs4_trimerge",
    "FICO 10T (bi-merge lowest)": "fico10t_bi_lowest",
    "VS4 (bi-merge lowest)": "vs4_bi_lowest",
}
HEAD = ["Classic FICO", "FICO 10T", "VantageScore 4.0"]

df = con.execute("""
    SELECT o.*, s.* EXCLUDE (loan_id),
           COALESCE(p.age_first_d90 <= 24, false)::INT AS bad,
           p.ever_forbearance, p.ever_disaster
    FROM orig o JOIN scores s USING (loan_id) JOIN perf_loan p USING (loan_id)
    WHERE o.vintage BETWEEN 2018 AND 2023
""").df()
df = df.dropna(subset=list(SCORES.values()))
COHORTS = {
    "2021-2023 (headline)": df[df.vintage >= 2021],
    "2018-2020 (COVID-affected)": df[df.vintage <= 2020],
}


def metrics(y, s):
    auc = roc_auc_score(y, -s)
    fpr, tpr, _ = roc_curve(y, -s)
    cut10 = np.quantile(s, 0.10)
    cut20 = np.quantile(s, 0.20)
    return {
        "gini": 2 * auc - 1,
        "ks": float(np.max(tpr - fpr)),
        "capture_bottom10": y[s <= cut10].sum() / y.sum(),
        "capture_bottom20": y[s <= cut20].sum() / y.sum(),
    }


def bootstrap_gini_diff(y, a, b, n=300, seed=7):
    rng = np.random.default_rng(seed)
    idx = np.arange(len(y))
    diffs = []
    for _ in range(n):
        i = rng.choice(idx, len(idx), replace=True)
        diffs.append(2 * (roc_auc_score(y[i], -a[i]) - roc_auc_score(y[i], -b[i])))
    return np.percentile(diffs, [2.5, 97.5])


rows, diff_rows = [], []
for cname, c in COHORTS.items():
    y = c["bad"].to_numpy()
    for label, col in SCORES.items():
        rows.append({"cohort": cname, "score": label, "loans": len(c), "defaults": int(y.sum()),
                     **metrics(y, c[col].to_numpy())})
    base = c["fico"].to_numpy()
    for label in ["FICO 10T", "VantageScore 4.0"]:
        s = c[SCORES[label]].to_numpy()
        lo, hi = bootstrap_gini_diff(y, s, base)
        diff_rows.append({"cohort": cname, "score": label, "gini_lift_vs_classic": 2 * (
            roc_auc_score(y, -s) - roc_auc_score(y, -base)), "ci95_lo": lo, "ci95_hi": hi})

res = pd.DataFrame(rows)
res.to_csv(OUT / "score_metrics.csv", index=False)
diffs = pd.DataFrame(diff_rows)
diffs.to_csv(OUT / "gini_lift_vs_classic.csv", index=False)
print(res.round(4).to_string(index=False))
print()
print(diffs.round(4).to_string(index=False))

# Swap-set analysis: at an equal 10% decline rate, who gets approved/declined differently?
h = COHORTS["2021-2023 (headline)"].copy()
swap_rows = []
for label in ["FICO 10T", "VantageScore 4.0"]:
    for rate in [0.05, 0.10, 0.20]:
        dec_old = h["fico"] <= h["fico"].quantile(rate)
        dec_new = h[SCORES[label]] <= h[SCORES[label]].quantile(rate)
        swap_out = h[~dec_old & dec_new]
        swap_in = h[dec_old & ~dec_new]
        swap_rows.append({
            "new_score": label, "decline_rate": rate,
            "declined_by_both_n": int((dec_old & dec_new).sum()),
            "swap_in_n": len(swap_in), "swap_in_default_rate": swap_in["bad"].mean(),
            "swap_out_n": len(swap_out), "swap_out_default_rate": swap_out["bad"].mean(),
            "defaults_avoided_per_10k_loans": (swap_out["bad"].sum() - swap_in["bad"].sum()) / len(h) * 1e4,
            "approved_default_rate_classic": h.loc[~dec_old, "bad"].mean(),
            "approved_default_rate_new": h.loc[~dec_new, "bad"].mean(),
        })
swaps = pd.DataFrame(swap_rows)
swaps.to_csv(OUT / "swap_sets.csv", index=False)
print()
print(swaps.round(4).to_string(index=False))

# Segment view: where does each score add the most rank-ordering power?
seg_defs = {
    "All": h.index == h.index,
    "First-time buyer": h.first_time_buyer == "Y",
    "LTV > 90": h.ltv > 90,
    "DTI > 43": h.dti > 43,
    "Single borrower": h.num_borrowers == 1,
    "Cash-out refi": h.loan_purpose == "C",
    "Classic FICO < 700": h.fico < 700,
}
seg_rows = []
for sname, m in seg_defs.items():
    s = h[m]
    y = s["bad"].to_numpy()
    r = {"segment": sname, "loans": len(s), "default_rate": y.mean()}
    for label in HEAD:
        r[f"gini_{label}"] = 2 * roc_auc_score(y, -s[SCORES[label]].to_numpy()) - 1
    seg_rows.append(r)
segs = pd.DataFrame(seg_rows)
segs.to_csv(OUT / "segment_gini.csv", index=False)
print()
print(segs.round(4).to_string(index=False))

"""Head-to-head rank-ordering comparison of Classic FICO, FICO 10T and VantageScore 4.0.

Outcome: 90+ days delinquent (or a credit-loss termination) within 24 months of first payment.
Writes aggregate-only CSVs to outputs/.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score, roc_curve

from common import (OUT, SCORES, HEAD, HEADLINE_VINTAGES, COVID_VINTAGES,
                    load_cohort, gini, decline_mask)

COHORTS = {
    "2021-2023 (headline)": load_cohort(*HEADLINE_VINTAGES),
    "2018-2020 (COVID-affected)": load_cohort(*COVID_VINTAGES),
}


def metrics(y, s):
    fpr, tpr, _ = roc_curve(y, -s)
    return {
        "gini": gini(y, s),
        "ks": float(np.max(tpr - fpr)),
        "capture_bottom10": y[decline_mask(s, 0.10)].sum() / y.sum(),
        "capture_bottom20": y[decline_mask(s, 0.20)].sum() / y.sum(),
    }


def bootstrap(y, a, b, n=300, seed=7):
    """Paired bootstrap of Gini(a), Gini(b) and Gini(a) - Gini(b)."""
    rng = np.random.default_rng(seed)
    ga, gb = [], []
    for _ in range(n):
        i = rng.integers(0, len(y), len(y))
        ga.append(2 * roc_auc_score(y[i], -a[i]) - 1)
        gb.append(2 * roc_auc_score(y[i], -b[i]) - 1)
    ga, gb = np.array(ga), np.array(gb)
    return ga, gb, ga - gb


rows, diff_rows = [], []
for cname, c in COHORTS.items():
    y = c["bad"].to_numpy()
    base = c["fico"].to_numpy()
    boot = {}
    for label in ["FICO 10T", "VantageScore 4.0"]:
        s = c[SCORES[label]].to_numpy()
        ga, gb, d = bootstrap(y, s, base)
        boot[label], boot["Classic FICO"] = ga, gb
        diff_rows.append({"cohort": cname, "score": label, "gini_lift_vs_classic": gini(y, s) - gini(y, base),
                          "ci95_lo": np.percentile(d, 2.5), "ci95_hi": np.percentile(d, 97.5)})
    for label, col in SCORES.items():
        r = {"cohort": cname, "score": label, "loans": len(c), "defaults": int(y.sum()),
             **metrics(y, c[col].to_numpy())}
        if label in boot:
            r["gini_ci95_lo"], r["gini_ci95_hi"] = np.percentile(boot[label], [2.5, 97.5])
        rows.append(r)

res = pd.DataFrame(rows)
res.to_csv(OUT / "score_metrics.csv", index=False)
diffs = pd.DataFrame(diff_rows)
diffs.to_csv(OUT / "gini_lift_vs_classic.csv", index=False)
print(res.round(4).to_string(index=False))
print()
print(diffs.round(4).to_string(index=False))

# Swap sets: at an equal decline rate, who is approved/declined differently and how do they perform?
h = COHORTS["2021-2023 (headline)"]
swap_rows = []
for label in ["FICO 10T", "VantageScore 4.0"]:
    for rate in [0.05, 0.10, 0.20]:
        dec_old = decline_mask(h["fico"], rate)
        dec_new = decline_mask(h[SCORES[label]], rate)
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

# Segments: where does each score add the most rank-ordering power?
seg_defs = {
    "All": np.ones(len(h), dtype=bool),
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
        r[f"gini_{label}"] = gini(y, s[SCORES[label]])
    seg_rows.append(r)
segs = pd.DataFrame(seg_rows)
segs.to_csv(OUT / "segment_gini.csv", index=False)
print()
print(segs.round(4).to_string(index=False))

# Default rate by score decile (decile 1 = lowest scores).
dec_rows = []
for label in HEAD:
    s = h[SCORES[label]].to_numpy()
    rank = np.argsort(np.argsort(s + np.random.default_rng(0).random(len(s)) * 1e-3))
    decile = rank * 10 // len(s) + 1
    g = pd.DataFrame({"decile": decile, "bad": h["bad"], "score": s}).groupby("decile")
    for d, grp in g:
        dec_rows.append({"score_name": label, "decile": d, "loans": len(grp), "min_score": grp.score.min(),
                         "max_score": grp.score.max(), "default_rate": grp.bad.mean(),
                         "share_of_defaults": grp.bad.sum() / h["bad"].sum()})
pd.DataFrame(dec_rows).to_csv(OUT / "default_rate_by_decile.csv", index=False)

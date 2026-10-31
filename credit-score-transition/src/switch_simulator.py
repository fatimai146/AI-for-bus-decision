"""Switch simulator: approval rate vs default rate and expected loss for each score.

For each decline rate (lowest-scored X% of loans declined), reports the approved book's
default rate and expected loss. Then answers the business question: at the same risk level
as Classic FICO, how many more borrowers could each new score approve?

Expected loss = defaulted original balance x assumed loss severity. Realized losses in this
window are sparse (275 loans, ~26% average severity), so a 25% severity is assumed.
"""
import numpy as np
import pandas as pd

from common import OUT, SCORES, HEAD, HEADLINE_VINTAGES, load_cohort, decline_mask

LOSS_SEVERITY = 0.25
h = load_cohort(*HEADLINE_VINTAGES)
bad = h["bad"].to_numpy()
upb = h["orig_upb"].to_numpy()

rows = []
for label in HEAD:
    s = h[SCORES[label]].to_numpy()
    for rate in np.round(np.arange(0, 0.301, 0.01), 2):
        approved = ~decline_mask(s, rate)
        rows.append({
            "score": label, "decline_rate": rate, "approval_rate": approved.mean(),
            "approved_loans": int(approved.sum()),
            "approved_default_rate": bad[approved].mean(),
            "defaults_per_10k_approved": bad[approved].mean() * 1e4,
            "expected_loss_bps": (bad[approved] * upb[approved]).sum() * LOSS_SEVERITY / upb[approved].sum() * 1e4,
        })
sim = pd.DataFrame(rows)
sim.to_csv(OUT / "switch_simulator.csv", index=False)

fine_rates = np.round(np.arange(0, 0.2501, 0.001), 3)
fine = {label: np.array([bad[~decline_mask(h[SCORES[label]], r)].mean() for r in fine_rates])
        for label in HEAD}
equal_rows = []
for rate in [0.05, 0.10, 0.15, 0.20]:
    target = fine["Classic FICO"][np.searchsorted(fine_rates, rate)]
    for label in ["FICO 10T", "VantageScore 4.0"]:
        new_rate = fine_rates[np.argmax(fine[label] <= target)]
        equal_rows.append({
            "classic_decline_rate": rate,
            "classic_approved_default_rate": target,
            "new_score": label,
            "new_decline_rate_for_same_risk": new_rate,
            "extra_approvals_per_10k_applicants": round((rate - new_rate) * 1e4),
        })
equal = pd.DataFrame(equal_rows)
equal.to_csv(OUT / "switch_equal_risk.csv", index=False)

print(sim[sim.decline_rate.isin([0, 0.05, 0.1, 0.2])].round(4).to_string(index=False))
print()
print(equal.round(4).to_string(index=False))

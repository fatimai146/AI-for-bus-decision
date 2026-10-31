"""Render README / memo figures from the aggregate CSVs in outputs/ (plus the capture curve)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import OUT, FIG, SCORES, HEAD, COLORS, HEADLINE_VINTAGES, load_cohort

plt.rcParams.update({"figure.dpi": 150, "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold"})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / name, bbox_inches="tight")
    plt.close(fig)


# 1. Gini with 95% CI
m = pd.read_csv(OUT / "score_metrics.csv")
m = m[(m.cohort == "2021-2023 (headline)") & m.score.isin(HEAD)].set_index("score").loc[HEAD]
fig, ax = plt.subplots(figsize=(6, 3.6))
err = np.vstack([m.gini - m.gini_ci95_lo, m.gini_ci95_hi - m.gini])
ax.bar(HEAD, m.gini, yerr=err, capsize=6, color=[COLORS[s] for s in HEAD])
for i, v in enumerate(m.gini):
    ax.text(i, v + 0.02, f"{v:.3f}", ha="center", fontweight="bold")
ax.set_ylim(0.4, 0.66)
ax.set_ylabel("Gini (higher = better risk ranking)")
ax.set_title("Rank-ordering power, 2021-2023 originations")
save(fig, "fig1_gini.png")

# 2. Cumulative default capture curve
h = load_cohort(*HEADLINE_VINTAGES)
fig, ax = plt.subplots(figsize=(6, 4))
for label in HEAD:
    s = h[SCORES[label]].to_numpy()
    order = np.argsort(s + np.random.default_rng(0).random(len(s)) * 1e-3)
    cum = np.cumsum(h["bad"].to_numpy()[order]) / h["bad"].sum()
    x = np.arange(1, len(s) + 1) / len(s)
    ax.plot(x * 100, cum * 100, label=label, color=COLORS[label], lw=2)
ax.plot([0, 100], [0, 100], ls=":", color="black", lw=1, label="Random")
ax.axvline(10, color="grey", lw=0.8, ls="--")
ax.set_xlim(0, 40)
ax.set_ylim(0, 85)
ax.set_xlabel("% of loans, lowest scores first")
ax.set_ylabel("% of all defaults captured")
ax.set_title("Who catches the defaults first?")
ax.legend(frameon=False, loc="lower right")
save(fig, "fig2_capture_curve.png")

# 3. Default rate by decile
d = pd.read_csv(OUT / "default_rate_by_decile.csv")
fig, ax = plt.subplots(figsize=(6, 3.6))
w = 0.27
for i, label in enumerate(HEAD):
    g = d[d.score_name == label]
    ax.bar(g.decile + (i - 1) * w, g.default_rate * 100, width=w, label=label, color=COLORS[label])
ax.set_xticks(range(1, 11))
ax.set_xlabel("Score decile (1 = lowest 10% of scores)")
ax.set_ylabel("Default rate within 24 months (%)")
ax.set_title("Default rate by score decile")
ax.legend(frameon=False)
save(fig, "fig3_default_by_decile.png")

# 4. Within-band Gini (selection-effect test)
b = pd.read_csv(OUT / "robustness_within_band_gini.csv")
fig, ax = plt.subplots(figsize=(7, 3.6))
x = np.arange(len(b))
for i, label in enumerate(HEAD):
    ax.bar(x + (i - 1) * w, b[f"gini_{label}"], width=w, label=label, color=COLORS[label])
ax.set_xticks(x)
ax.set_xticklabels(b.classic_fico_band)
ax.set_xlabel("Classic FICO band (borrowers Classic FICO sees as near-identical)")
ax.set_ylabel("Gini within band")
ax.set_title("New scores still separate risk inside each Classic FICO band")
ax.set_ylim(0, 0.5)
ax.legend(frameon=False, ncol=3, loc="upper center")
save(fig, "fig4_within_band.png")

# 5. Switch simulator
sim = pd.read_csv(OUT / "switch_simulator.csv")
fig, ax = plt.subplots(figsize=(6, 4))
for label in HEAD:
    g = sim[sim.score == label]
    ax.plot(g.approval_rate * 100, g.approved_default_rate * 100, label=label, color=COLORS[label], lw=2)
ax.axhline(sim[(sim.score == "Classic FICO") & (sim.decline_rate == 0.10)].approved_default_rate.iloc[0] * 100,
           color="grey", ls="--", lw=0.8)
ax.text(70, 1.13, "Classic FICO risk at 90% approval", ha="right", fontsize=8, color="grey")
ax.invert_xaxis()
ax.set_xlabel("Approval rate (%)")
ax.set_ylabel("Default rate of approved loans (%)")
ax.set_title("Switch simulator: approvals vs. risk")
ax.legend(frameon=False)
save(fig, "fig5_switch_simulator.png")

# 6. Swap sets at 10% decline rate
s = pd.read_csv(OUT / "swap_sets.csv")
s = s[s.decline_rate == 0.10]
fig, ax = plt.subplots(figsize=(6, 3.6))
x = np.arange(len(s))
ax.bar(x - 0.2, s.swap_out_default_rate * 100, width=0.4, color="#c0392b", label="Newly declined by new score")
ax.bar(x + 0.2, s.swap_in_default_rate * 100, width=0.4, color="#27ae60", label="Newly approved by new score")
for i, (o, n) in enumerate(zip(s.swap_out_default_rate, s.swap_in_default_rate)):
    ax.text(i - 0.2, o * 100 + 0.1, f"{o:.1%}", ha="center")
    ax.text(i + 0.2, n * 100 + 0.1, f"{n:.1%}", ha="center")
ax.set_xticks(x)
ax.set_xticklabels(s.new_score)
ax.set_ylabel("Default rate within 24 months (%)")
ax.set_title("Swap sets vs. Classic FICO at a 10% decline rate")
ax.set_ylim(0, 7.5)
ax.legend(frameon=False, ncol=2, loc="upper center", fontsize=8)
save(fig, "fig6_swap_sets.png")
print("figures written to", FIG)

"""Charts for the README (reads outputs/*.csv)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import COLORS, FIG, OUT, ensure_dirs

plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def fig_grading():
    m = pd.read_csv(OUT / "grading_metrics.csv").iloc[::-1]
    cols = [COLORS["ai"] if n.startswith("AI") else COLORS["base"] for n in m["model"]]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.6), sharey=True)
    a1.barh(m["model"], m["r2"].clip(lower=0), color=cols)
    for i, v in enumerate(m["r2"]):
        a1.text(max(v, 0) + 0.01, i, f"{v:.2f}", va="center", fontsize=7.5)
    a1.set_xlabel("Share of grade variation explained (R², out-of-sample)")
    a1.set_xlim(0, 1)
    a2.barh(m["model"], m["within_1_group"] * 100, color=cols)
    for i, v in enumerate(m["within_1_group"]):
        a2.text(v * 100 + 1, i, f"{v*100:.0f}%", va="center", fontsize=7.5)
    a2.set_xlabel("Jobs graded within 1 salary group of official (%)")
    a2.set_xlim(0, 100)
    fig.suptitle("Grading 1,165 state jobs from their descriptions (job families never seen in training)",
                 fontsize=10)
    save(fig, "fig1_grading_accuracy")


def fig_matching():
    m = pd.read_csv(OUT / "market_match_metrics.csv")
    r = pd.read_csv(OUT / "market_match_routing.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.6), gridspec_kw={"width_ratios": [1.4, 1]})
    x = np.arange(3)
    w = 0.26
    cols = [COLORS["base"], COLORS["ai"], COLORS["accent"]]
    for i, (_, row) in enumerate(m.iterrows()):
        vals = [row["top1_accuracy"], row["top3_accuracy"], row["top5_accuracy"]]
        a1.bar(x + (i - 1) * w, np.array(vals) * 100, w, color=cols[i], label=row["method"])
        for xi, v in zip(x + (i - 1) * w, vals):
            a1.text(xi, v * 100 + 1, f"{v*100:.0f}", ha="center", fontsize=7)
    a1.set_xticks(x, ["Top choice correct", "Correct in top 3", "Correct in top 5"])
    a1.set_ylabel("Hand-labeled job families (%)")
    a1.set_ylim(0, 130)
    a1.legend(frameon=False, fontsize=7.5, loc="upper left", ncol=3)
    a1.set_title(f"Matching state jobs to federal occupations ({int(m['families'].iloc[0])} labeled families)",
                 fontsize=9)

    a2.bar([f"All\n({r['families_auto_accepted'][0]})", f"Top 75%\n({r['families_auto_accepted'][1]})",
            f"Top 50%\n({r['families_auto_accepted'][2]})"],
           r["top1_accuracy_auto"] * 100, color=COLORS["accent"])
    for i, v in enumerate(r["top1_accuracy_auto"]):
        a2.text(i, v * 100 + 1, f"{v*100:.0f}%", ha="center", fontsize=8)
    a2.set_ylim(0, 110)
    a2.set_ylabel("Hybrid top choice correct (%)")
    a2.set_xlabel("Matches auto-accepted, ranked by confidence (n)", fontsize=8)
    a2.set_title("Auto-accept only confident matches;\nroute the rest to an analyst", fontsize=9)
    save(fig, "fig2_market_matching")


def fig_checks():
    g = pd.read_csv(OUT / "grading_gender_check.csv").iloc[::-1]
    s = pd.read_csv(OUT / "grading_vs_sao_reallocations.csv").iloc[0]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.2), gridspec_kw={"width_ratios": [1.5, 1]})
    y = range(len(g))
    a1.errorbar(g["gap_all_female_vs_all_male_pct"], y,
                xerr=[g["gap_all_female_vs_all_male_pct"] - g["ci_low"], g["ci_high"] - g["gap_all_female_vs_all_male_pct"]],
                fmt="o", color=COLORS["neutral"], capsize=2)
    a1.axvline(0, color="black", lw=0.8)
    a1.set_yticks(list(y), g["specification"], fontsize=8)
    a1.set_xlabel("Official grade vs AI estimate, all-female vs all-male job (%)")
    a1.set_title("Bias check: are female-dominated jobs graded lower\nthan their descriptions predict? (95% CI)",
                 fontsize=9)
    a2.bar(["SAO recommended\nupgrade", "Not recommended"],
           [s["share_recommended_where_ai_higher"] * 100, s["share_others_where_ai_higher"] * 100],
           color=[COLORS["flag"], COLORS["base"]])
    for i, v in enumerate([s["share_recommended_where_ai_higher"], s["share_others_where_ai_higher"]]):
        a2.text(i, v * 100 + 1.5, f"{v*100:.0f}%", ha="center", fontsize=8)
    a2.set_ylim(0, 80)
    a2.set_ylabel("Jobs the AI grades higher than official (%)")
    a2.set_title(f"External check vs State Auditor regrades\n(AUC {s['auc_ai_gap_predicts_reallocation']:.2f}; 0.50 = chance)",
                 fontsize=9)
    save(fig, "fig3_checks")


def main():
    ensure_dirs()
    fig_grading()
    fig_matching()
    fig_checks()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()

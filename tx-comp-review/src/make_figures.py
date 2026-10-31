"""Charts for the README and memo (reads outputs/*.csv)."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from common import COLORS, FIG, OUT, ensure_dirs

plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False})
BANDS = ["2-5", "5-10", "10-20", "20+"]
KEEP_UPPER = {"I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "IT"}


def nice_title(s):
    return " ".join(w if w in KEEP_UPPER else w.capitalize() for w in s.split())


def save(fig, name):
    fig.tight_layout()
    fig.savefig(FIG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)


def fig_tenure_premium():
    t = pd.read_csv(OUT / "tenure_premium.csv", dtype={"tenure_band": str})
    comps = {"same job title, same agency": COLORS["tenured"],
             "entry-level titles only, same agency": COLORS["accent"],
             "same job series (any level), same agency": COLORS["new"]}
    fig, ax = plt.subplots(figsize=(7.5, 4))
    w = 0.26
    for i, (c, col) in enumerate(comps.items()):
        d = t[t["comparison"] == c].set_index("tenure_band").loc[BANDS]
        x = [j + (i - 1) * w for j in range(len(BANDS))]
        ax.bar(x, d["premium_pct"], w, color=col, label=c,
               yerr=[d["premium_pct"] - d["ci_low_pct"], d["ci_high_pct"] - d["premium_pct"]],
               capsize=2, error_kw={"lw": 0.8})
        for xi, v, hi in zip(x, d["premium_pct"], d["ci_high_pct"]):
            ax.text(xi, hi + 0.4, f"{v:.0f}%", ha="center", fontsize=7)
    ax.set_xticks(range(len(BANDS)), [f"{b} yrs" for b in BANDS])
    ax.set_ylabel("Pay premium over new hires (<2 yrs)")
    ax.set_title("Long service earns little extra pay within the same job")
    ax.legend(frameon=False, fontsize=7.5, loc="upper left")
    ax.set_ylim(0, 27)
    save(fig, "fig1_tenure_premium")


def fig_range_position():
    t = pd.read_csv(OUT / "range_position_by_tenure.csv", dtype={"tenure_band": str})
    fig, ax = plt.subplots(figsize=(6.5, 3.6))
    cols = [COLORS["new"], COLORS["mid"], COLORS["mid"], COLORS["tenured"], COLORS["tenured"]]
    ax.bar(t["tenure_band"] + " yrs", t["median_penetration"] * 100, color=cols)
    for i, r in t.iterrows():
        ax.text(i, r["median_penetration"] * 100 + 1.5,
                f"{r['median_penetration']*100:.0f}%\ncompa {r['median_compa_ratio']:.2f}",
                ha="center", fontsize=7.5)
    ax.axhline(50, color=COLORS["neutral"], lw=0.8, ls="--", label="range midpoint")
    ax.legend(frameon=False, loc="upper left", fontsize=7.5)
    ax.set_ylim(0, 80)
    ax.set_ylabel("Median position in pay range (%)")
    ax.set_title("New hires start near the midpoint; 20-year staff sit only slightly higher")
    save(fig, "fig2_range_position")


def fig_compression_titles():
    t = pd.read_csv(OUT / "compression_titles.csv")
    t = t[(t["n_new"] >= 20) & (t["n_tenured"] >= 20)].head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.barh(t["class_title"].map(nice_title), (t["ratio_new_to_tenured"] - 1) * 100, color=COLORS["tenured"])
    for i, (_, r) in enumerate(t.iterrows()):
        ax.text((r["ratio_new_to_tenured"] - 1) * 100 + 0.3, i,
                f"\\${r['median_new']/1e3:.0f}k vs \\${r['median_tenured']/1e3:.0f}k", va="center", fontsize=7)
    ax.set_xlabel("New-hire median pay above 10+ year staff (%)")
    ax.set_title("Job titles where new hires out-earn 10+ year veterans\n(statewide, 20+ employees in each group)")
    ax.set_xlim(0, ax.get_xlim()[1] * 1.3)
    save(fig, "fig3_compression_titles")


def fig_cost_by_agency():
    t = pd.read_csv(OUT / "cost_to_fix_by_agency.csv").head(8).iloc[::-1]
    names = t["agency_name"].str.title().str.replace("Department", "Dept").str.replace("Commission", "Comm.")
    fig, ax = plt.subplots(figsize=(7, 3.8))
    y = range(len(t))
    ax.barh([i + 0.2 for i in y], t["s2_cost"] / 1e6, 0.4, color=COLORS["new"], label="Floor + tenure step")
    ax.barh([i - 0.2 for i in y], t["s1_cost"] / 1e6, 0.4, color=COLORS["tenured"], label="Compression floor")
    ax.set_yticks(list(y), names)
    ax.set_xlabel("Annual base-pay cost ($ millions)")
    ax.set_title("Cost to fix compression, largest agencies")
    ax.legend(frameon=False, loc="lower right")
    save(fig, "fig4_cost_by_agency")


def fig_pay_equity():
    t = pd.read_csv(OUT / "pay_equity_models.csv")
    order = ["Women vs men", "Black vs White", "Hispanic vs White", "Asian vs White",
             "American Indian vs White", "Other vs White"]
    raw = t[t["model"] == "1. Raw gap"].set_index("group").loc[order]
    adj = t[t["model"] == "4. + tenure"].set_index("group").loc[order]
    fig, ax = plt.subplots(figsize=(6.8, 3.6))
    y = list(range(len(order)))[::-1]
    ax.scatter(raw["gap_pct"], y, color=COLORS["neutral"], label="Raw gap", zorder=3)
    ax.errorbar(adj["gap_pct"], y, xerr=[adj["gap_pct"] - adj["ci_low_pct"], adj["ci_high_pct"] - adj["gap_pct"]],
                fmt="o", color=COLORS["tenured"], label="Same job, same agency, same tenure", zorder=3)
    for yi, r, a in zip(y, raw["gap_pct"], adj["gap_pct"]):
        ax.plot([r, a], [yi, yi], color="#cccccc", zorder=1)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_yticks(y, order)
    ax.set_xlabel("Pay difference (%)")
    ax.set_title("Raw pay gaps almost vanish once job, agency and tenure are matched")
    ax.legend(frameon=False, fontsize=7.5, loc="lower right")
    save(fig, "fig5_pay_equity")


def fig_market():
    t = pd.read_csv(OUT / "market_comparison.csv").dropna(subset=["market_index_texas"])
    t = t.sort_values("market_index_texas")
    fig, ax = plt.subplots(figsize=(7, 5.2))
    cols = [COLORS["new"] if tech else COLORS["neutral"] for tech in t["tech_role"]]
    ax.barh(t["series"], t["market_index_texas"], color=cols)
    for i, v in enumerate(t["market_index_texas"]):
        ax.text(v + 0.01, i, f"{v:.2f}", va="center", fontsize=7)
    ax.axvline(1, color="black", lw=0.8)
    ax.set_xlim(0.5, 1.15)
    ax.set_xlabel("State median pay / Texas market median (1.00 = at market)")
    ax.set_title("State pay vs Texas market (BLS OEWS, aged to Oct 2026)\nblue = technology roles")
    save(fig, "fig6_market_index")


def main():
    ensure_dirs()
    fig_tenure_premium()
    fig_range_position()
    fig_compression_titles()
    fig_cost_by_agency()
    fig_pay_equity()
    fig_market()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()

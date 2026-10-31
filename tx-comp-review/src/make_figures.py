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
    s = pd.read_csv(OUT / "title_premium_summary.csv")
    t = pd.read_csv(OUT / "title_premium.csv")
    order = ["new hires paid significantly more", "no significant difference",
             "veterans paid more, but under 5%", "veterans paid 5%+ more"]
    cols = [COLORS["tenured"], COLORS["accent"], COLORS["mid"], COLORS["new"]]
    s = s.set_index("result").loc[order]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10, 3.8), gridspec_kw={"width_ratios": [1, 1.25]})
    a1.barh(range(4)[::-1], s["titles"], color=cols)
    for i, (n, sh) in zip(range(4)[::-1], zip(s["titles"], s["share"])):
        a1.text(n + 1, i, f"{n} ({sh*100:.0f}%)", va="center", fontsize=8)
    a1.set_yticks(range(4)[::-1], [o[0].upper() + o[1:] for o in order], fontsize=8)
    a1.set_xlim(0, s["titles"].max() * 1.35)
    a1.set_xlabel("Job titles")
    a1.set_title(f"10+ yr vs new-hire pay, same title and agency\n({len(t)} titles with 20+ in each group)", fontsize=9)

    inv = t[t["result"] == order[0]].sort_values("premium_pct", ascending=False)
    y = range(len(inv))
    a2.errorbar(inv["premium_pct"], y, xerr=[inv["premium_pct"] - inv["ci_low_pct"],
                inv["ci_high_pct"] - inv["premium_pct"]], fmt="o", color=COLORS["tenured"], capsize=2)
    a2.axvline(0, color="black", lw=0.8)
    a2.set_yticks(list(y), [f"{nice_title(n)} ({a} agencies)" for n, a in zip(inv["class_title"], inv["agencies"])],
                  fontsize=8)
    a2.set_xlabel("10+ year staff pay vs new hires, same agency (%, 95% CI)")
    a2.set_title("Titles where new hires are paid significantly more", fontsize=9)
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
    ax.set_title("Annual cost of a pay floor for experienced staff, largest agencies")
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


def fig_structure():
    from common import connect
    con = connect()
    lad = con.execute("""
        SELECT c.level, c.class_title_sao AS title, c.salary_group, r.range_min, r.range_max, r.range_mid,
               quantile_cont(e.annual, 0.1) AS p10, median(e.annual) AS p50, quantile_cont(e.annual, 0.9) AS p90,
               count(e.annual) AS n
        FROM classes c JOIN ranges r USING (salary_group)
        LEFT JOIN emp e USING (class_code)
        WHERE c.series = 'Accountant' GROUP BY ALL ORDER BY c.level""").df()
    con.close()
    pairs = pd.read_csv(OUT / "structure_ladders.csv")

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 4), gridspec_kw={"width_ratios": [1.3, 1]})
    for i, r in lad.iterrows():
        a1.bar(i, (r["range_max"] - r["range_min"]) / 1e3, bottom=r["range_min"] / 1e3, width=0.6,
               color=COLORS["mid"], alpha=0.6, label="Official range" if i == 0 else None)
        a1.plot([i, i], [r["p10"] / 1e3, r["p90"] / 1e3], color=COLORS["tenured"], lw=2,
                label="Actual pay, 10th-90th pct" if i == 0 else None)
        a1.plot(i, r["p50"] / 1e3, "o", color=COLORS["tenured"], label="Actual median" if i == 0 else None)
    a1.set_xticks(range(len(lad)), [f"{t.split()[-1]}\n{g}" for t, g in zip(lad["title"], lad["salary_group"])])
    a1.set_ylim(lad["range_min"].min() / 1e3 - 5, lad["range_max"].max() / 1e3 + 5)
    a1.set_ylabel("Annual salary ($k)")
    a1.set_xlabel("Accountant level and salary group")
    a1.set_title("Example ladder (Accountant I-VII): wide, overlapping ranges,\nactual pay clustered mid-range", fontsize=9)
    a1.legend(frameon=False, fontsize=7.5, loc="upper left")

    a2.hist(pairs["range_overlap"] * 100, bins=range(0, 101, 5), color=COLORS["neutral"])
    a2.set_xlim(30, 100)
    a2.axvline(50, color="black", ls="--", lw=0.8)
    a2.text(48, a2.get_ylim()[1] * 0.92, "common guide:\nunder 50%", ha="right", fontsize=7.5)
    a2.set_xlabel("Range overlap with the next level up (%)")
    a2.set_ylabel("Adjacent level pairs")
    a2.set_title(f"All {len(pairs)} level pairs in {pairs['series'].nunique()} career ladders", fontsize=9)
    save(fig, "fig7_structure")


def main():
    ensure_dirs()
    fig_tenure_premium()
    fig_range_position()
    fig_compression_titles()
    fig_cost_by_agency()
    fig_pay_equity()
    fig_market()
    fig_structure()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()

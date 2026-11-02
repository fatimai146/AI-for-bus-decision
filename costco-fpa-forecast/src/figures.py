import matplotlib
import matplotlib.dates

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from common import COLORS, FIG, OUT, RAW, ensure_dirs

plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.titlesize": 11})


def fig1_backtest():
    y = pd.read_csv(OUT / "backtest_by_year.csv")
    s = pd.read_csv(OUT / "backtest_summary.csv").set_index("method")
    fig, ax = plt.subplots(figsize=(10, 4.6))
    x = np.arange(len(y))
    w = 0.27
    for i, (col, lab, c) in enumerate((("driver_plan_err", "Driver-based budget", COLORS["plan"]),
                                       ("naive_trend_err", "Last year's growth repeated", COLORS["neutral"]),
                                       ("ets_err", "Holt-Winters (statistical)", COLORS["fcst"]))):
        m = s.loc[col.replace("_err", ""), "FY_MAPE"]
        ax.bar(x + (i - 1) * w, y[col] * 100, w, color=c, label=f"{lab} (avg miss {m:.1%})")
    ax.plot(x, y.plan_err_ex_gasfx * 100, "o-", color=COLORS["actual"], lw=1.4, ms=4,
            label=f"Driver budget, gas & FX removed (avg miss {s.loc['driver_plan_ex_gasfx', 'FY_MAPE']:.1%})")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, [f"FY{str(v)[2:]}" for v in y.fy])
    ax.set_ylabel("Full-year sales forecast error (%)")
    ax.set_title("Budget set at the start of each fiscal year vs. actual net sales, FY2013-FY2026")
    ax.legend(loc="upper left", fontsize=8.5, ncol=2, frameon=False)
    ax.set_ylim(-9, 14)
    fig.tight_layout()
    fig.savefig(FIG / "fig1_backtest_fy_error.png", dpi=160)
    plt.close(fig)


def waterfall(ax, labels, values, title, unit_div=1000, fmt="${:,.1f}B"):
    start = values[0]
    run = start
    ax.bar(0, start / unit_div, color=COLORS["plan"])
    ax.text(0, start / unit_div, fmt.format(start / unit_div), ha="center", va="bottom", fontsize=8.5)
    for i, v in enumerate(values[1:-1], start=1):
        c = COLORS["pos"] if v >= 0 else COLORS["neg"]
        ax.bar(i, v / unit_div, bottom=run / unit_div, color=c)
        ax.text(i, (run + max(v, 0)) / unit_div, f"{'+' if v >= 0 else '-'}{fmt.format(abs(v) / unit_div)}",
                ha="center", va="bottom", fontsize=8.5)
        run += v
    ax.bar(len(values) - 1, values[-1] / unit_div, color=COLORS["actual"])
    ax.text(len(values) - 1, values[-1] / unit_div, fmt.format(values[-1] / unit_div), ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(range(len(values)), labels, fontsize=8.5)
    ax.set_title(title)
    lo = min(np.cumsum(values[:-1]).min(), values[-1]) / unit_div
    hi = max(np.cumsum(values[:-1]).max(), values[-1]) / unit_div
    pad = (hi - lo) * 0.6
    ax.set_ylim(lo - pad, hi + pad * 0.6)


def fig2_bridges():
    sb = pd.read_csv(OUT / "fy2026_sales_bridge.csv").sum()
    ob = pd.read_csv(OUT / "fy2026_oi_bridge.csv").sum()
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.4))
    waterfall(a1, ["Budget", "Underlying\ncomps", "Gas & FX", "New warehouses\n& other", "Actual"],
              [sb.plan, sb.comp_adj, sb.gas_fx, sb.new_wh_other, sb.actual],
              "FY2026 net sales: budget to actual", fmt="${:,.2f}B")
    waterfall(a2, ["Budget", "Sales\nvolume", "Gross margin\nrate", "SG&A\nrate", "Membership\nfees", "Actual"],
              [ob.plan, ob.sales_volume, ob.gross_margin_rate, ob.sga_rate + ob.other_opex, ob.membership_fees, ob.actual],
              "FY2026 operating income: budget to actual", unit_div=1, fmt="${:,.0f}M")
    a1.set_ylabel("$ billions")
    a2.set_ylabel("$ millions")
    fig.tight_layout()
    fig.savefig(FIG / "fig2_fy2026_bva_bridges.png", dpi=160)
    plt.close(fig)


def fig3_reforecast():
    r = pd.read_csv(OUT / "reforecast_accuracy.csv")
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    for fy, g in r.groupby("fy"):
        ax.plot(g.quarters_known, g.sales_err.abs() * 100, color=COLORS["neutral"], lw=0.8, alpha=0.6)
    m = r.groupby("quarters_known")[["sales_err", "oi_err"]].agg(lambda x: x.abs().mean() * 100)
    ax.plot(m.index, m.sales_err, "o-", color=COLORS["plan"], lw=2.2, label="Net sales (average across years)")
    ax.plot(m.index, m.oi_err, "s--", color=COLORS["fcst"], lw=2.2, label="Operating income (average)")
    for k, v in m.sales_err.items():
        ax.annotate(f"{v:.1f}%", (k, v), textcoords="offset points", xytext=(8, -14), fontsize=8.5, color=COLORS["plan"])
    ax.set_xticks(range(4), ["Budget\n(start of year)", "After Q1", "After Q2", "After Q3"])
    ax.set_ylabel("Full-year forecast error, absolute (%)")
    ax.set_title("Rolling reforecast: full-year error as quarters come in (FY2013-FY2026)")
    ax.plot([], [], color=COLORS["neutral"], lw=0.8, label="Net sales, individual years")
    ax.legend(frameon=False, fontsize=8.5)
    fig.tight_layout()
    fig.savefig(FIG / "fig3_reforecast_convergence.png", dpi=160)
    plt.close(fig)


def fig4_decomposition():
    d = pd.read_csv(OUT / "quarterly_actuals_and_drivers.csv")
    d = d[d.fy >= 2011]
    d["k"] = d.py_net_sales * d.cal
    d["calendar"] = d.cal - 1
    parts = {"Underlying comps (ex gas & FX)": ("comp_adj", COLORS["plan"]),
             "Gas & FX": ("gasfx", COLORS["fcst"]),
             "New warehouses & other": ("noncomp", COLORS["pos"]),
             "53rd week (calendar)": ("calendar", COLORS["neutral"])}
    a = d.groupby("fy").apply(lambda g: pd.Series({
        **{lab: np.average(g[c], weights=g.k) * 100 for lab, (c, _) in parts.items()},
        "total": (g.net_sales.sum() / g.py_net_sales.sum() - 1) * 100}))
    fig, ax = plt.subplots(figsize=(10, 4.4))
    x = np.arange(len(a))
    pos = np.zeros(len(a))
    neg = np.zeros(len(a))
    for lab, (c, col) in parts.items():
        v = a[lab].values
        ax.bar(x, np.where(v > 0, v, 0), bottom=pos, color=col, label=lab, width=0.7)
        ax.bar(x, np.where(v < 0, v, 0), bottom=neg, color=col, width=0.7)
        pos += np.where(v > 0, v, 0)
        neg += np.where(v < 0, v, 0)
    ax.plot(x, a.total, "o", color=COLORS["actual"], label="Reported net sales growth")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x, [f"FY{str(v)[2:]}" for v in a.index])
    ax.set_ylabel("Year-over-year growth (%)")
    ax.set_ylim(-7, 24)
    ax.set_title("What drove Costco's sales growth each year")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left", ncol=3)
    fig.tight_layout()
    fig.savefig(FIG / "fig4_growth_decomposition.png", dpi=160)
    plt.close(fig)


def fig5_fy2027():
    gas = pd.read_csv(RAW / "fred_GASREGW.csv", parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
    gas = gas["2024-09-01":]
    sc = pd.read_csv(OUT / "fy2027_scenarios.csv")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1.1, 1]})
    a1.plot(gas.index, gas.values, color=COLORS["actual"], lw=1.5)
    for s, e, lab in (("2024-09-02", "2025-08-31", "FY2025"), ("2025-09-01", "2026-08-30", "FY2026"),
                      ("2026-08-31", "2026-11-22", "FY27 Q1")):
        a1.axvspan(pd.Timestamp(s), pd.Timestamp(e), color=COLORS["neutral"], alpha=0.12 if "Q1" not in lab else 0.3)
        a1.text(pd.Timestamp(s) + (pd.Timestamp(e) - pd.Timestamp(s)) / 2, 4.75, lab, ha="center", fontsize=8.5)
    a1.set_ylim(2.5, 4.95)
    a1.xaxis.set_major_locator(matplotlib.dates.MonthLocator(bymonth=[3, 9]))
    a1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %Y"))
    a1.set_ylabel("$ per gallon")
    a1.set_title("U.S. regular gasoline (EIA via FRED, weekly)")
    sc = sc.iloc[::-1]
    def colors(col):
        return [COLORS["plan"] if "Budget" in s else (COLORS["pos"] if v >= 0 else COLORS["neg"])
                for s, v in zip(sc.scenario, sc[col])]
    y = np.arange(len(sc))
    a2.barh(y - 0.18, sc.sales_vs_budget * 100, 0.36, color=colors("sales_vs_budget"), label="Net sales")
    a2.barh(y + 0.18, sc.oi_vs_budget * 100, 0.36, color=colors("oi_vs_budget"), alpha=0.45, hatch="//",
            label="Operating income")
    for yy, v, o in zip(y, sc.sales_vs_budget, sc.oi_vs_budget):
        a2.text(v * 100 + (0.08 if v >= 0 else -0.08), yy - 0.18, f"{v:+.1%}", va="center",
                ha="left" if v >= 0 else "right", fontsize=8)
        a2.text(o * 100 + (0.08 if o >= 0 else -0.08), yy + 0.18, f"{o:+.1%}", va="center",
                ha="left" if o >= 0 else "right", fontsize=8, color="#555")
    base = sc[sc.scenario.str.startswith("Budget")].iloc[0]
    a2.set_yticks(y, [s if not s.startswith("Budget") else f"Budget: ${base.net_sales / 1000:.1f}B sales,\n"
                      f"${base.operating_income / 1000:.2f}B op. income" for s in sc.scenario], fontsize=8.5)
    a2.axvline(0, color="black", lw=0.8)
    a2.set_xlim(-5, 4.2)
    a2.set_xlabel("Change vs FY2027 budget (%)")
    a2.set_title("FY2027 scenarios")
    a2.legend(frameon=False, fontsize=8, loc="upper right")
    fig.tight_layout()
    fig.savefig(FIG / "fig5_fy2027_gas_scenarios.png", dpi=160)
    plt.close(fig)


def main():
    ensure_dirs()
    fig1_backtest()
    fig2_bridges()
    fig3_reforecast()
    fig4_decomposition()
    fig5_fy2027()
    print("figures written to", FIG)


if __name__ == "__main__":
    main()

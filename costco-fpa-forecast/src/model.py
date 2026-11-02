"""Driver-based quarterly plan, backtest, budget-vs-actual bridges, rolling reforecast, FY2027 plan.

All plans are built "as of" a date using only quarters released before that date.

Sales identity per quarter (growth measured per comparable week):
    sales = base_LY x calendar x (1 + adjusted comp + gas/FX effect + non-comp)
    calendar     = weeks / weeks last year (53-week years)
    adjusted comp = comparable sales excl. gasoline and FX (Costco disclosure)
    gas/FX effect = reported comp - adjusted comp
    non-comp      = everything else (mainly new warehouses), the residual of total growth
Operating income = sales x (GM% - SG&A% - other opex%) + membership fees
"""
import warnings

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from common import INTERIM, OUT, RAW, ensure_dirs

warnings.filterwarnings("ignore")

FIRST_BACKTEST_FY = 2013
# One-time items removed from the base before rolling it forward (bps of quarter net sales).
# FY2026 Q4: IEEPA tariff refunds, net of reinvestment, disclosed as +9 bps of gross margin (Exhibit 99.2).
ONE_TIME_GM_BPS = {(2026, 4): 9}
# Warehouse-count weights for the FX basket (Costco, Sept 2026); currency units per USD unless inverted
FX_WEIGHTS = {"DEXCAUS": (115, False), "DEXMXUS": (43, False), "DEXJPUS": (37, False), "DEXUSUK": (29, True),
              "DEXKOUS": (20, False), "DEXUSAL": (15, True), "DEXTAUS": (14, False)}


def quarter_weeks(pnl):
    ends = pd.concat([pnl[["fy", "fq", "end"]],
                      pnl.assign(fy=pnl.fy - 1, end=pnl.prior_end)[["fy", "fq", "end"]]])
    ends = ends.drop_duplicates(["fy", "fq"]).sort_values("end").reset_index(drop=True)
    ends["weeks"] = (ends["end"].diff().dt.days / 7).round()
    # first quarter in the file (or after a gap) has no usable predecessor
    bad = ends.weeks.isna() | (ends.weeks > 17)
    ends.loc[bad, "weeks"] = np.where(ends.loc[bad, "fq"] == 4, 16, 12)
    return ends


def load():
    pnl = pd.read_csv(INTERIM / "release_pnl.csv", parse_dates=["end", "prior_end"])
    comps = pd.read_csv(INTERIM / "release_comps.csv")
    notes = pd.read_csv(INTERIM / "release_notes.csv")
    d = pnl.merge(comps, on=["fy", "fq"]).merge(notes, on=["fy", "fq"], how="left")
    wk = quarter_weeks(pnl)
    d = d.merge(wk[["fy", "fq", "weeks"]].rename(columns={"weeks": "py_weeks"})
                .assign(fy=lambda x: x.fy + 1), on=["fy", "fq"], how="left")
    d = d[d.fy >= 2010].sort_values(["fy", "fq"]).reset_index(drop=True)
    d["cal"] = d.weeks / d.py_weeks
    d["g"] = d.net_sales / (d.py_net_sales * d.cal) - 1
    d["comp_adj"] = d.total_adj / 100
    d["gasfx"] = (d.total_rep - d.total_adj) / 100
    d["noncomp"] = d.g - d.total_rep / 100
    d["gm_pct"] = 1 - d.merch_costs / d.net_sales
    d["sga_pct"] = d.sga / d.net_sales
    d["oth_pct"] = d.other_opex / d.net_sales
    d["fee_g"] = d.membership_fees / (d.py_membership_fees * d.cal) - 1
    d["gm_pct_norm"] = d.gm_pct - [ONE_TIME_GM_BPS.get((a, b), 0) / 1e4 for a, b in zip(d.fy, d.fq)]
    d["release_order"] = np.arange(len(d))

    # long sales history for the statistical baseline (own release, else prior-year column of next release)
    hist = pd.concat([pnl[["fy", "fq", "net_sales"]],
                      pnl.assign(fy=pnl.fy - 1, net_sales=pnl.py_net_sales)[["fy", "fq", "net_sales"]]])
    hist = hist.drop_duplicates(["fy", "fq"]).merge(wk[["fy", "fq", "weeks", "end"]], on=["fy", "fq"])
    hist = hist.sort_values(["fy", "fq"])
    hist = hist[hist.fy >= 2006].reset_index(drop=True)
    return d, hist


def wmean(x, w):
    return float(np.average(x, weights=w))


def ttm(d, fy, fq, col, n=4):
    """Weeks-weighted mean of `col` over the n quarters released before (fy, fq)."""
    prior = d[(d.fy < fy) | ((d.fy == fy) & (d.fq < fq))].tail(n)
    return wmean(prior[col], prior.weeks)


def plan_year(d, fy, known=0, gasfx_override=None):
    """Plan for every quarter of `fy`, made after `known` quarters of `fy` were released.

    known=0 is the annual budget: trailing-4-quarter comp and non-comp growth, latest-quarter
    membership fee growth, gas/FX held at zero (budget rates),
    margin rates at last year's same-quarter level. known>0 is a reforecast: YTD drivers,
    gas/FX at the latest quarter's effect, and margin rates moved by the YTD year-over-year change.
    """
    ly = d[d.fy == fy - 1].set_index("fq")
    cur = d[d.fy == fy].set_index("fq")
    if known == 0:
        comp = ttm(d, fy, 1, "comp_adj")
        nonc = ttm(d, fy, 1, "noncomp")
        # fees are recognized ratably, so the latest quarter's growth already reflects lapped fee increases
        feeg = ttm(d, fy, 1, "fee_g", n=1)
        gasfx = 0.0
        dgm = dsga = 0.0
    else:
        ytd = cur.loc[1:known]
        comp = wmean(ytd.comp_adj, ytd.weeks)
        nonc = wmean(ytd.noncomp, ytd.weeks)
        feeg = wmean(ytd.fee_g, ytd.weeks)
        gasfx = ytd.gasfx.iloc[-1]
        dgm = wmean(ytd.gm_pct - ly.loc[ytd.index, "gm_pct_norm"], ytd.weeks)
        dsga = wmean(ytd.sga_pct - ly.loc[ytd.index, "sga_pct"], ytd.weeks)
    if gasfx_override is not None:
        gasfx = gasfx_override
    rows = []
    for q in range(1, 5):
        if q <= known:
            a = cur.loc[q]
            rows.append({"fy": fy, "fq": q, "status": "actual", "net_sales": a.net_sales,
                         "membership_fees": a.membership_fees, "gm_pct": a.gm_pct, "sga_pct": a.sga_pct,
                         "oth_pct": a.oth_pct, "operating_income": a.operating_income})
            continue
        b = ly.loc[q]
        weeks = cur.loc[q, "weeks"] if q in cur.index else b.weeks
        cal = weeks / b.weeks
        sales = b.net_sales * cal * (1 + comp + gasfx + nonc)
        fees = b.membership_fees * cal * (1 + feeg)
        gm, sga, oth = b.gm_pct_norm + dgm, b.sga_pct + dsga, b.oth_pct
        rows.append({"fy": fy, "fq": q, "status": "plan" if known == 0 else "reforecast",
                     "base_sales": b.net_sales, "cal": cal, "comp_adj": comp, "gasfx": gasfx, "noncomp": nonc,
                     "net_sales": sales, "membership_fees": fees, "fee_g": feeg,
                     "gm_pct": gm, "sga_pct": sga, "oth_pct": oth,
                     "operating_income": sales * (gm - sga - oth) + fees})
    return pd.DataFrame(rows)


def ets_year(hist, fy):
    """Holt-Winters on log weekly sales, trained on quarters before `fy`, forecasting its 4 quarters."""
    train = hist[hist.fy < fy]
    y = np.log(train.net_sales.values / train.weeks.values)
    fit = ExponentialSmoothing(y, trend="add", seasonal="add", seasonal_periods=4, damped_trend=True).fit()
    weeks = hist[hist.fy == fy].weeks.values
    if len(weeks) < 4:
        weeks = hist[hist.fy == fy - 1].weeks.values
    return np.exp(fit.forecast(4)) * weeks


def backtest(d, hist):
    rows = []
    for fy in range(FIRST_BACKTEST_FY, int(d.fy.max()) + 1):
        act = d[d.fy == fy].set_index("fq")
        ly = d[d.fy == fy - 1].set_index("fq")
        plan = plan_year(d, fy).set_index("fq")
        g_ly = ttm(d, fy, 1, "g")
        ets = ets_year(hist, fy)
        for q in range(1, 5):
            base = ly.loc[q, "net_sales"] * act.loc[q, "cal"]
            rows.append({"fy": fy, "fq": q, "actual": act.loc[q, "net_sales"],
                         "driver_plan": plan.loc[q, "net_sales"],
                         "naive_last_year": base,
                         "naive_trend": base * (1 + g_ly),
                         "ets": ets[q - 1],
                         "gasfx_actual": act.loc[q, "gasfx"],
                         "op_inc_actual": act.loc[q, "operating_income"],
                         "op_inc_plan": plan.loc[q, "operating_income"]})
    bt = pd.DataFrame(rows)
    methods = ["driver_plan", "naive_last_year", "naive_trend", "ets"]
    q_err = {m: (bt[m] / bt.actual - 1) for m in methods}
    fy_tot = bt.groupby("fy")[["actual", *methods, "op_inc_actual", "op_inc_plan"]].sum()
    summary = []
    for m in methods:
        e_fy = fy_tot[m] / fy_tot.actual - 1
        summary.append({"method": m,
                        "quarter_MAPE": q_err[m].abs().mean(), "quarter_bias": q_err[m].mean(),
                        "FY_MAPE": e_fy.abs().mean(), "FY_bias": e_fy.mean(),
                        "FY_MAPE_ex_FY2020_22": e_fy.drop([2020, 2021, 2022]).abs().mean(),
                        "years_within_2pct": int((e_fy.abs() <= 0.02).sum()), "n_years": len(e_fy)})
    # how much of the driver plan's miss is gas/FX, which the budget holds at zero by design
    bt["plan_err"] = bt.driver_plan / bt.actual - 1
    bt["plan_err_ex_gasfx"] = (bt.driver_plan * (1 + bt.gasfx_actual) / bt.actual - 1)
    e = bt.groupby("fy").apply(lambda x: pd.Series({
        "plan_err": x.driver_plan.sum() / x.actual.sum() - 1,
        "plan_err_ex_gasfx": (x.driver_plan * (1 + x.gasfx_actual)).sum() / x.actual.sum() - 1,
        "op_inc_err": x.op_inc_plan.sum() / x.op_inc_actual.sum() - 1}))
    summary.append({"method": "driver_plan_ex_gasfx",
                    "quarter_MAPE": bt.plan_err_ex_gasfx.abs().mean(), "quarter_bias": bt.plan_err_ex_gasfx.mean(),
                    "FY_MAPE": e.plan_err_ex_gasfx.abs().mean(), "FY_bias": e.plan_err_ex_gasfx.mean(),
                    "FY_MAPE_ex_FY2020_22": e.plan_err_ex_gasfx.drop([2020, 2021, 2022]).abs().mean(),
                    "years_within_2pct": int((e.plan_err_ex_gasfx.abs() <= 0.02).sum()), "n_years": len(e)})
    summary.append({"method": "driver_plan_operating_income",
                    "FY_MAPE": e.op_inc_err.abs().mean(), "FY_bias": e.op_inc_err.mean(),
                    "FY_MAPE_ex_FY2020_22": e.op_inc_err.drop([2020, 2021, 2022]).abs().mean(),
                    "years_within_2pct": int((e.op_inc_err.abs() <= 0.02).sum()), "n_years": len(e)})
    by_year = pd.concat([(fy_tot[methods].div(fy_tot.actual, axis=0) - 1).add_suffix("_err"), e], axis=1)
    return bt, pd.DataFrame(summary), by_year.reset_index()


def sales_bridge(d, fy, plan):
    """Plan-to-actual net sales bridge per quarter. Closes exactly by construction."""
    act = d[d.fy == fy].set_index("fq")
    rows = []
    for q, p in plan.set_index("fq").iterrows():
        a = act.loc[q]
        k = p.base_sales * p.cal
        g_a = a.net_sales / k - 1
        nonc_a = g_a - a.total_rep / 100
        rows.append({"fy": fy, "fq": q, "plan": p.net_sales,
                     "comp_adj": k * (a.comp_adj - p.comp_adj),
                     "gas_fx": k * (a.gasfx - p.gasfx),
                     "new_wh_other": k * (nonc_a - p.noncomp),
                     "actual": a.net_sales})
    b = pd.DataFrame(rows)
    b["check"] = b.plan + b.comp_adj + b.gas_fx + b.new_wh_other - b.actual
    return b


def oi_bridge(d, fy, plan):
    """Plan-to-actual operating income bridge per quarter. Closes exactly by construction."""
    act = d[d.fy == fy].set_index("fq")
    rows = []
    for q, p in plan.set_index("fq").iterrows():
        a = act.loc[q]
        rows.append({"fy": fy, "fq": q, "plan": p.operating_income,
                     "sales_volume": (a.net_sales - p.net_sales) * (p.gm_pct - p.sga_pct - p.oth_pct),
                     "gross_margin_rate": a.net_sales * (a.gm_pct - p.gm_pct),
                     "sga_rate": -a.net_sales * (a.sga_pct - p.sga_pct),
                     "other_opex": -a.net_sales * (a.oth_pct - p.oth_pct),
                     "membership_fees": a.membership_fees - p.membership_fees,
                     "actual": a.operating_income})
    b = pd.DataFrame(rows)
    b["check"] = b[["plan", "sales_volume", "gross_margin_rate", "sga_rate", "other_opex", "membership_fees"]].sum(axis=1) - b.actual
    return b


def reforecasts(d):
    rows = []
    for fy in range(FIRST_BACKTEST_FY, int(d.fy.max()) + 1):
        act = d[d.fy == fy]
        for k in range(0, 4):
            f = plan_year(d, fy, known=k)
            rows.append({"fy": fy, "quarters_known": k,
                         "sales_fcst": f.net_sales.sum(), "sales_actual": act.net_sales.sum(),
                         "oi_fcst": f.operating_income.sum(), "oi_actual": act.operating_income.sum()})
    r = pd.DataFrame(rows)
    r["sales_err"] = r.sales_fcst / r.sales_actual - 1
    r["oi_err"] = r.oi_fcst / r.oi_actual - 1
    return r


def gas_fx_drivers(d):
    """Quarter-average gas price and FX basket, year-over-year, aligned to Costco fiscal quarters."""
    gas = pd.read_csv(RAW / "fred_GASREGW.csv", parse_dates=["observation_date"]).set_index("observation_date").iloc[:, 0]
    fx = {}
    for sid, (w, inverted) in FX_WEIGHTS.items():
        s = pd.to_numeric(pd.read_csv(RAW / f"fred_{sid}.csv", parse_dates=["observation_date"])
                          .set_index("observation_date").iloc[:, 0], errors="coerce").dropna()
        fx[sid] = s if inverted else 1 / s  # USD value of one unit of local currency
    out = []
    for r in d.itertuples():
        start, end = r.end - pd.Timedelta(weeks=r.weeks) + pd.Timedelta(days=1), r.end
        pstart, pend = r.prior_end - pd.Timedelta(weeks=r.py_weeks) + pd.Timedelta(days=1), r.prior_end
        g = gas[start:end].mean() / gas[pstart:pend].mean() - 1
        tot = sum(w for w, _ in FX_WEIGHTS.values())
        f = sum(FX_WEIGHTS[s][0] / tot * (fx[s][start:end].mean() / fx[s][pstart:pend].mean() - 1) for s in fx)
        out.append({"fy": r.fy, "fq": r.fq, "gas_yoy": g, "fx_yoy": f, "gasfx": r.gasfx})
    x = pd.DataFrame(out)
    X = np.column_stack([x.gas_yoy, x.fx_yoy])
    beta, *_ = np.linalg.lstsq(X, x.gasfx, rcond=None)  # no intercept: no gas/FX change, no effect
    x["fitted"] = X @ beta
    r2 = 1 - ((x.gasfx - x.fitted) ** 2).sum() / ((x.gasfx - x.gasfx.mean()) ** 2).sum()
    return x, beta, r2, gas, fx


def sga_leverage(d):
    """Year-over-year SG&A rate change (bps) vs adjusted comp and gas/FX effect (both in points)."""
    y = (d.sga_pct - d.py_sga / d.py_net_sales) * 1e4
    X = np.column_stack([np.ones(len(d)), d.total_adj, d.total_rep - d.total_adj])
    b, *_ = np.linalg.lstsq(X, y, rcond=None)
    r2 = 1 - ((y - X @ b) ** 2).sum() / ((y - y.mean()) ** 2).sum()
    return b, r2


def fy2027(d, beta, gas, fx, lev):
    """Live FY2027 plan (fiscal year Sept 2026 - Aug 2027) built from data through FY2026 Q4."""
    ly = d[d.fy == 2026].copy()
    nxt = ly.copy()
    nxt["fy"] = 2027
    nxt[["comp_adj", "gasfx", "noncomp", "fee_g", "total_rep", "total_adj"]] = np.nan
    dd = pd.concat([d, nxt], ignore_index=True)
    base = plan_year(dd, 2027)
    # where gas and FX stand today versus each FY2026 quarter, held flat for the year ("spot" view)
    gas_now = gas.iloc[-4:].mean()
    fx_now = {s: v.iloc[-20:].mean() for s, v in fx.items()}
    tot = sum(w for w, _ in FX_WEIGHTS.values())
    spot = []
    for r in ly.itertuples():
        start = r.end - pd.Timedelta(weeks=r.weeks) + pd.Timedelta(days=1)
        g = gas_now / gas[start:r.end].mean() - 1
        f = sum(FX_WEIGHTS[s][0] / tot * (fx_now[s] / fx[s][start:r.end].mean() - 1) for s in fx)
        spot.append({"fq": r.fq, "gas_vs_ly": g, "fx_vs_ly": f,
                     "gas_effect": beta[0] * g, "fx_effect": beta[1] * f, "gasfx_spot": beta[0] * g + beta[1] * f})
    spot = pd.DataFrame(spot).set_index("fq")
    scen = {"Budget (gas & FX at zero)": base}
    # Gasoline dollars are treated as carrying no extra operating profit (fuel earns cents per gallon),
    # FX translates the whole foreign P&L, and slower comps deleverage SG&A at the historical rate.
    for name, comp_shift, gas_shock, use_fx in (("Spot gas & FX held all year", 0.0, None, True),
                                                ("Gas +25% vs FY2026", 0.0, 0.25, False),
                                                ("Gas -15% vs FY2026", 0.0, -0.15, False),
                                                ("Underlying comps 2 pts below plan", -0.02, 0.0, False),
                                                ("Comps -2 pts with spot gas & FX", -0.02, None, True)):
        s = base.copy()
        for i, p in s.iterrows():
            k = p.base_sales * p.cal
            gas_e = spot.loc[p.fq, "gas_effect"] if gas_shock is None else beta[0] * gas_shock
            fx_e = spot.loc[p.fq, "fx_effect"] if use_fx else 0.0
            core = k * (1 + p.comp_adj + comp_shift + p.noncomp)
            sga = p.sga_pct + lev[1] * comp_shift * 100 / 1e4
            margin = core * (1 + fx_e) * (p.gm_pct - sga - p.oth_pct)
            s.loc[i, ["comp_adj", "gasfx", "sga_pct", "net_sales", "operating_income"]] = [
                p.comp_adj + comp_shift, gas_e + fx_e, sga, core * (1 + gas_e + fx_e), margin + p.membership_fees]
        scen[name] = s
    table = pd.DataFrame([{"scenario": k, "net_sales": v.net_sales.sum(), "operating_income": v.operating_income.sum()}
                          for k, v in scen.items()])
    table["sales_vs_budget"] = table.net_sales / table.net_sales.iloc[0] - 1
    table["oi_vs_budget"] = table.operating_income / table.operating_income.iloc[0] - 1
    quarterly = pd.concat([v.assign(scenario=k) for k, v in scen.items()], ignore_index=True)
    return base, spot.reset_index(), table, quarterly, gas_now


def main():
    ensure_dirs()
    d, hist = load()
    d.to_csv(OUT / "quarterly_actuals_and_drivers.csv", index=False)

    bt, summary, by_year = backtest(d, hist)
    bt.to_csv(OUT / "backtest_quarters.csv", index=False)
    summary.to_csv(OUT / "backtest_summary.csv", index=False)
    by_year.to_csv(OUT / "backtest_by_year.csv", index=False)

    plan26 = plan_year(d, 2026)
    sb, ob = sales_bridge(d, 2026, plan26), oi_bridge(d, 2026, plan26)
    plan26.to_csv(OUT / "fy2026_budget.csv", index=False)
    sb.to_csv(OUT / "fy2026_sales_bridge.csv", index=False)
    ob.to_csv(OUT / "fy2026_oi_bridge.csv", index=False)
    assert sb.check.abs().max() < 1e-6 and ob.check.abs().max() < 1e-6

    rf = reforecasts(d)
    rf.to_csv(OUT / "reforecast_accuracy.csv", index=False)

    gx, beta, r2, gas, fx = gas_fx_drivers(d)
    gx.to_csv(OUT / "gas_fx_effect_model.csv", index=False)

    lev, lev_r2 = sga_leverage(d)
    plan27, spot, scen, scen_q, gas_now = fy2027(d, beta, gas, fx, lev)
    plan27.to_csv(OUT / "fy2027_plan.csv", index=False)
    spot.to_csv(OUT / "fy2027_gas_fx_spot.csv", index=False)
    scen.to_csv(OUT / "fy2027_scenarios.csv", index=False)
    scen_q.to_csv(OUT / "fy2027_scenarios_quarterly.csv", index=False)
    pd.DataFrame([{"gas_beta": beta[0], "fx_beta": beta[1], "gasfx_r2": r2, "sga_intercept_bps": lev[0],
                   "sga_bps_per_comp_pt": lev[1], "sga_bps_per_gasfx_pt": lev[2], "sga_r2": lev_r2,
                   "gas_now": gas_now, "gas_now_date": str(gas.index[-1].date())}]).to_csv(OUT / "model_parameters.csv", index=False)

    pd.set_option("display.width", 200)
    print("== Backtest FY%d-FY%d ==" % (FIRST_BACKTEST_FY, d.fy.max()))
    print(summary.round(4).to_string(index=False))
    print(by_year.round(4).to_string(index=False))
    print("\n== FY2026 sales bridge ($M) ==\n", sb.round(0).to_string(index=False))
    print("\n== FY2026 operating income bridge ($M) ==\n", ob.round(0).to_string(index=False))
    print("\n== Reforecast FY error by quarters known ==")
    print(rf.groupby("quarters_known")[["sales_err", "oi_err"]].agg(lambda x: x.abs().mean()).round(4))
    print(f"\n== Gas/FX effect model: gasfx_pp = {beta[0]:.3f} x gas_yoy + {beta[1]:.3f} x fx_yoy, R2 = {r2:.2f}")
    print(f"SG&A bps change = {lev[0]:.1f} + {lev[1]:.2f} x adj comp pts + {lev[2]:.2f} x gas/FX pts, R2 = {lev_r2:.2f}")
    print(f"gas now ${gas_now:.2f}\n", spot.round(4).to_string(index=False))
    print("\n== FY2027 plan ==\n", plan27[["fq", "net_sales", "comp_adj", "noncomp", "membership_fees", "gm_pct", "sga_pct",
                                         "operating_income"]].round(4).to_string(index=False))
    print(scen.round(4).to_string(index=False))


if __name__ == "__main__":
    main()

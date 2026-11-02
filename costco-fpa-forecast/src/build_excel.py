"""Excel workbook with a live FY2027 plan (formulas), the FY2026 budget-vs-actual bridge, and backtest results."""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from common import EXCEL, OUT, ensure_dirs

BLUE_INPUT = Font(color="1F4FD8")
BOLD = Font(bold=True)
HEAD = PatternFill("solid", fgColor="1F2937")
HEAD_FONT = Font(bold=True, color="FFFFFF")
INPUT_FILL = PatternFill("solid", fgColor="EEF4FF")
TOTAL_BORDER = Border(top=Side(style="thin"))
M = '#,##0;(#,##0)'
P1 = '0.0%'
P2 = '0.00%'
Q = ["Q1", "Q2", "Q3", "Q4"]
COLS = ["C", "D", "E", "F"]


def header(ws, row, labels, start_col=1):
    for i, lab in enumerate(labels):
        c = ws.cell(row=row, column=start_col + i, value=lab)
        c.fill, c.font = HEAD, HEAD_FONT
        c.alignment = Alignment(horizontal="center")


def put(ws, ref, value, fmt=None, font=None, fill=None):
    c = ws[ref]
    c.value = value
    if fmt:
        c.number_format = fmt
    if font:
        c.font = font
    if fill:
        c.fill = fill
    return c


def widths(ws, w):
    for i, x in enumerate(w, start=1):
        ws.column_dimensions[get_column_letter(i)].width = x


def readme(wb, params):
    ws = wb.active
    ws.title = "README"
    lines = [
        ("Costco FY2027 Forecast & Budget-vs-Actual Model", BOLD),
        ("Built only from public data: Costco 8-K earnings releases (SEC EDGAR) and FRED gasoline / exchange-rate series.", None),
        ("Independent portfolio project; not affiliated with or endorsed by Costco. Not investment advice.", None),
        ("", None),
        ("Sheets", BOLD),
        ("Inputs        - FY2027 drivers. Blue cells are inputs; change them and the plan recalculates.", None),
        ("Plan_FY2027   - quarterly P&L plan built with formulas from Inputs.", None),
        ("BvA_FY2026    - FY2026 budget (set Sept 2025) vs actual, with sales and operating-income bridges that close to zero.", None),
        ("Scenarios     - FY2027 scenario results from the Python model (gas, FX, slower comps).", None),
        ("Backtest      - accuracy of the same budget method for FY2013-FY2026 vs simple and statistical baselines.", None),
        ("Actuals       - quarterly P&L and comparable-sales drivers, FY2010-FY2026.", None),
        ("", None),
        ("Sales identity", BOLD),
        ("Net sales = last year's quarter x calendar factor x (1 + adjusted comp + non-comp) x (1 + gas effect + FX effect)", None),
        ("Adjusted comp = comparable sales excluding gasoline prices and FX, as disclosed by Costco each quarter.", None),
        ("Non-comp = growth not in comparable sales (mainly new warehouses).", None),
        ("Gas and FX are held at zero in the budget (constant prices and rates); the switch on Inputs turns on today's levels.", None),
        ("", None),
        ("Estimated relationships (FY2010-FY2026 quarters)", BOLD),
        (f"Gas/FX effect on comps = {params.gas_beta:.3f} x gas price change + {params.fx_beta:.3f} x FX basket change (R-squared {params.gasfx_r2:.2f})", None),
        (f"SG&A rate change = {params.sga_bps_per_comp_pt:.1f} bps per point of adjusted comp (R-squared of full regression {params.sga_r2:.2f})", None),
    ]
    for i, (t, f) in enumerate(lines, start=1):
        c = ws.cell(row=i, column=1, value=t)
        if f:
            c.font = f
    ws.column_dimensions["A"].width = 120


def inputs(wb, plan, spot, ly, params):
    ws = wb.create_sheet("Inputs")
    widths(ws, [46, 12, 13, 13, 13, 13, 50])
    put(ws, "A1", "FY2027 plan inputs (fiscal year Sept 2026 - Aug 2027)", font=BOLD)
    put(ws, "A3", "Global switches", font=BOLD)
    rows = [
        (4, "Underlying comp shift vs plan (points, e.g. -2)", 0, '0.0', True),
        (5, "Include gas & FX at today's levels? (1 = yes, 0 = budget)", 0, '0', True),
        (6, "Gas beta (sales % change per 1% gas price change)", params.gas_beta, '0.000', True),
        (7, "FX beta (sales % change per 1% FX basket change)", params.fx_beta, '0.000', True),
        (8, "SG&A bps per point of underlying comp", params.sga_bps_per_comp_pt, '0.00', True),
        (9, f"U.S. regular gasoline today ($/gal, 4-week avg to {params.gas_now_date})", params.gas_now, '0.00', True),
    ]
    for r, lab, v, fmt, is_input in rows:
        put(ws, f"A{r}", lab)
        put(ws, f"B{r}", float(v), fmt, BLUE_INPUT if is_input else None, INPUT_FILL if is_input else None)
    header(ws, 11, ["Per-quarter drivers", "", *Q, "Source / formula"])
    ly = ly.set_index("fq")
    plan = plan.set_index("fq")
    spot = spot.set_index("fq")
    spec = [
        (12, "FY2026 net sales ($M)", lambda q: ly.loc[q, "net_sales"], M, False, "Costco 8-K, FY2026"),
        (13, "FY2026 weeks", lambda q: ly.loc[q, "weeks"], '0', False, "Fiscal calendar"),
        (14, "FY2027 weeks", lambda q: ly.loc[q, "weeks"], '0', True, "FY2027 is a 52-week year"),
        (15, "Calendar factor", lambda q: f"={COLS[q-1]}14/{COLS[q-1]}13", '0.000', False, "= FY2027 weeks / FY2026 weeks"),
        (16, "Adjusted comp, plan", lambda q: plan.loc[q, "comp_adj"], P2, True, "Weeks-weighted FY2026 adjusted comps"),
        (17, "Non-comp growth (new warehouses), plan", lambda q: plan.loc[q, "noncomp"], P2, True, "Weeks-weighted FY2026 non-comp growth"),
        (18, "FY2026 average gas price ($/gal)", lambda q: params.gas_now / (1 + spot.loc[q, "gas_vs_ly"]), '0.00', False, "FRED GASREGW over the FY2026 quarter"),
        (19, "Gas price change vs FY2026 at today's price", lambda q: f"=$B$9/{COLS[q-1]}18-1", P1, False, "= today / FY2026 quarter average - 1"),
        (20, "FX basket change vs FY2026 at today's rates", lambda q: spot.loc[q, "fx_vs_ly"], P1, True, "Warehouse-weighted CAD, MXN, JPY, GBP, KRW, AUD, TWD"),
        (21, "Gas effect on sales", lambda q: f"=$B$5*$B$6*{COLS[q-1]}19", P2, False, "= switch x beta x gas change"),
        (22, "FX effect on sales", lambda q: f"=$B$5*$B$7*{COLS[q-1]}20", P2, False, "= switch x beta x FX change"),
        (23, "FY2026 membership fees ($M)", lambda q: ly.loc[q, "membership_fees"], M, False, "Costco 8-K, FY2026"),
        (24, "Membership fee growth, plan", lambda q: plan.loc[q, "fee_g"], P2, True, "Q4 FY2026 fee growth (latest run-rate)"),
        (25, "FY2026 gross margin % of net sales", lambda q: ly.loc[q, "gm_pct"], P2, False, "1 - merchandise costs / net sales"),
        (26, "One-time items removed (bps)", lambda q: round((ly.loc[q, "gm_pct"] - ly.loc[q, "gm_pct_norm"]) * 1e4, 2), '0.0', True, "Q4: IEEPA tariff refunds net of reinvestment (+9 bps, Costco Q4 supplement)"),
        (27, "Gross margin %, plan", lambda q: f"={COLS[q-1]}25-{COLS[q-1]}26/10000", P2, False, "= FY2026 rate less one-time items"),
        (28, "FY2026 SG&A % of net sales", lambda q: ly.loc[q, "sga_pct"], P2, False, "Costco 8-K, FY2026"),
        (29, "SG&A %, plan", lambda q: f"={COLS[q-1]}28+$B$8*$B$4/10000", P2, False, "= FY2026 rate + deleverage if comps shift"),
        (30, "Other operating expense % (preopening etc.)", lambda q: ly.loc[q, "oth_pct"], P2, True, "FY2026 rate"),
    ]
    for r, lab, fn, fmt, is_input, src in spec:
        put(ws, f"A{r}", lab)
        for q in range(1, 5):
            v = fn(q)
            v = v if isinstance(v, str) else float(v)
            put(ws, f"{COLS[q-1]}{r}", v, fmt, BLUE_INPUT if is_input else None, INPUT_FILL if is_input else None)
        put(ws, f"G{r}", src.replace("= ", "Formula: ", 1), font=Font(italic=True, color="666666"))
    ws.freeze_panes = "C12"


def plan_sheet(wb):
    ws = wb.create_sheet("Plan_FY2027")
    widths(ws, [40, 4, 13, 13, 13, 13, 14])
    put(ws, "A1", "FY2027 quarterly plan ($ millions) - all cells are formulas on Inputs", font=BOLD)
    header(ws, 3, ["", "", *Q, "FY2027"])
    I = "Inputs!"
    lines = [
        (4, "Core sales (ex gas & FX)", lambda c: f"={I}{c}12*{I}{c}15*(1+{I}{c}16+{I}$B$4/100+{I}{c}17)", M),
        (5, "Net sales", lambda c: f"={c}4*(1+{I}{c}21+{I}{c}22)", M),
        (6, "Membership fees", lambda c: f"={I}{c}23*{I}{c}15*(1+{I}{c}24)", M),
        (7, "Total revenue", lambda c: f"={c}5+{c}6", M),
        (8, "Gross margin on net sales", lambda c: f"={c}4*(1+{I}{c}22)*{I}{c}27", M),
        (9, "Merchandise costs", lambda c: f"={c}5-{c}8", M),
        (10, "SG&A", lambda c: f"={c}4*(1+{I}{c}22)*{I}{c}29", M),
        (11, "Other operating expense", lambda c: f"={c}4*(1+{I}{c}22)*{I}{c}30", M),
        (12, "Operating income", lambda c: f"={c}8-{c}10-{c}11+{c}6", M),
        (14, "Net sales growth vs FY2026", lambda c: f"={c}5/{I}{c}12-1", P1),
        (15, "Gross margin %", lambda c: f"={c}8/{c}5", P2),
        (16, "SG&A %", lambda c: f"={c}10/{c}5", P2),
        (17, "Operating margin % of total revenue", lambda c: f"={c}12/{c}7", P2),
    ]
    for r, lab, fn, fmt in lines:
        put(ws, f"A{r}", lab, font=BOLD if r in (5, 12) else None)
        for c in COLS:
            put(ws, f"{c}{r}", fn(c), fmt)
        if r <= 12:
            put(ws, f"G{r}", f"=SUM(C{r}:F{r})", fmt, BOLD)
    put(ws, "G14", "=G5/SUM(Inputs!C12:F12)-1", P1)
    put(ws, "G15", "=G8/G5", P2)
    put(ws, "G16", "=G10/G5", P2)
    put(ws, "G17", "=G12/G7", P2)
    for c in "ACDEFG":
        ws[f"{c}12"].border = TOTAL_BORDER
    put(ws, "A19", "Gasoline sales are assumed to add revenue but no operating profit (fuel earns cents per gallon).",
        font=Font(italic=True, color="666666"))


def bva_sheet(wb, d, plan26):
    ws = wb.create_sheet("BvA_FY2026")
    widths(ws, [44, 4, 13, 13, 13, 13, 14])
    put(ws, "A1", "FY2026 budget (set at the start of the year) vs actual ($ millions)", font=BOLD)
    header(ws, 3, ["Budget drivers (from FY2025 data)", "", *Q, "FY2026"])
    a = d[d.fy == 2026].set_index("fq")
    p = plan26.set_index("fq")
    vals = [
        (4, "FY2025 base net sales x calendar", lambda q: p.loc[q, "base_sales"] * p.loc[q, "cal"], M),
        (5, "Adjusted comp, budget", lambda q: p.loc[q, "comp_adj"], P2),
        (6, "Gas & FX effect, budget", lambda q: p.loc[q, "gasfx"], P2),
        (7, "Non-comp growth, budget", lambda q: p.loc[q, "noncomp"], P2),
        (8, "Gross margin %, budget", lambda q: p.loc[q, "gm_pct"], P2),
        (9, "SG&A %, budget", lambda q: p.loc[q, "sga_pct"], P2),
        (10, "Other opex %, budget", lambda q: p.loc[q, "oth_pct"], P2),
        (11, "Membership fees, budget", lambda q: p.loc[q, "membership_fees"], M),
        (14, "Net sales, actual", lambda q: a.loc[q, "net_sales"], M),
        (15, "Reported comp, actual", lambda q: a.loc[q, "total_rep"] / 100, P2),
        (16, "Adjusted comp (ex gas & FX), actual", lambda q: a.loc[q, "total_adj"] / 100, P2),
        (17, "Gross margin %, actual", lambda q: a.loc[q, "gm_pct"], P2),
        (18, "SG&A %, actual", lambda q: a.loc[q, "sga_pct"], P2),
        (19, "Other opex %, actual", lambda q: a.loc[q, "oth_pct"], P2),
        (20, "Membership fees, actual", lambda q: a.loc[q, "membership_fees"], M),
        (21, "Operating income, actual", lambda q: a.loc[q, "operating_income"], M),
    ]
    header(ws, 13, ["Actuals (Costco 8-K)", "", *Q, "FY2026"])
    for r, lab, fn, fmt in vals:
        put(ws, f"A{r}", lab)
        for q in range(1, 5):
            put(ws, f"{COLS[q-1]}{r}", float(fn(q)), fmt, BLUE_INPUT)
    for r in (4, 11, 14, 20, 21):
        put(ws, f"G{r}", f"=SUM(C{r}:F{r})", M)
    header(ws, 23, ["Net sales bridge", "", *Q, "FY2026"])
    sb = [
        (24, "Budget net sales", lambda c: f"={c}4*(1+{c}5+{c}6+{c}7)"),
        (25, "Underlying comps", lambda c: f"={c}4*({c}16-{c}5)"),
        (26, "Gas & FX", lambda c: f"={c}4*(({c}15-{c}16)-{c}6)"),
        (27, "New warehouses & other (non-comp)", lambda c: f"={c}4*(({c}14/{c}4-1-{c}15)-{c}7)"),
        (28, "Actual net sales", lambda c: f"={c}14"),
        (29, "Check (should be 0)", lambda c: f"=ROUND({c}24+{c}25+{c}26+{c}27-{c}28,6)"),
    ]
    header(ws, 31, ["Operating income bridge", "", *Q, "FY2026"])
    ob = [
        (32, "Budget operating income", lambda c: f"={c}24*({c}8-{c}9-{c}10)+{c}11"),
        (33, "Sales volume (at budget margin)", lambda c: f"=({c}14-{c}24)*({c}8-{c}9-{c}10)"),
        (34, "Gross margin rate", lambda c: f"={c}14*({c}17-{c}8)"),
        (35, "SG&A rate", lambda c: f"=-{c}14*({c}18-{c}9)"),
        (36, "Other opex rate", lambda c: f"=-{c}14*({c}19-{c}10)"),
        (37, "Membership fees", lambda c: f"={c}20-{c}11"),
        (38, "Actual operating income", lambda c: f"={c}21"),
        (39, "Check (should be 0)", lambda c: f"=ROUND(SUM({c}32:{c}37)-{c}38,6)"),
    ]
    for r, lab, fn in sb + ob:
        put(ws, f"A{r}", lab, font=BOLD if r in (24, 28, 32, 38) else None)
        for c in COLS:
            put(ws, f"{c}{r}", fn(c), M)
        put(ws, f"G{r}", f"=SUM(C{r}:F{r})", M, BOLD if r in (24, 28, 32, 38) else None)
    put(ws, "A41", "Q4 gross-margin rate includes about +$84M of IEEPA tariff refunds (9 bps of Q4 sales) that the budget could not have known.",
        font=Font(italic=True, color="666666"))


def table_sheet(wb, name, df, fmts=None, title=None, width=14):
    ws = wb.create_sheet(name)
    r0 = 1
    if title:
        put(ws, "A1", title, font=BOLD)
        r0 = 3
    header(ws, r0, list(df.columns))
    for i, row in enumerate(df.itertuples(index=False), start=r0 + 1):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v)))
            col = df.columns[j - 1]
            if fmts and col in fmts:
                c.number_format = fmts[col]
    widths(ws, [max(width, len(str(c)) + 2) for c in df.columns])
    ws.freeze_panes = ws.cell(row=r0 + 1, column=1)
    return ws


def main():
    ensure_dirs()
    d = pd.read_csv(OUT / "quarterly_actuals_and_drivers.csv")
    params = pd.read_csv(OUT / "model_parameters.csv").iloc[0]
    plan27 = pd.read_csv(OUT / "fy2027_plan.csv")
    spot = pd.read_csv(OUT / "fy2027_gas_fx_spot.csv")
    plan26 = pd.read_csv(OUT / "fy2026_budget.csv")
    wb = Workbook()
    readme(wb, params)
    inputs(wb, plan27, spot, d[d.fy == 2026].copy(), params)
    plan_sheet(wb)
    bva_sheet(wb, d, plan26)
    sc = pd.read_csv(OUT / "fy2027_scenarios.csv")
    table_sheet(wb, "Scenarios", sc, {"net_sales": M, "operating_income": M, "sales_vs_budget": P1, "oi_vs_budget": P1},
                "FY2027 scenarios ($ millions), from src/model.py", width=16).column_dimensions["A"].width = 36
    s = pd.read_csv(OUT / "backtest_summary.csv")
    pct = {c: P2 for c in s.columns if c not in ("method", "years_within_2pct", "n_years")}
    ws = table_sheet(wb, "Backtest", s, pct, "Budget accuracy FY2013-FY2026 (error = forecast / actual - 1)", width=14)
    ws.column_dimensions["A"].width = 30
    by = pd.read_csv(OUT / "backtest_by_year.csv")
    start = len(s) + 6
    header(ws, start, list(by.columns))
    for i, row in enumerate(by.itertuples(index=False), start=start + 1):
        for j, v in enumerate(row, start=1):
            c = ws.cell(row=i, column=j, value=v.item() if hasattr(v, "item") else v)
            if j > 1:
                c.number_format = P2
    cols = ["fy", "fq", "weeks", "end", "net_sales", "membership_fees", "merch_costs", "sga", "other_opex",
            "operating_income", "net_income", "total_rep", "total_adj", "us_rep", "us_adj", "warehouses",
            "comp_adj", "gasfx", "noncomp", "gm_pct", "sga_pct"]
    act = d[cols].copy()
    fm = {c: M for c in cols[4:11]}
    fm.update({c: P2 for c in ("comp_adj", "gasfx", "noncomp", "gm_pct", "sga_pct")})
    table_sheet(wb, "Actuals", act, fm, "Quarterly actuals as first reported in Costco 8-K earnings releases ($ millions; comps in %)", width=11)
    wb.calculation.fullCalcOnLoad = True
    path = EXCEL / "costco_fy2027_plan_and_bva.xlsx"
    wb.save(path)
    print("saved", path)


if __name__ == "__main__":
    main()

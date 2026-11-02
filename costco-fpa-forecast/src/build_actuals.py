"""Cross-check the parsed earnings-release P&L against Costco's XBRL company facts.

Costco's fiscal year ends on the Sunday nearest Aug 31. Quarters are 12/12/12/16 weeks
(17-week Q4 in 53-week years). XBRL has Q1-Q3 directly; Q4 = full year minus 36-week YTD.
From FY2019 XBRL tags net sales and membership fees on a dimension the company-facts feed drops,
so only total revenue and operating income are compared.
"""
import json

import pandas as pd

from common import INTERIM, OUT, RAW, ensure_dirs

CONCEPTS = {
    "net_sales": ["SalesRevenueNet", "RevenueFromContractWithCustomerExcludingAssessedTax"],
    "total_revenue": ["Revenues"],
    "membership_fees": ["RevenueFromEnrollmentAndRegistrationFeesExcludingHospitalityEnterprises"],
    "merch_costs": ["CostOfGoodsSold", "CostOfGoodsAndServicesSold"],
    "sga": ["SellingGeneralAndAdministrativeExpense"],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss"],
}


def durations(facts, names):
    rows = []
    for n in names:
        if n not in facts:
            continue
        for x in facts[n]["units"]["USD"]:
            if "start" in x:
                rows.append((x["start"], x["end"], x["val"] / 1e6, x["filed"]))
    df = pd.DataFrame(rows, columns=["start", "end", "val", "filed"])
    df["start"] = pd.to_datetime(df["start"])
    df["end"] = pd.to_datetime(df["end"])
    df["days"] = (df["end"] - df["start"]).dt.days + 1
    # restated values: keep the latest filing for each period
    return df.sort_values("filed").groupby(["start", "end"], as_index=False).last()


def fiscal_year(end):
    return end.year + 1 if end.month >= 10 else end.year


def quarterize(df):
    q = df[df["days"].between(77, 126)].copy()
    q["fy"] = q["end"].map(fiscal_year)
    q = q[q["days"] <= 91]  # Q1-Q3 are 12 weeks
    q = q.sort_values("end")
    q["fq"] = q.groupby("fy").cumcount() + 1
    out = {(r.fy, r.fq): (r.start, r.end, r.val) for r in q.itertuples()}
    annual = df[df["days"].between(357, 372)].copy()
    ytd36 = df[df["days"].between(245, 259)].copy()
    for r in annual.itertuples():
        fy = fiscal_year(r.end)
        m = ytd36[(ytd36["start"] == r.start)]
        if len(m):
            m = m.iloc[0]
            out[(fy, 4)] = (m["end"] + pd.Timedelta(days=1), r.end, r.val - m["val"])
    return out


def main():
    ensure_dirs()
    facts = json.loads((RAW / "companyfacts.json").read_text())["facts"]["us-gaap"]
    frames = {}
    for k, names in CONCEPTS.items():
        for key, (s, e, v) in quarterize(durations(facts, names)).items():
            frames.setdefault(key, {"start": s, "end": e})[k] = v
    df = pd.DataFrame.from_dict(frames, orient="index")
    df.index.names = ["fy", "fq"]
    df = df.reset_index().sort_values(["fy", "fq"])
    df["membership_fees"] = df["membership_fees"].fillna(df["total_revenue"] - df["net_sales"])
    df["weeks"] = ((df["end"] - df["start"]).dt.days + 1) // 7
    df["gross_margin"] = df["net_sales"] - df["merch_costs"]
    df["gm_pct"] = df["gross_margin"] / df["net_sales"]
    df["sga_pct"] = df["sga"] / df["net_sales"]
    df["op_check"] = df["net_sales"] + df["membership_fees"] - df["merch_costs"] - df["sga"] - df["operating_income"]
    df = df[(df["fy"] >= 2009) & df["net_sales"].notna()]
    complete = df.groupby("fy")["fq"].transform("count") == 4
    df = df[complete]
    df.to_csv(INTERIM / "xbrl_quarterly.csv", index=False)
    rel = pd.read_csv(INTERIM / "release_pnl.csv")
    m = rel.merge(df, on=["fy", "fq"], suffixes=("_release", "_xbrl"))
    m = m[m.fy >= 2010]
    out = m[["fy", "fq", "total_revenue_release", "total_revenue_xbrl", "operating_income_release", "operating_income_xbrl"]].copy()
    out["revenue_diff_pct"] = out.total_revenue_xbrl / out.total_revenue_release - 1
    out["op_income_diff_pct"] = out.operating_income_xbrl / out.operating_income_release - 1
    out.to_csv(OUT / "xbrl_crosscheck.csv", index=False)
    close = (out.revenue_diff_pct.abs() < 0.005) & (out.op_income_diff_pct.abs() < 0.005)
    print(f"XBRL cross-check: {close.sum()} of {len(out)} quarters within 0.5% on total revenue and operating income")
    print(out[~close].round(4).to_string(index=False))


if __name__ == "__main__":
    main()

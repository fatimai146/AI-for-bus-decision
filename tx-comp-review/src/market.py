"""Market comparison: state pay vs BLS OEWS (May 2025) for benchmark job families.

OEWS wages are aged forward to the payroll snapshot with an assumed annual
salary-increase rate, the standard way compensation teams age survey data.

Market index = state median salary / aged market median (1.00 = at market).

Output
  market_comparison.csv
"""
import json

import pandas as pd

from common import OEWS_JSON, OUT, connect, ensure_dirs

AGING_RATE = 0.035
AGING_MONTHS = 17  # May 2025 OEWS reference -> Oct 2026 payroll snapshot
SOC_TITLES = {
    "132011": "Accountants and Auditors", "132031": "Budget Analysts",
    "132051": "Financial and Investment Analysts", "131071": "Human Resources Specialists",
    "131151": "Training and Development Specialists", "131020": "Buyers and Purchasing Agents",
    "131111": "Management Analysts", "131082": "Project Management Specialists",
    "152051": "Data Scientists", "151211": "Computer Systems Analysts",
    "151251": "Computer Programmers", "151244": "Network and Computer Systems Administrators",
    "151231": "Computer Network Support Specialists", "151232": "Computer User Support Specialists",
    "151212": "Information Security Analysts", "151242": "Database Administrators",
    "231011": "Lawyers", "232011": "Paralegals and Legal Assistants",
    "193051": "Urban and Regional Planners",
}
TECH = {"151211", "151251", "151244", "151231", "151232", "151212", "151242", "152051"}


def oews():
    d = json.loads(OEWS_JSON.read_text())
    t = pd.DataFrame(d["rows"])
    t["value"] = pd.to_numeric(t["value"], errors="coerce")
    w = t.pivot_table(index=["soc", "area"], columns="field", values="value", aggfunc="first").reset_index()
    tx = w[w["area"] == "Texas"].drop(columns="area").add_prefix("tx_").rename(columns={"tx_soc": "soc"})
    au = w[w["area"] != "Texas"].drop(columns="area").add_prefix("austin_").rename(columns={"austin_soc": "soc"})
    return d["benchmarks"], tx.merge(au, on="soc", how="left")


def main():
    ensure_dirs()
    bench, mkt = oews()
    con = connect()
    con.register("b", pd.DataFrame({"series": list(bench), "soc": list(bench.values())}))
    state = con.execute("""
        SELECT b.series, b.soc, count(*) AS state_employees,
               quantile_cont(annual, 0.25) AS state_p25, median(annual) AS state_median,
               quantile_cont(annual, 0.75) AS state_p75, median(range_mid) AS state_range_mid_median,
               median(tenure) AS state_median_tenure
        FROM emp JOIN b USING (series) GROUP BY ALL""").df()
    con.close()

    aging = (1 + AGING_RATE) ** (AGING_MONTHS / 12)
    t = state.merge(mkt, on="soc", how="left")
    t["soc_title"] = t["soc"].map(SOC_TITLES)
    t["tech_role"] = t["soc"].isin(TECH)
    for c in ["tx_p25", "tx_median", "tx_p75", "austin_p25", "austin_median", "austin_p75"]:
        t[c + "_aged"] = t[c] * aging
    t["market_index_texas"] = t["state_median"] / t["tx_median_aged"]
    t["market_index_austin"] = t["state_median"] / t["austin_median_aged"]
    t["gap_to_texas_median"] = t["tx_median_aged"] - t["state_median"]
    t = t.sort_values("market_index_texas")
    t.to_csv(OUT / "market_comparison.csv", index=False)
    print(f"aging factor {aging:.4f}")
    print(t[["series", "soc_title", "state_employees", "state_median", "tx_median_aged",
             "market_index_texas", "market_index_austin"]].round(3).to_string(index=False))
    w = t.dropna(subset=["market_index_texas"])
    overall = (w["market_index_texas"] * w["state_employees"]).sum() / w["state_employees"].sum()
    tech = w[w["tech_role"]]
    tech_idx = (tech["market_index_texas"] * tech["state_employees"]).sum() / tech["state_employees"].sum()
    print(f"headcount-weighted market index: all {overall:.3f}, tech {tech_idx:.3f}")


if __name__ == "__main__":
    main()

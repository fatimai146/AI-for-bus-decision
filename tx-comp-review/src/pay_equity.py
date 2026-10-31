"""Adjusted pay-equity analysis (gender and ethnicity).

Log-salary regressions that add controls step by step, the way a pay-equity
consultant would: raw gap -> same job title -> same job title in the same
agency -> plus tenure. Standard errors are clustered by agency x job title.

Outputs
  pay_equity_models.csv     gap (%) for each group under each model
  pay_equity_by_agency.csv  fully adjusted gender gap for agencies with 300+
                            employees and 50+ of each gender
"""
import numpy as np
import pandas as pd

from common import OUT, connect, ensure_dirs
from stats import fe_ols, pct

GROUPS = {"female": "Women vs men", "eth_HISPANIC": "Hispanic vs White",
          "eth_BLACK": "Black vs White", "eth_ASIAN": "Asian vs White",
          "eth_OTHER": "Other vs White", "eth_AM INDIAN": "American Indian vs White"}
TENURE_TERMS = ["tenure", "tenure_sq"]


def load():
    con = connect()
    df = con.execute("""
        SELECT person_id, agency, agency_name, class_code, gender, ethnicity, annual, tenure
        FROM emp ORDER BY person_id""").df()
    con.close()
    df["log_pay"] = np.log(df["annual"])
    df["female"] = (df["gender"] == "FEMALE").astype(float)
    for e in ["HISPANIC", "BLACK", "ASIAN", "OTHER", "AM INDIAN"]:
        df[f"eth_{e}"] = (df["ethnicity"] == e).astype(float)
    df["tenure_sq"] = df["tenure"] ** 2
    df["cell"] = df["agency"] + "|" + df["class_code"]
    df["all"] = "all"
    return df


def main():
    ensure_dirs()
    df = load()
    xs = list(GROUPS)
    models = [
        ("1. Raw gap", xs, None, "cell"),
        ("2. Same job title", xs, "class_code", "cell"),
        ("3. Same job title, same agency", xs, "cell", "cell"),
        ("4. + tenure", xs + TENURE_TERMS, "cell", "cell"),
    ]
    rows = []
    for name, x, fe, cl in models:
        r = fe_ols(df, "log_pay", x, fe=fe, cluster=cl)
        for _, t in r[r["term"].isin(GROUPS)].iterrows():
            rows.append({"model": name, "group": GROUPS[t["term"]], "gap_pct": pct(t["coef"]),
                         "ci_low_pct": pct(t["ci_low"]), "ci_high_pct": pct(t["ci_high"])})
    res = pd.DataFrame(rows)
    res.to_csv(OUT / "pay_equity_models.csv", index=False)
    print(res.pivot(index="group", columns="model", values="gap_pct").round(2).to_string())

    ag_rows = []
    for (a, name), d in df.groupby(["agency", "agency_name"]):
        nf, nm = int(d["female"].sum()), int((1 - d["female"]).sum())
        if len(d) < 300 or nf < 50 or nm < 50:
            continue
        r = fe_ols(d, "log_pay", ["female"] + TENURE_TERMS, fe="cell")
        t = r.iloc[0]
        raw = d.loc[d["female"] == 1, "annual"].median() / d.loc[d["female"] == 0, "annual"].median() - 1
        ag_rows.append({
            "agency": a, "agency_name": name, "employees": len(d), "women": nf, "men": nm,
            "raw_median_gap_pct": raw * 100,
            "adjusted_gap_pct": pct(t["coef"]), "ci_low_pct": pct(t["ci_low"]), "ci_high_pct": pct(t["ci_high"]),
            "significant": (t["ci_low"] > 0) or (t["ci_high"] < 0),
        })
    ag = pd.DataFrame(ag_rows).sort_values("adjusted_gap_pct")
    ag.to_csv(OUT / "pay_equity_by_agency.csv", index=False)
    print(ag.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

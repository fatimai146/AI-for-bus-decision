"""Pay compression: how much more do long-tenured staff earn than new hires in the same job?

Outputs
  tenure_premium.csv          pay premium by tenure band vs new hires, within job+agency,
                              within job series+agency, and within entry-level titles only
  compression_titles.csv      statewide new-hire vs 10+ year median pay by job title
  compression_cells.csv       the same comparison inside each agency x job title
  compression_summary.csv     share of titles/cells/employees that are compressed or inverted
  compression_by_category.csv summary by occupational category
"""
import numpy as np
import pandas as pd

from common import MIN_CELL, NEW_HIRE_MAX_YEARS, OUT, TENURED_MIN_YEARS, connect, ensure_dirs
from stats import fe_ols, pct

BANDS = ["2-5", "5-10", "10-20", "20+"]
COMPRESSED = 0.95


def load():
    con = connect()
    df = con.execute("""
        SELECT person_id, agency, agency_name, class_code, class_title, series, level,
               occ_category, annual, tenure, tenure_band, range_min, range_max
        FROM emp ORDER BY person_id""").df()
    con.close()
    df["log_pay"] = np.log(df["annual"])
    df["cell"] = df["agency"] + "|" + df["class_code"]
    df["series_cell"] = df["agency"] + "|" + df["series"]
    for b in BANDS:
        df[f"band_{b}"] = (df["tenure_band"] == b).astype(float)
    series_levels = df.groupby("series")["level"].agg(["min", "nunique"])
    df = df.join(series_levels, on="series")
    df["entry_level"] = (df["level"] == df["min"]) & (df["nunique"] > 1)
    return df


def tenure_premium(df):
    xs = [f"band_{b}" for b in BANDS]
    specs = [
        ("same job title, same agency", df, "cell"),
        ("same job series (any level), same agency", df, "series_cell"),
        ("entry-level titles only, same agency", df[df["entry_level"]], "cell"),
    ]
    rows = []
    for name, d, fe in specs:
        r = fe_ols(d, "log_pay", xs, fe=fe)
        for _, t in r.iterrows():
            rows.append({
                "comparison": name, "tenure_band": t["term"].removeprefix("band_"),
                "premium_pct": pct(t["coef"]), "ci_low_pct": pct(t["ci_low"]),
                "ci_high_pct": pct(t["ci_high"]), "employees": len(d),
            })
    return pd.DataFrame(rows)


def new_vs_tenured(df, keys, min_each):
    new = df[df["tenure"] < NEW_HIRE_MAX_YEARS]
    ten = df[df["tenure"] >= TENURED_MIN_YEARS]
    a = new.groupby(keys)["annual"].agg(n_new="size", median_new="median")
    b = ten.groupby(keys)["annual"].agg(n_tenured="size", median_tenured="median")
    t = a.join(b, how="inner")
    t = t[(t["n_new"] >= min_each) & (t["n_tenured"] >= min_each)].copy()
    t["ratio_new_to_tenured"] = t["median_new"] / t["median_tenured"]
    t["compressed"] = t["ratio_new_to_tenured"] >= COMPRESSED
    t["inverted"] = t["ratio_new_to_tenured"] >= 1.0
    return t.reset_index()


def summarise(t, unit):
    emp = t["n_new"] + t["n_tenured"]
    return {
        "unit": unit, "groups_compared": len(t),
        "compressed_groups": int(t["compressed"].sum()), "inverted_groups": int(t["inverted"].sum()),
        "pct_compressed": t["compressed"].mean() * 100, "pct_inverted": t["inverted"].mean() * 100,
        "employees_compared": int(emp.sum()),
        "employees_in_compressed": int(emp[t["compressed"]].sum()),
        "employees_in_inverted": int(emp[t["inverted"]].sum()),
        "median_ratio": t["ratio_new_to_tenured"].median(),
    }


def main():
    ensure_dirs()
    df = load()

    prem = tenure_premium(df)
    prem.to_csv(OUT / "tenure_premium.csv", index=False)
    print(prem.round(2).to_string(index=False))

    titles = new_vs_tenured(df, ["class_code", "class_title", "occ_category"], 10)
    titles.sort_values("ratio_new_to_tenured", ascending=False).to_csv(
        OUT / "compression_titles.csv", index=False)

    cells = new_vs_tenured(df, ["agency", "agency_name", "class_code", "class_title", "occ_category"], MIN_CELL)
    cells.sort_values("ratio_new_to_tenured", ascending=False).to_csv(
        OUT / "compression_cells.csv", index=False)

    summary = pd.DataFrame([summarise(titles, "job title (statewide, 10+ in each group)"),
                            summarise(cells, f"agency x job title ({MIN_CELL}+ in each group)")])
    summary.to_csv(OUT / "compression_summary.csv", index=False)
    print(summary.round(3).to_string(index=False))

    cat = pd.DataFrame([dict(summarise(g, "agency x job title"), occ_category=c)
                        for c, g in cells.groupby("occ_category") if len(g) >= 5])
    cat = cat.sort_values("pct_compressed", ascending=False)
    cat.to_csv(OUT / "compression_by_category.csv", index=False)
    print(cat[["occ_category", "groups_compared", "pct_compressed", "pct_inverted"]].round(1).to_string(index=False))


if __name__ == "__main__":
    main()

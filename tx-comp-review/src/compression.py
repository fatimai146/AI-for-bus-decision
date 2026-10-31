"""Pay compression: how much more do long-tenured staff earn than new hires in the same job?

Outputs
  tenure_premium.csv        pay premium by tenure band vs new hires, within job+agency,
                            within job series+agency, and within entry-level titles only
  title_premium.csv         per job title: 10+ year vs new-hire (<2 yr) premium at the
                            same agency, with 95% CI and a classification
  title_premium_summary.csv count of titles in each classification
  inversion_null_check.csv  share of agency x title groups that look compressed/inverted on
                            raw medians, actual vs with tenure randomly shuffled
"""
import numpy as np
import pandas as pd

from common import MIN_CELL, NEW_HIRE_MAX_YEARS, OUT, TENURED_MIN_YEARS, connect, ensure_dirs
from stats import fe_ols, pct

BANDS = ["2-5", "5-10", "10-20", "20+"]
MIN_TITLE_GROUP = 20
SMALL_PREMIUM = 5.0
N_SHUFFLES = 200


def load():
    con = connect()
    df = con.execute("""
        SELECT person_id, agency, agency_name, class_code, class_title, series, level,
               occ_category, annual, tenure, tenure_band
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


def classify(r):
    if r["ci_high_pct"] < 0:
        return "new hires paid significantly more"
    if r["ci_low_pct"] <= 0:
        return "no significant difference"
    if r["premium_pct"] < SMALL_PREMIUM:
        return f"veterans paid more, but under {SMALL_PREMIUM:.0f}%"
    return f"veterans paid {SMALL_PREMIUM:.0f}%+ more"


def title_premium(df):
    """10+ year vs <2 year premium inside each job title, agency fixed effects, HC1 SEs."""
    d = df[(df["tenure"] < NEW_HIRE_MAX_YEARS) | (df["tenure"] >= TENURED_MIN_YEARS)].copy()
    d["tenured"] = (d["tenure"] >= TENURED_MIN_YEARS).astype(float)
    rows = []
    for (cc, title, cat), g in d.groupby(["class_code", "class_title", "occ_category"]):
        n_ten = int(g["tenured"].sum())
        n_new = len(g) - n_ten
        if n_new < MIN_TITLE_GROUP or n_ten < MIN_TITLE_GROUP:
            continue
        by = g.groupby("agency")
        y = g["log_pay"] - by["log_pay"].transform("mean")
        x = g["tenured"] - by["tenured"].transform("mean")
        sxx = (x ** 2).sum()
        if sxx == 0:
            continue
        b = (x * y).sum() / sxx
        e = y - b * x
        dof = len(g) - g["agency"].nunique() - 1
        if dof <= 0:
            continue
        se = np.sqrt((x ** 2 * e ** 2).sum() / sxx ** 2 * len(g) / dof)
        rows.append({
            "class_code": cc, "class_title": title, "occ_category": cat,
            "agencies": g["agency"].nunique(), "n_new": n_new, "n_tenured": n_ten,
            "median_new": g.loc[g["tenured"] == 0, "annual"].median(),
            "median_tenured": g.loc[g["tenured"] == 1, "annual"].median(),
            "premium_pct": pct(b), "ci_low_pct": pct(b - 1.96 * se), "ci_high_pct": pct(b + 1.96 * se),
        })
    t = pd.DataFrame(rows)
    t["result"] = t.apply(classify, axis=1)
    return t.sort_values("premium_pct")


def raw_inversion_shares(d):
    m = (d[d["grp"] != "mid"].groupby(["cell", "grp"])["annual"]
         .agg(["size", "median"]).unstack())
    m = m[(m[("size", "new")] >= MIN_CELL) & (m[("size", "ten")] >= MIN_CELL)]
    ratio = m[("median", "new")] / m[("median", "ten")]
    return (ratio >= 0.95).mean(), (ratio >= 1.0).mean(), len(ratio)


def inversion_null_check(df):
    """Raw median comparisons in small groups look 'inverted' often by chance alone.

    Shuffling tenure within each agency x title group removes any real tenure
    effect; the shuffled shares are the baseline the actual shares must beat.
    """
    d = df[["cell", "annual"]].copy()
    d["grp"] = np.select([df["tenure"] < NEW_HIRE_MAX_YEARS, df["tenure"] >= TENURED_MIN_YEARS],
                         ["new", "ten"], "mid")
    comp, inv, n = raw_inversion_shares(d)
    rng = np.random.default_rng(0)
    order = d.sort_values("cell", kind="stable").index
    cells = d.loc[order, "cell"].to_numpy()
    grp = d.loc[order, "grp"].to_numpy()
    bounds = np.flatnonzero(np.r_[True, cells[1:] != cells[:-1], True])
    sims = []
    for _ in range(N_SHUFFLES):
        g = grp.copy()
        for a, b in zip(bounds[:-1], bounds[1:]):
            g[a:b] = rng.permutation(g[a:b])
        s = d.loc[order].assign(grp=g)
        sims.append(raw_inversion_shares(s)[:2])
    sims = np.array(sims)
    return pd.DataFrame([
        {"measure": "share of groups compressed (new-hire median >= 95% of 10+ yr median)",
         "actual": comp, "if_tenure_had_no_effect": sims[:, 0].mean(), "groups": n},
        {"measure": "share of groups inverted (new-hire median >= 10+ yr median)",
         "actual": inv, "if_tenure_had_no_effect": sims[:, 1].mean(), "groups": n},
    ])


def main():
    ensure_dirs()
    df = load()

    prem = tenure_premium(df)
    prem.to_csv(OUT / "tenure_premium.csv", index=False)
    print(prem.round(2).to_string(index=False))

    titles = title_premium(df)
    titles.to_csv(OUT / "title_premium.csv", index=False)
    summary = titles["result"].value_counts().rename_axis("result").reset_index(name="titles")
    summary["share"] = summary["titles"] / len(titles)
    summary.to_csv(OUT / "title_premium_summary.csv", index=False)
    print(summary.round(3).to_string(index=False))
    print(f"median title premium: {titles['premium_pct'].median():.1f}%")
    print(titles[titles["result"].str.startswith("new hires")].round(1).to_string(index=False))

    null = inversion_null_check(df)
    null.to_csv(OUT / "inversion_null_check.csv", index=False)
    print(null.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

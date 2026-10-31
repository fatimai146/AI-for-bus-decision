"""Annual base-pay cost of two pay-floor policies for experienced staff.

These are policy costings, not estimates of an underpayment: some of the gap
below any median is ordinary pay dispersion.


1. Compression floor: in each agency x job title with 5+ new hires (<2 years),
   raise staff with 5+ years whose pay is below the new-hire median up to it.
2. Floor plus tenure step: raise staff with 2+ years to the new-hire median plus
   1% per year of service beyond 2 years (capped at +10%), so experience is paid
   above new-hire rates.

Raises never take anyone above their range maximum. Costs are base salary only
(no benefits load).

Outputs
  cost_to_fix.csv            one row per scenario
  cost_to_fix_by_agency.csv  scenario 1 and 2 cost by agency
"""
import numpy as np
import pandas as pd

from common import MIN_CELL, NEW_HIRE_MAX_YEARS, OUT, connect, ensure_dirs

FLOOR_MIN_TENURE = 5
STEP_PER_YEAR = 0.01
STEP_CAP = 0.10


def load():
    con = connect()
    df = con.execute("""
        SELECT person_id, agency, agency_name, class_code, class_title, occ_category,
               annual, tenure, range_min, range_max
        FROM emp ORDER BY person_id""").df()
    con.close()
    new = df[df["tenure"] < NEW_HIRE_MAX_YEARS].groupby(["agency", "class_code"])["annual"]
    ref = new.agg(n_new="size", new_median="median").reset_index()
    ref = ref[ref["n_new"] >= MIN_CELL]
    return df.merge(ref, on=["agency", "class_code"], how="left")


def raises(df, target, eligible):
    tgt = np.minimum(target, df["range_max"])
    r = np.where(eligible, np.maximum(tgt - df["annual"], 0), 0.0)
    return pd.Series(r, index=df.index)


def summarise(name, df, r):
    hit = r > 0
    return {
        "scenario": name, "employees_raised": int(hit.sum()),
        "pct_of_workforce": hit.mean() * 100,
        "annual_cost": r.sum(), "pct_of_payroll": r.sum() / df["annual"].sum() * 100,
        "median_raise": r[hit].median(), "median_raise_pct": (r[hit] / df.loc[hit, "annual"]).median() * 100,
    }


def main():
    ensure_dirs()
    df = load()
    has_ref = df["new_median"].notna()
    eligible = has_ref & (df["tenure"] >= FLOOR_MIN_TENURE)

    s1 = raises(df, df["new_median"], eligible)
    step = np.clip((df["tenure"] - NEW_HIRE_MAX_YEARS) * STEP_PER_YEAR, 0, STEP_CAP)
    s2 = raises(df, df["new_median"] * (1 + step), has_ref & (df["tenure"] >= NEW_HIRE_MAX_YEARS))

    out = pd.DataFrame([
        summarise("1. Compression floor (5+ yrs up to new-hire median)", df, s1),
        summarise("2. Floor + 1%/yr tenure step (cap 10%)", df, s2),
    ])
    out.to_csv(OUT / "cost_to_fix.csv", index=False)
    print(out.round(2).to_string(index=False))

    df["s1"], df["s2"] = s1, s2
    ag = df.groupby(["agency", "agency_name"]).agg(
        employees=("annual", "size"), payroll=("annual", "sum"),
        s1_employees=("s1", lambda x: int((x > 0).sum())), s1_cost=("s1", "sum"),
        s2_employees=("s2", lambda x: int((x > 0).sum())), s2_cost=("s2", "sum"),
    ).reset_index()
    ag["s1_pct_payroll"] = ag["s1_cost"] / ag["payroll"] * 100
    ag["s2_pct_payroll"] = ag["s2_cost"] / ag["payroll"] * 100
    ag = ag[ag["s1_employees"] >= MIN_CELL].sort_values("s1_cost", ascending=False)
    ag.to_csv(OUT / "cost_to_fix_by_agency.csv", index=False)
    print(ag.head(10).round(1).to_string(index=False))


if __name__ == "__main__":
    main()

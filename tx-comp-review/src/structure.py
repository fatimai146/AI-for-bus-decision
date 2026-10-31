"""Salary structure design review: range spread, midpoint progression, and
level-to-level overlap in the State's career ladders (e.g. Accountant I-VII).

Definitions
  range spread        = (max - min) / min
  midpoint step       = midpoint of next level / midpoint of this level - 1
  range overlap       = (max of lower level - min of higher level) / (max - min of lower level)
  pay overlap         = share of lower-level employees paid above the median of the next
                        level up at the same agency

Outputs
  structure_schedule.csv   one row per salary group
  structure_ladders.csv    one row per adjacent level pair in a career ladder
  structure_summary.csv    headline metrics against common design rules of thumb
"""
import pandas as pd

from common import MIN_CELL, OUT, connect, ensure_dirs

# Common rules of thumb for professional/exempt structures.
MIDPOINT_STEP_RANGE = (0.10, 0.15)
MAX_OVERLAP = 0.50


def schedule(con):
    t = con.execute("""
        SELECT schedule, salary_group, range_min, range_max, range_mid,
               (range_max - range_min) / range_min AS spread,
               range_mid / lag(range_mid) OVER (PARTITION BY schedule ORDER BY range_min) - 1 AS midpoint_step
        FROM ranges ORDER BY schedule, range_min""").df()
    return t


def ladders(con):
    lv = con.execute("""
        SELECT c.series, c.level, c.class_code, c.class_title_sao AS class_title, c.occ_category,
               c.salary_group, r.range_min, r.range_max, r.range_mid
        FROM classes c JOIN ranges r USING (salary_group)
        ORDER BY c.series, c.level""").df()
    lv["next_level"] = lv.groupby("series")["level"].shift(-1)
    nxt = lv.add_prefix("hi_").rename(columns={"hi_series": "series", "hi_level": "next_level"})
    pairs = lv.merge(nxt[["series", "next_level", "hi_class_code", "hi_class_title", "hi_salary_group",
                          "hi_range_min", "hi_range_max", "hi_range_mid"]],
                     on=["series", "next_level"])
    pairs = pairs[pairs["next_level"] == pairs["level"] + 1].copy()
    pairs["midpoint_step"] = pairs["hi_range_mid"] / pairs["range_mid"] - 1
    pairs["range_overlap"] = ((pairs["range_max"] - pairs["hi_range_min"])
                              / (pairs["range_max"] - pairs["range_min"])).clip(lower=0)
    pairs["same_group"] = pairs["salary_group"] == pairs["hi_salary_group"]
    return pairs


def pay_overlap(con, pairs):
    emp = con.execute("SELECT agency, class_code, annual FROM emp ORDER BY person_id").df()
    med = emp.groupby(["agency", "class_code"])["annual"].agg(n="size", median="median").reset_index()
    rows = []
    for _, p in pairs.iterrows():
        lo = emp[emp["class_code"] == p["class_code"]]
        hi = med[(med["class_code"] == p["hi_class_code"]) & (med["n"] >= MIN_CELL)]
        both = lo.merge(hi[["agency", "median"]], on="agency")
        n_hi = int(hi["n"].sum())
        rows.append({
            "n_lower_matched": len(both), "n_upper": n_hi,
            "pay_overlap": (both["annual"] > both["median"]).mean() if len(both) >= MIN_CELL else None,
        })
    return pd.concat([pairs.reset_index(drop=True), pd.DataFrame(rows)], axis=1)


def main():
    ensure_dirs()
    con = connect()
    sched = schedule(con)
    sched.to_csv(OUT / "structure_schedule.csv", index=False)

    pairs = pay_overlap(con, ladders(con))
    con.close()
    cols = ["series", "occ_category", "level", "class_title", "salary_group", "hi_class_title",
            "hi_salary_group", "midpoint_step", "range_overlap", "same_group",
            "n_lower_matched", "n_upper", "pay_overlap"]
    pairs[cols].to_csv(OUT / "structure_ladders.csv", index=False)

    lo, hi = MIDPOINT_STEP_RANGE
    occupied = pairs[pairs["pay_overlap"].notna()]
    w = occupied["n_lower_matched"]
    summary = pd.DataFrame([
        ("Salary groups (Schedules A and B)", len(sched), ""),
        ("Median range spread, Schedule B", sched.loc[sched["schedule"] == "B", "spread"].median(), "pct"),
        ("Median midpoint step between adjacent groups, Schedule B",
         sched.loc[sched["schedule"] == "B", "midpoint_step"].median(), "pct"),
        ("Career ladders (job series with 2+ levels)", pairs["series"].nunique(), ""),
        ("Adjacent level pairs", len(pairs), ""),
        ("Median midpoint step between levels", pairs["midpoint_step"].median(), "pct"),
        (f"Level pairs with midpoint step below {lo:.0%}", (pairs["midpoint_step"] < lo).mean(), "pct"),
        (f"Level pairs with midpoint step {lo:.0%}-{hi:.0%}",
         pairs["midpoint_step"].between(lo, hi).mean(), "pct"),
        ("Level pairs in the same salary group (no pay step)", pairs["same_group"].mean(), "pct"),
        ("Median range overlap between levels", pairs["range_overlap"].median(), "pct"),
        (f"Level pairs with range overlap above {MAX_OVERLAP:.0%}", (pairs["range_overlap"] > MAX_OVERLAP).mean(), "pct"),
        ("Level pairs with staff at both levels in the same agency", len(occupied), ""),
        ("Lower-level staff paid above the next level's median (same agency)",
         (occupied["pay_overlap"] * w).sum() / w.sum(), "pct"),
    ], columns=["metric", "value", "unit"])
    summary.to_csv(OUT / "structure_summary.csv", index=False)
    print(summary.to_string(index=False))

    big = occupied[(occupied["n_lower_matched"] >= 50) & (occupied["n_upper"] >= 50)]
    print(big.sort_values("pay_overlap", ascending=False)[
        ["class_title", "hi_class_title", "midpoint_step", "range_overlap", "n_lower_matched",
         "pay_overlap"]].head(12).round(3).to_string(index=False))


if __name__ == "__main__":
    main()

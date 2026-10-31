"""Aggregated extract for Tableau Public (no individual-level rows).

One row per agency x job title x tenure band x gender, with groups smaller than
MIN_CELL suppressed.
"""
from common import MIN_CELL, OUT, connect, ensure_dirs


def main():
    ensure_dirs()
    con = connect()
    t = con.execute(f"""
        SELECT agency_name AS "Agency", occ_category AS "Occupational Category",
               series AS "Job Series", class_title AS "Job Title", salary_group AS "Salary Group",
               tenure_band AS "Tenure Band", gender AS "Gender",
               count(*) AS "Employees",
               round(median(annual), 0) AS "Median Salary",
               round(avg(annual), 0) AS "Mean Salary",
               any_value(range_min) AS "Range Min", any_value(range_max) AS "Range Max",
               round(median(penetration), 3) AS "Median Range Penetration",
               round(median(compa_ratio), 3) AS "Median Compa-Ratio"
        FROM emp GROUP BY ALL HAVING count(*) >= {MIN_CELL}
        ORDER BY 1, 4, min(tenure), 7""").df()
    t.to_csv(OUT / "tableau_extract.csv", index=False)
    con.close()
    print(f"tableau_extract.csv: {len(t):,} rows covering {t['Employees'].sum():,} employees")


if __name__ == "__main__":
    main()

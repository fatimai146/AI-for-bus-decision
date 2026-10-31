"""Build data/txcomp.duckdb from the raw payroll, job-class list and salary schedule."""
import re

import pandas as pd

from common import DB, PAYROLL_CSV, SAO_HTML, SCHEDULE_HTML, SNAPSHOT_DATE, connect

ROMAN = {r: i for i, r in enumerate(
    ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"], start=1)}
SERIES_RE = re.compile(r"^(.*?)\s+(" + "|".join(sorted(ROMAN, key=len, reverse=True)) + r")$")


def norm_group(g):
    """'A09' and 'A9' name the same pay group; normalise to 'A9'."""
    return re.sub(r"^([A-Z])0*(\d+)$", r"\1\2", str(g).strip())


def job_classes():
    t = pd.read_html(SAO_HTML)[0].iloc[:, :4]
    t.columns = ["class_code", "class_title_sao", "salary_group_raw", "occ_category"]
    t["class_code"] = t["class_code"].astype(str).str.strip().str.lstrip("0")
    t["class_title_sao"] = t["class_title_sao"].str.strip()
    t["salary_group"] = t["salary_group_raw"].map(norm_group)
    parts = t["class_title_sao"].str.extract(SERIES_RE)
    t["series"] = parts[0].fillna(t["class_title_sao"])
    t["level"] = parts[1].map(ROMAN).fillna(1).astype(int)
    return t


def salary_ranges():
    rows = []
    for sched, tbl in zip("AB", pd.read_html(SCHEDULE_HTML)[:2]):
        tbl = tbl.iloc[:, :4]
        tbl.columns = ["salary_group", "period", "range_min", "range_max"]
        tbl = tbl[tbl["period"] == "Annual"].copy()
        tbl["schedule"] = sched
        rows.append(tbl)
    r = pd.concat(rows)
    r["salary_group"] = r["salary_group"].map(norm_group)
    r["range_min"] = r["range_min"].astype(float)
    r["range_max"] = r["range_max"].astype(float)
    r["range_mid"] = (r["range_min"] + r["range_max"]) / 2
    return r[["salary_group", "schedule", "range_min", "range_max", "range_mid"]]


def main():
    DB.unlink(missing_ok=True)
    con = connect(read_only=False)
    con.execute(f"""
        CREATE TABLE payroll AS
        SELECT trim(AGENCY) AS agency,
               trim("AGENCY NAME") AS agency_name,
               ltrim(trim("CLASS CODE"), '0') AS class_code,
               trim("CLASS TITLE") AS class_title,
               trim(ETHNICITY) AS ethnicity,
               trim(GENDER) AS gender,
               trim("EMPLOYEE TYPE") AS employee_type,
               left(trim("EMPLOYEE TYPE"), 3) AS emp_code,
               "HIRE DATE"::DATE AS hire_date,
               HRSWKD::DOUBLE AS hours,
               ANNUAL::DOUBLE AS annual,
               STATENUM AS person_id,
               coalesce(duplicated = 'True', false) AS duplicated,
               coalesce(multiple_full_time_jobs = 'True', false) AS multi_ft
        FROM read_csv('{PAYROLL_CSV}', all_varchar = true, header = true)
        ORDER BY person_id, agency, class_code
    """)
    con.register("classes_df", job_classes())
    con.execute("CREATE TABLE classes AS SELECT * FROM classes_df")
    con.register("ranges_df", salary_ranges())
    con.execute("CREATE TABLE ranges AS SELECT * FROM ranges_df")

    # Analysis population: regular full-time classified staff on Schedule A or B,
    # one job per person, valid hire date.
    con.execute(f"""
        CREATE TABLE emp AS
        SELECT p.*, c.series, c.level, c.occ_category, c.salary_group,
               r.schedule, r.range_min, r.range_max, r.range_mid,
               date_diff('day', p.hire_date, DATE '{SNAPSHOT_DATE}') / 365.25 AS tenure,
               CASE WHEN tenure < 2 THEN '0-2'
                    WHEN tenure < 5 THEN '2-5'
                    WHEN tenure < 10 THEN '5-10'
                    WHEN tenure < 20 THEN '10-20'
                    ELSE '20+' END AS tenure_band,
               (p.annual - r.range_min) / (r.range_max - r.range_min) AS penetration,
               p.annual / r.range_mid AS compa_ratio
        FROM payroll p
        JOIN classes c USING (class_code)
        JOIN ranges r USING (salary_group)
        WHERE p.emp_code = 'CRF'
          AND NOT p.duplicated
          AND p.hours = 40
          AND p.hire_date <= DATE '{SNAPSHOT_DATE}'
        ORDER BY p.person_id
    """)
    for t in ["payroll", "classes", "ranges", "emp"]:
        n = con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
        print(f"{t:10s} {n:>8,d}")
    con.close()


if __name__ == "__main__":
    main()

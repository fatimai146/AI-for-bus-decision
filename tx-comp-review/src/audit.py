"""Data-quality audit of the payroll file and the analysis population."""
from common import SNAPSHOT_DATE, connect


def section(con, title, sql):
    print(f"\n== {title} ==")
    print(con.execute(sql).df().to_string(index=False))


def main():
    con = connect()
    section(con, "Raw file", """
        SELECT count(*) AS rows, count(DISTINCT person_id) AS people,
               count(DISTINCT agency) AS agencies, count(DISTINCT class_code) AS job_classes,
               sum(duplicated::INT) AS rows_flagged_multi_job
        FROM payroll""")
    section(con, "Employee types", """
        SELECT employee_type, count(*) AS n FROM payroll GROUP BY 1 ORDER BY 2 DESC""")
    section(con, "Missing values (raw file)", """
        SELECT sum((gender IS NULL)::INT) AS gender, sum((ethnicity IS NULL)::INT) AS ethnicity,
               sum((hire_date IS NULL)::INT) AS hire_date, sum((annual IS NULL)::INT) AS annual
        FROM payroll""")
    section(con, f"Hire dates after the {SNAPSHOT_DATE} snapshot (excluded)", f"""
        SELECT hire_date, count(*) AS n FROM payroll
        WHERE hire_date > DATE '{SNAPSHOT_DATE}' GROUP BY 1 ORDER BY 1""")
    section(con, "Regular full-time classified staff: job class -> pay schedule", """
        SELECT CASE WHEN c.class_code IS NULL THEN 'no job class match'
                    WHEN r.schedule IS NULL THEN 'Schedule C (step pay, excluded)'
                    ELSE 'Schedule ' || r.schedule END AS mapping,
               count(*) AS n
        FROM payroll p LEFT JOIN classes c USING (class_code)
        LEFT JOIN ranges r USING (salary_group)
        WHERE p.emp_code = 'CRF' GROUP BY 1 ORDER BY 2 DESC""")
    section(con, "Analysis population", """
        SELECT count(*) AS employees, count(DISTINCT agency) AS agencies,
               count(DISTINCT class_code) AS job_classes,
               median(annual) AS median_salary, min(annual) AS min_salary, max(annual) AS max_salary
        FROM emp""")
    section(con, "Salary vs official range", """
        SELECT sum((annual < range_min)::INT) AS below_min,
               median(range_min - annual) FILTER (WHERE annual < range_min) AS median_shortfall,
               sum((annual < range_min - 1)::INT) AS below_min_by_over_1_dollar,
               sum((annual > range_max)::INT) AS above_max
        FROM emp""")
    section(con, "Tenure bands", """
        SELECT tenure_band, count(*) AS n, round(median(tenure), 1) AS median_years
        FROM emp GROUP BY 1 ORDER BY min(tenure)""")
    section(con, "Gender and ethnicity", """
        SELECT gender, ethnicity, count(*) AS n FROM emp GROUP BY ALL ORDER BY 1, 3 DESC""")
    con.close()


if __name__ == "__main__":
    main()

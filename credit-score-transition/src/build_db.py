"""Load sample origination/performance files and historical score files into DuckDB.

Produces data/sflld.duckdb with:
  orig        one row per sampled loan (2018-2026 vintages)
  perf_loan   one row per loan: performance outcomes summarised from the monthly file
  scores      FICO 10T and VantageScore 4.0 historical scores for sampled loans
"""
import pathlib
import duckdb
from schema import ORIG_COLS, PERF_COLS, SCORE_COLS_SUFFIX

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXT = ROOT / "data" / "extract"
DB = ROOT / "data" / "sflld.duckdb"


def cols_spec(names):
    return "{" + ", ".join(f"'{c}': 'VARCHAR'" for c in names) + "}"


def main():
    DB.unlink(missing_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("SET preserve_insertion_order=false")

    con.execute(f"""
        CREATE TABLE orig_raw AS
        SELECT * FROM read_csv('{EXT}/sample_orig_*.txt', delim='|', header=false,
                               columns={cols_spec(ORIG_COLS)}, filename=true)
    """)
    con.execute("""
        CREATE TABLE orig AS
        SELECT
            loan_id,
            CAST(regexp_extract(filename, 'sample_orig_(\\d{4})', 1) AS INT) AS vintage,
            '20' || substr(loan_id, 2, 2) || 'Q' || substr(loan_id, 5, 1) AS orig_quarter,
            NULLIF(TRY_CAST(fico AS INT), 9999) AS fico,
            NULLIF(TRY_CAST(vs4_orig AS INT), 9999) AS vs4_orig,
            TRY_CAST(first_pay_date AS INT) AS first_pay_date,
            first_time_buyer, occupancy, channel, amort_type, state, property_type,
            loan_purpose, seller_name, special_eligibility, valuation_method,
            NULLIF(TRY_CAST(ltv AS INT), 999) AS ltv,
            NULLIF(TRY_CAST(cltv AS INT), 999) AS cltv,
            NULLIF(TRY_CAST(dti AS INT), 999) AS dti,
            NULLIF(TRY_CAST(mi_pct AS INT), 999) AS mi_pct,
            TRY_CAST(orig_upb AS DOUBLE) AS orig_upb,
            TRY_CAST(orig_rate AS DOUBLE) AS orig_rate,
            TRY_CAST(orig_term AS INT) AS orig_term,
            NULLIF(TRY_CAST(num_borrowers AS INT), 99) AS num_borrowers,
            NULLIF(TRY_CAST(units AS INT), 99) AS units
        FROM orig_raw
    """)
    con.execute("DROP TABLE orig_raw")

    con.execute(f"""
        CREATE TABLE perf_loan AS
        WITH p AS (
            SELECT loan_id,
                   TRY_CAST(period AS INT) AS period,
                   TRY_CAST(loan_age AS INT) AS loan_age,
                   dlq_status,
                   CASE WHEN dlq_status = 'RA' THEN 99 ELSE TRY_CAST(dlq_status AS INT) END AS dlq,
                   zero_bal_code, TRY_CAST(zero_bal_date AS INT) AS zero_bal_date,
                   assistance_plan, disaster_dlq, payment_deferral, mod_flag,
                   TRY_CAST(actual_loss AS DOUBLE) AS actual_loss,
                   TRY_CAST(zb_removal_upb AS DOUBLE) AS zb_removal_upb
            FROM read_csv('{EXT}/sample_perf_*.txt', delim='|', header=false,
                          columns={cols_spec(PERF_COLS)}, null_padding=true)
        )
        SELECT loan_id,
               COUNT(*) AS n_months,
               MIN(period) AS first_period,
               MAX(period) AS last_period,
               MAX(loan_age) AS max_age,
               MAX(dlq) AS worst_dlq,
               MIN(CASE WHEN dlq >= 3 OR zero_bal_code IN ('02','03','09','15') THEN loan_age END) AS age_first_d90,
               MIN(CASE WHEN dlq >= 3 OR zero_bal_code IN ('02','03','09','15') THEN period END) AS period_first_d90,
               MIN(CASE WHEN dlq >= 2 THEN loan_age END) AS age_first_d60,
               MAX(zero_bal_code) AS zero_bal_code,
               MAX(zero_bal_date) AS zero_bal_date,
               MAX(CASE WHEN assistance_plan = 'F' THEN 1 ELSE 0 END) AS ever_forbearance,
               MAX(CASE WHEN disaster_dlq = 'Y' THEN 1 ELSE 0 END) AS ever_disaster,
               MAX(CASE WHEN payment_deferral IN ('C','P') THEN 1 ELSE 0 END) AS ever_deferral,
               MAX(CASE WHEN mod_flag IN ('Y','P') THEN 1 ELSE 0 END) AS ever_modified,
               SUM(actual_loss) AS actual_loss,
               MAX(zb_removal_upb) AS zb_removal_upb
        FROM p
        GROUP BY loan_id
    """)

    for prefix, files in [
        ("fico10t", ["FRE_FICO10T_SFLLD_Historical.txt"]),
        ("vs4", ["FRE_VS4_SFLLD_Historical.txt", "FRE_VS4_2023-Q32025_SFLLD_Historical.txt"]),
    ]:
        names = ["orig_quarter", "loan_id"] + [f"{prefix}_{s}" for s in SCORE_COLS_SUFFIX]
        casts = ", ".join(
            f"NULLIF(TRY_CAST({n} AS INT), 9999) AS {n}" for n in names[2:]
        )
        # Files differ in line endings; a multi-file read_csv silently drops the second file.
        union = " UNION ALL ".join(
            f"SELECT * FROM read_csv('{EXT}/{f}', delim='|', header=true, columns={cols_spec(names)})"
            for f in files
        )
        con.execute(f"""
            CREATE TABLE {prefix}_scores AS
            SELECT s.loan_id, {casts}
            FROM ({union}) s
            SEMI JOIN orig o ON o.loan_id = s.loan_id
        """)

    con.execute("""
        CREATE TABLE scores AS
        SELECT o.loan_id, f.* EXCLUDE (loan_id), v.* EXCLUDE (loan_id)
        FROM orig o
        LEFT JOIN fico10t_scores f USING (loan_id)
        LEFT JOIN vs4_scores v USING (loan_id)
    """)
    for t in ["orig", "perf_loan", "fico10t_scores", "vs4_scores", "scores"]:
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t:16s} {n:>10,}")
    con.close()


if __name__ == "__main__":
    main()

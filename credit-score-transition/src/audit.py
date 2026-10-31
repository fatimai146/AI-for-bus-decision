"""Data quality / realism audit of the joined SFLLD + historical score data."""
import pathlib
import duckdb
import pandas as pd

pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)
DB = pathlib.Path(__file__).resolve().parents[1] / "data" / "sflld.duckdb"
con = duckdb.connect(str(DB), read_only=True)


def q(title, sql):
    print(f"\n=== {title} ===")
    print(con.execute(sql).df().to_string(index=False))


q("Duplicate loan ids", """
    SELECT 'orig' t, COUNT(*) - COUNT(DISTINCT loan_id) dups FROM orig
    UNION ALL SELECT 'fico10t', COUNT(*) - COUNT(DISTINCT loan_id) FROM fico10t_scores
    UNION ALL SELECT 'vs4', COUNT(*) - COUNT(DISTINCT loan_id) FROM vs4_scores""")

q("Coverage by vintage (% of sampled loans with each score)", """
    SELECT vintage, COUNT(*) n,
      ROUND(100*AVG(COALESCE(fico IS NOT NULL, false)::INT),1) classic_fico,
      ROUND(100*AVG(COALESCE(vs4_orig IS NOT NULL, false)::INT),1) vs4_in_orig_file,
      ROUND(100*AVG(COALESCE(fico10t_current_method IS NOT NULL, false)::INT),1) fico10t,
      ROUND(100*AVG(COALESCE(vs4_current_method IS NOT NULL, false)::INT),1) vs4_hist,
      ROUND(100*AVG((fico IS NOT NULL AND fico10t_current_method IS NOT NULL
                     AND vs4_current_method IS NOT NULL)::INT),1) all_three
    FROM orig JOIN scores USING (loan_id) GROUP BY 1 ORDER BY 1""")

q("Score summary", """
    WITH u AS (UNPIVOT (SELECT fico, fico10t_current_method, vs4_current_method
                        FROM orig JOIN scores USING (loan_id))
               ON fico, fico10t_current_method, vs4_current_method INTO NAME score VALUE v)
    SELECT score, COUNT(v) n, MIN(v) mn, quantile_cont(v,0.05) p05, quantile_cont(v,0.5) p50,
           ROUND(AVG(v),1) mean, quantile_cont(v,0.95) p95, MAX(v) mx
    FROM u GROUP BY 1""")

q("Correlations (loans with all three)", """
    SELECT ROUND(corr(fico, fico10t_current_method),3) fico_vs_10t,
           ROUND(corr(fico, vs4_current_method),3) fico_vs_vs4,
           ROUND(corr(fico10t_current_method, vs4_current_method),3) t10_vs_vs4,
           ROUND(AVG(abs(fico - fico10t_current_method)),1) mad_fico_10t,
           ROUND(AVG(abs(fico - vs4_current_method)),1) mad_fico_vs4,
           ROUND(100*AVG(COALESCE(abs(fico - vs4_current_method) > 40, false)::INT),1) pct_gap40_vs4
    FROM orig JOIN scores USING (loan_id)
    WHERE fico IS NOT NULL AND fico10t_current_method IS NOT NULL AND vs4_current_method IS NOT NULL""")

q("VS4 in orig file vs historical file (where both present)", """
    SELECT COUNT(*) n, ROUND(AVG(COALESCE(vs4_orig = vs4_current_method, false)::INT)*100,1) pct_equal,
           ROUND(corr(vs4_orig, vs4_current_method),3) r
    FROM orig JOIN scores USING (loan_id)
    WHERE vs4_orig IS NOT NULL AND vs4_current_method IS NOT NULL""")

q("Merge-method internal consistency (lowest <= median <= highest)", """
    SELECT ROUND(100*AVG(COALESCE(fico10t_bi_lowest <= fico10t_bi_median AND fico10t_bi_median <= fico10t_bi_highest, false)::INT),2) fico10t_ok,
           ROUND(100*AVG(COALESCE(vs4_bi_lowest <= vs4_bi_median AND vs4_bi_median <= vs4_bi_highest, false)::INT),2) vs4_ok
    FROM scores WHERE fico10t_bi_lowest IS NOT NULL OR vs4_bi_lowest IS NOT NULL""")

q("Loan attributes sanity", """
    SELECT vintage, ROUND(AVG(orig_rate),2) avg_rate, ROUND(AVG(ltv),1) avg_ltv,
           ROUND(AVG(dti),1) avg_dti, ROUND(AVG(orig_upb)/1000,0) avg_upb_k,
           ROUND(100*AVG(COALESCE(loan_purpose='P', false)::INT),1) pct_purchase
    FROM orig GROUP BY 1 ORDER BY 1""")

q("Outcomes by vintage", """
    SELECT vintage, COUNT(*) n, ROUND(AVG(max_age),1) avg_months_obs,
      ROUND(100*AVG(COALESCE(zero_bal_code='01', false)::INT),1) pct_prepaid,
      ROUND(100*AVG(COALESCE(age_first_d90 IS NOT NULL, false)::INT),2) pct_ever_d90,
      ROUND(100*AVG(COALESCE(age_first_d90 <= 24, false)::INT),2) pct_d90_24m,
      ROUND(100*AVG(ever_forbearance),1) pct_forbearance,
      ROUND(100*AVG(COALESCE(zero_bal_code IN ('02','03','09','15'), false)::INT),2) pct_credit_loss_event
    FROM orig JOIN perf_loan USING (loan_id) GROUP BY 1 ORDER BY 1""")

q("Default rate (ever 90+ within 24m) by Classic FICO band, 2018-2023 vintages", """
    SELECT CASE WHEN fico < 660 THEN 'a <660' WHEN fico < 700 THEN 'b 660-699'
                WHEN fico < 740 THEN 'c 700-739' WHEN fico < 780 THEN 'd 740-779' ELSE 'e 780+' END band,
           COUNT(*) n, ROUND(100*AVG(COALESCE(age_first_d90 <= 24, false)::INT),2) d90_24m
    FROM orig JOIN perf_loan USING (loan_id)
    WHERE vintage BETWEEN 2018 AND 2023 AND fico IS NOT NULL GROUP BY 1 ORDER BY 1""")

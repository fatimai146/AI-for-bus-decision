"""Shared paths, score definitions and cohort loading."""
import pathlib
import duckdb
import numpy as np
from sklearn.metrics import roc_auc_score

ROOT = pathlib.Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "sflld.duckdb"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
OUT.mkdir(exist_ok=True)
FIG.mkdir(exist_ok=True)

SCORES = {
    "Classic FICO": "fico",
    "FICO 10T": "fico10t_current_method",
    "VantageScore 4.0": "vs4_current_method",
    "FICO 10T (tri-merge avg)": "fico10t_trimerge",
    "VS4 (tri-merge avg)": "vs4_trimerge",
    "FICO 10T (bi-merge lowest)": "fico10t_bi_lowest",
    "VS4 (bi-merge lowest)": "vs4_bi_lowest",
}
HEAD = ["Classic FICO", "FICO 10T", "VantageScore 4.0"]
COLORS = {"Classic FICO": "#7f7f7f", "FICO 10T": "#1f4e9c", "VantageScore 4.0": "#2a9d8f"}

DEFAULT_WINDOW_MONTHS = 24
HEADLINE_VINTAGES = (2021, 2023)
COVID_VINTAGES = (2018, 2020)


def load_cohort(first_vintage, last_vintage):
    """Loans in the vintage range with all scores present and a 24-month default flag."""
    con = duckdb.connect(str(DB), read_only=True)
    df = con.execute(f"""
        SELECT o.*, s.* EXCLUDE (loan_id),
               COALESCE(p.age_first_d90 <= {DEFAULT_WINDOW_MONTHS}, false)::INT AS bad,
               p.age_first_d90, p.ever_forbearance, p.actual_loss, p.zb_removal_upb
        FROM orig o JOIN scores s USING (loan_id) JOIN perf_loan p USING (loan_id)
        WHERE o.vintage BETWEEN {first_vintage} AND {last_vintage}
        ORDER BY o.loan_id
    """).df()
    con.close()
    return df.dropna(subset=list(SCORES.values())).reset_index(drop=True)


def gini(y, score):
    """Gini of a score where higher score means lower risk."""
    return 2 * roc_auc_score(y, -np.asarray(score)) - 1


def decline_mask(score, rate, seed=0):
    """Decline exactly `rate` of loans with the lowest scores (random tie-break)."""
    score = np.asarray(score, dtype=float)
    jitter = np.random.default_rng(seed).random(len(score)) * 1e-3
    order = np.argsort(score + jitter)
    mask = np.zeros(len(score), dtype=bool)
    mask[order[: int(round(rate * len(score)))]] = True
    return mask

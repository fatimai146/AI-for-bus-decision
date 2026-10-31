"""Checks on the AI grading results.

1. Review list: jobs where the AI grade differs from the official grade by 3+ salary groups.
2. External validation: does "AI says graded too low" line up with the State Auditor's
   October 2026 recommendations to move jobs to a higher salary group (report 27-701)?
3. Gender check: are female-dominated jobs graded lower than their descriptions predict?

Outputs
  grading_review_list.csv
  grading_vs_sao_reallocations.csv
  grading_gender_check.csv
"""
import re

import duckdb
import numpy as np
import pandas as pd
from pypdf import PdfReader

from common import OUT, PAYROLL, SAO_REPORT, ensure_dirs

REVIEW_GROUPS = 3
MIN_EMPLOYEES = 20


def sao_reallocations():
    text = "\n".join((p.extract_text() or "") for p in PdfReader(SAO_REPORT).pages)
    codes = set()
    for line in text.splitlines():
        if "Reallocation" in line:
            codes.update(c.lstrip("0") for c in re.findall(r"\b(\d{4})\s+[AB]\d{2}\b", line))
    return codes


def headcount_and_gender():
    return duckdb.sql(f"""
        SELECT ltrim(trim("CLASS CODE"), '0') AS class_code, count(*) AS employees,
               avg((trim(GENDER) = 'FEMALE')::INT) AS female_share
        FROM read_csv('{PAYROLL}', all_varchar = true)
        WHERE "EMPLOYEE TYPE" LIKE 'CRF%' GROUP BY 1""").df()


def auc(score, label):
    """Probability a random positive scores above a random negative."""
    pos, neg = score[label], score[~label]
    ranks = pd.Series(np.r_[pos, neg]).rank().to_numpy()
    return (ranks[:len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg))


def female_slope(df, fe=None, weight=None):
    """Weighted OLS of official-vs-AI gap on female share; SEs clustered by job family,
    because levels of one family share a description."""
    X = df[["female_share"]].assign(const=1.0)
    if fe:
        X = pd.concat([df[["female_share"]], pd.get_dummies(df[fe], dtype=float)], axis=1)
    X = X.to_numpy(float)
    y = df["official_vs_ai_pct"].to_numpy()
    w = np.ones(len(y)) if weight is None else df[weight].to_numpy(float)
    inv = np.linalg.pinv(X.T @ (X * w[:, None]))
    b = inv @ X.T @ (w * y)
    e = y - X @ b
    codes = pd.factorize(df["pdf"])[0]
    s = np.zeros((codes.max() + 1, X.shape[1]))
    np.add.at(s, codes, X * (w * e)[:, None])
    se = np.sqrt((inv @ (s.T @ s) @ inv)[0, 0])
    return b[0], se


def main():
    ensure_dirs()
    p = pd.read_csv(OUT / "grading_predictions.csv", dtype={"class_code": str, "pdf": str})
    p = p.merge(headcount_and_gender(), on="class_code", how="left")
    p["employees"] = p["employees"].fillna(0).astype(int)

    review = p[p["ai_vs_official_groups"].abs() >= REVIEW_GROUPS].copy()
    review["direction"] = np.where(review["ai_vs_official_groups"] > 0,
                                   "AI grades higher (possible under-grading)",
                                   "AI grades lower (possible over-grading)")
    review = review.sort_values("ai_vs_official_groups", ascending=False)
    review[["class_code", "class_title", "occ_category", "salary_group", "range_mid", "predicted_mid",
            "ai_vs_official_groups", "ai_vs_official_pct", "employees", "direction"]].to_csv(
        OUT / "grading_review_list.csv", index=False)
    print(f"review list: {len(review)} of {len(p)} jobs differ by {REVIEW_GROUPS}+ groups")
    print(review["direction"].value_counts().to_string())

    realloc = sao_reallocations()
    p["sao_reallocation"] = p["class_code"].isin(realloc)
    lab = p["sao_reallocation"].to_numpy()
    score = p["ai_vs_official_pct"].to_numpy()
    sao = pd.DataFrame([{
        "sao_recommended_reallocations_matched": int(lab.sum()),
        "jobs_not_recommended": int((~lab).sum()),
        "mean_ai_vs_official_pct_recommended": score[lab].mean(),
        "mean_ai_vs_official_pct_others": score[~lab].mean(),
        "auc_ai_gap_predicts_reallocation": auc(score, lab),
        "share_recommended_where_ai_higher": (score[lab] > 0).mean(),
        "share_others_where_ai_higher": (score[~lab] > 0).mean(),
    }])
    sao.to_csv(OUT / "grading_vs_sao_reallocations.csv", index=False)
    print(sao.round(3).T.to_string(header=False))

    # official vs AI, in log points x 100: negative = official grade below what the description predicts
    g = p[p["employees"] >= MIN_EMPLOYEES].copy()
    g["official_vs_ai_pct"] = -np.log1p(g["ai_vs_official_pct"] / 100) * 100
    specs = [
        ("Jobs with 20+ employees", g, None, None),
        ("+ occupational category fixed effects", g, "occ_category", None),
        ("Weighted by headcount", g, None, "employees"),
        ("Jobs with 100+ employees", g[g["employees"] >= 100], None, None),
    ]
    rows = []
    for name, d, fe, w in specs:
        b, se = female_slope(d, fe, w)
        rows.append({"specification": name, "jobs": len(d),
                     "gap_all_female_vs_all_male_pct": b, "ci_low": b - 1.96 * se, "ci_high": b + 1.96 * se,
                     "significant": abs(b) > 1.96 * se})
    chk = pd.DataFrame(rows)
    chk.to_csv(OUT / "grading_gender_check.csv", index=False)
    print(chk.round(2).to_string(index=False))


if __name__ == "__main__":
    main()

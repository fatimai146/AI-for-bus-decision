"""AI-assisted job evaluation: predict a job's pay grade from its job description.

Every prediction is out-of-fold, with folds grouped by job family (one State
Auditor job description document), so the model always grades job families it
has never seen, the way it would grade a new job.

Outputs
  grading_metrics.csv     accuracy of each model and ablation
  grading_predictions.csv out-of-fold predictions per job class
  grading_routing.csv     accuracy when only confident predictions are auto-accepted
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline
from sklearn.svm import SVR

from common import INTERIM, OUT, SEED, ensure_dirs
from parse_jobs import salary_ranges

ALPHAS = np.logspace(-2, 3, 16)
ROUTE_SHARES = [1.0, 0.8, 0.6, 0.4]


def load():
    jobs = pd.read_parquet(INTERIM / "jobs.parquet")
    fam = np.load(INTERIM / "emb_family.npy")
    lvl = np.load(INTERIM / "emb_level.npy")
    keep = jobs["schedule"].notna().to_numpy()
    jobs = jobs[keep].reset_index(drop=True)
    return jobs, fam[keep], lvl[keep]


def oof(model_fn, X, y, groups):
    pred = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5, shuffle=True, random_state=SEED).split(X, y, groups):
        m = model_fn()
        m.fit(X[tr] if not isinstance(X, pd.Series) else X.iloc[tr], y[tr])
        pred[te] = m.predict(X[te] if not isinstance(X, pd.Series) else X.iloc[te])
    return pred


def neighbor_spread(fam, y, groups, k=10):
    """Confidence signal: spread of official grades among the k most similar job
    families seen in training. High spread = similar jobs disagree = route to a human."""
    out = np.zeros(len(y))
    for tr, te in GroupKFold(n_splits=5, shuffle=True, random_state=SEED).split(fam, y, groups):
        sim = fam[te] @ fam[tr].T
        idx = np.argsort(-sim, axis=1)[:, :k]
        out[te] = y[tr][idx].std(axis=1)
    return out


def group_index():
    r = salary_ranges().sort_values("range_mid")
    r["idx"] = r.groupby("schedule").cumcount()
    return r


def grade_distance(jobs, pred_log):
    """Distance in salary groups between the predicted midpoint and the actual group."""
    r = group_index()
    out = np.zeros(len(jobs), dtype=int)
    for sched, g in r.groupby("schedule"):
        mids = np.log(g["range_mid"].to_numpy())
        idx_of = dict(zip(g["salary_group"], g["idx"]))
        m = (jobs["schedule"] == sched).to_numpy()
        nearest = np.abs(pred_log[m][:, None] - mids[None, :]).argmin(axis=1)
        actual = jobs.loc[m, "salary_group"].map(idx_of).to_numpy()
        out[m] = g["idx"].to_numpy()[nearest] - actual
    return out


def metrics(name, jobs, y, pred):
    err = pred - y
    d = grade_distance(jobs, pred)
    return {
        "model": name,
        "median_abs_error_pct": np.median(np.abs(np.expm1(err))) * 100,
        "mean_abs_error_pct": np.mean(np.abs(np.expm1(err))) * 100,
        "r2": 1 - np.sum(err ** 2) / np.sum((y - y.mean()) ** 2),
        "exact_group": np.mean(d == 0), "within_1_group": np.mean(np.abs(d) <= 1),
        "within_2_groups": np.mean(np.abs(d) <= 2),
    }


def main():
    ensure_dirs()
    jobs, fam, lvl = load()
    y = jobs["log_mid"].to_numpy()
    groups = jobs["pdf"].to_numpy()
    text = jobs["class_title"] + ". " + jobs["family_text"] + " " + jobs["level_text"]
    svr = lambda: SVR(C=1.0, epsilon=0.05)

    preds = {
        "Baseline: everyone at the median grade": oof(
            lambda: type("M", (), {"fit": lambda s, X, y: setattr(s, "m", np.median(y)) or s,
                                   "predict": lambda s, X: np.full(len(X), s.m)})(),
            fam, y, groups),
        "Keyword model (TF-IDF + ridge)": oof(
            lambda: make_pipeline(TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
                                  RidgeCV(alphas=ALPHAS)), text, y, groups),
        "AI: family description only": oof(svr, fam, y, groups),
        "AI: title + level paragraph only": oof(svr, lvl, y, groups),
        "AI: full description (embeddings + SVR)": oof(svr, np.hstack([fam, lvl]), y, groups),
    }
    ai = preds["AI: full description (embeddings + SVR)"]
    kw = preds["Keyword model (TF-IDF + ridge)"]
    preds["AI + keyword ensemble"] = (ai + kw) / 2

    res = pd.DataFrame([metrics(k, jobs, y, v) for k, v in preds.items()])
    res.to_csv(OUT / "grading_metrics.csv", index=False)
    print(res.round(3).to_string(index=False))

    best = preds["AI + keyword ensemble"]
    out = jobs[["class_code", "class_title", "series", "level", "occ_category", "pdf", "schedule",
                "salary_group", "range_mid"]].copy()
    out["predicted_mid"] = np.exp(best)
    out["ai_vs_official_pct"] = np.expm1(best - y) * 100
    out["ai_vs_official_groups"] = grade_distance(jobs, best)
    out["uncertainty"] = neighbor_spread(fam, y, groups)
    out.to_csv(OUT / "grading_predictions.csv", index=False)

    rows = []
    order = np.argsort(out["uncertainty"].to_numpy())
    for share in ROUTE_SHARES:
        k = int(round(share * len(out)))
        auto = order[:k]
        rows.append({
            "auto_accepted_share": share, "jobs_auto_accepted": k, "jobs_to_human": len(out) - k,
            "within_1_group_auto": np.mean(np.abs(out["ai_vs_official_groups"].to_numpy()[auto]) <= 1),
            "median_abs_error_pct_auto": np.median(np.abs(out["ai_vs_official_pct"].to_numpy()[auto])),
        })
    route = pd.DataFrame(rows)
    route.to_csv(OUT / "grading_routing.csv", index=False)
    print(route.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

"""AI-assisted market matching: suggest the federal occupation (SOC) for each state job family.

Evaluated on 65 hand-labeled job families (labels/market_match_labels.csv), at the
6-digit SOC level used by BLS wage data. A match counts if it is in the label's
acceptable set.

Methods
  Title keyword match     TF-IDF of the state family name vs O*NET titles + alternate titles
  AI: description match   cosine similarity of embeddings, state family description vs O*NET
  Hybrid                  average of the two methods' scores

Outputs
  market_match_metrics.csv      top-1 / top-3 / top-5 accuracy per method
  market_match_labeled.csv      per labeled family: label, top-3 suggestions per method
  market_match_suggestions.csv  top-3 hybrid suggestions with confidence for all job families
  market_match_routing.csv      hybrid top-1 accuracy when only high-margin matches are auto-accepted
"""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from common import INTERIM, OUT, ROOT, ensure_dirs
from embed import read_onet

LABELS = ROOT / "labels" / "market_match_labels.csv"
TOPK = (1, 3, 5)


def families():
    jobs = pd.read_parquet(INTERIM / "jobs.parquet")
    emb = np.load(INTERIM / "emb_family_query.npy")
    first = jobs.reset_index().groupby("pdf").first()
    return first[["pdf_series", "series", "occ_category"]].reset_index(), emb[first["index"].to_numpy()]


def soc_scores(scores, onet):
    """Collapse O*NET detailed occupations to 6-digit SOC, keeping the best score."""
    df = pd.DataFrame(scores.T, index=onet["soc6"])
    return df.groupby(level=0).max().T


def title_scores(names, onet):
    alt = read_onet("Job Titles.txt")
    alt = alt.groupby("O*NET-SOC Code")["Job Title"].apply(lambda s: " ; ".join(s))
    docs = onet["title"] + " ; " + onet["onet_code"].map(alt).fillna("")
    vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, stop_words="english").fit(docs)
    return (vec.transform(names) @ vec.transform(docs).T).toarray()


def rank_norm(s):
    """Scale each row to 0-1 so the two methods' scores are comparable."""
    lo, hi = s.min(axis=1, keepdims=True), s.max(axis=1, keepdims=True)
    return (s - lo) / np.where(hi > lo, hi - lo, 1)


def topk(df, k):
    return [list(df.columns[np.argsort(-r)[:k]]) for r in df.to_numpy()]


def main():
    ensure_dirs()
    fam, emb = families()
    onet = pd.read_parquet(INTERIM / "onet.parquet")
    onet_emb = np.load(INTERIM / "emb_onet.npy")
    names = fam["pdf_series"].where(fam["pdf_series"].str.len() > 0, fam["series"])

    title = soc_scores(title_scores(names, onet), onet)
    ai = soc_scores(emb @ onet_emb.T, onet)
    hybrid = (rank_norm(title.to_numpy()) + rank_norm(ai.to_numpy())) / 2
    hybrid = pd.DataFrame(hybrid, columns=ai.columns)
    methods = {"Title keyword match": title, "AI: description match": ai, "Hybrid (title + AI)": hybrid}

    lab = pd.read_csv(LABELS, dtype=str)
    lab["acceptable"] = lab["soc_acceptable"].str.split(";")
    missing = {c for a in lab["acceptable"] for c in a} - set(ai.columns)
    if missing:
        print("label codes not in O*NET:", sorted(missing))
    pos = fam.reset_index().set_index("pdf")["index"]
    rows_idx = lab["pdf"].map(pos).to_numpy()

    metrics, per = [], lab[["pdf", "series", "soc_primary", "soc_acceptable"]].copy()
    soc_title = onet.groupby("soc6")["title"].first()
    for name, df in methods.items():
        top = topk(df.iloc[rows_idx], max(TOPK))
        hits = {k: np.mean([bool(set(t[:k]) & set(a)) for t, a in zip(top, lab["acceptable"])]) for k in TOPK}
        metrics.append({"method": name, **{f"top{k}_accuracy": v for k, v in hits.items()},
                        "families": len(lab)})
        per[f"{name} top3"] = [" | ".join(f"{c} {soc_title[c]}" for c in t[:3]) for t in top]
        per[f"{name} top1 correct"] = [t[0] in a for t, a in zip(top, lab["acceptable"])]
    m = pd.DataFrame(metrics)
    m.to_csv(OUT / "market_match_metrics.csv", index=False)
    per.to_csv(OUT / "market_match_labeled.csv", index=False)
    print(m.round(3).to_string(index=False))

    h = hybrid.to_numpy()
    srt = np.sort(h, axis=1)
    margin = srt[:, -1] - srt[:, -2]
    top3 = topk(hybrid, 3)
    sug = fam.assign(
        suggestion_1=[f"{t[0]} {soc_title[t[0]]}" for t in top3],
        suggestion_2=[f"{t[1]} {soc_title[t[1]]}" for t in top3],
        suggestion_3=[f"{t[2]} {soc_title[t[2]]}" for t in top3],
        confidence_margin=margin)
    sug.sort_values("confidence_margin", ascending=False).to_csv(OUT / "market_match_suggestions.csv", index=False)

    correct = per["Hybrid (title + AI) top1 correct"].to_numpy()
    lab_margin = margin[rows_idx]
    order = np.argsort(-lab_margin)
    route = []
    for share in (1.0, 0.75, 0.5):
        k = int(round(share * len(order)))
        route.append({"auto_accepted_share": share, "families_auto_accepted": k,
                      "top1_accuracy_auto": correct[order[:k]].mean(),
                      "top1_accuracy_routed_to_human": correct[order[k:]].mean() if k < len(order) else np.nan})
    r = pd.DataFrame(route)
    r.to_csv(OUT / "market_match_routing.csv", index=False)
    print(r.round(3).to_string(index=False))


if __name__ == "__main__":
    main()

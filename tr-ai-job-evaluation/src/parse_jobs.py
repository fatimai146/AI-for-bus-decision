"""Parse the State Auditor's job description PDFs into one row per job class.

Salary groups and dollar ranges printed in the PDFs are removed so the models
never see the answer.

Output: data/interim/jobs.parquet
  class_code, class_title, series, level, n_levels, occ_category, salary_group,
  schedule, range_mid, family_text (shared by all levels), level_text
"""
import re
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
from pypdf import PdfReader

from common import INTERIM, JD_DIR, SAO_INDEX, SCHEDULE, ensure_dirs

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII"]
TITLE_RE = re.compile(r"^(.*?)\s+(" + "|".join(sorted(ROMAN, key=len, reverse=True)) + r")$")
HEADINGS = ["GENERAL DESCRIPTION", "DISTINGUISHING CHARACTERISTICS", "EXAMPLES OF WORK PERFORMED",
            "DESCRIPTION OF LEVELS", "GENERAL QUALIFICATION GUIDELINES", "EXPERIENCE AND EDUCATION",
            "KNOWLEDGE, SKILLS, AND ABILITIES", "REGISTRATION, CERTIFICATION, OR LICENSURE"]
FAMILY_SECTIONS = ["GENERAL DESCRIPTION", "DISTINGUISHING CHARACTERISTICS", "EXAMPLES OF WORK PERFORMED",
                   "EXPERIENCE AND EDUCATION", "KNOWLEDGE, SKILLS, AND ABILITIES",
                   "REGISTRATION, CERTIFICATION, OR LICENSURE"]
NOISE = [re.compile(p) for p in [
    r"^State Classification Job Description\s*$", r"^\s*Job Classification Series:", r"^Occupational Category:",
    r"^Texas State Auditor.s Office", r"^CLASS TITLE\s+CLASS CODE", r"Page \d+ of \d+"]]
LEAK = [re.compile(p) for p in [r"\$[\d,]+(\.\d+)?", r"\b[ABC]\d{1,2}\b", r"\((Added|Revised|Deleted)[^)]*\)",
                                r"Revised \d+-\d+-\d+"]]


def norm_group(g):
    return re.sub(r"^([A-Z])0*(\d+)$", r"\1\2", str(g).strip())


def class_index():
    html = SAO_INDEX.read_text(errors="ignore")
    links = re.findall(r"JobDescriptions/([0-9A-Za-z]+)\.pdf\"[^>]*>\s*([0-9A-Za-z]{4})\s*</a>", html)
    pdf_of = {code.lstrip("0"): pdf for pdf, code in links}
    t = pd.read_html(SAO_INDEX)[0].iloc[:, :4]
    t.columns = ["class_code", "class_title", "salary_group", "occ_category"]
    t["class_code"] = t["class_code"].astype(str).str.strip().str.lstrip("0")
    t["class_title"] = t["class_title"].str.strip()
    t["occ_category"] = t["occ_category"].str.strip()
    t["salary_group"] = t["salary_group"].map(norm_group)
    t["pdf"] = t["class_code"].map(pdf_of)
    parts = t["class_title"].str.extract(TITLE_RE)
    t["series"] = parts[0].fillna(t["class_title"])
    t["level"] = parts[1].map({r: i for i, r in enumerate(ROMAN, 1)}).fillna(1).astype(int)
    return t


def salary_ranges():
    rows = []
    for sched, tbl in zip("AB", pd.read_html(SCHEDULE)[:2]):
        tbl = tbl.iloc[:, :4]
        tbl.columns = ["salary_group", "period", "mn", "mx"]
        tbl = tbl[tbl["period"] == "Annual"].copy()
        tbl["schedule"] = sched
        rows.append(tbl)
    r = pd.concat(rows)
    r["salary_group"] = r["salary_group"].map(norm_group)
    r["range_mid"] = (r["mn"].astype(float) + r["mx"].astype(float)) / 2
    return r[["salary_group", "schedule", "range_mid"]]


def clean_lines(text, series_name):
    out = []
    for line in text.splitlines():
        s = line.strip()
        if not s or any(p.search(s) for p in NOISE) or s.lower() == series_name.lower():
            continue
        if re.search(r"\s[0-9A-Z]{4}\s+[ABC]\d{1,2}\s+\$", s):
            continue
        out.append(s)
    return out


def split_sections(lines):
    sections, cur = {}, "PREAMBLE"
    for s in lines:
        key = s.rstrip(" :").upper()
        if key in HEADINGS:
            cur = key
            continue
        sections.setdefault(cur, []).append(s)
    return {k: " ".join(v) for k, v in sections.items()}


def scrub(text):
    for p in LEAK:
        text = p.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


MARKER_RE = re.compile(
    r"([A-Z][A-Z0-9 ,'’&/\-\.]+?)\s+(" + "|".join(sorted(ROMAN, key=len, reverse=True)) + r")\s*(?:\([^)]*\))?\s*:")


def level_paragraphs(levels_text, titles):
    """Split the DESCRIPTION OF LEVELS section at '<SERIES NAME> <ROMAN>:' markers.

    Markers are matched to class titles by level numeral plus a fuzzy match on
    the series name, because the PDFs contain typos and inline '(Added ...)' notes.
    """
    targets = []
    for t in titles:
        m = TITLE_RE.match(t)
        if m:
            targets.append((t.upper(), m.group(1).upper(), m.group(2)))
    hits = list(MARKER_RE.finditer(levels_text))
    paras = {}
    for i, m in enumerate(hits):
        name, roman = m.group(1).strip(), m.group(2)
        cands = [(SequenceMatcher(None, name, s).ratio(), t) for t, s, r in targets if r == roman]
        if not cands:
            continue
        score, title = max(cands)
        if score < 0.8:
            continue
        end = hits[i + 1].start() if i + 1 < len(hits) else len(levels_text)
        body = re.split(r"\bNote:", levels_text[m.end():end])[0]
        paras.setdefault(title, body)
    return paras


def main():
    ensure_dirs()
    idx = class_index().merge(salary_ranges(), on="salary_group", how="left")
    rows = []
    for pdf, grp in idx.dropna(subset=["pdf"]).groupby("pdf"):
        path = JD_DIR / f"{pdf}.pdf"
        text = "\n".join((p.extract_text() or "") for p in PdfReader(path).pages)
        series_name = re.search(r"Job Classification Series:\s*(.+)", text)
        series_name = series_name.group(1).strip() if series_name else ""
        sec = split_sections(clean_lines(text, series_name))
        family = scrub(" ".join(sec.get(s, "") for s in FAMILY_SECTIONS))
        paras = level_paragraphs(sec.get("DESCRIPTION OF LEVELS", ""), grp["class_title"])
        for _, r in grp.iterrows():
            rows.append({**r.to_dict(), "pdf_series": series_name, "family_text": family,
                         "level_text": scrub(paras.get(r["class_title"].upper(), ""))})
    jobs = pd.DataFrame(rows)
    jobs["n_levels"] = jobs.groupby("pdf")["class_code"].transform("size")
    jobs["log_mid"] = np.log(jobs["range_mid"])
    jobs = jobs.sort_values("class_code").reset_index(drop=True)
    jobs.to_parquet(INTERIM / "jobs.parquet", index=False)

    ab = jobs[jobs["schedule"].notna()]
    print(f"classes in index: {len(idx)}; parsed: {len(jobs)}; on Schedule A/B: {len(ab)}")
    print(f"job families (PDFs): {jobs['pdf'].nunique()}")
    multi = ab[ab["n_levels"] > 1]
    print(f"multi-level classes with a level paragraph: {(multi['level_text'].str.len() > 0).mean():.1%}")
    print(f"median family text words: {ab['family_text'].str.split().str.len().median():.0f}")
    leaks = ab["family_text"].str.contains(r"\$\d|\b[AB]\d{2}\b").sum() + ab["level_text"].str.contains(
        r"\$\d|\b[AB]\d{2}\b").sum()
    print(f"rows with salary text left after scrubbing: {leaks}")


if __name__ == "__main__":
    main()

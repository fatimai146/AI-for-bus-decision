"""Parse Costco quarterly earnings releases (8-K Exhibit 99.1/99.2) into tidy tables.

Outputs (data/interim/):
- release_pnl.csv     quarter P&L as first reported, plus the prior-year column from the same release
- release_comps.csv   quarter comparable sales, reported and excluding gasoline and FX ("adjusted")
- release_notes.csv   warehouse count, traffic/ticket and gross-margin bridge items when disclosed
"""
import glob
import html
import os
import re

import pandas as pd
from lxml import html as lh

from common import INTERIM, RELEASES, ensure_dirs

PNL_LINES = {
    "net sales": "net_sales",
    "membership fees": "membership_fees",
    "total revenue": "total_revenue",
    "merchandise costs": "merch_costs",
    "selling, general and administrative": "sga",
    "preopening expenses": "preopening",
    "provision for impaired assets and closing costs, net": "impairment",
    "operating income": "operating_income",
    "net income": "net_income_total",
    "net income including noncontrolling interests": "net_income_total",
    "net income attributable to costco": "net_income",
}
QWORD = {"FIRST": 1, "SECOND": 2, "THIRD": 3, "FOURTH": 4}


def load(path):
    raw = open(path, "rb").read().decode("latin-1")
    try:
        doc = lh.fromstring(raw)
    except Exception:
        return None, ""
    text = re.sub(r"\s+", " ", html.unescape(" ".join(doc.itertext())))
    return doc, text


def num(s):
    s = s.replace(",", "").replace("$", "").strip()
    neg = s.startswith("(")
    s = s.strip("()")
    try:
        v = float(s)
    except ValueError:
        return None
    return -v if neg else v


def table_rows(tb):
    out = []
    for tr in tb.xpath(".//tr"):
        c = [re.sub(r"\s+", " ", html.unescape(td.text_content())).strip() for td in tr.xpath("./td|./th")]
        c = [x for x in c if x and x not in ("$", "%", ")")]
        if c:
            out.append(c)
    return out


def parse_pnl(doc):
    for tb in doc.xpath("//table"):
        rows = table_rows(tb)
        labels = [r[0] for r in rows]
        if "Membership fees" not in labels or "Merchandise costs" not in labels:
            continue
        head = " ".join(" ".join(r) for r in rows[:3])
        weeks = re.findall(r"(\d+) ?Weeks", head) or [12]  # some Q1 tables omit the "12 Weeks Ended" row
        dates = re.findall(r"([A-Z][a-z]+\.? \d{1,2}, ?\d{4})", head)
        if not dates:
            continue
        cur, prior = {}, {}
        for r in rows:
            key = PNL_LINES.get(r[0].rstrip(":").lower())
            vals = [num(x) for x in r[1:]]
            vals = [v for v in vals if v is not None]
            if key and len(vals) >= 2 and key not in cur:
                cur[key], prior[key] = vals[0], vals[1]
        dates = [pd.to_datetime(d.replace(",", ", ").replace("  ", " ").replace(".", "")) for d in dates]
        end = dates[0]
        prior_end = dates[1] if len(dates) > 1 and dates[1] < end else end - pd.Timedelta(weeks=52)
        return int(weeks[0]), end, prior_end, cur, prior
    return None


PCT = r"\(?[-\u2013\u2212]?\d+(?:\.\d+)?\)?\s?%"


def pct_list(s):
    out = []
    for m in re.findall(PCT, s):
        m = m.replace("\u2013", "-").replace("\u2212", "-").replace("%", "").strip()
        out.append(-float(m.strip("()")) if m.startswith("(") else float(m))
    return out


def parse_comps(text, qweeks):
    """Return dict of quarter comps: total/us reported and adjusted."""
    start = text.find("omparable sales")
    if start < 0:
        return {}
    stop = text.find("Net income", start)
    sec = text[start:stop if stop > 0 else start + 4000]
    sec = re.sub(r"w/o gas[^U]*?FX", "Adjusted*", sec)
    sec = re.sub(r"Fiscal (Quarter|Year)\s*", "", sec)
    res = {}
    # some releases have no "N Weeks" header: reported table first, then the one excluding gas/FX
    if not re.search(r"\d+\s?Weeks", sec):
        totals = re.findall(r"Total(?: Company)?\s((?:\s*" + PCT + r")+)", sec)
        uss = re.findall(r"U\.S\.\s?((?:\s*" + PCT + r")+)", sec)
        for region, found in (("total", totals), ("us", uss)):
            for kind, s in zip(("rep", "adj"), found[:2]):
                res[f"{region}_{kind}"] = pct_list(s)[0]
        return res
    # split into table blocks at each header run of "N Weeks"
    blocks = []
    for m in re.finditer(r"((?:(?:Sept\.|[A-Z][a-z]+\.)?\s?\d+\s?Weeks\s*(?:Ended\s*)?)+)((?:Adjusted\*?\s*)*)", sec):
        blocks.append((m.start(), m.group(1), m.group(2), m.end()))
    for i, (pos, wk, adj, end) in enumerate(blocks):
        body = sec[end: blocks[i + 1][0] if i + 1 < len(blocks) else len(sec)]
        weeks = [int(w) for w in re.findall(r"(\d+)\s?Weeks", wk)]
        n_adj = len(re.findall("Adjusted", adj))
        paired = len(weeks) % 2 == 0 and all(weeks[j] == weeks[j + 1] for j in range(0, len(weeks), 2))
        cols = []
        if n_adj and paired:
            cols = [(w, j % 2 == 1) for j, w in enumerate(weeks)]
        elif "Adjusted" in wk:
            cols = [(w, "Adjusted" in part) for w, part in zip(weeks, re.split(r"(?<=Weeks)", wk))]
        else:
            # the sentence between the previous table and this one says whether it excludes gas/FX
            prev_end = blocks[i - 1][3] if i else 0
            intro = sec[prev_end:pos]
            intro = intro[max(intro.rfind("%") + 1, 0):].lower()
            cols = [(w, "excluding" in intro) for w in weeks]
        for region, pat in (("total", r"Total(?: Company)?\s"), ("us", r"U\.S\.\s?")):
            m = re.search(pat + r"((?:\s*" + PCT + r")+)", body)
            if not m:
                continue
            vals = pct_list(m.group(1))
            if len(vals) < len(cols):
                continue
            for (w, a), v in zip(cols, vals):
                if w == qweeks:
                    key = f"{region}_{'adj' if a else 'rep'}"
                    res.setdefault(key, v)
    return res


def parse_notes(text, supp):
    n = {}
    m = re.search(r"(?:operates|with) (\d{3,4}) warehouses", text)
    if m:
        n["warehouses"] = int(m.group(1))
    # the supplement's slide layout changes often; only these two labels are stable
    for key, pat in (("renewal_us_ca", r"([\d.]+)% US/CN Renewal Rate"),
                     ("paid_members_mm", r"([\d.]+)MM Paid Memberships")):
        m = re.search(pat, supp)
        if m:
            n[key] = float(m.group(1))
    return n


def main():
    ensure_dirs()
    pnl, comps, notes = [], [], []
    files = sorted(f for f in glob.glob(str(RELEASES / "*")) if not f.endswith("index.json"))
    by_acc = {}
    for f in files:
        by_acc.setdefault(os.path.basename(f)[:18], []).append(f)
    for acc, fs in by_acc.items():
        main_f = [f for f in fs if re.search(r"99(1|\.1|-1|18)", os.path.basename(f)[19:])] or fs
        doc, text = load(main_f[0])
        if doc is None:
            continue
        head = re.search(r"(?i)REPORTS? (FIRST|SECOND|THIRD|FOURTH) QUARTER", text[:4000])
        if not head:
            continue
        parsed = parse_pnl(doc)
        if not parsed:
            print("no P&L table:", main_f[0])
            continue
        weeks, end, prior_end, cur, prior = parsed
        fq = QWORD[head.group(1).upper()]
        fy = end.year + 1 if end.month >= 10 else end.year
        supp = ""
        for f in fs:
            if "9928" in f or "992." in f or "dex992" in f:
                supp = load(f)[1]
        pnl.append({"fy": fy, "fq": fq, "weeks": weeks, "end": end, "prior_end": prior_end, "accession": acc,
                    **cur, **{f"py_{k}": v for k, v in prior.items()}})
        comps.append({"fy": fy, "fq": fq, **parse_comps(text, weeks)})
        notes.append({"fy": fy, "fq": fq, **parse_notes(text, supp)})
    key = ["fy", "fq"]
    pnl = pd.DataFrame(pnl).sort_values(key).drop_duplicates(key, keep="last")
    money = [c for c in pnl if c not in ("fy", "fq", "weeks", "end", "prior_end", "accession")]
    in_thousands = pnl["net_sales"] > 1e6  # pre-2011 releases report in thousands
    pnl.loc[in_thousands, money] = pnl.loc[in_thousands, money] / 1000
    for p in ("", "py_"):
        pnl[f"{p}net_income"] = pnl[f"{p}net_income"].fillna(pnl[f"{p}net_income_total"])
        pnl[f"{p}other_opex"] = pnl[[f"{p}preopening", f"{p}impairment"]].fillna(0).sum(axis=1)
    pnl = pnl.drop(columns=[c for c in pnl if c.endswith(("net_income_total", "preopening", "impairment"))])
    comps = pd.DataFrame(comps).sort_values(key).drop_duplicates(key, keep="last")
    notes = pd.DataFrame(notes).sort_values(key).drop_duplicates(key, keep="last")
    pnl.to_csv(INTERIM / "release_pnl.csv", index=False)
    comps.to_csv(INTERIM / "release_comps.csv", index=False)
    notes.to_csv(INTERIM / "release_notes.csv", index=False)
    print(f"P&L: {len(pnl)} quarters FY{pnl.fy.min()}Q{pnl.fq.iloc[0]}-FY{pnl.fy.max()}Q{pnl.fq.iloc[-1]}")
    print("comps coverage:\n", comps.notna().groupby(comps.fy).sum().drop(columns=key).to_string())


if __name__ == "__main__":
    main()

"""Download every public input. Files are cached in data/raw/ and skipped if present.

- Costco 8-K exhibits (quarterly earnings releases and supplements) from SEC EDGAR
- Costco XBRL company facts (cross-check only)
- FRED: weekly U.S. gasoline price and daily exchange rates
"""
import json
import time

import requests

from common import CIK, FRED_SERIES, RAW, RELEASES, SEC_HEADERS, ensure_dirs

S = requests.Session()
S.headers.update(SEC_HEADERS)


def fetch(url, path, binary=False):
    if path.exists() and path.stat().st_size > 0:
        return path
    for attempt in range(5):
        r = S.get(url, timeout=60)
        if r.status_code == 200:
            path.write_bytes(r.content)
            time.sleep(0.12)
            return path
        time.sleep(2 ** attempt)
    raise RuntimeError(f"{url}: HTTP {r.status_code}")


def eight_k_filings():
    sub = json.loads(fetch(f"https://data.sec.gov/submissions/CIK{CIK}.json", RAW / "submissions.json").read_text())
    blocks = [sub["filings"]["recent"]]
    for f in sub["filings"].get("files", []):
        blocks.append(json.loads(fetch(f"https://data.sec.gov/submissions/{f['name']}", RAW / f["name"]).read_text()))
    rows = []
    for b in blocks:
        for i, form in enumerate(b["form"]):
            if form == "8-K":
                rows.append((b["filingDate"][i], b["accessionNumber"][i]))
    return sorted(set(rows))


def exhibits(accession):
    acc = accession.replace("-", "")
    idx = json.loads(fetch(f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc}/index.json",
                           RELEASES / f"{acc}_index.json").read_text())
    names = [i["name"] for i in idx["directory"]["item"]]
    ex = [n for n in names if n.lower().endswith((".htm", ".txt")) and "99" in n.lower() and "index" not in n.lower()]
    if not ex:
        ex = [n for n in names if n.endswith(".txt") and n.startswith(accession)]
    for n in ex:
        fetch(f"https://www.sec.gov/Archives/edgar/data/{int(CIK)}/{acc}/{n}", RELEASES / f"{acc}_{n}")


def main():
    ensure_dirs()
    filings = eight_k_filings()
    print(f"{len(filings)} 8-K filings, {filings[0][0]} to {filings[-1][0]}")
    for date, acc in filings:
        if date < "2005-01-01":
            continue
        exhibits(acc)
    fetch(f"https://data.sec.gov/api/xbrl/companyfacts/CIK{CIK}.json", RAW / "companyfacts.json")
    for sid in FRED_SERIES:
        r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", timeout=60)
        r.raise_for_status()
        (RAW / f"fred_{sid}.csv").write_bytes(r.content)
    print("downloads complete")


if __name__ == "__main__":
    main()

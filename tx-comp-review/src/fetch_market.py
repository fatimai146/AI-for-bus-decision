"""Fetch BLS OEWS May 2025 wages for benchmark occupations (Texas and Austin MSA).

The bls.gov flat files block scripted downloads, so this uses the public BLS API.
Results are cached in data/raw/oews_api.json; delete the file to refetch.
"""
import json
import time

import requests

from common import OEWS_JSON

# State job-classification series -> 2018 SOC code used by OEWS.
BENCHMARKS = {
    "Accountant": "132011",
    "Auditor": "132011",
    "Budget Analyst": "132031",
    "Financial Analyst": "132051",
    "Human Resources Specialist": "131071",
    "Training and Development Specialist": "131151",
    "Purchaser": "131020",
    "Management Analyst": "131111",
    "Project Manager": "131082",
    "Data Analyst": "152051",
    "Systems Analyst": "151211",
    "Information Technology Business Analyst": "151211",
    "Programmer": "151251",
    "Systems Administrator": "151244",
    "Network Specialist": "151231",
    "Information Technology Support Specialist": "151232",
    "Cybersecurity Analyst": "151212",
    "Database Administrator": "151242",
    "Attorney": "231011",
    "Legal Assistant": "232011",
    "Planner": "193051",
}

AREAS = {"Texas": "S4800000", "Austin-Round Rock-San Marcos MSA": "M0012420"}
DATATYPES = {"01": "employment", "12": "p25", "13": "median", "14": "p75"}
API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"
YEAR = "2025"


def series_ids():
    for soc in sorted(set(BENCHMARKS.values())):
        for area_name, area in AREAS.items():
            for dt in DATATYPES:
                yield f"OEU{area}000000{soc}{dt}", soc, area_name, DATATYPES[dt]


def main():
    if OEWS_JSON.exists():
        print(f"cached: {OEWS_JSON}")
        return
    ids = list(series_ids())
    meta = {sid: (soc, area, field) for sid, soc, area, field in ids}
    out = []
    for i in range(0, len(ids), 25):
        batch = [sid for sid, *_ in ids[i:i + 25]]
        r = requests.post(API, json={"seriesid": batch, "startyear": YEAR, "endyear": YEAR}, timeout=60)
        r.raise_for_status()
        body = r.json()
        if body.get("status") != "REQUEST_SUCCEEDED":
            raise RuntimeError(body.get("message"))
        for s in body["Results"]["series"]:
            soc, area, field = meta[s["seriesID"]]
            val = s["data"][0]["value"] if s["data"] else None
            out.append({"series_id": s["seriesID"], "soc": soc, "area": area, "field": field, "value": val})
        time.sleep(1)
    OEWS_JSON.write_text(json.dumps({"year": YEAR, "benchmarks": BENCHMARKS, "rows": out}, indent=1))
    print(f"wrote {len(out)} series to {OEWS_JSON}")


if __name__ == "__main__":
    main()

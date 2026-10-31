"""Download every public input. Files already present are skipped."""
import re
import time

import requests

from common import (JD_DIR, ONET_URL, ONET_ZIP, PAYROLL, PAYROLL_URL, RAW, SAO_INDEX, SAO_INDEX_URL,
                    SAO_REPORT, SAO_REPORT_URL, SCHEDULE, SCHEDULE_URL)

HEADERS = {"User-Agent": "Mozilla/5.0 (research; public-data download)"}


def fetch(url, path):
    if path.exists() and path.stat().st_size > 0:
        return False
    r = requests.get(url, headers=HEADERS, timeout=120)
    r.raise_for_status()
    path.write_bytes(r.content)
    return True


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    JD_DIR.mkdir(parents=True, exist_ok=True)
    for url, path in [(SAO_INDEX_URL, SAO_INDEX), (SCHEDULE_URL, SCHEDULE), (SAO_REPORT_URL, SAO_REPORT),
                      (ONET_URL, ONET_ZIP), (PAYROLL_URL, PAYROLL)]:
        print(("downloaded " if fetch(url, path) else "cached     ") + path.name)

    links = sorted(set(re.findall(r"https://hr\.sao\.texas\.gov/Compensation/JobDescriptions/[0-9A-Za-z]+\.pdf",
                                  SAO_INDEX.read_text(errors="ignore"))))
    new = 0
    for url in links:
        if fetch(url, JD_DIR / url.rsplit("/", 1)[1]):
            new += 1
            time.sleep(0.2)
    print(f"job descriptions: {len(links)} linked, {new} downloaded")


if __name__ == "__main__":
    main()

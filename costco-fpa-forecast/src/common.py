from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RELEASES = RAW / "releases"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"
EXCEL = ROOT / "excel"

CIK = "0000909832"
SEC_HEADERS = {"User-Agent": "Mozilla/5.0 (research) imanfatima@purdue.edu"}

FRED_SERIES = {
    "GASREGW": "US regular gasoline, $/gallon (weekly)",
    "DEXCAUS": "CAD per USD",
    "DEXJPUS": "JPY per USD",
    "DEXKOUS": "KRW per USD",
    "DEXUSUK": "USD per GBP",
    "DEXMXUS": "MXN per USD",
    "DEXUSAL": "USD per AUD",
    "DEXTAUS": "TWD per USD",
}

COLORS = {"actual": "#1f2937", "plan": "#2563eb", "fcst": "#f59e0b",
          "pos": "#16a34a", "neg": "#dc2626", "neutral": "#9ca3af"}


def ensure_dirs():
    for p in (RELEASES, INTERIM, OUT, FIG, EXCEL):
        p.mkdir(parents=True, exist_ok=True)

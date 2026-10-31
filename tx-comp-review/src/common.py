from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DB = ROOT / "data" / "txcomp.duckdb"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"

PAYROLL_CSV = RAW / "tx_payroll.csv"
SAO_HTML = RAW / "sao_job_classes.html"
SCHEDULE_HTML = RAW / "salary_schedule_fy26_27.html"
OEWS_JSON = RAW / "oews_api.json"

SNAPSHOT_DATE = "2026-10-01"

# Tenure bands used throughout (years since hire date, as of the snapshot).
NEW_HIRE_MAX_YEARS = 2
TENURED_MIN_YEARS = 10

# Published tables suppress any group smaller than this.
MIN_CELL = 5

COLORS = {
    "new": "#2b8cbe",
    "mid": "#7bccc4",
    "tenured": "#e34a33",
    "neutral": "#636363",
    "accent": "#fdae6b",
}


def connect(read_only=True):
    return duckdb.connect(str(DB), read_only=read_only)


def ensure_dirs():
    OUT.mkdir(exist_ok=True)
    FIG.mkdir(exist_ok=True)

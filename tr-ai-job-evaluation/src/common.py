from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
JD_DIR = RAW / "job_descriptions"
INTERIM = ROOT / "data" / "interim"
OUT = ROOT / "outputs"
FIG = ROOT / "figures"

SAO_INDEX_URL = "https://hr.sao.texas.gov/CompensationSystem/JobDescriptions"
SCHEDULE_URL = "https://fmx.cpa.texas.gov/fmx/payper/reascode/26-27/salsched_2026.php"
SAO_REPORT_URL = "https://sao.texas.gov/Reports/Main/27-701.pdf"
ONET_URL = "https://www.onetcenter.org/dl_files/database/db_31_0_text.zip"
PAYROLL_URL = ("https://s3.amazonaws.com/raw.texastribune.org/state_of_texas/salaries/"
               "02_non_duplicated_employees/2026-10-01.csv")

SAO_INDEX = RAW / "sao_job_classes.html"
SCHEDULE = RAW / "salary_schedule_fy26_27.html"
SAO_REPORT = RAW / "sao_27-701.pdf"
ONET_ZIP = RAW / "onet_db_31_0_text.zip"
PAYROLL = RAW / "tx_payroll.csv"

EMBED_MODEL = "BAAI/bge-base-en-v1.5"
SEED = 0

COLORS = {"ai": "#2b8cbe", "base": "#bdbdbd", "flag": "#e34a33", "neutral": "#636363", "accent": "#fdae6b"}


def ensure_dirs():
    for d in (INTERIM, OUT, FIG):
        d.mkdir(parents=True, exist_ok=True)

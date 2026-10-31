#!/usr/bin/env bash
# Rebuild every output from public sources (downloads are cached in data/raw/).
set -euo pipefail
cd "$(dirname "$0")/src"
PY=../.venv/bin/python
mkdir -p ../outputs ../figures

$PY download.py
$PY parse_jobs.py
$PY embed.py
$PY job_grading.py
$PY grading_checks.py
$PY market_match.py
$PY make_figures.py

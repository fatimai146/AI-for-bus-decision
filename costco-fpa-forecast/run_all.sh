#!/usr/bin/env bash
# Rebuild every output from public sources (downloads are cached in data/raw/).
set -euo pipefail
cd "$(dirname "$0")/src"
PY=../.venv/bin/python
mkdir -p ../outputs ../figures ../excel

$PY download.py
$PY parse_releases.py
$PY build_actuals.py
$PY model.py
$PY figures.py
$PY build_excel.py

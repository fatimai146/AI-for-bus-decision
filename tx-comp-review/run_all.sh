#!/usr/bin/env bash
# Rebuild every output from the raw files in data/raw/ (see README for downloads).
set -euo pipefail
cd "$(dirname "$0")/src"
PY=../.venv/bin/python
mkdir -p ../outputs ../figures

$PY fetch_market.py
$PY build_db.py
$PY audit.py > ../outputs/data_quality_audit.txt
$PY compression.py
$PY range_position.py
$PY cost_to_fix.py
$PY pay_equity.py
$PY market.py
$PY structure.py
$PY make_figures.py
$PY export_tableau.py

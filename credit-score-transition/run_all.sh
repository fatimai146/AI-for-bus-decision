#!/usr/bin/env bash
# Rebuilds the database, audit, all result tables and all figures.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p outputs figures
cd src
PY="${PYTHON:-../.venv/bin/python}"

"$PY" build_db.py
"$PY" audit.py > ../outputs/data_quality_audit.txt
"$PY" compare_scores.py
"$PY" robustness.py
"$PY" switch_simulator.py
"$PY" make_figures.py
"$PY" export_tableau.py
echo "Done: see outputs/ and figures/"

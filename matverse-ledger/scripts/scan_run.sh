#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

export MATVERSE_DB=".runtime/matversescan.db"
python3 scan/app.py

#!/usr/bin/env bash
set -euo pipefail

echo "[1/4] Checking tools..."
command -v python3 >/dev/null || { echo "python3 not found"; exit 1; }

echo "[2/4] Python venv..."
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip

echo "[3/4] Installing Python deps (indexer + scan + tooling)..."
pip install -r indexer/requirements.txt
pip install -r scan/requirements.txt
pip install -r requirements-dev.txt

echo "[4/4] Done."
echo "Next:"
echo "  bash scripts/devnet_up.sh"

#!/usr/bin/env bash
set -euo pipefail
source .runtime/addresses.env
source .venv/bin/activate

python3 indexer/indexer.py \
  --rpc "$RPC" \
  --pose "$POSE_ADDR" \
  --pole "$POLE_ADDR" \
  --db ".runtime/matversescan.db" \
  --from-block 0

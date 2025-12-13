#!/usr/bin/env bash
set -euo pipefail
if [ -f .anvil.pid ]; then
  kill "$(cat .anvil.pid)" || true
  rm -f .anvil.pid
fi
echo "Anvil stopped."

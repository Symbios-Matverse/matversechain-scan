#!/usr/bin/env bash
set -euo pipefail

# Anvil defaults: http://127.0.0.1:8545
echo "Starting anvil..."
nohup anvil --host 0.0.0.0 --port 8545 --chain-id 31337 > .anvil.log 2>&1 &
echo $! > .anvil.pid
sleep 1
echo "Anvil running (pid=$(cat .anvil.pid))"

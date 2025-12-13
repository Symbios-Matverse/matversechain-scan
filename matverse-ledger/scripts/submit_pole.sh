#!/usr/bin/env bash
set -euo pipefail
source .runtime/addresses.env

CLAIM_HASH_FILE=".runtime/claim_hash.txt"
if [ ! -f "$CLAIM_HASH_FILE" ]; then
  echo "claim hash not found. run: make claim" >&2
  exit 1
fi

CLAIM_HASH=$(tr -d '\n\r ' < "$CLAIM_HASH_FILE")
export CLAIM_HASH

# Simula uma execução determinística local e métricas
python3 bench/run_bench.py --out .runtime/bench_out.json

# Lê métricas e envia on-chain
python3 - <<PY
import json,subprocess,os
m=json.load(open(".runtime/bench_out.json"))
rpc=os.environ["RPC"]
pk=os.environ["PK"]
pole=os.environ["POLE_ADDR"]
claim=os.environ["CLAIM_HASH"]
verdict = 1 if m["verdict"]=="ACCEPT" else 0

# métricas uint: guardamos *1e6 para fixar precisão
def fx(x): return int(round(float(x)*1_000_000))

args = [
  "cast","send",
  "--rpc-url",rpc,
  "--private-key",pk,
  pole,
  "record(bytes32,uint8,uint256,uint256,uint256,uint256,bytes32)",
  claim,
  str(verdict),
  str(fx(m["omega"])),
  str(fx(m["psi"])),
  str(fx(m["cvar"])),
  str(int(m["latency_ms"])),
  m["run_hash"]
]
print(" ".join(args))
subprocess.check_call(args)
PY

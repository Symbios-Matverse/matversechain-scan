#!/usr/bin/env bash
set -euo pipefail

RPC="http://127.0.0.1:8545"
# Chave padrão do anvil[0]; para dev local apenas.
PK="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80"

echo "Deploying contracts via Foundry..."
pushd contracts >/dev/null

forge script script/Deploy.s.sol:Deploy \
  --rpc-url "$RPC" \
  --private-key "$PK" \
  --broadcast

# Extrai os endereços do broadcast json (Foundry)
OUT=$(ls -1 broadcast/Deploy.s.sol/31337/run-latest.json | tail -n 1)
POSE=$(python3 - <<PY
import json
p=json.load(open("$OUT"))
tx=p["transactions"]
# primeira criação
c=[t for t in tx if t.get("contractName")=="PoSERegistry"][0]
print(c["contractAddress"])
PY
)

POLE=$(python3 - <<PY
import json
p=json.load(open("$OUT"))
tx=p["transactions"]
c=[t for t in tx if t.get("contractName")=="PoLERegistry"][0]
print(c["contractAddress"])
PY
)

popd >/dev/null

mkdir -p .runtime
cat > .runtime/addresses.env <<EOF_ENV
RPC=$RPC
POSE_ADDR=$POSE
POLE_ADDR=$POLE
PK=$PK
EOF_ENV

echo "Deployed:"
echo "  PoSERegistry: $POSE"
echo "  PoLERegistry: $POLE"
echo "Saved .runtime/addresses.env"

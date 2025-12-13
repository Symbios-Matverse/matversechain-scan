#!/usr/bin/env bash
set -euo pipefail
source .runtime/addresses.env

CLAIM_HASH_FILE=".runtime/claim_hash.txt"
if [ ! -f "$CLAIM_HASH_FILE" ]; then
  echo "claim hash not found. run: make claim" >&2
  exit 1
fi

# Claim minimal: hash do claim compilado + proofHash + metadataURI
CLAIM_HASH=$(tr -d '\n\r ' < "$CLAIM_HASH_FILE")

PROOF_HASH="0x"$(python3 - <<PY
import os,hashlib
print(hashlib.sha256(b"pose-proof-v1").hexdigest())
PY
)

META_URI="ipfs://example/claim/1"

echo "Submitting PoSE..."
cast send \
  --rpc-url "$RPC" \
  --private-key "$PK" \
  "$POSE_ADDR" \
  "register(bytes32,string,bytes32)" \
  "$CLAIM_HASH" \
  "$META_URI" \
  "$PROOF_HASH"

echo "PoSE submitted:"
echo "  claimHash=$CLAIM_HASH"

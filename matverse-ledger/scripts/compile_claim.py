#!/usr/bin/env python3
"""
Validate and compile a claim file into a canonical form with hashed artifacts.

Steps performed:
- Load the claim YAML and validate it against the JSON schema.
- Hash the referenced artifact (e.g., bench/run_bench.py) and inject the digest.
- Emit the canonical claim hash (sha256 of the sorted JSON representation).
- Optionally write the updated claim and claim hash to disk.
"""
import argparse
import hashlib
import json
import pathlib

import yaml
from jsonschema import validate


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_bytes(payload: dict) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def resolve_artifact_path(uri: str, claim_path: pathlib.Path, artifact_root: pathlib.Path | None) -> pathlib.Path:
    path = pathlib.Path(uri)
    if not path.is_absolute():
        base = artifact_root if artifact_root is not None else claim_path.parent
        path = (base / path).resolve()
    return path


def hash_artifact(claim: dict, claim_path: pathlib.Path, artifact_root: pathlib.Path | None) -> str:
    artifact = claim.get("artifact", {})
    uri = artifact.get("uri")
    if not uri:
        raise ValueError("artifact.uri is required in the claim")
    artifact_path = resolve_artifact_path(uri, claim_path, artifact_root)
    data = artifact_path.read_bytes()
    return f"sha256:{sha256_hex(data)}"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_yaml(path: pathlib.Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def write_yaml(content: dict, path: pathlib.Path) -> None:
    path.write_text(yaml.safe_dump(content, sort_keys=False), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description="Compile a claim into a canonical hashable form")
    ap.add_argument("--claim", default="spec/claim.example.yaml", help="Path to the claim YAML file")
    ap.add_argument("--schema", default="spec/claim.schema.json", help="Path to the claim JSON schema")
    ap.add_argument("--artifact-root", default=None, help="Base directory to resolve relative artifact URIs")
    ap.add_argument("--out", default=None, help="Where to write the updated claim YAML (defaults to overwriting the input)")
    ap.add_argument("--hash-out", default=None, help="Optional file to write the computed claim hash")
    args = ap.parse_args()

    claim_path = pathlib.Path(args.claim).resolve()
    schema_path = pathlib.Path(args.schema).resolve()
    artifact_root = pathlib.Path(args.artifact_root).resolve() if args.artifact_root else None

    claim = load_yaml(claim_path)
    schema = load_json(schema_path)
    validate(instance=claim, schema=schema)

    artifact_hash = hash_artifact(claim, claim_path, artifact_root)
    claim["artifact"]["hash"] = artifact_hash

    claim_hash = "0x" + sha256_hex(canonical_bytes(claim))

    out_path = pathlib.Path(args.out).resolve() if args.out else claim_path
    write_yaml(claim, out_path)

    if args.hash_out:
        hash_out_path = pathlib.Path(args.hash_out)
        hash_out_path.parent.mkdir(parents=True, exist_ok=True)
        hash_out_path.write_text(claim_hash + "\n", encoding="utf-8")

    print(f"artifact_hash={artifact_hash}")
    print(f"claim_hash={claim_hash}")
    print(f"written={out_path}")
    if args.hash_out:
        print(f"hash_written={pathlib.Path(args.hash_out).resolve()}")


if __name__ == "__main__":
    main()

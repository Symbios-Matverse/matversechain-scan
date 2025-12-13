#!/usr/bin/env python3
"""Generate a compact, checksummed SQLite snapshot for MatVerseScan."""
import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any, Dict, Tuple

def sha256_file(path: Path, bufsize: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            chunk = f.read(bufsize)
            if not chunk:
                break
            h.update(chunk)
    return "0x" + h.hexdigest()

def row_counts(conn: sqlite3.Connection) -> Dict[str, int]:
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cur.fetchall()]
    counts: Dict[str, int] = {}
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        counts[table] = int(cur.fetchone()[0])
    return counts

def integrity_checks(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA quick_check;")
    quick = cur.fetchone()[0]
    if quick != "ok":
        raise RuntimeError(f"PRAGMA quick_check failed: {quick}")

    cur.execute("PRAGMA integrity_check;")
    integrity = cur.fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"PRAGMA integrity_check failed: {integrity}")

def optimize_and_vacuum(src: Path) -> None:
    # Optimize using WAL for safety, then VACUUM with DELETE mode for a compact file.
    conn = sqlite3.connect(src.as_posix())
    try:
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute("PRAGMA optimize;")
        integrity_checks(conn)
    finally:
        conn.close()

    conn = sqlite3.connect(src.as_posix())
    try:
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("VACUUM;")
    finally:
        conn.close()

def copy_db(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)

def maybe_zstd(src: Path, dst: Path) -> Tuple[bool, str]:
    """Attempt to compress with zstandard (Python or CLI)."""
    try:
        import zstandard as zstd  # type: ignore

        compressor = zstd.ZstdCompressor(level=19)
        with src.open("rb") as fin, dst.open("wb") as fout:
            compressor.copy_stream(fin, fout)
        return True, "python:zstandard"
    except Exception:
        pass

    if shutil.which("zstd"):
        code = os.system(f"zstd -q -19 --force -o {dst.as_posix()} {src.as_posix()}")
        if code == 0:
            return True, "cli:zstd"

    return False, "none"

def write_manifest(out_dir: Path, meta: Dict[str, Any]) -> Path:
    path = out_dir / "manifest.json"
    path.write_text(json.dumps(meta, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path

def main() -> int:
    ap = argparse.ArgumentParser(description="Generate a compacted, checksummed SQLite snapshot for MatVerseScan")
    ap.add_argument("--db", required=True, help="Path to source SQLite DB (e.g., .runtime/matversescan.db)")
    ap.add_argument("--out", default="dist", help="Output directory (default: dist)")
    ap.add_argument("--chain-id", type=int, default=31337, help="EVM chain id (default: 31337)")
    ap.add_argument("--from", dest="from_block", default="0", help="First indexed block (default: 0)")
    ap.add_argument("--to", dest="to_block", default="latest", help="Last indexed block (default: latest)")
    ap.add_argument("--name-prefix", default="mvscan", help="Artifact name prefix (default: mvscan)")
    args = ap.parse_args()

    src = Path(args.db).resolve()
    if not src.exists():
        print(f"error: DB not found: {src}", file=sys.stderr)
        return 2

    optimize_and_vacuum(src)

    timestamp = int(time.time())
    out_dir = Path(args.out).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    base = f"{args.name_prefix}_{args.chain_id}_{args.from_block}-{args.to_block}_{timestamp}"
    dst_sqlite = out_dir / f"{base}.sqlite"
    copy_db(src, dst_sqlite)

    conn = sqlite3.connect(dst_sqlite.as_posix())
    try:
        counts = row_counts(conn)
        integrity_checks(conn)
    finally:
        conn.close()

    sha = sha256_file(dst_sqlite)
    zst_path = out_dir / f"{base}.sqlite.zst"
    compressed, method = maybe_zstd(dst_sqlite, zst_path)
    zst_sha = sha256_file(zst_path) if compressed else None

    manifest = {
        "created_at": timestamp,
        "chain_id": args.chain_id,
        "blocks": {"from": args.from_block, "to": args.to_block},
        "files": {
            "sqlite": dst_sqlite.name,
            "sqlite_sha256": sha,
            "sqlite_zst": zst_path.name if compressed else None,
            "sqlite_zst_sha256": zst_sha,
            "compression": method,
        },
        "row_counts": counts,
        "db_version": 1,
        "schema": {
            "pose": [
                "id",
                "claim_hash",
                "submitter",
                "metadata_uri",
                "proof_hash",
                "block_number",
                "tx_hash",
                "timestamp",
            ],
            "pole": [
                "claim_hash",
                "run_hash",
                "submitter",
                "verdict",
                "omega_u6",
                "psi_u6",
                "cvar_u6",
                "latency_ms",
                "block_number",
                "tx_hash",
                "timestamp",
            ],
            "pole_pk": ["claim_hash", "run_hash"],
        },
    }
    manifest_path = write_manifest(out_dir, manifest)

    print(f"snapshot_sqlite={dst_sqlite}")
    print(f"snapshot_sqlite_sha256={sha}")
    if compressed:
        print(f"snapshot_sqlite_zst={zst_path}")
        print(f"snapshot_sqlite_zst_sha256={zst_sha}")
    print(f"manifest={manifest_path}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

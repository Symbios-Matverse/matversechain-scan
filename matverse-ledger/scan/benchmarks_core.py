"""GitHub-backed loader for matverse-core benchmark artifacts (data-only).

This module reads public JSON artifacts from the matverse-core repository via the
GitHub API, canonicalizes the observable matrix ``M`` and computes ``H(M)`` to
cross-check against the expected hash published in ``expected_output.json``.
No remote code execution occurs here; the verifier is intentionally deterministic
and side-effect free beyond HTTP requests.
"""

import hashlib
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import requests


@dataclass
class BenchRow:
    bench_dir: str
    claim_id: str
    version: str
    frozen_date: str
    h_m_calc: str
    h_m_expected: str
    match: bool
    metrics: Dict[str, Any]
    note: str


def canon_bytes(data: Dict[str, Any]) -> bytes:
    # Canonização idêntica ao core: sort_keys + separators
    return json.dumps(
        data,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def sha256_hex(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def gh_headers() -> Dict[str, str]:
    # Opcional: evita rate-limit em deploy (HF Spaces, etc.)
    token = os.getenv("GITHUB_TOKEN", "").strip()
    h = {"Accept": "application/vnd.github+json"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    return h


def gh_contents(owner: str, repo: str, path: str, ref: str) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}"
    r = requests.get(url, headers=gh_headers(), timeout=20)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        raise RuntimeError(f"GitHub contents API unexpected payload at {path}")
    return data


def gh_download_json(download_url: str) -> Dict[str, Any]:
    r = requests.get(download_url, headers=gh_headers(), timeout=20)
    r.raise_for_status()
    return r.json()


def _pick_download_url(entries: List[Dict[str, Any]], filename: str) -> Optional[str]:
    for it in entries:
        if it.get("type") == "file" and it.get("name") == filename:
            return it.get("download_url")
    return None


def load_core_benchmarks() -> List[BenchRow]:
    owner = os.getenv("CORE_OWNER", "Symbios-Matverse")
    repo = os.getenv("CORE_REPO", "matverse-core")
    ref = os.getenv("CORE_REF", "main")
    root = os.getenv("CORE_BENCH_ROOT", "benchmarks")

    entries = gh_contents(owner, repo, root, ref)
    bench_dirs = [e for e in entries if e.get("type") == "dir"]

    rows: List[BenchRow] = []

    for d in sorted(bench_dirs, key=lambda x: x.get("name", "")):
        bench_dir = d.get("name", "")

        # Cada benchmark precisa: spec/claim_v1.0.0.json + observable/expected_output.json + observable/M_canonical.json
        spec_entries = gh_contents(owner, repo, f"{root}/{bench_dir}/spec", ref)
        obs_entries = gh_contents(owner, repo, f"{root}/{bench_dir}/observable", ref)

        spec_url = _pick_download_url(spec_entries, "claim_v1.0.0.json")
        exp_url = _pick_download_url(obs_entries, "expected_output.json")
        m_url = _pick_download_url(obs_entries, "M_canonical.json")

        # Degrada com transparência: se faltar algo, aparece como FAIL com “note”
        if not spec_url or not exp_url or not m_url:
            claim_id = "UNKNOWN"
            version = "UNKNOWN"
            frozen_date = ""
            if spec_url:
                spec = gh_download_json(spec_url)
                claim_id = str(spec.get("claim_id", "UNKNOWN"))
                version = str(spec.get("version", "UNKNOWN"))
                frozen_date = str(spec.get("frozen_date", ""))

            h_m_expected = ""
            note = "incomplete: missing files in spec/ or observable/"
            if exp_url:
                exp = gh_download_json(exp_url)
                h_m_expected = str(exp.get("h_m", ""))

            rows.append(
                BenchRow(
                    bench_dir=bench_dir,
                    claim_id=claim_id,
                    version=version,
                    frozen_date=frozen_date,
                    h_m_calc="",
                    h_m_expected=h_m_expected,
                    match=False,
                    metrics={},
                    note=note,
                )
            )
            continue

        spec = gh_download_json(spec_url)
        exp = gh_download_json(exp_url)
        M = gh_download_json(m_url)

        h_m_calc = sha256_hex(canon_bytes(M))
        h_m_expected = str(exp.get("h_m", ""))
        match = h_m_calc == h_m_expected

        rows.append(
            BenchRow(
                bench_dir=bench_dir,
                claim_id=str(spec.get("claim_id", "")),
                version=str(spec.get("version", "")),
                frozen_date=str(spec.get("frozen_date", "")),
                h_m_calc=h_m_calc,
                h_m_expected=h_m_expected,
                match=match,
                metrics=dict(M.get("metrics", {})) if isinstance(M.get("metrics", {}), dict) else {},
                note=str(exp.get("note", "")),
            )
        )

    return rows

"""API CAPT para métricas runtime e benchmarks."""

from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, status

from capt.measurement.benchmark_freeze import CAPTBenchmarkFreezeStore
from capt.runtime.governed_client import ChromeOSRuntimeGovernor


MAX_PAYLOAD_BYTES = int(os.environ.get("CAPT_MAX_PAYLOAD_BYTES", "8192"))
MAX_PAYLOAD_KEYS = int(os.environ.get("CAPT_MAX_PAYLOAD_KEYS", "64"))


def _validate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if len(payload) > MAX_PAYLOAD_KEYS:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload has too many keys",
        )

    encoded = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_PAYLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="payload too large",
        )
    return payload


def _require_token(x_capt_token: str | None = Header(default=None)) -> None:
    expected = os.environ.get("CAPT_API_TOKEN")
    if not expected:
        return
    if x_capt_token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid token")


router = APIRouter(dependencies=[Depends(_require_token)])
_governor = ChromeOSRuntimeGovernor()
_freeze_store = CAPTBenchmarkFreezeStore()


@router.post("/capt/chromeos/capture")
async def capture_chromeos_metrics() -> dict:
    return await _governor.capture_metrics()


@router.post("/capt/terabox/measure")
async def measure_terabox_latency() -> dict:
    return await _governor.measure_terabox_latency()


@router.get("/capt/runtime/status")
async def runtime_status() -> dict:
    latest_freeze = _freeze_store.latest()
    return {
        "runtime": _governor.status(),
        "latest_benchmark_freeze": latest_freeze,
    }


@router.post("/capt/benchmark/freeze")
async def freeze_benchmark(payload: dict | None = None) -> dict:
    safe_payload = _validate_payload(payload or {})
    return _freeze_store.freeze(safe_payload)

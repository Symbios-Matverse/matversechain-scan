"""API CAPT para métricas runtime e benchmarks."""

from __future__ import annotations

from fastapi import APIRouter

from capt.measurement.benchmark_freeze import CAPTBenchmarkFreezeStore
from capt.runtime.governed_client import ChromeOSRuntimeGovernor


router = APIRouter()
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
    return _freeze_store.freeze(payload)

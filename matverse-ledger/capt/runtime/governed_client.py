"""Runtime governado para captura de métricas ChromeOS + TeraBox."""

from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass, field

import psutil


@dataclass
class ChromeOSRuntimeGovernor:
    """Captura métricas de /mnt/chromeos + TeraBox com governança."""

    chromeos_path: str = "/mnt/chromeos"
    terabox_path: str = "/mnt/terabox"
    terabox_sync: bool = True
    metrics_buffer: list[dict] = field(default_factory=list)
    max_buffer: int = 200
    last_sync_ts: float = field(default_factory=time.time)

    def _append_metrics(self, metrics: dict) -> dict:
        self.metrics_buffer.append(metrics)
        if len(self.metrics_buffer) > self.max_buffer:
            self.metrics_buffer = self.metrics_buffer[-self.max_buffer :]
        return metrics

    def _hash_entries(self, base_path: str, limit: int = 200) -> str:
        if not os.path.exists(base_path):
            return "missing"

        entries = []
        for root, dirs, files in os.walk(base_path):
            for name in sorted(dirs + files):
                path = os.path.join(root, name)
                try:
                    stat = os.stat(path)
                    entries.append(f"{os.path.relpath(path, base_path)}:{stat.st_size}:{stat.st_mtime}")
                except FileNotFoundError:
                    continue
                if len(entries) >= limit:
                    break
            if len(entries) >= limit:
                break

        digest = hashlib.sha256("|".join(entries).encode("utf-8")).hexdigest()
        return digest

    def get_sync_rate(self) -> float:
        now = time.time()
        elapsed = max(now - self.last_sync_ts, 1.0)
        return 1.0 / elapsed

    def hash_datasets(self) -> str:
        return self._hash_entries(self.chromeos_path)

    def analyze_model_cache(self) -> dict:
        cache_path = os.path.join(self.chromeos_path, "models")
        if not os.path.exists(cache_path):
            return {"path": cache_path, "entries": 0, "total_mb": 0.0}

        total_bytes = 0
        entries = 0
        for root, _, files in os.walk(cache_path):
            for name in files:
                entries += 1
                try:
                    total_bytes += os.path.getsize(os.path.join(root, name))
                except FileNotFoundError:
                    continue

        return {
            "path": cache_path,
            "entries": entries,
            "total_mb": round(total_bytes / (1024 * 1024), 2),
        }

    async def capture_metrics(self) -> dict:
        metrics = {
            "chromeos_cpu": psutil.cpu_percent(interval=0.1),
            "chromeos_mem": psutil.virtual_memory().percent,
            "terabox_sync_rate": self.get_sync_rate(),
            "datasets_hash": self.hash_datasets(),
            "model_cache": self.analyze_model_cache(),
            "timestamp": time.time(),
        }
        return self._append_metrics(metrics)

    async def measure_terabox_latency(self) -> dict:
        start = time.time()
        exists = os.path.exists(self.terabox_path)
        latency_ms = (time.time() - start) * 1000
        return {
            "terabox_path": self.terabox_path,
            "available": exists,
            "latency_ms": round(latency_ms, 2),
        }

    def status(self) -> dict:
        return {
            "chromeos_path": self.chromeos_path,
            "terabox_path": self.terabox_path,
            "terabox_sync": self.terabox_sync,
            "metrics_buffered": len(self.metrics_buffer),
        }

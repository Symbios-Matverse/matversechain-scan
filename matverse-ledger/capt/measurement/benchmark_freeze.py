"""Armazena benchmarks congelados do CAPT."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass
class CAPTBenchmarkFreezeStore:
    """Armazena eventos de congelamento em memória (scaffold)."""

    frozen: list[dict] = field(default_factory=list)
    max_entries: int = 100

    def freeze(self, payload: dict | None = None) -> dict:
        payload = payload or {}
        record = {
            "payload": payload,
            "timestamp": time.time(),
        }
        self.frozen.append(record)
        if len(self.frozen) > self.max_entries:
            self.frozen = self.frozen[-self.max_entries :]
        return record

    def latest(self) -> dict | None:
        if not self.frozen:
            return None
        return self.frozen[-1]

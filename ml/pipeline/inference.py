from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class InferenceResult:
    data: dict[str, Any]
    latency_ms: int
    cache_hit: bool = False


@dataclass
class PipelineStats:
    total_runs: int = 0
    cache_hits: int = 0
    latencies_ms: list[int] = field(default_factory=list)

    @property
    def average_ms(self) -> int:
        if not self.latencies_ms:
            return 0
        return int(sum(self.latencies_ms) / len(self.latencies_ms))

    @property
    def p95_ms(self) -> int:
        if not self.latencies_ms:
            return 0
        sorted_values = sorted(self.latencies_ms)
        index = max(0, int(len(sorted_values) * 0.95) - 1)
        return sorted_values[index]

    @property
    def p99_ms(self) -> int:
        if not self.latencies_ms:
            return 0
        sorted_values = sorted(self.latencies_ms)
        index = max(0, int(len(sorted_values) * 0.99) - 1)
        return sorted_values[index]


class InferencePipeline:
    def __init__(self) -> None:
        self._cache: dict[str, dict[str, Any]] = {}
        self.stats = PipelineStats()

    def _cache_key(self, task: str, payload: dict[str, Any]) -> str:
        canonical = json.dumps({"task": task, "payload": payload}, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def run(
        self,
        task: str,
        payload: dict[str, Any],
        handler: Callable[[dict[str, Any]], dict[str, Any]],
        *,
        use_cache: bool = True,
    ) -> InferenceResult:
        cache_key = self._cache_key(task, payload)
        if use_cache and cache_key in self._cache:
            self.stats.total_runs += 1
            self.stats.cache_hits += 1
            cached = self._cache[cache_key]
            return InferenceResult(data=cached, latency_ms=0, cache_hit=True)

        started = time.perf_counter()
        result = handler(payload)
        latency_ms = int((time.perf_counter() - started) * 1000)

        if use_cache:
            self._cache[cache_key] = result

        self.stats.total_runs += 1
        self.stats.latencies_ms.append(latency_ms)
        return InferenceResult(data=result, latency_ms=latency_ms, cache_hit=False)

    def clear_cache(self) -> None:
        self._cache.clear()


_pipeline: InferencePipeline | None = None


def get_inference_pipeline() -> InferencePipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = InferencePipeline()
    return _pipeline

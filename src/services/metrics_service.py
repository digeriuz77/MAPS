"""
Metrics Service
Lightweight in-memory metrics for LLM usage and memory pipeline events.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, DefaultDict
from collections import defaultdict

@dataclass
class LatencyStats:
    count: int = 0
    total_ms: float = 0.0
    max_ms: float = 0.0

    def add(self, ms: float):
        self.count += 1
        self.total_ms += ms
        if ms > self.max_ms:
            self.max_ms = ms

@dataclass
class Metrics:
    llm_calls_total: int = 0
    llm_calls_by_provider: DefaultDict[str, int] = field(default_factory=lambda: defaultdict(int))
    llm_calls_by_model: DefaultDict[str, int] = field(default_factory=lambda: defaultdict(int))
    llm_latency_ms_by_model: Dict[str, LatencyStats] = field(default_factory=dict)
    errors_total: int = 0

    summaries_created: int = 0
    consolidations_added: int = 0
    consolidations_updated: int = 0
    decay_updated: int = 0
    decay_pruned: int = 0

class MetricsService:
    def __init__(self):
        self.m = Metrics()

    def record_llm_call(self, provider: str, model: str, success: bool, latency_ms: float):
        self.m.llm_calls_total += 1
        self.m.llm_calls_by_provider[provider] += 1
        self.m.llm_calls_by_model[model] += 1
        stats = self.m.llm_latency_ms_by_model.setdefault(model, LatencyStats())
        stats.add(latency_ms)
        if not success:
            self.m.errors_total += 1

    def record_error(self):
        self.m.errors_total += 1

    def record_summary_created(self):
        self.m.summaries_created += 1

    def record_consolidation(self, action: str):
        if action.upper() == "ADD":
            self.m.consolidations_added += 1
        elif action.upper() == "UPDATE":
            self.m.consolidations_updated += 1

    def record_decay(self, updated: int, pruned: int):
        self.m.decay_updated += int(updated)
        self.m.decay_pruned += int(pruned)

    def get_metrics(self) -> Dict:
        out = {
            "llm": {
                "calls_total": self.m.llm_calls_total,
                "calls_by_provider": dict(self.m.llm_calls_by_provider),
                "calls_by_model": dict(self.m.llm_calls_by_model),
                "latency_ms_by_model": {
                    model: {
                        "count": s.count,
                        "avg_ms": round(s.total_ms / s.count, 2) if s.count else 0.0,
                        "max_ms": round(s.max_ms, 2),
                    }
                    for model, s in self.m.llm_latency_ms_by_model.items()
                },
                "errors_total": self.m.errors_total,
            },
            "memory": {
                "summaries_created": self.m.summaries_created,
                "consolidations_added": self.m.consolidations_added,
                "consolidations_updated": self.m.consolidations_updated,
                "decay_updated": self.m.decay_updated,
                "decay_pruned": self.m.decay_pruned,
            },
        }
        return out

# Global instance
metrics = MetricsService()
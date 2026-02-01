"""
Metrics Service
Enhanced metrics with persistent storage and database integration.
Supports both in-memory tracking and persistent storage via Supabase.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Dict, DefaultDict
from collections import defaultdict
from datetime import datetime

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
    def __init__(self, supabase_client=None):
        """
        Initialize MetricsService with optional database integration
        """
        self.m = Metrics()
        self.supabase_client = supabase_client
        self._initialized = False
        self._init_db()

    def _init_db(self):
        """Initialize database connection and ensure tables exist"""
        if not self.supabase_client:
            return

        try:
            # Check if metrics table exists
            result = self.supabase_client.table('system_metrics').select('id').limit(1).execute()
            if result.data is not None:
                self._initialized = True
                self._load_from_db()
        except Exception as e:
            print(f"Metrics database initialization failed: {e}")

    def _load_from_db(self):
        """Load persistent metrics from database"""
        try:
            result = self.supabase_client.table('system_metrics').select('*').execute()
            if result.data:
                # Use most recent metrics record
                latest = sorted(result.data, key=lambda x: x.get('created_at', ''), reverse=True)[0]
                if 'llm_calls_total' in latest:
                    self.m.llm_calls_total = latest['llm_calls_total']
                if 'errors_total' in latest:
                    self.m.errors_total = latest['errors_total']
                if 'summaries_created' in latest:
                    self.m.summaries_created = latest['summaries_created']
                if 'consolidations_added' in latest:
                    self.m.consolidations_added = latest['consolidations_added']
                if 'consolidations_updated' in latest:
                    self.m.consolidations_updated = latest['consolidations_updated']
                if 'decay_updated' in latest:
                    self.m.decay_updated = latest['decay_updated']
                if 'decay_pruned' in latest:
                    self.m.decay_pruned = latest['decay_pruned']
        except Exception as e:
            print(f"Failed to load metrics from database: {e}")

    def _save_to_db(self):
        """Save current metrics to database"""
        if not self.supabase_client or not self._initialized:
            return

        try:
            metrics_data = {
                'llm_calls_total': self.m.llm_calls_total,
                'errors_total': self.m.errors_total,
                'summaries_created': self.m.summaries_created,
                'consolidations_added': self.m.consolidations_added,
                'consolidations_updated': self.m.consolidations_updated,
                'decay_updated': self.m.decay_updated,
                'decay_pruned': self.m.decay_pruned,
                'created_at': datetime.utcnow().isoformat(),
                'llm_calls_by_provider': dict(self.m.llm_calls_by_provider),
                'llm_calls_by_model': dict(self.m.llm_calls_by_model),
                'llm_latency_ms_by_model': {
                    model: {
                        'count': s.count,
                        'avg_ms': round(s.total_ms / s.count, 2) if s.count else 0.0,
                        'max_ms': round(s.max_ms, 2)
                    }
                    for model, s in self.m.llm_latency_ms_by_model.items()
                }
            }
            self.supabase_client.table('system_metrics').insert(metrics_data).execute()
        except Exception as e:
            print(f"Failed to save metrics to database: {e}")

    def record_llm_call(self, provider: str, model: str, success: bool, latency_ms: float):
        """
        Record LLM call metrics with persistent storage
        """
        self.m.llm_calls_total += 1
        self.m.llm_calls_by_provider[provider] += 1
        self.m.llm_calls_by_model[model] += 1
        stats = self.m.llm_latency_ms_by_model.setdefault(model, LatencyStats())
        stats.add(latency_ms)
        if not success:
            self.m.errors_total += 1
        self._save_to_db()

    def record_error(self):
        """Record an error with persistent storage"""
        self.m.errors_total += 1
        self._save_to_db()

    def record_summary_created(self):
        """Record summary creation with persistent storage"""
        self.m.summaries_created += 1
        self._save_to_db()

    def record_consolidation(self, action: str):
        """Record consolidation event with persistent storage"""
        if action.upper() == "ADD":
            self.m.consolidations_added += 1
        elif action.upper() == "UPDATE":
            self.m.consolidations_updated += 1
        self._save_to_db()

    def record_decay(self, updated: int, pruned: int):
        """Record decay event with persistent storage"""
        self.m.decay_updated += int(updated)
        self.m.decay_pruned += int(pruned)
        self._save_to_db()

    def get_metrics(self) -> Dict:
        """
        Get current metrics as dictionary with database sync
        """
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
            "persistent": self._initialized
        }
        return out

    def reset_metrics(self):
        """
        Reset all metrics (for testing purposes)
        """
        self.m = Metrics()
        self._save_to_db()
        return True

# Initialize with dependency injection support
def get_metrics_service(supabase_client=None) -> MetricsService:
    """Factory function to create or get metrics service instance"""
    global metrics
    if supabase_client and not metrics.supabase_client:
        metrics.supabase_client = supabase_client
        metrics._init_db()
    return metrics

# Global instance (lazy initialization)
metrics = MetricsService()
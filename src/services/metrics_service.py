"""
Metrics Service
Enhanced metrics with persistent storage and database integration.
Supports both in-memory tracking and persistent storage via Supabase.

Optimized with async batching to reduce database write frequency.
"""
from __future__ import annotations

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Dict, DefaultDict, Optional
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

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
    """
    Metrics service with optimized async batch persistence.
    
    Features:
    - In-memory metrics collection
    - Async batch persistence to reduce DB load
    - Configurable persistence intervals
    - Automatic background persistence
    """
    
    def __init__(self, supabase_client=None, persist_interval_seconds: int = 60):
        """
        Initialize MetricsService with optional database integration
        
        Args:
            supabase_client: Supabase client for persistence
            persist_interval_seconds: How often to persist to DB (default: 60s)
        """
        self.m = Metrics()
        self.supabase_client = supabase_client
        self._initialized = False
        self._persist_interval = persist_interval_seconds
        self._last_persist_time = 0
        self._pending_changes = False
        self._persist_lock = asyncio.Lock()
        self._background_task = None
        self._shutdown = False
        
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
                # Start background persistence task
                self._start_background_persistence()
        except Exception as e:
            logger.error(f"Metrics database initialization failed: {e}")

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
            logger.error(f"Failed to load metrics from database: {e}")

    def _start_background_persistence(self):
        """Start background task for periodic persistence"""
        if self._background_task is None and self._initialized:
            self._background_task = asyncio.create_task(self._background_persist())
            logger.info(f"Started background metrics persistence (interval: {self._persist_interval}s)")

    async def _background_persist(self):
        """Background task to periodically persist metrics"""
        while not self._shutdown:
            try:
                await asyncio.sleep(self._persist_interval)
                if self._pending_changes:
                    await self._persist_to_db()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Background metrics persistence error: {e}")

    async def _persist_to_db(self):
        """
        Async persist current metrics to database with throttling.
        
        Uses locking to prevent concurrent writes and implements
        debouncing to avoid excessive database operations.
        """
        if not self.supabase_client or not self._initialized:
            return

        async with self._persist_lock:
            # Debounce: don't persist more frequently than interval/2
            time_since_last = time.time() - self._last_persist_time
            if time_since_last < self._persist_interval / 2:
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
                self._last_persist_time = time.time()
                self._pending_changes = False
                logger.debug("Metrics persisted to database")
            except Exception as e:
                logger.error(f"Failed to persist metrics to database: {e}")

    async def persist_metrics(self):
        """
        Public method to trigger immediate metrics persistence.
        
        Use this when you need to ensure metrics are saved immediately,
        such as during graceful shutdown or before a critical operation.
        """
        await self._persist_to_db()

    def record_llm_call(self, provider: str, model: str, success: bool, latency_ms: float):
        """
        Record LLM call metrics.
        
        Updates in-memory metrics immediately, with async batch persistence.
        """
        self.m.llm_calls_total += 1
        self.m.llm_calls_by_provider[provider] += 1
        self.m.llm_calls_by_model[model] += 1
        stats = self.m.llm_latency_ms_by_model.setdefault(model, LatencyStats())
        stats.add(latency_ms)
        if not success:
            self.m.errors_total += 1
        self._pending_changes = True

    def record_error(self):
        """Record an error"""
        self.m.errors_total += 1
        self._pending_changes = True

    def record_summary_created(self):
        """Record summary creation"""
        self.m.summaries_created += 1
        self._pending_changes = True

    def record_consolidation(self, action: str):
        """Record consolidation event"""
        if action.upper() == "ADD":
            self.m.consolidations_added += 1
        elif action.upper() == "UPDATE":
            self.m.consolidations_updated += 1
        self._pending_changes = True

    def record_decay(self, updated: int, pruned: int):
        """Record decay event"""
        self.m.decay_updated += int(updated)
        self.m.decay_pruned += int(pruned)
        self._pending_changes = True

    def get_metrics(self) -> Dict:
        """
        Get current metrics as dictionary.
        
        Note: This returns in-memory metrics which may not yet be persisted.
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
            "persistent": self._initialized,
            "pending_changes": self._pending_changes
        }
        return out

    async def reset_metrics(self):
        """
        Reset all metrics (for testing purposes).
        
        Persists the reset state immediately.
        """
        self.m = Metrics()
        self._pending_changes = True
        await self._persist_to_db()
        return True

    async def shutdown(self):
        """
        Graceful shutdown - persist any pending metrics.
        
        Call this during application shutdown to ensure no metrics are lost.
        """
        self._shutdown = True
        if self._background_task:
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        # Persist any remaining changes
        if self._pending_changes:
            await self._persist_to_db()
        logger.info("Metrics service shutdown complete")


# Initialize with dependency injection support
def get_metrics_service(supabase_client=None, persist_interval_seconds: int = 60) -> MetricsService:
    """
    Factory function to create or get metrics service instance.
    
    Args:
        supabase_client: Supabase client for persistence
        persist_interval_seconds: How often to persist to DB
    """
    global metrics
    if supabase_client and not metrics.supabase_client:
        metrics.supabase_client = supabase_client
        metrics._persist_interval = persist_interval_seconds
        metrics._init_db()
    return metrics


# Global instance (lazy initialization)
metrics = MetricsService()

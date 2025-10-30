"""
Forgetting Mechanisms
Applies time-based decay and optional pruning to long-term memories.
"""
import asyncio
import logging
import math
from datetime import datetime, timedelta, timezone

from src.config.settings import get_settings
from src.dependencies import get_supabase_client

logger = logging.getLogger(__name__)

class MemoryDecayService:
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()
        self._task = None

    def _decay(self, importance: float, days: float) -> float:
        # importance_t = importance_0 * e^(-lambda * days)
        return float(importance) * math.exp(-self.settings.FORGETTING_DECAY_LAMBDA * days)

    async def run_once(self) -> None:
        """Run a single decay/prune pass."""
        try:
            # Fetch a manageable batch
            result = self.supabase.table("long_term_memories").select("id, importance, last_accessed, created_at").limit(1000).execute()
            if not result.data:
                return
            now = datetime.now(timezone.utc)
            pruned = 0
            updated = 0
            for row in result.data:
                last = row.get("last_accessed") or row.get("created_at")
                try:
                    last_dt = datetime.fromisoformat(str(last).replace("Z", "+00:00"))
                except Exception:
                    last_dt = now
                days = (now - last_dt).total_seconds() / 86400
                new_importance = max(0.0, min(1.0, self._decay(row.get("importance", 0.5), days)))
                # Prune if inactive too long and unimportant
                if days >= self.settings.FORGETTING_INACTIVE_DAYS and new_importance < 0.15:
                    self.supabase.table("long_term_memories").delete().eq("id", row["id"]).execute()
                    pruned += 1
                else:
                    self.supabase.table("long_term_memories").update({
                        "importance": new_importance
                    }).eq("id", row["id"]).execute()
                    updated += 1
            if updated or pruned:
                try:
                    from src.services.metrics_service import metrics
                    metrics.record_decay(updated, pruned)
                except Exception:
                    pass
                logger.info(f"🧹 Decay pass complete: updated={updated}, pruned={pruned}")
        except Exception as e:
            logger.warning(f"Decay pass skipped or pending migrations: {e}")

    async def _periodic(self):
        # Run daily
        while True:
            await self.run_once()
            await asyncio.sleep(24 * 3600)

    def start_periodic(self):
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._periodic())

# Global instance
memory_decay_service = MemoryDecayService()
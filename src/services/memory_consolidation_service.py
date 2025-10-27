"""
Memory Consolidation Pipeline
Extracts structured long-term memories asynchronously and maintains an audit trail.

Tables assumed (create via migrations):
- long_term_memories(id, persona_id, session_id, memory_type, content, importance, last_accessed, created_at, updated_at, hash)
- memory_audit_log(id, action, persona_id, session_id, source, content_hash, details, created_at)
"""
import asyncio
import hashlib
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional

from src.config.settings import get_settings
from src.dependencies import get_supabase_client
from src.utils.logging import track_step

logger = logging.getLogger(__name__)

@dataclass
class ConsolidationContext:
    session_id: str
    persona_id: str
    user_message: str
    persona_response: str

class MemoryConsolidationService:
    def __init__(self):
        self.settings = get_settings()
        self.supabase = get_supabase_client()

    async def schedule_consolidation(self, *, session_id: str, persona_id: str,
                                     user_message: str, persona_response: str) -> None:
        """Schedule consolidation after a small delay to keep UX snappy."""
        if not self.settings.ENABLE_MEMORY_CONSOLIDATION:
            return
        ctx = ConsolidationContext(session_id, persona_id, user_message, persona_response)
        asyncio.create_task(self._delayed_consolidate(ctx))

    async def _delayed_consolidate(self, ctx: ConsolidationContext):
        try:
            await asyncio.sleep(self.settings.CONSOLIDATION_DELAY_SECONDS)
            await self._consolidate(ctx)
        except Exception as e:
            logger.error(f"Consolidation task failed: {e}")

    def _hash_content(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _classify_memory_type(self, text: str) -> str:
        """Heuristic classifier; can be replaced with LLM later."""
        lower = text.lower()
        if any(k in lower for k in ["i like", "i prefer", "i love", "i enjoy", "favorite"]):
            return "preference"
        if any(k in lower for k in ["learned that", "means", "is when", "defined as"]):
            return "semantic"
        return "episodic"

    async def _consolidate(self, ctx: ConsolidationContext) -> None:
        context = {"session_id": ctx.session_id}
        async with track_step("memory_consolidation", context):
            # Build candidate from latest turn
            combined = f"User: {ctx.user_message}\nPersona: {ctx.persona_response}"
            content_hash = self._hash_content(combined)
            mem_type = self._classify_memory_type(combined)
            importance = 0.6  # default; could be derived from interaction quality later

            # Upsert into long_term_memories by hash to avoid duplicates
            now = datetime.utcnow().isoformat()
            record = {
                "persona_id": ctx.persona_id,
                "session_id": ctx.session_id,
                "memory_type": mem_type,
                "content": combined,
                "importance": importance,
                "last_accessed": now,
                "created_at": now,
                "updated_at": now,
                "hash": content_hash,
            }
            try:
                # Try update first
                existing = self.supabase.table("long_term_memories").select("id, importance").eq("hash", content_hash).maybe_single().execute()
                if existing.data:
                    mem_id = existing.data["id"]
                    # Bump importance slightly on repeat signal
                    new_importance = min(1.0, float(existing.data.get("importance", 0.5)) * 0.9 + importance * 0.1)
                    self.supabase.table("long_term_memories").update({
                        "importance": new_importance,
                        "last_accessed": now,
                        "updated_at": now
                    }).eq("id", mem_id).execute()
                    action = "UPDATE"
                else:
                    self.supabase.table("long_term_memories").insert(record).execute()
                    action = "ADD"

                # Write audit log
                self._write_audit(action=action, persona_id=ctx.persona_id, session_id=ctx.session_id,
                                  source="conversation_memories", content_hash=content_hash,
                                  details={"memory_type": mem_type, "importance": importance})
                # Metrics
                try:
                    from src.services.metrics_service import metrics
                    metrics.record_consolidation(action)
                except Exception:
                    pass
                logger.info(f"🧠 Consolidated {mem_type} memory ({action}) for session {ctx.session_id}")
            except Exception as e:
                logger.warning(f"Consolidation skipped or pending migrations: {e}")

    def _write_audit(self, *, action: str, persona_id: str, session_id: str,
                     source: str, content_hash: str, details: Optional[Dict] = None) -> None:
        try:
            self.supabase.table("memory_audit_log").insert({
                "action": action,
                "persona_id": persona_id,
                "session_id": session_id,
                "source": source,
                "content_hash": content_hash,
                "details": details or {},
                "created_at": datetime.utcnow().isoformat()
            }).execute()
        except Exception:
            # Non-fatal if audit table not present
            pass

# Global instance
memory_consolidation_service = MemoryConsolidationService()
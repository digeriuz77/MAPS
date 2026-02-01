"""
Character Vector Database Service V2 - Database-Driven
Provides deep character knowledge and situational response variety
ALL persona data loaded from Supabase - NO HARDCODED PERSONAS
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from supabase import Client

logger = logging.getLogger(__name__)


@dataclass
class CharacterMemory:
    """A character's specific memory/knowledge/experience"""
    memory_id: str
    persona_id: str
    memory_type: str  # 'experience', 'knowledge', 'response_pattern', 'emotional_trigger'
    content: str
    context_tags: List[str]  # ['work_stress', 'family_pressure', 'health_concern']
    emotional_weight: float  # 0.0-1.0
    trust_level_required: float  # 0.0-1.0 when this becomes available
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None


class CharacterVectorService:
    """
    Service for storing and retrieving character-specific knowledge, experiences,
    and response patterns to enable deep, varied persona interactions
    LOADS ALL DATA FROM DATABASE - NO HARDCODED PERSONAS
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        # Cache for loaded memories
        self._memory_cache: Dict[str, List[CharacterMemory]] = {}
        self._cache_loaded: Dict[str, bool] = {}

    async def _load_memories_from_db(self, persona_id: str) -> List[CharacterMemory]:
        """Load all memories for a persona from database"""
        if persona_id in self._cache_loaded:
            return self._memory_cache.get(persona_id, [])

        try:
            # Load from character_vector_memories table
            result = self.supabase.table('character_vector_memories')\
                .select('*')\
                .eq('persona_id', persona_id)\
                .execute()

            memories = []
            if result.data:
                for row in result.data:
                    memories.append(CharacterMemory(
                        memory_id=row['memory_id'],
                        persona_id=row['persona_id'],
                        memory_type=row['memory_type'],
                        content=row['content'],
                        context_tags=row.get('context_tags', []),
                        emotional_weight=row.get('emotional_weight', 0.5),
                        trust_level_required=row.get('trust_level_required', 0.0),
                        embedding=row.get('embedding'),
                        created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None
                    ))

            # Cache the results
            self._memory_cache[persona_id] = memories
            self._cache_loaded[persona_id] = True
            logger.debug(f"Loaded {len(memories)} memories for persona {persona_id}")

        except Exception as e:
            logger.error(f"Error loading character memories for {persona_id}: {e}")
            self._memory_cache[persona_id] = []
            self._cache_loaded[persona_id] = True

        return self._memory_cache.get(persona_id, [])

    async def get_relevant_memories(
        self,
        persona_id: str,
        context_tags: List[str],
        trust_level: float,
        limit: int = 10
    ) -> List[CharacterMemory]:
        """
        Get memories relevant to current context that the user has earned access to
        """
        # Load memories from database
        memories = await self._load_memories_from_db(persona_id)

        # Filter by trust level
        accessible_memories = [
            m for m in memories if m.trust_level_required <= trust_level
        ]

        # Score by relevance to context tags
        scored_memories = []
        for memory in accessible_memories:
            # Calculate tag overlap
            if context_tags:
                overlap = len(set(memory.context_tags) & set(context_tags))
                score = overlap + memory.emotional_weight
            else:
                score = memory.emotional_weight
            scored_memories.append((memory, score))

        # Sort by relevance and emotional weight
        scored_memories.sort(key=lambda x: (x[1], x[0].emotional_weight), reverse=True)

        return [memory for memory, _ in scored_memories[:limit]]

    async def get_character_context(
        self,
        persona_id: str,
        user_input: str,
        trust_level: float,
        interaction_quality: str
    ) -> Dict:
        """
        Get comprehensive character context for response generation

        Args:
            persona_id: Character identifier
            user_input: Current user input
            trust_level: Current trust level
            interaction_quality: Interaction quality assessment

        Returns:
            Dictionary with character context for LLM
        """
        # Extract context tags from user input
        context_tags = self._extract_context_tags(user_input)

        # Get relevant memories
        relevant_memories = await self.get_relevant_memories(persona_id, context_tags, trust_level)

        # Build context dictionary
        context = {
            "memories": [
                {
                    "type": m.memory_type,
                    "content": m.content,
                    "emotional_weight": m.emotional_weight,
                    "tags": m.context_tags
                }
                for m in relevant_memories
            ],
            "response_guidance": None
        }

        # Find best response pattern memory for guidance
        response_memories = [m for m in relevant_memories if m.memory_type == 'response_pattern']
        if response_memories:
            best_pattern = response_memories[0]
            context["response_guidance"] = {
                "style": best_pattern.content,
                "emotional_weight": best_pattern.emotional_weight,
                "sharing_level": "high" if best_pattern.trust_level_required < 0.5 else "limited"
            }

        return context

    def _extract_context_tags(self, user_input: str) -> List[str]:
        """Extract context tags from user input"""
        user_lower = user_input.lower()
        tags = []

        # Work-related
        if any(word in user_lower for word in ['work', 'job', 'performance', 'deadline', 'manager', 'boss']):
            tags.append('work_stress')
        if any(word in user_lower for word in ['late', 'behind', 'struggling', 'difficult']):
            tags.append('performance_concern')

        # Family-related
        if any(word in user_lower for word in ['family', 'child', 'children', 'kid', 'son', 'daughter', 'parent']):
            tags.append('family_pressure')
        if any(word in user_lower for word in ['sick', 'health', 'doctor', 'hospital', 'illness']):
            tags.append('health_concern')

        # Emotional
        if any(word in user_lower for word in ['stress', 'worried', 'anxious', 'overwhelmed', 'tired']):
            tags.append('emotional_distress')
        if any(word in user_lower for word in ['help', 'support', 'advice', 'what should']):
            tags.append('seeking_support')

        # Communication style
        if any(word in user_lower for word in ['direct', 'honest', 'blunt', 'straightforward']):
            tags.append('direct_communication')
        if any(word in user_lower for word in ['understand', 'feel', 'empathy', 'caring']):
            tags.append('empathetic_approach')

        return tags

    def clear_cache(self, persona_id: Optional[str] = None):
        """Clear memory cache"""
        if persona_id:
            self._memory_cache.pop(persona_id, None)
            self._cache_loaded.pop(persona_id, None)
            logger.info(f"Cleared memory cache for {persona_id}")
        else:
            self._memory_cache.clear()
            self._cache_loaded.clear()
            logger.info("Cleared all memory caches")


# Global instance (will be initialized with supabase client)
character_vector_service = None


def initialize_character_vector_service(supabase_client: Client):
    """Initialize the global character vector service"""
    global character_vector_service
    character_vector_service = CharacterVectorService(supabase_client)
    return character_vector_service

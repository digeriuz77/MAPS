"""
Character Vector Database Service V2 - Database-Driven
Provides deep character knowledge and situational response variety
ALL persona data loaded from Supabase - NO HARDCODED PERSONAS
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
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

@dataclass
class SituationalResponse:
    """A character's response pattern for specific situations (deprecated - loaded from memories)"""
    response_id: str
    persona_id: str
    situation_tags: List[str]
    trust_level: float
    interaction_quality: str
    response_style: str
    example_responses: List[str]
    emotional_tone: str
    sharing_level: str

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

        logger.info("🎭 Character Vector Service V2 initialized (database-driven)")

    async def _load_memories_from_db(self, persona_id: str) -> List[CharacterMemory]:
        """
        Load character memories from database for a specific persona
        """
        # Check cache first
        if persona_id in self._memory_cache:
            return self._memory_cache[persona_id]

        try:
            # Load from character_vector_memories table
            result = self.supabase.table('character_vector_memories')\
                .select('*')\
                .eq('persona_id', persona_id)\
                .execute()

            if not result.data:
                logger.warning(f"No vector memories found for persona {persona_id}")
                self._memory_cache[persona_id] = []
                return []

            # Convert to CharacterMemory objects
            memories = []
            for row in result.data:
                memory = CharacterMemory(
                    memory_id=row['memory_id'],
                    persona_id=row['persona_id'],
                    memory_type=row['memory_type'],
                    content=row['content'],
                    context_tags=row.get('context_tags', []),
                    emotional_weight=row['emotional_weight'],
                    trust_level_required=row['trust_level_required'],
                    embedding=row.get('embedding_json'),  # JSON array for now
                    created_at=datetime.fromisoformat(row['created_at']) if row.get('created_at') else None
                )
                memories.append(memory)

            # Cache the results
            self._memory_cache[persona_id] = memories
            self._cache_loaded[persona_id] = True

            logger.info(f"Loaded {len(memories)} vector memories for {persona_id}")
            return memories

        except Exception as e:
            logger.error(f"Error loading memories for {persona_id}: {e}")
            self._memory_cache[persona_id] = []
            return []

    async def get_relevant_memories(self, persona_id: str, context_tags: List[str],
                            trust_level: float, limit: int = 5) -> List[CharacterMemory]:
        """
        Retrieve character memories relevant to current context and trust level

        Args:
            persona_id: Character identifier
            context_tags: Current conversation context tags
            trust_level: Current trust level (0.0-1.0)
            limit: Maximum memories to return

        Returns:
            List of relevant character memories
        """
        # Load memories from database
        memories = await self._load_memories_from_db(persona_id)

        if not memories:
            return []

        # Filter by trust level
        accessible_memories = [
            m for m in memories if m.trust_level_required <= trust_level
        ]

        # Score by relevance to context tags
        scored_memories = []
        for memory in accessible_memories:
            relevance_score = len(set(memory.context_tags) & set(context_tags))
            if relevance_score > 0:
                scored_memories.append((memory, relevance_score))

        # Sort by relevance and emotional weight
        scored_memories.sort(key=lambda x: (x[1], x[0].emotional_weight), reverse=True)

        return [memory for memory, _ in scored_memories[:limit]]

    async def get_situational_response(self, persona_id: str, situation_tags: List[str],
                               trust_level: float, interaction_quality: str) -> Optional[SituationalResponse]:
        """
        Get appropriate response pattern for current situation
        NOTE: SituationalResponse is now deprecated - memories of type 'response_pattern' used instead

        Args:
            persona_id: Character identifier
            situation_tags: Current situation context
            trust_level: Current trust level
            interaction_quality: Quality of interaction so far

        Returns:
            Matching situational response or None (converted from response_pattern memories)
        """
        # Load memories and filter for response_pattern type
        memories = await self._load_memories_from_db(persona_id)
        response_memories = [m for m in memories if m.memory_type == 'response_pattern']

        if not response_memories:
            return None

        # Find best matching response memory
        best_match = None
        best_score = 0

        for memory in response_memories:
            # Check trust level compatibility (within 0.2 range)
            trust_diff = abs(memory.trust_level_required - trust_level)
            if trust_diff > 0.2:
                continue

            # Score situation tag overlap
            tag_overlap = len(set(memory.context_tags) & set(situation_tags))
            if tag_overlap > best_score:
                best_score = tag_overlap
                best_match = memory

        # Convert to SituationalResponse format if match found
        if best_match:
            return SituationalResponse(
                response_id=best_match.memory_id,
                persona_id=best_match.persona_id,
                situation_tags=best_match.context_tags,
                trust_level=best_match.trust_level_required,
                interaction_quality=interaction_quality,
                response_style=best_match.content,  # Content describes response style
                example_responses=[best_match.content],
                emotional_tone="neutral",  # Could be derived from emotional_weight
                sharing_level="moderate"  # Could be derived from trust_level_required
            )

        return None

    async def get_character_context(self, persona_id: str, user_input: str,
                            trust_level: float, interaction_quality: str) -> Dict:
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

        # Get situational response pattern
        situation_tags = self._extract_situation_tags(user_input, interaction_quality)
        response_pattern = await self.get_situational_response(persona_id, situation_tags, trust_level, interaction_quality)

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

        if response_pattern:
            context["response_guidance"] = {
                "style": response_pattern.response_style,
                "emotional_tone": response_pattern.emotional_tone,
                "sharing_level": response_pattern.sharing_level,
                "example_approaches": response_pattern.example_responses[:2]  # Limit examples
            }

        return context

    def _extract_context_tags(self, user_input: str) -> List[str]:
        """
        Extract context tags from user input
        Simple keyword matching for MVP (could be enhanced with LLM/embeddings)
        """
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

    def _extract_situation_tags(self, user_input: str, interaction_quality: str) -> List[str]:
        """
        Extract situation-specific tags considering interaction quality
        """
        tags = self._extract_context_tags(user_input)  # Start with context tags

        user_lower = user_input.lower()

        # Add situation-specific tags
        if any(word in user_lower for word in ['criticism', 'wrong', 'mistake', 'error', 'problem']):
            tags.append('criticism')
        if any(word in user_lower for word in ['achievement', 'success', 'good job', 'well done']):
            tags.append('praise')
        if any(word in user_lower for word in ['why', 'how', 'explain', 'understand']):
            tags.append('seeking_understanding')

        # Consider interaction quality
        if interaction_quality in ['poor', 'adequate']:
            tags.append('defensive_situation')
        elif interaction_quality in ['good', 'excellent']:
            tags.append('open_situation')

        return tags

    def clear_cache(self, persona_id: Optional[str] = None):
        """
        Clear memory cache

        Args:
            persona_id: If provided, clear only this persona's cache. Otherwise clear all.
        """
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

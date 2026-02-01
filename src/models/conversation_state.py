"""
Conversation State Management for Natural Persona Interactions
"""

from dataclasses import dataclass
from typing import List, Dict
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Track conversation stage and emotional progression"""
    session_id: str
    stage: str  # "defensive", "cautious", "building_rapport", "opening_up", "full_trust"
    trust_level: float  # 0.0-1.0 normalized trust level
    key_topics: List[str]  # Tracked topics for continuity
    turn_count: int
    emotional_trajectory: List[Dict]  # Track emotional arc over time
    last_updated: datetime

    def __post_init__(self):
        if not self.emotional_trajectory:
            self.emotional_trajectory = []


@dataclass
class EmotionalPoint:
    """Single point in emotional trajectory"""
    turn_number: int
    openness_level: float  # 0-10
    resistance_level: float  # 0-10
    trust_delta: float  # Change from previous turn
    empathy_score: float
    dominant_emotion: str  # "defensive", "opening", "engaged", "resistant"


class ConversationStateManager:
    """Manages conversation state progression and emotional tracking"""

    def __init__(self, supabase_client, trust_config_service=None):
        self.supabase = supabase_client
        self._state_cache = {}
        if trust_config_service is None:
            from src.services.trust_configuration_service import TrustConfigurationService
            self.trust_config_service = TrustConfigurationService(supabase_client)
        else:
            self.trust_config_service = trust_config_service

    async def get_conversation_state(self, session_id: str, persona_id: str = None) -> ConversationState:
        """Get current conversation state"""
        if session_id in self._state_cache:
            return self._state_cache[session_id]

        # Get persona-specific starting trust level from database
        starting_trust = 0.3  # Default fallback
        if persona_id:
            try:
                result = self.supabase.table('enhanced_personas').select('trust_starting_level').eq(
                    'persona_id', persona_id
                ).execute()

                if result.data and len(result.data) > 0:
                    starting_trust = result.data[0].get('trust_starting_level', 0.3)
                    logger.info(f"Starting conversation with {persona_id} at trust_level={starting_trust:.2f}")
                else:
                    logger.warning(f"No persona data found for {persona_id}, using default 0.3")
            except Exception as e:
                logger.warning(f"Could not get starting trust for {persona_id}: {e}, using default 0.3")

        state = ConversationState(
            session_id=session_id,
            stage="defensive",
            trust_level=starting_trust,
            key_topics=[],
            turn_count=0,
            emotional_trajectory=[],
            last_updated=datetime.now()
        )

        self._state_cache[session_id] = state
        return state

    async def update_conversation_state(
        self,
        session_id: str,
        interaction_context,
        user_message: str,
        persona_id: str = None
    ) -> ConversationState:
        """Update conversation state based on latest interaction"""
        state = await self.get_conversation_state(session_id)
        state.turn_count += 1

        # Calculate trust delta using database configuration
        trust_delta = await self._calculate_trust_delta(interaction_context, state, persona_id)
        state.trust_level = max(0.0, min(1.0, state.trust_level + trust_delta))

        # Calculate emotional metrics
        openness_level = self._calculate_openness(interaction_context, state)
        resistance_level = self._calculate_resistance(interaction_context, state)
        dominant_emotion = self._determine_dominant_emotion(
            openness_level, resistance_level, trust_delta
        )

        # Add emotional trajectory point
        emotional_point = EmotionalPoint(
            turn_number=state.turn_count,
            openness_level=openness_level,
            resistance_level=resistance_level,
            trust_delta=trust_delta,
            empathy_score=self._get_empathy_score(interaction_context),
            dominant_emotion=dominant_emotion
        )
        state.emotional_trajectory.append(emotional_point.__dict__)

        # Keep only last 10 emotional points
        if len(state.emotional_trajectory) > 10:
            state.emotional_trajectory = state.emotional_trajectory[-10:]

        # Update conversation stage
        state.stage = self._determine_conversation_stage(state)

        # Extract key topics
        new_topics = self._extract_topics(user_message)
        state.key_topics = list(set(state.key_topics + new_topics))[:20]

        state.last_updated = datetime.now()
        return state

    def _get_empathy_score(self, interaction_context) -> float:
        """Extract empathy score from interaction context"""
        quality_scores = {
            "excellent": 9.0,
            "good": 7.5,
            "adequate": 5.5,
            "poor": 3.0
        }
        base_score = quality_scores.get(interaction_context.interaction_quality, 5.0)

        # Adjust based on empathy tone
        if interaction_context.empathy_tone == "supportive":
            base_score += 0.5
        elif interaction_context.empathy_tone == "hostile":
            base_score -= 2.0

        return max(0.0, min(10.0, base_score))

    def _calculate_openness(self, interaction_context, state: ConversationState) -> float:
        """Calculate openness level based on trust and interaction"""
        base_openness = state.trust_level * 10  # Convert 0-1 to 0-10

        if interaction_context.trust_trajectory == 'building':
            base_openness += 1.0
        elif interaction_context.trust_trajectory == 'declining':
            base_openness -= 1.0

        return max(0.0, min(10.0, base_openness))

    def _calculate_resistance(self, interaction_context, state: ConversationState) -> float:
        """Calculate resistance level based on empathy and techniques"""
        empathy_score = self._get_empathy_score(interaction_context)
        base_resistance = 10 - empathy_score

        techniques_used = getattr(interaction_context, 'techniques_used', [])
        if 'advice' in techniques_used or 'closed_question' in techniques_used:
            base_resistance += 1.5

        return min(10.0, max(0.0, base_resistance))

    async def _calculate_trust_delta(
        self,
        interaction_context,
        state: ConversationState,
        persona_id: str = None
    ) -> float:
        """Calculate trust delta using persona-specific configuration from database"""
        if persona_id is None:
            logger.warning("No persona_id provided, using default delta")
            return self._get_default_delta(interaction_context)

        try:
            trust_config = self.trust_config_service.get_persona_trust_config(persona_id)
            trust_delta = self.trust_config_service.calculate_trust_delta(
                quality=interaction_context.interaction_quality,
                empathy_tone=interaction_context.empathy_tone,
                approach=interaction_context.user_approach,
                trajectory=interaction_context.trust_trajectory,
                trust_config=trust_config
            )
            return trust_delta
        except Exception as e:
            logger.error(f"Failed to get trust delta from DB for {persona_id}: {e}")
            return self._get_default_delta(interaction_context)

    def _get_default_delta(self, interaction_context) -> float:
        """Get default trust delta based on interaction quality"""
        quality_deltas = {
            "excellent": 0.015,
            "good": 0.010,
            "adequate": 0.005,
            "poor": -0.015
        }
        return quality_deltas.get(interaction_context.interaction_quality, 0.0)

    def _determine_dominant_emotion(self, openness: float, resistance: float, trust_delta: float) -> str:
        """Determine dominant emotional state"""
        if resistance > 7.0:
            return "resistant"
        elif trust_delta > 0.02:
            return "opening"
        elif openness > 7.0 and resistance < 3.0:
            return "engaged"
        elif trust_delta < -0.01:
            return "defensive"
        else:
            return "neutral"

    def _determine_conversation_stage(self, state: ConversationState) -> str:
        """Determine conversation stage based on trust level"""
        if state.trust_level < 0.3:
            return "defensive"
        elif state.trust_level < 0.5:
            return "cautious"
        elif state.trust_level < 0.75:
            return "building_rapport"
        elif state.trust_level < 0.9:
            return "opening_up"
        else:
            return "full_trust"

    def _extract_topics(self, user_message: str) -> List[str]:
        """Simple topic extraction from user message"""
        topic_keywords = {
            'work': ['job', 'work', 'career', 'boss', 'colleague', 'office'],
            'family': ['family', 'parent', 'child', 'spouse', 'relationship'],
            'health': ['health', 'doctor', 'sick', 'medical', 'therapy'],
            'anxiety': ['anxiety', 'worry', 'stress', 'nervous', 'panic'],
            'depression': ['depression', 'sad', 'down', 'hopeless', 'empty'],
            'goals': ['goal', 'future', 'plan', 'want', 'hope', 'dream']
        }

        message_lower = user_message.lower()
        detected_topics = []

        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                detected_topics.append(topic)

        return detected_topics

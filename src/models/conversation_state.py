"""
Conversation State Management for Natural Persona Interactions
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class ConversationState:
    """Track conversation stage and emotional progression"""
    session_id: str
    stage: str  # "building_rapport", "exploring", "deepening", "action_planning"
    trust_level: float  # 0.0-1.0 normalized trust level (not 0-10!)
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
        # Import here to avoid circular dependency
        if trust_config_service is None:
            from src.services.trust_configuration_service import TrustConfigurationService
            self.trust_config_service = TrustConfigurationService(supabase_client)
        else:
            self.trust_config_service = trust_config_service
    
    async def get_conversation_state(self, session_id: str, persona_id: str = None) -> ConversationState:
        """Get current conversation state"""
        if session_id in self._state_cache:
            return self._state_cache[session_id]

        # Try to load from database (if we add a conversation_state table later)
        # For now, create default state

        # Get persona-specific starting trust level if persona_id provided
        starting_trust = 0.3  # Default fallback
        if persona_id:
            try:
                trust_config = await self.trust_config_service.get_persona_trust_config(persona_id)
                starting_trust = trust_config.trust_starting_level
                logger.info(f"Starting conversation with {persona_id} at trust_level={starting_trust:.2f} (persona-specific)")
            except Exception as e:
                logger.warning(f"Could not get persona trust config for {persona_id}: {e}, using default 0.3")

        state = ConversationState(
            session_id=session_id,
            stage="defensive",  # Start defensive - trust must be earned
            trust_level=starting_trust,  # Persona-specific starting trust
            key_topics=[],
            turn_count=0,
            emotional_trajectory=[],
            last_updated=datetime.now()
        )

        self._state_cache[session_id] = state
        return state
    
    async def update_conversation_state(self, session_id: str, mi_analysis: Dict, user_message: str, persona_id: str = None) -> ConversationState:
        """Update conversation state based on latest interaction"""
        state = await self.get_conversation_state(session_id)
        state.turn_count += 1
        
        empathy_score = mi_analysis.get('empathy_score', 5)
        openness_change = mi_analysis.get('openness_change', 'same')
        
        # Calculate emotional metrics
        openness_level = self._calculate_openness(mi_analysis, state)
        resistance_level = self._calculate_resistance(mi_analysis, state)
        trust_delta = await self._calculate_trust_delta_from_db(empathy_score, state, persona_id)
        
        # STAGED SYSTEM: Apply calculated trust delta
        state.trust_level = max(0.0, min(1.0, state.trust_level + trust_delta))
        
        # Add emotional trajectory point
        emotional_point = EmotionalPoint(
            turn_number=state.turn_count,
            openness_level=openness_level,
            resistance_level=resistance_level,
            trust_delta=trust_delta,
            empathy_score=empathy_score,
            dominant_emotion=self._determine_dominant_emotion(openness_level, resistance_level, trust_delta)
        )
        
        state.emotional_trajectory.append(emotional_point.__dict__)
        
        # Keep only last 10 emotional points to prevent memory bloat
        if len(state.emotional_trajectory) > 10:
            state.emotional_trajectory = state.emotional_trajectory[-10:]
        
        # Update conversation stage
        state.stage = self._determine_conversation_stage(state)
        
        # Extract key topics (simple keyword extraction)
        new_topics = self._extract_topics(user_message)
        for topic in new_topics:
            if topic not in state.key_topics and len(state.key_topics) < 5:
                state.key_topics.append(topic)
        
        state.last_updated = datetime.now()
        self._state_cache[session_id] = state
        
        return state
    
    def _calculate_openness(self, mi_analysis: Dict, state: ConversationState) -> float:
        """Calculate current openness level (0-10)"""
        empathy_score = mi_analysis.get('empathy_score', 5)
        openness_change = mi_analysis.get('openness_change', 'same')
        
        # Base openness from trust level
        base_openness = state.trust_level
        
        # Adjust based on current interaction
        if openness_change == 'increase':
            return min(10.0, base_openness + 1.5)
        elif openness_change == 'decrease':
            return max(0.0, base_openness - 2.0)
        else:
            return base_openness
    
    def _calculate_resistance(self, mi_analysis: Dict, state: ConversationState) -> float:
        """Calculate current resistance level (0-10)"""
        empathy_score = mi_analysis.get('empathy_score', 5)
        techniques_used = mi_analysis.get('techniques_used', [])
        
        # High empathy = low resistance
        base_resistance = 10 - empathy_score
        
        # Adjust for problematic techniques
        if 'advice' in techniques_used or 'closed_question' in techniques_used:
            base_resistance += 1.5
        
        return min(10.0, max(0.0, base_resistance))
    
    def _calculate_trust_delta(self, empathy_score: float, state: ConversationState) -> float:
        """Calculate change in trust from previous interaction (LEGACY - not used in staged system)"""
        if not state.emotional_trajectory:
            return 0.0
        
        previous_empathy = state.emotional_trajectory[-1].get('empathy_score', 5.0)
        return empathy_score - previous_empathy
    
    def _calculate_trust_delta_staged(self, empathy_score: float, state: ConversationState) -> float:
        """LEGACY: Hardcoded trust deltas (replaced by _calculate_trust_delta_from_db)"""
        logger.warning("Using legacy hardcoded trust deltas - should use persona-specific deltas from DB")
        if empathy_score >= 8.5:
            trust_delta = +0.015  # Scaled to 0.0-1.0 range
        elif empathy_score >= 7.0:
            trust_delta = +0.010
        elif empathy_score >= 5.0:
            trust_delta = +0.005
        elif empathy_score < 4.0:
            trust_delta = -0.015
        else:
            trust_delta = 0.0
        
        return trust_delta
    
    async def _calculate_trust_delta_from_db(self, empathy_score: float, state: ConversationState, persona_id: str = None) -> float:
        """Calculate trust delta using persona-specific configuration from database"""
        if persona_id is None:
            logger.warning("No persona_id provided, using legacy hardcoded deltas")
            return self._calculate_trust_delta_staged(empathy_score, state)
        
        try:
            # Get persona-specific trust configuration from database
            trust_config = await self.trust_config_service.get_persona_trust_config(persona_id)
            
            # Calculate delta using TrustConfigurationService
            trust_delta = self.trust_config_service.calculate_trust_delta(empathy_score, trust_config)
            
            logger.debug(f"Calculated trust_delta={trust_delta:.3f} for empathy={empathy_score:.1f} using persona {persona_id}")
            return trust_delta
            
        except Exception as e:
            logger.error(f"Failed to get trust delta from DB for persona {persona_id}: {e}, using legacy fallback")
            return self._calculate_trust_delta_staged(empathy_score, state)
    
    def _determine_dominant_emotion(self, openness: float, resistance: float, trust_delta: float) -> str:
        """Determine dominant emotional state"""
        if resistance > 7.0:
            return "resistant"
        elif trust_delta > 0.02:  # Scaled to 0.0-1.0 range (was 2.0)
            return "opening"
        elif openness > 7.0 and resistance < 3.0:
            return "engaged"
        elif trust_delta < -0.01:  # Scaled to 0.0-1.0 range (was -1.0)
            return "defensive"
        else:
            return "neutral"
    
    def _determine_conversation_stage(self, state: ConversationState) -> str:
        """
        Determine conversation stage based on trust level (0.0-1.0 scale)
        Trust must be earned - personas start defensive with strangers
        """
        if state.trust_level < 0.3:
            return "defensive"  # Guarded, minimal sharing
        elif state.trust_level < 0.5:
            return "cautious"  # Surface-level engagement
        elif state.trust_level < 0.75:
            return "building_rapport"  # Testing trust, sharing work challenges
        elif state.trust_level < 0.9:
            return "opening_up"  # Sharing family concerns, vulnerability
        else:
            return "full_trust"  # Complete vulnerability, ready for partnership
    
    def _extract_topics(self, user_message: str) -> List[str]:
        """Simple topic extraction from user message"""
        # Simple keyword-based topic extraction
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
    

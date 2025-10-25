"""
LLM-Powered Interaction Analysis
Replaces hard-coded pattern matching with intelligent LLM analysis
"""

import logging
import json
from typing import Dict, List, Optional
from dataclasses import dataclass

from src.services.model_provider_service import multi_model_service

logger = logging.getLogger(__name__)

@dataclass
class InteractionContext:
    """Rich context for persona interactions"""
    empathy_tone: str  # "hostile", "neutral", "supportive", "deeply_empathetic"
    interaction_quality: str  # "poor", "adequate", "good", "excellent"
    emotional_safety: bool
    user_approach: str  # "directive", "questioning", "reflective", "collaborative"
    trust_trajectory: str  # "declining", "stable", "building", "breakthrough"

class LLMInteractionAnalyzer:
    """
    Intelligent interaction analyzer using LLM understanding
    Drop-in replacement for EmotionalStateTracker with same interface
    """
    
    def __init__(self):
        self.emotional_memory_window = 5  # Remember last 5 interactions
    
    async def assess_interaction_quality(self, user_message: str, conversation_history: List[Dict]) -> InteractionContext:
        """
        Assess interaction quality using LLM analysis instead of pattern matching
        Returns same InteractionContext as before for compatibility
        """
        try:
            # Analyze user's communication approach
            user_approach = await self._detect_communication_approach(user_message)
            empathy_tone = await self._assess_empathy_tone(user_message, user_approach)
            emotional_safety = await self._assess_emotional_safety(user_message, empathy_tone)
            
            # Determine overall interaction quality
            interaction_quality = await self._determine_interaction_quality(empathy_tone, user_approach, emotional_safety)
            
            # Assess trust trajectory based on recent pattern
            trust_trajectory = await self._assess_trust_trajectory(conversation_history, empathy_tone)
            
            logger.info(f"🔍 LLM Analysis - Approach: {user_approach}, Empathy: {empathy_tone}, Quality: {interaction_quality}")
            
            return InteractionContext(
                empathy_tone=empathy_tone,
                interaction_quality=interaction_quality,
                emotional_safety=emotional_safety,
                user_approach=user_approach,
                trust_trajectory=trust_trajectory
            )
            
        except Exception as e:
            logger.error(f"LLM interaction analysis failed: {e}, falling back to neutral assessment")
            # Fallback to safe defaults
            return InteractionContext(
                empathy_tone="neutral",
                interaction_quality="adequate", 
                emotional_safety=True,
                user_approach="neutral",
                trust_trajectory="stable"
            )

    async def _detect_communication_approach(self, message: str) -> str:
        """
        Use LLM to detect communication approach instead of keyword matching.
        Returns: "collaborative", "reflective", "directive", "questioning", or "neutral"
        """
        
        prompt = f"""Analyze this message from someone talking to a stressed, defensive employee:

Message: "{message}"

Classify the communication approach as ONE of these:
- collaborative (partnership language: "let's", "together", "what do you think", "help me understand")
- reflective (reflective listening: "it sounds like", "you mentioned", "what I'm hearing", "that must be")
- directive (telling/advising: "you should", "why don't you", "have you tried", "the best thing")
- questioning (asking questions, can be supportive or intrusive depending on tone)
- neutral (none of the above, matter-of-fact statements)

Consider the overall intent and tone, not just individual words.

Respond with ONLY the classification word, nothing else."""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistent classification
                max_tokens=20,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            classification = response.strip().lower()
            
            # Validate it's one of our expected values
            valid_approaches = ["collaborative", "reflective", "directive", "questioning", "neutral"]
            
            if classification in valid_approaches:
                return classification
            
            # Fallback if response is unexpected
            logger.warning(f"Unexpected approach classification: {classification}, defaulting to neutral")
            return "neutral"
            
        except Exception as e:
            logger.error(f"Communication approach analysis failed: {e}, falling back to neutral")
            return "neutral"

    async def _assess_empathy_tone(self, message: str, approach: str) -> str:
        """
        Use LLM to assess empathy tone.
        Returns: "hostile", "neutral", "supportive", or "deeply_empathetic"
        """
        
        prompt = f"""Rate the empathy level in this message to a stressed employee:

Message: "{message}"
Communication approach: {approach}

Classify empathy level as ONE of these:
- hostile (aggressive, blaming, dismissive, insulting, "what's wrong with you", "that's ridiculous")
- neutral (matter-of-fact, no particular warmth or coldness, professional but not empathetic)
- supportive (understanding, validating, "I understand", "that makes sense", "tell me more")
- deeply_empathetic (deeply validating, "that sounds so hard", "you've been through so much", acknowledging pain/struggle)

Focus on the emotional tone and intent behind the words.

Respond with ONLY the classification word, nothing else."""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=20,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            tone = response.strip().lower().replace("_", " ")
            
            valid_tones = ["hostile", "neutral", "supportive", "deeply_empathetic", "deeply empathetic"]
            
            if tone in valid_tones:
                return tone.replace(" ", "_")  # Normalize to underscore format
            
            logger.warning(f"Unexpected empathy tone: {tone}, defaulting to neutral")
            return "neutral"
            
        except Exception as e:
            logger.error(f"Empathy assessment failed: {e}, falling back to neutral")
            return "neutral"

    async def _assess_emotional_safety(self, message: str, empathy_tone: str) -> bool:
        """
        Use LLM to determine emotional safety.
        Returns True if interaction feels safe, False if unsafe.
        """
        
        # Quick check: hostile tone is always unsafe
        if empathy_tone == "hostile":
            return False
        
        prompt = f"""Does this message create emotional safety for a stressed, defensive employee?

Message: "{message}"

Emotional safety means:
- No judgment, criticism, or blame
- No dismissiveness ("get over it", "not a big deal", "everyone has problems")
- No pressure or demands ("you should just", "calm down")
- Person feels heard and respected
- No invalidation of their feelings ("you're overreacting", "it's all in your head")

Answer with ONLY: "safe" or "unsafe"
"""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=10,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            result = response.strip().lower()
            return result == "safe"
            
        except Exception as e:
            logger.error(f"Safety assessment failed: {e}, defaulting to True")
            return True  # Default to safe on error

    async def _determine_interaction_quality(
        self, 
        empathy_tone: str, 
        approach: str, 
        emotional_safety: bool
    ) -> str:
        """
        Use LLM to determine overall interaction quality.
        Returns: "poor", "adequate", "good", or "excellent"
        """
        
        prompt = f"""Rate the quality of this motivational interviewing interaction:

Communication approach: {approach}
Empathy tone: {empathy_tone}  
Emotionally safe: {emotional_safety}

Rate as ONE of: poor, adequate, good, excellent

Criteria:
- poor: hostile tone, unsafe, directive without empathy, dismissive
- adequate: neutral tone, safe but not particularly empathetic, basic interaction
- good: supportive or empathetic tone, some good techniques (reflective listening, validation)
- excellent: deeply empathetic, collaborative/reflective approach, creates strong emotional safety

Respond with ONLY the rating word."""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=10,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            quality = response.strip().lower()
            
            if quality in ["poor", "adequate", "good", "excellent"]:
                return quality
            
            logger.warning(f"Unexpected quality rating: {quality}, defaulting to adequate")
            return "adequate"
            
        except Exception as e:
            logger.error(f"Quality assessment failed: {e}, falling back to adequate")
            return "adequate"

    async def _assess_trust_trajectory(self, conversation_history: List[Dict], current_empathy: str) -> str:
        """
        Assess whether trust is building or declining over recent interactions
        Uses LLM to analyze conversation patterns
        """
        
        if len(conversation_history) < 4:  # Not enough history
            if current_empathy in ["deeply_empathetic", "supportive"]:
                return "building"
            elif current_empathy == "hostile":
                return "declining"
            return "stable"
        
        # Get recent user messages for pattern analysis
        recent_user_messages = [
            msg['content'] for msg in conversation_history[-6:] 
            if msg.get('role') == 'user'
        ][-3:]  # Last 3 user messages max
        
        if not recent_user_messages:
            return "stable"
        
        # Combine recent messages for context
        conversation_context = "\n".join([f"Message {i+1}: {msg}" for i, msg in enumerate(recent_user_messages)])
        
        prompt = f"""Analyze this sequence of messages from someone talking to a stressed employee:

{conversation_context}

Current message empathy level: {current_empathy}

How is the trust/rapport trajectory progressing?

Classify as ONE of:
- declining (becoming more hostile, directive, dismissive, or impatient over time)
- stable (consistent tone, no significant change in empathy or approach)  
- building (becoming more empathetic, understanding, or supportive over time)
- breakthrough (significant positive shift, deeply empathetic after previous struggles)

Look for patterns in tone, empathy, and approach across the messages.

Respond with ONLY the classification word."""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=15,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            trajectory = response.strip().lower()
            
            valid_trajectories = ["declining", "stable", "building", "breakthrough"]
            
            if trajectory in valid_trajectories:
                return trajectory
            
            logger.warning(f"Unexpected trust trajectory: {trajectory}, defaulting to stable")
            return "stable"
            
        except Exception as e:
            logger.error(f"Trust trajectory assessment failed: {e}, falling back to stable")
            return "stable"

    # Optional: Add belief checking if needed later
    async def _check_beliefs_addressed(self, message: str, persona_beliefs: Dict[str, str]) -> Dict:
        """
        Use LLM to check if specific persona beliefs are addressed.
        This is optional - can be added if the persona system needs it.
        """
        
        if not persona_beliefs:
            return {
                "beliefs_addressed": {},
                "count": 0,
                "any_addressed": False
            }
        
        beliefs_list = "\n".join([f"- {key}: {desc}" for key, desc in persona_beliefs.items()])
        
        prompt = f"""A trainee is talking to a resistant employee who has these core beliefs/concerns:

{beliefs_list}

Trainee's message: "{message}"

For each belief, determine if the trainee's message addresses it (acknowledges it, validates it, or offers concrete help for it).

Respond with ONLY a JSON object in this exact format:
{{
    "{list(persona_beliefs.keys())[0] if persona_beliefs else 'example'}": true,
    "{list(persona_beliefs.keys())[1] if len(persona_beliefs) > 1 else 'example2'}": false
}}

Be strict: only mark true if the message ACTUALLY addresses that specific belief/concern."""

        try:
            response_obj = await multi_model_service.generate_response(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
                use_case="fast_feedback"
            )
            response = response_obj.content
            
            # Parse JSON response
            beliefs_addressed = json.loads(response.strip())
            
            return {
                "beliefs_addressed": beliefs_addressed,
                "count": sum(beliefs_addressed.values()),
                "any_addressed": any(beliefs_addressed.values())
            }
            
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Beliefs check failed: {e}")
            # Fallback: assume nothing addressed
            return {
                "beliefs_addressed": {key: False for key in persona_beliefs.keys()},
                "count": 0,
                "any_addressed": False
            }

# Global instance for compatibility
llm_interaction_analyzer = LLMInteractionAnalyzer()
"""
Interaction Analyzer - Analyzes single turns against MAPS rubric

Provides structured analysis of manager-persona interactions including:
- MI techniques used
- MAPS dimension scores
- Behaviors detected
- State trajectory
"""

import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)


@dataclass
class InteractionAnalysis:
    """Structured analysis of a single turn"""
    mi_techniques_used: List[str]  # ["reflection", "open_question", "advice", etc.]
    maps_scores: Dict[str, float]  # {"empathy": 4.0, "autonomy": 3.5, ...}
    behaviors_detected: Dict[str, bool]  # {"unsolicited_advice": True, "reflection": True}
    state_trajectory: str  # "trust_increased", "trust_stable", "resistance_triggered"
    feedback_notes: Optional[str] = None  # Notes for feedback generator
    
    def to_dict(self) -> Dict:
        return asdict(self)


class InteractionAnalyzer:
    """
    Analyzes single turns against MAPS rubric.
    
    Simplified from the full conversation analyzer to focus on
    real-time, single-turn analysis.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def analyze_turn(
        self,
        manager_message: str,
        persona_response: str,
        persona_state_change: Dict[str, Any],
        rubric: Dict[str, Any]
    ) -> InteractionAnalysis:
        """
        Analyze a single interaction turn.
        
        Args:
            manager_message: What the manager said
            persona_response: How the persona responded
            persona_state_change: How the persona state changed
            rubric: MAPS rubric for scoring
            
        Returns:
            InteractionAnalysis with scores and detected behaviors
        """
        # Build analysis prompt
        prompt = self._build_analysis_prompt(
            manager_message, persona_response, persona_state_change, rubric
        )
        
        try:
            # Request structured JSON response
            response_obj = await self.llm.structured_completion(
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistent analysis
                max_tokens=500,
                use_case="interaction_analysis",
                response_format="json"
            )
            
            # Parse structured response
            analysis_data = self._parse_analysis_response(response_obj.content)
            
            return InteractionAnalysis(
                mi_techniques_used=analysis_data.get("mi_techniques", []),
                maps_scores=analysis_data.get("maps_scores", {}),
                behaviors_detected=analysis_data.get("behaviors", {}),
                state_trajectory=analysis_data.get("state_trajectory", "stable"),
                feedback_notes=analysis_data.get("feedback_notes")
            )
            
        except Exception as e:
            logger.error(f"LLM interaction analysis failed: {e}")
            # Return fallback analysis
            return self._get_fallback_analysis(manager_message)
    
    def _build_analysis_prompt(
        self,
        manager_message: str,
        persona_response: str,
        persona_state_change: Dict[str, Any],
        rubric: Dict[str, Any]
    ) -> str:
        """Build prompt for interaction analysis"""
        
        dimensions = rubric.get("dimensions", [])
        dimension_text = ""
        for dim in dimensions:
            dimension_text += f"- {dim['name']} (weight: {dim['weight']})\n"
        
        previous_trust = persona_state_change.get("previous_trust", 4)
        new_trust = persona_state_change.get("trust_level", 4)
        
        if new_trust > previous_trust:
            trajectory = "trust_increased"
        elif new_trust < previous_trust:
            trajectory = "trust_decreased"
        else:
            trajectory = "stable"
        
        prompt = f"""Analyze this interaction for MI (Motivational Interviewing) quality.

=== MANAGER'S MESSAGE ===
"{manager_message}"

=== PERSONA'S RESPONSE ===
"{persona_response}"

=== STATE CHANGE ===
Trust level: {previous_trust} → {new_trust} ({trajectory})
Resistance active: {persona_state_change.get("resistance_active", False)}

=== MAPS RUBRIC DIMENSIONS ===
{dimension_text}

=== ANALYSIS REQUIRED ===
Classify the manager's communication:

1. MI TECHNIQUES USED (check all that apply):
   - open_question: Open-ended question inviting exploration
   - complex_reflection: Reflection that adds meaning/feeling
   - simple_reflection: Reflection that repeats/paraphrases
   - affirmation: Positive acknowledgment of the person
   - summarization: Summary of what's been discussed
   - giving_advice: Giving information or advice (neutral or negative)
   - closed_question: Question with yes/no answer (neutral)
   - other: Anything else

2. MAPS SCORES (1-5 scale, 5 = excellent):
   Rate each dimension based on the interaction quality.

3. BEHAVIORS DETECTED:
   - unsolicited_advice: Giving advice without permission
   - reflection: Using reflective listening
   - empathy: Showing understanding of feelings
   - autonomy_support: Supporting the person's choice
   - confrontation: Challenging or arguing
   - fix_mode: Trying to fix the person's problems
   - permission_asking: Asking before giving advice/exploring

4. STATE TRAJECTORY:
   - trust_increased: Trust went up
   - trust_decreased: Trust went down
   - trust_stable: Trust unchanged
   - resistance_triggered: Resistance was activated

Respond in JSON format:
{{
    "mi_techniques": ["reflection", "open_question"],
    "maps_scores": {{"empathy": 4.0, "autonomy_support": 3.5, "evocation": 3.0, "focus": 3.5}},
    "behaviors": {{"reflection": true, "unsolicited_advice": false, "empathy": true}},
    "state_trajectory": "trust_increased",
    "feedback_notes": "Good use of reflection"
}}"""
        
        return prompt
    
    def _parse_analysis_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into analysis data"""
        import json
        
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Handle cases where LLM adds markdown code blocks
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            response = response.strip()
            
            return json.loads(response)
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse analysis response: {e}")
            return {}
    
    def _get_fallback_analysis(self, manager_message: str) -> InteractionAnalysis:
        """Get basic analysis when LLM fails"""
        message_lower = manager_message.lower()
        
        # Simple heuristic detection
        mi_techniques = []
        behaviors = {}
        
        # Check for questions
        if "?" in manager_message:
            if any(word in message_lower for word in ["what", "how", "tell me", "describe"]):
                mi_techniques.append("open_question")
                behaviors["reflection"] = True
            else:
                mi_techniques.append("closed_question")
        
        # Check for reflection indicators
        reflection_words = ["sounds like", "seem", "you're feeling", "i hear", "it seems"]
        if any(word in message_lower for word in reflection_words):
            mi_techniques.append("simple_reflection")
            behaviors["reflection"] = True
            behaviors["empathy"] = True
        
        # Check for advice
        if any(word in message_lower for word in ["you should", "try to", "why don't", "you need to"]):
            mi_techniques.append("giving_advice")
            behaviors["unsolicited_advice"] = True
        
        # Check for affirmation
        affirmation_words = ["good job", "great", "excellent", "i appreciate", "thank you for"]
        if any(word in message_lower for word in affirmation_words):
            mi_techniques.append("affirmation")
        
        return InteractionAnalysis(
            mi_techniques_used=mi_techniques,
            maps_scores={"empathy": 3.0, "autonomy_support": 3.0, "evocation": 3.0, "focus": 3.0},
            behaviors_detected=behaviors,
            state_trajectory="stable"
        )


# Singleton instance
_interaction_analyzer: Optional[InteractionAnalyzer] = None


def get_interaction_analyzer() -> InteractionAnalyzer:
    """Get or create the singleton InteractionAnalyzer"""
    global _interaction_analyzer
    if _interaction_analyzer is None:
        from src.services.llm_service import get_llm_service
        llm = get_llm_service()
        _interaction_analyzer = InteractionAnalyzer(llm)
    return _interaction_analyzer

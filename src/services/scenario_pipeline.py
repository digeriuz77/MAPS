"""
Scenario Pipeline - Core orchestrator for scenario processing

This is the heart of the scenario-based architecture. It orchestrates:
1. Persona response generation (creative)
2. Interaction analysis (deterministic scoring)
3. Feedback generation (template-based)
4. Completion checking (rules-based)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, List

from src.services.persona_response_engine import (
    PersonaResponseEngine, 
    PersonaState,
    get_persona_response_engine
)
from src.services.interaction_analyzer import (
    InteractionAnalyzer,
    get_interaction_analyzer
)
from src.services.feedback_generator import (
    FeedbackGenerator,
    get_feedback_generator
)
from src.services.completion_checker import (
    CompletionChecker,
    get_completion_checker
)

logger = logging.getLogger(__name__)


@dataclass
class TurnResult:
    """Result of processing a single turn"""
    persona_message: str
    persona_state: Dict[str, Any]
    analysis: Dict[str, Any]
    realtime_feedback: Optional[str]
    is_complete: bool
    completion_reason: Optional[str]
    turn_number: int


class ScenarioPipeline:
    """
    Deterministic pipeline for processing scenario turns.
    
    Pipeline flow:
    1. Persona responds (LLM - creative/contextual)
    2. Analyze interaction (LLM - structured scoring)
    3. Generate feedback (template - deterministic)
    4. Check completion (rules - deterministic)
    """
    
    def __init__(
        self,
        persona_engine: PersonaResponseEngine = None,
        analyzer: InteractionAnalyzer = None,
        feedback_gen: FeedbackGenerator = None,
        completion_checker: CompletionChecker = None
    ):
        self.persona_engine = persona_engine or get_persona_response_engine()
        self.analyzer = analyzer or get_interaction_analyzer()
        self.feedback_gen = feedback_gen or get_feedback_generator()
        self.completion_checker = completion_checker or get_completion_checker()
    
    async def process_turn(
        self,
        scenario: Dict[str, Any],
        attempt: Dict[str, Any],
        manager_input: str,
        settings: Dict[str, Any] = None
    ) -> TurnResult:
        """
        Process one turn of the scenario.
        
        Args:
            scenario: Full scenario configuration
            attempt: Current attempt record
            manager_input: What the manager said
            settings: Optional settings (feedback frequency, etc.)
            
        Returns:
            TurnResult with persona response, analysis, and feedback
        """
        settings = settings or {}
        show_feedback = settings.get("feedback_frequency", "key_moments")
        
        # Get current state
        current_state = PersonaState.from_dict(
            attempt.get("current_persona_state", {})
        )
        
        # Get conversation history
        transcript = attempt.get("transcript", [])
        conversation_history = self._extract_history_for_persona(transcript)
        
        # Store previous state for analysis
        previous_state = current_state.to_dict()
        
        logger.info(f"Processing turn {attempt.get('turn_count', 0) + 1} for scenario {scenario.get('code', 'unknown')}")
        
        # STEP 1: Persona responds (LLM - creative)
        persona_response = await self.persona_engine.generate_response(
            persona_config=scenario["persona_config"],
            manager_message=manager_input,
            conversation_history=conversation_history,
            current_state=current_state
        )
        
        # STEP 2: Analyze the interaction (LLM - structured)
        state_change = {
            "previous_trust": previous_state.get("trust_level", 4),
            **persona_response.updated_state.to_dict()
        }
        
        analysis = await self.analyzer.analyze_turn(
            manager_message=manager_input,
            persona_response=persona_response.message,
            persona_state_change=state_change,
            rubric=scenario.get("maps_rubric", {})
        )
        
        # STEP 3: Generate real-time feedback (template - deterministic)
        feedback = self.feedback_gen.generate_realtime_tip(
            analysis=analysis,
            learning_objective=scenario.get("learning_objective", ""),
            turn_count=attempt.get("turn_count", 0) + 1
        )
        
        # STEP 4: Check completion (rules - deterministic)
        # Prepare updated attempt data
        updated_attempt = self._prepare_updated_attempt(
            attempt, manager_input, persona_response, analysis
        )
        
        completion_result = self.completion_checker.check_completion(
            scenario=scenario,
            attempt=updated_attempt,
            latest_analysis=analysis.to_dict()
        )
        
        # Check for early termination
        should_end, end_reason = self.completion_checker.should_end_early(
            scenario, updated_attempt, analysis.to_dict()
        )
        
        if should_end and not completion_result.is_complete:
            completion_result = CompletionResult(
                is_complete=False,
                reason=end_reason,
                success=False,
                should_end=True
            )
        
        logger.info(f"Turn complete - Complete: {completion_result.is_complete}, Reason: {completion_result.reason}")
        
        return TurnResult(
            persona_message=persona_response.message,
            persona_state=persona_response.updated_state.to_dict(),
            analysis=analysis.to_dict(),
            realtime_feedback=feedback,
            is_complete=completion_result.is_complete,
            completion_reason=completion_result.reason if completion_result.is_complete else None,
            turn_number=attempt.get("turn_count", 0) + 1
        )
    
    def _extract_history_for_persona(
        self, 
        transcript: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Extract conversation history in format needed by persona engine"""
        history = []
        for turn in transcript[-10:]:  # Last 10 turns for context
            history.append({
                "turn": turn.get("turn", len(history) + 1),
                "manager_message": turn.get("manager_message", ""),
                "persona_response": turn.get("persona_response", ""),
                "persona_name": turn.get("persona_name", "Persona")
            })
        return history
    
    def _prepare_updated_attempt(
        self,
        attempt: Dict[str, Any],
        manager_input: str,
        persona_response,
        analysis
    ) -> Dict[str, Any]:
        """Prepare updated attempt data for completion checking"""
        turn_count = attempt.get("turn_count", 0) + 1
        
        # Build turn record
        turn_record = {
            "turn": turn_count,
            "manager_message": manager_input,
            "persona_response": persona_response.message,
            "persona_state": persona_response.updated_state.to_dict(),
            "analysis": analysis.to_dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Update transcript
        transcript = attempt.get("transcript", [])
        transcript.append(turn_record)
        
        # Update skills demonstrated
        skills = set(attempt.get("skills_demonstrated", []))
        for technique in analysis.mi_techniques_used:
            if technique in ["reflection", "open_question", "affirmation", "summarization"]:
                skills.add(technique)
        skills_list = list(skills)
        
        # Update negative behaviors
        negative = set(attempt.get("negative_behaviors", []))
        if analysis.behaviors_detected.get("unsolicited_advice"):
            negative.add("unsolicited_advice")
        if analysis.behaviors_detected.get("fix_mode"):
            negative.add("fixing")
        negative_list = list(negative)
        
        return {
            **attempt,
            "turn_count": turn_count,
            "transcript": transcript,
            "current_persona_state": persona_response.updated_state.to_dict(),
            "skills_demonstrated": skills_list,
            "negative_behaviors": negative_list
        }
    
    def get_scenario_summary(
        self,
        scenario: Dict[str, Any],
        attempt: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get a summary of the scenario and current attempt status"""
        criteria = scenario.get("success_criteria", {})
        turn_count = attempt.get("turn_count", 0)
        turn_range = criteria.get("turn_range", [3, 15])
        
        return {
            "scenario_code": scenario.get("code", ""),
            "scenario_title": scenario.get("title", ""),
            "skill_category": scenario.get("mi_skill_category", ""),
            "difficulty": scenario.get("difficulty", ""),
            "learning_objective": scenario.get("learning_objective", ""),
            "persona_name": scenario.get("persona_config", {}).get("name", "Persona"),
            "turn_count": turn_count,
            "turn_range": turn_range,
            "progress": f"{turn_count}/{turn_range[1]} turns",
            "required_skills": criteria.get("required_skills", []),
            "avoid_behaviors": criteria.get("avoid_behaviors", [])
        }


# Singleton instance
_scenario_pipeline: Optional[ScenarioPipeline] = None


def get_scenario_pipeline() -> ScenarioPipeline:
    """Get or create the singleton ScenarioPipeline"""
    global _scenario_pipeline
    if _scenario_pipeline is None:
        _scenario_pipeline = ScenarioPipeline()
    return _scenario_pipeline

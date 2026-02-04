"""
Scenario Pipeline - Core orchestrator for scenario processing

This is the heart of the scenario-based architecture. It orchestrates:
1. Persona response generation (creative)
2. Interaction analysis (deterministic scoring)
3. Feedback generation (template-based)
4. Completion checking (rules-based)
"""

import logging
from dataclasses import dataclass, asdict
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
    CompletionResult,
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

        # STEP 2.5: Refine persona state based on LLM analysis
        # This replaces the rigid keyword matching with actual technique detection
        refined_state = self._refine_state_from_analysis(
            current_state=current_state,
            analysis=analysis,
            persona_config=scenario.get("persona_config", {})
        )
        # Update the persona response with refined state
        persona_response.updated_state = refined_state

        # Convert analysis to dict for feedback generation
        analysis_dict = asdict(analysis)

        # STEP 3: Generate real-time feedback (template - deterministic)
        feedback_result = self.feedback_gen.generate_realtime_tip(
            analysis=analysis_dict,
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
            analysis=analysis_dict,
            realtime_feedback=feedback_result.tip,
            is_complete=completion_result.is_complete,
            completion_reason=completion_result.reason if completion_result.is_complete else None,
            turn_number=attempt.get("turn_count", 0) + 1
        )
    
    def _refine_state_from_analysis(
        self,
        current_state: PersonaState,
        analysis,
        persona_config: Dict[str, Any]
    ) -> PersonaState:
        """
        Refine persona state based on LLM analysis of detected techniques.

        This replaces the rigid keyword matching with actual technique detection.
        The LLM has already identified what techniques the manager actually used,
        so we use those to determine trust/openness changes.

        Args:
            current_state: The state before this turn
            analysis: InteractionAnalysis from LLM
            persona_config: Persona configuration with response patterns

        Returns:
            Refined PersonaState based on detected techniques
        """
        techniques = analysis.mi_techniques_used
        behaviors = analysis.behaviors_detected
        trajectory = analysis.state_trajectory

        trust_delta = 0
        openness_delta = 0
        resistance_triggered = current_state.resistance_active

        # === TRUST-BUILDING TECHNIQUES (detected by LLM) ===
        # These are actual MI-adherent techniques that build rapport

        if "complex_reflection" in techniques:
            trust_delta += 2  # Strong trust builder
            openness_delta += 2
            logger.debug("Trust +2: Complex reflection detected")

        if "simple_reflection" in techniques:
            trust_delta += 1
            openness_delta += 1
            logger.debug("Trust +1: Simple reflection detected")

        if "open_question" in techniques:
            trust_delta += 1
            openness_delta += 1
            logger.debug("Trust +1: Open question detected")

        if "affirmation" in techniques:
            trust_delta += 1
            logger.debug("Trust +1: Affirmation detected")

        if "summarization" in techniques:
            trust_delta += 1
            openness_delta += 1
            logger.debug("Trust +1: Summarization detected")

        # === TRUST-ERODING TECHNIQUES ===

        if "giving_advice" in techniques and behaviors.get("unsolicited_advice"):
            trust_delta -= 2
            openness_delta -= 1
            resistance_triggered = True
            logger.debug("Trust -2: Unsolicited advice detected")

        if behaviors.get("confrontation"):
            trust_delta -= 2
            resistance_triggered = True
            logger.debug("Trust -2: Confrontation detected")

        if behaviors.get("fix_mode"):
            trust_delta -= 1
            resistance_triggered = True
            logger.debug("Trust -1: Fix mode detected")

        # === NEUTRAL/MINOR IMPACT ===

        if "closed_question" in techniques and not any(t in techniques for t in
            ["open_question", "reflection", "simple_reflection", "complex_reflection"]):
            # Only closed questions with no positive techniques
            trust_delta -= 1
            logger.debug("Trust -1: Only closed questions used")

        # === USE LLM TRAJECTORY AS TIE-BREAKER ===
        # If the LLM detected trust increased/decreased, weight that

        if trajectory == "trust_increased" and trust_delta == 0:
            trust_delta += 1
            logger.debug("Trust +1: LLM detected trust increase")
        elif trajectory == "trust_decreased" and trust_delta == 0:
            trust_delta -= 1
            resistance_triggered = True
            logger.debug("Trust -1: LLM detected trust decrease")
        elif trajectory == "resistance_triggered":
            resistance_triggered = True
            logger.debug("Resistance triggered by LLM analysis")

        # === CALCULATE NEW STATE ===

        new_trust = max(1, min(10, current_state.trust_level + trust_delta))
        new_openness = max(1, min(10, current_state.openness_level + openness_delta))

        # Natural resistance decay at high trust
        if new_trust >= 7 and resistance_triggered:
            resistance_triggered = False
            logger.debug("Resistance cleared: High trust level reached")

        logger.info(
            f"State refined from analysis: trust={current_state.trust_level}->{new_trust}, "
            f"openness={current_state.openness_level}->{new_openness}, "
            f"techniques={techniques}"
        )

        return PersonaState(
            trust_level=new_trust,
            openness_level=new_openness,
            resistance_active=resistance_triggered
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
            "analysis": asdict(analysis),
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

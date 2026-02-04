"""
Completion Checker - Determines if a scenario is complete

Uses deterministic rule-based logic to check if success criteria are met.
"""

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class CompletionResult:
    """Result of completion check"""
    is_complete: bool
    reason: str
    success: bool
    should_end: bool = None
    
    def __post_init__(self):
        if self.should_end is None:
            self.should_end = self.is_complete


class CompletionChecker:
    """
    Determines if a scenario has been successfully completed.
    
    Checks:
    - Turn count within allowed range
    - Required skills demonstrated
    - Avoided negative behaviors
    - State goals met (e.g., trust maintained)
    """
    
    def check_completion(
        self,
        scenario: Dict[str, Any],
        attempt: Dict[str, Any],
        latest_analysis: Dict[str, Any],
        max_turns: int = 15,
        min_turns: int = 3
    ) -> CompletionResult:
        """
        Check if scenario completion criteria are met.
        
        Args:
            scenario: Full scenario configuration with success_criteria
            attempt: Current attempt record with transcript and turn_count
            latest_analysis: Analysis of the latest turn
            max_turns: Maximum turns allowed (fallback)
            min_turns: Minimum turns needed (fallback)
            
        Returns:
            CompletionResult with is_complete, reason, and success
        """
        criteria = scenario.get("success_criteria", {})
        turn_count = attempt.get("turn_count", 0)
        
        # Get turn range from criteria or use fallbacks
        turn_range = criteria.get("turn_range", [min_turns, max_turns])
        min_required, max_allowed = turn_range[0], turn_range[1]
        
        # Check 1: Turn count range
        if turn_count < min_required:
            return CompletionResult(
                is_complete=False,
                reason=f"Too early - minimum {min_required} turns required",
                success=False
            )
        
        if turn_count >= max_allowed:
            return CompletionResult(
                is_complete=False,
                reason=f"Maximum turns ({max_allowed}) reached",
                success=False,
                should_end=True
            )
        
        # Check 2: Required skills demonstrated
        # Support both "required_skills" and "required_techniques" for backwards compatibility
        required_skills = criteria.get("required_skills", criteria.get("required_techniques", []))
        skills_demonstrated = attempt.get("skills_demonstrated", [])
        
        missing_skills = [skill for skill in required_skills if skill not in skills_demonstrated]
        if missing_skills:
            return CompletionResult(
                is_complete=False,
                reason=f"Still need to demonstrate: {', '.join(missing_skills)}",
                success=False
            )
        
        # Check 3: Avoided negative behaviors
        avoid_behaviors = criteria.get("avoid_behaviors", [])
        negative_behaviors = attempt.get("negative_behaviors", [])
        
        violated_behaviors = [behavior for behavior in avoid_behaviors if behavior in negative_behaviors]
        if violated_behaviors:
            return CompletionResult(
                is_complete=False,
                reason=f"Used discouraged behaviors: {', '.join(violated_behaviors)}",
                success=False,
                should_end=True
            )
        
        # Check 4: State goals
        state_goals = criteria.get("state_goals", {})
        current_state = attempt.get("current_persona_state", {})
        initial_state = attempt.get("initial_persona_state", {})
        current_trust = current_state.get("trust_level", 4)

        # Check min_trust threshold (direct field or in state_goals)
        min_trust = criteria.get("min_trust", state_goals.get("min_trust"))
        if min_trust is not None:
            if current_trust < min_trust:
                return CompletionResult(
                    is_complete=False,
                    reason=f"Trust level ({current_trust}) hasn't reached minimum ({min_trust})",
                    success=False
                )

        # Check trust maintenance
        if state_goals.get("trust_maintained"):
            initial_trust = initial_state.get("trust_level", 4)

            if current_trust < initial_trust - 1:  # Allow small variance
                return CompletionResult(
                    is_complete=False,
                    reason="Trust level decreased - try to maintain rapport",
                    success=False
                )

        # Check trust increased
        if state_goals.get("trust_increased"):
            initial_trust = initial_state.get("trust_level", 4)
            if current_trust <= initial_trust:
                return CompletionResult(
                    is_complete=False,
                    reason="Trust hasn't increased yet - continue building rapport",
                    success=False
                )

        # Check resistance not increased
        if state_goals.get("resistance_not_increased"):
            if current_state.get("resistance_active"):
                return CompletionResult(
                    is_complete=False,
                    reason="Resistance was triggered - try a different approach",
                    success=False
                )

        # Check resistance decreased
        if state_goals.get("resistance_decreased"):
            initial_resistance = initial_state.get("resistance_active", True)
            current_resistance = current_state.get("resistance_active", True)
            if initial_resistance and current_resistance:
                return CompletionResult(
                    is_complete=False,
                    reason="Resistance is still active - try to build more rapport",
                    success=False
                )
        
        # All checks passed - scenario complete!
        return CompletionResult(
            is_complete=True,
            reason="Success criteria met",
            success=True,
            should_end=True
        )
    
    def should_end_early(
        self,
        scenario: Dict[str, Any],
        attempt: Dict[str, Any],
        latest_analysis: Dict[str, Any]
    ) -> tuple[bool, str]:
        """
        Check if scenario should end early (either success or failure).
        
        Returns:
            Tuple of (should_end, reason)
        """
        # Check for clear success - strong performance consistently
        scores = latest_analysis.get("maps_scores", {})
        
        if scores:
            avg_score = sum(scores.values()) / len(scores)
            
            # If consistently excellent (4+ across all dimensions)
            if all(s >= 4 for s in scores.values()) and attempt.get("turn_count", 0) >= 3:
                return True, "Excellent performance - scenario complete"
            
            # If consistently poor (below 2.5) after minimum turns
            if all(s < 2.5 for s in scores.values()) and attempt.get("turn_count", 0) >= 5:
                return True, "Consider trying a different approach"
        
        # Check for resistance escalation
        trajectory = latest_analysis.get("state_trajectory", "")
        if trajectory == "trust_decreased":
            # Give a couple turns to recover
            if attempt.get("turn_count", 0) >= 6:
                return True, "Trust has been declining - consider ending and reflecting"
        
        return False, ""
    
    def generate_completion_reason(
        self,
        result: CompletionResult,
        scenario: Dict[str, Any],
        attempt: Dict[str, Any]
    ) -> str:
        """Generate a human-readable completion reason"""
        if result.success:
            return f"Successfully completed: {scenario.get('title', 'Scenario')}"
        
        if "maximum turns" in result.reason.lower():
            return "Scenario ended: Maximum turns reached"
        
        if "resistance" in result.reason.lower():
            return "Scenario ended: Resistance was triggered"
        
        return f"Scenario ended: {result.reason}"


# Singleton instance
_completion_checker: Optional[CompletionChecker] = None


def get_completion_checker() -> CompletionChecker:
    """Get or create the singleton CompletionChecker"""
    global _completion_checker
    if _completion_checker is None:
        _completion_checker = CompletionChecker()
    return _completion_checker

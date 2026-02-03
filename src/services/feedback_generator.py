"""
Feedback Generator Service - Generates real-time feedback for scenarios
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class FeedbackResult:
    """Result of feedback generation"""
    tip: str
    category: str  # "technique", "approach", "empathy", "general"
    confidence: float = 0.8


class FeedbackGenerator:
    """Generates real-time feedback for scenario training"""

    def __init__(self):
        logger.info("FeedbackGenerator initialized")

    def generate_realtime_tip(
        self,
        analysis: Dict[str, Any],
        learning_objective: str = "",
        turn_count: int = 1
    ) -> FeedbackResult:
        """
        Generate real-time feedback tip based on interaction analysis

        Args:
            analysis: Interaction analysis results (InteractionAnalysis.to_dict())
            learning_objective: Current learning objective
            turn_count: Current turn number

        Returns:
            FeedbackResult with tip and category
        """
        # Handle InteractionAnalysis structure
        mi_techniques = analysis.get('mi_techniques_used', [])
        maps_scores = analysis.get('maps_scores', {})
        behaviors = analysis.get('behaviors_detected', {})

        # Calculate quality from available data
        empathy = maps_scores.get('empathy', 5.0)
        autonomy = maps_scores.get('autonomy_support', maps_scores.get('autonomy', 5.0))
        quality_score = (empathy + autonomy) / 2

        # Check for negative behaviors
        has_unsolicited_advice = behaviors.get('unsolicited_advice', False)
        has_fixing = behaviors.get('fix_mode', False)

        # Generate feedback based on quality and behaviors
        if has_unsolicited_advice:
            tip = "Try to avoid giving advice directly. Instead, use an open question to explore their thoughts."
            category = "technique"
        elif has_fixing:
            tip = "You seem to be in 'fix mode'. Try reflecting back what they shared instead of offering solutions."
            category = "approach"
        elif not mi_techniques:
            tip = "Try to use an open question or reflection to engage more deeply with what they shared."
            category = "technique"
        elif 'reflection' in mi_techniques and 'open_question' in mi_techniques:
            tip = "Great combination of reflections and open questions! Continue exploring their perspective."
            category = "technique"
        elif quality_score >= 7:
            tip = "Good interaction. Your response shows strong person-centered approach."
            category = "empathy"
        elif quality_score >= 5:
            tip = "Fair attempt. Consider using more reflections to demonstrate understanding."
            category = "general"
        else:
            tip = "Take a moment to reflect their words before responding. This shows you're truly listening."
            category = "general"

        return FeedbackResult(tip=tip, category=category, confidence=0.8)

    def generate_end_of_scenario_feedback(
        self,
        analyses: list[Dict[str, Any]],
        success: bool = False,
        completion_reason: str = "unknown"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive feedback at the end of a scenario.

        Args:
            analyses: List of turn analyses from the scenario
            success: Whether the scenario was completed successfully
            completion_reason: Reason for scenario completion

        Returns:
            Dict with success, completion_reason, average_scores, strengths, opportunities, summary
        """
        if not analyses:
            return {
                'success': False,
                'completion_reason': completion_reason,
                'average_scores': {},
                'strengths': [],
                'opportunities': [],
                'summary': 'No analysis data available'
            }

        # Calculate average scores across all turns
        all_scores = {}
        score_counts = {}
        all_techniques = []
        all_behaviors = {'positive': [], 'negative': []}

        for analysis in analyses:
            maps_scores = analysis.get('maps_scores', {})
            for key, value in maps_scores.items():
                if isinstance(value, (int, float)):
                    all_scores[key] = all_scores.get(key, 0) + value
                    score_counts[key] = score_counts.get(key, 0) + 1

            techniques = analysis.get('mi_techniques_used', [])
            all_techniques.extend(techniques)

            behaviors = analysis.get('behaviors_detected', {})
            for behavior, detected in behaviors.items():
                if detected:
                    if behavior in ['reflection', 'empathy', 'autonomy_support', 'permission_asking']:
                        all_behaviors['positive'].append(behavior)
                    elif behavior in ['unsolicited_advice', 'fix_mode', 'confrontation']:
                        all_behaviors['negative'].append(behavior)

        # Calculate averages
        average_scores = {
            key: all_scores[key] / score_counts[key]
            for key in all_scores
        }

        # Generate strengths
        strengths = []
        if average_scores.get('empathy', 0) >= 4:
            strengths.append("Strong empathy demonstrated throughout")
        if average_scores.get('autonomy_support', 0) >= 4:
            strengths.append("Good support for client autonomy")
        if 'reflection' in all_techniques:
            strengths.append("Used reflective listening effectively")
        if 'open_question' in all_techniques:
            strengths.append("Asked open-ended questions to explore")
        if 'affirmation' in all_techniques:
            strengths.append("Provided affirmations to build confidence")

        # Generate opportunities for improvement
        opportunities = []
        if 'unsolicited_advice' in all_behaviors['negative']:
            opportunities.append("Work on avoiding unsolicited advice - ask permission first")
        if 'fix_mode' in all_behaviors['negative']:
            opportunities.append("Practice staying out of 'fix mode' - reflect instead of solving")
        if average_scores.get('empathy', 5) < 3.5:
            opportunities.append("Focus on demonstrating empathy through reflections")
        if average_scores.get('autonomy_support', 5) < 3.5:
            opportunities.append("Emphasize client choice and autonomy more")
        if 'open_question' not in all_techniques and 'simple_reflection' not in all_techniques:
            opportunities.append("Incorporate more open questions and reflections")

        # Generate summary
        if success:
            summary = "Congratulations! You successfully completed the scenario. "
            if len(strengths) >= 2:
                summary += "You demonstrated strong MI skills throughout the conversation."
            else:
                summary += "You met the success criteria for this scenario."
        else:
            summary = f"Scenario ended: {completion_reason}. "
            if opportunities:
                summary += "Review the opportunities for improvement and try again."

        return {
            'success': success,
            'completion_reason': completion_reason,
            'average_scores': average_scores,
            'strengths': strengths,
            'opportunities': opportunities,
            'summary': summary
        }


# Global instance
_feedback_generator = None


def get_feedback_generator() -> FeedbackGenerator:
    """Get or create the feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = FeedbackGenerator()
    return _feedback_generator

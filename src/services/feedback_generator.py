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

        # Build technique confirmation string
        technique_confirmation = self._build_technique_confirmation(mi_techniques, behaviors)

        # Generate coaching tip based on quality and behaviors
        if has_unsolicited_advice:
            coaching_tip = "Try asking permission before offering suggestions."
            category = "technique"
        elif has_fixing:
            coaching_tip = "Try reflecting back what they shared instead of offering solutions."
            category = "approach"
        elif not mi_techniques:
            coaching_tip = "Try using an open question or reflection to explore their perspective."
            category = "technique"
        elif 'complex_reflection' in mi_techniques:
            coaching_tip = "Excellent depth in your reflection! You're capturing underlying feelings."
            category = "technique"
        elif 'simple_reflection' in mi_techniques and 'open_question' in mi_techniques:
            coaching_tip = "Great combination! Continue exploring their perspective."
            category = "technique"
        elif quality_score >= 7:
            coaching_tip = "Strong person-centered approach in this response."
            category = "empathy"
        elif quality_score >= 5:
            coaching_tip = "Consider adding a reflection to show understanding."
            category = "general"
        else:
            coaching_tip = "Take a moment to reflect their words before responding."
            category = "general"

        # Combine technique confirmation with coaching tip
        if technique_confirmation:
            tip = f"{technique_confirmation}\n\n{coaching_tip}"
        else:
            tip = coaching_tip

        return FeedbackResult(tip=tip, category=category, confidence=0.8)

    def _build_technique_confirmation(
        self,
        mi_techniques: list,
        behaviors: Dict[str, bool]
    ) -> str:
        """
        Build a technique confirmation string showing what was detected.

        Returns formatted string like:
        "✓ Detected: Complex reflection, Open question"
        """
        detected = []

        # Map technique codes to friendly names
        technique_names = {
            'complex_reflection': 'Complex reflection',
            'simple_reflection': 'Simple reflection',
            'open_question': 'Open question',
            'closed_question': 'Closed question',
            'affirmation': 'Affirmation',
            'summarization': 'Summary',
            'giving_advice': 'Advice giving',
        }

        # Add detected MI techniques
        for technique in mi_techniques:
            if technique in technique_names:
                detected.append(technique_names[technique])

        # Add positive behaviors
        if behaviors.get('empathy') and 'Complex reflection' not in detected:
            detected.append('Empathy shown')
        if behaviors.get('autonomy_support'):
            detected.append('Autonomy support')
        if behaviors.get('permission_asking'):
            detected.append('Permission asking')

        if detected:
            return f"✓ Detected: {', '.join(detected)}"
        return ""

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

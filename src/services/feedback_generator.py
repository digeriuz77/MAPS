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
            analysis: Interaction analysis results
            learning_objective: Current learning objective
            turn_count: Current turn number

        Returns:
            FeedbackResult with tip and category
        """
        quality_score = analysis.get('quality_score', 5.0)
        technique = analysis.get('technique', 'unknown')
        empathy_score = analysis.get('empathy_score', 5.0)

        # Generate feedback based on quality
        if quality_score >= 8:
            tip = "Excellent work! You're demonstrating strong MI techniques."
            category = "technique"
        elif quality_score >= 6:
            tip = "Good interaction. Consider using more open questions to explore deeper."
            category = "approach"
        elif quality_score >= 4:
            tip = "Fair attempt. Try to reflect more on what the client shared."
            category = "empathy"
        else:
            tip = "Consider slowing down and truly listening before responding."
            category = "general"

        return FeedbackResult(tip=tip, category=category, confidence=0.8)


# Global instance
_feedback_generator = None


def get_feedback_generator() -> FeedbackGenerator:
    """Get or create the feedback generator instance"""
    global _feedback_generator
    if _feedback_generator is None:
        _feedback_generator = FeedbackGenerator()
    return _feedback_generator

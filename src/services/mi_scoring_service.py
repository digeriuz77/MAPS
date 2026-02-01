"""
MI Scoring Service

Service for scoring MI practice attempts across 5 dimensions
using continuous spectrum scoring (1-10) instead of binary right/wrong.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

from src.models.mi_models import (
    MIPracticeAttempt,
    FinalScores,
    MAPSRubric,
    CompetencyIndicator,
)

logger = logging.getLogger(__name__)


@dataclass
class DimensionScore:
    """Score for a single scoring dimension"""
    dimension_id: str
    score: float  # 1-10
    confidence: float  # 0.0-1.0
    evidence: List[str]
    improvement_areas: List[str]


@dataclass
class ScoringResult:
    """Complete scoring result"""
    overall_score: float
    dimension_scores: Dict[str, DimensionScore]
    technique_breakdown: Dict[str, int]
    key_moments: List[Dict[str, Any]]
    recommendations: List[str]


class MIScoringService:
    """
    Service for scoring MI practice attempts.
    
    Implements continuous spectrum scoring (1-10) across 5 dimensions:
    1. Engagement & Rapport Building (A6)
    2. Reflective Listening (2.1.1, 2.1.2)
    3. Evoking Change Talk (3.1.1, 3.2.1)
    4. Managing Resistance (4.1.1)
    5. Therapeutic Alliance (B6)
    
    Uses continuous interpolation rather than binary right/wrong.
    """
    
    # Scoring dimensions and their weights
    DIMENSIONS = {
        'engagement': {
            'name': 'Engagement & Rapport Building',
            'competency_ids': ['A6'],
            'weight': 1.5,
            'description': 'Ability to establish and maintain therapeutic rapport',
        },
        'reflection': {
            'name': 'Reflective Listening',
            'competency_ids': ['2.1.1', '2.1.2'],
            'weight': 2.0,
            'description': 'Use of simple and complex reflections',
        },
        'evocation': {
            'name': 'Evoking Change Talk',
            'competency_ids': ['3.1.1', '3.2.1'],
            'weight': 1.8,
            'description': 'Eliciting and strengthening motivation for change',
        },
        'resistance': {
            'name': 'Managing Resistance',
            'competency_ids': ['4.1.1'],
            'weight': 1.7,
            'description': 'Rolling with resistance and avoiding confrontation',
        },
        'alliance': {
            'name': 'Therapeutic Alliance',
            'competency_ids': ['B6'],
            'weight': 1.5,
            'description': 'Overall partnership and collaboration',
        },
    }
    
    # Technique scoring weights
    TECHNIQUE_WEIGHTS = {
        # MI-adherent techniques (positive)
        'simple_reflection': 1.0,
        'complex_reflection': 1.2,
        'open_question': 1.0,
        'affirmation': 1.1,
        'summarizing': 1.0,
        'amplified_reflection': 1.3,
        'double_sided_reflection': 1.2,
        'metaphor': 1.1,
        
        # MI-non-adherent techniques (negative)
        'righting_reflex': -1.5,
        'confrontation': -2.0,
        'educating': -1.0,
        'advising': -0.8,
        'questioning': -0.5,
        'defending': -1.5,
        'interpreting': -0.7,
        
        # Neutral/variable
        'closed_question': -0.3,
        'information': 0.0,
    }
    
    def __init__(self):
        logger.info("MIScoringService initialized")
    
    def score_attempt(
        self,
        attempt: MIPracticeAttempt,
        rubric: Optional[MAPSRubric] = None
    ) -> ScoringResult:
        """
        Score a complete practice attempt.
        
        Args:
            attempt: The completed attempt
            rubric: Optional custom scoring rubric
            
        Returns:
            ScoringResult with detailed scores
        """
        choices = attempt.choices_made
        
        if not choices:
            return self._empty_result()
        
        # Calculate dimension scores
        dimension_scores = {}
        
        for dim_id, dim_config in self.DIMENSIONS.items():
            score = self._calculate_dimension_score(
                dim_id, dim_config, choices, attempt
            )
            dimension_scores[dim_id] = score
        
        # Calculate overall score using weighted average
        total_weight = sum(d['weight'] for d in self.DIMENSIONS.values())
        weighted_sum = sum(
            dimension_scores[dim_id].score * dim_config['weight']
            for dim_id, dim_config in self.DIMENSIONS.items()
        )
        overall_score = weighted_sum / total_weight
        
        # Ensure score is within 1-10 range
        overall_score = max(1.0, min(10.0, overall_score))
        
        # Generate technique breakdown
        technique_breakdown = self._count_techniques(choices)
        
        # Identify key moments
        key_moments = self._identify_key_moments(choices, attempt)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(dimension_scores, technique_breakdown)
        
        return ScoringResult(
            overall_score=round(overall_score, 1),
            dimension_scores=dimension_scores,
            technique_breakdown=technique_breakdown,
            key_moments=key_moments,
            recommendations=recommendations,
        )
    
    def _calculate_dimension_score(
        self,
        dimension_id: str,
        dimension_config: Dict[str, Any],
        choices: List[Dict[str, Any]],
        attempt: MIPracticeAttempt
    ) -> DimensionScore:
        """
        Calculate score for a single dimension.
        
        Uses continuous scoring based on:
        - Technique usage patterns
        - Rapport/resistance impacts
        - Consistency across the attempt
        """
        evidence = []
        improvement_areas = []
        
        # Base score starts at 5 (neutral)
        base_score = 5.0
        
        # Analyze choices for this dimension
        positive_signals = 0
        negative_signals = 0
        
        for idx, choice in enumerate(choices):
            techniques = choice.get('techniques_used', [])
            rapport_impact = choice.get('rapport_impact', 0)
            resistance_impact = choice.get('resistance_impact', 0)
            
            # Score based on dimension-specific criteria
            if dimension_id == 'engagement':
                score_delta, sig_evidence = self._score_engagement(
                    choice, techniques, rapport_impact
                )
                base_score += score_delta
                if sig_evidence:
                    evidence.append(f"Turn {idx + 1}: {sig_evidence}")
                    
            elif dimension_id == 'reflection':
                score_delta, sig_evidence = self._score_reflection(
                    choice, techniques
                )
                base_score += score_delta
                if sig_evidence:
                    evidence.append(f"Turn {idx + 1}: {sig_evidence}")
                    
            elif dimension_id == 'evocation':
                score_delta, sig_evidence = self._score_evocation(
                    choice, techniques, attempt.tone_spectrum_position
                )
                base_score += score_delta
                if sig_evidence:
                    evidence.append(f"Turn {idx + 1}: {sig_evidence}")
                    
            elif dimension_id == 'resistance':
                score_delta, sig_evidence = self._score_resistance_management(
                    choice, techniques, resistance_impact
                )
                base_score += score_delta
                if sig_evidence:
                    evidence.append(f"Turn {idx + 1}: {sig_evidence}")
                    
            elif dimension_id == 'alliance':
                score_delta, sig_evidence = self._score_alliance(
                    choice, techniques, rapport_impact, attempt.tone_spectrum_position
                )
                base_score += score_delta
                if sig_evidence:
                    evidence.append(f"Turn {idx + 1}: {sig_evidence}")
            
            # Track positive/negative signals
            if score_delta > 0.3:
                positive_signals += 1
            elif score_delta < -0.3:
                negative_signals += 1
        
        # Normalize score to 1-10 range
        final_score = max(1.0, min(10.0, base_score))
        
        # Calculate confidence based on number of choices
        confidence = min(1.0, len(choices) / 5)  # Full confidence at 5+ choices
        
        # Generate improvement areas
        if dimension_id == 'reflection' and 'simple_reflection' not in str(choices):
            improvement_areas.append("Practice using more reflections to demonstrate listening")
        
        if dimension_id == 'resistance' and negative_signals > positive_signals:
            improvement_areas.append("Focus on rolling with resistance rather than confronting it")
        
        if dimension_id == 'engagement' and attempt.current_rapport_score <= 0:
            improvement_areas.append("Work on building initial rapport before exploring change")
        
        return DimensionScore(
            dimension_id=dimension_id,
            score=round(final_score, 1),
            confidence=round(confidence, 2),
            evidence=evidence[:5],  # Limit evidence items
            improvement_areas=improvement_areas,
        )
    
    def _score_engagement(
        self,
        choice: Dict[str, Any],
        techniques: List[str],
        rapport_impact: int
    ) -> tuple[float, str]:
        """Score engagement dimension"""
        score_delta = 0.0
        evidence = ""
        
        # Positive signals
        if 'simple_reflection' in techniques or 'complex_reflection' in techniques:
            score_delta += 0.5
            evidence = "Used reflection to show understanding"
        
        if 'open_question' in techniques:
            score_delta += 0.4
            if not evidence:
                evidence = "Used open question to invite exploration"
        
        if rapport_impact > 0:
            score_delta += 0.3 * rapport_impact
        
        # Negative signals
        if 'righting_reflex' in techniques or 'confrontation' in techniques:
            score_delta -= 1.0
            evidence = "Confrontational approach may damage rapport"
        
        return score_delta, evidence
    
    def _score_reflection(
        self,
        choice: Dict[str, Any],
        techniques: List[str]
    ) -> tuple[float, str]:
        """Score reflective listening dimension"""
        score_delta = 0.0
        evidence = ""
        
        # Simple reflection
        if 'simple_reflection' in techniques:
            score_delta += 0.6
            evidence = "Used simple reflection effectively"
        
        # Complex/amplified reflection (higher skill)
        if 'complex_reflection' in techniques or 'amplified_reflection' in techniques:
            score_delta += 0.8
            evidence = "Used advanced reflection technique"
        
        # Double-sided reflection
        if 'double_sided_reflection' in techniques:
            score_delta += 0.9
            evidence = "Acknowledged ambivalence with double-sided reflection"
        
        # Missing reflection opportunity
        if not any('reflection' in t for t in techniques):
            if 'question' in str(techniques).lower():
                score_delta -= 0.3
                evidence = "Missed opportunity to reflect before questioning"
        
        return score_delta, evidence
    
    def _score_evocation(
        self,
        choice: Dict[str, Any],
        techniques: List[str],
        final_tone: float
    ) -> tuple[float, str]:
        """Score evocation dimension"""
        score_delta = 0.0
        evidence = ""
        
        # Open questions help evoke
        if 'open_question' in techniques:
            score_delta += 0.5
            evidence = "Open question invites deeper exploration"
        
        # Affirmations strengthen motivation
        if 'affirmation' in techniques:
            score_delta += 0.6
            evidence = "Affirmation builds confidence for change"
        
        # Tone progression indicates successful evocation
        if final_tone > 0.6:
            score_delta += 0.3
        
        return score_delta, evidence
    
    def _score_resistance_management(
        self,
        choice: Dict[str, Any],
        techniques: List[str],
        resistance_impact: int
    ) -> tuple[float, str]:
        """Score resistance management dimension"""
        score_delta = 0.0
        evidence = ""
        
        # Negative impact indicates resistance was triggered
        if resistance_impact > 0:
            score_delta -= 0.5 * resistance_impact
            evidence = f"Resistance increased (impact: +{resistance_impact})"
        
        # Positive impact indicates resistance was reduced
        if resistance_impact < 0:
            score_delta += 0.6 * abs(resistance_impact)
            evidence = f"Successfully reduced resistance"
        
        # Non-adherent techniques trigger resistance
        if 'righting_reflex' in techniques:
            score_delta -= 1.2
            evidence = "Righting reflex triggered resistance"
        
        if 'confrontation' in techniques:
            score_delta -= 1.5
            evidence = "Confrontation increased resistance"
        
        # Reflections help manage resistance
        if 'simple_reflection' in techniques and resistance_impact < 0:
            score_delta += 0.4
            evidence = "Reflection helped reduce resistance"
        
        return score_delta, evidence
    
    def _score_alliance(
        self,
        choice: Dict[str, Any],
        techniques: List[str],
        rapport_impact: int,
        final_tone: float
    ) -> tuple[float, str]:
        """Score therapeutic alliance dimension"""
        score_delta = 0.0
        evidence = ""
        
        # Rapport building
        if rapport_impact > 0:
            score_delta += 0.4 * rapport_impact
            evidence = "Built rapport through response"
        
        # Tone progression shows alliance strengthening
        if final_tone > 0.5:
            score_delta += 0.3
        
        # Collaboration signals
        if 'affirmation' in techniques:
            score_delta += 0.5
            if not evidence:
                evidence = "Affirmation strengthens partnership"
        
        # Damaging signals
        if rapport_impact < 0:
            score_delta += 0.5 * rapport_impact  # Negative impact
            evidence = "Response may have damaged alliance"
        
        return score_delta, evidence
    
    def _count_techniques(self, choices: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count technique usage across all choices"""
        counts = {}
        
        for choice in choices:
            for technique in choice.get('techniques_used', []):
                counts[technique] = counts.get(technique, 0) + 1
        
        return counts
    
    def _identify_key_moments(
        self,
        choices: List[Dict[str, Any]],
        attempt: MIPracticeAttempt
    ) -> List[Dict[str, Any]]:
        """Identify key moments in the attempt"""
        moments = []
        
        for idx, choice in enumerate(choices):
            techniques = choice.get('techniques_used', [])
            rapport = choice.get('rapport_impact', 0)
            
            # Best moments
            if rapport >= 2 and 'reflection' in str(techniques):
                moments.append({
                    'turn': idx + 1,
                    'type': 'strength',
                    'description': 'Strong rapport-building response',
                    'techniques': techniques,
                })
            
            # Learning moments
            if 'righting_reflex' in techniques or 'confrontation' in techniques:
                moments.append({
                    'turn': idx + 1,
                    'type': 'learning_opportunity',
                    'description': 'Opportunity to use reflection instead',
                    'techniques': techniques,
                })
            
            # Breakthrough moments (significant tone shift)
            tone_shift = choice.get('tone_shift', 0)
            if tone_shift > 0.2:
                moments.append({
                    'turn': idx + 1,
                    'type': 'breakthrough',
                    'description': 'Significant progress in openness',
                    'tone_shift': tone_shift,
                })
        
        return moments[:5]  # Limit to top 5 moments
    
    def _generate_recommendations(
        self,
        dimension_scores: Dict[str, DimensionScore],
        technique_breakdown: Dict[str, int]
    ) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Identify weakest dimension
        weakest = min(dimension_scores.items(), key=lambda x: x[1].score)
        if weakest[1].score < 6.0:
            recommendations.append(
                f"Focus on improving {weakest[1].dimension_id}: {weakest[1].improvement_areas[0] if weakest[1].improvement_areas else 'Practice this skill more'}"
            )
        
        # Check technique balance
        reflection_count = technique_breakdown.get('simple_reflection', 0) + technique_breakdown.get('complex_reflection', 0)
        question_count = technique_breakdown.get('open_question', 0) + technique_breakdown.get('closed_question', 0)
        
        if reflection_count < question_count:
            recommendations.append(
                "Try to use more reflections relative to questions - aim for 2:1 ratio"
            )
        
        # Check for overuse of non-adherent techniques
        non_adherent = sum(
            count for tech, count in technique_breakdown.items()
            if self.TECHNIQUE_WEIGHTS.get(tech, 0) < 0
        )
        
        if non_adherent > 2:
            recommendations.append(
                "Watch for the 'righting reflex' - practice staying in the patient's perspective longer"
            )
        
        # Add strength-based recommendations
        strongest = max(dimension_scores.items(), key=lambda x: x[1].score)
        if strongest[1].score >= 8.0:
            recommendations.append(
                f"Your {strongest[1].dimension_id} is strong - use this to support other areas"
            )
        
        return recommendations[:3]  # Limit to top 3
    
    def _empty_result(self) -> ScoringResult:
        """Return empty scoring result"""
        return ScoringResult(
            overall_score=5.0,
            dimension_scores={},
            technique_breakdown={},
            key_moments=[],
            recommendations=["Complete more choices to receive detailed scoring"],
        )
    
    def calculate_competency_scores(
        self,
        attempt: MIPracticeAttempt
    ) -> Dict[str, float]:
        """
        Calculate MAPS competency scores from an attempt.
        
        Returns dict mapping competency IDs to scores (1-10).
        """
        scoring_result = self.score_attempt(attempt)
        
        competency_scores = {}
        
        # Map dimensions to competencies
        for dim_id, dim_score in scoring_result.dimension_scores.items():
            dim_config = self.DIMENSIONS.get(dim_id, {})
            for comp_id in dim_config.get('competency_ids', []):
                if comp_id in competency_scores:
                    # Average if multiple dimensions map to same competency
                    competency_scores[comp_id] = (
                        competency_scores[comp_id] + dim_score.score
                    ) / 2
                else:
                    competency_scores[comp_id] = dim_score.score
        
        return competency_scores
    
    def generate_final_scores(self, attempt: MIPracticeAttempt) -> FinalScores:
        """
        Generate FinalScores object from attempt.
        
        This is the main entry point for final scoring after attempt completion.
        """
        scoring_result = self.score_attempt(attempt)
        
        # Calculate competency scores
        competency_scores = self.calculate_competency_scores(attempt)
        
        # Count resistance triggers
        resistance_triggered = sum(
            1 for c in attempt.choices_made
            if c.get('rapport_impact', 0) < 0
        )
        
        # Build technique counts
        technique_counts = scoring_result.technique_breakdown
        
        return FinalScores(
            overall_score=scoring_result.overall_score,
            competency_scores=competency_scores,
            technique_counts=technique_counts,
            resistance_triggered=resistance_triggered,
            rapport_built=attempt.current_rapport_score > 0,
            final_tone_position=attempt.tone_spectrum_position,
        )

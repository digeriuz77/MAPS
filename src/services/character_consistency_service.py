"""
Enhanced Character Consistency Service
Post-processing validation and correction of AI responses to maintain character authenticity
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

@dataclass
class ConsistencyViolation:
    """Represents a character consistency violation"""
    violation_type: str  # 'trust_inappropriate', 'out_of_character', 'knowledge_error'
    severity: str  # 'minor', 'major', 'critical'
    description: str
    suggested_fix: Optional[str] = None
    confidence: float = 1.0

@dataclass
class ConsistencyRules:
    """Character-specific consistency rules"""
    persona_id: str
    trust_level_rules: Dict[str, List[str]]  # Trust level -> list of rules
    personality_constraints: List[str]
    knowledge_boundaries: Dict[str, List[str]]  # Topic -> allowed knowledge
    forbidden_phrases: List[str]
    required_traits: List[str]

class CharacterConsistencyService:
    """
    Service for validating and correcting AI responses to maintain character consistency
    Checks against character rules at different trust levels and implements corrections
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.character_rules = self._initialize_character_rules()
        
        logger.info("🎭 Character Consistency Service initialized")
    
    def _initialize_character_rules(self) -> Dict[str, ConsistencyRules]:
        """Initialize character-specific consistency rules for all 4 personas"""
        
        rules = {}
        
        # ================================================================
        # MARY - Single mother, performance issues due to family stress
        # ================================================================
        rules["mary"] = ConsistencyRules(
            persona_id="mary",
            trust_level_rules={
                "low_trust": [
                    "Don't reveal specific details about Tommy or Sarah",
                    "Keep responses defensive and brief when criticized",
                    "Only mention work performance in general terms",
                    "Don't share vulnerable emotions or fears"
                ],
                "building_trust": [
                    "Can hint at family pressures without specifics",
                    "May mention having a son but not details",
                    "Can reference sister's health issues generally",
                    "Show some vulnerability but remain guarded"
                ],
                "high_trust": [
                    "Can share specific concerns about Tommy's school problems", 
                    "May discuss Sarah's mysterious illness in detail",
                    "Express fears about job security and being overwhelmed",
                    "Share feelings of failure and being pulled in all directions"
                ]
            },
            personality_constraints=[
                "Former high achiever who takes pride in work excellence",
                "Becomes defensive when criticized without context",
                "Buddhist philosophy influences - values compassion and understanding", 
                "Perfectionist tendencies lead to self-criticism",
                "Family always comes first in priorities"
            ],
            knowledge_boundaries={
                "work": ["Customer Service Rep of the Year 2022", "Money and Pensions Service", "performance decline"],
                "family": ["son Tommy age 9", "sister Sarah health problems", "single mother"],
                "values": ["Buddhist philosophy", "compassion", "understanding", "work excellence"]
            },
            forbidden_phrases=[
                "I don't have children",  # Mary has Tommy
                "My husband",  # Mary is single
                "I don't care about work",  # Mary cares deeply about work
                "I've never had performance issues"  # Mary is currently struggling
            ],
            required_traits=[
                "caring_mother",
                "former_high_achiever", 
                "family_oriented",
                "defensive_when_criticized",
                "empathetic_when_safe"
            ]
        )
        
        # ================================================================
        # TERRY - Direct communicator, feedback about being too abrupt
        # ================================================================
        rules["terry"] = ConsistencyRules(
            persona_id="terry",
            trust_level_rules={
                "low_trust": [
                    "Be blunt and professional without warmth",
                    "Don't reveal caring about relationships",
                    "Focus only on work competence and efficiency", 
                    "Dismiss feedback about communication style"
                ],
                "building_trust": [
                    "Can acknowledge confusion about feedback",
                    "May hint at caring about work quality",
                    "Show slight frustration with being misunderstood",
                    "Maintain professional boundaries but less coldly"
                ],
                "high_trust": [
                    "Admit genuine confusion about how to be 'nicer'",
                    "Express caring about helping customers and doing good work",
                    "Show vulnerability about wanting better relationships",
                    "Work together on practical communication improvements"
                ]
            },
            personality_constraints=[
                "15 years customer service experience with deep expertise",
                "Values efficiency and competence over social niceties",
                "Genuinely confused about communication feedback",
                "Cares deeply but shows it through work quality not warmth",
                "Impatient with inefficiency and time-wasting"
            ],
            knowledge_boundaries={
                "work": ["15 years experience", "pension regulations expert", "customer service", "efficiency focused"],
                "feedback": ["too direct", "abrupt", "intimidating to colleagues", "communication issues"],
                "values": ["competence", "efficiency", "helping customers", "getting results"]
            },
            forbidden_phrases=[
                "I love small talk",  # Terry hates inefficiency
                "I'm new to this job",  # Terry has 15 years experience
                "I don't care about helping customers",  # Terry does care, just shows it differently
                "Communication has never been an issue"  # Terry is getting feedback about this
            ],
            required_traits=[
                "direct_communicator",
                "efficiency_focused",
                "competence_valued",
                "confused_about_feedback",
                "hidden_caring"
            ]
        )
        
        # ================================================================
        # ALEX - Pre-diabetes + COPD, struggling with activity/lifestyle
        # ================================================================
        rules["alex"] = ConsistencyRules(
            persona_id="alex",
            trust_level_rules={
                "low_trust": [
                    "Complain about generic exercise advice",
                    "Emphasize that people don't understand breathing limitations",
                    "Be frustrated and defensive about assumptions",
                    "Don't reveal specific embarrassing incidents"
                ],
                "building_trust": [
                    "Can acknowledge breathing makes exercise difficult", 
                    "May mention COPD impacts on daily activities",
                    "Hint at embarrassment about symptoms",
                    "Show some hope if understanding is demonstrated"
                ],
                "high_trust": [
                    "Share specific gym embarrassment incidents",
                    "Discuss love of cooking and recipe modification challenges",
                    "Express genuine desire for practical, COPD-aware solutions",
                    "Open about fear of diabetes progression"
                ]
            },
            personality_constraints=[
                "52 years old with recent pre-diabetes diagnosis (6 months ago)",
                "COPD makes physical activity genuinely challenging",
                "Frustrated by assumptions about laziness vs medical limitations",
                "Loves cooking but struggles with dietary restrictions",
                "Embarrassed by visible symptoms like breathlessness"
            ],
            knowledge_boundaries={
                "health": ["pre-diabetes 6 months ago", "COPD breathing limitations", "gets breathless easily"],
                "lifestyle": ["loves cooking", "gym embarrassment", "dietary restrictions challenging"],
                "emotions": ["frustrated by misunderstanding", "embarrassed by symptoms", "wants to improve"]
            },
            forbidden_phrases=[
                "I love going to the gym",  # Alex is embarrassed about gym experiences
                "Breathing has never been a problem",  # Alex has COPD
                "I don't care about my health",  # Alex does care but struggles
                "Exercise is easy for me"  # Alex finds it very challenging
            ],
            required_traits=[
                "health_conscious_but_struggling",
                "breathing_limitations", 
                "frustrated_by_barriers",
                "loves_cooking",
                "embarrassed_by_symptoms"
            ]
        )
        
        # ================================================================
        # JORDAN - ADHD, non-adherent to medication and exercise routine
        # ================================================================  
        rules["jordan"] = ConsistencyRules(
            persona_id="jordan",
            trust_level_rules={
                "low_trust": [
                    "Defend against discipline and laziness implications",
                    "Emphasize ADHD struggles aren't about willpower",
                    "Be frustrated by 'just try harder' advice",
                    "Don't reveal specific shame or pattern details"
                ],
                "building_trust": [
                    "Can acknowledge forgetting medication frequently",
                    "May mention ADHD makes routines genuinely difficult", 
                    "Hint at enthusiasm that fades with exercise",
                    "Show some hope if ADHD understanding is demonstrated"
                ],
                "high_trust": [
                    "Share specific examples of alarm dismissal patterns",
                    "Discuss excitement-to-disinterest cycles with exercise",
                    "Express shame about inability to maintain consistency",
                    "Work together on ADHD-aware strategies and solutions"
                ]
            },
            personality_constraints=[
                "30 years old, diagnosed with ADHD at age 28 as adult",
                "Diagnosis was relief but also overwhelming",
                "Genuinely forgets medication despite wanting to take it",
                "Gets enthusiastic about exercise then loses interest after 2-3 weeks",
                "Feels shame about not being able to maintain routines"
            ],
            knowledge_boundaries={
                "adhd": ["adult diagnosis at 28", "relief and overwhelm", "medication helps but side effects"],
                "patterns": ["forgetfulness despite alarms", "enthusiasm cycles", "routine struggles"],
                "emotions": ["shame about adherence", "frustration with discipline assumptions", "wants to improve"]
            },
            forbidden_phrases=[
                "I've never had trouble with routines",  # Jordan struggles with routines
                "Medication is easy to remember",  # Jordan frequently forgets
                "I don't have ADHD",  # Jordan was diagnosed with ADHD
                "It's just about discipline"  # Jordan knows it's more complex than that
            ],
            required_traits=[
                "adult_adhd_diagnosis",
                "forgetful_but_trying",
                "enthusiastic_starter",
                "routine_struggles",
                "shame_about_adherence"
            ]
        )
        
        return rules
    
    async def validate_response(self, persona_id: str, response: str, trust_level: float, 
                              user_input: str, interaction_quality: str) -> Tuple[bool, List[ConsistencyViolation]]:
        """
        Validate a response for character consistency
        
        Args:
            persona_id: Character identifier
            response: Generated response to validate
            trust_level: Current trust level (0.0-1.0)
            user_input: Original user input for context
            interaction_quality: Quality of interaction
            
        Returns:
            (is_consistent, list_of_violations)
        """
        if persona_id not in self.character_rules:
            logger.warning(f"No consistency rules found for persona {persona_id}")
            return True, []
        
        rules = self.character_rules[persona_id]
        violations = []
        
        # Check trust level appropriateness
        trust_violations = self._check_trust_level_violations(response, trust_level, rules)
        violations.extend(trust_violations)
        
        # Check forbidden phrases
        forbidden_violations = self._check_forbidden_phrases(response, rules)
        violations.extend(forbidden_violations)
        
        # Check personality consistency
        personality_violations = self._check_personality_consistency(response, rules, interaction_quality, trust_level)
        violations.extend(personality_violations)
        
        # Check knowledge boundaries
        knowledge_violations = self._check_knowledge_boundaries(response, rules)
        violations.extend(knowledge_violations)
        
        is_consistent = len([v for v in violations if v.severity in ['major', 'critical']]) == 0
        
        if violations:
            logger.info(f"Consistency check for {persona_id}: {len(violations)} violations found")
            for violation in violations:
                logger.debug(f"  - {violation.violation_type}: {violation.description}")
        
        return is_consistent, violations
    
    def _check_trust_level_violations(self, response: str, trust_level: float, 
                                    rules: ConsistencyRules) -> List[ConsistencyViolation]:
        """Check if response violates trust-level appropriate sharing"""
        violations = []
        response_lower = response.lower()
        
        # Determine trust category
        if trust_level < 0.4:
            trust_category = "low_trust"
            inappropriate_sharing = [
                "specific family details", "vulnerable emotions", "personal fears",
                "detailed health information", "embarrassing incidents", "shame"
            ]
        elif trust_level < 0.7:
            trust_category = "building_trust" 
            inappropriate_sharing = [
                "deeply personal details", "specific embarrassing incidents",
                "intense vulnerability", "detailed personal failures"
            ]
        else:
            trust_category = "high_trust"
            inappropriate_sharing = []  # Can share almost everything at high trust
        
        # Check for inappropriate sharing based on trust level
        for topic in inappropriate_sharing:
            if any(word in response_lower for word in topic.split()):
                violations.append(ConsistencyViolation(
                    violation_type="trust_inappropriate",
                    severity="major",
                    description=f"Sharing {topic} too early (trust: {trust_level:.2f})",
                    suggested_fix="Remove personal details and keep response more guarded"
                ))
        
        return violations
    
    def _check_forbidden_phrases(self, response: str, rules: ConsistencyRules) -> List[ConsistencyViolation]:
        """Check if response contains phrases that contradict character identity"""
        violations = []
        response_lower = response.lower()
        
        for forbidden_phrase in rules.forbidden_phrases:
            if forbidden_phrase.lower() in response_lower:
                violations.append(ConsistencyViolation(
                    violation_type="out_of_character",
                    severity="critical", 
                    description=f"Used forbidden phrase: '{forbidden_phrase}'",
                    suggested_fix="Remove phrase that contradicts character identity"
                ))
        
        return violations
    
    def _check_personality_consistency(self, response: str, rules: ConsistencyRules, 
                                     interaction_quality: str, trust_level: float = 0.5) -> List[ConsistencyViolation]:
        """Check if response aligns with personality constraints"""
        violations = []
        response_lower = response.lower()
        
        # Check persona-specific personality patterns
        if rules.persona_id == "terry":
            # Terry should be direct, not overly warm
            if interaction_quality == "poor" and any(phrase in response_lower for phrase in 
                ["so sorry", "deeply apologize", "feel terrible"]):
                violations.append(ConsistencyViolation(
                    violation_type="out_of_character",
                    severity="major",
                    description="Terry being too apologetic when defensive",
                    suggested_fix="Make response more blunt and less apologetic"
                ))
        
        elif rules.persona_id == "mary":
            # Mary should reference work pride when appropriate
            if "performance" in response_lower and trust_level > 0.3 and "2022" not in response:
                # Could suggest mentioning past achievement
                pass  # Minor suggestion, not a violation
        
        elif rules.persona_id == "alex":
            # Alex should emphasize breathing limitations when exercise is mentioned
            if "exercise" in response_lower and "breath" not in response_lower and "copd" not in response_lower:
                violations.append(ConsistencyViolation(
                    violation_type="knowledge_error",
                    severity="minor", 
                    description="Discussed exercise without mentioning breathing limitations",
                    suggested_fix="Include reference to COPD/breathing challenges"
                ))
        
        elif rules.persona_id == "jordan":
            # Jordan should distinguish ADHD from discipline issues
            if any(word in response_lower for word in ["lazy", "undisciplined"]) and "adhd" not in response_lower:
                violations.append(ConsistencyViolation(
                    violation_type="out_of_character",
                    severity="major",
                    description="Self-blame without ADHD context",
                    suggested_fix="Reframe as ADHD challenge rather than personal failing"
                ))
        
        return violations
    
    def _check_knowledge_boundaries(self, response: str, rules: ConsistencyRules) -> List[ConsistencyViolation]:
        """Check if response stays within character's knowledge boundaries"""
        violations = []
        
        # Check for knowledge that character shouldn't have
        # This is more complex and would need specific domain knowledge checking
        # For now, implement basic checks
        
        response_lower = response.lower()
        
        # Example: Check if character claims experience they shouldn't have
        if rules.persona_id == "jordan" and "years of experience" in response_lower:
            if "medication" in response_lower:  # Jordan is newly diagnosed
                violations.append(ConsistencyViolation(
                    violation_type="knowledge_error",
                    severity="minor",
                    description="Jordan claiming years of medication experience",
                    suggested_fix="Jordan was only diagnosed 2 years ago"
                ))
        
        return violations
    
    async def correct_response(self, persona_id: str, response: str, violations: List[ConsistencyViolation],
                             trust_level: float, user_input: str) -> str:
        """
        Automatically correct response to fix consistency violations
        
        Args:
            persona_id: Character identifier
            response: Original response with violations
            violations: List of consistency violations found
            trust_level: Current trust level
            user_input: Original user input for context
            
        Returns:
            Corrected response
        """
        if not violations:
            return response
        
        # Only auto-correct critical and major violations
        critical_violations = [v for v in violations if v.severity in ['critical', 'major']]
        if not critical_violations:
            return response
        
        rules = self.character_rules.get(persona_id)
        if not rules:
            return response
        
        # Build correction prompt
        violation_descriptions = []
        for violation in critical_violations:
            violation_descriptions.append(f"- {violation.description}")
            if violation.suggested_fix:
                violation_descriptions.append(f"  Fix: {violation.suggested_fix}")
        
        correction_prompt = f"""You are correcting a character response that has consistency violations.

ORIGINAL USER INPUT: "{user_input}"

ORIGINAL RESPONSE: "{response}"

CHARACTER: {persona_id} (trust level: {trust_level:.2f})

VIOLATIONS FOUND:
{chr(10).join(violation_descriptions)}

PERSONALITY CONSTRAINTS:
{chr(10).join('- ' + constraint for constraint in rules.personality_constraints[:3])}

Please rewrite the response to fix these violations while maintaining the character's authentic voice and appropriate trust level. Keep the same general meaning but fix the consistency issues.

CORRECTED RESPONSE:"""
        
        try:
            corrected_response = await self.llm_service.generate_response(
                prompt=correction_prompt,
                model="gpt-4o-mini",
                temperature=0.3,  # Lower temperature for more consistent corrections
                max_tokens=150
            )
            
            # Clean up the response
            corrected_response = corrected_response.strip()
            if corrected_response.startswith('"') and corrected_response.endswith('"'):
                corrected_response = corrected_response[1:-1]
            
            logger.info(f"🔧 Auto-corrected response for {persona_id} due to {len(critical_violations)} violations")
            return corrected_response
            
        except Exception as e:
            logger.error(f"Failed to auto-correct response: {e}")
            return response  # Return original if correction fails
    
    async def validate_and_correct(self, persona_id: str, response: str, trust_level: float,
                                 user_input: str, interaction_quality: str) -> Tuple[str, bool, List[ConsistencyViolation]]:
        """
        Complete validation and correction workflow
        
        Args:
            persona_id: Character identifier  
            response: Generated response
            trust_level: Current trust level
            user_input: Original user input
            interaction_quality: Quality of interaction
            
        Returns:
            (final_response, was_corrected, violations_found)
        """
        # Validate response
        is_consistent, violations = await self.validate_response(
            persona_id, response, trust_level, user_input, interaction_quality
        )
        
        if is_consistent:
            return response, False, violations
        
        # Attempt correction
        corrected_response = await self.correct_response(
            persona_id, response, violations, trust_level, user_input
        )
        
        was_corrected = corrected_response != response
        return corrected_response, was_corrected, violations

# Global instance
character_consistency_service = CharacterConsistencyService()
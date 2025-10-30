"""
Enhanced Character Consistency Service - Database-Driven (V2)
Post-processing validation and correction of AI responses to maintain character authenticity
ALL persona data loaded from Supabase - NO HARDCODED PERSONAS
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from src.services.llm_service import LLMService
from supabase import Client

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
    """Character-specific consistency rules loaded from database"""
    persona_id: str
    forbidden_phrases: List[str]
    required_traits: List[str]
    knowledge_boundaries: Dict[str, List[str]]
    personality_constraints: List[str]
    trust_level_rules: Dict[str, List[str]]
    length_constraints: Dict[str, Dict[str, int]]

class CharacterConsistencyService:
    """
    Service for validating and correcting AI responses to maintain character consistency
    Loads all rules from database - NO HARDCODED PERSONA DATA
    """

    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.llm_service = LLMService()
        self._rules_cache: Dict[str, ConsistencyRules] = {}

        logger.info("🎭 Character Consistency Service V2 initialized (database-driven)")

    async def get_consistency_rules(self, persona_id: str) -> Optional[ConsistencyRules]:
        """
        Load consistency rules from database with caching
        """
        # Check cache first
        if persona_id in self._rules_cache:
            return self._rules_cache[persona_id]

        try:
            # Load from database
            result = self.supabase.table('character_consistency_rules')\
                .select('*')\
                .eq('persona_id', persona_id)\
                .single()\
                .execute()

            if not result.data:
                logger.warning(f"No consistency rules found for persona {persona_id}")
                return None

            data = result.data

            # Convert to dataclass
            rules = ConsistencyRules(
                persona_id=persona_id,
                forbidden_phrases=data.get('forbidden_phrases', []),
                required_traits=data.get('required_traits', []),
                knowledge_boundaries=data.get('knowledge_boundaries', {}),
                personality_constraints=data.get('personality_constraints', []),
                trust_level_rules=data.get('trust_level_rules', {}),
                length_constraints=data.get('length_constraints', {})
            )

            # Cache for future use
            self._rules_cache[persona_id] = rules

            logger.debug(f"Loaded consistency rules for {persona_id} from database")
            return rules

        except Exception as e:
            logger.error(f"Failed to load consistency rules for {persona_id}: {e}")
            return None

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
        rules = await self.get_consistency_rules(persona_id)

        if not rules:
            logger.warning(f"No consistency rules found for persona {persona_id} - skipping validation")
            return True, []

        violations = []

        # Check trust level appropriateness
        trust_violations = self._check_trust_level_violations(response, trust_level, rules)
        violations.extend(trust_violations)

        # Check forbidden phrases
        forbidden_violations = self._check_forbidden_phrases(response, rules)
        violations.extend(forbidden_violations)

        # Check personality consistency
        personality_violations = self._check_personality_constraints(response, rules, interaction_quality, trust_level)
        violations.extend(personality_violations)

        # Check knowledge boundaries
        knowledge_violations = self._check_knowledge_boundaries(response, rules)
        violations.extend(knowledge_violations)

        # Check length constraints
        length_violations = self._check_length_constraints(response, trust_level, rules, interaction_quality)
        violations.extend(length_violations)

        is_consistent = len([v for v in violations if v.severity in ['major', 'critical']]) == 0

        if violations:
            logger.info(f"Consistency check for {persona_id}: {len(violations)} violations found")
            for violation in violations:
                logger.debug(f"  - {violation.violation_type}: {violation.description}")

        return is_consistent, violations

    def _check_trust_level_violations(self, response: str, trust_level: float,
                                    rules: ConsistencyRules) -> List[ConsistencyViolation]:
        """Check if response violates trust-level appropriate sharing using database rules"""
        violations = []
        response_lower = response.lower()

        # Determine trust tier
        if trust_level < 0.4:
            tier = "defensive"
        elif trust_level < 0.6:
            tier = "cautious"
        elif trust_level < 0.8:
            tier = "opening"
        else:
            tier = "trusting"

        # Get rules for current tier from database
        tier_rules = rules.trust_level_rules.get(tier, [])

        # Check if response violates any tier-specific rules
        # This is a simplified check - could be enhanced with more sophisticated pattern matching
        for rule in tier_rules:
            rule_lower = rule.lower()
            # Check for keywords that indicate rule violation
            if "don't" in rule_lower or "avoid" in rule_lower or "keep" in rule_lower:
                # Extract what should be avoided
                if "specific" in rule_lower and "specific" in response_lower:
                    violations.append(ConsistencyViolation(
                        violation_type="trust_inappropriate",
                        severity="major",
                        description=f"Sharing too specifically for {tier} tier (trust: {trust_level:.2f})",
                        suggested_fix=f"Follow tier rule: {rule}"
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

    def _check_personality_constraints(self, response: str, rules: ConsistencyRules,
                                     interaction_quality: str, trust_level: float) -> List[ConsistencyViolation]:
        """Check if response aligns with personality constraints from database"""
        violations = []

        # Check required traits are reflected (simplified - could use ML for better detection)
        # For now, just ensure response isn't completely out of character based on length and tone

        response_lower = response.lower()

        # Example: If personality constraint mentions "defensive when criticized"
        for constraint in rules.personality_constraints:
            constraint_lower = constraint.lower()
            if "defensive" in constraint_lower and interaction_quality == "poor":
                # Should show some defensiveness
                collaborative_words = ["let's work together", "i'd love to", "that sounds great"]
                if any(phrase in response_lower for phrase in collaborative_words):
                    violations.append(ConsistencyViolation(
                        violation_type="personality_inconsistent",
                        severity="minor",
                        description="Response too collaborative for poor interaction quality",
                        suggested_fix="Show appropriate guardedness given criticism"
                    ))

        return violations

    def _check_knowledge_boundaries(self, response: str, rules: ConsistencyRules) -> List[ConsistencyViolation]:
        """Check if response references knowledge character shouldn't have"""
        violations = []

        # This is a placeholder - could be enhanced with knowledge graph
        # For now, just ensure no contradictory information

        return violations

    def _check_length_constraints(self, response: str, trust_level: float,
                                 rules: ConsistencyRules, interaction_quality: str) -> List[ConsistencyViolation]:
        """Check if response length is appropriate for trust level"""
        violations = []

        # Determine tier
        if trust_level < 0.4:
            tier = "defensive"
        elif trust_level < 0.6:
            tier = "cautious"
        elif trust_level < 0.8:
            tier = "opening"
        else:
            tier = "trusting"

        # Get length constraints for tier
        tier_constraints = rules.length_constraints.get(tier, {})

        response_length = len(response)

        # Check max length (especially for hostile interactions in defensive tier)
        if interaction_quality == "poor" and tier == "defensive":
            hostile_max = tier_constraints.get("hostile_max", 150)
            if response_length > hostile_max:
                violations.append(ConsistencyViolation(
                    violation_type="length_inappropriate",
                    severity="minor",
                    description=f"Response too long for {tier} tier with poor interaction ({response_length} > {hostile_max})",
                    suggested_fix=f"Shorten to under {hostile_max} characters"
                ))
        else:
            max_length = tier_constraints.get("max", 300)
            if response_length > max_length:
                violations.append(ConsistencyViolation(
                    violation_type="length_inappropriate",
                    severity="minor",
                    description=f"Response exceeds max for {tier} tier ({response_length} > {max_length})",
                    suggested_fix=f"Shorten to under {max_length} characters"
                ))

        return violations

    async def validate_and_correct(self, persona_id: str, response: str, trust_level: float,
                                  user_input: str, interaction_quality: str) -> Tuple[str, bool, List[ConsistencyViolation]]:
        """
        Validate response and optionally correct violations

        Returns:
            (corrected_response, was_corrected, violations)
        """
        is_consistent, violations = await self.validate_response(
            persona_id, response, trust_level, user_input, interaction_quality
        )

        # If no critical violations, return original
        critical_violations = [v for v in violations if v.severity == 'critical']
        if not critical_violations:
            return response, False, violations

        # Apply simple corrections
        corrected = response
        was_corrected = False

        rules = await self.get_consistency_rules(persona_id)

        if rules:
            # Remove forbidden phrases
            for phrase in rules.forbidden_phrases:
                if phrase.lower() in corrected.lower():
                    # Simple removal (could be more sophisticated)
                    corrected = re.sub(re.escape(phrase), '', corrected, flags=re.IGNORECASE)
                    corrected = corrected.strip()
                    was_corrected = True

        # If still has issues, could invoke LLM for rewrite (not implemented here)

        return corrected, was_corrected, violations

    def clear_cache(self):
        """Clear the rules cache (useful after database updates)"""
        self._rules_cache.clear()
        logger.info("Consistency rules cache cleared")


# Global instance (will be initialized with supabase client)
character_consistency_service = None

def initialize_character_consistency_service(supabase_client: Client):
    """Initialize the global character consistency service"""
    global character_consistency_service
    character_consistency_service = CharacterConsistencyService(supabase_client)
    return character_consistency_service

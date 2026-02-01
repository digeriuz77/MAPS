"""
Trust Configuration Service V2 - Database-Driven
Uses NEW trust_configuration table from migration 0008
Supports rich multipliers and modifiers for nuanced trust progression
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

logger = logging.getLogger(__name__)

@dataclass
class PersonaTrustConfig:
    """Persona-specific trust progression configuration from trust_configuration table"""
    persona_id: str

    # Quality deltas (base trust change per interaction quality)
    quality_deltas: Dict[str, float]  # {"poor": -0.02, "adequate": 0.01, "good": 0.04, "excellent": 0.06}

    # Empathy multipliers (multiply delta based on empathy tone)
    empathy_multipliers: Dict[str, float]  # {"hostile": 0.3, "neutral": 1.0, "supportive": 1.6, ...}

    # Trajectory adjustments (bonus/penalty for trust direction)
    trajectory_adjustments: Dict[str, float]  # {"declining": -0.01, "stable": 0.0, "building": 0.02, ...}

    # Approach modifiers (multiply based on communication approach)
    approach_modifiers: Dict[str, float]  # {"directive": 1.2, "collaborative": 1.9, ...}

    # Other parameters
    trust_decay_rate: float
    tier_transition_momentum: float
    regression_penalty: float

class TrustConfigurationService:
    """Service for managing persona-specific trust progression using trust_configuration table"""

    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._persona_cache: Dict[str, tuple] = {}  # Cache: {persona_id: (config, timestamp)}
        self._cache_duration = 300  # 5 minutes

    def get_persona_trust_config(self, persona_id: str, use_cache: bool = True) -> Optional[PersonaTrustConfig]:
        """
        Get trust configuration for a specific persona from trust_configuration table

        Args:
            persona_id: ID of the persona
            use_cache: Whether to use cached configuration

        Returns:
            PersonaTrustConfig or None if not found
        """
        # Check cache
        if use_cache and persona_id in self._persona_cache:
            cached_config, timestamp = self._persona_cache[persona_id]
            if time.time() - timestamp < self._cache_duration:
                return cached_config

        try:
            # Query trust_configuration table
            result = self.supabase.table('trust_configuration').select('*').eq(
                'persona_id', persona_id
            ).execute()

            if not result.data:
                logger.warning(f"No trust configuration found for persona {persona_id}, using defaults")
                return self._get_default_trust_config(persona_id)

            data = result.data[0]

            # Build PersonaTrustConfig
            config = PersonaTrustConfig(
                persona_id=persona_id,
                quality_deltas=data.get('quality_deltas', {}),
                empathy_multipliers=data.get('empathy_multipliers', {}),
                trajectory_adjustments=data.get('trajectory_adjustments', {}),
                approach_modifiers=data.get('approach_modifiers', {}),
                trust_decay_rate=float(data.get('trust_decay_rate', 0.01)),
                tier_transition_momentum=float(data.get('tier_transition_momentum', 0.02)),
                regression_penalty=float(data.get('regression_penalty', -0.03))
            )

            # Cache it
            self._persona_cache[persona_id] = (config, time.time())

            logger.debug(f"Loaded trust configuration for {persona_id} from database")
            return config

        except Exception as e:
            logger.error(f"Failed to load trust configuration for persona {persona_id}: {e}", exc_info=True)
            return self._get_default_trust_config(persona_id)

    def _get_default_trust_config(self, persona_id: str = "default") -> PersonaTrustConfig:
        """Return default trust configuration when database lookup fails"""
        return PersonaTrustConfig(
            persona_id=persona_id,
            quality_deltas={
                "poor": -0.02,
                "adequate": 0.01,
                "good": 0.03,
                "excellent": 0.05
            },
            empathy_multipliers={
                "hostile": 0.3,
                "neutral": 1.0,
                "supportive": 1.6,
                "deeply_empathetic": 2.0
            },
            trajectory_adjustments={
                "declining": -0.01,
                "stable": 0.0,
                "building": 0.015,
                "breakthrough": 0.03
            },
            approach_modifiers={
                "directive": 0.8,
                "questioning": 1.0,
                "curious": 1.3,
                "collaborative": 1.7,
                "supportive": 1.8
            },
            trust_decay_rate=0.01,
            tier_transition_momentum=0.02,
            regression_penalty=-0.03
        )

    def calculate_trust_delta(
        self,
        quality: str,  # "poor", "adequate", "good", "excellent"
        empathy_tone: str,  # "hostile", "neutral", "supportive", "deeply_empathetic"
        approach: str,  # "directive", "questioning", "curious", "collaborative", "supportive"
        trajectory: str,  # "declining", "stable", "building", "breakthrough"
        trust_config: PersonaTrustConfig,
        max_delta_per_turn: float = 0.15  # Cap to prevent unrealistic jumps
    ) -> float:
        """
        Calculate trust delta using the rich multiplier system

        Formula:
        delta = (base_quality_delta + trajectory_adjustment) × empathy_multiplier × approach_modifier
        delta = min(delta, max_delta_per_turn)  # Cap at reasonable max

        Args:
            quality: Interaction quality
            empathy_tone: Empathy level shown
            approach: Communication approach used
            trajectory: Recent trust direction
            trust_config: Persona configuration
            max_delta_per_turn: Maximum allowed delta (prevents unrealistic jumps)

        Returns:
            Calculated trust delta (can be negative)
        """
        # Get base delta from quality
        base_delta = float(trust_config.quality_deltas.get(quality, 0.01))

        # Add trajectory adjustment
        trajectory_adj = float(trust_config.trajectory_adjustments.get(trajectory, 0.0))
        subtotal = base_delta + trajectory_adj

        # Apply empathy multiplier
        empathy_mult = float(trust_config.empathy_multipliers.get(empathy_tone, 1.0))
        subtotal = subtotal * empathy_mult

        # Apply approach modifier
        approach_mod = float(trust_config.approach_modifiers.get(approach, 1.0))
        final_delta = subtotal * approach_mod

        # Cap at max_delta_per_turn (both positive and negative)
        if final_delta > 0:
            final_delta = min(final_delta, max_delta_per_turn)
        else:
            final_delta = max(final_delta, -max_delta_per_turn)

        logger.info(
            f"💰 Trust delta calculation: quality={quality} ({base_delta:+.3f}) + "
            f"trajectory={trajectory} ({trajectory_adj:+.3f}) × empathy={empathy_tone} ({empathy_mult:.2f}x) × "
            f"approach={approach} ({approach_mod:.2f}x) = {final_delta:+.3f}"
        )

        return final_delta

    def clear_cache(self, persona_id: Optional[str] = None):
        """Clear configuration cache for one or all personas"""
        if persona_id:
            self._persona_cache.pop(persona_id, None)
            logger.info(f"Cleared trust config cache for {persona_id}")
        else:
            self._persona_cache.clear()
            logger.info("Cleared all trust config caches")


# Global instance (will be initialized with supabase client)
trust_configuration_service = None

def initialize_trust_configuration_service(supabase_client):
    """Initialize the global trust configuration service"""
    global trust_configuration_service
    trust_configuration_service = TrustConfigurationService(supabase_client)
    return trust_configuration_service

def get_trust_configuration_service(supabase_client=None):
    """Get the global trust configuration service"""
    if trust_configuration_service is None and supabase_client:
        return initialize_trust_configuration_service(supabase_client)
    return trust_configuration_service

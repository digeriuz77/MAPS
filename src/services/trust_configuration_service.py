"""
Trust Configuration Service

Manages persona-specific trust progression parameters from enhanced_personas table.
Each persona has unique trust deltas based on their personality traits.
"""

import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
import asyncio

logger = logging.getLogger(__name__)

@dataclass
class PersonaTrustConfig:
    """Persona-specific trust progression configuration"""
    # Trust deltas (from persona)
    trust_delta_excellent: float
    trust_delta_good: float
    trust_delta_adequate: float
    trust_delta_poor: float
    
    # Trust thresholds (from persona)
    trust_threshold_cautious: float
    trust_threshold_opening: float
    trust_threshold_trusting: float
    
    # Starting level (from persona)
    trust_starting_level: float
    
    # Fixed empathy thresholds (global)
    empathy_threshold_excellent: float = 8.5
    empathy_threshold_good: float = 7.0
    empathy_threshold_adequate: float = 5.0
    empathy_threshold_poor: float = 4.0

class TrustConfigurationService:
    """Service for managing persona-specific trust progression configuration"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        self._persona_cache = {}  # Cache by persona_id
        self._cache_duration = 300  # 5 minutes cache
    
    async def get_persona_trust_config(self, persona_id: str, use_cache: bool = True) -> PersonaTrustConfig:
        """
        Get trust configuration for a specific persona using trust_variable + trust_tiers lookup
        
        Args:
            persona_id: ID of the persona to get configuration for
            use_cache: Whether to use cached configuration (default: True)
            
        Returns:
            PersonaTrustConfig object with persona-specific settings
        """
        
        # Check cache first
        if use_cache and persona_id in self._persona_cache:
            cached_config, timestamp = self._persona_cache[persona_id]
            import time
            if time.time() - timestamp < self._cache_duration:
                return cached_config
        
        try:
            # Step 1: Get persona's trust_variable
            persona_result = self.supabase.table('enhanced_personas').select(
                'trust_variable'
            ).eq('persona_id', persona_id).execute()

            if not persona_result.data:
                logger.warning(f"No persona found for ID {persona_id}, using defaults")
                return self._get_default_trust_config()

            trust_variable = float(persona_result.data[0].get('trust_variable', 0.50))

            # Step 2: Find which trust tier this persona falls into
            # Find the tier with the highest min_threshold that's <= trust_variable
            # This avoids ambiguity at boundary overlaps (e.g., trust_variable = 0.25)
            tiers_result = self.supabase.table('trust_tiers').select(
                'tier_name, min_threshold, trust_delta_excellent, trust_delta_good, trust_delta_adequate, trust_delta_poor'
            ).lte('min_threshold', trust_variable
            ).order('min_threshold', desc=True  # Get highest matching threshold
            ).limit(1  # Take only the best match
            ).execute()

            if not tiers_result.data:
                logger.warning(f"No trust tier found for trust_variable {trust_variable}, using defaults")
                return self._get_default_trust_config()

            tier_data = tiers_result.data[0]
            
            # Step 3: Build PersonaTrustConfig with tier-specific deltas
            trust_config = PersonaTrustConfig(
                trust_delta_excellent=float(tier_data['trust_delta_excellent']),
                trust_delta_good=float(tier_data['trust_delta_good']),
                trust_delta_adequate=float(tier_data['trust_delta_adequate']),
                trust_delta_poor=float(tier_data['trust_delta_poor']),
                
                # Use fixed thresholds for conversation trust levels (0.0-1.0 scale)
                trust_threshold_cautious=0.45,
                trust_threshold_opening=0.65,
                trust_threshold_trusting=0.80,
                
                # Starting trust level based on persona's trust variable (0.0-1.0 scale)
                trust_starting_level=0.3 + (trust_variable * 0.4)  # Scale 0.0-1.0 to 0.3-0.7 range
            )
            
            # Update cache
            import time
            self._persona_cache[persona_id] = (trust_config, time.time())
            
            logger.info(f"Trust configuration loaded for persona {persona_id}: tier={tier_data['tier_name']}, variable={trust_variable}, excellent_delta={trust_config.trust_delta_excellent}")
            
            return trust_config
            
        except Exception as e:
            logger.error(f"Failed to load trust configuration for persona {persona_id}: {e}, using defaults")
            return self._get_default_trust_config()
    
    def _get_default_trust_config(self) -> PersonaTrustConfig:
        """Get default trust configuration if persona data unavailable (0.0-1.0 scale)"""
        return PersonaTrustConfig(
            trust_delta_excellent=0.020,  # Scaled to 0.0-1.0 range
            trust_delta_good=0.015,
            trust_delta_adequate=0.010,
            trust_delta_poor=-0.015,
            trust_threshold_cautious=0.45,  # Scaled to 0.0-1.0 range
            trust_threshold_opening=0.65,
            trust_threshold_trusting=0.80,
            trust_starting_level=0.3  # Defensive starting point
        )
    
    def calculate_trust_delta(self, empathy_score: float, config: PersonaTrustConfig) -> float:
        """
        Calculate trust delta based on empathy score and persona configuration
        
        Args:
            empathy_score: Current empathy score (0-10)
            config: Persona trust configuration with delta values
            
        Returns:
            Trust delta to apply
        """
        
        if empathy_score >= config.empathy_threshold_excellent:
            return config.trust_delta_excellent
        elif empathy_score >= config.empathy_threshold_good:
            return config.trust_delta_good
        elif empathy_score >= config.empathy_threshold_adequate:
            return config.trust_delta_adequate
        elif empathy_score < config.empathy_threshold_poor:
            return config.trust_delta_poor
        else:
            return 0.0  # No change for neutral scores
    
    def get_trust_tier(self, trust_level: float, config: PersonaTrustConfig) -> str:
        """
        Determine trust tier based on trust level and persona thresholds
        
        Args:
            trust_level: Current trust level (0.0-1.0 scale)
            config: Persona trust configuration with threshold values
            
        Returns:
            Trust tier name
        """
        
        if trust_level >= config.trust_threshold_trusting:
            return "trusting"
        elif trust_level >= config.trust_threshold_opening:
            return "opening"
        elif trust_level >= config.trust_threshold_cautious:
            return "cautious"
        else:
            return "defensive"
    
    async def update_persona_trust_variable(self, persona_id: str, new_trust_variable: float) -> bool:
        """
        Update a persona's trust_variable (which determines their trust tier)
        
        Args:
            persona_id: ID of the persona to update
            new_trust_variable: New trust variable (0.00-1.00)
            
        Returns:
            Success status
        """
        
        # Validate range
        if not (0.0 <= new_trust_variable <= 1.0):
            logger.error(f"Trust variable must be between 0.00 and 1.00, got {new_trust_variable}")
            return False
        
        try:
            result = self.supabase.table('enhanced_personas').update({
                'trust_variable': new_trust_variable
            }).eq('persona_id', persona_id).execute()
            
            if result.data:
                logger.info(f"Updated trust_variable to {new_trust_variable} for persona {persona_id}")
                # Clear cache to force reload
                if persona_id in self._persona_cache:
                    del self._persona_cache[persona_id]
                return True
            else:
                logger.error(f"Failed to update trust_variable for persona {persona_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating persona trust variable: {e}")
            return False
    
    async def get_persona_trust_summary(self, persona_id: str) -> Dict[str, Any]:
        """Get a summary of persona trust configuration for debugging"""
        
        config = await self.get_persona_trust_config(persona_id)
        
        return {
            "persona_id": persona_id,
            "trust_deltas": {
                "excellent (8.5+)": f"+{config.trust_delta_excellent}",
                "good (7.0+)": f"+{config.trust_delta_good}",
                "adequate (5.0+)": f"+{config.trust_delta_adequate}",
                "poor (<4.0)": f"{config.trust_delta_poor}"
            },
            "trust_thresholds": {
                "cautious": config.trust_threshold_cautious,
                "opening": config.trust_threshold_opening,
                "trusting": config.trust_threshold_trusting
            },
            "empathy_thresholds": {
                "excellent": config.empathy_threshold_excellent,
                "good": config.empathy_threshold_good,
                "adequate": config.empathy_threshold_adequate,
                "poor": config.empathy_threshold_poor
            },
            "starting_trust": config.trust_starting_level,
            "estimated_turns_to_trusting": self._estimate_turns_to_trusting(config)
        }
    
    def _estimate_turns_to_trusting(self, config: PersonaTrustConfig) -> Dict[str, int]:
        """Estimate turns needed to reach trusting tier"""
        
        start_trust = config.trust_starting_level
        target_trust = config.trust_threshold_trusting
        trust_needed = target_trust - start_trust
        
        return {
            "perfect_empathy": int(trust_needed / config.trust_delta_excellent) if config.trust_delta_excellent > 0 else 999,
            "good_empathy": int(trust_needed / config.trust_delta_good) if config.trust_delta_good > 0 else 999,
            "adequate_empathy": int(trust_needed / config.trust_delta_adequate) if config.trust_delta_adequate > 0 else 999
        }

    async def get_all_persona_trust_variations(self) -> Dict[str, Dict[str, Any]]:
        """Get trust configurations for all personas to see variation"""
        
        try:
            result = self.supabase.table('enhanced_personas').select(
                'persona_id, name, trust_variable'
            ).execute()
            
            personas = {}
            for persona in result.data:
                # Get the trust config for this persona (includes tier lookup)
                trust_config = await self.get_persona_trust_config(persona['persona_id'], use_cache=False)
                
                personas[persona['persona_id']] = {
                    "name": persona['name'],
                    "trust_variable": persona['trust_variable'],
                    "trust_deltas": {
                        "excellent": trust_config.trust_delta_excellent,
                        "good": trust_config.trust_delta_good,
                        "adequate": trust_config.trust_delta_adequate,
                        "poor": trust_config.trust_delta_poor
                    },
                    "starting_trust": trust_config.trust_starting_level,
                    "trust_thresholds": {
                        "cautious": trust_config.trust_threshold_cautious,
                        "opening": trust_config.trust_threshold_opening,
                        "trusting": trust_config.trust_threshold_trusting
                    }
                }
            
            return personas
            
        except Exception as e:
            logger.error(f"Error fetching persona trust variations: {e}")
            return {}

# Global instance for easy access
_trust_config_service = None

def get_trust_configuration_service(supabase_client=None):
    """Get or create trust configuration service instance"""
    global _trust_config_service
    
    if _trust_config_service is None:
        if supabase_client is None:
            from src.dependencies import get_supabase_client
            supabase_client = get_supabase_client()
        
        _trust_config_service = TrustConfigurationService(supabase_client)
        logger.info("Trust configuration service initialized")
    
    return _trust_config_service
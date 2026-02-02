"""
Multi-Model Provider Service - Production-ready LLM abstraction
Enables seamless switching between OpenAI, Claude, and Gemini with failover support
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from src.config.settings import get_settings
from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ModelProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic" 
    GEMINI = "gemini"

@dataclass
class ModelConfig:
    """Configuration for a specific model"""
    provider: ModelProvider
    model_name: str
    max_tokens: int = 1000
    temperature: float = 0.7
    cost_per_1k_tokens: float = 0.0
    supports_system_prompt: bool = True
    recommended_for: List[str] = None

@dataclass
class ProviderResponse:
    """Response from an LLM provider"""
    content: str
    provider: ModelProvider
    model: str
    tokens_used: int = 0
    response_time: float = 0.0
    success: bool = True
    error: Optional[str] = None

class MultiModelProviderService:
    """
    Production-ready multi-model provider service with:
    - Automatic failover between providers
    - Cost tracking and optimization
    - Performance monitoring
    - Model-specific prompt optimization
    """

    def __init__(self):
        self.settings = get_settings()
        self.llm_service = LLMService()
        
        # Model configurations optimized for latency and performance
        self.model_configs = {
            # OpenAI Models - Optimized for speed
            "gpt-4.1-nano": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4.1-nano",
                max_tokens=500,  # Smaller for speed
                temperature=0.3,
                cost_per_1k_tokens=0.0001,  # Estimated
                recommended_for=["fast_analysis", "immediate_feedback", "state_management"]
            ),
            "gpt-4o": ModelConfig(
                provider=ModelProvider.OPENAI,
                model_name="gpt-4o",
                max_tokens=1500,
                temperature=0.7,
                cost_per_1k_tokens=0.005,
                recommended_for=["high_quality", "complex_reasoning"]
            ),
            
            # Claude Models - High quality fallbacks
            "claude-3-haiku": ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-haiku",
                max_tokens=1000,
                temperature=0.7,
                cost_per_1k_tokens=0.00025,
                recommended_for=["fast_response", "cost_effective", "analysis_fallback"]
            ),
            "claude-3-sonnet": ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-sonnet", 
                max_tokens=1500,
                temperature=0.7,
                cost_per_1k_tokens=0.003,
                recommended_for=["balanced", "persona_fallback", "mi_analysis_fallback"]
            ),
            "claude-3-5-sonnet": ModelConfig(
                provider=ModelProvider.ANTHROPIC,
                model_name="claude-3-5-sonnet",
                max_tokens=1500,
                temperature=0.7,
                cost_per_1k_tokens=0.003,
                recommended_for=["high_quality_fallback", "complex_reasoning"]
            ),
            
            # Gemini Models - Optimized for persona responses
            "gemini-2.5-flash-lite-001": ModelConfig(
                provider=ModelProvider.GEMINI,
                model_name="gemini-2.5-flash-lite-001",
                max_tokens=1200,  # Good for longer persona responses
                temperature=0.8,  # Higher for personality variation
                cost_per_1k_tokens=0.00008,  # Estimated - very cost effective
                recommended_for=["persona_response", "long_form", "authentic_conversation"]
            ),
            "gemini-2.5-flash": ModelConfig(
                provider=ModelProvider.GEMINI,
                model_name="gemini-2.5-flash",
                max_tokens=1000,
                temperature=0.7,
                cost_per_1k_tokens=0.0001,
                recommended_for=["persona_primary", "creative_response"]
            ),
            "gemini-1.5-pro": ModelConfig(
                provider=ModelProvider.GEMINI,
                model_name="gemini-1.5-pro",
                max_tokens=1500,
                temperature=0.7,
                cost_per_1k_tokens=0.002,
                recommended_for=["high_quality_fallback"]
            )
        }
        
        # Optimized failover chains - NO gemini-1.5-flash per user preference
        self.failover_chains = {
            "persona_response": ["gemini-2.5-flash-lite-001", "gemini-2.5-flash", "claude-3-sonnet"],
            "mi_analysis": ["gpt-4.1-nano", "claude-3-haiku", "gemini-2.5-flash"],
            "memory_formation": ["gpt-4.1-nano", "claude-3-haiku", "gemini-2.5-flash"],
            "behavioral_state": ["gpt-4.1-nano", "claude-3-haiku"],
            "fast_feedback": ["gpt-4.1-nano", "claude-3-haiku"],
            "general": ["gpt-4.1-nano", "gemini-2.5-flash-lite-001", "claude-3-haiku"],
            "cost_effective": ["gemini-2.5-flash-lite-001", "gpt-4.1-nano", "claude-3-haiku"],
            "high_quality": ["claude-3-5-sonnet", "gpt-4o", "gemini-1.5-pro"]
        }
    
    async def generate_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        use_case: str = "general",
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        enable_failover: bool = True
    ) -> ProviderResponse:
        """
        Generate LLM response with automatic model selection and failover chain.
        
        This is the main entry point for multi-model LLM generation. It implements
        a resilient architecture with:
        
        1. **Use Case-Based Model Selection**: Automatically selects the optimal
           model based on the use case (persona_response, mi_analysis, etc.)
        
        2. **Failover Chain**: If the primary model fails, automatically tries
           backup models in priority order until one succeeds
        
        3. **Graceful Degradation**: Returns a friendly error message if all
           models in the chain fail
        
        Failover Chain Example (persona_response):
            Primary: gemini-2.5-flash-lite-001 (fast, cost-effective)
            Secondary: gemini-2.5-flash (balanced)
            Tertiary: claude-3-sonnet (high quality fallback)
        
        Args:
            prompt: The user prompt to send to the LLM
            system_prompt: Optional system prompt for context/behavior
            model: Specific model to use (if None, auto-selected by use_case)
            use_case: Category determining model selection and failover chain:
                - "persona_response": Authentic character responses
                - "mi_analysis": Motivational interviewing analysis
                - "memory_formation": Conversation memory processing
                - "fast_feedback": Quick real-time feedback
                - "high_quality": Complex reasoning tasks
            temperature: Sampling temperature (0.0-2.0, None uses config default)
            max_tokens: Maximum response tokens (None uses config default)
            enable_failover: Whether to try backup models on failure (default: True)
            
        Returns:
            ProviderResponse: Contains response content, provider info, timing,
                            and success/error status
                            
        Raises:
            No exceptions raised - failures are captured in ProviderResponse
        """
        # ============================================================================
        # STEP 1: Model Selection
        # If no specific model requested, select based on use case.
        # This optimizes for both cost and performance based on the task requirements.
        # ============================================================================
        if model is None:
            model = self.get_recommended_model(use_case)
            logger.debug(f"Auto-selected model '{model}' for use_case '{use_case}'")
        
        # ============================================================================
        # STEP 2: Primary Model Attempt
        # Try the selected (or specified) model first. This will be the optimal
        # choice based on cost/performance for this use case.
        # ============================================================================
        logger.info(f"Attempting generation with primary model: {model}")
        response = await self._try_model(
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # If primary succeeds, return immediately - no failover needed
        if response.success:
            logger.debug(f"Primary model {model} succeeded")
            return response
        
        # ============================================================================
        # STEP 3: Failover Chain Execution
        # If primary failed and failover is enabled, iterate through the failover
        # chain for this use case. Each use case has a prioritized list of
        # alternative models optimized for that specific task type.
        # ============================================================================
        if enable_failover:
            # Get failover chain for this use case, default to gpt-4o-mini if unknown
            failover_models = self.failover_chains.get(use_case, ["gpt-4o-mini"])
            logger.warning(
                f"Primary model {model} failed, initiating failover chain "
                f"({len(failover_models)} backups available)"
            )
            
            # Try each backup model in order
            for backup_model in failover_models:
                # Skip if this is the same as the failed primary (avoid retrying same model)
                if backup_model != model:
                    logger.warning(f"Trying failover model: {backup_model}")
                    
                    # Attempt generation with backup model
                    response = await self._try_model(
                        model=backup_model,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    
                    # If backup succeeds, log and return immediately
                    if response.success:
                        logger.info(f"Failover successful with {backup_model}")
                        return response
                    else:
                        logger.warning(f"Failover model {backup_model} also failed")
        
        # ============================================================================
        # STEP 4: Exhausted Failover - Graceful Degradation
        # All models in the chain have failed. Return a user-friendly error message
        # wrapped in a ProviderResponse so calling code can handle it gracefully.
        # This ensures the application remains functional even during provider outages.
        # ============================================================================
        logger.error(
            f"All models failed for use_case '{use_case}'. "
            f"Primary: {model}, Failover chain exhausted."
        )
        
        return ProviderResponse(
            content="I apologize, but I'm experiencing technical difficulties right now.",
            provider=ModelProvider.OPENAI,
            model="fallback",
            success=False,
            error="All configured models failed"
        )
    
    async def _try_model(
        self,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> ProviderResponse:
        """Try a specific model and return response with metadata"""
        
        config = self.model_configs.get(model)
        if not config:
            return ProviderResponse(
                content="",
                provider=ModelProvider.OPENAI,
                model=model,
                success=False,
                error=f"Unknown model: {model}"
            )
        
        # Use config defaults if not specified
        actual_temperature = temperature if temperature is not None else config.temperature
        actual_max_tokens = max_tokens if max_tokens is not None else config.max_tokens
        
        try:
            import time
            start_time = time.time()
            
            # Use existing LLMService for the actual API call
            content = await self.llm_service.generate_response(
                prompt=prompt,
                system_prompt=system_prompt,
                model=config.model_name,
                temperature=actual_temperature,
                max_tokens=actual_max_tokens
            )
            
            response_time = time.time() - start_time
            
            return ProviderResponse(
                content=content,
                provider=config.provider,
                model=config.model_name,
                tokens_used=self._estimate_tokens(prompt + (system_prompt or "") + content),
                response_time=response_time,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Model {model} failed: {e}")
            return ProviderResponse(
                content="",
                provider=config.provider,
                model=config.model_name,
                success=False,
                error=str(e)
            )
    
    def get_recommended_model(self, use_case: str) -> str:
        """Get the recommended model for a specific use case"""
        failover_chain = self.failover_chains.get(use_case, ["gpt-4o-mini"])
        
        # Check if the primary model is available (has API key)
        for model_name in failover_chain:
            config = self.model_configs[model_name]
            
            if self._is_provider_available(config.provider):
                return model_name
        
        # Fallback to first available model
        return "gpt-4o-mini"
    
    def _is_provider_available(self, provider: ModelProvider) -> bool:
        """Check if a provider has the required API key configured"""
        if provider == ModelProvider.OPENAI:
            return bool(self.settings.OPENAI_API_KEY)
        elif provider == ModelProvider.ANTHROPIC:
            return bool(self.settings.ANTHROPIC_API_KEY)
        elif provider == ModelProvider.GEMINI:
            return bool(self.settings.GEMINI_API_KEY)
        return False
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        return len(text) // 4
    
    def get_available_models(self) -> Dict[str, ModelConfig]:
        """Get all available models based on configured API keys"""
        available = {}
        
        for model_name, config in self.model_configs.items():
            if self._is_provider_available(config.provider):
                available[model_name] = config
        
        return available
    
    def get_cost_estimate(self, model: str, token_count: int) -> float:
        """Estimate cost for a given model and token count"""
        config = self.model_configs.get(model)
        if not config:
            return 0.0
        
        return (token_count / 1000) * config.cost_per_1k_tokens

# Global instance
multi_model_service = MultiModelProviderService()
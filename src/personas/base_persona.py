"""
Base persona abstract class
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from src.models.schemas import PersonaResponse, Message, MessageRole
from src.services.llm_service import LLMService
from src.config.settings import get_settings
from src.core.constants import ConversationConstants

logger = logging.getLogger(__name__)

class BasePersona(ABC):
    """Abstract base class for all personas"""
    
    def __init__(
        self,
        persona_id: str,
        name: str,
        description: str,
        max_tokens: int = 500
    ):
        self.persona_id = persona_id
        self.name = name
        self.description = description
        self.max_tokens = max_tokens
        self.conversation_history: List[Message] = []
        self.llm_service = LLMService()
        self.settings = get_settings()
        self.created_at = datetime.utcnow()
        
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this persona"""
        pass
        
    @abstractmethod
    def get_traits(self) -> List[str]:
        """Get the personality traits of this persona"""
        pass
        
    async def generate_response(
        self,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ) -> PersonaResponse:
        """Generate a response to the user's message"""
        
        # Add message to history
        user_message = Message(
            role=MessageRole.USER,
            content=message,
            metadata=context
        )
        self.conversation_history.append(user_message)
        
        # Prepare conversation for LLM
        system_prompt = self.get_system_prompt()
        
        # Include context in system prompt if provided
        if context:
            context_str = self._format_context(context)
            system_prompt += f"{chr(10)}{chr(10)}Current context: {context_str}"
        
        # Generate response
        try:
            response_content = await self.llm_service.generate_response(
                prompt=message,
                system_prompt=system_prompt,
                model=self.settings.DEFAULT_MODEL,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                conversation_history=self._get_recent_history()
            )
            
            # Add response to history
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=response_content
            )
            self.conversation_history.append(assistant_message)
            
            # Analyze response for traits
            activated_traits = await self._analyze_activated_traits(response_content)
            
            return PersonaResponse(
                content=response_content,
                confidence=0.85,  # Base confidence, can be adjusted
                traits_activated=activated_traits,
                analysis=self._generate_analysis(message, response_content)
            )
            
        except Exception as e:
            logger.error(f"Error generating response for persona {self.persona_id}: {e}")
            raise
            
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary into a readable string"""
        formatted_parts = []
        for key, value in context.items():
            formatted_parts.append(f"{key}: {value}")
        return ", ".join(formatted_parts)
        
    def _get_recent_history(self, limit: Optional[int] = None) -> List[Message]:
        """Get recent conversation history"""
        if limit is None:
            limit = ConversationConstants.RECENT_HISTORY_LIMIT
        return self.conversation_history[-limit:] if len(self.conversation_history) > limit else self.conversation_history
        
    async def _analyze_activated_traits(self, response: str) -> List[str]:
        """Analyze which traits were activated in the response"""
        # This is a placeholder - implement trait detection logic
        # based on response patterns
        traits = self.get_traits()
        activated = []
        
        # Simple keyword-based detection (to be enhanced)
        response_lower = response.lower()
        
        trait_keywords = {
            "defensive": ["not my fault", "unfair", "why me", "being attacked"],
            "passive_aggressive": ["fine", "whatever", "if you say so", "guess"],
            "argumentative": ["but", "however", "actually", "disagree"],
            "resistant": ["don't see why", "always worked", "unnecessary"],
            "empathetic": ["understand", "feel", "hear you", "must be"],
            "supportive": ["help", "support", "together", "we can"]
        }
        
        for trait, keywords in trait_keywords.items():
            if trait in traits and any(keyword in response_lower for keyword in keywords):
                activated.append(trait)
                
        return activated
        
    def _generate_analysis(self, message: str, response: str) -> Dict[str, Any]:
        """Generate analysis of the interaction"""
        return {
            "message_length": len(message),
            "response_length": len(response),
            "interaction_count": len(self.conversation_history) // 2,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert persona to dictionary representation"""
        return {
            "persona_id": self.persona_id,
            "name": self.name,
            "description": self.description,
            "persona_type": self.__class__.__name__,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "traits": self.get_traits(),
            "created_at": self.created_at.isoformat(),
            "conversation_count": len(self.conversation_history)
        }
        
    def reset_conversation(self) -> None:
        """Reset conversation history"""
        self.conversation_history = []
        logger.info(f"Reset conversation history for persona {self.persona_id}")

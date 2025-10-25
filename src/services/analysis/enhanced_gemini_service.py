"""
Enhanced GeminiService with database integration
"""
import logging
from typing import List, Dict, Any, Optional
from .gemini_service import GeminiService as BaseGeminiService
from .database_service import get_database_service
from .types import ParsedTurn, ConversationContext, MitiCode

logger = logging.getLogger(__name__)

class EnhancedGeminiService(BaseGeminiService):
    """Enhanced Gemini service that uses database-stored prompts and examples"""
    
    def __init__(self):
        super().__init__()
        self.db_service = get_database_service()
        self.miti_definitions = self.db_service.get_miti_code_definitions()
        self.cached_system_prompt = None
        logger.info("Enhanced Gemini service initialized with database integration")
    
    def _generate_improved_coding_prompt(
        self, 
        batch: List[ParsedTurn], 
        context: ConversationContext
    ) -> str:
        """Generate enhanced prompt using database-stored examples and definitions"""
        
        # Get system prompt from database
        if not self.cached_system_prompt:
            self.cached_system_prompt = self.db_service.get_system_prompt()
        
        # Use database prompt if available, fallback to original
        if self.cached_system_prompt:
            base_prompt = self.cached_system_prompt
        else:
            base_prompt = super()._generate_improved_coding_prompt(batch, context)
            logger.warning("Using fallback prompt - database prompt not available")
        
        # Enhance with relevant examples from database
        enhanced_prompt = self._add_relevant_examples(base_prompt, batch, context)
        
        # Add detailed MITI definitions if available
        if self.miti_definitions:
            enhanced_prompt = self._add_detailed_definitions(enhanced_prompt)
        
        return enhanced_prompt
    
    def _add_relevant_examples(
        self, 
        base_prompt: str, 
        batch: List[ParsedTurn], 
        context: ConversationContext
    ) -> str:
        """Add relevant examples from database based on conversation content"""
        
        # Analyze conversation to determine relevant examples
        relevant_codes = self._identify_likely_codes(batch)
        
        # Get examples that demonstrate these codes
        examples = self.db_service.get_examples_for_codes(relevant_codes[:3])  # Limit to top 3
        
        if not examples:
            return base_prompt
        
        examples_section = "\n\n**RELEVANT EXAMPLES FROM DATABASE:**\n"
        
        for example in examples[:2]:  # Limit to 2 examples to avoid prompt bloat
            examples_section += f"{chr(10)}**{example['title']}** (Focus: {', '.join(example['focus_codes'])}){chr(10)}"
            examples_section += f"Transcript:{chr(10)}{example['transcript_snippet']}{chr(10)}"
            examples_section += f"Learning Point: {example['learning_points']}{chr(10)}"
            examples_section += f"Rationale: {example['rationale']}{chr(10)}"
        
        # Insert examples before the input turns section
        input_marker = "**INPUT TURNS"
        if input_marker in base_prompt:
            return base_prompt.replace(input_marker, examples_section + "\n" + input_marker)
        else:
            return base_prompt + examples_section
    
    def _add_detailed_definitions(self, prompt: str) -> str:
        """Add detailed MITI code definitions from database"""
        
        definitions_section = "\n\n**DETAILED MITI CODE DEFINITIONS:**\n"
        
        # Add practitioner codes
        definitions_section += "\n**PRACTITIONER CODES:**\n"
        for code, definition in self.miti_definitions.items():
            if definition['category'] == 'practitioner':
                definitions_section += f"{chr(10)}**{code} - {definition['full_name']}:**{chr(10)}"
                definitions_section += f"Definition: {definition['definition']}{chr(10)}"
                definitions_section += f"Key Indicators: {definition['key_indicators']}{chr(10)}"
                definitions_section += f"Examples: {definition['examples']}{chr(10)}"
        
        # Add client codes
        definitions_section += "\n**CLIENT CODES:**\n"
        for code, definition in self.miti_definitions.items():
            if definition['category'] == 'client':
                definitions_section += f"{chr(10)}**{code} - {definition['full_name']}:**{chr(10)}"
                definitions_section += f"Definition: {definition['definition']}{chr(10)}"
                definitions_section += f"Examples: {definition['examples']}{chr(10)}"
        
        # Insert before coding guidelines
        guidelines_marker = "**MITI CODING RULES"
        if guidelines_marker in prompt:
            return prompt.replace(guidelines_marker, definitions_section + "\n" + guidelines_marker)
        else:
            return prompt + definitions_section
    
    def _identify_likely_codes(self, batch: List[ParsedTurn]) -> List[str]:
        """Identify likely MITI codes based on conversation content analysis"""
        likely_codes = []
        
        for turn in batch:
            text_lower = turn.text.lower()
            
            # Simple heuristics to identify likely codes
            if '?' in turn.text:
                likely_codes.append('Q')
            
            if any(phrase in text_lower for phrase in ['sounds like', 'seems like', 'i hear']):
                likely_codes.append('CR')
            
            if any(phrase in text_lower for phrase in ['you are', 'you have', 'you seem']):
                likely_codes.append('SR')
            
            if any(phrase in text_lower for phrase in ['that takes', 'you showed', 'impressive']):
                likely_codes.append('AF')
            
            if any(phrase in text_lower for phrase in ['your choice', 'up to you', 'you decide']):
                likely_codes.append('EA')
            
            if any(phrase in text_lower for phrase in ['you should', 'you need to', 'you have to']):
                likely_codes.append('Per')
        
        # Remove duplicates while preserving order
        seen = set()
        unique_codes = []
        for code in likely_codes:
            if code not in seen:
                seen.add(code)
                unique_codes.append(code)
        
        return unique_codes
    
    def get_learning_examples(
        self, 
        codes: List[str], 
        difficulty: str = 'intermediate'
    ) -> List[Dict[str, Any]]:
        """Get learning examples for specific MITI codes"""
        return self.db_service.get_examples_for_codes(codes)
    
    def get_examples_by_performance(self, performance_type: str) -> List[Dict[str, Any]]:
        """Get examples showing excellent or poor MI performance"""
        if performance_type.lower() in ['excellent', 'good']:
            return self.db_service.get_excellent_examples()
        elif performance_type.lower() in ['poor', 'bad']:
            return self.db_service.get_poor_examples()
        else:
            return self.db_service.get_training_examples(example_type=performance_type)

# Update the singleton to use enhanced service
def get_enhanced_gemini_service() -> EnhancedGeminiService:
    """Get enhanced Gemini service with database integration"""
    return EnhancedGeminiService()
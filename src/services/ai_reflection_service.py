"""
AI-Powered Reflection Service using LLM for dynamic response generation
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.services.llm_service import LLMService
from src.config.settings import get_settings

logger = logging.getLogger(__name__)

class AIReflectionService:
    """
    Reflection service that actually uses AI models to generate contextual responses
    """
    
    def __init__(self):
        self.llm_service = LLMService()
        self.settings = get_settings()
        self.reflection_stage = "greeting"
        self.reflection_history = []
        self.coach_name = "Dr. Sarah Chen"
        self.coach_style = "warm, empathetic, and insightful"
        
    async def start_reflection_session(self) -> Dict[str, Any]:
        """Start a new AI-powered reflection session"""
        self.reflection_stage = "greeting"
        self.reflection_history = []
        
        # Generate personalized greeting using AI
        system_prompt = f"""You are {self.coach_name}, an expert Motivational Interviewing reflection coach.
Your communication style is {self.coach_style}.

Generate a warm, personalized greeting for someone starting a reflection session about their MI practice.
Keep it concise (2-3 sentences) and end with an open-ended question about their recent practice experience."""

        greeting = await self.llm_service.generate_response(
            prompt="Generate reflection greeting",
            system_prompt=system_prompt,
            model=self.settings.REFLECTION_MODEL,  # Use dedicated cost-optimized reflection model
            temperature=0.7,
            max_tokens=150
        )
        
        logger.info("Started AI-powered reflection session")
        
        return {
            "status": "started",
            "coach_name": self.coach_name,
            "greeting": greeting,
            "stage": self.reflection_stage,
            "current_stage": self.reflection_stage
        }
    
    async def process_reflection_response(
        self,
        user_response: str,
        analysis_report: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate AI response based on user input and analysis report"""
        
        # Store user response
        self.reflection_history.append({
            "stage": self.reflection_stage,
            "user": user_response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Build comprehensive system prompt
        system_prompt = self._build_system_prompt(analysis_report)
        
        # Build user prompt with full context
        user_prompt = self._build_user_prompt(user_response, analysis_report)
        
        # Generate AI response
        try:
            coach_response = await self.llm_service.generate_response(
                prompt=user_prompt,
                system_prompt=system_prompt,
                model=self.settings.REFLECTION_MODEL,  # Use dedicated cost-optimized reflection model
                temperature=0.8,
                max_tokens=300,
                conversation_history=self._get_conversation_history()
            )
            
            # Store coach response
            self.reflection_history.append({
                "stage": self.reflection_stage,
                "coach": coach_response,
                "timestamp": datetime.now().isoformat()
            })
            
            # Advance to next stage
            current_stage = self.reflection_stage
            next_stage = self._advance_stage()
            
            return {
                "coach_response": coach_response,
                "current_stage": current_stage,
                "next_stage": next_stage,
                "coach_name": self.coach_name
            }
            
        except Exception as e:
            logger.error(f"Failed to generate AI response: {e}")
            return {
                "error": "Failed to generate response",
                "coach_response": "I apologize, but I'm having trouble processing that. Could you please share your thoughts again?",
                "current_stage": self.reflection_stage,
                "next_stage": self.reflection_stage
            }
    
    def _build_system_prompt(self, analysis_report: Optional[str]) -> str:
        """Build comprehensive system prompt for the AI"""
        
        stage_guidance = {
            "greeting": "Welcome the practitioner warmly and ask about their recent MI practice experience.",
            "what_went_well": "Explore specific moments that went well. Be curious about what made these moments successful.",
            "struggles": "Gently explore challenges without judgment. Show empathy and normalize difficulties.",
            "differently": "Help them identify specific changes they could make. Focus on concrete, actionable insights.",
            "observations": "Provide specific observations about their MI practice based on what they've shared and any analysis report.",
            "suggestions": "Offer 2-3 specific, practical suggestions for improvement based on their reflections and analysis.",
            "summary": "Summarize key insights from the reflection and affirm their commitment to learning."
        }
        
        base_prompt = f"""You are {self.coach_name}, an expert Motivational Interviewing (MI) reflection coach.
Your communication style is {self.coach_style}.

Current reflection stage: {self.reflection_stage}
Stage guidance: {stage_guidance.get(self.reflection_stage, "")}

IMPORTANT PRINCIPLES:
1. Use MI spirit: Partnership, Acceptance, Compassion, Evocation
2. Ask open-ended questions to deepen reflection
3. Reflect back what you hear with empathy
4. Affirm strengths and efforts
5. Be curious rather than prescriptive
6. Keep responses concise (3-5 sentences)
7. End with a thought-provoking question (except in summary stage)
"""
        
        if analysis_report:
            base_prompt += f"""

ANALYSIS REPORT PROVIDED:
The practitioner has shared their MITI analysis report. Use this information to:
- Reference specific scores or observations when relevant
- Provide targeted feedback based on identified strengths and areas for growth
- Make connections between their reflections and the analysis data
- Offer specific suggestions aligned with the report's findings

Analysis Report Content:
{analysis_report}
"""
        
        return base_prompt
    
    def _build_user_prompt(self, user_response: str, analysis_report: Optional[str]) -> str:
        """Build the user prompt with full context"""
        
        prompt = f"Practitioner's reflection: {user_response}"
        
        if self.reflection_stage == "observations" and analysis_report:
            prompt += "\n\nProvide specific observations connecting their reflection to the analysis report data."
        elif self.reflection_stage == "suggestions" and analysis_report:
            prompt += "\n\nOffer targeted suggestions based on both their reflection and the specific areas identified in the analysis report."
        
        return prompt
    
    def _get_conversation_history(self) -> List[Dict[str, str]]:
        """Get formatted conversation history for context"""
        history = []
        
        # Include last 3 exchanges for context
        recent_history = self.reflection_history[-6:] if len(self.reflection_history) > 6 else self.reflection_history
        
        for entry in recent_history:
            if "user" in entry:
                history.append({"role": "user", "content": entry["user"]})
            elif "coach" in entry:
                history.append({"role": "assistant", "content": entry["coach"]})
        
        return history
    
    def _advance_stage(self) -> str:
        """Advance to next reflection stage"""
        stages = ["greeting", "what_went_well", "struggles", "differently", 
                 "observations", "suggestions", "summary"]
        
        try:
            current_index = stages.index(self.reflection_stage)
            if current_index < len(stages) - 1:
                self.reflection_stage = stages[current_index + 1]
            else:
                return "complete"
        except ValueError:
            self.reflection_stage = "what_went_well"
        
        return self.reflection_stage
    
    async def get_reflection_summary(self) -> Dict[str, Any]:
        """Generate AI-powered summary of the reflection session"""
        if not self.reflection_history:
            return {"error": "No reflection data available"}
        
        # Build summary prompt
        conversation_text = "\n\n".join([
            f"{entry.get('stage', 'unknown').upper()}: "
            f"{'User' if 'user' in entry else 'Coach'}: "
            f"{entry.get('user', entry.get('coach', ''))}"
            for entry in self.reflection_history
        ])
        
        system_prompt = f"""You are {self.coach_name}. 
Create a concise summary of this reflection session that includes:
1. Key strengths identified
2. Main challenges discussed  
3. Specific areas for improvement
4. 2-3 actionable next steps

Keep it encouraging and focused on growth."""

        summary = await self.llm_service.generate_response(
            prompt=f"Summarize this reflection session:\n\n{conversation_text}",
            system_prompt=system_prompt,
            model=self.settings.REFLECTION_MODEL,  # Use dedicated cost-optimized reflection model
            temperature=0.7,
            max_tokens=400
        )
        
        return {
            "summary": summary,
            "coach_name": self.coach_name,
            "session_length": len(self.reflection_history),
            "completed_stages": [entry["stage"] for entry in self.reflection_history if "user" in entry]
        }

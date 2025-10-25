"""
Enhanced Reflection Service with Supabase Coach Integration
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.services.coach_service import get_coach_service
# Note: MotivationalCoachPersona reference removed - using database-driven personas
# from src.personas.motivational_coach import MotivationalCoachPersona
from src.models.schemas import PersonaResponse

logger = logging.getLogger(__name__)

class SupabaseReflectionCoach:
    """
    Enhanced reflection coach that uses the unified Supabase coach for personalized guidance
    """
    
    # Use the unified coach ID
    UNIFIED_COACH_ID = '00000000-0000-0000-0000-000000000001'
    
    def __init__(self, coach_id: str = None):
        # Always use the unified coach ID, ignore passed coach_id
        self.coach_id = self.UNIFIED_COACH_ID
        self.coach_service = get_coach_service()
        self.coach_data = None
        self.reflection_stage = "greeting"
        self.reflection_history = []
        self.context_tags = []
        
        # Load coach data from Supabase
        self._load_coach_data()
    
    def _load_coach_data(self):
        """Load detailed coach information from Supabase"""
        self.coach_data = self.coach_service.get_coach_by_id(self.coach_id)
        if self.coach_data:
            logger.info(f"Loaded coach: {self.coach_data['name']}")
        else:
            logger.error(f"Failed to load coach data for ID: {self.coach_id}")
    
    def start_reflection_session(self) -> Dict[str, Any]:
        """
        Start a new reflection session with personalized greeting
        
        Returns:
            Dict containing greeting and session info
        """
        if not self.coach_data:
            return {
                "error": "Coach not available",
                "message": "Unable to load coach data from database"
            }
        
        self.reflection_stage = "greeting"
        self.reflection_history = []
        
        # Get personalized greeting prompt
        greeting_prompt = self.coach_service.get_contextual_prompt(
            self.coach_id,
            "greeting",
            context_tags=["warm_welcome", "partnership"]
        )
        
        if not greeting_prompt:
            greeting_prompt = f"Welcome! I'm {self.coach_data['name']}, and I'm here to guide you through a reflective exploration of your MI practice. This is your space to think deeply about your experience."
        
        # Personalize based on coach style
        coaching_style = self.coach_data.get('coaching_style', 'supportive')
        communication_style = self.coach_data.get('communication_style', {})
        
        # Add coach personality to the greeting
        if communication_style.get('warmth', 0) > 0.8:
            greeting_prompt = f"Hello there! {greeting_prompt}"
        
        return {
            "status": "started",
            "coach_name": self.coach_data['name'],
            "coach_title": self.coach_data.get('title', ''),
            "coaching_style": coaching_style,
            "greeting": greeting_prompt,
            "stage": self.reflection_stage,
            "session_id": f"reflection_{self.coach_id}_{int(datetime.now().timestamp())}"
        }
    
    def process_reflection_response(
        self, 
        user_response: str, 
        analysis_context: Optional[Dict[str, Any]] = None,
        analysis_report: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Enhanced process user's reflection response with optional analysis report
        
        Args:
            user_response: The user's reflection input
            analysis_context: Optional analysis results to inform responses
            analysis_report: Optional analysis report text (like MITI report)
            
        Returns:
            Dict containing coach response and session info
        """
        if not self.coach_data:
            return {"error": "Coach not available"}
        
        # Store the user's response
        self.reflection_history.append({
            "stage": self.reflection_stage,
            "user_response": user_response,
            "analysis_report": analysis_report,  # Store analysis report if provided
            "timestamp": datetime.now().isoformat()
        })
        
        # Determine context tags based on response and analysis
        self._analyze_response_context(user_response, analysis_report)
        
        # Generate coach response BEFORE moving to next stage
        coach_response = self._generate_stage_response(user_response, analysis_context, analysis_report)
        
        # Now move to next stage for next iteration
        current_stage = self.reflection_stage  # Save current stage for response
        next_stage = self._advance_to_next_stage()
        
        return {
            "coach_response": coach_response,
            "current_stage": current_stage,  # Current stage that was just completed
            "next_stage": next_stage,        # Next stage for next response
            "progress": len(self.reflection_history),
            "context_tags": self.context_tags,
            "coach_name": self.coach_data['name'],
            "stage_completed": current_stage,
            "total_stages": 7
        }
    
    def _analyze_response_context(self, user_response: str, analysis_report: Optional[str] = None):
        """Enhanced context analysis including analysis report"""
        response_lower = user_response.lower()
        
        # Clear previous context tags
        self.context_tags = []
        
        # Determine emotional tone from user response
        if any(word in response_lower for word in ['good', 'great', 'well', 'successful', 'positive']):
            self.context_tags.append('positive_experience')
        elif any(word in response_lower for word in ['difficult', 'hard', 'struggled', 'challenging', 'frustrated']):
            self.context_tags.append('challenging_experience')
        elif any(word in response_lower for word in ['unsure', 'uncertain', 'confused', 'mixed']):
            self.context_tags.append('uncertain_experience')
        
        # Analyze content focus
        if any(word in response_lower for word in ['client', 'person', 'individual', 'they', 'them']):
            self.context_tags.append('client_focused')
        elif any(word in response_lower for word in ['i felt', 'my approach', 'i tried', 'i said']):
            self.context_tags.append('self_focused')
        
        # Analyze MI technique mentions
        if any(word in response_lower for word in ['questions', 'asking', 'open-ended']):
            self.context_tags.append('questioning_focus')
        elif any(word in response_lower for word in ['listened', 'listening', 'reflected', 'reflection']):
            self.context_tags.append('listening_focus')
        elif any(word in response_lower for word in ['affirmation', 'affirmed', 'strengths', 'positive']):
            self.context_tags.append('affirmation_focus')
        
        # NEW: Analyze analysis report if provided
        if analysis_report:
            self.context_tags.append('has_analysis_report')
            report_lower = analysis_report.lower()
            
            # Extract key areas from analysis report
            if 'partnership' in report_lower:
                if any(phrase in report_lower for phrase in ['demonstrates', 'shows', 'good', 'strong']):
                    self.context_tags.append('strong_partnership')
                else:
                    self.context_tags.append('needs_partnership')
            
            if 'empathy' in report_lower:
                if any(phrase in report_lower for phrase in ['demonstrates', 'shows', 'good', 'strong']):
                    self.context_tags.append('strong_empathy')
                else:
                    self.context_tags.append('needs_empathy')
            
            if 'change talk' in report_lower:
                if 'minimal' in report_lower or 'limited' in report_lower:
                    self.context_tags.append('needs_change_talk')
                else:
                    self.context_tags.append('good_change_talk')
            
            if 'sustain talk' in report_lower:
                if 'softening' in report_lower or 'effective' in report_lower:
                    self.context_tags.append('good_sustain_handling')
                else:
                    self.context_tags.append('needs_sustain_handling')
    
    def _generate_stage_response(
        self, 
        user_response: str, 
        analysis_context: Optional[Dict[str, Any]] = None,
        analysis_report: Optional[str] = None
    ) -> str:
        """Enhanced stage response generation with analysis report integration"""
        
        # Get base prompt for current stage with enhanced context
        base_prompt = self.coach_service.get_contextual_prompt(
            self.coach_id,
            self.reflection_stage,
            self.context_tags,
            user_response
        )
        
        if not base_prompt:
            base_prompt = self._get_enhanced_fallback_response()
        
        # Enhance response based on coach personality
        enhanced_response = self._personalize_response(base_prompt, user_response)
        
        # NEW: Integrate analysis report insights throughout reflection
        if analysis_report:
            enhanced_response = self._integrate_analysis_report(enhanced_response, analysis_report)
        
        # Add analysis integration if available (for compatibility)
        if analysis_context and self.reflection_stage in ['observations', 'suggestions']:
            enhanced_response = self._integrate_analysis_feedback(enhanced_response, analysis_context)
        
        return enhanced_response
    
    def _personalize_response(self, base_response: str, user_response: str) -> str:
        """Personalize response based on coach's adaptive communication style"""
        communication_style = self.coach_data.get('communication_style', {})
        mi_approach = self.coach_data.get('mi_approach', {})
        
        # Get adaptive ranges for warmth and empathy
        warmth_range = communication_style.get('warmth_range', [0.8, 1.0])
        empathy_range = communication_style.get('empathy_range', [0.8, 1.0])
        
        # Determine appropriate warmth level based on context
        warmth_level = warmth_range[1] if 'challenging' in self.context_tags else warmth_range[0]
        empathy_level = empathy_range[1] if any(tag in self.context_tags for tag in ['challenging', 'uncertain']) else empathy_range[0]
        
        # Add empathetic reflections if needed
        if empathy_level > 0.9:
            if 'challenging' in self.context_tags:
                base_response = f"I can hear that this brought up some real challenges for you. {base_response}"
            elif 'positive' in self.context_tags:
                base_response = f"There's a sense of satisfaction in how you describe that experience. {base_response}"
            elif 'uncertain' in self.context_tags:
                base_response = f"I notice some uncertainty in your reflection, which is completely natural. {base_response}"
        
        # Add warmth and curiosity based on adaptive levels
        curiosity_level = communication_style.get('curiosity', 0.9)
        if curiosity_level > 0.85 and '?' not in base_response:
            curiosity_phrases = [
                "I'm curious to hear more about your experience with that.",
                "What draws your attention about that particular moment?",
                "I wonder what your intuition tells you about that.",
                "What else comes to mind as you reflect on that?"
            ]
            import random
            base_response += f" {random.choice(curiosity_phrases)}"
        
        return base_response
    
    def _integrate_analysis_feedback(
        self, 
        base_response: str, 
        analysis_context: Dict[str, Any]
    ) -> str:
        """Integrate MITI analysis results into coaching response"""
        if not analysis_context:
            return base_response
        
        # Get relevant MI knowledge for the analysis results
        analysis_results = analysis_context.get('analysis_result', {})
        
        if self.reflection_stage == 'observations':
            # Add specific observations based on analysis
            if hasattr(analysis_results, 'report'):
                summary = getattr(analysis_results.report, 'summary_insights', '')
                if summary:
                    base_response += f" Looking at your conversation, I notice {summary.lower()}"
        
        elif self.reflection_stage == 'suggestions':
            # Add targeted suggestions based on analysis
            if hasattr(analysis_results, 'report'):
                recommendations = getattr(analysis_results.report, 'actionable_recommendations', {})
                if hasattr(recommendations, 'immediate_focus'):
                    immediate_focus = getattr(recommendations, 'immediate_focus', '')
                    if immediate_focus:
                        base_response += f" Based on your conversation analysis, you might focus on {immediate_focus.lower()}"
        
        return base_response
    
    def _advance_to_next_stage(self) -> str:
        """Advance to the next reflection stage and return it"""
        stage_order = [
            'greeting', 'what_went_well', 'struggles', 'differently', 
            'observations', 'suggestions', 'summary'
        ]
        
        try:
            current_index = stage_order.index(self.reflection_stage)
            if current_index < len(stage_order) - 1:
                # Move to next stage
                self.reflection_stage = stage_order[current_index + 1]
                return self.reflection_stage
            else:
                # Already at last stage
                return 'complete'
        except ValueError:
            # If current stage not found, default to next logical stage
            self.reflection_stage = 'what_went_well'
            return self.reflection_stage
    
    def _get_next_stage(self) -> str:
        """Deprecated - use _advance_to_next_stage instead"""
        return self._advance_to_next_stage()
    
    def _integrate_analysis_report(self, base_response: str, analysis_report: str) -> str:
        """Integrate analysis report insights based on current stage"""
        
        if self.reflection_stage == 'what_went_well':
            # Look for strengths in the analysis report
            strengths = self._extract_strengths_from_report(analysis_report)
            if strengths:
                base_response += f" I notice from your analysis report that {strengths[0].lower()}"
        
        elif self.reflection_stage == 'struggles':
            # Look for areas needing improvement
            challenges = self._extract_challenges_from_report(analysis_report)
            if challenges:
                base_response += f" Your analysis report suggests some areas where you might explore further: {challenges[0].lower()}"
        
        elif self.reflection_stage == 'differently':
            # Suggest specific techniques based on report
            suggestions = self._extract_suggestions_from_report(analysis_report)
            if suggestions:
                base_response += f" Based on your analysis, you might consider {suggestions[0].lower()}"
        
        elif self.reflection_stage == 'observations':
            # Provide specific observations from the report
            base_response += f"\n\nLooking at your analysis report, I can see some specific patterns in your MI practice..."
            observations = self._extract_detailed_observations(analysis_report)
            if observations:
                base_response += f" {observations}"
        
        elif self.reflection_stage == 'suggestions':
            # Provide targeted suggestions based on report scores
            targeted_suggestions = self._generate_targeted_suggestions(analysis_report)
            if targeted_suggestions:
                base_response += f"\n\nBased on your specific analysis results, here are some focused areas for development: {targeted_suggestions}"
        
        return base_response
    
    def _extract_strengths_from_report(self, report: str) -> List[str]:
        """Extract strengths mentioned in analysis report"""
        strengths = []
        lines = report.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['demonstrates', 'shows', 'good', 'strong', 'effective']):
                if any(skill in line.lower() for skill in ['partnership', 'empathy', 'change talk', 'reflection']):
                    strengths.append(line.strip())
        
        return strengths[:2]  # Return top 2 strengths
    
    def _extract_challenges_from_report(self, report: str) -> List[str]:
        """Extract areas needing improvement from analysis report"""
        challenges = []
        lines = report.split('\n')
        
        for line in lines:
            if any(word in line.lower() for word in ['however', 'needs', 'could', 'minimal', 'limited', 'hinders']):
                challenges.append(line.strip())
        
        return challenges[:2]  # Return top 2 challenges
    
    def _extract_suggestions_from_report(self, report: str) -> List[str]:
        """Extract specific suggestions from analysis report"""
        suggestions = []
        lines = report.split('\n')
        
        for line in lines:
            if any(phrase in line.lower() for phrase in ['could be', 'would be', 'might', 'should', 'beneficial']):
                suggestions.append(line.strip())
        
        return suggestions[:2]
    
    def _extract_detailed_observations(self, report: str) -> str:
        """Extract key observations for the observations stage"""
        # Parse report sections and extract key points
        sections = report.split('\n\n')
        observations = []
        
        for section in sections:
            if any(word in section for word in ['Partnership', 'Empathy', 'Change Talk', 'Sustain Talk']):
                # Extract the first sentence which usually contains the main observation
                sentences = section.split('.')
                if len(sentences) > 1:
                    observations.append(sentences[1].strip())
        
        return ' '.join(observations[:3])  # Combine top 3 observations
    
    def _generate_targeted_suggestions(self, report: str) -> str:
        """Generate specific suggestions based on report analysis"""
        suggestions = []
        
        # Check specific areas and provide targeted advice
        if 'partnership' in report.lower() and any(word in report.lower() for word in ['hinders', 'detracts', 'limited']):
            suggestions.append("focusing more on collaborative exploration rather than information-gathering questions")
        
        if 'empathy' in report.lower() and 'could be' in report.lower():
            suggestions.append("balancing empathy with solution-focused exploration")
        
        if 'change talk' in report.lower() and 'minimal' in report.lower():
            suggestions.append("improving skills in eliciting and reinforcing change talk through more targeted questions")
        
        if 'sustain talk' in report.lower() and 'more effective' in report.lower():
            suggestions.append("using more reflective approaches when clients express resistance")
        
        return ', '.join(suggestions)
    
    def _get_enhanced_fallback_response(self) -> str:
        """Enhanced fallback responses with analysis awareness"""
        stage_fallbacks = {
            'greeting': "Welcome to our reflection space. I'd love to hear about your MI practice experience.",
            'what_went_well': "Tell me about the moments in your conversation that felt most natural and effective for you.",
            'struggles': "I'm curious about any parts of the conversation that felt challenging or where you wished things had gone differently.",
            'differently': "If you could approach that conversation again with what you know now, what might you try differently?",
            'observations': "I've been listening carefully to your reflections. Let me share what I'm noticing about your MI practice...",
            'suggestions': "Based on everything you've shared, I have some thoughts about next steps that might support your continued growth.",
            'summary': "Thank you for this rich reflection. Let me offer you a summary of the key insights and growth opportunities we've explored together."
        }
        
        return stage_fallbacks.get(self.reflection_stage, "Please continue sharing your thoughts about your practice.")
    
    def _get_fallback_response(self) -> str:
        """Deprecated - use _get_enhanced_fallback_response instead"""
        return self._get_enhanced_fallback_response()
    
    def get_reflection_summary(self) -> Dict[str, Any]:
        """Generate comprehensive reflection summary"""
        if not self.reflection_history:
            return {"error": "No reflection data available"}
        
        coach_name = self.coach_data['name'] if self.coach_data else "Your Reflection Coach"
        
        summary = {
            "session_date": datetime.now().isoformat(),
            "coach_name": coach_name,
            "coach_title": self.coach_data.get('title', '') if self.coach_data else '',
            "coaching_approach": self.coach_data.get('coaching_style', 'supportive') if self.coach_data else 'supportive',
            "reflection_stages_completed": len(self.reflection_history),
            "key_insights": self._extract_insights(),
            "growth_areas": self._extract_growth_areas(),
            "strengths_identified": self._extract_strengths(),
            "next_steps": self._generate_next_steps(),
            "reflection_responses": self.reflection_history
        }
        
        return summary
    
    def _extract_insights(self) -> List[str]:
        """Extract key insights from reflection responses"""
        insights = []
        for response in self.reflection_history:
            if response['stage'] in ['what_went_well', 'differently']:
                content = response['user_response'][:200]
                if content:
                    insights.append(f"Stage {response['stage']}: {content}")
        return insights[:3]  # Limit to top 3
    
    def _extract_growth_areas(self) -> List[str]:
        """Extract growth areas from challenges discussed"""
        growth_areas = []
        for response in self.reflection_history:
            if response['stage'] == 'struggles':
                content = response['user_response'][:150]
                if content:
                    growth_areas.append(content)
        return growth_areas
    
    def _extract_strengths(self) -> List[str]:
        """Extract identified strengths"""
        strengths = []
        for response in self.reflection_history:
            if response['stage'] == 'what_went_well':
                content = response['user_response'][:150]
                if content:
                    strengths.append(content)
        return strengths
    
    def _generate_next_steps(self) -> List[str]:
        """Generate personalized next steps based on the reflection"""
        next_steps = []
        
        # Get coach's knowledge about skill development
        knowledge_items = self.coach_service.get_coach_knowledge(
            self.coach_id,
            knowledge_type='technique',
            category='skill_development'
        )
        
        if knowledge_items:
            for item in knowledge_items[:3]:
                next_steps.append(item.get('content', ''))
        else:
            # Default next steps
            next_steps = [
                "Continue practicing open-ended questions in your conversations",
                "Focus on reflective listening to build deeper understanding",
                "Notice and affirm client strengths during your interactions"
            ]
        
        return next_steps
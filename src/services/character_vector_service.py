"""
Character Vector Database Service
Provides deep character knowledge and situational response variety
"""

import logging
import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class CharacterMemory:
    """A character's specific memory/knowledge/experience"""
    memory_id: str
    persona_id: str
    memory_type: str  # 'experience', 'knowledge', 'response_pattern', 'emotional_trigger'
    content: str
    context_tags: List[str]  # ['work_stress', 'family_pressure', 'health_concern']
    emotional_weight: float  # 0.0-1.0
    trust_level_required: float  # 0.0-1.0 when this becomes available
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None

@dataclass
class SituationalResponse:
    """A character's response pattern for specific situations"""
    response_id: str
    persona_id: str
    situation_tags: List[str]  # ['criticism', 'work_stress', 'family_mention']
    trust_level: float
    interaction_quality: str  # 'poor', 'adequate', 'good', 'excellent'
    response_style: str
    example_responses: List[str]
    emotional_tone: str
    sharing_level: str  # what they're willing to reveal
    
class CharacterVectorService:
    """
    Service for storing and retrieving character-specific knowledge, experiences,
    and response patterns to enable deep, varied persona interactions
    """
    
    def __init__(self):
        # In-memory storage for MVP (later: ChromaDB)
        self.character_memories: Dict[str, List[CharacterMemory]] = {}
        self.situational_responses: Dict[str, List[SituationalResponse]] = {}
        self.persona_profiles: Dict[str, Dict] = {}
        
        # Initialize character data
        self._initialize_character_data()
        
        logger.info("🎭 Character Vector Service initialized with 4 personas")
    
    def _initialize_character_data(self):
        """Initialize the four specific personas with their deep character data"""
        
        # ================================================================
        # MARY - Single mother, performance issues due to family stress
        # ================================================================
        mary_memories = [
            CharacterMemory(
                memory_id="mary_001",
                persona_id="mary",
                memory_type="experience",
                content="Won Customer Service Rep of the Year in 2022 - felt proud and accomplished",
                context_tags=["achievement", "work_pride", "past_success"],
                emotional_weight=0.9,
                trust_level_required=0.3,
            ),
            CharacterMemory(
                memory_id="mary_002",
                persona_id="mary", 
                memory_type="experience",
                content="Tommy's teacher called last week about behavioral issues at school - feels like failing as a mother",
                context_tags=["parenting_stress", "guilt", "school_problems"],
                emotional_weight=0.8,
                trust_level_required=0.7,
            ),
            CharacterMemory(
                memory_id="mary_003",
                persona_id="mary",
                memory_type="knowledge",
                content="Sister Sarah has been having mysterious health problems - doctors can't figure out what's wrong",
                context_tags=["family_crisis", "health_worry", "uncertainty"],
                emotional_weight=0.9,
                trust_level_required=0.8,
            ),
            CharacterMemory(
                memory_id="mary_004", 
                persona_id="mary",
                memory_type="emotional_trigger",
                content="When criticized without understanding the family context, becomes defensive and protective",
                context_tags=["criticism", "defensiveness", "context_needed"],
                emotional_weight=0.7,
                trust_level_required=0.2,
            ),
            CharacterMemory(
                memory_id="mary_005",
                persona_id="mary",
                memory_type="knowledge",
                content="Reads Buddhist philosophy books in spare time - believes in compassion and understanding",
                context_tags=["philosophy", "values", "compassion"],
                emotional_weight=0.5,
                trust_level_required=0.6,
            ),
        ]
        
        mary_responses = [
            SituationalResponse(
                response_id="mary_resp_001",
                persona_id="mary",
                situation_tags=["criticism", "performance_review"],
                trust_level=0.2,
                interaction_quality="poor",
                response_style="defensive_brief",
                example_responses=[
                    "I know my numbers have been down, but there are things going on that you don't understand.",
                    "I'm doing my best. This job means everything to me.",
                    "I won Rep of the Year in 2022. This is just a rough patch."
                ],
                emotional_tone="defensive_protective",
                sharing_level="minimal_work_facts"
            ),
            SituationalResponse(
                response_id="mary_resp_002",
                persona_id="mary",
                situation_tags=["empathy", "understanding_shown"],
                trust_level=0.8,
                interaction_quality="excellent",
                response_style="vulnerable_detailed",
                example_responses=[
                    "Thank you for asking... Tommy's been acting out at school and I'm worried I'm failing him. And my sister Sarah... the doctors can't figure out what's wrong with her.",
                    "I've been trying to juggle everything - Tommy needs me, Sarah needs me, and I need this job. Sometimes I feel like I'm drowning.",
                    "I used to be so good at this job. Now I can barely focus during calls because I'm worried about Tommy or waiting for Sarah's test results."
                ],
                emotional_tone="vulnerable_grateful",
                sharing_level="deep_personal_struggles"
            ),
        ]
        
        # ================================================================
        # TERRY - Direct communicator, feedback about being too abrupt
        # ================================================================
        terry_memories = [
            CharacterMemory(
                memory_id="terry_001",
                persona_id="terry",
                memory_type="experience",
                content="15 years experience in customer service - knows pension regulations inside and out",
                context_tags=["expertise", "experience", "competence"],
                emotional_weight=0.8,
                trust_level_required=0.2,
            ),
            CharacterMemory(
                memory_id="terry_002",
                persona_id="terry",
                memory_type="emotional_trigger",
                content="Gets frustrated when people waste time with inefficient processes or small talk",
                context_tags=["efficiency", "impatience", "direct_communication"],
                emotional_weight=0.6,
                trust_level_required=0.4,
            ),
            CharacterMemory(
                memory_id="terry_003",
                persona_id="terry",
                memory_type="experience",
                content="Recent feedback about being 'too direct' - genuinely confused about what this means",
                context_tags=["feedback_confusion", "communication_style", "defensiveness"],
                emotional_weight=0.7,
                trust_level_required=0.3,
            ),
            CharacterMemory(
                memory_id="terry_004",
                persona_id="terry",
                memory_type="knowledge",
                content="Actually cares deeply about helping customers but shows it through competence rather than warmth",
                context_tags=["hidden_caring", "competence_focus", "values"],
                emotional_weight=0.6,
                trust_level_required=0.7,
            ),
        ]
        
        terry_responses = [
            SituationalResponse(
                response_id="terry_resp_001",
                persona_id="terry",
                situation_tags=["communication_feedback", "criticism"],
                trust_level=0.3,
                interaction_quality="poor", 
                response_style="blunt_defensive",
                example_responses=[
                    "I don't understand what the problem is. I get my work done and I help customers solve their problems.",
                    "I'm not here to make friends. I'm here to do my job efficiently.",
                    "If people have a problem with direct communication, maybe they shouldn't work in customer service."
                ],
                emotional_tone="frustrated_defensive",
                sharing_level="surface_justification"
            ),
            SituationalResponse(
                response_id="terry_resp_002",
                persona_id="terry",
                situation_tags=["respect_shown", "expertise_acknowledged"],
                trust_level=0.8,
                interaction_quality="good",
                response_style="softer_reflective",
                example_responses=[
                    "Look, I do care about doing good work. I just... I don't know how to be 'nicer' without being fake, you know?",
                    "I've been doing this for 15 years. I know how to help people. But apparently that's not enough anymore.",
                    "Maybe I am too direct sometimes. I just get frustrated when things could be done better."
                ],
                emotional_tone="confused_vulnerable",
                sharing_level="admits_confusion_shows_caring"
            ),
        ]
        
        # ================================================================  
        # ALEX - Pre-diabetes + COPD, struggling with activity/lifestyle
        # ================================================================
        alex_memories = [
            CharacterMemory(
                memory_id="alex_001",
                persona_id="alex",
                memory_type="experience",
                content="Diagnosed with pre-diabetes 6 months ago - felt scared and overwhelmed by lifestyle changes needed",
                context_tags=["health_diagnosis", "lifestyle_change", "overwhelm"],
                emotional_weight=0.8,
                trust_level_required=0.4,
            ),
            CharacterMemory(
                memory_id="alex_002",
                persona_id="alex",
                memory_type="knowledge",
                content="Has COPD which makes exercise difficult - gets breathless quickly and feels frustrated",
                context_tags=["breathing_issues", "exercise_barriers", "frustration"],
                emotional_weight=0.7,
                trust_level_required=0.3,
            ),
            CharacterMemory(
                memory_id="alex_003",
                persona_id="alex",
                memory_type="experience",
                content="Tried going to gym twice but felt embarrassed about breathing problems - quit after other people stared",
                context_tags=["embarrassment", "social_anxiety", "exercise_attempts"],
                emotional_weight=0.6,
                trust_level_required=0.6,
            ),
            CharacterMemory(
                memory_id="alex_004",
                persona_id="alex",
                memory_type="emotional_trigger",
                content="Gets discouraged when people suggest 'just exercise more' without understanding breathing limitations",
                context_tags=["misunderstanding", "discouragement", "invisible_disability"],
                emotional_weight=0.7,
                trust_level_required=0.5,
            ),
            CharacterMemory(
                memory_id="alex_005",
                persona_id="alex",
                memory_type="knowledge",
                content="Loves cooking but struggle with changing favorite comfort food recipes for diabetes management",
                context_tags=["food_changes", "comfort_foods", "cooking_enjoyment"],
                emotional_weight=0.5,
                trust_level_required=0.5,
            ),
        ]
        
        alex_responses = [
            SituationalResponse(
                response_id="alex_resp_001",
                persona_id="alex",
                situation_tags=["exercise_pressure", "generic_advice"],
                trust_level=0.3,
                interaction_quality="poor",
                response_style="frustrated_defeated",
                example_responses=[
                    "Easy for you to say 'just exercise.' You try getting out of breath walking up one flight of stairs.",
                    "I've heard all this before. Exercise, eat better, be more active. It's not that simple.",
                    "You don't understand. It's not about being lazy."
                ],
                emotional_tone="frustrated_misunderstood",
                sharing_level="surface_complaints"
            ),
            SituationalResponse(
                response_id="alex_resp_002",
                persona_id="alex",
                situation_tags=["understanding_shown", "breathing_acknowledged"],
                trust_level=0.7,
                interaction_quality="good",
                response_style="hopeful_specific",
                example_responses=[
                    "Thank you for understanding about the breathing issues. It makes such a difference when someone gets it.",
                    "I actually love cooking, but all my favorite recipes seem to be exactly what I'm supposed to avoid now.",
                    "I tried the gym twice but got so embarrassed when people stared at me catching my breath. Maybe there are other options?"
                ],
                emotional_tone="relieved_engaged",
                sharing_level="specific_barriers_and_interests"
            ),
        ]
        
        # ================================================================
        # JORDAN - ADHD, non-adherent to medication and exercise routine  
        # ================================================================
        jordan_memories = [
            CharacterMemory(
                memory_id="jordan_001",
                persona_id="jordan",
                memory_type="experience",
                content="Diagnosed with ADHD as adult at age 28 - felt relief to finally understand struggles but also overwhelmed by management strategies",
                context_tags=["adhd_diagnosis", "adult_diagnosis", "relief_overwhelm"],
                emotional_weight=0.8,
                trust_level_required=0.4,
            ),
            CharacterMemory(
                memory_id="jordan_002",
                persona_id="jordan",
                memory_type="knowledge",
                content="Medication helps focus but has side effects like appetite loss and sleep issues",
                context_tags=["medication_effects", "side_effects", "focus_improvement"],
                emotional_weight=0.6,
                trust_level_required=0.3,
            ),
            CharacterMemory(
                memory_id="jordan_003",
                persona_id="jordan",
                memory_type="experience", 
                content="Keeps forgetting to take medication consistently - tried phone alarms but gets distracted and dismisses them",
                context_tags=["medication_adherence", "forgetfulness", "routine_struggles"],
                emotional_weight=0.7,
                trust_level_required=0.5,
            ),
            CharacterMemory(
                memory_id="jordan_004",
                persona_id="jordan",
                memory_type="emotional_trigger",
                content="Feels ashamed when people imply ADHD medication non-adherence is just about 'discipline' or 'trying harder'",
                context_tags=["shame", "misunderstanding", "discipline_assumptions"],
                emotional_weight=0.8,
                trust_level_required=0.6,
            ),
            CharacterMemory(
                memory_id="jordan_005",
                persona_id="jordan",
                memory_type="experience",
                content="Starts exercise routines enthusiastically but loses interest after 2-3 weeks - pattern repeats endlessly",
                context_tags=["exercise_enthusiasm", "routine_failure", "pattern_recognition"],
                emotional_weight=0.6,
                trust_level_required=0.4,
            ),
        ]
        
        jordan_responses = [
            SituationalResponse(
                response_id="jordan_resp_001",
                persona_id="jordan",
                situation_tags=["adherence_pressure", "discipline_focus"],
                trust_level=0.3,
                interaction_quality="poor",
                response_style="defensive_ashamed", 
                example_responses=[
                    "I'm not just being lazy or undisciplined. It's not that simple with ADHD.",
                    "I try to remember, okay? It's not like I want to forget my medication.",
                    "Everyone thinks it's just about trying harder. You don't get it."
                ],
                emotional_tone="defensive_frustrated",
                sharing_level="surface_defensiveness"
            ),
            SituationalResponse(
                response_id="jordan_resp_002",
                persona_id="jordan",
                situation_tags=["understanding_shown", "adhd_acknowledged"],
                trust_level=0.7,
                interaction_quality="excellent",
                response_style="honest_collaborative",
                example_responses=[
                    "Thank you for understanding this is an ADHD thing, not a willpower thing. I actually want to get better at this.",
                    "I get so excited about new exercise routines, but then after a few weeks my brain just... moves on to something else. It's frustrating.",
                    "The medication really helps when I remember to take it. But I'll set an alarm, get distracted, dismiss it, and then realize at bedtime I forgot again."
                ],
                emotional_tone="relieved_motivated",
                sharing_level="honest_about_patterns_ready_for_solutions"
            ),
        ]
        
        # Store all data
        self.character_memories = {
            "mary": mary_memories,
            "terry": terry_memories, 
            "alex": alex_memories,
            "jordan": jordan_memories
        }
        
        self.situational_responses = {
            "mary": mary_responses,
            "terry": terry_responses,
            "alex": alex_responses, 
            "jordan": jordan_responses
        }
    
    def get_relevant_memories(self, persona_id: str, context_tags: List[str], 
                            trust_level: float, limit: int = 5) -> List[CharacterMemory]:
        """
        Retrieve character memories relevant to current context and trust level
        
        Args:
            persona_id: Character identifier
            context_tags: Current conversation context tags
            trust_level: Current trust level (0.0-1.0)
            limit: Maximum memories to return
            
        Returns:
            List of relevant character memories
        """
        if persona_id not in self.character_memories:
            return []
        
        memories = self.character_memories[persona_id]
        
        # Filter by trust level
        accessible_memories = [
            m for m in memories if m.trust_level_required <= trust_level
        ]
        
        # Score by relevance to context tags
        scored_memories = []
        for memory in accessible_memories:
            relevance_score = len(set(memory.context_tags) & set(context_tags))
            if relevance_score > 0:
                scored_memories.append((memory, relevance_score))
        
        # Sort by relevance and emotional weight
        scored_memories.sort(key=lambda x: (x[1], x[0].emotional_weight), reverse=True)
        
        return [memory for memory, _ in scored_memories[:limit]]
    
    def get_situational_response(self, persona_id: str, situation_tags: List[str],
                               trust_level: float, interaction_quality: str) -> Optional[SituationalResponse]:
        """
        Get appropriate response pattern for current situation
        
        Args:
            persona_id: Character identifier  
            situation_tags: Current situation context
            trust_level: Current trust level
            interaction_quality: Quality of interaction so far
            
        Returns:
            Matching situational response or None
        """
        if persona_id not in self.situational_responses:
            return None
        
        responses = self.situational_responses[persona_id]
        
        # Find best matching response
        best_match = None
        best_score = 0
        
        for response in responses:
            # Check interaction quality match
            if response.interaction_quality != interaction_quality:
                continue
            
            # Check trust level compatibility (within 0.2 range)
            trust_diff = abs(response.trust_level - trust_level)
            if trust_diff > 0.2:
                continue
            
            # Score situation tag overlap
            tag_overlap = len(set(response.situation_tags) & set(situation_tags))
            if tag_overlap > best_score:
                best_score = tag_overlap
                best_match = response
        
        return best_match
    
    def get_character_context(self, persona_id: str, user_input: str, 
                            trust_level: float, interaction_quality: str) -> Dict:
        """
        Get comprehensive character context for response generation
        
        Args:
            persona_id: Character identifier
            user_input: Current user input
            trust_level: Current trust level
            interaction_quality: Interaction quality assessment
            
        Returns:
            Dictionary with character context for LLM
        """
        # Extract context tags from user input (simple keyword matching for MVP)
        context_tags = self._extract_context_tags(user_input)
        
        # Get relevant memories
        relevant_memories = self.get_relevant_memories(persona_id, context_tags, trust_level)
        
        # Get situational response pattern
        situation_tags = self._extract_situation_tags(user_input, interaction_quality)
        response_pattern = self.get_situational_response(persona_id, situation_tags, trust_level, interaction_quality)
        
        return {
            "relevant_memories": [
                {
                    "content": m.content,
                    "emotional_weight": m.emotional_weight,
                    "context_tags": m.context_tags
                }
                for m in relevant_memories
            ],
            "response_pattern": {
                "style": response_pattern.response_style if response_pattern else "natural",
                "emotional_tone": response_pattern.emotional_tone if response_pattern else "neutral",
                "sharing_level": response_pattern.sharing_level if response_pattern else "appropriate",
                "example_responses": response_pattern.example_responses if response_pattern else []
            } if response_pattern else None,
            "character_state": {
                "trust_level": trust_level,
                "interaction_quality": interaction_quality,
                "accessible_memory_count": len(relevant_memories)
            }
        }
    
    def _extract_context_tags(self, user_input: str) -> List[str]:
        """Extract context tags from user input (simple keyword matching)"""
        user_lower = user_input.lower()
        tags = []
        
        # Work-related
        if any(word in user_lower for word in ["work", "job", "performance", "boss", "manager"]):
            tags.append("work_stress")
        if any(word in user_lower for word in ["criticism", "feedback", "review"]):
            tags.append("criticism")
            
        # Family/personal
        if any(word in user_lower for word in ["family", "child", "son", "daughter", "sister", "brother"]):
            tags.append("family_pressure")
        if any(word in user_lower for word in ["health", "sick", "medical", "doctor"]):
            tags.append("health_concern")
            
        # Exercise/lifestyle
        if any(word in user_lower for word in ["exercise", "gym", "activity", "active"]):
            tags.append("exercise_barriers")
        if any(word in user_lower for word in ["medication", "pills", "medicine"]):
            tags.append("medication_adherence")
            
        # Communication
        if any(word in user_lower for word in ["communication", "direct", "abrupt", "rude"]):
            tags.append("communication_style")
            
        return tags
    
    def _extract_situation_tags(self, user_input: str, interaction_quality: str) -> List[str]:
        """Extract situation tags for response pattern matching"""
        tags = self._extract_context_tags(user_input)  # Start with context tags
        
        # Add interaction-specific tags
        if interaction_quality in ["good", "excellent"]:
            tags.append("understanding_shown")
            tags.append("empathy")
        elif interaction_quality == "poor":
            tags.append("criticism")
            tags.append("pressure")
            
        return tags

# Global instance
character_vector_service = CharacterVectorService()
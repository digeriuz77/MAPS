"""
MI Practice Module Models
Pydantic schemas for Motivational Interviewing practice modules
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


# ============================================
# ENUMS
# ============================================

class ContentType(str, Enum):
    """Content type classification for MI modules"""
    SHARED = "shared"
    CUSTOMER_FACING = "customer_facing"
    COLLEAGUE_FACING = "colleague_facing"


class DifficultyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class CompletionStatus(str, Enum):
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    MAX_TURNS = "max_turns"
    IN_PROGRESS = "in_progress"


class MIFocusArea(str, Enum):
    BUILDING_RAPPORT = "Building Rapport"
    EXPLORING_RESISTANCE = "Exploring Resistance"
    ACTION_PLANNING = "Action Planning"
    ELICITING_CHANGE_TALK = "Eliciting Change Talk"
    AFFIRMING = "Affirming"
    REFLECTIVE_LISTENING = "Reflective Listening"


# ============================================
# DIALOGUE STRUCTURE MODELS
# ============================================

class ChoicePoint(BaseModel):
    """A single choice option at a dialogue node"""
    id: str = Field(..., description="Unique identifier for this choice point")
    option_text: str = Field(..., description="The text shown for this choice")
    preview_hint: Optional[str] = Field(None, description="Hint about the approach style")
    
    # Impact assessment
    rapport_impact: int = Field(0, description="Change to rapport score (-3 to +3)")
    resistance_impact: int = Field(0, description="Change to resistance level (-3 to +3)")
    tone_shift: float = Field(0.0, ge=-0.5, le=0.5, description="Shift in tone spectrum position")
    
    # Technique and competency mapping
    technique_tags: List[str] = Field(default_factory=list, description="MI techniques used")
    competency_links: List[str] = Field(default_factory=list, description="MAPS competencies demonstrated")
    
    # Feedback
    feedback: Dict[str, str] = Field(default_factory=dict, description="Immediate and learning feedback")
    
    # Branching
    next_node_id: str = Field(..., description="ID of the next node to navigate to")
    exploration_depth: str = Field("surface", description="surface, middle, or deep")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "cp_start_1",
            "option_text": "Thanks for coming in. I wanted to check in about how things are going.",
            "preview_hint": "Open, appreciative invitation",
            "rapport_impact": 1,
            "resistance_impact": -1,
            "tone_shift": 0.1,
            "technique_tags": ["open_question", "rapport_building"],
            "competency_links": ["A6", "B6"],
            "feedback": {
                "immediate": "Starting with appreciation helps establish safety.",
                "learning_note": "Open questions invite the person to share their perspective."
            },
            "next_node_id": "node_2_open",
            "exploration_depth": "surface"
        }
    })


class DialogueNode(BaseModel):
    """A node in the dialogue tree representing a persona response"""
    id: str = Field(..., description="Unique node identifier")
    persona_text: str = Field(..., description="The persona's response text")
    persona_mood: str = Field(..., description="Current mood/state descriptor")
    themes: List[str] = Field(default_factory=list, description="Themes present in this node")
    choice_points: List[ChoicePoint] = Field(default_factory=list, description="Available choices")
    is_endpoint: bool = Field(False, description="Whether this is an ending node")
    endpoint_type: Optional[str] = Field(None, description="Type of ending if applicable")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "id": "node_1",
            "persona_text": "I'm not sure why we're meeting. Is this about my performance?",
            "persona_mood": "defensive_guarded",
            "themes": ["Work Performance", "Trust"],
            "choice_points": [],
            "is_endpoint": False
        }
    })


class DialogueStructure(BaseModel):
    """Complete dialogue tree structure"""
    start_node_id: str = Field(..., description="ID of the starting node")
    nodes: Dict[str, DialogueNode] = Field(default_factory=dict, description="All nodes by ID")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "start_node_id": "node_1",
            "nodes": {
                "node_1": {
                    "id": "node_1",
                    "persona_text": "I'm not sure why we're meeting...",
                    "persona_mood": "defensive_guarded",
                    "themes": ["Trust"],
                    "choice_points": []
                }
            }
        }
    })


# ============================================
# PERSONA CONFIGURATION MODELS
# ============================================

class ToneSpectrumConfig(BaseModel):
    """Configuration for continuous tone interpolation (0.0 to 1.0)"""
    # Word choice complexity (0.0=simple, 1.0=sophisticated)
    word_complexity: float = Field(0.5, ge=0.0, le=1.0)
    
    # Sentence length (0.0=terse, 1.0=elaborate)
    sentence_length: float = Field(0.5, ge=0.0, le=1.0)
    
    # Emotional expressiveness (0.0=flat, 1.0=warm)
    emotional_expressiveness: float = Field(0.5, ge=0.0, le=1.0)
    
    # Disclosure level (0.0=minimal, 1.0=forthcoming)
    disclosure_level: float = Field(0.5, ge=0.0, le=1.0)
    
    # Response latency simulation (0.0=hesitant, 1.0=immediate)
    response_latency: float = Field(0.5, ge=0.0, le=1.0)
    
    # Hedging language (0.0=hedged "perhaps/maybe", 1.0=confident assertions)
    confidence_level: float = Field(0.5, ge=0.0, le=1.0)

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "word_complexity": 0.3,
            "sentence_length": 0.4,
            "emotional_expressiveness": 0.2,
            "disclosure_level": 0.1,
            "response_latency": 0.3,
            "confidence_level": 0.2
        }
    })


class PersonaConfig(BaseModel):
    """Persona configuration for MI practice module"""
    name: str = Field(..., description="Persona name")
    role: str = Field(..., description="Persona's role (e.g., 'team member', 'client')")
    background: str = Field(..., description="Background context for the persona")
    personality_traits: List[str] = Field(default_factory=list, description="Key personality traits")
    
    # Tone spectrum for continuous interpolation
    tone_spectrum: ToneSpectrumConfig = Field(default_factory=ToneSpectrumConfig)
    
    # Starting position on tone spectrum (0.0=guarded, 1.0=open)
    starting_tone_position: float = Field(0.2, ge=0.0, le=1.0)
    
    # Triggers and sensitivities
    triggers: List[str] = Field(default_factory=list, description="Topics/approaches that increase resistance")
    comfort_topics: List[str] = Field(default_factory=list, description="Topics that decrease resistance")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "name": "Jordan",
            "role": "team member",
            "background": "Recently disengaged employee with performance concerns",
            "personality_traits": ["defensive", "guarded", "values autonomy"],
            "tone_spectrum": {
                "word_complexity": 0.4,
                "sentence_length": 0.3,
                "emotional_expressiveness": 0.2,
                "disclosure_level": 0.1,
                "response_latency": 0.3,
                "confidence_level": 0.3
            },
            "starting_tone_position": 0.2,
            "triggers": ["direct criticism", "being told what to do"],
            "comfort_topics": ["autonomy", "growth opportunities"]
        }
    })


# ============================================
# RUBRIC AND SCORING MODELS
# ============================================

class CompetencyIndicator(BaseModel):
    """Indicator for assessing a MAPS competency"""
    description: str
    weight: float = Field(1.0, ge=0.0, le=2.0)
    positive_signals: List[str] = Field(default_factory=list)
    negative_signals: List[str] = Field(default_factory=list)


class MAPSRubric(BaseModel):
    """MAPS competency scoring rubric for a module"""
    dimensions: Dict[str, CompetencyIndicator] = Field(default_factory=dict)
    overall_scoring_logic: str = Field("average", description="How to calculate overall score")

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "dimensions": {
                "A6": {
                    "description": "Rapport Building",
                    "weight": 1.5,
                    "positive_signals": ["open_questions", "affirmations"],
                    "negative_signals": ["confrontation"]
                }
            },
            "overall_scoring_logic": "weighted_average"
        }
    })


# ============================================
# CHOICE AND ATTEMPT HISTORY MODELS
# ============================================

class ChoiceMade(BaseModel):
    """Record of a choice made during an attempt"""
    node_id: str
    choice_point_id: str
    chosen_at: datetime = Field(default_factory=datetime.utcnow)
    rapport_impact: int
    resistance_impact: int
    tone_shift: float
    techniques_used: List[str] = Field(default_factory=list)
    competencies_demonstrated: List[str] = Field(default_factory=list)


class FinalScores(BaseModel):
    """Final assessment scores for an attempt"""
    overall_score: float = Field(..., ge=0.0, le=10.0)
    competency_scores: Dict[str, float] = Field(default_factory=dict)
    technique_counts: Dict[str, int] = Field(default_factory=dict)
    resistance_triggered: int = Field(0)
    rapport_built: bool = Field(False)
    final_tone_position: float = Field(..., ge=0.0, le=1.0)


# ============================================
# MAIN ENTITY MODELS
# ============================================

class MIPracticeModule(BaseModel):
    """Complete MI Practice Module schema"""
    id: Optional[str] = None
    code: str = Field(..., description="Module code (e.g., shared-simple-reflections-001)")
    title: str = Field(..., min_length=5, max_length=200)

    # Categorization
    content_type: ContentType = Field(ContentType.SHARED, description="Content type: shared, customer_facing, or colleague_facing")
    mi_focus_area: Optional[str] = None
    difficulty_level: DifficultyLevel = DifficultyLevel.BEGINNER
    estimated_minutes: int = Field(5, ge=1, le=60)

    # Learning design
    learning_objective: str = Field(..., min_length=10)
    scenario_context: str = Field(..., min_length=10)

    # Configuration
    persona_config: PersonaConfig
    dialogue_structure: DialogueStructure

    # MAPS alignment
    target_competencies: List[str] = Field(default_factory=list)
    maps_rubric: MAPSRubric
    maps_framework_alignment: Optional[Dict[str, Any]] = None

    # Metadata
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "mi-explore-resistance-001",
            "title": "Exploring Resistance with Jordan",
            "mi_focus_area": "Exploring Resistance",
            "difficulty_level": "intermediate",
            "estimated_minutes": 8,
            "learning_objective": "Practice responding to defensive statements without triggering additional resistance",
            "scenario_context": "Jordan is a team member who has become disengaged recently...",
            "target_competencies": ["A6", "B6", "1.2.1"]
        }
    })


class MIPracticeModuleSummary(BaseModel):
    """Lightweight summary of a module for listing"""
    id: str
    code: str
    title: str
    content_type: ContentType
    mi_focus_area: Optional[str]
    difficulty_level: str
    estimated_minutes: int
    learning_objective: str
    target_competencies: List[str]

    # User-specific fields (populated at runtime)
    user_attempts: int = 0
    best_score: Optional[float] = None
    is_completed: bool = False
    last_attempted_at: Optional[datetime] = None


class MIPracticeAttempt(BaseModel):
    """MI Practice Attempt schema"""
    id: Optional[str] = None
    user_id: str
    module_id: str
    
    # Timing
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    
    # Progress tracking
    current_node_id: Optional[str] = None
    path_taken: List[str] = Field(default_factory=list)
    
    # State tracking (continuous spectrum)
    current_rapport_score: int = Field(0, ge=-10, le=10)
    current_resistance_level: int = Field(5, ge=1, le=10)
    tone_spectrum_position: float = Field(0.0, ge=0.0, le=1.0)
    
    # Attempt data
    choices_made: List[ChoiceMade] = Field(default_factory=list)
    
    # Final assessment
    completion_status: Optional[CompletionStatus] = None
    final_scores: Optional[FinalScores] = None
    insights_generated: List[Dict[str, Any]] = Field(default_factory=list)
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MILearningPath(BaseModel):
    """MI Learning Path schema"""
    id: Optional[str] = None
    code: str = Field(..., pattern=r'^path-[a-z0-9-]+$')
    title: str = Field(..., min_length=5, max_length=200)
    description: Optional[str] = None
    
    # Path structure
    module_sequence: List[str] = Field(..., description="Ordered list of module IDs")
    
    # Learning design
    target_audience: Optional[str] = None
    estimated_total_minutes: Optional[int] = None
    
    # MAPS alignment
    maps_competencies_targeted: List[str] = Field(default_factory=list)
    
    # Metadata
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class MILearningPathSummary(BaseModel):
    """Lightweight summary of a learning path"""
    id: str
    code: str
    title: str
    description: Optional[str]
    module_count: int
    estimated_total_minutes: Optional[int]
    target_audience: Optional[str]
    
    # User-specific fields
    is_enrolled: bool = False
    progress_percent: float = 0.0
    current_module_index: int = 0


class CompetencyScoreDetail(BaseModel):
    """Detailed competency score with trend"""
    current: float
    trend: str = Field(..., pattern=r'^(improving|stable|declining)$')
    attempts: int = 0


class TechniquePracticeDetail(BaseModel):
    """Technique practice statistics"""
    count: int = 0
    avg_quality: float = Field(0.0, ge=0.0, le=10.0)


class MIUserProgress(BaseModel):
    """Aggregated MI User Progress schema"""
    id: Optional[str] = None
    user_id: str
    
    # Overall progress
    modules_completed: int = 0
    modules_attempted: int = 0
    total_practice_minutes: int = 0
    
    # Competency tracking
    competency_scores: Dict[str, CompetencyScoreDetail] = Field(default_factory=dict)
    
    # Technique exposure
    techniques_practiced: Dict[str, TechniquePracticeDetail] = Field(default_factory=dict)
    
    # Current learning path
    active_learning_path_id: Optional[str] = None
    current_module_index: int = 0
    
    # Insights
    learning_insights: List[Dict[str, Any]] = Field(default_factory=list)
    
    updated_at: Optional[datetime] = None


# ============================================
# API REQUEST/RESPONSE MODELS
# ============================================

class StartAttemptRequest(BaseModel):
    """Request to start a new practice attempt"""
    module_id: str
    user_id: Optional[str] = None  # Optional - will use authenticated user if not provided


class StartAttemptResponse(BaseModel):
    """Response when starting a new attempt"""
    attempt_id: str
    module_id: str
    module_code: str
    module_title: str
    current_state: Dict[str, Any]  # Current dialogue state
    choice_points: List[Dict[str, str]]  # Available choices (id, option_text, preview_hint)
    learning_objective: str


class MakeChoiceRequest(BaseModel):
    """Request to make a choice in an attempt"""
    choice_point_id: str


class MakeChoiceResponse(BaseModel):
    """Response after making a choice"""
    attempt_id: str
    turn_number: int
    choice_made: Dict[str, Any]
    feedback: Dict[str, Any]
    new_state: Dict[str, Any]
    next_choice_points: List[Dict[str, str]]
    is_complete: bool


class AttemptReviewResponse(BaseModel):
    """Response for reviewing a completed attempt"""
    attempt_id: str
    module: Dict[str, str]  # id, code, title
    completed_at: datetime
    completion_status: str
    turns_taken: int
    final_scores: FinalScores
    path_review: List[Dict[str, Any]]
    key_moments: List[Dict[str, Any]]
    learning_notes: List[str]


class UserProgressResponse(BaseModel):
    """Response for user progress endpoint"""
    modules_completed: int
    modules_attempted: int
    total_practice_minutes: int
    overall_progress_percent: float
    competency_scores: Dict[str, CompetencyScoreDetail]
    techniques_practiced: Dict[str, TechniquePracticeDetail]
    recent_attempts: List[Dict[str, Any]]
    learning_insights: List[Dict[str, Any]]


class EnrollPathRequest(BaseModel):
    """Request to enroll in a learning path"""
    path_id: str  # Required in request body for backward compatibility
    user_id: str  # Required - but backend will normalize "anonymous" to actual UUID


class EnrollPathResponse(BaseModel):
    """Response after enrolling in a path"""
    success: bool
    path_id: str
    path_title: str
    current_module_id: str
    message: str

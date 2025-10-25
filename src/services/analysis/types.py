"""
Types and models for MITI transcript analysis
"""
from typing import List, Dict, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum

# Speaker Role
class SpeakerRole(str, Enum):
    PRACTITIONER = "Practitioner"
    CLIENT = "Client"

# MITI Codes
class MitiCode(str, Enum):
    # Practitioner Volley
    Q = "Q"  # Question
    SR = "SR"  # Simple Reflection
    CR = "CR"  # Complex Reflection
    
    # MI-Adherent
    AF = "AF"  # Affirmation
    SEEK = "Seek"  # Seeking Collaboration
    EA = "EA"  # Emphasizing Autonomy
    
    # MI-Non-Adherent
    PER = "Per"  # Persuasion
    C = "C"  # Confrontation
    
    # Other Practitioner Codes
    GI = "GI"  # Giving Information
    O = "O"  # Other
    
    # Client Talk
    CHANGE_TALK = "ChangeTalk"
    SUSTAIN_TALK = "SustainTalk"
    NEUTRAL = "Neutral"

# Progress stages
class ProgressStage(str, Enum):
    IDLE = "idle"
    PARSING = "parsing"
    CACHING_CHECK = "caching_check"
    CODING = "coding"
    AGGREGATING = "aggregating"
    SUPERVISING = "supervising"
    COMPLETE = "complete"
    ERROR = "error"

# Models
class ParsedTurn(BaseModel):
    speaker: SpeakerRole
    text: str
    original_index: int  # 0-based index from original transcript

class AnnotatedTurn(BaseModel):
    turn_index: int  # original_index from ParsedTurn
    speaker: SpeakerRole
    text: str
    codes: List[MitiCode]
    confidence: Optional[float] = None

class ConversationContext(BaseModel):
    practitioner_role: str = Field(default="Therapist/Coach", description="Semantic role of practitioner")
    client_role: str = Field(default="Patient/Client", description="Semantic role of client")
    scenario_description: str = Field(default="A motivational interviewing session", description="Description of scenario")

class SpeakerIdentifierHints(BaseModel):
    practitioner_identifier_hint: Optional[str] = None
    client_identifier_hint: Optional[str] = None

class ParseTranscriptOutput(BaseModel):
    parsed_turns: List[ParsedTurn]
    actual_practitioner_identifier: Optional[str] = None  # Raw speaker string mapped to Practitioner
    actual_client_identifier: Optional[str] = None  # Raw speaker string mapped to Client
    all_unique_speaker_strings: List[str]  # All unique raw speaker strings found

class AggregatedStats(BaseModel):
    total_turns: int
    practitioner_turns: int
    client_turns: int
    reflection_to_question_ratio: str  # e.g., "2:1" or "N/A"
    percentage_complex_reflections: str  # e.g., "50%" or "N/A"
    code_counts: Dict[str, int]  # MitiCode to count mapping
    mia_to_mina_ratio: str  # MI-Adherent to MI-Non-Adherent ratio

class GlobalRatingItem(BaseModel):
    score: int = Field(ge=1, le=5, description="Rating score from 1 to 5")
    rationale: str

class KeyMoment(BaseModel):
    turn_quote: str
    explanation: str

class PractitionerPatterns(BaseModel):
    strengths: str
    challenge_areas: str

class ActionableRecommendations(BaseModel):
    immediate_focus: str
    skill_development: str

class GlobalRatings(BaseModel):
    partnership: GlobalRatingItem
    empathy: GlobalRatingItem
    cultivating_change_talk: GlobalRatingItem
    softening_sustain_talk: GlobalRatingItem

class SupervisoryReportData(BaseModel):
    global_ratings: GlobalRatings
    key_moments: List[KeyMoment]
    client_language_themes: str
    practitioner_patterns: PractitionerPatterns
    actionable_recommendations: ActionableRecommendations

class CompleteAnalysisResult(BaseModel):
    annotated_turns: List[AnnotatedTurn]
    statistics: AggregatedStats
    report: SupervisoryReportData
    context_used: ConversationContext
    speaker_identifiers_used: SpeakerIdentifierHints

class ProgressState(BaseModel):
    stage: ProgressStage
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    current_item: str = Field(description="Description of current task")
    message: Optional[str] = Field(default=None, description="For errors or additional info")

# Request/Response models for API
class AnalysisRequest(BaseModel):
    transcript: str
    context: Optional[ConversationContext] = None
    speaker_hints: Optional[SpeakerIdentifierHints] = None

class AudioAnalysisRequest(BaseModel):
    context: Optional[ConversationContext] = None
    speaker_hints: Optional[SpeakerIdentifierHints] = None

# Constants
PRACTITIONER_CODES = [
    MitiCode.Q, MitiCode.SR, MitiCode.CR, 
    MitiCode.AF, MitiCode.SEEK, MitiCode.EA, 
    MitiCode.PER, MitiCode.C, 
    MitiCode.GI, MitiCode.O
]

CLIENT_CODES = [
    MitiCode.CHANGE_TALK, 
    MitiCode.SUSTAIN_TALK, 
    MitiCode.NEUTRAL
]

ALL_MITI_CODES = PRACTITIONER_CODES + CLIENT_CODES

MI_ADHERENT_CODES = [
    MitiCode.AF, MitiCode.SEEK, MitiCode.EA, 
    MitiCode.SR, MitiCode.CR
]

MI_NON_ADHERENT_CODES = [
    MitiCode.PER, MitiCode.C
]

KNOWN_SYSTEM_SPEAKERS = [
    "System Notification", 
    "System Message",
    "System", 
    "Notification", 
    "Info", 
    "Meta",
    "Chatbot Message",
    "AI Assistant"
]

# Batch processing constants
DEFAULT_BATCH_SIZE = 12
DEFAULT_PRACTITIONER_ROLE = "Therapist/Coach"
DEFAULT_CLIENT_ROLE = "Patient/Client"
DEFAULT_SCENARIO_DESCRIPTION = "A motivational interviewing session"

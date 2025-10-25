"""
Data models and schemas for the AI Persona System
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from enum import Enum

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class PersonaType(str, Enum):
    """Legacy persona types - Now using database-driven personas"""
    # Note: Production system loads personas dynamically from Supabase
    # These are kept for backward compatibility
    MARY = "mary"  # Primary production persona

class Message(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None

class SafetyResult(BaseModel):
    is_safe: bool
    confidence: float
    reason: Optional[str] = None
    flags: List[str] = Field(default_factory=list)

class PersonaResponse(BaseModel):
    content: str
    confidence: float
    traits_activated: List[str]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    safety_flags: Optional[List[str]] = None
    analysis: Optional[Dict[str, Any]] = None

class PersonaConfig(BaseModel):
    persona_type: PersonaType
    name: str
    description: str
    difficulty_level: Optional[int] = Field(default=5, ge=1, le=10)
    custom_traits: Optional[List[str]] = None
    max_tokens: Optional[int] = Field(default=500, ge=1, le=4000)
    context_settings: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    persona_id: str
    message: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    response: PersonaResponse
    persona_id: str
    session_id: str
    conversation_id: Optional[str] = None

class PersonaCreate(BaseModel):
    persona_type: PersonaType
    name: str
    description: str
    difficulty_level: Optional[int] = Field(default=5, ge=1, le=10)
    custom_traits: Optional[List[str]] = None
    max_tokens: Optional[int] = Field(default=500, ge=1, le=4000)

class PersonaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=10)
    custom_traits: Optional[List[str]] = None
    max_tokens: Optional[int] = Field(default=None, ge=1, le=4000)

class PersonaInfo(BaseModel):
    id: str
    persona_type: PersonaType
    name: str
    description: str
    difficulty_level: int
    custom_traits: List[str]
    max_tokens: int
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

class EvaluationRequest(BaseModel):
    persona_id: str
    conversation_id: str
    evaluation_type: Optional[str] = "general"

class EvaluationResponse(BaseModel):
    overall_score: float
    detailed_analysis: Dict[str, Any]
    recommendations: List[str]
    strengths: List[str]
    areas_for_improvement: List[str]

# New schemas for MI Quality Tracking System

class MITechniqueType(str, Enum):
    OPEN_QUESTION = "open_question"
    REFLECTION = "reflection"
    AFFIRMATION = "affirmation"
    SUMMARY = "summary"
    CONFRONTATION = "confrontation"
    ADVICE_WITHOUT_PERMISSION = "advice_without_permission"
    UNKNOWN = "unknown"

class DepthLevel(str, Enum):
    SURFACE = "surface"
    MIDDLE = "middle"
    DEEP = "deep"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class ConversationCreate(BaseModel):
    persona_id: str
    persona_seed: Optional[str] = None
    session_id: str
    user_id: Optional[str] = None

class MIAnalysisRequest(BaseModel):
    message: str
    recent_history: List[Dict[str, str]] = Field(default_factory=list)
    conversation_id: Optional[str] = None

class MIAnalysisResponse(BaseModel):
    technique: MITechniqueType
    quality_score: float = Field(ge=0, le=10)
    empathy_score: float = Field(ge=0, le=10)
    neutrality: bool
    triggers_resistance: bool
    specific_issues: List[str] = Field(default_factory=list)
    analysis_details: Optional[Dict[str, Any]] = None

# Quality patterns removed - not needed as per user requirements
# class QualityPatterns(BaseModel):
#     conversation_id: str
#     sustained_empathy: float
#     recent_resistance: int
#     depth_achieved: DepthLevel
#     last_quality_scores: List[float]
#     avg_quality_score: float
#     avg_empathy_score: float
#     total_turns: int

class ResponseInstruction(BaseModel):
    instruction: str
    depth: DepthLevel
    emotional_tone: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class PersonaResponseRequest(BaseModel):
    conversation_id: str
    instruction: str
    conversation_memory: List[str] = Field(default_factory=list)
    persona_seed: str

class MIConversationResponse(BaseModel):
    user_message: str
    persona_response: str
    mi_analysis: MIAnalysisResponse
    # quality_patterns: QualityPatterns  # Removed - not needed
    adaptations_applied: List[str] = Field(default_factory=list)

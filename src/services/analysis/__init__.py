"""
MAPS Person-Centred Analysis Service
V3 System - MITI framework removed, MAPS framework active
"""
from .maps_analysis_service import (
    MAPSAnalysisService,
    get_maps_analysis_service,
    create_standalone_maps_service,
    MAPSAnalysisResult,
    ConditionsForChange,
    PersonCentredConditions,
    PatternsObserved,
    StrengthsAndSuggestions
)
from .types import (
    ConversationContext,
    SpeakerIdentifierHints,
    CompleteAnalysisResult,
    ProgressState,
    ProgressStage,
    AnalysisRequest,
    AudioAnalysisRequest,
    AggregatedStats,
    SupervisoryReportData,
    ALL_MITI_CODES,
    DEFAULT_BATCH_SIZE,
    DEFAULT_PRACTITIONER_ROLE,
    DEFAULT_CLIENT_ROLE,
    DEFAULT_SCENARIO_DESCRIPTION
)

__all__ = [
    # MAPS Services (V3 Active)
    "MAPSAnalysisService",
    "get_maps_analysis_service",
    "create_standalone_maps_service",
    "MAPSAnalysisResult",
    "ConditionsForChange",
    "PersonCentredConditions",
    "PatternsObserved",
    "StrengthsAndSuggestions",
    # Type definitions (kept for compatibility)
    "ConversationContext",
    "SpeakerIdentifierHints",
    "CompleteAnalysisResult",
    "ProgressState",
    "ProgressStage",
    "AnalysisRequest",
    "AudioAnalysisRequest",
    "AggregatedStats",
    "SupervisoryReportData",
    "ALL_MITI_CODES",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_PRACTITIONER_ROLE",
    "DEFAULT_CLIENT_ROLE",
    "DEFAULT_SCENARIO_DESCRIPTION"
]

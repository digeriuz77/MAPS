"""
MITI Transcript Analysis Service with Enhanced Capabilities
"""
from .analysis_service import AnalysisService, get_analysis_service
from .cache_service import get_analysis_cache
from .json_parser import clean_and_validate_json_response
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
from .aggregator import get_summary_statistics, calculate_mi_proficiency_score

# Database-enhanced services removed - MAPS uses standard Gemini service directly
DATABASE_INTEGRATION_AVAILABLE = False

__all__ = [
    "AnalysisService",
    "get_analysis_service",
    "get_analysis_cache",
    "clean_and_validate_json_response",
    "ConversationContext",
    "SpeakerIdentifierHints",
    "CompleteAnalysisResult",
    "ProgressState",
    "ProgressStage",
    "AnalysisRequest",
    "AudioAnalysisRequest",
    "AggregatedStats",
    "SupervisoryReportData",
    "get_summary_statistics",
    "calculate_mi_proficiency_score",
    "ALL_MITI_CODES",
    "DEFAULT_BATCH_SIZE",
    "DEFAULT_PRACTITIONER_ROLE",
    "DEFAULT_CLIENT_ROLE",
    "DEFAULT_SCENARIO_DESCRIPTION"
]

# Database-enhanced services removed (MAPS uses Gemini directly)
# No additional exports needed
"""
DEPRECATED: MAPS Analysis Routes

This file is deprecated. All MAPS analysis functionality has been
consolidated into src/api/routes/analysis.py.

Please use:
- POST /api/analysis/transcript (was POST /api/v1/maps/analyze/transcript)
- POST /api/analysis/conversation (was POST /api/v1/maps/analyze/conversation)
- GET /api/analysis/status/{job_id} (was GET /api/v1/maps/status/{job_id})
- GET /api/analysis/result/{job_id} (was GET /api/v1/maps/result/{job_id})

This file will be removed in a future update.
"""

import logging
from fastapi import APIRouter, HTTPException, Response
from typing import Dict, Any

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/maps", tags=["maps_analysisdeprecated"])


@router.get("/deprecated")
async def maps_deprecated():
    """Redirect notice for deprecated maps_analysis routes"""
    return {
        "message": "This endpoint is deprecated. Please use /api/analysis/* instead.",
        "transcript_endpoint": "POST /api/analysis/transcript",
        "conversation_endpoint": "POST /api/analysis/conversation",
        "status_endpoint": "GET /api/analysis/status/{job_id}",
        "result_endpoint": "GET /api/analysis/result/{job_id}"
    }


# Mark all endpoints as deprecated redirects

@router.post("/analyze/transcript")
async def deprecated_analyze_transcript(request):
    """DEPRECATED: Use POST /api/analysis/transcript"""
    logger.warning("Using deprecated /api/v1/maps/analyze/transcript - use /api/analysis/transcript")
    from src.api.routes.analysis import analyze_transcript
    return await analyze_transcript(request)


@router.post("/analyze/conversation")
async def deprecated_analyze_conversation(request):
    """DEPRECATED: Use POST /api/analysis/conversation"""
    logger.warning("Using deprecated /api/v1/maps/analyze/conversation - use /api/analysis/conversation")
    from src.api.routes.analysis import analyze_conversation
    return await analyze_conversation(request)


@router.get("/status/{job_id}")
async def deprecated_get_status(job_id: str):
    """DEPRECATED: Use GET /api/analysis/status/{job_id}"""
    logger.warning(f"Using deprecated /api/v1/maps/status/{job_id} - use /api/analysis/status/{job_id}")
    from src.api.routes.analysis import get_analysis_status
    return await get_analysis_status(job_id)


@router.get("/result/{job_id}")
async def deprecated_get_result(job_id: str):
    """DEPRECATED: Use GET /api/analysis/result/{job_id}"""
    logger.warning(f"Using deprecated /api/v1/maps/result/{job_id} - use /api/analysis/result/{job_id}")
    from src.api.routes.analysis import get_analysis_result
    return await get_analysis_result(job_id)


@router.delete("/cache")
async def deprecated_clear_cache():
    """DEPRECATED: Use DELETE /api/analysis/cache"""
    logger.warning("Using deprecated /api/v1/maps/cache - use /api/analysis/cache")
    from src.api.routes.analysis import clear_analysis_cache
    return await clear_analysis_cache()

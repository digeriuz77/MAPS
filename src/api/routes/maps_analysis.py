"""
Direct MAPS analysis routes - bypassing the general analysis.py
Uses the updated MAPS service with OpenAI fallback
"""
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.dependencies import get_supabase_client
from src.services.analysis.maps_analysis_service import get_maps_analysis_service, create_standalone_maps_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/maps", tags=["maps_analysis"])

# In-memory job storage for this service (production: use Redis)
maps_jobs: Dict[str, Dict[str, Any]] = {}


def _to_maps_frontend_dict(result: Any) -> Dict[str, Any]:
    """Normalize MAPS analysis result (Pydantic or dict) to the frontend shape.
    Omits any overall x/10 score by design.
    """
    # Extract raw data from Pydantic if needed
    if hasattr(result, "model_dump"):
        data = result.model_dump()
    elif hasattr(result, "dict"):
        data = result.dict()
    else:
        data = result if isinstance(result, dict) else {}

    core = data.get("core_coaching_effectiveness", {}) or {}
    strengths = data.get("strengths_and_suggestions", {}) or {}
    patterns = data.get("patterns_observed", {}) or {}

    def get_theme(d: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "score": d.get("score"),
            "evidence": d.get("evidence", []),
            "notes": d.get("notes", "")
        }

    frontend = {
        # No overall_quality_score
        "maps_values_summary": data.get("maps_values_summary", ""),
        "report": {
            "core_coaching_effectiveness": {
                "foundational_trust_safety": get_theme(core.get("foundational_trust_safety", {})),
                "empathic_partnership_autonomy": get_theme(core.get("empathic_partnership_autonomy", {})),
                "empowerment_clarity": get_theme(core.get("empowerment_clarity", {})),
            },
            "strengths_and_suggestions": {
                "strengths": [
                    (s.model_dump() if hasattr(s, "model_dump") else (s.dict() if hasattr(s, "dict") else s))
                    for s in strengths.get("strengths", [])
                ],
                "opportunities": [
                    (o.model_dump() if hasattr(o, "model_dump") else (o.dict() if hasattr(o, "dict") else o))
                    for o in strengths.get("opportunities", [])
                ],
                "next_session_focus": strengths.get("next_session_focus", []),
                "maps_alignment": strengths.get("maps_alignment", "")
            },
            "patterns_observed": {
                "manager_patterns": patterns.get("manager_patterns", []),
                "employee_patterns": patterns.get("employee_patterns", []),
                "interaction_dynamics": patterns.get("interaction_dynamics", ""),
                "conversation_balance": patterns.get("conversation_balance", {}),
            }
        }
    }

    return frontend


class TranscriptAnalysisRequest(BaseModel):
    transcript: str
    context: Optional[Dict[str, Any]] = None
    manager_name: str = "Manager"
    persona_name: str = "Employee"


class ConversationAnalysisRequest(BaseModel):
    conversation_id: str
    context: Optional[Dict[str, Any]] = None


@router.post("/analyze/transcript")
async def analyze_transcript(request: TranscriptAnalysisRequest):
    """
    Analyze a raw transcript using MAPS framework
    Uses standalone service (no Supabase dependency)
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS transcript analysis: job_id={job_id}, length={len(request.transcript)}")
        
        # Store job with initial status
        maps_jobs[job_id] = {
            "status": "processing",
            "progress": 10,
            "stage": "analyzing",
            "current_item": "Running MAPS analysis...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "analysis_type": "transcript"
        }
        
        try:
            # Create standalone service (no Supabase needed)
            service = create_standalone_maps_service()
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 30,
                "current_item": "Analyzing behavioral patterns..."
            })
            
            # Run analysis
            result = await service.analyze_transcript(
                transcript=request.transcript,
                context=request.context,
                manager_name=request.manager_name,
                persona_name=request.persona_name
            )
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating report..."
            })
            
            # Convert result to frontend-compatible dict using the canonical normalizer
            result_dict = _to_maps_frontend_dict(result)
            
            # Complete job
            maps_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": result_dict,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS transcript analysis completed: job_id={job_id}")
            
        except Exception as e:
            logger.error(f"MAPS analysis failed for job {job_id}: {e}", exc_info=True)
            maps_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted", "analysis_type": "maps_transcript"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS transcript analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.post("/analyze/conversation")
async def analyze_conversation(
    request: ConversationAnalysisRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Analyze a conversation from Supabase by conversation_id using MAPS framework
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS conversation analysis: job_id={job_id}, conversation_id={request.conversation_id}")
        
        # Store job with initial status
        maps_jobs[job_id] = {
            "status": "processing",
            "progress": 10,
            "stage": "fetching",
            "current_item": "Fetching conversation from database...",
            "created_at": datetime.utcnow().isoformat(),
            "result": None,
            "error": None,
            "analysis_type": "conversation",
            "conversation_id": request.conversation_id
        }
        
        try:
            # Get MAPS service with Supabase
            service = get_maps_analysis_service(supabase_client=supabase)
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 30,
                "current_item": "Analyzing conversation with MAPS framework..."
            })
            
            # Run analysis
            result = await service.analyze_conversation_by_id(
                conversation_id=request.conversation_id,
                context=request.context
            )
            
            # Update progress
            maps_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating detailed report..."
            })
            
            # Convert result to frontend-compatible dict using the canonical normalizer
            result_dict = _to_maps_frontend_dict(result)
            
            # Complete job
            maps_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": result_dict,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS conversation analysis completed: job_id={job_id}")
            
        except Exception as e:
            logger.error(f"MAPS conversation analysis failed for job {job_id}: {e}", exc_info=True)
            maps_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted", "analysis_type": "maps_conversation"}
        
    except Exception as e:
        logger.error(f"Failed to submit MAPS conversation analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.get("/status/{job_id}")
async def get_maps_job_status(job_id: str):
    """Get MAPS analysis job status"""
    if job_id not in maps_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = maps_jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "current_item": job.get("current_item", ""),
        "created_at": job["created_at"],
        "analysis_type": job.get("analysis_type", "maps"),
        "error": job.get("error")
    }
    
    # Include result when complete
    if job["status"] == "complete" and job.get("result"):
        response["result"] = job["result"]
    
    return response


@router.get("/result/{job_id}")
async def get_maps_result(job_id: str):
    """Get completed MAPS analysis results"""
    if job_id not in maps_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = maps_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "analysis_type": job.get("analysis_type", "maps"),
        "result": job["result"],
        "completed_at": job.get("completed_at", job["created_at"])
    }


@router.delete("/cache")
async def clear_maps_cache():
    """Clear MAPS analysis cache"""
    try:
        global maps_jobs
        cleared_count = len(maps_jobs)
        maps_jobs.clear()
        
        return {
            "status": "success",
            "message": f"MAPS cache cleared successfully. Removed {cleared_count} cached analyses.",
            "cleared_jobs": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear MAPS cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")
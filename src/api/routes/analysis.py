"""
Analysis API Routes - Consolidated MAPS Analysis

Consolidated from analysis.py and maps_analysis.py into a single, clean API.
Uses the MAPS framework for person-centred transcript analysis.
"""

import logging
import json
import uuid
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from src.dependencies import get_supabase_client
from src.services.analysis.maps_analysis_service import (
    get_maps_analysis_service, 
    create_standalone_maps_service
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analysis", tags=["analysis"])

# In-memory job storage (production: use Redis or database)
analysis_jobs: Dict[str, Dict[str, Any]] = {}


# ========== Request Models ==========

class TranscriptAnalysisRequest(BaseModel):
    """Submit raw transcript text for MAPS analysis"""
    transcript: str
    context: Optional[Dict[str, Any]] = None
    manager_name: str = "Manager"
    persona_name: str = "Person"


class ConversationAnalysisRequest(BaseModel):
    """Analyze existing conversation from database"""
    conversation_id: str
    context: Optional[Dict[str, Any]] = None


class ScenarioAnalysisRequest(BaseModel):
    """Analyze scenario attempt transcript"""
    attempt_id: str


# ========== Helper Functions ==========

def _to_frontend_dict(result: Any) -> Dict[str, Any]:
    """Normalize MAPS analysis result to frontend format"""
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
    
    return {
        "maps_values_summary": data.get("maps_values_summary", ""),
        "report": {
            "core_coaching_effectiveness": {
                "foundational_trust_safety": get_theme(core.get("foundational_trust_safety", {})),
                "empathic_partnership_autonomy": get_theme(core.get("empathic_partnership_autonomy", {})),
                "empowerment_clarity": get_theme(core.get("empowerment_clarity", {})),
            },
            "strengths_and_suggestions": {
                "strengths": [
                    (s.model_dump() if hasattr(s, "model_dump") else s)
                    for s in strengths.get("strengths", [])
                ],
                "opportunities": [
                    (o.model_dump() if hasattr(o, "model_dump") else o)
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


# ========== Route Implementations ==========

@router.post("/transcript")
async def analyze_transcript(request: TranscriptAnalysisRequest):
    """
    Analyze raw transcript text using MAPS framework.
    
    Uses standalone service (no database dependency).
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS transcript analysis: job_id={job_id}")
        
        # Store job with initial status
        analysis_jobs[job_id] = {
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
            # Create standalone service
            service = create_standalone_maps_service()
            
            # Update progress
            analysis_jobs[job_id].update({
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
            analysis_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating report..."
            })
            
            # Convert result to frontend format
            result_dict = _to_frontend_dict(result)
            
            # Complete job
            analysis_jobs[job_id].update({
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
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"Failed to submit analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.post("/conversation")
async def analyze_conversation(
    request: ConversationAnalysisRequest,
    supabase=Depends(get_supabase_client)
):
    """
    Analyze existing conversation from database using MAPS framework.
    """
    try:
        job_id = str(uuid.uuid4())
        
        logger.info(f"Starting MAPS conversation analysis: job_id={job_id}, conversation_id={request.conversation_id}")
        
        analysis_jobs[job_id] = {
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
            service = get_maps_analysis_service(supabase_client=supabase)
            
            analysis_jobs[job_id].update({
                "progress": 30,
                "current_item": "Analyzing conversation with MAPS framework..."
            })
            
            result = await service.analyze_conversation_by_id(
                conversation_id=request.conversation_id,
                context=request.context
            )
            
            analysis_jobs[job_id].update({
                "progress": 80,
                "current_item": "Generating detailed report..."
            })
            
            result_dict = _to_frontend_dict(result)
            
            analysis_jobs[job_id].update({
                "status": "complete",
                "progress": 100,
                "stage": "complete",
                "current_item": "Analysis complete!",
                "result": result_dict,
                "completed_at": datetime.utcnow().isoformat()
            })
            
            logger.info(f"MAPS conversation analysis completed: job_id={job_id}")
            
        except Exception as e:
            logger.error(f"Conversation analysis failed for job {job_id}: {e}", exc_info=True)
            analysis_jobs[job_id].update({
                "status": "error",
                "error": str(e),
                "stage": "error",
                "current_item": f"Error: {str(e)}"
            })
        
        return {"job_id": job_id, "status": "submitted"}
        
    except Exception as e:
        logger.error(f"Failed to submit conversation analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to submit analysis: {str(e)}")


@router.get("/status/{job_id}")
async def get_analysis_status(job_id: str):
    """Get analysis job status"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    response = {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "stage": job["stage"],
        "current_item": job.get("current_item", ""),
        "created_at": job["created_at"],
        "analysis_type": job.get("analysis_type", "analysis"),
        "error": job.get("error")
    }
    
    if job["status"] == "complete" and job.get("result"):
        response["result"] = job["result"]
    
    return response


@router.get("/result/{job_id}")
async def get_analysis_result(job_id: str):
    """Get completed analysis results"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    return {
        "job_id": job_id,
        "status": job["status"],
        "analysis_type": job.get("analysis_type", "analysis"),
        "result": job["result"],
        "completed_at": job.get("completed_at", job["created_at"])
    }


@router.get("/result/{job_id}/export")
async def export_analysis_result(
    job_id: str, 
    format: str = Query("json", description="Export format: json, html, txt")
):
    """Export analysis results in various formats"""
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = analysis_jobs[job_id]
    
    if job["status"] != "complete":
        raise HTTPException(status_code=400, detail=f"Job not complete. Status: {job['status']}")
    
    result = job["result"]
    if not result:
        raise HTTPException(status_code=404, detail="No results available")
    
    try:
        if format == "json":
            content = json.dumps(result, indent=2)
            media_type = "application/json"
            filename = f"maps_analysis_{job_id}.json"
            
        elif format == "html":
            content = _generate_html_report(result, job_id)
            media_type = "text/html"
            filename = f"maps_analysis_{job_id}.html"
            
        elif format == "txt":
            content = _generate_text_report(result, job_id)
            media_type = "text/plain"
            filename = f"maps_analysis_{job_id}.txt"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")
        
        from fastapi.responses import Response
        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        logger.error(f"Failed to export analysis: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analysis")


@router.delete("/cache")
async def clear_analysis_cache():
    """Clear analysis cache"""
    try:
        global analysis_jobs
        cleared_count = len(analysis_jobs)
        analysis_jobs.clear()
        
        return {
            "status": "success",
            "message": f"Cache cleared. Removed {cleared_count} analyses.",
            "cleared_jobs": cleared_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")


# ========== Report Generation ==========

def _generate_html_report(result: Dict[str, Any], job_id: str) -> str:
    """Generate HTML report from analysis result"""
    maps_summary = result.get("maps_values_summary", "")
    report = result.get("report", {})
    core = report.get("core_coaching_effectiveness", {})
    strengths = report.get("strengths_and_suggestions", {})
    patterns = report.get("patterns_observed", {})
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>MAPS Analysis Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        h1 {{ color: #2c3e50; }}
        h2 {{ color: #34495e; margin-top: 30px; }}
        .score {{ font-weight: bold; color: #27ae60; }}
        .evidence {{ background: #f8f9fa; padding: 10px; margin: 5px 0; border-left: 3px solid #3498db; }}
        .strength {{ color: #27ae60; }}
        .opportunity {{ color: #e67e22; }}
    </style>
</head>
<body>
    <h1>MAPS Analysis Report</h1>
    <p><strong>Summary:</strong> {maps_summary}</p>
    
    <h2>Core Coaching Effectiveness</h2>
    <h3>Foundational Trust & Safety</h3>
    <p class="score">Score: {core.get('foundational_trust_safety', {}).get('score', 'N/A')}</p>
    <div class="evidence">{' '.join(core.get('foundational_trust_safety', {}).get('evidence', []))}</div>
    
    <h3>Empathic Partnership & Autonomy</h3>
    <p class="score">Score: {core.get('empathic_partnership_autonomy', {}).get('score', 'N/A')}</p>
    <div class="evidence">{' '.join(core.get('empathic_partnership_autonomy', {}).get('evidence', []))}</div>
    
    <h3>Empowerment & Clarity</h3>
    <p class="score">Score: {core.get('empowerment_clarity', {}).get('score', 'N/A')}</p>
    <div class="evidence">{' '.join(core.get('empowerment_clarity', {}).get('evidence', []))}</div>
    
    <h2>Strengths</h2>
    <ul>
        {''.join(f'<li class="strength">{s.get("text", "")}</li>' for s in strengths.get('strengths', []))}
    </ul>
    
    <h2>Opportunities</h2>
    <ul>
        {''.join(f'<li class="opportunity">{o.get("text", "")}</li>' for o in strengths.get('opportunities', []))}
    </ul>
    
    <h2>Patterns Observed</h2>
    <p><strong>Manager Patterns:</strong> {', '.join(patterns.get('manager_patterns', []))}</p>
    <p><strong>Employee Patterns:</strong> {', '.join(patterns.get('employee_patterns', []))}</p>
    
    <hr>
    <p><em>Generated: {datetime.utcnow().isoformat()}</em></p>
</body>
</html>"""
    
    return html


def _generate_text_report(result: Dict[str, Any], job_id: str) -> str:
    """Generate plain text report from analysis result"""
    maps_summary = result.get("maps_values_summary", "")
    report = result.get("report", {})
    core = report.get("core_coaching_effectiveness", {})
    strengths = report.get("strengths_and_suggestions", {})
    patterns = report.get("patterns_observed", {})
    
    text = f"""MAPS ANALYSIS REPORT
{'='*50}

SUMMARY
{maps_summary}

CORE COACHING EFFECTIVENESS
{'-'*30}

Foundational Trust & Safety
Score: {core.get('foundational_trust_safety', {}).get('score', 'N/A')}
Evidence:
{chr(10).join('- ' + e for e in core.get('foundational_trust_safety', {}).get('evidence', []))}

Empathic Partnership & Autonomy
Score: {core.get('empathic_partnership_autonomy', {}).get('score', 'N/A')}
Evidence:
{chr(10).join('- ' + e for e in core.get('empathic_partnership_autonomy', {}).get('evidence', []))}

Empowerment & Clarity
Score: {core.get('empowerment_clarity', {}).get('score', 'N/A')}
Evidence:
{chr(10).join('- ' + e for e in core.get('empowerment_clarity', {}).get('evidence', []))}

STRENGTHS
{'-'*30}
{chr(10).join('- ' + s.get('text', '') for s in strengths.get('strengths', []))}

OPPORTUNITIES
{'-'*30}
{chr(10).join('- ' + o.get('text', '') for o in strengths.get('opportunities', []))}

PATTERNS OBSERVED
{'-'*30}
Manager Patterns: {', '.join(patterns.get('manager_patterns', []))}
Employee Patterns: {', '.join(patterns.get('employee_patterns', []))}

{'='*50}
Generated: {datetime.utcnow().isoformat()}
"""
    
    return text

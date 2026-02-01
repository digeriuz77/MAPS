from fastapi import APIRouter, Query, Depends
from src.dependencies import get_metrics_service

router = APIRouter(prefix="/api", tags=["metrics"])

@router.get("/metrics")
async def get_metrics(service=Depends(get_metrics_service)):
    """
    Get system metrics with persistent storage integration.
    
    Returns:
        dict: Metrics including LLM calls, errors, memory operations, and persistence status.
    """
    return service.get_metrics()

@router.post("/metrics/reset")
async def reset_metrics(service=Depends(get_metrics_service)):
    """
    Reset all metrics (for testing/debugging purposes).
    
    Returns:
        dict: Reset status and message.
    """
    success = service.reset_metrics()
    if success:
        return {"status": "success", "message": "Metrics reset successfully"}
    return {"status": "error", "message": "Failed to reset metrics"}
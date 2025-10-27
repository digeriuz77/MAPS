from fastapi import APIRouter, Query
from src.services.metrics_service import metrics

router = APIRouter(prefix="/api", tags=["metrics"])

@router.get("/metrics")
async def get_metrics():
    return metrics.get_metrics()
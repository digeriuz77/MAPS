"""
Logging configuration
"""
import logging
import sys
from pathlib import Path

def setup_logging(level: str = "INFO"):
    """Setup logging configuration"""
    
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "persona_system.log")
        ]
    )
    
    # Set specific loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

from contextlib import asynccontextmanager
import time
from typing import Dict

def get_logger(name: str = __name__):
    return logging.getLogger(name)

@asynccontextmanager
async def track_step(step_name: str, context: Dict):
    """Lightweight async step tracker for pipeline instrumentation"""
    log = logging.getLogger("pipeline")
    start = time.time()
    log.info("step_start", extra={"step": step_name, "session_id": context.get("session_id")})
    try:
        yield
        duration = time.time() - start
        log.info("step_complete", extra={"step": step_name, "duration": round(duration, 3)})
    except Exception as e:
        log.error("step_failed", extra={"step": step_name, "error": str(e)})
        raise

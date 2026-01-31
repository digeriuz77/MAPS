"""
AI Persona System - Main Application Entry Point
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from datetime import datetime

from src.config.settings import get_settings
from src.dependencies import get_app_state, get_supabase_client

# Initialize database-driven services at MODULE level BEFORE any imports that use them
_supabase = get_supabase_client()

from src.services.character_consistency_service import initialize_character_consistency_service
initialize_character_consistency_service(_supabase)

from src.services.character_vector_service import initialize_character_vector_service
initialize_character_vector_service(_supabase)

from src.services.trust_configuration_service import initialize_trust_configuration_service
initialize_trust_configuration_service(_supabase)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    app_state = get_app_state()
    settings = get_settings()
    
    # Initialize logging
    logging.basicConfig(level=settings.LOG_LEVEL)
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Persona System")
    logger.info("Database-driven services already initialized at module level")

    app_state.is_initialized = True
    logger.info("AI Persona System started successfully")
    
    yield
    
    # Cleanup
    app_state.is_initialized = False
    logger.info("AI Persona System shutdown complete")

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    logger = logging.getLogger(__name__)
    
    app = FastAPI(
        title="AI Persona System",
        description="AI persona management for training and coaching",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.FRONTEND_URL],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # ANALYSIS SYSTEM ROUTES (consolidated - includes former maps_analysis)
    from src.api.routes.analysis import router as analysis_router
    app.include_router(analysis_router, tags=["analysis"])
    
    # METRICS ROUTES
    try:
        from src.api.routes.metrics import router as metrics_router
        app.include_router(metrics_router)
    except Exception:
        pass

    # FEEDBACK SYSTEM ROUTES
    from src.api.routes.feedback import router as feedback_router
    app.include_router(feedback_router, tags=["feedback"])

    # REFLECTION SYSTEM ROUTES
    from src.api.routes.reflection import router as reflection_router
    app.include_router(reflection_router, tags=["reflection"])
    
    # SCENARIO-BASED TRAINING ROUTES
    from src.api.routes.scenarios import router as scenarios_router
    app.include_router(scenarios_router, prefix="/api", tags=["scenarios"])
    
    # VOICE ROUTES (STT/TTS for scenarios)
    try:
        from src.api.routes.voice import router as voice_router
        app.include_router(voice_router, prefix="/api", tags=["voice"])
        logger.info("Voice routes loaded successfully")
    except ImportError as e:
        logger.warning(f"Voice routes not available (missing dependencies): {e}")
    except Exception as e:
        logger.error(f"Failed to load voice routes: {e}")
    
    # Mount static files
    static_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_path):
        app.mount("/static", StaticFiles(directory=static_path), name="static")
    
    @app.get("/api/config/supabase")
    async def get_supabase_config():
        """Get Supabase configuration for frontend"""
        return {
            "url": settings.SUPABASE_URL,
            "anonKey": settings.SUPABASE_ANON_KEY
        }
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        try:
            supabase_client = get_supabase_client()
            scenarios_result = supabase_client.table('scenarios').select('id').limit(1).execute()
            database_status = "healthy" if scenarios_result.data else "unhealthy"

            # Metrics summary (best-effort)
            metrics_summary = {}
            try:
                from src.services.metrics_service import metrics
                m = metrics.get_metrics()
                metrics_summary = {
                    "llm_calls_total": m.get("llm", {}).get("calls_total", 0),
                    "errors_total": m.get("llm", {}).get("errors_total", 0),
                    "summaries_created": m.get("memory", {}).get("summaries_created", 0),
                    "consolidations": {
                        "added": m.get("memory", {}).get("consolidations_added", 0),
                        "updated": m.get("memory", {}).get("consolidations_updated", 0)
                    }
                }
            except Exception:
                metrics_summary = {}
            
            return {
                "status": "healthy" if database_status == "healthy" else "degraded",
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "database_status": database_status,
                "api_status": "running",
                "metrics": metrics_summary
            }
        except Exception as e:
            return {
                "status": "error",
                "version": "1.0.0",
                "environment": settings.ENVIRONMENT,
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e)
            }

    @app.get("/")
    async def root():
        # Redirect to auth page as the default entry point
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/auth", status_code=307)
    
    @app.get("/auth")
    async def auth_page():
        auth_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "auth.html")
        if os.path.exists(auth_path):
            return FileResponse(auth_path)
        raise HTTPException(status_code=404, detail="Authentication page not found")
    
    @app.get("/welcome")
    async def welcome_page():
        welcome_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "welcome.html")
        if os.path.exists(welcome_path):
            return FileResponse(welcome_path)
        raise HTTPException(status_code=404, detail="Welcome page not found")
    
    @app.get("/persona-select")
    async def persona_select_page():
        select_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "persona-select.html")
        if os.path.exists(select_path):
            return FileResponse(select_path)
        raise HTTPException(status_code=404, detail="Persona selection page not found")
    
    @app.get("/chat")
    async def chat_page():
        chat_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "chat.html")
        if os.path.exists(chat_path):
            return FileResponse(chat_path)
        raise HTTPException(status_code=404, detail="Chat interface not found")
    
    @app.get("/analysis")
    async def analysis_page():
        analysis_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "analysis.html")
        if os.path.exists(analysis_path):
            return FileResponse(analysis_path)
        raise HTTPException(status_code=404, detail="Analysis page not found")
    
    @app.get("/reflection")
    async def reflection_page():
        reflection_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "reflection.html")
        if os.path.exists(reflection_path):
            return FileResponse(reflection_path)
        raise HTTPException(status_code=404, detail="Reflection interface not found")

    @app.get("/feedback")
    async def feedback_page():
        feedback_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "feedback.html")
        if os.path.exists(feedback_path):
            return FileResponse(feedback_path)
        raise HTTPException(status_code=404, detail="Feedback page not found")
    
    @app.get("/thank-you")
    async def thank_you_page():
        """Thank you page for FULL access users after completing feedback"""
        thankyou_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "thankyou.html")
        if os.path.exists(thankyou_path):
            return FileResponse(thankyou_path)
        raise HTTPException(status_code=404, detail="Thank you page not found")
    
    @app.get("/thank-you-locked")
    async def thank_you_locked_page():
        """Thank you page for CONTROL users blocked from FULL-only features"""
        locked_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "thank-you-locked.html")
        if os.path.exists(locked_path):
            return FileResponse(locked_path)
        raise HTTPException(status_code=404, detail="Thank you page not found")
    
    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )

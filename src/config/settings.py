"""
Application settings and configuration management
"""
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"
    
    # API Keys
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    
    # LLM Provider Selection
    LLM_PROVIDER: str = "openai"  # Options: "openai", "anthropic", "gemini"
    
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/persona_db"
    REDIS_URL: str = "redis://localhost:6379"
    
    # Supabase Database
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SCHEMA: str = "public"
    
    # Security
    SECRET_KEY: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Model Configuration - Cost Optimized
    DEFAULT_MODEL: str = "gpt-4.1-nano-2025-04-14"  # Cost optimized: $0.0001/1K vs gpt-4o-mini $0.15/1K
    REFLECTION_MODEL: str = "gpt-4.1-nano-2025-04-14"  # Dedicated reflection model for cost efficiency
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    MAX_TOKENS: int = 2000
    TEMPERATURE: float = 0.7
    
    # Gemini Configuration
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_TEMPERATURE: float = 0.2
    
    # Analysis Settings
    MITI_BATCH_SIZE: int = 10
    ENABLE_ANALYSIS_CACHE: bool = True
    USE_DATABASE_ENHANCED_ANALYSIS: bool = True  # Enable database-enhanced analysis
    
    # Memory Consolidation & Forgetting
    ENABLE_MEMORY_CONSOLIDATION: bool = True
    CONSOLIDATION_DELAY_SECONDS: int = 30  # Run consolidation ~30s after events
    CONSOLIDATION_BATCH_SIZE: int = 50
    FORGETTING_DECAY_LAMBDA: float = 0.05  # Daily decay rate for long-term memories
    FORGETTING_INACTIVE_DAYS: int = 60  # Prune memories unused for N days if low importance
    MEMORY_CAP_PER_PERSONA: int = 500  # Soft cap for long-term memories per persona
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    PROMETHEUS_PORT: int = 8001
    
    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    FROM_EMAIL: Optional[str] = None
    
    # Voice/Speech Configuration (Deepgram)
    DEEPGRAM_API_KEY: Optional[str] = None
    
    # Voice Agent Configuration (Full mode)
    DEEPGRAM_VOICE_AGENT_LISTEN_MODEL: str = "nova-3"
    DEEPGRAM_VOICE_AGENT_THINK_MODEL: str = "gpt-4o-mini"
    DEEPGRAM_VOICE_AGENT_SPEAK_MODEL: str = "aura-2-thalia-en"
    
    # Flux STT Configuration
    DEEPGRAM_FLUX_MODEL: str = "flux-general-en"
    DEEPGRAM_FLUX_EOT_THRESHOLD: float = 0.7  # End-of-turn confidence (0.5-0.9)
    DEEPGRAM_FLUX_EAGER_EOT_THRESHOLD: Optional[float] = None  # Early EOT threshold (0.3-0.9)
    DEEPGRAM_FLUX_EOT_TIMEOUT_MS: int = 5000  # Max silence before forced EOT (500-10000)
    
    # Voice Session Settings
    VOICE_ENABLED: bool = False
    VOICE_DEFAULT_MODE: str = "stt_only"  # "full", "stt_only", "tts_only"
    VOICE_INPUT_SAMPLE_RATE: int = 16000  # For Flux (16000 recommended)
    VOICE_OUTPUT_SAMPLE_RATE: int = 24000  # For TTS
    VOICE_MAX_SESSION_DURATION_SECONDS: int = 1800  # 30 minute max
    
    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra fields from testing harness .env

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

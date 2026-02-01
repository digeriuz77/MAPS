-- 0003_current_voice_sessions.sql
-- CURRENT APPLICATION - MAPS MI Training Platform
-- Voice sessions table for voice-enabled scenario training

CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL,
    user_id UUID NOT NULL,
    
    -- Session configuration
    mode VARCHAR(20) NOT NULL DEFAULT 'stt_only',
    
    -- Flux-specific configuration
    flux_config JSONB,
    
    -- Persona configuration
    persona_config JSONB,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP NULL,
    duration_seconds INT DEFAULT 0,
    
    -- Transcript data
    transcript JSONB DEFAULT '[]',
    
    -- Speech metrics and analysis
    metrics JSONB,
    speech_analysis JSONB,
    
    -- Audio data
    audio_chunks_count INT DEFAULT 0,
    audio_storage_url TEXT,
    
    -- Session state
    status VARCHAR(20) DEFAULT 'created',
    error TEXT,
    
    -- Foreign keys
    CONSTRAINT fk_voice_attempt FOREIGN KEY (attempt_id) REFERENCES scenario_attempts(id) ON DELETE CASCADE,
    CONSTRAINT fk_voice_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT valid_mode CHECK (mode IN ('full', 'stt_only', 'tts_only')),
    CONSTRAINT valid_status CHECK (status IN ('created', 'connecting', 'connected', 'listening', 'processing', 'speaking', 'closed', 'error'))
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_voice_sessions_attempt ON voice_sessions(attempt_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_started ON voice_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status) WHERE status NOT IN ('closed', 'error');

-- Enable RLS
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies
CREATE POLICY voice_sessions_select_own ON voice_sessions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY voice_sessions_insert_own ON voice_sessions FOR INSERT WITH CHECK (auth.uid() = user_id);
CREATE POLICY voice_sessions_update_own ON voice_sessions FOR UPDATE USING (auth.uid() = user_id);

COMMENT ON TABLE voice_sessions IS 'Voice sessions for real-time audio interactions';
COMMENT ON COLUMN voice_sessions.mode IS 'Voice mode: full, stt_only, tts_only';

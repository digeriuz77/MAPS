-- 0017_create_voice_sessions.sql
-- Voice sessions table for voice-enabled scenario training

CREATE TABLE IF NOT EXISTS voice_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    attempt_id UUID NOT NULL,
    user_id UUID NOT NULL,
    
    -- Session configuration
    mode VARCHAR(20) NOT NULL DEFAULT 'stt_only',  -- 'full', 'stt_only', 'tts_only'
    
    -- Flux-specific configuration (for STT mode)
    flux_config JSONB,  -- {eot_threshold, eager_eot_threshold, eot_timeout_ms}
    
    -- Persona configuration (for full voice agent mode)
    persona_config JSONB,
    
    -- Timestamps
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP NULL,
    duration_seconds INT DEFAULT 0,
    
    -- Transcript data
    transcript JSONB DEFAULT '[]',  -- Array of transcript entries with timing
    
    -- Speech metrics and analysis
    metrics JSONB,  -- {pause_count, hesitation_count, words_per_minute, etc.}
    speech_analysis JSONB,  -- {fluency_score, engagement_score, insights, etc.}
    
    -- Audio data (optional - for storing recordings)
    audio_chunks_count INT DEFAULT 0,
    audio_storage_url TEXT,  -- URL to stored audio file if saved
    
    -- Session state
    status VARCHAR(20) DEFAULT 'created',  -- created, connected, listening, processing, speaking, closed, error
    error TEXT,  -- Error message if status is 'error'
    
    -- Foreign keys
    CONSTRAINT fk_voice_attempt FOREIGN KEY (attempt_id) REFERENCES scenario_attempts(id) ON DELETE CASCADE,
    CONSTRAINT fk_voice_user FOREIGN KEY (user_id) REFERENCES auth.users(id) ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT valid_mode CHECK (mode IN ('full', 'stt_only', 'tts_only')),
    CONSTRAINT valid_status CHECK (status IN ('created', 'connecting', 'connected', 'listening', 'processing', 'speaking', 'closed', 'error'))
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_voice_sessions_attempt ON voice_sessions(attempt_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user ON voice_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_started ON voice_sessions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_voice_sessions_status ON voice_sessions(status) WHERE status NOT IN ('closed', 'error');
CREATE INDEX IF NOT EXISTS idx_voice_sessions_user_attempt ON voice_sessions(user_id, attempt_id);

-- Comments
COMMENT ON TABLE voice_sessions IS 'Voice sessions for real-time audio interactions in scenarios';
COMMENT ON COLUMN voice_sessions.mode IS 'Voice mode: full (Voice Agent), stt_only (Flux STT), tts_only';
COMMENT ON COLUMN voice_sessions.flux_config IS 'Flux configuration: {eot_threshold, eager_eot_threshold, eot_timeout_ms}';
COMMENT ON COLUMN voice_sessions.transcript IS 'Array of transcript entries with text, timing, confidence, and word-level data';
COMMENT ON COLUMN voice_sessions.metrics IS 'Speech metrics: pause count/duration, hesitations, speaking rate, interruptions';
COMMENT ON COLUMN voice_sessions.speech_analysis IS 'Analysis results: fluency score, engagement score, insights, improvement areas';


-- Voice session transcript entries view for easier querying
CREATE OR REPLACE VIEW voice_transcript_view AS
SELECT 
    vs.id as session_id,
    vs.attempt_id,
    vs.user_id,
    vs.mode,
    vs.started_at,
    vs.ended_at,
    vs.duration_seconds,
    vs.status,
    jsonb_array_length(vs.transcript) as turn_count,
    (
        SELECT string_agg(entry->>'text', ' ' ORDER BY entry->>'timestamp')
        FROM jsonb_array_elements(vs.transcript) as entry
        WHERE entry->>'role' = 'user'
    ) as user_transcript,
    vs.metrics,
    vs.speech_analysis
FROM voice_sessions vs;

COMMENT ON VIEW voice_transcript_view IS 'Simplified view of voice sessions with aggregated user transcript';


-- Function to calculate voice session duration
CREATE OR REPLACE FUNCTION calculate_voice_session_duration()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.ended_at IS NOT NULL AND NEW.started_at IS NOT NULL THEN
        NEW.duration_seconds := EXTRACT(EPOCH FROM (NEW.ended_at - NEW.started_at))::INT;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to auto-calculate duration on update
DROP TRIGGER IF EXISTS voice_session_duration_trigger ON voice_sessions;
CREATE TRIGGER voice_session_duration_trigger
    BEFORE UPDATE ON voice_sessions
    FOR EACH ROW
    WHEN (NEW.ended_at IS DISTINCT FROM OLD.ended_at)
    EXECUTE FUNCTION calculate_voice_session_duration();


-- RLS Policies (if RLS is enabled)
-- Users can only access their own voice sessions

-- Enable RLS
ALTER TABLE voice_sessions ENABLE ROW LEVEL SECURITY;

-- Policy for users to select their own sessions
CREATE POLICY voice_sessions_select_own ON voice_sessions
    FOR SELECT
    USING (auth.uid() = user_id);

-- Policy for users to insert their own sessions
CREATE POLICY voice_sessions_insert_own ON voice_sessions
    FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Policy for users to update their own sessions
CREATE POLICY voice_sessions_update_own ON voice_sessions
    FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Policy for users to delete their own sessions
CREATE POLICY voice_sessions_delete_own ON voice_sessions
    FOR DELETE
    USING (auth.uid() = user_id);

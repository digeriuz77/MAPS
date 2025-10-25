-- Migration: Create user_feedback table
-- Purpose: Store user feedback after practice sessions
-- Date: 2025-10-18

-- User feedback collection table
CREATE TABLE IF NOT EXISTS user_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(255),  -- Changed from UUID to support string session IDs
    conversation_id VARCHAR(255),  -- Changed from UUID to support string conversation IDs
    persona_practiced VARCHAR(50),
    helpfulness_score INT CHECK (helpfulness_score >= 0 AND helpfulness_score <= 10),
    what_was_helpful TEXT,
    improvement_suggestions TEXT,
    user_email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for analytics and queries
CREATE INDEX IF NOT EXISTS idx_feedback_created ON user_feedback(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_feedback_score ON user_feedback(helpfulness_score);
CREATE INDEX IF NOT EXISTS idx_feedback_persona ON user_feedback(persona_practiced);

-- Enable Row Level Security
ALTER TABLE user_feedback ENABLE ROW LEVEL SECURITY;

-- Policy for service role access
CREATE POLICY "Service role can manage feedback" ON user_feedback
FOR ALL USING (auth.role() = 'service_role');

-- Grant permissions
GRANT ALL ON user_feedback TO service_role;

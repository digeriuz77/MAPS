-- Migration: Update reflection_sessions table for new reflection system
-- Purpose: Repurpose existing reflection_sessions for storing complete reflection responses
-- Date: 2025-10-22

-- Drop the old reflection_responses table (outdated)
DROP TABLE IF EXISTS reflection_responses;

-- Update reflection_sessions table to store complete reflection data
-- First add new columns
ALTER TABLE reflection_sessions 
ADD COLUMN IF NOT EXISTS conversation_id UUID,
ADD COLUMN IF NOT EXISTS persona_practiced VARCHAR(100),
ADD COLUMN IF NOT EXISTS question1_response TEXT,
ADD COLUMN IF NOT EXISTS question2_response TEXT,
ADD COLUMN IF NOT EXISTS question3_response TEXT,
ADD COLUMN IF NOT EXISTS ai_summary TEXT,
ADD COLUMN IF NOT EXISTS summary_generated_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS email_sent_to VARCHAR(255),
ADD COLUMN IF NOT EXISTS downloaded_at TIMESTAMPTZ;

-- Drop the old current_stage column (no longer needed)
ALTER TABLE reflection_sessions DROP COLUMN IF EXISTS current_stage;

-- Add foreign key constraint to conversations table
ALTER TABLE reflection_sessions 
ADD CONSTRAINT fk_reflection_conversation 
FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE;

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_reflection_sessions_conversation_id ON reflection_sessions(conversation_id);
CREATE INDEX IF NOT EXISTS idx_reflection_sessions_coach_created ON reflection_sessions(coach_id, created_at DESC);

-- Update the table comment
COMMENT ON TABLE reflection_sessions IS 'Stores complete reflection responses and AI-generated summaries for practice sessions';
COMMENT ON COLUMN reflection_sessions.conversation_id IS 'Links to the conversation that was reflected upon';
COMMENT ON COLUMN reflection_sessions.persona_practiced IS 'Name of the persona practiced with';
COMMENT ON COLUMN reflection_sessions.question1_response IS 'What went well in the conversation';
COMMENT ON COLUMN reflection_sessions.question2_response IS 'What did you struggle with';
COMMENT ON COLUMN reflection_sessions.question3_response IS 'What might you do differently next time';
COMMENT ON COLUMN reflection_sessions.ai_summary IS 'AI-generated summary from the three responses';
COMMENT ON COLUMN reflection_sessions.summary_generated_at IS 'When the AI summary was generated';
COMMENT ON COLUMN reflection_sessions.email_sent_to IS 'Email address where reflection was sent (if any)';
COMMENT ON COLUMN reflection_sessions.downloaded_at IS 'When the reflection was downloaded (if any)';

-- Clear existing test data (since structure has changed)
DELETE FROM reflection_sessions;
-- Migration: Fix user_feedback table column types
-- Purpose: Change session_id and conversation_id from UUID to VARCHAR to support string IDs
-- Date: 2025-10-19

-- Drop existing policies first
DROP POLICY IF EXISTS "Service role can manage feedback" ON user_feedback;

-- Alter column types from UUID to VARCHAR
ALTER TABLE user_feedback 
    ALTER COLUMN session_id TYPE VARCHAR(255),
    ALTER COLUMN conversation_id TYPE VARCHAR(255);

-- Re-create RLS policy
CREATE POLICY "Service role can manage feedback" ON user_feedback
FOR ALL USING (auth.role() = 'service_role');

-- Ensure permissions are maintained
GRANT ALL ON user_feedback TO service_role;

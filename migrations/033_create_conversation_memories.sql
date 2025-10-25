-- Migration 033: Create Conversation Memories Table
-- Purpose: Store dynamic memories formed during conversations (CRITICAL - this table was missing!)
-- Created: 2025-10-19
-- Issue: conversation_memories table referenced in code but never created, causing silent memory formation failures

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create conversation_memories table for dynamic memory storage
CREATE TABLE IF NOT EXISTS conversation_memories (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
    key_insights TEXT NOT NULL,
    importance_score DECIMAL(3,1) NOT NULL DEFAULT 6.0 CHECK (importance_score >= 0 AND importance_score <= 10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for fast retrieval by session
CREATE INDEX IF NOT EXISTS idx_conversation_memories_session_id 
ON conversation_memories(session_id);

-- Index for importance-based queries (used in memory archival)
CREATE INDEX IF NOT EXISTS idx_conversation_memories_importance 
ON conversation_memories(session_id, importance_score DESC, created_at ASC);

-- Index for chronological ordering
CREATE INDEX IF NOT EXISTS idx_conversation_memories_created_at 
ON conversation_memories(session_id, created_at DESC);

-- Add comment explaining the table purpose
COMMENT ON TABLE conversation_memories IS 'Stores dynamic memories formed during specific conversations. These memories capture user statements, coaching interactions, and relationship context. Max 12 memories per conversation with archival of lowest importance when limit reached.';

COMMENT ON COLUMN conversation_memories.session_id IS 'References conversations(id). Each conversation has unique dynamic memories.';
COMMENT ON COLUMN conversation_memories.key_insights IS 'The actual memory text formed from user interactions (e.g., "User accused me of being drunk at DWP meeting")';
COMMENT ON COLUMN conversation_memories.importance_score IS 'Memory importance (6.0-10.0). Low empathy interactions and significant statements score higher. Used for archival decisions.';

-- Verify table creation
SELECT 'conversation_memories table created successfully' AS status;

-- Show table structure
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'conversation_memories'
ORDER BY ordinal_position;

-- Show indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'conversation_memories';

-- Migration 032: Create Conversation Transcripts Table
-- Purpose: Store full conversation transcripts for persistence and analysis
-- Created: 2025-10-19
-- Reference: CONVERSATION_PERSISTENCE_ANALYSIS.md

-- Create table for storing full conversation transcripts
CREATE TABLE IF NOT EXISTS conversation_transcripts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE NOT NULL,
    turn_number INT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'persona')),
    message TEXT NOT NULL,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_turn_message UNIQUE(conversation_id, turn_number, role)
);

-- Index for fast conversation retrieval by conversation_id
CREATE INDEX IF NOT EXISTS idx_conversation_transcripts_conversation_id 
ON conversation_transcripts(conversation_id);

-- Index for chronological ordering within a conversation
CREATE INDEX IF NOT EXISTS idx_conversation_transcripts_timestamp 
ON conversation_transcripts(conversation_id, timestamp);

-- Index for efficient turn-based queries
CREATE INDEX IF NOT EXISTS idx_conversation_transcripts_turn 
ON conversation_transcripts(conversation_id, turn_number);

-- Verify table creation
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'conversation_transcripts'
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'conversation_transcripts';

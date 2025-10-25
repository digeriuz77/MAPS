-- Simple migration for Supabase persona_memories table
-- Run this in Supabase SQL Editor

-- Enable vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create the table
CREATE TABLE persona_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID,
    persona_name TEXT NOT NULL DEFAULT 'Mary',
    memory_text TEXT NOT NULL,
    embedding vector(1536),
    importance_score FLOAT DEFAULT 0.0,
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Add foreign key constraint if conversations table exists
-- ALTER TABLE persona_memories
-- ADD CONSTRAINT fk_conversation
-- FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE;

-- Create basic indexes
CREATE INDEX idx_persona_memories_conversation ON persona_memories(conversation_id);
CREATE INDEX idx_persona_memories_persona ON persona_memories(persona_name);
CREATE INDEX idx_persona_memories_created ON persona_memories(created_at DESC);

-- Vector similarity index (may need to be created after some data exists)
-- CREATE INDEX idx_persona_memories_embedding
-- ON persona_memories USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
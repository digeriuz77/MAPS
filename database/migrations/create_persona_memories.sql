-- Enable the pgvector extension for vector similarity search
CREATE EXTENSION IF NOT EXISTS vector;

-- Create persona_memories table for persistent memory storage
CREATE TABLE IF NOT EXISTS public.persona_memories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    persona_name TEXT NOT NULL DEFAULT 'Mary',
    memory_text TEXT NOT NULL,
    embedding vector(1536), -- OpenAI ada-002/text-embedding-3-small dimension
    importance_score FLOAT DEFAULT 0.0,
    accessed_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_persona_memories_conversation
ON persona_memories(conversation_id);

CREATE INDEX IF NOT EXISTS idx_persona_memories_persona
ON persona_memories(persona_name);

CREATE INDEX IF NOT EXISTS idx_persona_memories_created
ON persona_memories(created_at DESC);

-- Vector similarity index for fast retrieval
CREATE INDEX IF NOT EXISTS idx_persona_memories_embedding
ON persona_memories USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Enable RLS (Row Level Security)
ALTER TABLE persona_memories ENABLE ROW LEVEL SECURITY;

-- Create policy for service role access
CREATE POLICY "Service role can manage persona_memories" ON persona_memories
FOR ALL USING (auth.role() = 'service_role');

-- Grant access to the application
GRANT ALL ON persona_memories TO service_role;

-- Add helpful comment
COMMENT ON TABLE persona_memories IS 'Persistent memory storage for GenerativeAgent personas with vector embeddings for similarity search';
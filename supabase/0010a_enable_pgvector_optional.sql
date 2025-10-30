-- 0010a_enable_pgvector_optional.sql
-- ⚠️ OPTIONAL: Do NOT run unless you need vector search
-- ⚠️ PREREQUISITES: Migration 0010 must be applied first!
--
-- This migration enables pgvector extension and adds vector column for semantic search
-- Only run if:
-- 1. Migration 0010 is already applied
-- 2. You want semantic similarity search
-- 3. You have pgvector extension available

-- STEP 1: Check if table exists (should return 1)
-- SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'character_vector_memories';

-- STEP 2: Enable pgvector extension (uncomment if available)
-- CREATE EXTENSION IF NOT EXISTS vector;

-- STEP 3: Add vector column (uncomment if extension enabled)
-- ALTER TABLE character_vector_memories
--   ADD COLUMN IF NOT EXISTS embedding VECTOR(1536);

-- STEP 4: Drop temporary JSON column (uncomment after populating embeddings)
-- ALTER TABLE character_vector_memories
--   DROP COLUMN IF EXISTS embedding_json;

-- STEP 5: Create index for vector similarity search (uncomment after adding column)
-- CREATE INDEX IF NOT EXISTS idx_vector_memories_embedding
--   ON character_vector_memories
--   USING ivfflat (embedding vector_cosine_ops)
--   WITH (lists = 100);

-- Example: Populate embeddings using OpenAI API
-- UPDATE character_vector_memories
-- SET embedding = '[0.1, 0.2, ...]'::vector  -- Replace with actual embedding
-- WHERE memory_id = 'mary_001';

-- Example: Semantic search query
-- SELECT memory_id, content, 1 - (embedding <=> '[query_vector]'::vector) AS similarity
-- FROM character_vector_memories
-- WHERE persona_id = 'mary'
-- ORDER BY embedding <=> '[query_vector]'::vector
-- LIMIT 5;

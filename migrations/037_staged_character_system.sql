-- Migration 037: Staged Character System
-- Purpose: Two-stage LLM generation to prevent information dumping
-- Created: 2025-10-19
-- Reference: context/Staged-system.txt

-- =============================================================================
-- TABLE 1: Character Knowledge Tiers
-- Stores what FACTS are available at different trust levels
-- =============================================================================

CREATE TABLE IF NOT EXISTS character_knowledge_tiers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id TEXT NOT NULL REFERENCES personas(persona_id) ON DELETE CASCADE,
    trust_threshold FLOAT NOT NULL,
    tier_name TEXT NOT NULL,
    knowledge_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT unique_persona_threshold UNIQUE(persona_id, trust_threshold)
);

CREATE INDEX idx_knowledge_tiers_persona ON character_knowledge_tiers(persona_id);
CREATE INDEX idx_knowledge_tiers_trust ON character_knowledge_tiers(trust_threshold);

COMMENT ON TABLE character_knowledge_tiers IS 'Stores facts available at different trust levels for staged character generation';
COMMENT ON COLUMN character_knowledge_tiers.trust_threshold IS 'Minimum trust level required to access this tier (3.0=defensive, 5.5=cautious, 7.5=opening, 9.0=trusting)';
COMMENT ON COLUMN character_knowledge_tiers.tier_name IS 'Human-readable tier name (defensive, cautious, opening, trusting)';
COMMENT ON COLUMN character_knowledge_tiers.knowledge_json IS 'JSON object containing facts character knows at this trust level';

-- =============================================================================
-- TABLE 2: Staged Generation Log
-- Logs each stage of LLM calls for debugging
-- =============================================================================

CREATE TABLE IF NOT EXISTS staged_generation_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT NOT NULL,
    turn_number INT NOT NULL,
    stage_number INT NOT NULL,
    stage_name TEXT NOT NULL,
    llm_model TEXT NOT NULL,
    input_prompt TEXT NOT NULL,
    output_text TEXT NOT NULL,
    trust_level FLOAT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_staged_log_session ON staged_generation_log(session_id, turn_number);
CREATE INDEX idx_staged_log_stage ON staged_generation_log(stage_number);

COMMENT ON TABLE staged_generation_log IS 'Logs each stage of multi-stage LLM generation for debugging';
COMMENT ON COLUMN staged_generation_log.stage_number IS '1=boundary_determination, 2=response_generation';
COMMENT ON COLUMN staged_generation_log.stage_name IS 'boundary_determination or response_generation';

-- =============================================================================
-- Verify table creation
-- =============================================================================

SELECT 'character_knowledge_tiers' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'character_knowledge_tiers'
ORDER BY ordinal_position;

SELECT 'staged_generation_log' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'staged_generation_log'
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename IN ('character_knowledge_tiers', 'staged_generation_log')
ORDER BY tablename, indexname;

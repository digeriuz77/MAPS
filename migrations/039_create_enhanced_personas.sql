-- Migration 039: Enhanced Personas Table
-- Purpose: Clean persona definitions optimized for enhanced natural empathy service
-- Created: 2025-10-20
-- Replaces old personas table dependencies for enhanced service

-- =============================================================================
-- TABLE: Enhanced Personas
-- Clean persona definitions without old system dependencies
-- =============================================================================

CREATE TABLE IF NOT EXISTS enhanced_personas (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    
    -- Core character definition
    core_identity TEXT NOT NULL,
    fundamental_traits JSONB NOT NULL,
    current_situation TEXT NOT NULL,
    personality_patterns JSONB NOT NULL,
    
    -- Enhanced service specific
    natural_behaviors JSONB NOT NULL,
    emotional_responses JSONB NOT NULL,
    character_boundaries TEXT NOT NULL,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Ensure unique persona_id
    CONSTRAINT unique_enhanced_persona_id UNIQUE(persona_id)
);

CREATE INDEX idx_enhanced_personas_persona_id ON enhanced_personas(persona_id);

COMMENT ON TABLE enhanced_personas IS 'Persona definitions optimized for enhanced natural empathy service';
COMMENT ON COLUMN enhanced_personas.core_identity IS 'Who the character fundamentally is - their essence';
COMMENT ON COLUMN enhanced_personas.fundamental_traits IS 'JSON array of core character traits that never change';
COMMENT ON COLUMN enhanced_personas.current_situation IS 'Current context/situation the character is in';
COMMENT ON COLUMN enhanced_personas.personality_patterns IS 'JSON object describing behavioral patterns';
COMMENT ON COLUMN enhanced_personas.natural_behaviors IS 'JSON object defining how character responds to different interaction qualities';
COMMENT ON COLUMN enhanced_personas.emotional_responses IS 'JSON object defining emotional reactions to empathy/hostility';
COMMENT ON COLUMN enhanced_personas.character_boundaries IS 'What character will/will not share and when';

-- =============================================================================
-- Verify table creation
-- =============================================================================

SELECT 'enhanced_personas' as table_name, column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'enhanced_personas'
ORDER BY ordinal_position;

-- Verify indexes
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'enhanced_personas'
ORDER BY indexname;
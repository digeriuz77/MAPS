-- Migration 041: Clean up Enhanced Personas Table
-- Purpose: Remove redundant fields that are now handled by knowledge tiers
-- Created: 2025-10-20
-- Removes: fundamental_traits, character_boundaries (trust_boundaries), description
-- Keeps: core_identity, current_situation, natural_behaviors, personality_patterns

-- =============================================================================
-- Remove redundant columns from enhanced_personas
-- =============================================================================

-- Remove fundamental_traits since personality is now in knowledge tiers
ALTER TABLE enhanced_personas 
DROP COLUMN IF EXISTS fundamental_traits;

-- Remove character_boundaries since stance is now in knowledge tiers
ALTER TABLE enhanced_personas 
DROP COLUMN IF EXISTS character_boundaries;

-- Remove description since it's verbose and redundant with core_identity
ALTER TABLE enhanced_personas 
DROP COLUMN IF EXISTS description;

-- Update comments
COMMENT ON TABLE enhanced_personas IS 'Lean persona definitions optimized for enhanced service using knowledge tiers';
COMMENT ON COLUMN enhanced_personas.core_identity IS 'Essential character identity - who they are fundamentally';
COMMENT ON COLUMN enhanced_personas.current_situation IS 'Current context/situation the character is in';
COMMENT ON COLUMN enhanced_personas.personality_patterns IS 'JSON object describing behavioral patterns and quirks';
COMMENT ON COLUMN enhanced_personas.natural_behaviors IS 'JSON object defining tone/style responses to interaction qualities';
COMMENT ON COLUMN enhanced_personas.emotional_responses IS 'JSON object defining emotional reactions to empathy levels';

-- =============================================================================
-- Verify cleanup
-- =============================================================================

SELECT 'enhanced_personas_after_cleanup' as status, column_name, data_type
FROM information_schema.columns
WHERE table_name = 'enhanced_personas'
ORDER BY ordinal_position;

-- Show remaining data structure
SELECT 
    persona_id,
    name,
    LENGTH(core_identity) as core_identity_length,
    LENGTH(current_situation) as current_situation_length
FROM enhanced_personas
ORDER BY persona_id;
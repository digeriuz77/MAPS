-- Migration 046: Remove character_boundaries
-- Purpose: Eliminate redundant character_boundaries field causing rigid responses
-- Created: 2025-10-22
-- Context: character_boundaries duplicates information already in behavioral_tier_service
--          and causes personas to get stuck in defensive loops

-- =============================================================================
-- STRATEGY
-- =============================================================================
-- REMOVE: character_boundaries (redundant, causes rigid responses)
-- KEEP: core_identity (WHO they are - used by behavioral_tier_service)
-- KEEP: current_situation (reference data - NOT used directly in prompts)
--
-- Prompt construction uses:
--   - core_identity: Stable traits, values (from behavioral_tier_service)
--   - conversation_memories: What's been discussed (dynamic)
--   - stage: Where we are in conversation (dynamic)
--   - behavioral_prompt: Trust-modulated guidance (includes situation context)

-- =============================================================================
-- BACKUP BEFORE DROPPING
-- =============================================================================
-- Save this output before proceeding:
-- SELECT persona_id, character_boundaries FROM enhanced_personas;

-- =============================================================================
-- STEP 1: Verify core_identity and current_situation are populated
-- =============================================================================

SELECT 
    persona_id,
    name,
    CASE WHEN core_identity IS NOT NULL AND core_identity != '' THEN '✓' ELSE '✗ MISSING' END as has_core_identity,
    CASE WHEN current_situation IS NOT NULL AND current_situation != '' THEN '✓' ELSE '✗ MISSING' END as has_current_situation,
    CASE WHEN character_boundaries IS NOT NULL THEN '✓ (will remove)' ELSE 'already null' END as has_boundaries
FROM enhanced_personas
ORDER BY persona_id;

-- =============================================================================
-- STEP 2: Drop character_boundaries column
-- =============================================================================

ALTER TABLE enhanced_personas 
DROP COLUMN IF EXISTS character_boundaries;

-- =============================================================================
-- VERIFY REMOVAL
-- =============================================================================

SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns
WHERE table_name = 'enhanced_personas'
AND column_name IN ('core_identity', 'current_situation', 'character_boundaries')
ORDER BY column_name;

-- Expected result: Only core_identity and current_situation should appear

-- =============================================================================
-- UPDATED SCHEMA DESCRIPTION
-- =============================================================================
COMMENT ON COLUMN enhanced_personas.core_identity IS 
'WHO the character fundamentally is: stable traits, values, worldview, personality patterns. Does not change with trust level.';

COMMENT ON COLUMN enhanced_personas.current_situation IS 
'WHAT is happening in their life: current stressors, challenges, circumstances, life events. Provides context for their behavior.';

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================
-- ALTER TABLE enhanced_personas ADD COLUMN character_boundaries TEXT;
-- -- Then restore from backup

-- Migration 034: Normalize Dynamic Memory Importance Scores
-- Purpose: Fix legacy memory scores (1-6) to proper dynamic memory range (6-10)
-- Created: 2025-10-19
-- Issue: Old memories with low scores get filtered out by trust-based retrieval

-- Problem Background:
-- - Current code expects dynamic memories to be scored 6.0-10.0
-- - Legacy memories have scores 1-8 (from old scoring logic)
-- - At defensive trust (<3.0), only memories ≤3.0 are retrieved
-- - Personas "forget" important conversation events scored 6-8

-- Normalize all legacy dynamic memory scores to 6.0-10.0 range
-- Preserves relative importance while ensuring visibility at all trust levels

UPDATE conversation_memories
SET 
    importance_score = CASE
        -- Very low scores (1-2) → Moderate importance (7.0-7.5)
        WHEN importance_score < 2.0 THEN 7.0
        WHEN importance_score < 3.0 THEN 7.5
        
        -- Low-medium scores (3-4) → High importance (8.0-8.5)
        WHEN importance_score < 4.0 THEN 8.0
        WHEN importance_score < 5.0 THEN 8.5
        
        -- Medium-high scores (5-6) → Very high importance (9.0-9.5)
        WHEN importance_score < 6.0 THEN 9.0
        WHEN importance_score = 6.0 THEN 9.5
        
        -- Scores already in 6.0-10.0 range → Keep as is (properly scored)
        ELSE importance_score
    END,
    updated_at = NOW()
WHERE importance_score < 6.0;  -- Only update legacy scores

-- Verify the normalization
SELECT 
    'Score Normalization Results' as check_type,
    MIN(importance_score) as min_score,
    MAX(importance_score) as max_score,
    AVG(importance_score) as avg_score,
    COUNT(*) as total_memories,
    COUNT(CASE WHEN importance_score < 6.0 THEN 1 END) as remaining_legacy_scores
FROM conversation_memories;

-- Show before/after distribution
SELECT 
    'Score Distribution' as check_type,
    CASE
        WHEN importance_score >= 9.5 THEN '9.5-10.0 (Critical)'
        WHEN importance_score >= 9.0 THEN '9.0-9.4 (Very High)'
        WHEN importance_score >= 8.0 THEN '8.0-8.9 (High)'
        WHEN importance_score >= 7.0 THEN '7.0-7.9 (Moderate)'
        WHEN importance_score >= 6.0 THEN '6.0-6.9 (Standard)'
        ELSE 'BELOW 6.0 (ERROR - should not exist!)'
    END as score_range,
    COUNT(*) as memory_count
FROM conversation_memories
GROUP BY score_range
ORDER BY MIN(importance_score) DESC;

-- Comment on expected results
COMMENT ON COLUMN conversation_memories.importance_score IS 
    'Dynamic memory importance (6.0-10.0 range). Higher scores = more significant interactions. 
    Migration 034 normalized all legacy scores to this range.';

-- Final validation
DO $$
DECLARE
    legacy_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO legacy_count
    FROM conversation_memories
    WHERE importance_score < 6.0;
    
    IF legacy_count > 0 THEN
        RAISE WARNING 'WARNING: % memories still have scores below 6.0 - normalization may have failed!', legacy_count;
    ELSE
        RAISE NOTICE '✓ SUCCESS: All dynamic memories normalized to 6.0-10.0 range';
    END IF;
END $$;

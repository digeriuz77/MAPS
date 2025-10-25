-- Migration 044: Fix Trust Threshold Scale Mismatch
-- Purpose: Convert trust thresholds from 0-10 scale to 0.0-1.0 scale
-- Created: 2025-10-22
-- Context: Trust system uses 0.0-1.0 but knowledge tiers use 0-10 scale

-- =============================================================================
-- PROBLEM: Trust thresholds in wrong scale
-- =============================================================================
-- Current: trust_threshold uses 3.0, 5.5, 7.5, 9.0 (0-10 scale)
-- Actual trust values: 0.0-1.0 (normalized scale)
-- Result: Personas never progress beyond defensive tier!

-- =============================================================================
-- BACKUP CURRENT VALUES
-- =============================================================================
-- SELECT persona_id, tier_name, trust_threshold FROM character_knowledge_tiers;

-- =============================================================================
-- FIX: Divide all trust_threshold values by 10
-- =============================================================================

UPDATE character_knowledge_tiers
SET trust_threshold = trust_threshold / 10.0
WHERE trust_threshold > 1.0;

-- =============================================================================
-- VERIFY CHANGES
-- =============================================================================

SELECT persona_id, tier_name, trust_threshold, 
       CASE tier_name
           WHEN 'defensive' THEN '0.3 (was 3.0)'
           WHEN 'cautious' THEN '0.55 (was 5.5)'
           WHEN 'opening' THEN '0.75 (was 7.5)'
           WHEN 'trusting' THEN '0.90 (was 9.0)'
       END as expected_value
FROM character_knowledge_tiers
ORDER BY persona_id, trust_threshold;

-- =============================================================================
-- EXPECTED RESULTS
-- =============================================================================
-- defensive: 0.3  (Mary starts at 0.65, so skips this)
-- cautious:  0.55 (Mary starts here)
-- opening:   0.75 (Mary reaches after ~5 excellent interactions)
-- trusting:  0.90 (Mary reaches after ~15 excellent interactions)

-- =============================================================================
-- ROLLBACK (if needed)
-- =============================================================================
-- UPDATE character_knowledge_tiers SET trust_threshold = trust_threshold * 10.0 WHERE trust_threshold <= 1.0;

-- Migration 042: Increase Trust Deltas for Accelerated MI Training
-- Purpose: Enable personas to reach trusting state within 30 turns with MI-adherent behavior
-- Created: 2025-10-22
-- Context: MI training simulation requires faster trust progression than realistic simulation

-- =============================================================================
-- BACKUP CURRENT VALUES (for rollback)
-- =============================================================================
-- Run this query first and save results before applying changes:
-- SELECT * FROM trust_tiers_rows;

-- =============================================================================
-- UPDATE TRUST DELTAS (approximately 80% increase)
-- =============================================================================

-- DEFENSIVE TIER (0.0-0.3): Slowest to build trust, quickest to lose
UPDATE trust_tiers_rows
SET 
    trust_delta_excellent = 0.20,  -- was 0.11
    trust_delta_good = 0.15,       -- was 0.08
    trust_delta_adequate = 0.08,   -- was 0.05
    trust_delta_poor = -0.15,      -- was -0.14 (keep punitive)
    updated_at = NOW()
WHERE tier_name = 'defensive';

-- CAUTIOUS TIER (0.3-0.5): Moderate trust building
UPDATE trust_tiers_rows
SET 
    trust_delta_excellent = 0.22,  -- was 0.15
    trust_delta_good = 0.16,       -- was 0.10
    trust_delta_adequate = 0.10,   -- was 0.06
    trust_delta_poor = -0.12,      -- was -0.10
    updated_at = NOW()
WHERE tier_name = 'cautious';

-- OPENING TIER (0.5-0.75): Faster trust building
UPDATE trust_tiers_rows
SET 
    trust_delta_excellent = 0.25,  -- was 0.18
    trust_delta_good = 0.18,       -- was 0.14
    trust_delta_adequate = 0.12,   -- was 0.08
    trust_delta_poor = -0.10,      -- was -0.08
    updated_at = NOW()
WHERE tier_name = 'opening';

-- TRUSTING TIER (0.75-1.0): Fastest trust growth, hardest to lose
UPDATE trust_tiers_rows
SET 
    trust_delta_excellent = 0.30,  -- was 0.25
    trust_delta_good = 0.22,       -- was 0.18
    trust_delta_adequate = 0.15,   -- was 0.10
    trust_delta_poor = -0.08,      -- same (already gentle)
    updated_at = NOW()
WHERE tier_name = 'trusting';

-- =============================================================================
-- VERIFY CHANGES
-- =============================================================================

SELECT 
    tier_name,
    min_threshold,
    max_threshold,
    trust_delta_excellent,
    trust_delta_good,
    trust_delta_adequate,
    trust_delta_poor,
    description
FROM trust_tiers_rows
ORDER BY min_threshold;

-- =============================================================================
-- EXPECTED PROGRESSION (with MI-adherent excellent interactions)
-- =============================================================================
-- Turn 1:  Vic starts at 0.25 (defensive)
-- Turn 5:  0.25 + (4 * 0.20) = 1.05 normalized to ~0.45 (cautious)
-- Turn 10: ~0.55 (opening)
-- Turn 20: ~0.85 (trusting)
-- Turn 30: ~1.00 (fully trusting, ready to commit)
--
-- This ensures defensive personas like Vic can reach trusting within 30 turns
-- with consistent MI-adherent behavior from the manager trainee.

-- =============================================================================
-- ROLLBACK SCRIPT (if needed)
-- =============================================================================
-- UPDATE trust_tiers_rows SET trust_delta_excellent = 0.11, trust_delta_good = 0.08, trust_delta_adequate = 0.05, trust_delta_poor = -0.14 WHERE tier_name = 'defensive';
-- UPDATE trust_tiers_rows SET trust_delta_excellent = 0.15, trust_delta_good = 0.10, trust_delta_adequate = 0.06, trust_delta_poor = -0.10 WHERE tier_name = 'cautious';
-- UPDATE trust_tiers_rows SET trust_delta_excellent = 0.18, trust_delta_good = 0.14, trust_delta_adequate = 0.08, trust_delta_poor = -0.08 WHERE tier_name = 'opening';
-- UPDATE trust_tiers_rows SET trust_delta_excellent = 0.25, trust_delta_good = 0.18, trust_delta_adequate = 0.10, trust_delta_poor = -0.08 WHERE tier_name = 'trusting';

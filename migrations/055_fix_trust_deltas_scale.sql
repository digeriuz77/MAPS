-- Migration 055: Fix Trust Deltas for 0.0-1.0 Scale
-- Purpose: Scale trust deltas appropriately for normalized 0.0-1.0 trust range
-- Created: 2025-10-22
-- Context: Previous deltas (0.20-0.30) were too high, allowing 1-turn jumps

-- =============================================================================
-- PROBLEM: Trust deltas calibrated for wrong scale
-- =============================================================================
-- Current: trust_delta_excellent = 0.20-0.30 (can jump entire tiers in 1 turn)
-- Trust range: 0.0-1.0 (normalized scale)
-- Result: Personas jump from defensive to trusting in 3-5 turns!

-- =============================================================================
-- SOLUTION: Scale deltas down by 10x for gradual progression
-- =============================================================================
-- Target: 20-30 excellent interactions to reach full trust from defensive
-- Realistic MI training progression: 5-8 turns per tier

-- =============================================================================
-- BACKUP CURRENT VALUES
-- =============================================================================
-- SELECT * FROM trust_tiers ORDER BY min_threshold;

-- =============================================================================
-- UPDATE TRUST DELTAS (scaled to 0.0-1.0 range)
-- =============================================================================

-- DEFENSIVE TIER (0.0-0.3): Slowest to build trust, quickest to lose
UPDATE trust_tiers
SET 
    trust_delta_excellent = 0.020,  -- was 0.20 (10x too high)
    trust_delta_good = 0.015,       -- was 0.15
    trust_delta_adequate = 0.008,   -- was 0.08
    trust_delta_poor = -0.015,      -- was -0.15
    updated_at = NOW()
WHERE tier_name = 'defensive';

-- CAUTIOUS TIER (0.3-0.5): Moderate trust building
UPDATE trust_tiers
SET 
    trust_delta_excellent = 0.022,  -- was 0.22
    trust_delta_good = 0.016,       -- was 0.16
    trust_delta_adequate = 0.010,   -- was 0.10
    trust_delta_poor = -0.012,      -- was -0.12
    updated_at = NOW()
WHERE tier_name = 'cautious';

-- OPENING TIER (0.5-0.75): Faster trust building
UPDATE trust_tiers
SET 
    trust_delta_excellent = 0.025,  -- was 0.25
    trust_delta_good = 0.018,       -- was 0.18
    trust_delta_adequate = 0.012,   -- was 0.12
    trust_delta_poor = -0.010,      -- was -0.10
    updated_at = NOW()
WHERE tier_name = 'opening';

-- TRUSTING TIER (0.75-1.0): Fastest trust growth, hardest to lose
UPDATE trust_tiers
SET 
    trust_delta_excellent = 0.030,  -- was 0.30
    trust_delta_good = 0.022,       -- was 0.22
    trust_delta_adequate = 0.015,   -- was 0.15
    trust_delta_poor = -0.008,      -- was -0.08
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
FROM trust_tiers
ORDER BY min_threshold;

-- =============================================================================
-- EXPECTED PROGRESSION (with MI-adherent excellent interactions)
-- =============================================================================
-- Vic starts at 0.25 (defensive tier)
-- 
-- Turn 5:  0.25 + (4 * 0.020) = 0.33 (moves to cautious)
-- Turn 10: 0.33 + (5 * 0.022) = 0.44 (still cautious)
-- Turn 15: 0.44 + (5 * 0.022) = 0.55 (moves to opening)
-- Turn 20: 0.55 + (5 * 0.025) = 0.675 (still opening)
-- Turn 25: 0.675 + (5 * 0.025) = 0.80 (moves to trusting)
-- Turn 30: 0.80 + (5 * 0.030) = 0.95 (fully trusting)
--
-- Mary starts at 0.65 (opening tier)
--
-- Turn 3:  0.65 + (2 * 0.025) = 0.70 (still opening)
-- Turn 6:  0.70 + (3 * 0.025) = 0.775 (moves to trusting)
-- Turn 10: 0.775 + (4 * 0.030) = 0.895 (deep trust)
-- Turn 15: 0.895 + (5 * 0.030) = 1.00 (maximum trust, ready to commit)
--
-- This provides realistic, gradual progression matching MI training expectations

-- =============================================================================
-- ROLLBACK SCRIPT (if needed)
-- =============================================================================
-- UPDATE trust_tiers SET trust_delta_excellent = 0.20, trust_delta_good = 0.15, trust_delta_adequate = 0.08, trust_delta_poor = -0.15 WHERE tier_name = 'defensive';
-- UPDATE trust_tiers SET trust_delta_excellent = 0.22, trust_delta_good = 0.16, trust_delta_adequate = 0.10, trust_delta_poor = -0.12 WHERE tier_name = 'cautious';
-- UPDATE trust_tiers SET trust_delta_excellent = 0.25, trust_delta_good = 0.18, trust_delta_adequate = 0.12, trust_delta_poor = -0.10 WHERE tier_name = 'opening';
-- UPDATE trust_tiers SET trust_delta_excellent = 0.30, trust_delta_good = 0.22, trust_delta_adequate = 0.15, trust_delta_poor = -0.08 WHERE tier_name = 'trusting';

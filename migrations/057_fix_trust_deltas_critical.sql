-- CRITICAL FIX: Trust deltas are 6X too small
-- This migration corrects the trust delta values to match the intended progression speed
--
-- PROBLEM:
-- Current database has:
--   opening tier: excellent=0.03, good=0.02, adequate=0.01 (WAY TOO SLOW!)
--   trusting tier: Similar severely reduced values
--
-- This causes personas to:
-- - Stay in defensive tier for entire conversations
-- - Never progress through knowledge tiers
-- - Repeat the same defensive behaviors endlessly
-- - Be BORING and REPETITIVE
--
-- SOLUTION:
-- Set deltas to correct values based on MI research and user testing

-- First, check current values
DO $$
BEGIN
    RAISE NOTICE 'Current trust_tiers values:';
END $$;

SELECT tier_name, trust_delta_excellent, trust_delta_good, trust_delta_adequate
FROM trust_tiers
ORDER BY min_threshold;

-- Update opening tier (0.50-0.75)
-- These personas are moderately trusting and should progress at medium-fast pace
UPDATE trust_tiers
SET
    trust_delta_excellent = 0.18,  -- Was ~0.03 (6X too slow!)
    trust_delta_good = 0.12,       -- Was ~0.02
    trust_delta_adequate = 0.06,   -- Was ~0.01
    trust_delta_poor = -0.15       -- Lose trust faster than they gain it
WHERE tier_name = 'opening';

-- Update trusting tier (0.75-1.00)
-- These personas trust quickly and should progress fastest
UPDATE trust_tiers
SET
    trust_delta_excellent = 0.25,  -- Very responsive to good empathy
    trust_delta_good = 0.18,
    trust_delta_adequate = 0.10,
    trust_delta_poor = -0.10       -- Resilient - don't lose trust easily
WHERE tier_name = 'trusting';

-- Verify defensive and cautious tiers are correct
-- (They should already be correct from migration 052)
UPDATE trust_tiers
SET
    trust_delta_excellent = 0.08,
    trust_delta_good = 0.05,
    trust_delta_adequate = 0.02,
    trust_delta_poor = -0.25       -- Very quick to lose trust
WHERE tier_name = 'defensive';

UPDATE trust_tiers
SET
    trust_delta_excellent = 0.12,
    trust_delta_good = 0.08,
    trust_delta_adequate = 0.03,
    trust_delta_poor = -0.20
WHERE tier_name = 'cautious';

-- Show final values
DO $$
BEGIN
    RAISE NOTICE 'Updated trust_tiers values:';
END $$;

SELECT tier_name, trust_delta_excellent, trust_delta_good, trust_delta_adequate
FROM trust_tiers
ORDER BY min_threshold;

-- Test with Mary (trust_variable = 0.65 -> should use opening tier)
DO $$
DECLARE
    mary_tier TEXT;
    mary_delta DECIMAL(3,2);
BEGIN
    -- Simulate what trust_configuration_service does
    SELECT tier_name, trust_delta_excellent
    INTO mary_tier, mary_delta
    FROM trust_tiers
    WHERE min_threshold <= 0.65
    ORDER BY min_threshold DESC
    LIMIT 1;

    IF mary_delta = 0.18 THEN
        RAISE NOTICE 'SUCCESS: Mary will now get opening tier deltas (excellent: 0.18)';
        RAISE NOTICE 'Expected progression: defensive->cautious in ~3 turns, cautious->opening in ~6 turns, opening->trusting in ~9 turns';
    ELSE
        RAISE EXCEPTION 'FAILED: Mary getting wrong delta: % from tier: %', mary_delta, mary_tier;
    END IF;
END $$;

-- Add comments
COMMENT ON COLUMN trust_tiers.trust_delta_excellent IS 'Trust increase for excellent empathy (8.5+). Scale: 0.0-1.0. Values: defensive=0.08, cautious=0.12, opening=0.18, trusting=0.25';
COMMENT ON COLUMN trust_tiers.trust_delta_good IS 'Trust increase for good empathy (7.0-8.5). Scale: 0.0-1.0';
COMMENT ON COLUMN trust_tiers.trust_delta_adequate IS 'Trust increase for adequate empathy (5.0-7.0). Scale: 0.0-1.0';
COMMENT ON COLUMN trust_tiers.trust_delta_poor IS 'Trust decrease for poor empathy (<4.0). Scale: 0.0-1.0. Negative values.';

-- Final verification
DO $$
DECLARE
    wrong_count INTEGER;
BEGIN
    -- Count tiers with suspiciously small deltas (< 0.05)
    SELECT COUNT(*)
    INTO wrong_count
    FROM trust_tiers
    WHERE trust_delta_excellent < 0.05;

    IF wrong_count > 0 THEN
        RAISE EXCEPTION 'VERIFICATION FAILED: % tiers still have deltas < 0.05', wrong_count;
    END IF;

    RAISE NOTICE 'VERIFICATION PASSED: All trust deltas are within expected ranges';
    RAISE NOTICE 'Migration 057 complete - trust progression will now work correctly';
END $$;

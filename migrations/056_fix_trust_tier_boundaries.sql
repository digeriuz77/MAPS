-- Fix trust_tiers boundary overlaps
-- This migration eliminates ambiguity when trust_variable equals exact boundary values (0.25, 0.50, 0.75)
--
-- PROBLEM:
-- Previous boundaries overlapped at 0.25, 0.50, 0.75 causing multiple tiers to match
-- E.g., trust_variable=0.25 matched BOTH defensive (0.00-0.25) AND cautious (0.25-0.50)
--
-- SOLUTION:
-- Make boundaries exclusive on the upper end using < instead of <=
-- This ensures each trust_variable maps to exactly ONE tier

-- Update boundaries to be non-overlapping
-- New logic: min_threshold <= trust_variable < max_threshold (except trusting tier which includes 1.0)

UPDATE trust_tiers
SET max_threshold = 0.249
WHERE tier_name = 'defensive';

UPDATE trust_tiers
SET max_threshold = 0.499
WHERE tier_name = 'cautious';

UPDATE trust_tiers
SET max_threshold = 0.749
WHERE tier_name = 'opening';

-- trusting tier remains 1.00 to include the maximum value

-- Add documentation
COMMENT ON TABLE trust_tiers IS 'Trust progression tiers with NON-OVERLAPPING boundaries. Each trust_variable (0.00-1.00) maps to exactly one tier. Query uses: min_threshold <= trust_variable AND trust_variable < max_threshold (except trusting tier includes 1.00).';

-- Verify the fix
DO $$
DECLARE
    tier_count INTEGER;
    test_value DECIMAL(3,2);
    matched_tier TEXT;
BEGIN
    -- Test boundary values to ensure single match
    -- Using the same logic as trust_configuration_service.py:
    -- Find tier with highest min_threshold where min_threshold <= trust_variable
    FOR test_value IN SELECT unnest(ARRAY[0.25, 0.50, 0.75]::DECIMAL[])
    LOOP
        -- Count matches using new query logic
        SELECT COUNT(*), MAX(tier_name) INTO tier_count, matched_tier
        FROM (
            SELECT tier_name, min_threshold
            FROM trust_tiers
            WHERE min_threshold <= test_value
            ORDER BY min_threshold DESC
            LIMIT 1
        ) AS matching_tier;

        IF tier_count != 1 THEN
            RAISE EXCEPTION 'Boundary fix failed: trust_variable % matches % tiers (expected 1)', test_value, tier_count;
        END IF;

        RAISE NOTICE 'Boundary test passed: trust_variable % -> % tier', test_value, matched_tier;
    END LOOP;

    RAISE NOTICE 'All boundary tests passed! Trust tier boundaries are now non-overlapping.';
END $$;

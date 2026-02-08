-- 0013_fix_scenario_attempts_not_null.sql
-- Fix NOT NULL constraints on persona state columns for scenario_attempts table

-- Make initial_persona_state nullable with default
ALTER TABLE scenario_attempts
    ALTER COLUMN initial_persona_state DROP NOT NULL;

ALTER TABLE scenario_attempts
    ALTER COLUMN initial_persona_state
    SET DEFAULT '{"trust_level": 3, "openness_level": 2, "resistance_active": true}'::jsonb;

-- Check if current_persona_state exists and fix it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'scenario_attempts'
        AND column_name = 'current_persona_state'
        AND is_nullable = 'NO'
    ) THEN
        ALTER TABLE scenario_attempts
            ALTER COLUMN current_persona_state DROP NOT NULL;

        ALTER TABLE scenario_attempts
            ALTER COLUMN current_persona_state
            SET DEFAULT '{"trust_level": 3, "openness_level": 2, "resistance_active": true}'::jsonb;
    END IF;
END $$;

-- Verification query
SELECT
    table_name,
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'scenario_attempts'
    AND column_name LIKE '%persona_state%'
ORDER BY column_name;

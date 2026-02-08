-- 0013_fix_all_not_null_constraints.sql
-- Fix all NOT NULL constraints on persona state columns for attempts tables

-- =====================================================
-- scenario_attempts table fixes
-- =====================================================

-- Make all persona state columns nullable with defaults
ALTER TABLE scenario_attempts
    ALTER COLUMN initial_persona_state DROP NOT NULL,
    ALTER COLUMN initial_persona_state
    SET DEFAULT '{"trust_level": 3, "openness_level": 2, "resistance_active": true}'::jsonb;

-- Check if current_persona_state exists and fix it
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'scenario_attempts'
        AND column_name = 'current_persona_state'
    ) THEN
        ALTER TABLE scenario_attempts
            ALTER COLUMN current_persona_state DROP NOT NULL;
        ALTER TABLE scenario_attempts
            ALTER COLUMN current_persona_state
            SET DEFAULT '{"trust_level": 3, "openness_level": 2, "resistance_active": true}'::jsonb;
    END IF;
END $$;

-- =====================================================
-- mi_practice_attempts table fixes
-- =====================================================

-- Check if table exists first
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'mi_practice_attempts') THEN
        -- Make initial_persona_state nullable with default
        ALTER TABLE mi_practice_attempts
            ALTER COLUMN initial_persona_state DROP NOT NULL;

        ALTER TABLE mi_practice_attempts
            ALTER COLUMN initial_persona_state
            SET DEFAULT '{"rapport": 50, "resistance": 5}'::jsonb;

        -- Check if current_persona_state exists
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'mi_practice_attempts'
            AND column_name = 'current_persona_state'
        ) THEN
            ALTER TABLE mi_practice_attempts
                ALTER COLUMN current_persona_state DROP NOT NULL;

            ALTER TABLE mi_practice_attempts
                ALTER COLUMN current_persona_state
                SET DEFAULT '{"rapport": 50, "resistance": 5}'::jsonb;
        END IF;
    END IF;
END $$;

-- =====================================================
-- Verification query
-- =====================================================
SELECT
    table_name,
    column_name,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name IN ('scenario_attempts', 'mi_practice_attempts')
    AND column_name LIKE '%persona_state%'
ORDER BY table_name, column_name;

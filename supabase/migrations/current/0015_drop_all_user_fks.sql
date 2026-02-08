-- 0015_drop_all_user_fks.sql
-- Drop ALL foreign key constraints on user_id columns for demo purposes

-- First, let's see what constraints exist
DO $$
DECLARE
    r RECORD;
BEGIN
    -- Drop all foreign key constraints on scenario_attempts
    FOR r IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid::regclass::text = 'scenario_attempts'
        AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE scenario_attempts DROP CONSTRAINT IF EXISTS %I', r.conname);
    END LOOP;

    -- Drop all foreign key constraints on mi_practice_attempts
    FOR r IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid::regclass::text = 'mi_practice_attempts'
        AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE mi_practice_attempts DROP CONSTRAINT IF EXISTS %I', r.conname);
    END LOOP;

    -- Drop all foreign key constraints on mi_user_progress
    FOR r IN
        SELECT conname
        FROM pg_constraint
        WHERE conrelid::regclass::text = 'mi_user_progress'
        AND contype = 'f'
    LOOP
        EXECUTE format('ALTER TABLE mi_user_progress DROP CONSTRAINT IF EXISTS %I', r.conname);
    END LOOP;
END $$;

-- Verification - should return no rows if successful
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name
FROM pg_constraint
WHERE conrelid::regclass::text IN ('scenario_attempts', 'mi_practice_attempts', 'mi_user_progress')
    AND contype = 'f';

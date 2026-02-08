-- 0014_remove_user_fk_constraints.sql
-- Remove foreign key constraints to auth.users for demo/development purposes
-- This allows creating attempts without requiring users in auth.users table

-- Remove foreign key from scenario_attempts
ALTER TABLE scenario_attempts
    DROP CONSTRAINT IF EXISTS fk_user;

-- Remove foreign key from scenario_attempts (alternate name)
ALTER TABLE scenario_attempts
    DROP CONSTRAINT IF EXISTS scenario_attempts_user_id_fkey;

-- Remove foreign key from mi_practice_attempts
ALTER TABLE mi_practice_attempts
    DROP CONSTRAINT IF EXISTS mi_practice_attempts_user_id_fkey;

-- Remove foreign key from mi_user_progress
ALTER TABLE mi_user_progress
    DROP CONSTRAINT IF EXISTS mi_user_progress_user_id_fkey;

-- Verification
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name
FROM pg_constraint
WHERE conrelid::regclass::text IN ('scenario_attempts', 'mi_practice_attempts', 'mi_user_progress')
    AND contype = 'f';

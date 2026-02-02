-- 0006_fix_scenarios_rls.sql
-- Fix RLS policies for Scenarios to ensure frontend access

-- 1. Enable RLS on scenarios table
ALTER TABLE scenarios ENABLE ROW LEVEL SECURITY;

-- 2. Drop existing policy if it exists (to avoid error)
DROP POLICY IF EXISTS "Scenarios readable by authenticated users" ON scenarios;

-- 3. Create Policy for Authenticated Users
CREATE POLICY "Scenarios readable by authenticated users"
    ON scenarios FOR SELECT TO authenticated USING (is_active = TRUE);

-- 4. Ensure Permissions (Grants) are set correctly
GRANT SELECT ON scenarios TO authenticated;
GRANT SELECT ON scenarios TO anon;
GRANT SELECT ON scenarios TO service_role;

GRANT SELECT ON mi_practice_modules TO authenticated;
GRANT SELECT ON mi_practice_modules TO anon;
GRANT SELECT ON mi_practice_modules TO service_role;

-- 5. Force update of updated_at to ensure caches break if any
UPDATE scenarios SET updated_at = NOW() WHERE is_active = TRUE;

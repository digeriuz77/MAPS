-- 0011_fix_rls_policies.sql
-- Fix RLS policies for attempts tables - ensure RLS is enabled and policies are correct

-- Enable RLS on scenario_attempts if not already enabled
ALTER TABLE scenario_attempts ENABLE ROW LEVEL SECURITY;

-- Enable RLS on mi_practice_attempts if not already enabled
ALTER TABLE mi_practice_attempts ENABLE ROW LEVEL SECURITY;

-- Remove ALL existing policies on scenario_attempts first (to avoid conflicts)
DROP POLICY IF EXISTS "Anon users can create attempts" ON scenario_attempts;
DROP POLICY IF EXISTS "Anon users can update attempts" ON scenario_attempts;
DROP POLICY IF EXISTS "Anon users can view own attempts" ON scenario_attempts;
DROP POLICY IF EXISTS "Users can view own attempts" ON scenario_attempts;
DROP POLICY IF EXISTS "Users can update own attempts" ON scenario_attempts;
DROP POLICY IF EXISTS "Users can insert attempts" ON scenario_attempts;

-- Remove ALL existing policies on mi_practice_attempts first
DROP POLICY IF EXISTS "Anon users can create MI attempts" ON mi_practice_attempts;
DROP POLICY IF EXISTS "Anon users can update MI attempts" ON mi_practice_attempts;
DROP POLICY IF EXISTS "Anon users can view own attempts" ON mi_practice_attempts;
DROP POLICY IF EXISTS "Users can view own attempts" ON mi_practice_attempts;
DROP POLICY IF EXISTS "Users can update own attempts" ON mi_practice_attempts;
DROP POLICY IF EXISTS "Users can insert attempts" ON mi_practice_attempts;

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon;
GRANT ALL ON scenario_attempts TO anon;
GRANT ALL ON mi_practice_attempts TO anon;

-- CREATE fresh policies for scenario_attempts
CREATE POLICY "Enable all access for anon users on scenario_attempts"
    ON scenario_attempts FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- CREATE fresh policies for mi_practice_attempts
CREATE POLICY "Enable all access for anon users on mi_practice_attempts"
    ON mi_practice_attempts FOR ALL
    TO anon
    USING (true)
    WITH CHECK (true);

-- Verify RLS status
SELECT
    tablename,
    rowsecurity as rls_enabled
FROM pg_tables
WHERE schemaname = 'public'
    AND tablename IN ('scenario_attempts', 'mi_practice_attempts');

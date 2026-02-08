-- 0010_add_anon_insert_to_attempts.sql
-- Add anon INSERT access to attempts tables for public demo functionality

-- Grant INSERT on scenario_attempts to anon
GRANT INSERT ON scenario_attempts TO anon;

-- Drop existing policy if exists
DROP POLICY IF EXISTS "Anon users can create attempts" ON scenario_attempts;

-- Create policy for anon users to insert attempts
CREATE POLICY "Anon users can create attempts"
    ON scenario_attempts FOR INSERT TO anon
    WITH CHECK (true);  -- Allow anon for demo purposes

-- Grant INSERT on mi_practice_attempts to anon
GRANT INSERT ON mi_practice_attempts TO anon;

-- Drop existing policy if exists
DROP POLICY IF EXISTS "Anon users can create MI attempts" ON mi_practice_attempts;

-- Create policy for anon users to insert MI attempts
CREATE POLICY "Anon users can create MI attempts"
    ON mi_practice_attempts FOR INSERT TO anon
    WITH CHECK (true);  -- Allow anon for demo purposes

-- Also add UPDATE permissions for progress tracking
GRANT UPDATE ON scenario_attempts TO anon;

DROP POLICY IF EXISTS "Anon users can update attempts" ON scenario_attempts;

CREATE POLICY "Anon users can update attempts"
    ON scenario_attempts FOR UPDATE TO anon
    USING (true);

GRANT UPDATE ON mi_practice_attempts TO anon;

DROP POLICY IF EXISTS "Anon users can update MI attempts" ON mi_practice_attempts;

CREATE POLICY "Anon users can update MI attempts"
    ON mi_practice_attempts FOR UPDATE TO anon
    USING (true);

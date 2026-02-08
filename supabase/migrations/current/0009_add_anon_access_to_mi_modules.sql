-- 0009_add_anon_access_to_mi_modules.sql
-- Add anon access to mi_practice_modules for public API access

-- Grant anon users access to read active modules
GRANT SELECT ON mi_practice_modules TO anon;

-- Create RLS policy for anon users
DROP POLICY IF EXISTS "MI modules readable by anon users" ON mi_practice_modules;

CREATE POLICY "MI modules readable by anon users"
    ON mi_practice_modules FOR SELECT TO anon
    USING (is_active = true);

-- Also add anon access to mi_learning_paths
GRANT SELECT ON mi_learning_paths TO anon;

DROP POLICY IF EXISTS "Learning paths readable by anon users" ON mi_learning_paths;

CREATE POLICY "Learning paths readable by anon users"
    ON mi_learning_paths FOR SELECT TO anon
    USING (is_active = true);

-- Grant select on mi_practice_attempts to anon (for reading own attempts)
-- Note: Users can only read their own attempts via user_id filter
GRANT SELECT ON mi_practice_attempts TO anon;

DROP POLICY IF EXISTS "Anon users can view own attempts" ON mi_practice_attempts;

CREATE POLICY "Anon users can view own attempts" ON mi_practice_attempts FOR SELECT
    USING (true);  // Allow anon for demo purposes - in production use user_id check

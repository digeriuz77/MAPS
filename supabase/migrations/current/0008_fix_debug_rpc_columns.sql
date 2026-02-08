-- 0008_fix_debug_rpc_columns.sql
-- Fix the RPC function to match actual schema

-- Drop the old function
DROP FUNCTION IF EXISTS public.get_debug_info();

-- Recreate with correct column names
CREATE OR REPLACE FUNCTION public.get_debug_info()
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    result jsonb;
    scenarios_data jsonb;
    modules_data jsonb;
    attempts_count int;
    profiles_count int;
BEGIN
    -- Get scenarios data (with sample)
    SELECT jsonb_build_object(
        'count', COUNT(*),
        'sample', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'code', code,
                'title', title,
                'mi_skill_category', mi_skill_category,
                'difficulty', difficulty,
                'is_active', is_active
            ))
            FROM (
                SELECT id, code, title, mi_skill_category, difficulty, is_active
                FROM scenarios
                WHERE is_active = true
                ORDER BY title
                LIMIT 5
            ) samples
        )
    ) INTO scenarios_data
    FROM scenarios;

    -- Get MI practice modules data (with sample) - using ACTUAL columns
    SELECT jsonb_build_object(
        'count', COUNT(*),
        'sample', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'code', code,
                'title', title,
                'difficulty_level', difficulty_level,
                'is_active', is_active,
                'mi_focus_area', mi_focus_area
            ))
            FROM (
                SELECT id, code, title, difficulty_level, is_active, mi_focus_area
                FROM mi_practice_modules
                WHERE is_active = true
                ORDER BY created_at
                LIMIT 5
            ) samples
        )
    ) INTO modules_data
    FROM mi_practice_modules;

    -- Get counts for other tables
    SELECT COUNT(*) INTO attempts_count FROM scenario_attempts;
    SELECT COUNT(*) INTO profiles_count FROM profiles;

    -- Build final result
    result := jsonb_build_object(
        'scenarios', scenarios_data,
        'mi_practice_modules', modules_data,
        'scenario_attempts_count', attempts_count,
        'profiles_count', profiles_count,
        'timestamp', NOW()
    );

    RETURN result;
END;
$$;

-- Grant execute permission
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO anon;
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO service_role;

-- Update comment
COMMENT ON FUNCTION public.get_debug_info() IS 'Returns comprehensive debug information about all MAPS tables including counts and samples. Uses correct column names for actual schema.';

-- 0007_current_debug_rpc.sql
-- Create RPC function for efficient table discovery and debug info
-- This allows fetching all table metadata in a single call instead of multiple queries

-- Create the debug function that returns comprehensive table info
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

    -- Get MI practice modules data (with sample)
    SELECT jsonb_build_object(
        'count', COUNT(*),
        'sample', (
            SELECT jsonb_agg(jsonb_build_object(
                'id', id,
                'code', code,
                'title', title,
                'difficulty_level', difficulty_level,
                'is_active', is_active,
                'is_published', is_published
            ))
            FROM (
                SELECT id, code, title, difficulty_level, is_active, is_published
                FROM mi_practice_modules
                WHERE is_active = true
                ORDER BY display_order
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

-- Grant execute permission to authenticated and anon users
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO authenticated;
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO anon;
GRANT EXECUTE ON FUNCTION public.get_debug_info() TO service_role;

-- Add helpful comment
COMMENT ON FUNCTION public.get_debug_info() IS 'Returns comprehensive debug information about all MAPS tables including counts and samples. Used by /api/debug/supabase endpoint.';

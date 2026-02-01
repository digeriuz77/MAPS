-- ============================================
-- Content Classification Verification Queries
-- Phase 6: Testing & Verification
-- ============================================

-- 1. Check all content types in database
-- Expected: shared, customer_facing, colleague_facing
SELECT 
    content_type,
    COUNT(*) as module_count
FROM mi_practice_modules
WHERE is_active = TRUE
GROUP BY content_type
ORDER BY content_type;

-- 2. List all modules with their content classification
SELECT 
    code,
    title,
    content_type,
    difficulty_level,
    mi_focus_area,
    estimated_minutes
FROM mi_practice_modules
WHERE is_active = TRUE
ORDER BY content_type, difficulty_level, title;

-- 3. Verify SHARED modules use neutral language
-- Check that persona roles don't contain customer/colleague terms
SELECT 
    code,
    title,
    persona_config->>'role' as persona_role
FROM mi_practice_modules
WHERE content_type = 'shared'
    AND is_active = TRUE
ORDER BY code;

-- 4. Verify CUSTOMER-FACING modules have financial context
SELECT 
    code,
    title,
    persona_config->>'role' as persona_role,
    learning_objective
FROM mi_practice_modules
WHERE content_type = 'customer_facing'
    AND is_active = TRUE
ORDER BY code;

-- 5. Verify COLLEAGUE-FACING modules have workplace context
SELECT 
    code,
    title,
    persona_config->>'role' as persona_role,
    learning_objective
FROM mi_practice_modules
WHERE content_type = 'colleague_facing'
    AND is_active = TRUE
ORDER BY code;

-- 6. Check MAPS competency alignment by content type
SELECT 
    content_type,
    unnest(target_competencies) as competency,
    COUNT(*) as module_count
FROM mi_practice_modules
WHERE is_active = TRUE
GROUP BY content_type, unnest(target_competencies)
ORDER BY content_type, competency;

-- 7. Verify dialogue structure exists for all modules
SELECT 
    code,
    title,
    CASE 
        WHEN dialogue_structure IS NOT NULL 
             AND dialogue_structure->>'start_node_id' IS NOT NULL 
        THEN 'Valid'
        ELSE 'Invalid/Missing'
    END as dialogue_status
FROM mi_practice_modules
WHERE is_active = TRUE
ORDER BY code;

-- 8. Check maps_rubric exists for all modules
SELECT 
    code,
    title,
    CASE 
        WHEN maps_rubric IS NOT NULL 
             AND maps_rubric->>'dimensions' IS NOT NULL 
        THEN 'Valid'
        ELSE 'Invalid/Missing'
    END as rubric_status
FROM mi_practice_modules
WHERE is_active = TRUE
ORDER BY code;

-- 9. Verify learning paths have content_type
SELECT 
    code,
    title,
    content_type
FROM mi_learning_paths
WHERE is_active = TRUE
ORDER BY content_type, code;

-- 10. Count modules by difficulty and content type
SELECT 
    content_type,
    difficulty_level,
    COUNT(*) as count
FROM mi_practice_modules
WHERE is_active = TRUE
GROUP BY content_type, difficulty_level
ORDER BY content_type, difficulty_level;

-- 11. Check for modules missing required fields
SELECT 
    code,
    title,
    CASE WHEN learning_objective IS NULL THEN 'Missing learning_objective' END as missing_field
FROM mi_practice_modules
WHERE is_active = TRUE
    AND (learning_objective IS NULL 
         OR scenario_context IS NULL 
         OR persona_config IS NULL 
         OR dialogue_structure IS NULL)
ORDER BY code;

-- 12. Verify content_type column exists and has valid values
-- This will fail if content_type column doesn't exist
SELECT 
    DISTINCT content_type
FROM mi_practice_modules
WHERE content_type IN ('shared', 'customer_facing', 'colleague_facing')
    OR content_type IS NULL;

-- 13. Sample query for frontend filtering test
-- Simulates what the API returns when filtering by content_type
SELECT 
    id,
    code,
    title,
    content_type,
    mi_focus_area,
    difficulty_level,
    estimated_minutes,
    learning_objective,
    target_competencies
FROM mi_practice_modules
WHERE is_active = TRUE
    AND content_type = 'shared'  -- Change to test different filters
ORDER BY difficulty_level, title
LIMIT 10;

-- 14. Verify module count matches expected totals
-- Expected: 12 SHARED, 6 CUSTOMER-FACING, 5 COLLEAGUE-FACING
WITH counts AS (
    SELECT 
        content_type,
        COUNT(*) as actual_count
    FROM mi_practice_modules
    WHERE is_active = TRUE
    GROUP BY content_type
)
SELECT 
    content_type,
    actual_count,
    CASE content_type
        WHEN 'shared' THEN 12
        WHEN 'customer_facing' THEN 6
        WHEN 'colleague_facing' THEN 5
    END as expected_count,
    CASE 
        WHEN actual_count = CASE content_type
            WHEN 'shared' THEN 12
            WHEN 'customer_facing' THEN 6
            WHEN 'colleague_facing' THEN 5
        END THEN '✓ Match'
        ELSE '✗ Mismatch'
    END as status
FROM counts
ORDER BY content_type;

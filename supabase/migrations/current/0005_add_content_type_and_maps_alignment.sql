-- 0005_add_content_type_and_maps_alignment.sql
-- Migration to add content_type classification and MAPS framework alignment
-- This migration supports the new MAPS-aligned MI Practice module classification system

-- ============================================
-- 1. ADD CONTENT_TYPE COLUMN
-- ============================================
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) NOT NULL DEFAULT 'shared';

-- Add check constraint to ensure only valid values
ALTER TABLE mi_practice_modules
    ADD CONSTRAINT content_type_check
    CHECK (content_type IN ('shared', 'customer_facing', 'colleague_facing'));

-- Create index for content type filtering
CREATE INDEX IF NOT EXISTS idx_mi_modules_content_type
    ON mi_practice_modules(content_type);

-- ============================================
-- 2. ADD MAPS_FRAMEWORK_ALIGNMENT COLUMN
-- ============================================
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS maps_framework_alignment JSONB;

COMMENT ON COLUMN mi_practice_modules.maps_framework_alignment IS 'JSONB field containing MAPS Money Guidance Competency Framework alignment details (framework_name, sections, tier_relevance, domains)';

-- ============================================
-- 3. UPDATE EXISTING ROWS BASED ON MODULE CODES
-- ============================================

-- SHARED modules (Core Skills - neutral language, universal application)
UPDATE mi_practice_modules
SET content_type = 'shared'
WHERE code LIKE 'shared-%';

-- CUSTOMER_FACING modules (MAPS financial scenarios - debt, budgeting, pensions)
UPDATE mi_practice_modules
SET content_type = 'customer_facing'
WHERE code LIKE 'customer-%';

-- COLLEAGUE_FACING modules (MAPS workplace scenarios - performance, coaching, team dynamics)
UPDATE mi_practice_modules
SET content_type = 'colleague_facing'
WHERE code LIKE 'colleague-%';

-- ============================================
-- 4. UPDATE mi_learning_paths WITH ADDITIONAL FIELDS
-- ============================================

-- Add code column if it doesn't exist (for consistency with modules table)
ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS code VARCHAR(50) UNIQUE;

-- Add pathway_data JSONB column for structured path information
ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS pathway_data JSONB;

COMMENT ON COLUMN mi_practice_modules.content_type IS 'Module classification: shared (core skills), customer_facing (MAPS financial scenarios), colleague_facing (MAPS workplace scenarios)';
COMMENT ON TABLE mi_learning_paths IS 'Updated to support structured pathway_data configuration';

-- ============================================
-- 5. CREATE OR REPLACE VIEW FOR MODULE LISTS WITH CONTENT TYPE
-- ============================================

CREATE OR REPLACE VIEW mi_modules_with_content_type AS
SELECT
    id,
    code,
    title,
    content_type,
    mi_focus_area,
    difficulty_level,
    estimated_minutes,
    learning_objective,
    target_competencies,
    maps_rubric,
    maps_framework_alignment,
    is_active,
    created_at,
    updated_at
FROM mi_practice_modules
WHERE is_active = TRUE;

COMMENT ON VIEW mi_modules_with_content_type IS 'View of active MI practice modules with content type classification for easy filtering';

-- ============================================
-- 6. VERIFICATION QUERIES (for testing)
-- ============================================

-- Expected content type distribution after migration:
-- SHARED: 12 modules
-- CUSTOMER_FACING: 5 modules
-- COLLEAGUE_FACING: 3 modules
-- TOTAL: 20 modules

-- Verify content type distribution:
-- SELECT content_type, COUNT(*) as count
-- FROM mi_practice_modules
-- WHERE is_active = TRUE
-- GROUP BY content_type
-- ORDER BY content_type;

-- Verify all modules have content_type:
-- SELECT COUNT(*) as modules_without_content_type
-- FROM mi_practice_modules
-- WHERE content_type IS NULL;

-- ============================================
-- END OF MIGRATION
-- ============================================

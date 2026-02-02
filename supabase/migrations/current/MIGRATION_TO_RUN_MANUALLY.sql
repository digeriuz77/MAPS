-- ============================================
-- MAPS MI Practice Platform - Content Type Migration
-- Run this in Supabase SQL Editor
-- ============================================

-- Step 1: Add content_type column
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) NOT NULL DEFAULT 'shared';

-- Step 2: Add content type constraint
ALTER TABLE mi_practice_modules
    DROP CONSTRAINT IF EXISTS content_type_check;

ALTER TABLE mi_practice_modules
    ADD CONSTRAINT content_type_check
    CHECK (content_type IN ('shared', 'customer_facing', 'colleague_facing'));

-- Step 3: Create index for filtering
CREATE INDEX IF NOT EXISTS idx_mi_modules_content_type
    ON mi_practice_modules(content_type);

-- Step 4: Add MAPS framework alignment column
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS maps_framework_alignment JSONB;

-- Step 5: Add code column to learning_paths
ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS code VARCHAR(50) UNIQUE;

-- Step 6: Add pathway_data column to learning_paths
ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS pathway_data JSONB;

-- Step 7: Verify migration
SELECT 'Migration complete!' as status;

-- Verify content_type column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'mi_practice_modules'
  AND column_name IN ('content_type', 'maps_framework_alignment');

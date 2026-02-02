#!/usr/bin/env python3
"""
Supabase Migration Helper

Since Supabase REST API cannot execute DDL (ALTER TABLE, etc.) directly,
this script provides:
1. Direct link to SQL Editor with pre-formatted migration
2. Option to copy migration SQL to clipboard
"""

import os
import sys
import webbrowser
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
project_ref = SUPABASE_URL.split('https://')[1].split('.')[0]

sql_editor_url = f"https://supabase.com/dashboard/project/{project_ref}/sql"

migration_sql = """-- ============================================
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
"""

print("="*70)
print("SUPABASE MIGRATION HELPER")
print("="*70)
print()
print(f"Your Supabase Project: {project_ref}")
print(f"SQL Editor URL: {sql_editor_url}")
print()
print("STEPS TO COMPLETE THE MIGRATION:")
print()
print("1. Opening SQL Editor in your browser...")
print("2. Copy and paste the SQL below into the editor")
print("3. Click 'Run' to execute the migration")
print()

# Open SQL Editor in browser
webbrowser.open(sql_editor_url)

# Save SQL to file for easy copying
sql_file = Path(__file__).parent.parent / "supabase" / "migrations" / "current" / "MIGRATION_TO_RUN_MANUALLY.sql"
sql_file.write_text(migration_sql)

print(f"SQL saved to: {sql_file}")
print()
print("-" * 70)
print("MIGRATION SQL (copy this):")
print("-" * 70)
print(migration_sql)
print("-" * 70)
print()
print("After running the migration, run:")
print("  python scripts/seed_from_json.py --seed")

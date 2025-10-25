-- ===================================================================
-- SCHEMA CHECK QUERIES
-- Run these first to see what columns exist in each table
-- ===================================================================

-- Check what columns exist in each table
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'conversations'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'mi_analysis'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'persona_responses'
ORDER BY ordinal_position;

SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'quality_patterns'
ORDER BY ordinal_position;

-- Check if legacy tables exist
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('personas', 'messages', 'users', 'sessions');
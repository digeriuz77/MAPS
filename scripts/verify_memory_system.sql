-- Diagnostic: Verify Dynamic Memory System
-- Purpose: Check if conversation_memories table exists and test memory formation
-- Run AFTER migration 033

-- Step 1: Verify table exists
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_name = 'conversation_memories'
        ) 
        THEN '✓ conversation_memories table EXISTS'
        ELSE '✗ conversation_memories table MISSING - Run migration 033!'
    END AS table_status;

-- Step 2: Check table structure matches code expectations
SELECT 
    column_name,
    data_type,
    is_nullable,
    CASE 
        WHEN column_name = 'session_id' AND data_type = 'uuid' THEN '✓'
        WHEN column_name = 'key_insights' AND data_type = 'text' THEN '✓'
        WHEN column_name = 'importance_score' AND data_type = 'numeric' THEN '✓'
        WHEN column_name = 'created_at' AND data_type = 'timestamp with time zone' THEN '✓'
        ELSE '?'
    END AS matches_code
FROM information_schema.columns
WHERE table_name = 'conversation_memories'
ORDER BY ordinal_position;

-- Step 3: Check foreign key constraint to conversations table
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.table_name = 'conversation_memories' 
    AND tc.constraint_type = 'FOREIGN KEY';

-- Step 4: Verify indexes for performance
SELECT 
    indexname,
    indexdef
FROM pg_indexes
WHERE tablename = 'conversation_memories';

-- Step 5: Count existing memories (should be 0 immediately after migration)
SELECT 
    COUNT(*) as total_memories,
    COUNT(DISTINCT session_id) as unique_conversations
FROM conversation_memories;

-- Step 6: Test insert (to verify table is writable)
DO $$
DECLARE
    test_conversation_id UUID;
BEGIN
    -- Get a real conversation ID from the database
    SELECT id INTO test_conversation_id
    FROM conversations
    LIMIT 1;
    
    IF test_conversation_id IS NOT NULL THEN
        -- Insert test memory
        INSERT INTO conversation_memories (
            session_id,
            key_insights,
            importance_score,
            created_at
        ) VALUES (
            test_conversation_id,
            'TEST MEMORY: User made specific accusation about being drunk at DWP meeting',
            8.5,
            NOW()
        );
        
        RAISE NOTICE '✓ Successfully inserted test memory';
        
        -- Verify it was stored
        IF EXISTS (
            SELECT 1 FROM conversation_memories 
            WHERE key_insights LIKE 'TEST MEMORY:%'
        ) THEN
            RAISE NOTICE '✓ Test memory successfully retrieved';
            
            -- Clean up test data
            DELETE FROM conversation_memories 
            WHERE key_insights LIKE 'TEST MEMORY:%';
            
            RAISE NOTICE '✓ Test memory cleaned up';
        END IF;
    ELSE
        RAISE NOTICE '⚠ No conversations found to test with';
    END IF;
END $$;

-- Step 7: Summary
SELECT 
    '=== DYNAMIC MEMORY SYSTEM STATUS ===' AS summary;

SELECT 
    CASE 
        WHEN EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'conversation_memories')
        THEN 'READY - Dynamic memory system is operational'
        ELSE 'BROKEN - conversation_memories table missing'
    END AS overall_status;

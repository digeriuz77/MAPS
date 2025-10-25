-- Diagnostic: Check why Vic's conversation has no dynamic memories
-- Conversation ID: c0c138a7-6e0e-4af9-9a48-971072f6a1b3

-- Step 1: Verify conversation exists
SELECT 
    'Conversation Check' as check_type,
    id,
    persona_id,
    status,
    created_at
FROM conversations
WHERE id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 2: Check which persona this conversation is with
SELECT 
    'Persona Check' as check_type,
    p.persona_id,
    p.name,
    p.description
FROM conversations c
JOIN personas p ON c.persona_id = p.persona_id
WHERE c.id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 3: Check for dynamic memories in conversation_memories table
SELECT 
    'Dynamic Memories' as check_type,
    COUNT(*) as total_memories,
    MIN(created_at) as first_memory,
    MAX(created_at) as last_memory,
    AVG(importance_score) as avg_importance
FROM conversation_memories
WHERE session_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 4: Show actual memory content if any exists
SELECT 
    'Memory Content' as check_type,
    id,
    LEFT(key_insights, 100) as insight_preview,
    importance_score,
    created_at
FROM conversation_memories
WHERE session_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3'
ORDER BY created_at DESC
LIMIT 10;

-- Step 5: Check conversation transcripts (to verify messages were stored)
SELECT 
    'Transcript Check' as check_type,
    COUNT(*) as total_messages,
    COUNT(CASE WHEN role = 'user' THEN 1 END) as user_messages,
    COUNT(CASE WHEN role = 'persona' THEN 1 END) as persona_messages,
    MIN(timestamp) as first_message,
    MAX(timestamp) as last_message
FROM conversation_transcripts
WHERE conversation_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 6: Show sample transcript messages
SELECT 
    'Sample Transcript' as check_type,
    turn_number,
    role,
    LEFT(message, 80) as message_preview,
    timestamp
FROM conversation_transcripts
WHERE conversation_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3'
ORDER BY turn_number
LIMIT 10;

-- Step 7: Compare with other personas - do THEY have memories?
SELECT 
    'Memory Comparison' as check_type,
    p.name as persona_name,
    COUNT(DISTINCT cm.session_id) as conversations_with_memories,
    COUNT(cm.id) as total_memories,
    AVG(cm.importance_score) as avg_importance
FROM personas p
LEFT JOIN conversations c ON p.persona_id = c.persona_id
LEFT JOIN conversation_memories cm ON c.id = cm.session_id
GROUP BY p.name
ORDER BY total_memories DESC;

-- Step 8: Check mi_analysis table for this conversation
SELECT 
    'MI Analysis' as check_type,
    COUNT(*) as total_analyses,
    AVG(empathy_score) as avg_empathy,
    AVG(quality_score) as avg_quality,
    MIN(created_at) as first_analysis,
    MAX(created_at) as last_analysis
FROM mi_analysis
WHERE conversation_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 9: Check persona_responses table
SELECT 
    'Persona Responses' as check_type,
    COUNT(*) as total_responses,
    MIN(generated_at) as first_response,
    MAX(generated_at) as last_response
FROM persona_responses
WHERE conversation_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3';

-- Step 10: Final diagnosis summary
SELECT 
    'DIAGNOSIS' as summary,
    CASE 
        WHEN (SELECT COUNT(*) FROM conversation_memories WHERE session_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3') > 0
        THEN '✓ Memories exist - retrieval issue'
        WHEN (SELECT COUNT(*) FROM conversation_transcripts WHERE conversation_id = 'c0c138a7-6e0e-4af9-9a48-971072f6a1b3') > 0
        THEN '✗ Transcripts exist but NO memories formed - memory formation failed'
        ELSE '✗ No transcripts or memories - conversation may not have been saved'
    END as diagnosis;

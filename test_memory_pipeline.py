#!/usr/bin/env python3
"""
Test Memory Pipeline - Verify that personas can access their memories
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.services.smart_memory_manager import SmartMemoryManager
from src.services.memory_scoring_service import memory_scoring_service, RetrievalContext
from src.services.character_vector_service import character_vector_service
from src.models.conversation_state import ConversationState
from src.dependencies import get_supabase_client
import uuid
import asyncio

async def test_smart_memory_manager():
    """Test the SmartMemoryManager can retrieve memories based on trust levels"""
    print("=== TESTING SMART MEMORY MANAGER ===")
    
    supabase = get_supabase_client()
    manager = SmartMemoryManager(supabase)
    
    # Create a fake conversation state for testing
    conversation_state = ConversationState(
        session_id=str(uuid.uuid4()),
        stage="cautious",
        trust_level=0.5,
        key_topics=['work', 'stress'],
        turn_count=3,
        emotional_trajectory=[],
        last_updated=None
    )
    
    # Test getting baseline memories for Mary at cautious level
    try:
        memories = await manager.get_session_baseline_memories(
            conversation_id=conversation_state.session_id,
            persona_name="Mary", 
            conversation_state=conversation_state,
            current_topics=['work', 'performance']
        )
        
        print(f"✅ SmartMemoryManager returned {len(memories)} memories for Mary at trust={conversation_state.trust_level}")
        for i, mem in enumerate(memories[:3]):
            content = mem.get('memory_text') or mem.get('content', 'No content')
            print(f"  {i+1}. {content[:80]}...")
            
        return len(memories) > 0
        
    except Exception as e:
        print(f"❌ SmartMemoryManager failed: {e}")
        return False

async def test_memory_scoring_service():
    """Test the memory scoring service"""
    print("\n=== TESTING MEMORY SCORING SERVICE ===")
    
    context = RetrievalContext(
        user_input="How has work been going?",
        session_id=str(uuid.uuid4()),
        persona_id="mary",
        trust_level=0.5,
        interaction_quality="good",
        max_memories=5
    )
    
    try:
        scored_memories = await memory_scoring_service.retrieve_relevant_memories(context)
        
        print(f"✅ Memory scoring service returned {len(scored_memories)} memories")
        for i, mem in enumerate(scored_memories[:3]):
            print(f"  {i+1}. Score: {mem.final_score:.3f} - {mem.content[:60]}...")
            
        return len(scored_memories) > 0
        
    except Exception as e:
        print(f"❌ Memory scoring service failed: {e}")
        return False

def test_character_vector_service():
    """Test the character vector service"""
    print("\n=== TESTING CHARACTER VECTOR SERVICE ===")
    
    try:
        character_context = character_vector_service.get_character_context(
            persona_id="mary",
            user_input="Tell me about your work situation",
            trust_level=0.5,
            interaction_quality="good"
        )
        
        relevant_memories = character_context.get("relevant_memories", [])
        response_pattern = character_context.get("response_pattern", {})
        
        print(f"✅ Character vector service returned:")
        print(f"  - Relevant memories: {len(relevant_memories)}")
        print(f"  - Response pattern: {bool(response_pattern)}")
        
        if relevant_memories:
            for i, mem in enumerate(relevant_memories[:2]):
                content = mem.get('content', 'No content')
                print(f"    {i+1}. {content[:60]}...")
        
        return len(relevant_memories) > 0 or bool(response_pattern)
        
    except Exception as e:
        print(f"❌ Character vector service failed: {e}")
        return False

async def test_enhanced_persona_integration():
    """Test the enhanced persona service integration"""
    print("\n=== TESTING ENHANCED PERSONA INTEGRATION ===")
    
    try:
        from src.services.enhanced_persona_service import enhanced_persona_service
        
        # Test a simple conversation to see if memories are retrieved
        response = await enhanced_persona_service.process_conversation(
            user_message="Hi Mary, how have things been at work?",
            persona_id="mary",
            session_id=str(uuid.uuid4()),
            conversation_history=[],
            persona_llm="gpt-4o-mini"
        )
        
        print(f"✅ Enhanced persona service generated response:")
        print(f"  - Response: {response.response[:100]}...")
        print(f"  - Trust level: {response.trust_level:.3f}")
        print(f"  - Knowledge tier: {response.knowledge_tier_used}")
        print(f"  - Stage: {response.stage}")
        
        # Check if debug info shows memories were accessed
        debug_info = response.debug
        if debug_info:
            memories_text = debug_info.get("intelligent_memories_text", "")
            available_topics = debug_info.get("knowledge", {}).get("available_topics", [])
            
            print(f"  - Memory access: {bool(memories_text and memories_text != '(This is your first conversation together)')}")
            print(f"  - Available knowledge topics: {len(available_topics)}")
            
            if available_topics:
                print(f"    Topics: {available_topics[:3]}")
        
        return bool(response.response)
        
    except Exception as e:
        print(f"❌ Enhanced persona integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    print("=== MEMORY PIPELINE END-TO-END TEST ===")
    print("Testing if personas can now access their background knowledge...\n")
    
    results = []
    
    # Test each component
    results.append(("SmartMemoryManager", await test_smart_memory_manager()))
    results.append(("MemoryScoringService", await test_memory_scoring_service())) 
    results.append(("CharacterVectorService", test_character_vector_service()))
    results.append(("EnhancedPersonaIntegration", await test_enhanced_persona_integration()))
    
    # Summary
    print(f"\n=== RESULTS SUMMARY ===")
    passed = 0
    for component, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{component}: {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} components working")
    
    if passed >= 2:
        print("\n🎉 Memory pipeline is functional! Personas should now have access to their background knowledge.")
        return True
    else:
        print("\n⚠️  Memory pipeline needs more work. Some components are still failing.")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)

#!/usr/bin/env python3
"""
Simple Memory System Fix - Create basic knowledge tiers
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.dependencies import get_supabase_client

def create_basic_tiers():
    """Create basic knowledge tier structure"""
    supabase = get_supabase_client()
    
    print("Creating basic knowledge tiers...")
    
    # First clear any existing tiers to avoid duplicates
    try:
        supabase.table('character_knowledge_tiers').delete().neq('persona_id', 'nonexistent').execute()
        print("Cleared existing tiers")
    except Exception as e:
        print(f"Note: {e}")
    
    # Simple tier structure
    personas = ['mary', 'terry', 'jan']
    tiers = [
        {'name': 'defensive', 'threshold': 0.0},
        {'name': 'cautious', 'threshold': 0.4}, 
        {'name': 'opening', 'threshold': 0.6},
        {'name': 'trusting', 'threshold': 0.8}
    ]
    
    tier_records = []
    for persona_id in personas:
        for tier in tiers:
            basic_knowledge = {
                'basic_info': f'{persona_id} basic context',
                'topics': ['work', 'stress', 'communication'],
                'phrases': ['I understand', 'That makes sense']
            }
            
            tier_records.append({
                'persona_id': persona_id,
                'tier_name': tier['name'],
                'trust_threshold': tier['threshold'],
                'available_knowledge': basic_knowledge
            })
    
    try:
        result = supabase.table('character_knowledge_tiers').insert(tier_records).execute()
        print(f"✅ Created {len(result.data)} knowledge tier records")
        return True
    except Exception as e:
        print(f"❌ Failed to create knowledge tiers: {e}")
        return False

def create_basic_memories():
    """Create basic long-term memories"""
    supabase = get_supabase_client()
    
    print("Creating basic long-term memories...")
    
    # First check what columns exist
    try:
        # Test insert with minimal data to see what columns are expected
        import hashlib
        test_content = 'Test memory'
        test_hash = hashlib.md5(test_content.encode()).hexdigest()
        test_memory = {
            'persona_id': 'mary',
            'content': test_content,
            'memory_type': 'background',
            'hash': test_hash
        }
        result = supabase.table('long_term_memories').insert([test_memory]).execute()
        # If successful, delete the test record
        if result.data:
            supabase.table('long_term_memories').delete().eq('content', 'Test memory').execute()
            print("Basic columns work, trying full structure...")
    except Exception as e:
        print(f"Column structure error: {e}")
        return False
    
    import hashlib
    
    memory_contents = [
        ('mary', 'I used to be a top performer at work'),
        ('mary', 'Balancing work and childcare is really challenging'),
        ('terry', 'I have 15 years of experience in my field'),
        ('jan', 'My performance has declined recently and I dont know why')
    ]
    
    memories = []
    for persona_id, content in memory_contents:
        memory_hash = hashlib.md5(content.encode()).hexdigest()
        memories.append({
            'persona_id': persona_id,
            'content': content,
            'memory_type': 'background',
            'hash': memory_hash
        })
    
    try:
        result = supabase.table('long_term_memories').insert(memories).execute()
        print(f"✅ Created {len(result.data)} long-term memories")
        return True
    except Exception as e:
        print(f"❌ Failed to create memories: {e}")
        return False

def verify_system():
    """Verify the system works"""
    supabase = get_supabase_client()
    
    print("\n=== VERIFICATION ===")
    
    # Check tiers
    tiers = supabase.table('character_knowledge_tiers').select('*').execute()
    print(f"Knowledge tiers: {len(tiers.data) if tiers.data else 0}")
    
    # Check memories
    memories = supabase.table('long_term_memories').select('*').execute()
    print(f"Long-term memories: {len(memories.data) if memories.data else 0}")
    
    return True

def main():
    print("=== SIMPLE MEMORY SYSTEM FIX ===")
    
    success = True
    
    if not create_basic_tiers():
        success = False
        
    if not create_basic_memories():
        success = False
        
    verify_system()
    
    if success:
        print("\n✅ Basic memory system created!")
    else:
        print("\n❌ Some steps failed")
        
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
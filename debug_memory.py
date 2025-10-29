#!/usr/bin/env python3

from src.dependencies import get_supabase_client

def main():
    supabase = get_supabase_client()

    print("=== MEMORY SYSTEM DEBUG ===")

    # Check if persona_memories table exists - try/except
    try:
        personas_result = supabase.table('persona_memories').select('*').limit(5).execute()
        print(f'Persona memories count: {len(personas_result.data) if personas_result.data else 0}')
        if personas_result.data:
            for mem in personas_result.data[:3]:
                print(f'- Persona: {mem.get("persona_name")}, Text: {mem.get("memory_text", "")[:100]}...')
                print(f'  Importance: {mem.get("importance_score")}, Metadata: {str(mem.get("metadata", {}))[:100]}')
        else:
            print("No persona memories found!")
    except Exception as e:
        print(f"ERROR: persona_memories table not found: {e}")

    # Check conversation_memories table  
    conv_result = supabase.table('conversation_memories').select('*').limit(5).execute()
    print(f'\nConversation memories count: {len(conv_result.data) if conv_result.data else 0}')
    if conv_result.data:
        for mem in conv_result.data[:3]:
            print(f'- Session: {mem.get("session_id")}, Insights: {mem.get("key_insights", "")[:100]}...')
    else:
        print("No conversation memories found!")

    # Check character_knowledge_tiers
    try:
        tiers_result = supabase.table('character_knowledge_tiers').select('*').limit(5).execute()  
        print(f'\nCharacter knowledge tiers count: {len(tiers_result.data) if tiers_result.data else 0}')
        if tiers_result.data:
            for tier in tiers_result.data[:3]:
                print(f'- Persona: {tier.get("persona_id")}, Tier: {tier.get("tier_name")}, Trust: {tier.get("trust_threshold")}')
        else:
            print("No character knowledge tiers found!")
    except Exception as e:
        print(f"ERROR: character_knowledge_tiers table not found: {e}")

    # Check character_memories table (alternative)
    try:
        char_result = supabase.table('character_memories').select('*').limit(5).execute()  
        print(f'\nCharacter memories count: {len(char_result.data) if char_result.data else 0}')
        if char_result.data:
            for mem in char_result.data[:3]:
                print(f'- Persona: {mem.get("persona_id")}, Content: {mem.get("content", "")[:100]}...')
                print(f'  Weight: {mem.get("emotional_weight")}, Tags: {mem.get("context_tags")}')
        else:
            print("No character memories found!")
    except Exception as e:
        print(f"ERROR: character_memories table not found: {e}")

    # Check long_term_memories table (suggested alternative)
    try:
        ltm_result = supabase.table('long_term_memories').select('*').limit(5).execute()  
        print(f'\nLong term memories count: {len(ltm_result.data) if ltm_result.data else 0}')
        if ltm_result.data:
            for mem in ltm_result.data[:3]:
                print(f'- Persona: {mem.get("persona_id")}, Content: {mem.get("content", "")[:100]}...')
                print(f'  Trust req: {mem.get("trust_level_required")}, Tags: {mem.get("tags")}')
        else:
            print("No long term memories found!")
    except Exception as e:
        print(f"ERROR: long_term_memories table not found: {e}")

    # Check enhanced_personas table
    enhanced_result = supabase.table('enhanced_personas').select('persona_id', 'name').limit(5).execute()
    print(f'\nEnhanced personas count: {len(enhanced_result.data) if enhanced_result.data else 0}')
    if enhanced_result.data:
        for persona in enhanced_result.data[:3]:
            print(f'- ID: {persona.get("persona_id")}, Name: {persona.get("name")}')
    else:
        print("No enhanced personas found!")

if __name__ == "__main__":
    main()
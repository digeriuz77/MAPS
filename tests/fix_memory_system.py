#!/usr/bin/env python3
"""
Fix Memory System - Create missing character knowledge tiers and long-term memories
This addresses the issue where personas have no background knowledge to access.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from src.dependencies import get_supabase_client

def create_base_knowledge_tiers():
    """Create the base knowledge tier structure that migrations expect to exist"""
    supabase = get_supabase_client()
    
    print("Creating base character knowledge tiers...")
    
    # Base tier structure for Mary, Terry, Jan
    personas = ['mary', 'terry', 'jan']
    tiers = ['defensive', 'cautious', 'opening', 'trusting']
    
    tier_records = []
    for persona_id in personas:
        for tier_name in tiers:
            tier_records.append({
                'persona_id': persona_id,
                'tier_name': tier_name,
                'trust_threshold': 0.0,  # Will be updated by migration 0005
                'available_knowledge': {}  # Will be updated by migration 0005
            })
    
    try:
        result = supabase.table('character_knowledge_tiers').insert(tier_records).execute()
        print(f"✅ Created {len(result.data)} knowledge tier records")
        return True
    except Exception as e:
        print(f"❌ Failed to create knowledge tiers: {e}")
        return False

def run_migration_updates():
    """Run the migration 0005 updates to populate the knowledge content"""
    supabase = get_supabase_client()
    
    print("Running migration 0005 updates...")
    
    try:
        # Read and execute the migration SQL
        with open('supabase/0005_tiers_mary_terry.sql', 'r') as f:
            migration_sql = f.read()
        
        # Split by statements and execute each
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip() and not stmt.strip().startswith('--')]
        
        for stmt in statements:
            if stmt.lower().startswith('update'):
                print(f"Executing: {stmt[:60]}...")
                # Convert to Supabase update - this is complex, let's do it manually
                pass  # We'll do manual updates below
        
        # Manual updates for Mary's tiers
        print("Updating Mary's defensive tier...")
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.00,
            'available_knowledge': {
                'opening_topics': ['workload feels heavy','time pressure','general stress'],
                'safe_details': ['tight mornings','late emails','evening fatigue'],
                'resistance_phrases': ['Im not sure that would work','I dont want to get into that','Its complicated'],
                'validation_phrases': ['I appreciate you asking','Thanks for checking in'],
                'topic_rotation': ['workload','time_pressure','stress_baseline'],
                'escalation_hooks': ['what makes this week harder','one small thing that eased stress yesterday']
            }
        }).eq('persona_id', 'mary').eq('tier_name', 'defensive').execute()
        
        print("Updating Mary's cautious tier...")
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.40,
            'available_knowledge': {
                'opening_topics': ['feedback stung','schedule juggling','risk of mistakes'],
                'safe_details': ['manager check-ins tense','childcare swaps','missed breaks'],
                'deeper_details': ['fear of dropping a ball','worry about reliability perception'],
                'values_conflicts': ['good parent vs. dependable teammate'],
                'topic_rotation': ['feedback_reaction','juggle_examples','reliability_fear'],
                'escalation_hooks': ['when did it feel a little better','what support helped once before']
            }
        }).eq('persona_id', 'mary').eq('tier_name', 'cautious').execute()
        
        print("Updating Mary's opening tier...")
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.60,
            'available_knowledge': {
                'opening_topics': ['a specific incident this week'],
                'deeper_details': ['when stress peaked','who was present','what I told myself'],
                'unsaid_fears': ['asking for help looks weak','they'll think I can't handle it'],
                'coping_strategies': ['post-bedtime batching','short walks','breathing pauses'],
                'topic_rotation': ['incident_story','internal_talk','coping'],
                'escalation_hooks': ['what would make trying X 10% easier']
            }
        }).eq('persona_id', 'mary').eq('tier_name', 'opening').execute()
        
        print("Updating Mary's trusting tier...")  
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.80,
            'available_knowledge': {
                'deeper_details': ['concrete ask to manager/team','boundary to trial','backup plan if slips'],
                'values_conflicts': ['fairness to self vs. expectations'],
                'topic_rotation': ['specific_ask','boundary_trial','backup_plan'],
                'validation_phrases': ['This feels doable.','I'd like to try that.']
            }
        }).eq('persona_id', 'mary').eq('tier_name', 'trusting').execute()
        
        # Terry's tiers
        print("Updating Terry's tiers...")
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.00,
            'available_knowledge': {
                'opening_topics': ['efficiency priority','accuracy focus','directness'],
                'safe_details': ['correcting misinformation','tight SLAs'],
                'resistance_phrases': ['I don't see the problem.','This feels like a time sink.'],
                'validation_phrases': ['I hear your point.','Appreciate the clarity.'],
                'topic_rotation': ['efficiency','accuracy','directness'],
                'escalation_hooks': ['one place tone caused friction','what a concrete alternative looks like']
            }
        }).eq('persona_id', 'terry').eq('tier_name', 'defensive').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.40,
            'available_knowledge': {
                'opening_topics': ['difference between direct vs rude'],
                'safe_details': ['trained current team on complex cases'],
                'deeper_details': ['confusion about "being nicer" without being fake'],
                'topic_rotation': ['perspective_on_direct','training_examples','confusion_point'],
                'escalation_hooks': ['specific phrasing to try once','what to say in a similar moment next time']
            }
        }).eq('persona_id', 'terry').eq('tier_name', 'cautious').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.60,
            'available_knowledge': {
                'deeper_details': ['how to acknowledge before correcting','tag questions to soften tone'],
                'topic_rotation': ['ack_before_correct','tag_questions'],
                'validation_phrases': ['That's actionable.','I can try that.']
            }
        }).eq('persona_id', 'terry').eq('tier_name', 'opening').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.80,
            'available_knowledge': {
                'deeper_details': ['agree on "warm then precise" pattern','plan to ask for feedback on tone'],
                'topic_rotation': ['pattern_commit','feedback_request'], 
                'validation_phrases': ['I'll adopt that pattern.','Let's check it next meeting.']
            }
        }).eq('persona_id', 'terry').eq('tier_name', 'trusting').execute()
        
        # For Jan, create basic tiers (not in migration but needed)
        print("Updating Jan's tiers...")
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.00,
            'available_knowledge': {
                'opening_topics': ['work feels different', 'numbers not the same'],
                'safe_details': ['targets were easier before', 'unsure what changed'],
                'resistance_phrases': ['I'm not sure what happened.', 'Things just feel harder.'],
                'validation_phrases': ['I appreciate your patience.', 'That makes sense.'],
                'topic_rotation': ['work_change', 'performance_shift'],
                'escalation_hooks': ['when did you first notice', 'what was different then']
            }
        }).eq('persona_id', 'jan').eq('tier_name', 'defensive').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.40,
            'available_knowledge': {
                'opening_topics': ['stress at home', 'concentration issues'],
                'safe_details': ['harder to focus', 'mind wanders more'],
                'deeper_details': ['living situation changed', 'sleep isn't great'],
                'topic_rotation': ['focus_issues', 'home_stress'],
                'escalation_hooks': ['what helps you focus', 'small thing that might help']
            }
        }).eq('persona_id', 'jan').eq('tier_name', 'cautious').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.60,
            'available_knowledge': {
                'deeper_details': ['breakup happened', 'living alone now', 'adjusting to quiet'],
                'unsaid_fears': ['maybe I'm not cut out for this', 'what if I never get back to where I was'],
                'coping_strategies': ['long walks', 'calling family more', 'earlier bedtime'],
                'topic_rotation': ['adjustment_story', 'self_doubt', 'coping'],
                'escalation_hooks': ['what would make the adjustment easier']
            }
        }).eq('persona_id', 'jan').eq('tier_name', 'opening').execute()
        
        supabase.table('character_knowledge_tiers').update({
            'trust_threshold': 0.80,
            'available_knowledge': {
                'deeper_details': ['specific routine to try', 'accountability check-in', 'self-compassion practice'],
                'values_conflicts': ['independence vs. asking for support'],
                'topic_rotation': ['routine_trial', 'check_in_plan', 'self_compassion'],
                'validation_phrases': ['I could try that.', 'Let's see how it goes.']
            }
        }).eq('persona_id', 'jan').eq('tier_name', 'trusting').execute()
        
        print("✅ Successfully populated all knowledge tiers")
        return True
        
    except Exception as e:
        print(f"❌ Failed to run migration updates: {e}")
        return False

def create_sample_long_term_memories():
    """Create some sample long-term memories for each persona"""
    supabase = get_supabase_client()
    
    print("Creating sample long-term memories...")
    
    memories = [
        # Mary's memories
        {
            'persona_id': 'mary',
            'content': 'Won Rep of the Year in 2022 - that feels like a different lifetime now',
            'trust_level_required': 0.3,
            'tags': ['achievement', 'work', 'past_success'],
            'emotional_weight': 0.8
        },
        {
            'persona_id': 'mary', 
            'content': 'Morning routine with my son - getting him ready while checking emails',
            'trust_level_required': 0.6,
            'tags': ['family', 'routine', 'juggling'],
            'emotional_weight': 0.7
        },
        {
            'persona_id': 'mary',
            'content': 'The conversation with my manager about "performance concerns" - still stings',
            'trust_level_required': 0.8,
            'tags': ['feedback', 'manager', 'vulnerability'],
            'emotional_weight': 0.9
        },
        
        # Terry's memories
        {
            'persona_id': 'terry',
            'content': '15 years here - trained half the current team on complex regulations',
            'trust_level_required': 0.3,
            'tags': ['experience', 'training', 'expertise'],
            'emotional_weight': 0.7
        },
        {
            'persona_id': 'terry',
            'content': 'Last week someone said I "intimidated" a new hire - apparently I was too direct',
            'trust_level_required': 0.6,
            'tags': ['feedback', 'communication', 'confusion'],
            'emotional_weight': 0.8
        },
        
        # Jan's memories
        {
            'persona_id': 'jan',
            'content': 'Used to hit my targets easily - something changed but I can\'t put my finger on it',
            'trust_level_required': 0.3,
            'tags': ['performance', 'confusion', 'change'],
            'emotional_weight': 0.6
        },
        {
            'persona_id': 'jan',
            'content': 'Living alone after the breakup - the quiet is still strange',
            'trust_level_required': 0.7,
            'tags': ['personal', 'adjustment', 'loneliness'],
            'emotional_weight': 0.8
        }
    ]
    
    try:
        result = supabase.table('long_term_memories').insert(memories).execute()
        print(f"✅ Created {len(result.data)} long-term memories")
        return True
    except Exception as e:
        print(f"❌ Failed to create long-term memories: {e}")
        return False

def verify_memory_system():
    """Verify the memory system is working"""
    supabase = get_supabase_client()
    
    print("\n=== VERIFICATION ===")
    
    # Check knowledge tiers
    tiers = supabase.table('character_knowledge_tiers').select('*').execute()
    print(f"Knowledge tiers: {len(tiers.data) if tiers.data else 0}")
    if tiers.data:
        for tier in tiers.data[:3]:
            print(f"  - {tier['persona_id']} {tier['tier_name']}: trust={tier['trust_threshold']}")
    
    # Check long-term memories  
    memories = supabase.table('long_term_memories').select('*').execute()
    print(f"Long-term memories: {len(memories.data) if memories.data else 0}")
    if memories.data:
        for mem in memories.data[:3]:
            print(f"  - {mem['persona_id']}: {mem['content'][:50]}...")
    
    return True

def main():
    print("=== FIXING MEMORY SYSTEM ===")
    print("This will create the missing knowledge tiers and memories that personas need.\n")
    
    success = True
    
    # Step 1: Create base knowledge tier structure
    if not create_base_knowledge_tiers():
        success = False
        
    # Step 2: Populate with migration content
    if not run_migration_updates():
        success = False
        
    # Step 3: Create sample long-term memories
    if not create_sample_long_term_memories():
        success = False
        
    # Step 4: Verify everything worked
    verify_memory_system()
    
    if success:
        print("\n✅ Memory system fixed! Personas should now have access to their background knowledge.")
    else:
        print("\n❌ Some steps failed. Check the errors above.")
        
    return success

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)
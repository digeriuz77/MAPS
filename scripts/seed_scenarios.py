"""
Seed Scenarios Script - Create example scenarios in the database

Run this script to populate the scenarios table with example MI training scenarios.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.dependencies import get_supabase_client


# Example Scenario 1: Closing with Ambivalent Employee
SCENARIO_CLOSING_AMBIVALENT = {
    "code": "close-ambivalent-001",
    "title": "Closing the Conversation",
    "mi_skill_category": "Closing",
    "difficulty": "beginner",
    "estimated_minutes": 5,
    
    "situation": """
    You're 8 minutes into a conversation with Jordan about time management. 
    Jordan has acknowledged some issues but hasn't committed to any actions. 
    The conversation needs to close soon.
    """,
    
    "learning_objective": "Practice closing appropriately without forcing commitment",
    
    "persona_config": {
        "name": "Jordan",
        "role": "Team member, 2 years in role",
        "current_mindset": "Polite but evasive - acknowledges problems but deflects solutions",
        
        "personality": """
        You're polite and professional, but you tend to deflect responsibility.
        You agree with criticisms in principle but always add "but" followed by
        external factors. You're ambivalent about change - part of you wants to
        improve, but part of you thinks the problems aren't really yours to solve.
        """,
        
        "response_patterns": {
            "to_reflection": "Cautiously agree but add caveats",
            "to_direct_advice": "Polite dismissal - 'I've tried that'",
            "to_confrontation": "Defensive - shift blame to external factors",
            "to_empathy": "Slightly more open, but still guarded",
            "to_autonomy_support": "Most responsive - hints at own ideas"
        },
        
        "triggers": {
            "trust_increase": ["empathy", "asking permission", "validating feelings", "what do you think", "would it be okay"],
            "trust_decrease": ["direct advice", "blame", "dismissing concerns", "you should", "you need to"],
            "resistance_increase": ["confrontation", "should", "have to", "fix"]
        },
        
        "starting_state": {
            "trust_level": 4,
            "openness_level": 3,
            "resistance_active": True
        }
    },
    
    "success_criteria": {
        "turn_range": [3, 8],
        "required_skills": ["reflection", "summarization"],
        "avoid_behaviors": ["unsolicited_advice", "fixing"],
        "state_goals": {
            "trust_maintained": True,
            "resistance_not_increased": True
        }
    },
    
    "maps_rubric": {
        "dimensions": [
            {"name": "summarization_quality", "weight": 0.3},
            {"name": "autonomy_support", "weight": 0.3},
            {"name": "empathy", "weight": 0.2},
            {"name": "evocation", "weight": 0.2}
        ]
    }
}


# Example Scenario 2: Action Planning
SCENARIO_ACTION_PLANNING = {
    "code": "action-planning-001",
    "title": "Moving to Action Planning",
    "mi_skill_category": "Action Planning",
    "difficulty": "intermediate",
    "estimated_minutes": 8,
    
    "situation": """
    You've been talking with Alex about their workload for about 10 minutes.
    Alex has mentioned several times that they want to make changes but 
    keeps hitting barriers. They're showing some change talk but haven't
    articulated specific actions.
    """,
    
    "learning_objective": "Guide the conversation from exploration to action planning",
    
    "persona_config": {
        "name": "Alex",
        "role": "Senior team member",
        "current_mindset": "Motivated but uncertain - wants change but overwhelmed",
        
        "personality": """
        Alex is genuinely motivated to improve but tends to get overwhelmed
        when thinking about solutions. They start with enthusiasm but quickly
        list all the reasons why things won't work. They need gentle 
        encouragement to break things down into smaller steps.
        """,
        
        "response_patterns": {
            "to_reflection": "Appreciates it, opens up more",
            "to_complex_reflection": "Feels understood, shares deeper concerns",
            "to_evocation_questions": "Engages with change talk",
            "to_jumping_to_solutions": "Shuts down, lists barriers",
            "to_autonomy_support": "Becomes more confident, suggests own ideas"
        },
        
        "triggers": {
            "trust_increase": ["complex reflection", "evocation", "what's important", "what would help"],
            "trust_decrease": ["solutions", "just do", "why don't you", "you should"],
            "resistance_increase": ["pressure", "deadlines", "must", "have to"]
        },
        
        "starting_state": {
            "trust_level": 5,
            "openness_level": 5,
            "resistance_active": False
        }
    },
    
    "success_criteria": {
        "turn_range": [4, 10],
        "required_skills": ["open_question", "reflection", "complex_reflection"],
        "avoid_behaviors": ["unsolicited_advice", "closed_question"],
        "state_goals": {
            "trust_maintained": True,
            "change_talk_elicted": True
        }
    },
    
    "maps_rubric": {
        "dimensions": [
            {"name": "evocation", "weight": 0.35},
            {"name": "autonomy_support", "weight": 0.25},
            {"name": "empathy", "weight": 0.25},
            {"name": "focus", "weight": 0.15}
        ]
    }
}


# Example Scenario 3: Change Talk
SCENARIO_CHANGE_TALK = {
    "code": "change-talk-001",
    "title": "Eliciting Change Talk",
    "mi_skill_category": "Change Talk",
    "difficulty": "intermediate",
    "estimated_minutes": 7,
    
    "situation": """
    You've been listening to Jamie discuss work-life balance issues.
    Jamie has mentioned feeling burnt out and acknowledged that something
    needs to change. Now you want to explore Jamie's own motivations 
    for change rather than suggesting solutions.
    """,
    
    "learning_objective": "Practice eliciting change talk using evocation techniques",
    
    "persona_config": {
        "name": "Jamie",
        "role": "Team lead, 3 years in role",
        "current_mindset": "Amotivated but hesitant - knows change is needed, fears consequences",
        
        "personality": """
        Jamie is intelligent and self-aware but tends to focus on obstacles
        rather than opportunities. They need permission to explore what
        they really want. When asked about their own motivations, they
        often deflect with practical concerns. Once they connect with
        their core values, they become more engaged.
        """,
        
        "response_patterns": {
            "to_value_exploration": "Engages, shares deeper motivations",
            "to_obstacle_focus": "Lists more problems, disengages",
            "to_permission_asking": "More open to exploring",
            "to_solution_presentation": "Focuses on why it won't work"
        },
        
        "triggers": {
            "trust_increase": ["what matters to you", "what do you want", "if things were different"],
            "trust_decrease": ["you should", "try harder", "just decide"],
            "resistance_increase": ["pressure", "deadlines", "other people's opinions"]
        },
        
        "starting_state": {
            "trust_level": 5,
            "openness_level": 4,
            "resistance_active": False
        }
    },
    
    "success_criteria": {
        "turn_range": [4, 9],
        "required_skills": ["open_question", "evocation"],
        "avoid_behaviors": ["advice_giving", "closed_question"],
        "state_goals": {
            "change_talk_quality": "high"
        }
    },
    
    "maps_rubric": {
        "dimensions": [
            {"name": "evocation", "weight": 0.4},
            {"name": "autonomy_support", "weight": 0.25},
            {"name": "focus", "weight": 0.2},
            {"name": "empathy", "weight": 0.15}
        ]
    }
}


def seed_scenarios():
    """Seed the scenarios table with example scenarios"""
    supabase = get_supabase_client()
    
    scenarios = [
        SCENARIO_CLOSING_AMBIVALENT,
        SCENARIO_ACTION_PLANNING,
        SCENARIO_CHANGE_TALK
    ]
    
    created = []
    skipped = []
    errors = []
    
    for scenario in scenarios:
        try:
            # Check if scenario exists
            existing = supabase.table('scenarios').select('id').eq('code', scenario['code']).execute()
            
            if existing.data:
                print(f"⏭ Skipping {scenario['code']} - already exists")
                skipped.append(scenario['code'])
                continue
            
            # Insert scenario
            result = supabase.table('scenarios').insert(scenario).execute()
            
            if result.data:
                print(f"✓ Created scenario: {scenario['code']} - {scenario['title']}")
                created.append(scenario['code'])
            else:
                print(f"✗ Failed to create {scenario['code']}")
                errors.append(scenario['code'])
                
        except Exception as e:
            print(f"✗ Error creating {scenario['code']}: {e}")
            errors.append(scenario['code'])
    
    print(f"\n{'='*50}")
    print(f"Created: {len(created)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Errors: {len(errors)}")
    
    if created:
        print(f"\nCreated scenarios: {', '.join(created)}")
    
    return created, skipped, errors


if __name__ == "__main__":
    print("Seeding example scenarios...\n")
    seed_scenarios()

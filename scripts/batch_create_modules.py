"""Batch create remaining Phase 2 modules"""
import json
from pathlib import Path

MODULES_DIR = Path("C:/builds/MAPS/src/data/mi_modules")

# Module templates for remaining modules
modules = [
    {
        "file": "shared_summarizing.json",
        "id": "00000000-0000-0001-0001-000000000005",
        "code": "shared-summarizing-005",
        "title": "Summarizing - Linking and Transitioning",
        "content_type": "shared",
        "focus": "Linking & Transitioning",
        "difficulty": "intermediate",
        "objective": "Learn to summarize key points, link themes, and transition smoothly between topics",
        "persona": {"name": "Morgan", "role": "person", "traits": ["reflective", "processing"]}
    },
    {
        "file": "shared_confidence_scaling.json",
        "id": "00000000-0000-0001-0001-000000000008",
        "code": "shared-confidence-scaling-008",
        "title": "Confidence Scaling - Assessment Practice",
        "content_type": "shared",
        "focus": "Assessment",
        "difficulty": "beginner",
        "objective": "Learn to use confidence scaling to assess readiness and explore what would increase or decrease confidence",
        "persona": {"name": "Riley", "role": "person", "traits": ["ambivalent", "uncertain"]}
    },
    {
        "file": "customer_financial_anxiety.json",
        "id": "00000000-0000-0002-0001-000000000003",
        "code": "customer-financial-anxiety-003",
        "title": "Supporting Financial Anxiety",
        "content_type": "customer_facing",
        "focus": "Domain 1 (Knowing Customer)",
        "difficulty": "intermediate",
        "objective": "Practice supporting customers experiencing financial anxiety using reflection and normalization",
        "persona": {"name": "Alex", "role": "customer", "traits": ["anxious", "overwhelmed", "ashamed"]}
    },
    {
        "file": "customer_savings_goals.json",
        "id": "00000000-0000-0002-0001-000000000004",
        "code": "customer-savings-goals-004",
        "title": "Savings Goal Setting",
        "content_type": "customer_facing",
        "focus": "Domain 5 (Budgeting)",
        "difficulty": "beginner",
        "objective": "Practice facilitating savings goal exploration using evoking and planning skills",
        "persona": {"name": "Casey", "role": "customer", "traits": ["hopeful", "uncertain", "motivated"]}
    },
    {
        "file": "colleague_skill_gap.json",
        "id": "00000000-0000-0003-0001-000000000003",
        "code": "colleague-skill-gap-003",
        "title": "Skill Gap Coaching: Development Support",
        "content_type": "colleague_facing",
        "focus": "Training & Development",
        "difficulty": "intermediate",
        "objective": "Practice coaching conversations about skill gaps while maintaining colleague dignity and ownership",
        "persona": {"name": "Sam", "role": "colleague", "traits": ["defensive", "aware", "growth_minded"]}
    }
]

# Create placeholder modules for remaining
for module in modules:
    print(f"Would create: {module['file']}")
    
print(f"\nNeed to create 5 more shared, 2 more customer, 1 more colleague module")
print("Plus learning pathways and seed scripts")

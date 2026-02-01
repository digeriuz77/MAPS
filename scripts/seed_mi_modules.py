"""
MI Module Seeding Script

Seeds converted MI practice modules into the MAPS database.
Usage: python scripts/seed_mi_modules.py [--modules-dir DIR] [--clear-existing]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.dependencies import get_supabase_client
from src.models.mi_models import MIPracticeModule


def load_module_files(modules_dir: str) -> List[Dict[str, Any]]:
    """Load all module JSON files from the specified directory"""
    modules = []
    modules_path = Path(modules_dir)
    
    if not modules_path.exists():
        print(f"[ERR] Modules directory not found: {modules_dir}")
        return []
    
    for file_path in sorted(modules_path.glob("module_*.json")):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                modules.append(data)
                print(f"[OK] Loaded: {file_path.name}")
        except Exception as e:
            print(f"[ERR] Failed to load {file_path.name}: {e}")
    
    return modules


def validate_module(module_data: Dict[str, Any]) -> bool:
    """Validate module data against MIPracticeModule schema"""
    required_fields = [
        'code', 'title', 'learning_objective', 'scenario_context',
        'persona_config', 'dialogue_structure', 'maps_rubric'
    ]
    
    for field in required_fields:
        if field not in module_data:
            print(f"[WARN] Module missing required field: {field}")
            return False
    
    # Validate dialogue structure
    dialogue = module_data.get('dialogue_structure', {})
    if 'start_node_id' not in dialogue or 'nodes' not in dialogue:
        print(f"[WARN] Module has invalid dialogue structure")
        return False
    
    return True


def seed_modules(supabase_client, modules: List[Dict[str, Any]], clear_existing: bool = False):
    """Seed modules into the database"""
    
    if clear_existing:
        print("\n[!] Clearing existing modules...")
        try:
            # Delete from mi_practice_modules (cascades to attempts)
            result = supabase_client.table('mi_practice_modules').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print(f"[OK] Cleared existing modules")
        except Exception as e:
            print(f"[WARN] Could not clear existing modules: {e}")
    
    print(f"\n[>] Seeding {len(modules)} modules...")
    
    success_count = 0
    error_count = 0
    
    for module_data in modules:
        try:
            # Validate module
            if not validate_module(module_data):
                print(f"[SKIP] Module validation failed: {module_data.get('code', 'unknown')}")
                error_count += 1
                continue
            
            # Check if module already exists
            code = module_data.get('code')
            existing = supabase_client.table('mi_practice_modules').select('id').eq('code', code).execute()
            
            if existing.data:
                print(f"[SKIP] Module already exists: {code}")
                continue
            
            # Prepare data for insertion
            insert_data = {
                'code': module_data['code'],
                'title': module_data['title'],
                'mi_focus_area': module_data.get('mi_focus_area'),
                'difficulty_level': module_data.get('difficulty_level', 'beginner'),
                'estimated_minutes': module_data.get('estimated_minutes', 5),
                'learning_objective': module_data['learning_objective'],
                'scenario_context': module_data['scenario_context'],
                'persona_config': module_data['persona_config'],
                'dialogue_structure': module_data['dialogue_structure'],
                'target_competencies': module_data.get('target_competencies', []),
                'maps_rubric': module_data['maps_rubric'],
                'is_active': module_data.get('is_active', True),
            }
            
            # Insert into database
            result = supabase_client.table('mi_practice_modules').insert(insert_data).execute()
            
            if result.data:
                print(f"[OK] Seeded: {code} - {module_data['title'][:50]}...")
                success_count += 1
            else:
                print(f"[ERR] Failed to seed: {code}")
                error_count += 1
                
        except Exception as e:
            print(f"[ERR] Error seeding module {module_data.get('code', 'unknown')}: {e}")
            error_count += 1
    
    return success_count, error_count


def create_sample_learning_paths(supabase_client, clear_existing: bool = False):
    """Create sample learning paths"""
    
    if clear_existing:
        try:
            supabase_client.table('mi_learning_paths').delete().neq('id', '00000000-0000-0000-0000-000000000000').execute()
            print("[OK] Cleared existing learning paths")
        except Exception as e:
            print(f"[WARN] Could not clear learning paths: {e}")
    
    # Get all module IDs
    result = supabase_client.table('mi_practice_modules').select('id, code, difficulty_level').execute()
    
    if not result.data:
        print("[WARN] No modules found to create learning paths")
        return
    
    modules = result.data
    
    # Group modules by difficulty
    beginner_modules = [m['id'] for m in modules if m['difficulty_level'] == 'beginner']
    intermediate_modules = [m['id'] for m in modules if m['difficulty_level'] == 'intermediate']
    advanced_modules = [m['id'] for m in modules if m['difficulty_level'] == 'advanced']
    
    learning_paths = [
        {
            'code': 'path-mi-foundations-001',
            'title': 'MI Foundations: Building Engagement',
            'description': 'Learn the fundamentals of Motivational Interviewing through structured practice scenarios. Focus on building rapport and using simple reflections.',
            'module_sequence': beginner_modules[:4] if len(beginner_modules) >= 4 else beginner_modules,
            'target_audience': 'beginners',
            'estimated_total_minutes': 30,
            'maps_competencies_targeted': ['A6', 'B6', '2.1.1'],
            'is_active': True,
        },
        {
            'code': 'path-mi-intermediate-001',
            'title': 'MI Intermediate: Evoking Change Talk',
            'description': 'Build on foundational skills to evoke and strengthen change talk. Practice open questions, affirmations, and reflections.',
            'module_sequence': intermediate_modules[:4] if len(intermediate_modules) >= 4 else intermediate_modules,
            'target_audience': 'intermediate',
            'estimated_total_minutes': 40,
            'maps_competencies_targeted': ['A6', 'B6', '2.1.1', '2.2.1', '2.3.1', '3.1.1'],
            'is_active': True,
        },
        {
            'code': 'path-mi-advanced-001',
            'title': 'MI Advanced: Managing Resistance',
            'description': 'Master advanced MI techniques including managing resistance, developing discrepancy, and collaborative planning.',
            'module_sequence': advanced_modules[:4] if len(advanced_modules) >= 4 else advanced_modules,
            'target_audience': 'advanced',
            'estimated_total_minutes': 50,
            'maps_competencies_targeted': ['A6', 'B6', '1.2.1', '2.1.1', '2.2.1', '3.1.1', '4.1.1'],
            'is_active': True,
        },
    ]
    
    print("\n[>] Creating learning paths...")
    
    for path_data in learning_paths:
        try:
            # Check if path already exists
            existing = supabase_client.table('mi_learning_paths').select('id').eq('code', path_data['code']).execute()
            
            if existing.data:
                print(f"[SKIP] Learning path already exists: {path_data['code']}")
                continue
            
            if not path_data['module_sequence']:
                print(f"[SKIP] No modules for path: {path_data['code']}")
                continue
            
            result = supabase_client.table('mi_learning_paths').insert(path_data).execute()
            
            if result.data:
                print(f"[OK] Created learning path: {path_data['code']}")
            else:
                print(f"[ERR] Failed to create path: {path_data['code']}")
                
        except Exception as e:
            print(f"[ERR] Error creating path {path_data['code']}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Seed MI practice modules into MAPS database')
    parser.add_argument('--modules-dir', default='src/data/mi_modules',
                        help='Directory containing converted module JSON files')
    parser.add_argument('--clear-existing', action='store_true',
                        help='Clear existing modules before seeding')
    parser.add_argument('--skip-paths', action='store_true',
                        help='Skip creating learning paths')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("MI Practice Module Seeding Tool")
    print("=" * 60)
    
    # Get Supabase client
    try:
        supabase = get_supabase_client()
        print("[OK] Connected to Supabase")
    except Exception as e:
        print(f"[ERR] Failed to connect to Supabase: {e}")
        sys.exit(1)
    
    # Load module files
    modules_dir = os.path.join(os.path.dirname(__file__), '..', args.modules_dir)
    modules = load_module_files(modules_dir)
    
    if not modules:
        print("[ERR] No modules found to seed")
        sys.exit(1)
    
    print(f"\n[>] Found {len(modules)} modules to seed")
    
    # Seed modules
    success_count, error_count = seed_modules(supabase, modules, args.clear_existing)
    
    print(f"\n" + "=" * 60)
    print(f"Seeding Results:")
    print(f"  Success: {success_count}")
    print(f"  Errors: {error_count}")
    print(f"  Total: {len(modules)}")
    print("=" * 60)
    
    # Create learning paths
    if not args.skip_paths:
        create_sample_learning_paths(supabase, args.clear_existing)
    
    print("\n[DONE] Seeding complete!")


if __name__ == "__main__":
    main()

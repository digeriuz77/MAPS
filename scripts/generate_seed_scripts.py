"""
Generate Supabase seed SQL scripts from converted MAPS module JSON files.
"""
import json
import os
from pathlib import Path

def escape_single_quotes(s):
    """Escape single quotes for SQL strings."""
    return s.replace("'", "''")

def json_to_sql_insert(module_data):
    """Convert module JSON to SQL INSERT statement."""
    
    # Basic fields
    fields = {
        'id': module_data.get('id', ''),
        'code': module_data.get('code', ''),
        'title': escape_single_quotes(module_data.get('title', '')),
        'mi_focus_area': module_data.get('mi_focus_area'),
        'difficulty_level': module_data.get('difficulty_level', 'beginner'),
        'estimated_minutes': module_data.get('estimated_minutes', 5),
        'learning_objective': escape_single_quotes(module_data.get('learning_objective', '')),
        'scenario_context': escape_single_quotes(module_data.get('scenario_context', '')),
    }
    
    # JSONB fields
    persona_config_json = json.dumps(module_data.get('persona_config', {}))
    dialogue_structure_json = json.dumps(module_data.get('dialogue_structure', {}))
    maps_rubric_json = json.dumps(module_data.get('maps_rubric', {}))
    
    # Array field
    target_competencies = module_data.get('target_competencies', [])
    competencies_array = "'" + json.dumps(target_competencies).replace("'", "''") + "'"
    
    # Build SQL
    sql = f"""INSERT INTO mi_practice_modules (
    id,
    code,
    title,
    mi_focus_area,
    difficulty_level,
    estimated_minutes,
    learning_objective,
    scenario_context,
    persona_config,
    dialogue_structure,
    target_competencies,
    maps_rubric,
    is_active
) VALUES (
    '{fields['id']}',
    '{fields['code']}',
    '{fields['title']}',
    '{fields['mi_focus_area']}',
    '{fields['difficulty_level']}',
    {fields['estimated_minutes']},
    '{fields['learning_objective']}',
    '{fields['scenario_context']}',
    '{escape_single_quotes(persona_config_json)}'::jsonb,
    '{escape_single_quotes(dialogue_structure_json)}'::jsonb,
    ARRAY{competencies_array.replace('"', '\\"')},
    '{escape_single_quotes(maps_rubric_json)}'::jsonb,
    true
) ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    mi_focus_area = EXCLUDED.mi_focus_area,
    difficulty_level = EXCLUDED.difficulty_level,
    estimated_minutes = EXCLUDED.estimated_minutes,
    learning_objective = EXCLUDED.learning_objective,
    scenario_context = EXCLUDED.scenario_context,
    persona_config = EXCLUDED.persona_config,
    dialogue_structure = EXCLUDED.dialogue_structure,
    target_competencies = EXCLUDED.target_competencies,
    maps_rubric = EXCLUDED.maps_rubric,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();"""
    
    return sql

def generate_seed_script(module_path, output_path):
    """Generate a complete seed script for a module."""
    
    with open(module_path, 'r', encoding='utf-8') as f:
        module = json.load(f)
    
    code = module.get('code', 'unknown')
    title = module.get('title', 'Unknown')
    
    header = f"""-- supabase/seed/seed_{code}.sql
-- MAPS Practice Module: {title}
-- Content Type: {module.get('content_type', 'shared')}
--
-- Usage:
--   supabase db execute --file supabase/seed/seed_{code}.sql
-- Or paste into Supabase SQL Editor

-- ============================================
-- INSERT MAPS PRACTICE MODULE
-- ============================================
"""
    
    footer = f"""

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Uncomment to verify insertion:
-- SELECT code, title, mi_focus_area, difficulty_level, estimated_minutes, is_active
-- FROM mi_practice_modules
-- WHERE code = '{code}';
"""
    
    sql_insert = json_to_sql_insert(module)
    
    full_script = header + sql_insert + footer
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_script)
    
    return code, title

def main():
    modules_dir = Path("C:/builds/MAPS/src/data/mi_modules")
    seed_dir = Path("C:/builds/MAPS/supabase/seed")
    
    # Find all *_maps.json files
    module_files = sorted(modules_dir.glob("*_maps.json"))
    
    print(f"Found {len(module_files)} converted modules")
    print("=" * 60)
    
    for module_file in module_files:
        # Generate seed script filename
        module_num = module_file.stem.split('_')[1]  # Extract module number
        output_name = f"seed_mi_module_{module_num}_{module_file.stem.replace('_maps', '')}.sql"
        output_path = seed_dir / output_name
        
        code, title = generate_seed_script(module_file, output_path)
        print(f"[OK] Created: {output_name}")
        print(f"  Code: {code}")
        print(f"  Title: {title[:60]}...")
        print()
    
    print("=" * 60)
    print(f"Generated {len(module_files)} seed scripts in {seed_dir}")

if __name__ == "__main__":
    main()

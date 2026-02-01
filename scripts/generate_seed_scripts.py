"""
Generate Supabase seed SQL scripts from MAPS module JSON files.

Supports the new module structure:
- shared_*: Core technique modules with neutral language
- customer_*: Customer-facing MAPS financial scenarios
- colleague_*: Colleague-facing workplace scenarios
"""
import json
import os
from pathlib import Path

def escape_single_quotes(s):
    """Escape single quotes for SQL strings."""
    if s is None:
        return ''
    return str(s).replace("'", "''")

def json_to_sql_insert(module_data):
    """Convert module JSON to SQL INSERT statement."""

    # Basic fields
    fields = {
        'id': module_data.get('id', ''),
        'code': module_data.get('code', ''),
        'title': escape_single_quotes(module_data.get('title', '')),
        'content_type': module_data.get('content_type', 'shared'),
        'mi_focus_area': module_data.get('mi_focus_area', ''),
        'difficulty_level': module_data.get('difficulty_level', 'beginner'),
        'estimated_minutes': module_data.get('estimated_minutes', 5),
        'learning_objective': escape_single_quotes(module_data.get('learning_objective', '')),
        'scenario_context': escape_single_quotes(module_data.get('scenario_context', '')),
    }

    # JSONB fields
    persona_config_json = json.dumps(module_data.get('persona_config', {}))
    dialogue_structure_json = json.dumps(module_data.get('dialogue_structure', {}))
    maps_rubric_json = json.dumps(module_data.get('maps_rubric', {}))
    maps_framework_alignment_json = json.dumps(module_data.get('maps_framework_alignment', {}))

    # Array field
    target_competencies = module_data.get('target_competencies', [])
    competencies_array = "'" + json.dumps(target_competencies).replace("'", "''") + "'"

    # Build SQL
    sql = f"""INSERT INTO mi_practice_modules (
    id,
    code,
    title,
    content_type,
    mi_focus_area,
    difficulty_level,
    estimated_minutes,
    learning_objective,
    scenario_context,
    persona_config,
    dialogue_structure,
    target_competencies,
    maps_rubric,
    maps_framework_alignment,
    is_active
) VALUES (
    '{fields['id']}',
    '{fields['code']}',
    '{fields['title']}',
    '{fields['content_type']}',
    '{fields['mi_focus_area']}',
    '{fields['difficulty_level']}',
    {fields['estimated_minutes']},
    '{fields['learning_objective']}',
    '{fields['scenario_context']}',
    '{escape_single_quotes(persona_config_json)}'::jsonb,
    '{escape_single_quotes(dialogue_structure_json)}'::jsonb,
    ARRAY{competencies_array.replace('"', '\\"')},
    '{escape_single_quotes(maps_rubric_json)}'::jsonb,
    '{escape_single_quotes(maps_framework_alignment_json)}'::jsonb,
    true
) ON CONFLICT (code) DO UPDATE SET
    title = EXCLUDED.title,
    content_type = EXCLUDED.content_type,
    mi_focus_area = EXCLUDED.mi_focus_area,
    difficulty_level = EXCLUDED.difficulty_level,
    estimated_minutes = EXCLUDED.estimated_minutes,
    learning_objective = EXCLUDED.learning_objective,
    scenario_context = EXCLUDED.scenario_context,
    persona_config = EXCLUDED.persona_config,
    dialogue_structure = EXCLUDED.dialogue_structure,
    target_competencies = EXCLUDED.target_competencies,
    maps_rubric = EXCLUDED.maps_rubric,
    maps_framework_alignment = EXCLUDED.maps_framework_alignment,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();"""

    return sql

def generate_seed_script(module_path, output_path):
    """Generate a complete seed script for a module."""

    with open(module_path, 'r', encoding='utf-8') as f:
        module = json.load(f)

    code = module.get('code', 'unknown')
    title = module.get('title', 'Unknown')
    content_type = module.get('content_type', 'shared')

    header = f"""-- supabase/seed/seed_{code}.sql
-- MAPS Practice Module: {title}
-- Content Type: {content_type}
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
-- SELECT code, title, content_type, mi_focus_area, difficulty_level, estimated_minutes, is_active
-- FROM mi_practice_modules
-- WHERE code = '{code}';
"""

    sql_insert = json_to_sql_insert(module)

    full_script = header + sql_insert + footer

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_script)

    return code, title, content_type

def generate_learning_pathways_seed():
    """Generate seed script for learning pathways."""
    pathways_path = Path("C:/builds/MAPS/src/data/learning_pathways.json")
    seed_dir = Path("C:/builds/MAPS/supabase/seed")

    if not pathways_path.exists():
        print("[SKIP] learning_pathways.json not found")
        return

    with open(pathways_path, 'r', encoding='utf-8') as f:
        pathways_data = json.load(f)

    output_path = seed_dir / "seed_learning_pathways.sql"

    header = """-- supabase/seed/seed_learning_pathways.sql
-- MAPS Learning Pathways Configuration
--
-- Usage:
--   supabase db execute --file supabase/seed/seed_learning_pathways.sql
-- Or paste into Supabase SQL Editor

-- ============================================
-- INSERT LEARNING PATHWAYS
-- ============================================

"""

    # Generate SQL for each pathway
    pathway_sqls = []
    for pathway_key, pathway in pathways_data.get('pathways', {}).items():
        pathway_json = json.dumps(pathway)
        sql = f"""INSERT INTO mi_learning_pathways (id, pathway_data)
VALUES (
    '{pathway.get('id', pathway_key)}',
    '{escape_single_quotes(pathway_json)}'::jsonb
) ON CONFLICT (id) DO UPDATE SET
    pathway_data = EXCLUDED.pathway_data,
    updated_at = NOW();"""
        pathway_sqls.append(sql)

    footer = """

-- ============================================
-- VERIFICATION QUERY
-- ============================================
-- Uncomment to verify insertion:
-- SELECT id, pathway_data->>'name' as name, pathway_data->>'target_audience' as audience
-- FROM mi_learning_pathways;
"""

    full_script = header + '\n\n'.join(pathway_sqls) + footer

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(full_script)

    print(f"[OK] Created: seed_learning_pathways.sql")

def main():
    modules_dir = Path("C:/builds/MAPS/src/data/mi_modules")
    seed_dir = Path("C:/builds/MAPS/supabase/seed")

    # Ensure seed directory exists
    seed_dir.mkdir(parents=True, exist_ok=True)

    # Find new module files (shared_*, customer_*, colleague_*)
    module_files = []
    for pattern in ['shared_*.json', 'customer_*.json', 'colleague_*.json']:
        module_files.extend(modules_dir.glob(pattern))

    # Sort for consistent output
    module_files = sorted(module_files)

    print(f"Found {len(module_files)} modules")
    print("=" * 70)

    for module_file in module_files:
        # Generate seed script filename from module code
        with open(module_file, 'r', encoding='utf-8') as f:
            module = json.load(f)
        code = module.get('code', module_file.stem)
        output_name = f"seed_{code}.sql"
        output_path = seed_dir / output_name

        code_out, title, content_type = generate_seed_script(module_file, output_path)
        type_indicator = {'shared': '[SHARED]', 'customer_facing': '[CUSTOMER]', 'colleague_facing': '[COLLEAGUE]'}.get(content_type, '[?]')
        print(f"{type_indicator} Created: {output_name}")
        print(f"  Code: {code_out}")
        print(f"  Title: {title[:70]}...")
        print()

    # Generate learning pathways seed
    print("-" * 70)
    generate_learning_pathways_seed()

    print("=" * 70)
    print(f"Generated {len(module_files)} module seed scripts + 1 pathways script in {seed_dir}")
    print()
    print("Next steps:")
    print("  1. Review generated scripts in supabase/seed/")
    print("  2. Run scripts individually or batch import:")
    print("     supabase db execute --file supabase/seed/seed_*.sql")
    print("  3. Verify in Supabase SQL Editor:")
    print("     SELECT code, title, content_type FROM mi_practice_modules;")

if __name__ == "__main__":
    main()

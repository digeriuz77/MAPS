#!/usr/bin/env python3
"""
JSON Module Seeder for MAPS MI Training Platform

This script seeds MI practice modules directly from JSON files
rather than parsing SQL seed files. It's more reliable and handles
complex JSONB data properly.

Usage:
    python scripts/seed_from_json.py [--verify] [--seed]

Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Service role key for admin operations
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed")

from supabase import create_client, Client


class JSONModuleSeeder:
    """Seed MI practice modules from JSON files"""

    def __init__(self, supabase_url: str, service_key: str):
        self.client: Client = create_client(supabase_url, service_key)
        self.modules_dir = project_root / "src" / "data" / "mi_modules"
        self.learning_paths_file = project_root / "src" / "data" / "learning_pathways.json"

    def verify_database(self) -> Dict[str, Any]:
        """Check current database state"""
        print("\n" + "="*60)
        print("DATABASE VERIFICATION")
        print("="*60)

        try:
            # Check if content_type column exists
            modules = self.client.table('mi_practice_modules').select('*').limit(1).execute()

            # Get counts
            all_modules = self.client.table('mi_practice_modules').select('id', count='exact').execute()
            module_count = all_modules.count if hasattr(all_modules, 'count') else 0

            all_paths = self.client.table('mi_learning_paths').select('id', count='exact').execute()
            path_count = all_paths.count if hasattr(all_paths, 'count') else 0

            print(f"\nModules in database: {module_count}")
            print(f"Learning paths in database: {path_count}")

            # Check for content_type column
            if module_count > 0:
                sample = all_modules.data[0] if all_modules.data else {}
                has_content_type = 'content_type' in sample
                print(f"Has content_type column: {has_content_type}")

                # Get content type distribution
                if has_content_type:
                    modules_with_ct = self.client.table('mi_practice_modules').select('content_type').execute()
                    ct_dist = {}
                    for m in modules_with_ct.data:
                        ct = m.get('content_type', 'unknown')
                        ct_dist[ct] = ct_dist.get(ct, 0) + 1
                    print(f"\nContent type distribution:")
                    for ct, count in sorted(ct_dist.items()):
                        print(f"  - {ct}: {count}")

            return {
                "modules": module_count,
                "paths": path_count,
                "has_content_type": module_count > 0 and 'content_type' in (all_modules.data[0] if all_modules.data else {})
            }

        except Exception as e:
            print(f"Error during verification: {e}")
            return {"error": str(e)}

    def seed_modules_from_json(self) -> List[Dict[str, Any]]:
        """Seed modules from JSON files in src/data/mi_modules/"""
        print("\n" + "="*60)
        print("SEEDING MODULES FROM JSON")
        print("="*60)

        if not self.modules_dir.exists():
            print(f"Error: Modules directory not found: {self.modules_dir}")
            return [{"error": f"Directory not found: {self.modules_dir}"}]

        results = []
        json_files = sorted(self.modules_dir.glob("*.json"))

        print(f"\nFound {len(json_files)} JSON module files\n")

        for i, json_file in enumerate(json_files, 1):
            try:
                module_data = json.loads(json_file.read_text(encoding='utf-8'))

                # Prepare data for Supabase
                insert_data = {
                    "code": module_data.get("code"),
                    "title": module_data.get("title"),
                    "content_type": module_data.get("content_type", "shared"),
                    "mi_focus_area": module_data.get("mi_focus_area"),
                    "difficulty_level": module_data.get("difficulty_level", "beginner"),
                    "estimated_minutes": module_data.get("estimated_minutes", 5),
                    "learning_objective": module_data.get("learning_objective"),
                    "scenario_context": module_data.get("scenario_context"),
                    "persona_config": module_data.get("persona_config"),
                    "dialogue_structure": module_data.get("dialogue_structure"),
                    "target_competencies": module_data.get("target_competencies", []),
                    "maps_rubric": module_data.get("maps_rubric"),
                    "maps_framework_alignment": module_data.get("maps_framework_alignment"),
                    "is_active": module_data.get("is_active", True)
                }

                # Remove None values
                insert_data = {k: v for k, v in insert_data.items() if v is not None}

                # Insert using ON CONFLICT to handle duplicates
                result = self.client.table('mi_practice_modules').upsert(
                    insert_data,
                    on_conflict="code"
                ).execute()

                print(f"[{i}/{len(json_files)}] [OK] {module_data.get('code', json_file.name)}")
                results.append({"success": True, "file": json_file.name, "code": module_data.get("code")})

            except Exception as e:
                print(f"[{i}/{len(json_files)}] [FAIL] {json_file.name}: {e}")
                results.append({"error": str(e), "file": json_file.name})

        return results

    def seed_learning_paths_from_json(self) -> Dict[str, Any]:
        """Seed learning pathways from JSON file"""
        print("\n" + "="*60)
        print("SEEDING LEARNING PATHWAYS")
        print("="*60)

        if not self.learning_paths_file.exists():
            print(f"Error: Learning pathways file not found: {self.learning_paths_file}")
            return {"error": f"File not found: {self.learning_paths_file}"}

        try:
            content = json.loads(self.learning_paths_file.read_text(encoding='utf-8'))

            # Handle different JSON structures
            # The learning_pathways.json has {pathways: {id: {...}, ...}, module_index: {...}, ...}
            if isinstance(content, dict) and 'pathways' in content:
                pathways_dict = content['pathways']
                # Convert dict values to list
                pathways_data = list(pathways_dict.values())
            elif isinstance(content, list):
                pathways_data = content
            else:
                print(f"Error: Unexpected JSON format - expected dict with 'pathways' key or list")
                return {"error": "Invalid format: expected dict with 'pathways' key or list"}

            print(f"\nFound {len(pathways_data)} learning pathways\n")

            seeded = 0
            for i, pathway in enumerate(pathways_data, 1):
                try:
                    # Prepare data - handle different JSON structures
                    insert_data = {
                        "code": pathway.get("code", f"path-{i:03d}"),
                        "title": pathway.get("title", "Untitled Path"),
                        "description": pathway.get("description"),
                        "module_sequence": pathway.get("module_sequence", []),
                        "target_audience": pathway.get("target_audience"),
                        "estimated_total_minutes": pathway.get("estimated_total_minutes"),
                        "maps_competencies_targeted": pathway.get("maps_competencies_targeted", []),
                        "pathway_data": pathway,  # Store full pathway data
                        "is_active": True
                    }

                    # Remove None values
                    insert_data = {k: v for k, v in insert_data.items() if v is not None}

                    self.client.table('mi_learning_paths').upsert(
                        insert_data,
                        on_conflict="code"
                    ).execute()

                    print(f"[{i}/{len(pathways_data)}] [OK] {pathway.get('title', 'Path ' + str(i))}")
                    seeded += 1

                except Exception as e:
                    print(f"[{i}/{len(pathways_data)}] [FAIL] {pathway.get('title', 'Path ' + str(i))}: {e}")

            return {"success": True, "seeded": seeded}

        except Exception as e:
            print(f"Error loading learning pathways: {e}")
            return {"error": str(e)}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Seed MAPS database from JSON files")
    parser.add_argument('--verify', action='store_true', help='Verify database state')
    parser.add_argument('--seed', action='store_true', help='Seed modules and pathways')
    parser.add_argument('--all', action='store_true', help='Verify then seed')

    args = parser.parse_args()

    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        sys.exit(1)

    seeder = JSONModuleSeeder(supabase_url, service_key)

    if args.verify or args.all:
        seeder.verify_database()

    if args.seed or args.all:
        print("\nIMPORTANT: Make sure you've run the migration first!")
        print("Run the SQL in: supabase/migrations/current/MIGRATION_TO_RUN_MANUALLY.sql")
        print("\nStarting seeding...")

        seeder.seed_modules_from_json()
        seeder.seed_learning_paths_from_json()

        print("\n" + "="*60)
        print("FINAL VERIFICATION")
        print("="*60)
        seeder.verify_database()


if __name__ == "__main__":
    main()

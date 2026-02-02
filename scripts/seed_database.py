#!/usr/bin/env python3
"""
Remote Database Seeder for MAPS MI Training Platform

This script seeds the Supabase database using the Supabase Python client.
It reads seed SQL files and executes them via the Supabase REST API.

Usage:
    python scripts/seed_database.py [--modules] [--paths] [--profiles] [--scenarios] [--all]

Environment variables required:
    - SUPABASE_URL: Your Supabase project URL
    - SUPABASE_SERVICE_ROLE_KEY: Service role key for admin operations
"""

import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from supabase import create_client, Client
except ImportError:
    print("Error: supabase-py not installed. Run: pip install supabase")
    sys.exit(1)

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_path = project_root / ".env"
    if env_path.exists():
        load_dotenv(env_path)
        print(f"Loaded environment from {env_path}")
except ImportError:
    print("Warning: python-dotenv not installed. Using system environment variables only.")


class DatabaseSeeder:
    """Handles remote database seeding via Supabase client"""

    def __init__(self, supabase_url: str, service_key: str):
        """Initialize Supabase client with service role credentials"""
        self.client: Client = create_client(supabase_url, service_key)
        self.seed_dir = project_root / "supabase" / "seed"

    def execute_sql(self, sql: str) -> dict:
        """
        Execute raw SQL via Supabase RPC

        Note: This uses the Supabase REST API which has limitations on SQL execution.
        For complex SQL, we parse and convert to API calls.
        """
        # Try using the RPC endpoint for raw SQL
        try:
            result = self.client.table('_debug').select('*').execute()
            return result
        except Exception as e:
            return {"error": str(e)}

    def insert_module_from_seed_file(self, seed_file: Path) -> dict:
        """
        Parse a module seed SQL file and insert via Supabase client

        Seed files have format like:
        INSERT INTO mi_practice_modules (...) VALUES (...);
        """
        try:
            sql_content = seed_file.read_text()

            # Extract the VALUES part using regex
            # Match: INSERT INTO mi_practice_modules (...) VALUES (...);
            pattern = r"INSERT INTO mi_practice_modules\s*\((.*?)\)\s*VALUES\s*\((.*?)\);"
            match = re.search(pattern, sql_content, re.DOTALL)

            if not match:
                return {"error": f"Could not parse INSERT statement in {seed_file.name}", "file": str(seed_file)}

            columns = [col.strip() for col in match.group(1).split(',')]
            values_str = match.group(2).strip()

            # Parse JSONB values (they're in the SQL as '::jsonb' strings)
            # We need to extract the actual JSON values
            module_data = {}

            # Simple regex-based parser for the values
            # This handles strings, numbers, and JSONB objects
            value_regex = r"""
                (?:
                    '.*?(?:(?:'')|[^'])*'  |  # String literal (with escaped quotes)
                    \{.*?\}                 |  # JSON object
                    \[.*?\]                 |  # JSON array
                    [^,]+                      # Other values (numbers, NULL, etc.)
                )
            """
            values = re.findall(value_regex, values_str, re.VERBOSE | re.DOTALL)

            for i, col in enumerate(columns):
                if i < len(values):
                    val = values[i].strip()

                    # Remove trailing ::jsonb, ::uuid, etc.
                    val = re.sub(r'::[a-z_]+$', '', val)

                    # Handle string literals
                    if val.startswith("'") and val.endswith("'"):
                        # Remove quotes and unescape
                        val = val[1:-1].replace("''", "'")
                        module_data[col] = val
                    # Handle JSON objects/arrays
                    elif val.startswith("{") or val.startswith("["):
                        try:
                            import json
                            module_data[col] = json.loads(val)
                        except json.JSONDecodeError:
                            module_data[col] = val
                    # Handle NULL
                    elif val.upper() == "NULL":
                        module_data[col] = None
                    # Handle boolean
                    elif val.upper() in ("TRUE", "FALSE"):
                        module_data[col] = val.upper() == "TRUE"
                    # Handle numbers (remove quotes if present)
                    else:
                        try:
                            module_data[col] = int(val)
                        except ValueError:
                            try:
                                module_data[col] = float(val)
                            except ValueError:
                                module_data[col] = val

            # Remove id if present (let database generate it)
            module_data.pop('id', None)

            # Insert via Supabase client
            result = self.client.table('mi_practice_modules').insert(module_data).execute()

            return {
                "success": True,
                "file": seed_file.name,
                "code": module_data.get('code', 'unknown'),
                "title": module_data.get('title', 'unknown')
            }

        except Exception as e:
            return {
                "error": str(e),
                "file": str(seed_file),
                "traceback": str(e)
            }

    def seed_modules(self, pattern: str = "seed_*.sql") -> List[dict]:
        """
        Seed MI practice modules from individual seed files

        Args:
            pattern: Glob pattern for seed files (default: seed_*.sql)

        Returns:
            List of results for each module
        """
        results = []

        # Find all module seed files (exclude seed_all.sql, seed_mi_modules.sql)
        seed_files = sorted(self.seed_dir.glob(pattern))

        # Filter out the aggregate files
        exclude_files = {
            "seed_all.sql",
            "seed_mi_modules.sql",
            "seed_learning_paths.sql",
            "seed_profiles.sql",
            "seed_scenarios.sql"
        }

        module_files = [f for f in seed_files if f.name not in exclude_files]

        print(f"\n{'='*60}")
        print(f"Seeding {len(module_files)} MI Practice Modules")
        print(f"{'='*60}\n")

        for i, seed_file in enumerate(module_files, 1):
            print(f"[{i}/{len(module_files)}] Seeding: {seed_file.name}...", end=" ")
            result = self.insert_module_from_seed_file(seed_file)

            if "error" in result:
                print(f"[X] FAILED")
                print(f"  Error: {result['error']}")
            else:
                print(f"[OK] {result.get('code', 'N/A')}")

            results.append(result)

        return results

    def seed_learning_paths(self) -> dict:
        """Seed learning pathways from seed_learning_paths.sql"""
        seed_file = self.seed_dir / "seed_learning_paths.sql"

        if not seed_file.exists():
            return {"error": "seed_learning_paths.sql not found"}

        print(f"\n{'='*60}")
        print(f"Seeding Learning Pathways")
        print(f"{'='*60}\n")

        try:
            sql_content = seed_file.read_text()

            # Parse INSERT statements for learning paths
            # Pattern: INSERT INTO mi_learning_paths (...) VALUES (...);
            pattern = r"INSERT INTO mi_learning_paths\s*\((.*?)\)\s*VALUES\s*\((.*?)\);"
            matches = re.findall(pattern, sql_content, re.DOTALL)

            paths_seeded = 0
            for i, match in enumerate(matches, 1):
                columns = [col.strip() for col in match[0].split(',')]
                values_str = match[1].strip()

                # Parse values (similar to module parsing)
                import json
                value_regex = r"""
                    (?:
                        '.*?(?:(?:'')|[^'])*'  |  # String literal
                        \{.*?\}                 |  # JSON object
                        \[.*?\]                 |  # JSON array
                        [^,]+                      # Other values
                    )
                """
                values = re.findall(value_regex, values_str, re.VERBOSE | re.DOTALL)

                path_data = {}
                for j, col in enumerate(columns):
                    if j < len(values):
                        val = values[j].strip()
                        val = re.sub(r'::[a-z_]+$', '', val)

                        if val.startswith("'") and val.endswith("'"):
                            val = val[1:-1].replace("''", "'")
                            path_data[col] = val
                        elif val.startswith("{") or val.startswith("["):
                            path_data[col] = json.loads(val)
                        elif val.upper() == "NULL":
                            path_data[col] = None
                        elif val.upper() in ("TRUE", "FALSE"):
                            path_data[col] = val.upper() == "TRUE"
                        else:
                            try:
                                path_data[col] = int(val)
                            except ValueError:
                                try:
                                    path_data[col] = float(val)
                                except ValueError:
                                    path_data[col] = val

                path_data.pop('id', None)

                result = self.client.table('mi_learning_paths').insert(path_data).execute()
                paths_seeded += 1
                print(f"[{i}/{len(matches)}] Seeded: {path_data.get('code', 'N/A')}")

            return {
                "success": True,
                "paths_seeded": paths_seeded
            }

        except Exception as e:
            return {"error": str(e), "traceback": str(e)}

    def verify_seeding(self) -> dict:
        """Verify that seeding was successful by checking counts"""
        print(f"\n{'='*60}")
        print(f"Verifying Seeding")
        print(f"{'='*60}\n")

        try:
            # Get module count
            modules_result = self.client.table('mi_practice_modules').select('id', count='exact').execute()
            module_count = modules_result.count if hasattr(modules_result, 'count') else len(modules_result.data)

            # Get learning path count
            paths_result = self.client.table('mi_learning_paths').select('id', count='exact').execute()
            path_count = paths_result.count if hasattr(paths_result, 'count') else len(paths_result.data)

            # Get content type distribution
            modules = self.client.table('mi_practice_modules').select('content_type').execute()

            content_types = {}
            for module in modules.data:
                ct = module.get('content_type', 'unknown')
                content_types[ct] = content_types.get(ct, 0) + 1

            print(f"Modules seeded: {module_count}")
            print(f"Learning paths seeded: {path_count}")
            print(f"\nContent type distribution:")
            for ct, count in sorted(content_types.items()):
                print(f"  - {ct}: {count}")

            return {
                "modules": module_count,
                "learning_paths": path_count,
                "content_types": content_types
            }

        except Exception as e:
            return {"error": str(e)}


def main():
    parser = argparse.ArgumentParser(description="Seed MAPS database remotely via Supabase")
    parser.add_argument('--modules', action='store_true', help='Seed MI practice modules')
    parser.add_argument('--paths', action='store_true', help='Seed learning pathways')
    parser.add_argument('--verify', action='store_true', help='Verify existing data')
    parser.add_argument('--all', action='store_true', help='Seed everything')

    args = parser.parse_args()

    # Get Supabase credentials from environment
    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables required")
        print("\nSet them in your .env file or export them:")
        print("  export SUPABASE_URL='your-project-url'")
        print("  export SUPABASE_SERVICE_ROLE_KEY='your-service-role-key'")
        sys.exit(1)

    # Create seeder
    seeder = DatabaseSeeder(supabase_url, service_key)

    # Verify only
    if args.verify:
        result = seeder.verify_seeding()
        return

    # Seed everything if --all specified
    if args.all:
        args.modules = True
        args.paths = True

    # Execute seeding
    if args.modules:
        results = seeder.seed_modules()
        success = sum(1 for r in results if 'error' not in r)
        print(f"\n{'='*60}")
        print(f"Module Seeding Complete: {success}/{len(results)} succeeded")
        print(f"{'='*60}")

    if args.paths:
        result = seeder.seed_learning_paths()
        if 'error' in result:
            print(f"Error seeding paths: {result['error']}")
        else:
            print(f"{'='*60}")
            print(f"Pathway Seeding Complete: {result.get('paths_seeded', 0)} paths seeded")
            print(f"{'='*60}")

    # Always verify at the end
    if args.modules or args.paths:
        seeder.verify_seeding()


if __name__ == "__main__":
    main()

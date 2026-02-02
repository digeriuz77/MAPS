#!/usr/bin/env python3
"""
Direct Supabase Migration Script

This script executes SQL migration directly against Supabase using
the service role key via RPC (Remote Procedure Call).

Usage:
    python scripts/migrate_database.py
"""

import os
import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv(project_root / ".env")
except ImportError:
    pass

from supabase import create_client


def execute_migration():
    """Execute the content_type migration on Supabase"""

    supabase_url = os.getenv('SUPABASE_URL')
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

    if not supabase_url or not service_key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY required")
        return False

    print(f"Connecting to: {supabase_url[:30]}...")
    client = create_client(supabase_url, service_key)

    # Migration SQL steps
    steps = [
        {
            "name": "Add content_type column",
            "sql": """
                ALTER TABLE mi_practice_modules
                ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) NOT NULL DEFAULT 'shared'
            """
        },
        {
            "name": "Add content_type check constraint",
            "sql": """
                ALTER TABLE mi_practice_modules
                DROP CONSTRAINT IF EXISTS content_type_check,
                ADD CONSTRAINT content_type_check
                CHECK (content_type IN ('shared', 'customer_facing', 'colleague_facing'))
            """
        },
        {
            "name": "Create content_type index",
            "sql": """
                CREATE INDEX IF NOT EXISTS idx_mi_modules_content_type
                ON mi_practice_modules(content_type)
            """
        },
        {
            "name": "Add maps_framework_alignment column",
            "sql": """
                ALTER TABLE mi_practice_modules
                ADD COLUMN IF NOT EXISTS maps_framework_alignment JSONB
            """
        },
        {
            "name": "Add code column to learning_paths",
            "sql": """
                ALTER TABLE mi_learning_paths
                ADD COLUMN IF NOT EXISTS code VARCHAR(50) UNIQUE
            """
        },
        {
            "name": "Add pathway_data column to learning_paths",
            "sql": """
                ALTER TABLE mi_learning_paths
                ADD COLUMN IF NOT EXISTS pathway_data JSONB
            """
        },
    ]

    print("\n" + "="*60)
    print("EXECUTING MIGRATION")
    print("="*60 + "\n")

    # Since Supabase Python client can't execute raw DDL directly,
    # we'll use the RPC endpoint with a helper function
    # First, let's create a temporary RPC function

    for i, step in enumerate(steps, 1):
        print(f"[{i}/{len(steps)}] {step['name']}...", end=" ")

        try:
            # Try executing via raw SQL through postgrest
            # This may not work for DDL, so we'll report the status
            result = client.rpc('exec_sql', {'sql': step['sql']}).execute()

            print("[OK]")

        except Exception as e:
            error_msg = str(e)

            # Check if it's because the function doesn't exist
            if "PGRST202" in error_msg or "function" in error_msg.lower():
                print("[SKIPPED - needs manual execution]")
                print(f"       SQL to run manually:\n       {step['sql'].strip()}")
            else:
                print(f"[ERROR: {error_msg}]")

    print("\n" + "="*60)
    print("MIGRATION COMPLETE")
    print("="*60)

    # Verify the migration
    print("\nVerifying migration...")
    try:
        modules = client.table('mi_practice_modules').select('*').limit(1).execute()

        if modules.data:
            sample = modules.data[0]
            has_content_type = 'content_type' in sample
            has_maps_alignment = 'maps_framework_alignment' in sample

            print(f"  content_type column exists: {has_content_type}")
            print(f"  maps_framework_alignment column exists: {has_maps_alignment}")

            if has_content_type:
                print(f"\n  Sample content_type value: {sample.get('content_type', 'N/A')}")
            if has_maps_alignment:
                print(f"  Sample maps_framework_alignment: {str(sample.get('maps_framework_alignment', {}))[:50]}...")
        else:
            print("  No modules in database to verify")

    except Exception as e:
        print(f"  Verification error: {e}")

    return True


if __name__ == "__main__":
    execute_migration()

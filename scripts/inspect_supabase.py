#!/usr/bin/env python3
"""
Inspect Supabase database to understand current state
Shows all tables, their structure, and data
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime

# Add the project root to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.dependencies import get_supabase_client
from src.config.settings import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def inspect_table(supabase, table_name, description=""):
    """Inspect a single table and show its contents"""
    print(f"\n{'='*50}")
    print(f"TABLE: {table_name}")
    if description:
        print(f"Description: {description}")
    print('='*50)

    try:
        # Get all data from table
        response = supabase.table(table_name).select('*').execute()

        if response.data:
            print(f"Found {len(response.data)} records:")
            for i, record in enumerate(response.data):
                print(f"\n--- Record {i+1} ---")
                for key, value in record.items():
                    # Pretty print the value
                    if isinstance(value, dict) or isinstance(value, list):
                        value_str = json.dumps(value, indent=2)
                    elif isinstance(value, str) and len(value) > 100:
                        value_str = value[:100] + "..."
                    else:
                        value_str = str(value)

                    print(f"{key:20}: {value_str}")
        else:
            print("No records found in this table")

    except Exception as e:
        print(f"ERROR accessing table {table_name}: {e}")

def main():
    """Main inspection function"""
    print("=== SUPABASE DATABASE INSPECTION ===")

    try:
        settings = get_settings()
        supabase = get_supabase_client()
        print(f"Connected to Supabase URL: {settings.SUPABASE_URL[:50]}...")

        # Tables we expect based on our migrations
        tables_to_inspect = [
            ("conversations", "Main conversations table with persona seeds"),
            ("mi_analysis", "MI technique analysis results"),
            ("persona_responses", "Generated persona responses"),
            ("quality_patterns", "Quality patterns and tracking"),
        ]

        for table_name, description in tables_to_inspect:
            inspect_table(supabase, table_name, description)

        # Also try some tables that might exist from legacy systems
        print(f"\n{'='*50}")
        print("CHECKING FOR LEGACY TABLES")
        print('='*50)

        legacy_tables = ["personas", "users", "sessions", "messages"]
        for table_name in legacy_tables:
            try:
                response = supabase.table(table_name).select('*').limit(1).execute()
                print(f"✓ Found legacy table: {table_name}")
            except Exception:
                print(f"✗ No table: {table_name}")

        print(f"\n{'='*50}")
        print("SUMMARY")
        print('='*50)
        print("This shows what's currently in your Supabase database.")
        print("Look for:")
        print("1. Where persona information is stored")
        print("2. What persona_seed values exist")
        print("3. If the tables match our expected schema")
        print("4. Any hardcoded data that needs updating")

    except Exception as e:
        print(f"FAILED to inspect database: {e}")
        return False

if __name__ == "__main__":
    main()
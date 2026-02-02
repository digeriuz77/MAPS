#!/usr/bin/env python3
"""
Supabase SQL Executor via HTTP

Uses Supabase's internal SQL endpoint to execute migrations.
This requires the service role key which has admin privileges.
"""

import os
import sys
import requests
import json
from pathlib import Path

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Extract project reference
project_ref = SUPABASE_URL.split('https://')[1].split('.')[0]

# Supabase SQL API endpoint (internal)
SQL_ENDPOINT = f"https://{project_ref}.supabase.co/rest/v1/rpc/exec_sql"

print(f"Project: {project_ref}")
print(f"Endpoint: {SQL_ENDPOINT}")

headers = {
    'apikey': SERVICE_KEY,
    'Authorization': f'Bearer {SERVICE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=representation'
}

# Migration SQL
migration_sql = """
-- Add content_type column
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) NOT NULL DEFAULT 'shared';

-- Add constraint
ALTER TABLE mi_practice_modules
    DROP CONSTRAINT IF EXISTS content_type_check;

ALTER TABLE mi_practice_modules
    ADD CONSTRAINT content_type_check
    CHECK (content_type IN ('shared', 'customer_facing', 'colleague_facing'));

-- Create index
CREATE INDEX IF NOT EXISTS idx_mi_modules_content_type
    ON mi_practice_modules(content_type);

-- Add maps_framework_alignment column
ALTER TABLE mi_practice_modules
    ADD COLUMN IF NOT EXISTS maps_framework_alignment JSONB;

-- Update learning_paths table
ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS code VARCHAR(50) UNIQUE;

ALTER TABLE mi_learning_paths
    ADD COLUMN IF NOT EXISTS pathway_data JSONB;
"""

print("\nAttempting to execute migration via HTTP...")

# Try using the Supabase SQL API
try:
    response = requests.post(
        SQL_ENDPOINT,
        headers=headers,
        json={'sql': migration_sql}
    )

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        print("Migration executed successfully!")
        print(f"Response: {response.text[:200]}")
    else:
        print(f"Error: {response.text}")

except Exception as e:
    print(f"Exception: {e}")

print("\n" + "="*60)
print("If the automatic migration failed, please run the SQL manually:")
print("="*60)
print(f"\n1. Go to: https://supabase.com/dashboard/project/{project_ref}/sql")
print("2. Paste and execute the migration SQL from:")
print("   supabase/migrations/current/MIGRATION_TO_RUN_MANUALLY.sql")

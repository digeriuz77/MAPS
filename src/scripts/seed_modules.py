
import os
import json
import glob
import asyncio
from typing import List, Dict, Any
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set in .env")
    print(f"Looking for .env at: {env_path}")
    print(f"Current vars: URL={bool(SUPABASE_URL)}, KEY={bool(SUPABASE_KEY)}")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "mi_modules")

async def seed_modules():
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    
    # Get all JSON files
    json_files = glob.glob(os.path.join(DATA_DIR, "*.json"))
    print(f"Found {len(json_files)} module files in {DATA_DIR}")

    success_count = 0
    error_count = 0

    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                module_data = json.load(f)

            # Validate required fields (basic check)
            required_fields = ['id', 'code', 'title', 'content_type', 'mi_focus_area']
            if not all(field in module_data for field in required_fields):
                print(f"Skipping {os.path.basename(file_path)}: Missing required fields")
                continue

            # Ensure dialogue_structure is a dict, not a string (common issue)
            if isinstance(module_data.get('dialogue_structure'), str):
                 try:
                     module_data['dialogue_structure'] = json.loads(module_data['dialogue_structure'])
                 except:
                     pass # Leave as is if not valid JSON string

            # Prepare data for upset
            # We filter out specific keys if they don't match the DB schema, 
            # but based on the JSON file viewed, it maps 1:1 to the DB columns inferred from mi_module_service.py
            
            # Upsert into Supabase
            # Using 'code' as the conflict constraint to allow updating existing modules by code
            # We must remove 'id' if we want to rely on the DB's existing ID for that code, 
            # OR ensuring the JSON 'id' matches. Safest is to let DB ID persist if code matches.
            
            # First, check if module exists by code
            existing = supabase.table('mi_practice_modules').select('id').eq('code', module_data['code']).execute()
            if existing.data:
                # Update existing record, preserving its ID
                module_data['id'] = existing.data[0]['id']
            
            # Now upsert
            response = supabase.table('mi_practice_modules').upsert(module_data).execute()
            
            print(f"✅ Seeded: {module_data['code']} - {module_data['title']}")
            success_count += 1

        except Exception as e:
            print(f"❌ Error seeding {os.path.basename(file_path)}: {str(e)}")
            error_count += 1

    print("\n" + "="*30)
    print(f"Seeding Complete")
    print(f"Success: {success_count}")
    print(f"Failed:  {error_count}")
    print("="*30)

if __name__ == "__main__":
    asyncio.run(seed_modules())

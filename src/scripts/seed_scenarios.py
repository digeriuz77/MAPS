
import os
import json
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
load_dotenv(env_path)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"Error: SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_ROLE_KEY) must be set in .env")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DATA_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "scenarios.json")

async def seed_scenarios():
    print(f"Connecting to Supabase at {SUPABASE_URL}...")
    
    if not os.path.exists(DATA_FILE):
        print(f"Error: Data file not found at {DATA_FILE}")
        return

    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            scenarios = json.load(f)

        print(f"Found {len(scenarios)} scenarios to seed.")

        success_count = 0
        error_count = 0

        for scenario in scenarios:
            try:
                # Upsert into Supabase using 'code' as conflict constraint
                # First, check if exists by code to preserve ID
                existing = supabase.table('scenarios').select('id').eq('code', scenario['code']).execute()
                if existing.data:
                    scenario['id'] = existing.data[0]['id']
                
                response = supabase.table('scenarios').upsert(scenario).execute()
                
                print(f"✅ Seeded: {scenario['code']} - {scenario['title']}")
                success_count += 1

            except Exception as e:
                print(f"❌ Error seeding {scenario['code']}: {str(e)}")
                error_count += 1

        print("\n" + "="*30)
        print(f"Scenario Seeding Complete")
        print(f"Success: {success_count}")
        print(f"Failed:  {error_count}")
        print("="*30)

    except Exception as e:
        print(f"Critical Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(seed_scenarios())

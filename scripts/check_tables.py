"""
Check Supabase Tables
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Get all tables
result = supabase.table('information_schema.tables').select(
    'table_name'
).eq('table_schema', 'public').execute()

print("Tables in public schema:")
print("-" * 40)
for table in result.data:
    print(f"  - {table['table_name']}")

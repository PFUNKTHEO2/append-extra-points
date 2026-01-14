"""
Delete female players from Supabase player_rankings table
Run this after deleting from BigQuery
"""

import os
from supabase import create_client

# Get credentials from environment or use defaults
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://bnqgjderzanvqqkozfkn.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_KEY:
    print("ERROR: SUPABASE_SERVICE_ROLE_KEY environment variable not set")
    print("Set it with: set SUPABASE_SERVICE_ROLE_KEY=your_key_here")
    exit(1)

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Delete female players (teams ending with (W))
print("Deleting female players from Supabase...")

try:
    # Delete where current_team contains '(W)'
    result = supabase.table('player_rankings').delete().like('current_team', '%(W)%').execute()

    print(f"Deleted {len(result.data)} female players from Supabase")

except Exception as e:
    print(f"Error: {e}")

print("Done!")

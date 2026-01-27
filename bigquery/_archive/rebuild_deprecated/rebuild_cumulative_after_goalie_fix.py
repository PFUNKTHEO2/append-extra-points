"""
Rebuild player_cumulative_points after Goalie Stats Fix
========================================================
This incorporates the F06, F07, F11, F12 improvements
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

print("="*70)
print("REBUILDING player_cumulative_points")
print("="*70)
print("\nThis will incorporate the goalie stats fixes (F06, F07, F11, F12)")

# Read the SQL file
sql_file = 'rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql'
with open(sql_file, 'r', encoding='utf-8') as f:
    rebuild_sql = f.read()

print(f"\nLoaded SQL from: {sql_file}")
print(f"SQL length: {len(rebuild_sql):,} characters")

# Backup current table first
print("\n[STEP 1] Creating backup of current table...")
backup_query = """
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251208_goalie_fix` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""

try:
    job = client.query(backup_query)
    job.result()
    print("SUCCESS: Backup created")
except Exception as e:
    print(f"ERROR creating backup: {e}")
    sys.exit(1)

# Execute rebuild
print("\n[STEP 2] Rebuilding player_cumulative_points...")
print("This may take a minute...")

try:
    job = client.query(rebuild_sql)
    job.result()
    print("SUCCESS: Table rebuilt")
except Exception as e:
    print(f"ERROR rebuilding table: {e}")
    sys.exit(1)

# Verify results
print("\n[STEP 3] Verifying rebuild...")

verify_query = """
SELECT
  COUNT(*) as total_players,
  COUNTIF(f06_current_gaa > 0) as has_f06,
  COUNTIF(f07_current_svp > 0) as has_f07,
  COUNTIF(f11_last_gaa > 0) as has_f11,
  COUNTIF(f12_last_svp > 0) as has_f12,
  COUNTIF(total_points > 0) as has_any_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""

df = client.query(verify_query).to_dataframe()
print("\nNew Coverage:")
for col in df.columns:
    count = df[col].iloc[0]
    total = df['total_players'].iloc[0]
    if col != 'total_players':
        pct = (count / total) * 100
        print(f"  {col}: {count:,} ({pct:.2f}%)")
    else:
        print(f"  {col}: {count:,}")

# Compare to backup
compare_query = """
SELECT
  'Before Fix' as status,
  COUNT(*) as total_players,
  COUNTIF(f06_current_gaa > 0) as has_f06,
  COUNTIF(f07_current_svp > 0) as has_f07,
  COUNTIF(f11_last_gaa > 0) as has_f11,
  COUNTIF(f12_last_svp > 0) as has_f12
FROM `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251208_goalie_fix`
UNION ALL
SELECT
  'After Fix',
  COUNT(*),
  COUNTIF(f06_current_gaa > 0),
  COUNTIF(f07_current_svp > 0),
  COUNTIF(f11_last_gaa > 0),
  COUNTIF(f12_last_svp > 0)
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""

print("\n" + "-"*70)
print("BEFORE vs AFTER COMPARISON")
print("-"*70)
cmp_df = client.query(compare_query).to_dataframe()
print(cmp_df.to_string(index=False))

print("\n" + "="*70)
print("REBUILD COMPLETE")
print("="*70)

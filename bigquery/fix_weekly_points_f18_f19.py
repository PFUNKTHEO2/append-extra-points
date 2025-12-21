#!/usr/bin/env python3
"""
Fix F18 and F19 Weekly Points Calculation
==========================================
Issue: factor_18_points and factor_19_points store raw counts (1, 2, 3...)
       instead of multiplied values with caps.

Correct calculation per David's NEW ALGORITHM spreadsheet:
- F18: 40 points per goal, capped at 200 (max 5 goals worth)
- F19: 25 points per assist, capped at 125 (max 5 assists worth)

This script:
1. Backs up the existing tables
2. Updates F18 with: LEAST(points_added_this_week * 40, 200)
3. Updates F19 with: LEAST(assists_added_this_week * 25, 125)
4. Rebuilds player_cumulative_points
"""

from google.cloud import bigquery
from datetime import datetime

def main():
    client = bigquery.Client(project='prodigy-ranking')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    print("=" * 70)
    print("FIX F18/F19 WEEKLY POINTS CALCULATION")
    print("=" * 70)

    # Step 1: Show current state
    print("\n[1] Current State Analysis")
    print("-" * 50)

    query_current = """
    SELECT
      'F18 Goals' as factor,
      COUNT(*) as total_records,
      MAX(points_added_this_week) as max_raw_goals,
      MAX(factor_18_points) as current_max_points,
      'Should be: ' || CAST(LEAST(MAX(points_added_this_week) * 40, 200) AS STRING) as correct_max
    FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
    WHERE points_added_this_week > 0

    UNION ALL

    SELECT
      'F19 Assists' as factor,
      COUNT(*) as total_records,
      MAX(assists_added_this_week) as max_raw_assists,
      MAX(factor_19_points) as current_max_points,
      'Should be: ' || CAST(LEAST(MAX(assists_added_this_week) * 25, 125) AS STRING) as correct_max
    FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
    WHERE assists_added_this_week > 0
    """

    result = client.query(query_current).to_dataframe()
    print(result.to_string(index=False))

    # Step 2: Backup current tables
    print(f"\n[2] Creating Backups (timestamp: {timestamp})")
    print("-" * 50)

    backup_f18 = f"""
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta_backup_{timestamp}` AS
    SELECT * FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
    """
    client.query(backup_f18).result()
    print(f"  Backed up PT_F18_weekly_points_delta")

    backup_f19 = f"""
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta_backup_{timestamp}` AS
    SELECT * FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
    """
    client.query(backup_f19).result()
    print(f"  Backed up PT_F19_weekly_assists_delta")

    # Step 3: Fix F18 - Update factor_18_points
    print("\n[3] Fixing F18: 40 pts/goal, max 200")
    print("-" * 50)

    fix_f18 = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta` AS
    SELECT
      player_id,
      player_name,
      position,
      yearofbirth,
      season_slug,
      team_name,
      league_name,
      last_update_date,
      previous_points,
      current_points,
      points_added_this_week,
      games_added_this_week,
      -- FIX: 40 points per goal, capped at 200
      LEAST(CAST(points_added_this_week AS NUMERIC) * 40, 200) AS factor_18_points,
      CURRENT_TIMESTAMP() AS calculated_at,
      'v2.8-fixed-multiplier' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
    """
    client.query(fix_f18).result()
    print("  Updated factor_18_points = LEAST(goals * 40, 200)")

    # Step 4: Fix F19 - Update factor_19_points
    print("\n[4] Fixing F19: 25 pts/assist, max 125")
    print("-" * 50)

    fix_f19 = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta` AS
    SELECT
      player_id,
      player_name,
      position,
      yearofbirth,
      season_slug,
      team_name,
      league_name,
      last_update_date,
      previous_assists,
      current_assists,
      assists_added_this_week,
      games_added_this_week,
      -- FIX: 25 points per assist, capped at 125
      LEAST(CAST(assists_added_this_week AS NUMERIC) * 25, 125) AS factor_19_points,
      CURRENT_TIMESTAMP() AS calculated_at,
      'v2.8-fixed-multiplier' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
    """
    client.query(fix_f19).result()
    print("  Updated factor_19_points = LEAST(assists * 25, 125)")

    # Step 5: Verify the fix
    print("\n[5] Verification - After Fix")
    print("-" * 50)

    query_verify = """
    SELECT
      'F18 Goals' as factor,
      COUNT(*) as total_records,
      MAX(points_added_this_week) as max_raw_goals,
      MAX(factor_18_points) as new_max_points,
      'Expected: 200 (capped)' as expected
    FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
    WHERE points_added_this_week > 0

    UNION ALL

    SELECT
      'F19 Assists' as factor,
      COUNT(*) as total_records,
      MAX(assists_added_this_week) as max_raw_assists,
      MAX(factor_19_points) as new_max_points,
      'Expected: 125 (capped)' as expected
    FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
    WHERE assists_added_this_week > 0
    """

    result_verify = client.query(query_verify).to_dataframe()
    print(result_verify.to_string(index=False))

    # Step 6: Sample of corrected values
    print("\n[6] Sample Corrected Values (Top 10 F18)")
    print("-" * 50)

    sample_f18 = """
    SELECT
      player_name,
      points_added_this_week as goals,
      factor_18_points as points,
      CASE WHEN factor_18_points = 200 THEN 'CAPPED' ELSE '' END as status
    FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
    WHERE points_added_this_week > 0
    ORDER BY points_added_this_week DESC
    LIMIT 10
    """
    sample_result = client.query(sample_f18).to_dataframe()
    print(sample_result.to_string(index=False))

    print("\n" + "=" * 70)
    print("F18/F19 FIX COMPLETE!")
    print("=" * 70)
    print("\nNEXT STEP: Run the rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql")
    print("to update player_cumulative_points with the corrected values.")
    print("\nBackup tables created:")
    print(f"  - PT_F18_weekly_points_delta_backup_{timestamp}")
    print(f"  - PT_F19_weekly_assists_delta_backup_{timestamp}")

if __name__ == "__main__":
    main()

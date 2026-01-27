"""
Fix F09 and Rebuild Cumulative Points
=====================================
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

def execute_query(query, description):
    print(f"\n{'='*70}")
    print(f"EXECUTING: {description}")
    print('='*70)
    try:
        job = client.query(query)
        result = job.result()
        print(f"SUCCESS: {job.num_dml_affected_rows if job.num_dml_affected_rows else 'completed'}")
        return True
    except Exception as e:
        print(f"ERROR: {e}")
        return False

print("="*70)
print("FIX F09 AND REBUILD CUMULATIVE")
print("="*70)

# Step 1: Fix PT_F09_LGPGD with proper type casting
print("\n[STEP 1] Rebuilding PT_F09_LGPGD with type fixes...")

execute_query("""
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F09_LGPGD` AS
WITH current_season_defensemen AS (
  SELECT
    CAST(id AS INT64) as player_id,
    name as player_name,
    position,
    yearOfBirth as birth_year,
    latestStats_season_slug as last_season,
    latestStats_team_name as last_team,
    latestStats_league_name as last_league,
    SAFE_CAST(latestStats_regularStats_GP AS INT64) as games_played,
    SAFE_CAST(latestStats_regularStats_G AS INT64) as goals
  FROM `prodigy-ranking.algorithm.player_stats`
  WHERE yearOfBirth BETWEEN 2007 AND 2011
    AND UPPER(position) = 'D'
    AND SAFE_CAST(latestStats_regularStats_GP AS INT64) >= 5
    AND latestStats_season_slug = '2024-2025'
),
historical_season_defensemen AS (
  SELECT
    CAST(ps.id AS INT64) as player_id,
    ps.name as player_name,
    ps.position,
    ps.yearOfBirth as birth_year,
    '2024-2025' as last_season,
    pss.team_name as last_team,
    pss.league_name as last_league,
    CAST(pss.regularStats_GP AS INT64) as games_played,
    CAST(pss.regularStats_G AS INT64) as goals  -- Cast to INT64
  FROM `prodigy-ranking.algorithm.player_stats` ps
  INNER JOIN `prodigy-ranking.algorithm.player_season_stats_staging` pss
    ON CAST(ps.id AS INT64) = pss.api_player_id
  WHERE ps.yearOfBirth BETWEEN 2007 AND 2011
    AND UPPER(ps.position) = 'D'
    AND ps.latestStats_season_slug = '2025-2026'
    AND pss.season_slug = '2024-2025'
    AND pss.regularStats_GP >= 5
),
all_defensemen AS (
  SELECT * FROM current_season_defensemen
  UNION ALL
  SELECT * FROM historical_season_defensemen
),
best_stats AS (
  SELECT
    player_id,
    MAX(goals) as best_goals
  FROM all_defensemen
  GROUP BY player_id
),
deduped AS (
  SELECT DISTINCT
    ad.player_id,
    ad.player_name,
    ad.position,
    ad.birth_year,
    ad.last_season,
    ad.last_team,
    ad.last_league,
    ad.games_played,
    ad.goals
  FROM all_defensemen ad
  INNER JOIN best_stats bs ON ad.player_id = bs.player_id AND ad.goals = bs.best_goals
),
scored AS (
  SELECT
    *,
    SAFE_DIVIDE(CAST(goals AS FLOAT64), CAST(games_played AS FLOAT64)) as goals_per_game,
    GREATEST(0, LEAST(300,
      CASE
        WHEN games_played IS NULL OR games_played = 0 THEN 0
        WHEN goals IS NULL OR goals = 0 THEN 0
        ELSE (SAFE_DIVIDE(CAST(goals AS FLOAT64), CAST(games_played AS FLOAT64)) / 1.5) * 300
      END
    )) as factor_9_lgpgd_points
  FROM deduped
)
SELECT
  player_id,
  player_name,
  position,
  birth_year,
  last_season,
  last_team,
  last_league,
  games_played,
  goals,
  ROUND(goals_per_game, 3) as goals_per_game,
  ROUND(factor_9_lgpgd_points, 2) as factor_9_lgpgd_points,
  CURRENT_TIMESTAMP() as calculated_at,
  'v2.8-season-fix' as algorithm_version
FROM scored
ORDER BY factor_9_lgpgd_points DESC
""", "Rebuild PT_F09_LGPGD with type fixes")

# Verify F09 fix
verify_f09 = """
SELECT
  COUNT(*) as total_rows,
  COUNTIF(factor_9_lgpgd_points > 0) as with_positive_points,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD_backup_20251208_v2`) as old_count
FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
"""

print("\nF09 Verification:")
df = client.query(verify_f09).to_dataframe()
print(df.to_string(index=False))

# Step 2: Rebuild cumulative points table
print("\n[STEP 2] Rebuilding player_cumulative_points...")

# Read the SQL file
sql_file = 'rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql'
with open(sql_file, 'r', encoding='utf-8') as f:
    rebuild_sql = f.read()

execute_query(rebuild_sql, "Rebuild player_cumulative_points")

# Step 3: Verify final coverage
print("\n[STEP 3] Verifying final coverage...")

final_verify = """
WITH position_counts AS (
  SELECT
    COUNT(*) as total,
    COUNTIF(UPPER(position) = 'F') as forwards,
    COUNTIF(UPPER(position) = 'D') as defensemen,
    COUNTIF(UPPER(position) = 'G') as goalies
  FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
)
SELECT
  'F04 Current Goals (D)' as factor,
  (SELECT COUNTIF(f04_current_goals_d > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) as count,
  (SELECT defensemen FROM position_counts) as expected,
  ROUND((SELECT COUNTIF(f04_current_goals_d > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT defensemen FROM position_counts), 2) as coverage_pct

UNION ALL
SELECT 'F06 Current GAA',
  (SELECT COUNTIF(f06_current_gaa > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`),
  (SELECT goalies FROM position_counts),
  ROUND((SELECT COUNTIF(f06_current_gaa > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT goalies FROM position_counts), 2)

UNION ALL
SELECT 'F07 Current SVP',
  (SELECT COUNTIF(f07_current_svp > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`),
  (SELECT goalies FROM position_counts),
  ROUND((SELECT COUNTIF(f07_current_svp > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT goalies FROM position_counts), 2)

UNION ALL
SELECT 'F09 Last Goals (D)',
  (SELECT COUNTIF(f09_last_goals_d > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`),
  (SELECT defensemen FROM position_counts),
  ROUND((SELECT COUNTIF(f09_last_goals_d > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT defensemen FROM position_counts), 2)

UNION ALL
SELECT 'F11 Last GAA',
  (SELECT COUNTIF(f11_last_gaa > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`),
  (SELECT goalies FROM position_counts),
  ROUND((SELECT COUNTIF(f11_last_gaa > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT goalies FROM position_counts), 2)

UNION ALL
SELECT 'F12 Last SVP',
  (SELECT COUNTIF(f12_last_svp > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`),
  (SELECT goalies FROM position_counts),
  ROUND((SELECT COUNTIF(f12_last_svp > 0) FROM `prodigy-ranking.algorithm_core.player_cumulative_points`) * 100.0 / (SELECT goalies FROM position_counts), 2)
"""

print("\nFinal Coverage (Position-Adjusted):")
print("-"*70)
df2 = client.query(final_verify).to_dataframe()
print(df2.to_string(index=False))

print("\n" + "="*70)
print("REBUILD COMPLETE")
print("="*70)

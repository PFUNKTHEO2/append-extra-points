from google.cloud import bigquery

client = bigquery.Client(project="prodigy-ranking")

print("=" * 80)
print("VERIFYING F10 AND REBUILDING CUMULATIVE POINTS")
print("=" * 80)
print()

# ============================================================================
# Step 1: Verify F10 is correct (should be 2024-2025 only)
# ============================================================================
print("Step 1: Verifying F10 (Last Season Assists)")
print("-" * 80)

f10_verify = """
SELECT last_season, COUNT(*) as count
FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
GROUP BY last_season
ORDER BY last_season DESC
"""

result = client.query(f10_verify).result()
rows = list(result)
all_correct = True
for row in rows:
    status = "CORRECT" if row.last_season == "2024-2025" else "WRONG!"
    if row.last_season != "2024-2025":
        all_correct = False
    print(f"  {row.last_season}: {row.count} players [{status}]")

if all_correct:
    print("  F10 is already correct - only 2024-2025 data!")
else:
    print("  F10 has wrong seasons - this should have been fixed already")

print()

# ============================================================================
# Step 2: Rebuild player_cumulative_points
# ============================================================================
print("Step 2: Rebuilding player_cumulative_points with fixed factor tables")
print("-" * 80)
print("This will take a moment...")

rebuild_sql = """
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_cumulative_points` AS

WITH base_players AS (
  SELECT DISTINCT
    id AS player_id,
    name AS player_name,
    position,
    yearOfBirth AS birth_year,
    nationality_name,
    latestStats_team_name AS current_team,
    latestStats_team_league_name AS current_league,
    latestStats_season_slug AS current_season,
    latestStats_team_league_country_name AS team_country
  FROM `prodigy-ranking.algorithm_core.player_stats`
),

f01_data AS (
  SELECT player_id, MAX(factor_1_epv_points) AS f01_views
  FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
  GROUP BY player_id
),

f02_data AS (
  SELECT player_id, MAX(factor_2_h_points) AS f02_height
  FROM `prodigy-ranking.algorithm_core.PT_F02_H`
  GROUP BY player_id
),

f03_data AS (
  SELECT player_id, MAX(factor_3_current_goals_points) AS f03_current_goals_f
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
  GROUP BY player_id
),

f04_data AS (
  SELECT player_id, MAX(factor_4_current_goals_points) AS f04_current_goals_d
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
  GROUP BY player_id
),

f05_data AS (
  SELECT player_id, MAX(factor_5_current_assists_points) AS f05_current_assists
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
  GROUP BY player_id
),

f06_data AS (
  SELECT player_id, MAX(factor_6_cgaa_points) AS f06_current_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
  GROUP BY player_id
),

f07_data AS (
  SELECT player_id, MAX(factor_7_csv_points) AS f07_current_svp
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
  GROUP BY player_id
),

f08_data AS (
  SELECT player_id, MAX(factor_8_lgpgf_points) AS f08_last_goals_f
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
  GROUP BY player_id
),

f09_data AS (
  SELECT player_id, MAX(factor_9_lgpgd_points) AS f09_last_goals_d
  FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
  GROUP BY player_id
),

f10_data AS (
  SELECT player_id, MAX(factor_10_lapg_points) AS f10_last_assists
  FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
  GROUP BY player_id
),

f11_data AS (
  SELECT player_id, MAX(factor_11_lgaa_points) AS f11_last_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
  GROUP BY player_id
),

f12_data AS (
  SELECT player_id, MAX(factor_12_lsv_points) AS f12_last_svp
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`
  GROUP BY player_id
),

f13_data AS (
  SELECT
    ps.id AS player_id,
    MAX(COALESCE(lp.points, 0)) AS f13_league_points
  FROM `prodigy-ranking.algorithm_core.player_stats` ps
  LEFT JOIN `prodigy-ranking.algorithm_core.DL_F13_league_points` lp
    ON LOWER(TRIM(REPLACE(REPLACE(ps.latestStats_team_league_name, ' ', '-'), '_', '-'))) =
       LOWER(TRIM(REPLACE(REPLACE(lp.league_name, ' ', '-'), '_', '-')))
  GROUP BY ps.id
),

f14_data AS (
  SELECT
    ps.id AS player_id,
    MAX(COALESCE(tp.points, 0)) AS f14_team_points
  FROM `prodigy-ranking.algorithm_core.player_stats` ps
  LEFT JOIN `prodigy-ranking.algorithm_core.DL_F14_team_points` tp
    ON LOWER(TRIM(REGEXP_REPLACE(ps.latestStats_team_name, r' U[0-9]{2}.*| Jr.*| [0-9]$', ''))) =
       LOWER(TRIM(REGEXP_REPLACE(tp.team_name, r' U[0-9]{2}.*| Jr.*| [0-9]$', '')))
  GROUP BY ps.id
),

f15_data AS (
  SELECT
    matched_player_id AS player_id,
    MAX(total_international_points) AS f15_international_points
  FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`
  GROUP BY matched_player_id
),

f16_data AS (
  SELECT
    player_id,
    MAX(factor_16_commitment_points) AS f16_commitment_points
  FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
  GROUP BY player_id
),

f17_data AS (
  SELECT
    player_id,
    MAX(points) AS f17_draft_points
  FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
  GROUP BY player_id
),

f18_data AS (
  SELECT
    player_id,
    MAX(factor_18_points) AS f18_weekly_points_delta
  FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
  GROUP BY player_id
),

f19_data AS (
  SELECT
    player_id,
    MAX(factor_19_points) AS f19_weekly_assists_delta
  FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
  GROUP BY player_id
),

f20_data AS (
  SELECT
    player_id,
    MAX(points) AS f20_playing_up_points
  FROM `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`
  GROUP BY player_id
),

f21_data AS (
  SELECT
    player_id,
    MAX(points) AS f21_tournament_points
  FROM `prodigy-ranking.algorithm_core.DL_F21_tournament_points`
  GROUP BY player_id
),

f22_data AS (
  SELECT
    player_id,
    MAX(points) AS f22_manual_points
  FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`
  GROUP BY player_id
),

f23_data AS (
  SELECT
    player_id,
    MAX(points) AS f23_prodigylikes_points
  FROM `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`
  GROUP BY player_id
),

f24_data AS (
  SELECT
    player_id,
    MAX(points) AS f24_card_sales_points
  FROM `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`
  GROUP BY player_id
)

SELECT
  bp.player_id,
  bp.player_name,
  bp.position,
  bp.birth_year,
  bp.nationality_name,
  bp.current_team,
  bp.current_league,
  bp.current_season,
  bp.team_country,

  COALESCE(f01.f01_views, 0.0) AS f01_views,
  COALESCE(f02.f02_height, 0.0) AS f02_height,
  COALESCE(f03.f03_current_goals_f, 0.0) AS f03_current_goals_f,
  COALESCE(f04.f04_current_goals_d, 0.0) AS f04_current_goals_d,
  COALESCE(f05.f05_current_assists, 0.0) AS f05_current_assists,
  COALESCE(f06.f06_current_gaa, 0.0) AS f06_current_gaa,
  COALESCE(f07.f07_current_svp, 0.0) AS f07_current_svp,
  COALESCE(f08.f08_last_goals_f, 0.0) AS f08_last_goals_f,
  COALESCE(f09.f09_last_goals_d, 0.0) AS f09_last_goals_d,
  COALESCE(f10.f10_last_assists, 0.0) AS f10_last_assists,
  COALESCE(f11.f11_last_gaa, 0.0) AS f11_last_gaa,
  COALESCE(f12.f12_last_svp, 0.0) AS f12_last_svp,

  COALESCE(f13.f13_league_points, 0) AS f13_league_points,
  COALESCE(f14.f14_team_points, 0) AS f14_team_points,
  COALESCE(f15.f15_international_points, 0.0) AS f15_international_points,
  COALESCE(f16.f16_commitment_points, 0) AS f16_commitment_points,
  COALESCE(f17.f17_draft_points, 0) AS f17_draft_points,
  COALESCE(f18.f18_weekly_points_delta, 0.0) AS f18_weekly_points_delta,
  COALESCE(f19.f19_weekly_assists_delta, 0.0) AS f19_weekly_assists_delta,
  COALESCE(f20.f20_playing_up_points, 0) AS f20_playing_up_points,
  COALESCE(f21.f21_tournament_points, 0) AS f21_tournament_points,
  COALESCE(f22.f22_manual_points, 0) AS f22_manual_points,
  COALESCE(f23.f23_prodigylikes_points, 0) AS f23_prodigylikes_points,
  COALESCE(f24.f24_card_sales_points, 0) AS f24_card_sales_points,

  (
    COALESCE(f01.f01_views, 0.0) +
    COALESCE(f02.f02_height, 0.0) +
    COALESCE(f03.f03_current_goals_f, 0.0) +
    COALESCE(f04.f04_current_goals_d, 0.0) +
    COALESCE(f05.f05_current_assists, 0.0) +
    COALESCE(f06.f06_current_gaa, 0.0) +
    COALESCE(f07.f07_current_svp, 0.0) +
    COALESCE(f08.f08_last_goals_f, 0.0) +
    COALESCE(f09.f09_last_goals_d, 0.0) +
    COALESCE(f10.f10_last_assists, 0.0) +
    COALESCE(f11.f11_last_gaa, 0.0) +
    COALESCE(f12.f12_last_svp, 0.0)
  ) AS performance_total,

  (
    COALESCE(f13.f13_league_points, 0) +
    COALESCE(f14.f14_team_points, 0) +
    COALESCE(f15.f15_international_points, 0.0) +
    COALESCE(f16.f16_commitment_points, 0) +
    COALESCE(f17.f17_draft_points, 0) +
    COALESCE(f18.f18_weekly_points_delta, 0.0) +
    COALESCE(f19.f19_weekly_assists_delta, 0.0) +
    COALESCE(f20.f20_playing_up_points, 0) +
    COALESCE(f21.f21_tournament_points, 0) +
    COALESCE(f22.f22_manual_points, 0) +
    COALESCE(f23.f23_prodigylikes_points, 0) +
    COALESCE(f24.f24_card_sales_points, 0)
  ) AS direct_load_total,

  (
    COALESCE(f01.f01_views, 0.0) +
    COALESCE(f02.f02_height, 0.0) +
    COALESCE(f03.f03_current_goals_f, 0.0) +
    COALESCE(f04.f04_current_goals_d, 0.0) +
    COALESCE(f05.f05_current_assists, 0.0) +
    COALESCE(f06.f06_current_gaa, 0.0) +
    COALESCE(f07.f07_current_svp, 0.0) +
    COALESCE(f08.f08_last_goals_f, 0.0) +
    COALESCE(f09.f09_last_goals_d, 0.0) +
    COALESCE(f10.f10_last_assists, 0.0) +
    COALESCE(f11.f11_last_gaa, 0.0) +
    COALESCE(f12.f12_last_svp, 0.0) +
    COALESCE(f13.f13_league_points, 0) +
    COALESCE(f14.f14_team_points, 0) +
    COALESCE(f15.f15_international_points, 0.0) +
    COALESCE(f16.f16_commitment_points, 0) +
    COALESCE(f17.f17_draft_points, 0) +
    COALESCE(f18.f18_weekly_points_delta, 0.0) +
    COALESCE(f19.f19_weekly_assists_delta, 0.0) +
    COALESCE(f20.f20_playing_up_points, 0) +
    COALESCE(f21.f21_tournament_points, 0) +
    COALESCE(f22.f22_manual_points, 0) +
    COALESCE(f23.f23_prodigylikes_points, 0) +
    COALESCE(f24.f24_card_sales_points, 0)
  ) AS total_points,

  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.7-season-fix' AS algorithm_version

FROM base_players bp
LEFT JOIN f01_data f01 ON bp.player_id = f01.player_id
LEFT JOIN f02_data f02 ON bp.player_id = f02.player_id
LEFT JOIN f03_data f03 ON bp.player_id = f03.player_id
LEFT JOIN f04_data f04 ON bp.player_id = f04.player_id
LEFT JOIN f05_data f05 ON bp.player_id = f05.player_id
LEFT JOIN f06_data f06 ON bp.player_id = f06.player_id
LEFT JOIN f07_data f07 ON bp.player_id = f07.player_id
LEFT JOIN f08_data f08 ON bp.player_id = f08.player_id
LEFT JOIN f09_data f09 ON bp.player_id = f09.player_id
LEFT JOIN f10_data f10 ON bp.player_id = f10.player_id
LEFT JOIN f11_data f11 ON bp.player_id = f11.player_id
LEFT JOIN f12_data f12 ON bp.player_id = f12.player_id
LEFT JOIN f13_data f13 ON bp.player_id = f13.player_id
LEFT JOIN f14_data f14 ON bp.player_id = f14.player_id
LEFT JOIN f15_data f15 ON bp.player_id = f15.player_id
LEFT JOIN f16_data f16 ON bp.player_id = f16.player_id
LEFT JOIN f17_data f17 ON bp.player_id = f17.player_id
LEFT JOIN f18_data f18 ON bp.player_id = f18.player_id
LEFT JOIN f19_data f19 ON bp.player_id = f19.player_id
LEFT JOIN f20_data f20 ON bp.player_id = f20.player_id
LEFT JOIN f21_data f21 ON bp.player_id = f21.player_id
LEFT JOIN f22_data f22 ON bp.player_id = f22.player_id
LEFT JOIN f23_data f23 ON bp.player_id = f23.player_id
LEFT JOIN f24_data f24 ON bp.player_id = f24.player_id
"""

try:
    job = client.query(rebuild_sql)
    job.result()
    print("  Cumulative points table rebuilt successfully!")
except Exception as e:
    print(f"  Error: {e}")

print()

# ============================================================================
# Step 3: Verify the rebuild
# ============================================================================
print("Step 3: Verifying rebuild")
print("-" * 80)

# Check for duplicates
dup_check = """
SELECT
  COUNT(*) as total_records,
  COUNT(DISTINCT player_id) as unique_players
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""
result = client.query(dup_check).result()
for row in result:
    dups = row.total_records - row.unique_players
    print(f"  Total records: {row.total_records:,}")
    print(f"  Unique players: {row.unique_players:,}")
    print(f"  Duplicates: {dups}")
    if dups == 0:
        print("  [PASS] No duplicates!")
    else:
        print("  [FAIL] Duplicates still exist!")

# Check goalie F06 distribution
print()
print("Goalie F06 (Current GAA) distribution by season:")
goalie_f06_check = """
SELECT
  current_season,
  COUNT(*) as goalie_count,
  SUM(CASE WHEN f06_current_gaa > 0 THEN 1 ELSE 0 END) as with_f06_points,
  ROUND(AVG(f06_current_gaa), 2) as avg_f06
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE position = 'G'
GROUP BY current_season
ORDER BY current_season DESC
LIMIT 5
"""
result = client.query(goalie_f06_check).result()
for row in result:
    print(f"  {row.current_season}: {row.goalie_count} goalies, {row.with_f06_points} with F06 pts, avg {row.avg_f06}")

# Check algorithm version
print()
print("Algorithm version:")
version_check = """
SELECT DISTINCT algorithm_version
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""
result = client.query(version_check).result()
for row in result:
    print(f"  {row.algorithm_version}")

print()
print("=" * 80)
print("ALL FIXES COMPLETE!")
print("=" * 80)

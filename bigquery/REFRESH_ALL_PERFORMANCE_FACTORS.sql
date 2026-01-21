-- ============================================================================
-- MASTER SCRIPT: REFRESH ALL PERFORMANCE FACTORS (F03-F12)
-- ============================================================================
-- This script refreshes all stats-based performance factors and rebuilds
-- the player_cumulative_points table.
--
-- EXECUTION ORDER:
-- 1. Current Season Factors (F03-F07) - from v_latest_player_stats view
-- 2. Last Season Factors (F08-F12) - from player_season_stats
-- 3. Rebuild player_cumulative_points
-- 4. Rebuild player_cumulative_points_ranked
--
-- USAGE: Run each section separately in BigQuery Console, or execute
--        the individual script files in order.
--
-- LAST UPDATED: 2026-01-21
-- VERSION: v2.5
-- CHANGE: Migrated current season factors to use v_latest_player_stats view
-- ============================================================================


-- ============================================================================
-- PREREQUISITE: CREATE v_latest_player_stats VIEW (if not exists)
-- ============================================================================
-- Run create_v_latest_player_stats.sql first to create the view


-- ============================================================================
-- STEP 1: REFRESH CURRENT SEASON FACTORS (F03-F07)
-- ============================================================================
-- These use v_latest_player_stats view (derived from player_season_stats)
-- joined with player_stats for metadata (name, position, yearOfBirth)

-- F03: Current Goals Per Game - Forwards
-- Source: v_latest_player_stats view
-- Formula: (goals_per_game / 2.0) * 500, max 500

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F03_CGPGF` AS
SELECT
  pm.id AS player_id,
  pm.name AS player_name,
  pm.position,
  pm.yearOfBirth AS birth_year,
  v.season_slug AS current_season,
  v.season_start_year AS season_year,
  v.team_name AS current_team,
  v.league_name AS current_league,
  CAST(v.gp AS INT64) AS games_played,
  CAST(v.goals AS INT64) AS goals,
  ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64), CAST(v.gp AS FLOAT64)), 4) AS goals_per_game,
  LEAST(ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64), CAST(v.gp AS FLOAT64)) / 2.0 * 500, 2), 500.0) AS factor_3_current_goals_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'F'
  AND CAST(v.gp AS INT64) >= 5
  AND v.goals IS NOT NULL;


-- F04: Current Goals Per Game - Defensemen
-- Formula: (goals_per_game / 1.5) * 500, max 500

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F04_CGPGD` AS
SELECT
  pm.id AS player_id,
  pm.name AS player_name,
  pm.position,
  pm.yearOfBirth AS birth_year,
  v.season_slug AS current_season,
  v.season_start_year AS season_year,
  v.team_name AS current_team,
  v.league_name AS current_league,
  CAST(v.gp AS INT64) AS games_played,
  CAST(v.goals AS INT64) AS goals,
  ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64), CAST(v.gp AS FLOAT64)), 4) AS goals_per_game,
  LEAST(ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64), CAST(v.gp AS FLOAT64)) / 1.5 * 500, 2), 500.0) AS factor_4_current_goals_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'D'
  AND CAST(v.gp AS INT64) >= 5
  AND v.goals IS NOT NULL;


-- F05: Current Assists Per Game - All Skaters
-- Formula: (assists_per_game / 2.5) * 500, max 500

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F05_CAPG` AS
SELECT
  pm.id AS player_id,
  pm.name AS player_name,
  pm.position,
  pm.yearOfBirth AS birth_year,
  v.season_slug AS current_season,
  v.season_start_year AS season_year,
  v.team_name AS current_team,
  v.league_name AS current_league,
  CAST(v.gp AS INT64) AS games_played,
  CAST(v.assists AS INT64) AS assists,
  ROUND(SAFE_DIVIDE(CAST(v.assists AS FLOAT64), CAST(v.gp AS FLOAT64)), 4) AS assists_per_game,
  LEAST(ROUND(SAFE_DIVIDE(CAST(v.assists AS FLOAT64), CAST(v.gp AS FLOAT64)) / 2.5 * 500, 2), 500.0) AS factor_5_current_assists_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position IN ('F', 'D')
  AND CAST(v.gp AS INT64) >= 5
  AND v.assists IS NOT NULL;


-- F06: Current GAA - Goalies
-- Formula: (1 - gaa/3.5) * 500, 0 if GAA >= 3.5

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F06_CGAA` AS
SELECT
  pm.id AS player_id,
  pm.name AS player_name,
  pm.position,
  pm.yearOfBirth AS birth_year,
  v.season_slug AS current_season,
  v.season_start_year AS season_year,
  v.team_name AS current_team,
  v.league_name AS current_league,
  CAST(v.gp AS INT64) AS games_played,
  CAST(v.gaa AS FLOAT64) AS gaa,
  CASE
    WHEN CAST(v.gaa AS FLOAT64) >= 3.5 THEN 0.0
    ELSE ROUND((1 - CAST(v.gaa AS FLOAT64) / 3.5) * 500, 2)
  END AS factor_6_cgaa_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'G'
  AND CAST(v.gp AS INT64) >= 5
  AND v.gaa IS NOT NULL;


-- F07: Current Save % - Goalies
-- Formula: (svp - 0.699) / (1 - 0.699) * 300

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F07_CSV` AS
SELECT
  pm.id AS player_id,
  pm.name AS player_name,
  pm.position,
  pm.yearOfBirth AS birth_year,
  v.season_slug AS current_season,
  v.season_start_year AS season_year,
  v.team_name AS current_team,
  v.league_name AS current_league,
  CAST(v.gp AS INT64) AS games_played,
  CAST(v.svp AS FLOAT64) AS save_pct,
  CASE
    WHEN CAST(v.svp AS FLOAT64) <= 0.699 THEN 0.0
    WHEN CAST(v.svp AS FLOAT64) >= 1.0 THEN 300.0
    ELSE ROUND((CAST(v.svp AS FLOAT64) - 0.699) / (1.0 - 0.699) * 300, 2)
  END AS factor_7_csv_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'G'
  AND CAST(v.gp AS INT64) >= 5
  AND v.svp IS NOT NULL;


-- ============================================================================
-- STEP 2: REFRESH LAST SEASON FACTORS (F08-F12)
-- ============================================================================
-- These use player_season_stats directly with season_start_year = 2024
-- (no change from previous implementation)

-- F08: Last Season Goals Per Game - Forwards
-- Source: player_season_stats (2024-2025 season)
-- Formula: (goals_per_game / 2.0) * 300, max 300

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F08_LGPGF` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.goals AS INT64) AS goals,
    SAFE_DIVIDE(CAST(pss.goals AS FLOAT64), CAST(pss.gp AS FLOAT64)) AS goals_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024 AND ps.position = 'F'
    AND CAST(pss.gp AS INT64) >= 5 AND pss.goals IS NOT NULL
),
best_performance AS (
  SELECT player_id, MAX(goals_per_game) AS best_goals_per_game,
    ARRAY_AGG(team_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(goals ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS goals
  FROM last_season_stats GROUP BY player_id
)
SELECT bp.player_id, ps.name AS player_name, ps.position, ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season, bp.last_team, bp.last_league, bp.games_played, bp.goals,
  ROUND(bp.best_goals_per_game, 4) AS goals_per_game,
  LEAST(ROUND(bp.best_goals_per_game / 2.0 * 300, 2), 300.0) AS factor_8_lgpgf_points,
  CURRENT_TIMESTAMP() AS calculated_at, 'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- F09: Last Season Goals Per Game - Defensemen
-- Formula: (goals_per_game / 1.5) * 300, max 300

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F09_LGPGD` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.goals AS INT64) AS goals,
    SAFE_DIVIDE(CAST(pss.goals AS FLOAT64), CAST(pss.gp AS FLOAT64)) AS goals_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024 AND ps.position = 'D'
    AND CAST(pss.gp AS INT64) >= 5 AND pss.goals IS NOT NULL
),
best_performance AS (
  SELECT player_id, MAX(goals_per_game) AS best_goals_per_game,
    ARRAY_AGG(team_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(goals ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS goals
  FROM last_season_stats GROUP BY player_id
)
SELECT bp.player_id, ps.name AS player_name, ps.position, ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season, bp.last_team, bp.last_league, bp.games_played, bp.goals,
  ROUND(bp.best_goals_per_game, 4) AS goals_per_game,
  LEAST(ROUND(bp.best_goals_per_game / 1.5 * 300, 2), 300.0) AS factor_9_lgpgd_points,
  CURRENT_TIMESTAMP() AS calculated_at, 'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- F10: Last Season Assists Per Game - All Skaters
-- Formula: (assists_per_game / 2.5) * 300, max 300

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F10_LAPG` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.assists AS INT64) AS assists,
    SAFE_DIVIDE(CAST(pss.assists AS FLOAT64), CAST(pss.gp AS FLOAT64)) AS assists_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024 AND ps.position IN ('F', 'D')
    AND CAST(pss.gp AS INT64) >= 5 AND pss.assists IS NOT NULL
),
best_performance AS (
  SELECT player_id, MAX(assists_per_game) AS best_assists_per_game,
    ARRAY_AGG(team_name ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(assists ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS assists
  FROM last_season_stats GROUP BY player_id
)
SELECT bp.player_id, ps.name AS player_name, ps.position, ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season, bp.last_team, bp.last_league, bp.games_played, bp.assists,
  ROUND(bp.best_assists_per_game, 4) AS assists_per_game,
  LEAST(ROUND(bp.best_assists_per_game / 2.5 * 300, 2), 300.0) AS factor_10_lapg_points,
  CURRENT_TIMESTAMP() AS calculated_at, 'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- F11: Last Season GAA - Goalies
-- Formula: (1 - gaa/3.5) * 300, 0 if GAA >= 3.5

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F11_LGAA` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.gaa AS FLOAT64) AS gaa
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024 AND ps.position = 'G'
    AND CAST(pss.gp AS INT64) >= 5 AND pss.gaa IS NOT NULL
),
best_performance AS (
  SELECT player_id, MIN(gaa) AS best_gaa,
    ARRAY_AGG(team_name ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS games_played
  FROM last_season_stats GROUP BY player_id
)
SELECT bp.player_id, ps.name AS player_name, ps.position, ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season, bp.last_team, bp.last_league, bp.games_played,
  bp.best_gaa AS gaa,
  CASE
    WHEN bp.best_gaa >= 3.5 THEN 0.0
    ELSE ROUND((1 - bp.best_gaa / 3.5) * 300, 2)
  END AS factor_11_lgaa_points,
  CURRENT_TIMESTAMP() AS calculated_at, 'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- F12: Last Season Save % - Goalies
-- Formula: (svp - 0.699) / (1 - 0.699) * 200

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F12_LSV` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.svp AS FLOAT64) AS save_pct
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024 AND ps.position = 'G'
    AND CAST(pss.gp AS INT64) >= 5 AND pss.svp IS NOT NULL
),
best_performance AS (
  SELECT player_id, MAX(save_pct) AS best_save_pct,
    ARRAY_AGG(team_name ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS games_played
  FROM last_season_stats GROUP BY player_id
)
SELECT bp.player_id, ps.name AS player_name, ps.position, ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season, bp.last_team, bp.last_league, bp.games_played,
  bp.best_save_pct AS save_pct,
  CASE
    WHEN bp.best_save_pct <= 0.699 THEN 0.0
    WHEN bp.best_save_pct >= 1.0 THEN 200.0
    ELSE ROUND((bp.best_save_pct - 0.699) / (1.0 - 0.699) * 200, 2)
  END AS factor_12_lsv_points,
  CURRENT_TIMESTAMP() AS calculated_at, 'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- ============================================================================
-- STEP 3: VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify the refresh worked correctly

-- Check row counts for each factor table
-- SELECT 'PT_F03_CGPGF' as table_name, COUNT(*) as row_count FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
-- UNION ALL SELECT 'PT_F04_CGPGD', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
-- UNION ALL SELECT 'PT_F05_CAPG', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
-- UNION ALL SELECT 'PT_F06_CGAA', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
-- UNION ALL SELECT 'PT_F07_CSV', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
-- UNION ALL SELECT 'PT_F08_LGPGF', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
-- UNION ALL SELECT 'PT_F09_LGPGD', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
-- UNION ALL SELECT 'PT_F10_LAPG', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
-- UNION ALL SELECT 'PT_F11_LGAA', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
-- UNION ALL SELECT 'PT_F12_LSV', COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`;

-- Check Sawyer Thompson specifically
-- SELECT player_id, player_name, games_played, goals, goals_per_game, factor_3_current_goals_points
-- FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
-- WHERE player_id = 946038;


-- ============================================================================
-- STEP 4: REBUILD player_cumulative_points
-- ============================================================================
-- After refreshing factors, run rebuild_cumulative_with_fixes.sql
-- to aggregate all 24 factors into the main output table.

-- Then run create_ranking_views.sql to update the ranking views.


-- ============================================================================
-- EXECUTION SUMMARY
-- ============================================================================
-- After running this script:
-- 1. PT_F03_CGPGF should have ~29,000+ forwards (was 12,587)
-- 2. PT_F04_CGPGD should have ~15,000+ defensemen (was 6,626)
-- 3. PT_F05_CAPG should have ~44,000+ skaters (was 19,223)
-- 4. PT_F06_CGAA should have goalies with current season GAA
-- 5. PT_F07_CSV should have goalies with current season save %
-- 6. PT_F08_LGPGF should have ~50,000+ forwards with 2024-25 data
-- 7. PT_F09_LGPGD should have ~25,000+ defensemen with 2024-25 data
-- 8. PT_F10_LAPG should have ~75,000+ skaters with 2024-25 data
-- 9. PT_F11_LGAA should have goalies with 2024-25 GAA
-- 10. PT_F12_LSV should have goalies with 2024-25 save %
--
-- Players like Sawyer Thompson (946038) who now have 5+ GP will be included.
-- ============================================================================

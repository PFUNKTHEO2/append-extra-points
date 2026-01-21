-- ============================================================================
-- FIX: Performance Factors Pipeline (F03-F12)
-- ============================================================================
-- Run this script AFTER running DIAGNOSTIC_performance_factors.sql
-- This will refresh all PT tables and rebuild the cumulative table
-- Created: 2026-01-20
-- Updated: 2026-01-21 - Migrated to v_latest_player_stats view
-- ============================================================================
--
-- EXECUTION ORDER:
-- 1. Run each section separately in BigQuery Console
-- 2. Wait for each to complete before running the next
-- 3. After all complete, run the sync to Supabase
--
-- ============================================================================


-- ============================================================================
-- PREREQUISITE: CREATE v_latest_player_stats VIEW (if not exists)
-- ============================================================================
-- Run create_v_latest_player_stats.sql first to create the view


-- ============================================================================
-- PART 1: REFRESH CURRENT SEASON FACTORS (F03-F07)
-- ============================================================================
-- These use v_latest_player_stats view (derived from player_season_stats)
-- joined with player_stats for metadata (name, position, yearOfBirth)

-- F03: Current Goals Per Game (Forwards)
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
  ROUND(SAFE_DIVIDE(
    CAST(v.goals AS FLOAT64),
    CAST(v.gp AS FLOAT64)
  ), 4) AS goals_per_game,
  LEAST(
    ROUND(SAFE_DIVIDE(
      CAST(v.goals AS FLOAT64),
      CAST(v.gp AS FLOAT64)
    ) / 2.0 * 500, 2),
    500.0
  ) AS factor_3_current_goals_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'F'
  AND CAST(v.gp AS INT64) >= 5
  AND v.goals IS NOT NULL
  AND CAST(v.goals AS INT64) >= 0;

-- F04: Current Goals Per Game (Defenders)
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
  ROUND(SAFE_DIVIDE(
    CAST(v.goals AS FLOAT64),
    CAST(v.gp AS FLOAT64)
  ), 4) AS goals_per_game,
  LEAST(
    ROUND(SAFE_DIVIDE(
      CAST(v.goals AS FLOAT64),
      CAST(v.gp AS FLOAT64)
    ) / 1.5 * 500, 2),
    500.0
  ) AS factor_4_current_goals_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position = 'D'
  AND CAST(v.gp AS INT64) >= 5
  AND v.goals IS NOT NULL
  AND CAST(v.goals AS INT64) >= 0;

-- F05: Current Assists Per Game (Forwards & Defenders)
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
  ROUND(SAFE_DIVIDE(
    CAST(v.assists AS FLOAT64),
    CAST(v.gp AS FLOAT64)
  ), 4) AS assists_per_game,
  LEAST(
    ROUND(SAFE_DIVIDE(
      CAST(v.assists AS FLOAT64),
      CAST(v.gp AS FLOAT64)
    ) / 2.5 * 500, 2),
    500.0
  ) AS factor_5_current_assists_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
WHERE pm.position IN ('F', 'D')
  AND CAST(v.gp AS INT64) >= 5
  AND v.assists IS NOT NULL
  AND CAST(v.assists AS INT64) >= 0;

-- F06: Current GAA (Goalies)
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

-- F07: Current Save % (Goalies)
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
-- PART 2: REFRESH PAST SEASON FACTORS (F08-F12)
-- ============================================================================
-- These use player_season_stats with season_start_year = 2024

-- F08: Last Season Goals Per Game (Forwards)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F08_LGPGF` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.season_start_year,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.goals AS INT64) AS goals,
    SAFE_DIVIDE(
      CAST(pss.goals AS FLOAT64),
      CAST(pss.gp AS FLOAT64)
    ) AS goals_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps
    ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024
    AND ps.position = 'F'
    AND CAST(pss.gp AS INT64) >= 5
    AND pss.goals IS NOT NULL
),
best_performance AS (
  SELECT
    player_id,
    MAX(goals_per_game) AS best_goals_per_game,
    ARRAY_AGG(team_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(goals ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS goals
  FROM last_season_stats
  GROUP BY player_id
)
SELECT
  bp.player_id,
  ps.name AS player_name,
  ps.position,
  ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season,
  bp.last_team,
  bp.last_league,
  bp.games_played,
  bp.goals,
  ROUND(bp.best_goals_per_game, 4) AS goals_per_game,
  LEAST(ROUND(bp.best_goals_per_game / 2.0 * 300, 2), 300.0) AS factor_8_lgpgf_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;

-- F09: Last Season Goals Per Game (Defenders)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F09_LGPGD` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.season_start_year,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.goals AS INT64) AS goals,
    SAFE_DIVIDE(
      CAST(pss.goals AS FLOAT64),
      CAST(pss.gp AS FLOAT64)
    ) AS goals_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps
    ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024
    AND ps.position = 'D'
    AND CAST(pss.gp AS INT64) >= 5
    AND pss.goals IS NOT NULL
),
best_performance AS (
  SELECT
    player_id,
    MAX(goals_per_game) AS best_goals_per_game,
    ARRAY_AGG(team_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(goals ORDER BY goals_per_game DESC LIMIT 1)[OFFSET(0)] AS goals
  FROM last_season_stats
  GROUP BY player_id
)
SELECT
  bp.player_id,
  ps.name AS player_name,
  ps.position,
  ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season,
  bp.last_team,
  bp.last_league,
  bp.games_played,
  bp.goals,
  ROUND(bp.best_goals_per_game, 4) AS goals_per_game,
  LEAST(ROUND(bp.best_goals_per_game / 1.5 * 300, 2), 300.0) AS factor_9_lgpgd_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;

-- F10: Last Season Assists Per Game (Forwards & Defenders)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F10_LAPG` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.season_start_year,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.assists AS INT64) AS assists,
    SAFE_DIVIDE(
      CAST(pss.assists AS FLOAT64),
      CAST(pss.gp AS FLOAT64)
    ) AS assists_per_game
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps
    ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024
    AND ps.position IN ('F', 'D')
    AND CAST(pss.gp AS INT64) >= 5
    AND pss.assists IS NOT NULL
),
best_performance AS (
  SELECT
    player_id,
    MAX(assists_per_game) AS best_assists_per_game,
    ARRAY_AGG(team_name ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS games_played,
    ARRAY_AGG(assists ORDER BY assists_per_game DESC LIMIT 1)[OFFSET(0)] AS assists
  FROM last_season_stats
  GROUP BY player_id
)
SELECT
  bp.player_id,
  ps.name AS player_name,
  ps.position,
  ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season,
  bp.last_team,
  bp.last_league,
  bp.games_played,
  bp.assists,
  ROUND(bp.best_assists_per_game, 4) AS assists_per_game,
  LEAST(ROUND(bp.best_assists_per_game / 2.5 * 300, 2), 300.0) AS factor_10_lapg_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;

-- F11: Last Season GAA (Goalies)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F11_LGAA` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.gaa AS FLOAT64) AS gaa
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps
    ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024
    AND ps.position = 'G'
    AND CAST(pss.gp AS INT64) >= 5
    AND pss.gaa IS NOT NULL
),
best_performance AS (
  SELECT
    player_id,
    MIN(gaa) AS best_gaa,
    ARRAY_AGG(team_name ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY gaa ASC LIMIT 1)[OFFSET(0)] AS games_played
  FROM last_season_stats
  GROUP BY player_id
)
SELECT
  bp.player_id,
  ps.name AS player_name,
  ps.position,
  ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season,
  bp.last_team,
  bp.last_league,
  bp.games_played,
  bp.best_gaa AS gaa,
  CASE
    WHEN bp.best_gaa >= 3.5 THEN 0.0
    ELSE ROUND((1 - bp.best_gaa / 3.5) * 300, 2)
  END AS factor_11_lgaa_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;

-- F12: Last Season Save % (Goalies)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F12_LSV` AS
WITH last_season_stats AS (
  SELECT
    pss.player_id,
    pss.team_name,
    pss.league_name,
    CAST(pss.gp AS INT64) AS games_played,
    CAST(pss.svp AS FLOAT64) AS save_pct
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps
    ON pss.player_id = ps.id
  WHERE pss.season_start_year = 2024
    AND ps.position = 'G'
    AND CAST(pss.gp AS INT64) >= 5
    AND pss.svp IS NOT NULL
),
best_performance AS (
  SELECT
    player_id,
    MAX(save_pct) AS best_save_pct,
    ARRAY_AGG(team_name ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS last_team,
    ARRAY_AGG(league_name ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS last_league,
    ARRAY_AGG(games_played ORDER BY save_pct DESC LIMIT 1)[OFFSET(0)] AS games_played
  FROM last_season_stats
  GROUP BY player_id
)
SELECT
  bp.player_id,
  ps.name AS player_name,
  ps.position,
  ps.yearOfBirth AS birth_year,
  '2024-2025' AS last_season,
  bp.last_team,
  bp.last_league,
  bp.games_played,
  bp.best_save_pct AS save_pct,
  CASE
    WHEN bp.best_save_pct <= 0.699 THEN 0.0
    WHEN bp.best_save_pct >= 1.0 THEN 200.0
    ELSE ROUND((bp.best_save_pct - 0.699) / (1.0 - 0.699) * 200, 2)
  END AS factor_12_lsv_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version
FROM best_performance bp
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON bp.player_id = ps.id;


-- ============================================================================
-- PART 3: VERIFY PT TABLE REFRESH
-- ============================================================================
-- Run this to confirm the refresh worked

SELECT
  'POST-REFRESH CHECK' as status,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`) as f03_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`) as f04_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`) as f05_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`) as f06_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`) as f07_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`) as f08_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`) as f09_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`) as f10_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`) as f11_rows,
  (SELECT COUNT(*) FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`) as f12_rows;


-- ============================================================================
-- PART 4: REBUILD CUMULATIVE TABLE
-- ============================================================================
-- Run this AFTER Parts 1-3 complete
-- This is the same as rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql
-- Paste the contents of that file here, or run it separately
-- ============================================================================

-- After running rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql, verify:
-- SELECT COUNT(*), COUNTIF(f03_current_goals_f > 0), COUNTIF(performance_total > 0)
-- FROM `prodigy-ranking.algorithm_core.player_cumulative_points`;


-- ============================================================================
-- PART 5: SYNC TO SUPABASE
-- ============================================================================
-- After BigQuery is updated, trigger the sync function:
-- curl -X POST https://us-central1-prodigy-ranking.cloudfunctions.net/syncRankings
-- OR run sync.js locally
-- ============================================================================

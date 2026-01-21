-- ============================================================================
-- REFRESH PT_F05_CAPG - Current Assists Per Game (All Skaters)
-- ============================================================================
-- Factor 5: Current Season Assists Per Game for All Skaters (F and D)
-- Source: v_latest_player_stats (derived from player_season_stats)
--         player_stats (for metadata: name, position, yearOfBirth)
-- Formula: (assists_per_game / 2.5) * 500, capped at 500 points
-- Minimum: 5 games played
-- Updated: 2026-01-21 - Migrated to v_latest_player_stats view
-- ============================================================================

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
  -- Formula: (assists_per_game / 2.5) * 500, max 500
  LEAST(
    ROUND(
      SAFE_DIVIDE(
        CAST(v.assists AS FLOAT64),
        CAST(v.gp AS FLOAT64)
      ) / 2.5 * 500,
      2
    ),
    500.0
  ) AS factor_5_current_assists_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version

FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm
  ON v.player_id = pm.id

WHERE
  -- Skaters only (Forwards and Defensemen)
  pm.position IN ('F', 'D')
  -- Minimum 5 games played
  AND CAST(v.gp AS INT64) >= 5
  -- Must have assists data
  AND v.assists IS NOT NULL
  AND CAST(v.assists AS INT64) >= 0;

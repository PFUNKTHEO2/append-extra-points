-- ============================================================================
-- REFRESH PT_F04_CGPGD - Current Goals Per Game (Defensemen)
-- ============================================================================
-- Factor 4: Current Season Goals Per Game for Defensemen
-- Source: v_latest_player_stats (derived from player_season_stats)
--         player_stats (for metadata: name, position, yearOfBirth)
-- Formula: (goals_per_game / 1.5) * 500, capped at 500 points
-- Note: Defensemen use 1.5 divisor (vs 2.0 for forwards) since they score less
-- Minimum: 5 games played
-- Updated: 2026-01-21 - Migrated to v_latest_player_stats view
-- ============================================================================

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
  -- Formula: (goals_per_game / 1.5) * 500, max 500
  LEAST(
    ROUND(
      SAFE_DIVIDE(
        CAST(v.goals AS FLOAT64),
        CAST(v.gp AS FLOAT64)
      ) / 1.5 * 500,
      2
    ),
    500.0
  ) AS factor_4_current_goals_points,
  CURRENT_TIMESTAMP() AS calculated_at,
  'v2.5' AS algorithm_version

FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm
  ON v.player_id = pm.id

WHERE
  -- Defensemen only
  pm.position = 'D'
  -- Minimum 5 games played
  AND CAST(v.gp AS INT64) >= 5
  -- Must have goals data
  AND v.goals IS NOT NULL
  AND CAST(v.goals AS INT64) >= 0;

-- ============================================================================
-- CONSOLIDATED player_rankings REBUILD
-- ============================================================================
-- VERSION: v3.0-consolidated
--
-- This is the new consolidated rebuild that calculates ALL factors inline
-- instead of reading from PT_ tables. This reduces table count from 104 to 8.
--
-- DEPENDENCIES:
--   1. player_stats (EP source data)
--   2. player_season_stats (historical seasons for F08-F12) - in algorithm_staging
--   3. leagues (league tier points for F13) - renamed from DL_all_leagues
--   4. player_external_factors (consolidated external data for F15-F24)
--
-- CHANGES FROM v2.9:
--   - F01-F12: Calculated inline from player_stats/player_season_stats
--   - F13: Uses leagues table instead of DL_F13_league_points
--   - F15-F24: Uses player_external_factors instead of individual DL_ tables
--   - F14: Still disabled (returns 0)
--   - F18, F19, F25-F27: Calculated inline (currently returns 0 - no delta data)
-- ============================================================================

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_rankings` AS

WITH
-- ============================================================================
-- BASE PLAYERS from player_stats
-- ============================================================================
base_players AS (
  SELECT DISTINCT
    id AS player_id,
    name AS player_name,
    position,
    yearOfBirth AS birth_year,
    nationality_name,
    COALESCE(latestStats_teamName, latestStats_team_name) AS current_team,
    COALESCE(latestStats_league_name, latestStats_team_league_name) AS current_league,
    latestStats_season_slug AS current_season,
    COALESCE(latestStats_league_country_name, latestStats_team_league_country_name) AS team_country,
    -- Raw stats for inline calculations
    views,
    height_metrics AS height_cm,
    height_imperial AS height_inches,
    SAFE_CAST(latestStats_regularStats_GP AS INT64) AS gp,
    SAFE_CAST(latestStats_regularStats_G AS INT64) AS goals,
    SAFE_CAST(latestStats_regularStats_A AS INT64) AS assists,
    SAFE_CAST(latestStats_regularStats_GAA AS FLOAT64) AS gaa,
    SAFE_CAST(latestStats_regularStats_SVP AS FLOAT64) AS svp,
    latestStats_season_startYear AS season_year
  FROM `prodigy-ranking.algorithm_core.player_stats`
  WHERE COALESCE(latestStats_teamName, latestStats_team_name) NOT LIKE '%(W)%'
),

-- ============================================================================
-- F01: VIEWS POINTS (from PT_F01_EPV - has correct views data)
-- Note: player_stats.views is stale for many players, PT_F01_EPV has current data
-- Formula: (views - 100) * (2000 / 29900), capped at 0-2000
-- ============================================================================
f01_calc AS (
  SELECT
    player_id,
    COALESCE(factor_1_epv_points, 0) AS f01_views
  FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
),

-- ============================================================================
-- F02: HEIGHT POINTS (Inline calculation)
-- Formula: Linear distribution, varies by birth year & position
-- Max 200 points (per Algorithm 2026.01.14 spec)
-- ============================================================================
f02_calc AS (
  SELECT
    player_id,
    CASE
      WHEN height_cm IS NOT NULL AND height_cm > 0
        THEN LEAST(GREATEST((height_cm - 175) * 10, 0), 200)
      WHEN height_inches IS NOT NULL AND SAFE_CAST(height_inches AS FLOAT64) > 0
        THEN LEAST(GREATEST(((SAFE_CAST(height_inches AS FLOAT64) - 65) / 11) * 200, 0), 200)
      ELSE 0
    END AS f02_height
  FROM base_players
),

-- ============================================================================
-- F03: CURRENT GOALS - FORWARDS (Inline calculation)
-- Formula: (goals_per_game / 2.0) * 500, max 500, min 5 GP
-- ============================================================================
f03_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'F' AND gp >= 5 AND goals IS NOT NULL
      THEN LEAST(ROUND(SAFE_DIVIDE(CAST(goals AS FLOAT64), gp) / 2.0 * 500, 2), 500)
      ELSE 0
    END AS f03_current_goals_f
  FROM base_players
),

-- ============================================================================
-- F04: CURRENT GOALS - DEFENSEMEN (Inline calculation)
-- Formula: (goals_per_game / 1.5) * 500, max 500, min 5 GP
-- ============================================================================
f04_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'D' AND gp >= 5 AND goals IS NOT NULL
      THEN LEAST(ROUND(SAFE_DIVIDE(CAST(goals AS FLOAT64), gp) / 1.5 * 500, 2), 500)
      ELSE 0
    END AS f04_current_goals_d
  FROM base_players
),

-- ============================================================================
-- F05: CURRENT ASSISTS (Inline calculation)
-- Formula: (assists_per_game / 2.5) * 500, max 500, min 5 GP
-- ============================================================================
f05_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position IN ('F', 'D') AND gp >= 5 AND assists IS NOT NULL
      THEN LEAST(ROUND(SAFE_DIVIDE(CAST(assists AS FLOAT64), gp) / 2.5 * 500, 2), 500)
      ELSE 0
    END AS f05_current_assists
  FROM base_players
),

-- ============================================================================
-- F06: CURRENT GAA - GOALIES (Inline calculation)
-- Formula: ((3.5 - GAA) / 3.5) * 500, max 500 (inverted - lower GAA = more points)
-- ============================================================================
f06_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'G' AND gp >= 5 AND gaa IS NOT NULL
      THEN GREATEST(0, LEAST(500,
        CASE
          WHEN gaa <= 0 THEN 500
          WHEN gaa >= 3.5 THEN 0
          ELSE ROUND(((3.5 - gaa) / 3.5) * 500, 2)
        END
      ))
      ELSE 0
    END AS f06_current_gaa
  FROM base_players
),

-- ============================================================================
-- F07: CURRENT SAVE % - GOALIES (Inline calculation)
-- Formula: ((save_pct - 70) / 30) * 300, max 300
-- ============================================================================
f07_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'G' AND gp >= 5 AND svp IS NOT NULL
      THEN GREATEST(0, LEAST(300,
        CASE
          -- Normalize SVP (if stored as 0-1, multiply by 100)
          WHEN svp <= 1 THEN ROUND(((svp * 100) - 70) / 30 * 300, 2)
          ELSE ROUND((svp - 70) / 30 * 300, 2)
        END
      ))
      ELSE 0
    END AS f07_current_svp
  FROM base_players
),

-- ============================================================================
-- F08-F12: LAST SEASON STATS (from player_season_stats_staging)
-- ============================================================================
last_season_stats AS (
  SELECT
    pss.api_player_id AS player_id,
    ps.position,
    CAST(pss.regularStats_GP AS INT64) AS gp,
    CAST(pss.regularStats_G AS INT64) AS goals,
    CAST(pss.regularStats_A AS INT64) AS assists,
    CAST(pss.regularStats_GAA AS FLOAT64) AS gaa,
    pss.regularStats_SVP AS svp
  FROM `prodigy-ranking.algorithm_staging.player_season_stats_staging` pss
  INNER JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pss.api_player_id = ps.id
  WHERE pss.season_startYear = 2024
    AND CAST(pss.regularStats_GP AS INT64) >= 5
),

-- Best last season performance per player (handles multiple teams)
last_season_best AS (
  SELECT
    player_id,
    position,
    MAX(SAFE_DIVIDE(CAST(goals AS FLOAT64), gp)) AS best_gpg,
    MAX(SAFE_DIVIDE(CAST(assists AS FLOAT64), gp)) AS best_apg,
    MIN(gaa) AS best_gaa,  -- Lower is better
    MAX(CASE WHEN svp <= 1 THEN svp * 100 ELSE svp END) AS best_svp  -- Higher is better
  FROM last_season_stats
  GROUP BY player_id, position
),

-- F08: Last Season Goals - Forwards
f08_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'F' AND best_gpg IS NOT NULL
      THEN LEAST(ROUND(best_gpg / 2.0 * 300, 2), 300)
      ELSE 0
    END AS f08_last_goals_f
  FROM last_season_best
),

-- F09: Last Season Goals - Defensemen
f09_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'D' AND best_gpg IS NOT NULL
      THEN LEAST(ROUND(best_gpg / 1.5 * 300, 2), 300)
      ELSE 0
    END AS f09_last_goals_d
  FROM last_season_best
),

-- F10: Last Season Assists
f10_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position IN ('F', 'D') AND best_apg IS NOT NULL
      THEN LEAST(ROUND(best_apg / 2.5 * 300, 2), 300)
      ELSE 0
    END AS f10_last_assists
  FROM last_season_best
),

-- F11: Last Season GAA - Goalies
f11_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'G' AND best_gaa IS NOT NULL
      THEN GREATEST(0, LEAST(300,
        CASE
          WHEN best_gaa <= 0 THEN 300
          WHEN best_gaa >= 3.5 THEN 0
          ELSE ROUND(((3.5 - best_gaa) / 3.5) * 300, 2)
        END
      ))
      ELSE 0
    END AS f11_last_gaa
  FROM last_season_best
),

-- F12: Last Season Save % - Goalies
f12_calc AS (
  SELECT
    player_id,
    CASE
      WHEN position = 'G' AND best_svp IS NOT NULL AND best_svp > 0
      THEN GREATEST(0, LEAST(200,
        CASE
          WHEN best_svp < 70 THEN 0
          WHEN best_svp >= 100 THEN 200
          ELSE ROUND((best_svp - 70) / 30 * 200, 2)
        END
      ))
      ELSE 0
    END AS f12_last_svp
  FROM last_season_best
),

-- ============================================================================
-- F13: LEAGUE POINTS (from leagues table)
-- ============================================================================
f13_calc AS (
  SELECT
    bp.player_id,
    MAX(COALESCE(l.league_points, 0)) AS f13_league_points
  FROM base_players bp
  LEFT JOIN `prodigy-ranking.algorithm_core.DL_all_leagues` l
    ON LOWER(TRIM(REPLACE(REPLACE(bp.current_league, ' ', '-'), '_', '-'))) =
       LOWER(TRIM(REPLACE(REPLACE(l.league_name, ' ', '-'), '_', '-')))
  GROUP BY bp.player_id
),

-- ============================================================================
-- F14: TEAM POINTS (DISABLED - always 0)
-- ============================================================================

-- ============================================================================
-- F15-F24: EXTERNAL FACTORS (from player_external_factors)
-- ============================================================================
external_factors AS (
  SELECT
    player_id,
    COALESCE(international_points, 0) AS f15_international_points,
    COALESCE(commitment_points, 0) AS f16_commitment_points,
    COALESCE(draft_points, 0) AS f17_draft_points,
    COALESCE(tournament_points, 0) AS f21_tournament_points,
    COALESCE(manual_points, 0) AS f22_manual_points,
    COALESCE(playing_up_points, 0) AS f20_playing_up_points,
    COALESCE(prodigylikes_points, 0) AS f23_prodigylikes_points,
    COALESCE(card_sales_points, 0) AS f24_card_sales_points
  FROM `prodigy-ranking.algorithm_core.player_external_factors`
),

-- ============================================================================
-- F18/F19/F25: WEEKLY DELTAS (from weekly_stats_snapshot)
-- Per Algorithm 2026.01.14 spec:
--   F18: 40 points per goal delta, max 200, capped at 5 goals (F,D only)
--   F19: 25 points per assist delta, max 125, capped at 5 assists (F,D only)
--   F25: 1 point per view delta, max 200 (all positions)
-- ============================================================================
latest_snapshot AS (
  SELECT
    player_id,
    goals AS snapshot_goals,
    assists AS snapshot_assists,
    views AS snapshot_views
  FROM `prodigy-ranking.algorithm_core.weekly_stats_snapshot`
  WHERE snapshot_date = (
    SELECT MAX(snapshot_date)
    FROM `prodigy-ranking.algorithm_core.weekly_stats_snapshot`
    WHERE snapshot_date < CURRENT_DATE()  -- Get previous snapshot, not today's
  )
),

weekly_deltas AS (
  SELECT
    bp.player_id,
    bp.position,
    -- Goal delta (current - snapshot), capped at 5
    LEAST(GREATEST(COALESCE(bp.goals, 0) - COALESCE(ls.snapshot_goals, 0), 0), 5) AS goal_delta,
    -- Assist delta (current - snapshot), capped at 5
    LEAST(GREATEST(COALESCE(bp.assists, 0) - COALESCE(ls.snapshot_assists, 0), 0), 5) AS assist_delta,
    -- View delta (current - snapshot), no negative
    GREATEST(COALESCE(bp.views, 0) - COALESCE(ls.snapshot_views, 0), 0) AS view_delta
  FROM base_players bp
  LEFT JOIN latest_snapshot ls ON bp.player_id = ls.player_id
),

f18_f19_f25_calc AS (
  SELECT
    player_id,
    -- F18: Weekly Goals (F,D only) - 40 pts/goal, max 200
    CASE
      WHEN position IN ('F', 'D') THEN LEAST(goal_delta * 40, 200)
      ELSE 0
    END AS f18_weekly_goals,
    -- F19: Weekly Assists (F,D only) - 25 pts/assist, max 125
    CASE
      WHEN position IN ('F', 'D') THEN LEAST(assist_delta * 25, 125)
      ELSE 0
    END AS f19_weekly_assists,
    -- F25: Weekly EP Views (all positions) - 1 pt/view, max 200
    LEAST(view_delta, 200) AS f25_weekly_views
  FROM weekly_deltas
)

-- ============================================================================
-- FINAL SELECT: Combine all factors
-- ============================================================================
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

  -- Performance Factors (F01-F12) - Inline calculated
  COALESCE(f01.f01_views, 0) AS f01_views,
  COALESCE(f02.f02_height, 0) AS f02_height,
  COALESCE(f03.f03_current_goals_f, 0) AS f03_current_goals_f,
  COALESCE(f04.f04_current_goals_d, 0) AS f04_current_goals_d,
  COALESCE(f05.f05_current_assists, 0) AS f05_current_assists,
  COALESCE(f06.f06_current_gaa, 0) AS f06_current_gaa,
  COALESCE(f07.f07_current_svp, 0) AS f07_current_svp,
  COALESCE(f08.f08_last_goals_f, 0) AS f08_last_goals_f,
  COALESCE(f09.f09_last_goals_d, 0) AS f09_last_goals_d,
  COALESCE(f10.f10_last_assists, 0) AS f10_last_assists,
  COALESCE(f11.f11_last_gaa, 0) AS f11_last_gaa,
  COALESCE(f12.f12_last_svp, 0) AS f12_last_svp,

  -- Direct Load Factors (F13-F24)
  COALESCE(f13.f13_league_points, 0) AS f13_league_points,
  0 AS f14_team_points,  -- DISABLED
  COALESCE(ef.f15_international_points, 0) AS f15_international_points,
  COALESCE(ef.f16_commitment_points, 0) AS f16_commitment_points,
  COALESCE(ef.f17_draft_points, 0) AS f17_draft_points,
  COALESCE(wd.f18_weekly_goals, 0) AS f18_weekly_points_delta,
  COALESCE(wd.f19_weekly_assists, 0) AS f19_weekly_assists_delta,
  COALESCE(ef.f20_playing_up_points, 0) AS f20_playing_up_points,
  COALESCE(ef.f21_tournament_points, 0) AS f21_tournament_points,
  COALESCE(ef.f22_manual_points, 0) AS f22_manual_points,
  COALESCE(ef.f23_prodigylikes_points, 0) AS f23_prodigylikes_points,
  COALESCE(ef.f24_card_sales_points, 0) AS f24_card_sales_points,
  COALESCE(wd.f25_weekly_views, 0) AS f25_weekly_views,
  0 AS f26_weight_points,   -- TODO: Needs Physical Standards tables
  0 AS f27_bmi_points,      -- TODO: Needs Physical Standards tables

  -- Calculate performance total (F01-F12)
  (
    COALESCE(f01.f01_views, 0) +
    COALESCE(f02.f02_height, 0) +
    COALESCE(f03.f03_current_goals_f, 0) +
    COALESCE(f04.f04_current_goals_d, 0) +
    COALESCE(f05.f05_current_assists, 0) +
    COALESCE(f06.f06_current_gaa, 0) +
    COALESCE(f07.f07_current_svp, 0) +
    COALESCE(f08.f08_last_goals_f, 0) +
    COALESCE(f09.f09_last_goals_d, 0) +
    COALESCE(f10.f10_last_assists, 0) +
    COALESCE(f11.f11_last_gaa, 0) +
    COALESCE(f12.f12_last_svp, 0)
  ) AS performance_total,

  -- Calculate direct load total (F13-F27)
  (
    COALESCE(f13.f13_league_points, 0) +
    0 +  -- F14 disabled
    COALESCE(ef.f15_international_points, 0) +
    COALESCE(ef.f16_commitment_points, 0) +
    COALESCE(ef.f17_draft_points, 0) +
    COALESCE(wd.f18_weekly_goals, 0) +
    COALESCE(wd.f19_weekly_assists, 0) +
    COALESCE(ef.f20_playing_up_points, 0) +
    COALESCE(ef.f21_tournament_points, 0) +
    COALESCE(ef.f22_manual_points, 0) +
    COALESCE(ef.f23_prodigylikes_points, 0) +
    COALESCE(ef.f24_card_sales_points, 0) +
    COALESCE(wd.f25_weekly_views, 0) +
    0 +  -- F26 needs Physical Standards tables
    0    -- F27 needs Physical Standards tables
  ) AS direct_load_total,

  -- Calculate total points
  (
    -- Performance
    COALESCE(f01.f01_views, 0) +
    COALESCE(f02.f02_height, 0) +
    COALESCE(f03.f03_current_goals_f, 0) +
    COALESCE(f04.f04_current_goals_d, 0) +
    COALESCE(f05.f05_current_assists, 0) +
    COALESCE(f06.f06_current_gaa, 0) +
    COALESCE(f07.f07_current_svp, 0) +
    COALESCE(f08.f08_last_goals_f, 0) +
    COALESCE(f09.f09_last_goals_d, 0) +
    COALESCE(f10.f10_last_assists, 0) +
    COALESCE(f11.f11_last_gaa, 0) +
    COALESCE(f12.f12_last_svp, 0) +
    -- Direct Load
    COALESCE(f13.f13_league_points, 0) +
    0 +  -- F14 disabled
    COALESCE(ef.f15_international_points, 0) +
    COALESCE(ef.f16_commitment_points, 0) +
    COALESCE(ef.f17_draft_points, 0) +
    COALESCE(wd.f18_weekly_goals, 0) +
    COALESCE(wd.f19_weekly_assists, 0) +
    COALESCE(ef.f20_playing_up_points, 0) +
    COALESCE(ef.f21_tournament_points, 0) +
    COALESCE(ef.f22_manual_points, 0) +
    COALESCE(ef.f23_prodigylikes_points, 0) +
    COALESCE(ef.f24_card_sales_points, 0) +
    COALESCE(wd.f25_weekly_views, 0)
  ) AS total_points,

  CURRENT_TIMESTAMP() AS calculated_at,
  'v3.3-2026.01.15-f01-fix' AS algorithm_version

FROM base_players bp
LEFT JOIN f01_calc f01 ON bp.player_id = f01.player_id
LEFT JOIN f02_calc f02 ON bp.player_id = f02.player_id
LEFT JOIN f03_calc f03 ON bp.player_id = f03.player_id
LEFT JOIN f04_calc f04 ON bp.player_id = f04.player_id
LEFT JOIN f05_calc f05 ON bp.player_id = f05.player_id
LEFT JOIN f06_calc f06 ON bp.player_id = f06.player_id
LEFT JOIN f07_calc f07 ON bp.player_id = f07.player_id
LEFT JOIN f08_calc f08 ON bp.player_id = f08.player_id
LEFT JOIN f09_calc f09 ON bp.player_id = f09.player_id
LEFT JOIN f10_calc f10 ON bp.player_id = f10.player_id
LEFT JOIN f11_calc f11 ON bp.player_id = f11.player_id
LEFT JOIN f12_calc f12 ON bp.player_id = f12.player_id
LEFT JOIN f13_calc f13 ON bp.player_id = f13.player_id
LEFT JOIN external_factors ef ON bp.player_id = ef.player_id
LEFT JOIN f18_f19_f25_calc wd ON bp.player_id = wd.player_id;

-- ============================================================================
-- REBUILD player_cumulative_points WITH FULLY DEDUPLICATED JOINS
-- ============================================================================
-- VERSION: v3.1 (F13 uses DL_all_leagues)
-- CHANGE: F13 now uses algorithm.DL_all_leagues instead of DL_F13_league_points
--         Scale changed from 0-4500 to 0-1000 points
-- PREVIOUS: v2.9 (F15 Capped at 1000)
-- PREVIOUS: Added LEAST(total_international_points, 1000) cap to F15
-- PREVIOUS: v2.8 Added F25 Weekly Views
-- PREVIOUS: v2.7 Added F26 Weight Points (max 150) and F27 BMI Points (max 250)
-- PREVIOUS: F14 Team Points DISABLED as of 2025-12-16 (returns 0 for all players)
-- PREVIOUS FIX: Added GROUP BY + MAX() to F13 CTE to prevent duplicates
--
-- ROOT CAUSE OF DUPLICATES:
--   DL_F13_league_points contains case-variant duplicates (e.g., 'OHL' and 'ohl')
--   When the JOIN normalizes case with LOWER(), players match BOTH entries,
--   creating duplicate rows in the final table.
--
-- SOLUTION: Use MAX(points) with GROUP BY player_id in F13 CTE (same as F14)
-- ============================================================================

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_cumulative_points` AS

WITH base_players AS (
  -- Get all unique players from player_stats as the base
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

-- Performance Factors (F01-F12)
f01_data AS (
  SELECT player_id, factor_1_epv_points AS f01_views
  FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
),

f02_data AS (
  SELECT player_id, factor_2_h_points AS f02_height
  FROM `prodigy-ranking.algorithm_core.PT_F02_H`
),

f03_data AS (
  SELECT player_id, factor_3_current_goals_points AS f03_current_goals_f
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
),

f04_data AS (
  SELECT player_id, factor_4_current_goals_points AS f04_current_goals_d
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
),

f05_data AS (
  SELECT player_id, factor_5_current_assists_points AS f05_current_assists
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
),

f06_data AS (
  SELECT player_id, factor_6_cgaa_points AS f06_current_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
),

f07_data AS (
  SELECT player_id, factor_7_csv_points AS f07_current_svp
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
),

f08_data AS (
  SELECT player_id, factor_8_lgpgf_points AS f08_last_goals_f
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
),

f09_data AS (
  SELECT player_id, factor_9_lgpgd_points AS f09_last_goals_d
  FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
),

f10_data AS (
  SELECT player_id, factor_10_lapg_points AS f10_last_assists
  FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
),

f11_data AS (
  SELECT player_id, factor_11_lgaa_points AS f11_last_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
),

f12_data AS (
  SELECT player_id, factor_12_lsv_points AS f12_last_svp
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`
),

-- ============================================================================
-- F13: League Points - UPDATED 2026-01-02 TO USE DL_all_leagues
-- ============================================================================
-- SOURCE: algorithm.DL_all_leagues (per David's email)
-- SCALE: 0-1000 points (was 0-4500 with old DL_F13_league_points)
-- LOGIC: Match by league_name OR league_slug, pick highest value
-- COVERAGE: 148,680 players (more than previous 139,829)
-- ============================================================================
f13_data AS (
  SELECT
    ps.id AS player_id,
    MAX(COALESCE(al.league_points, 0)) AS f13_league_points
  FROM `prodigy-ranking.algorithm_core.player_stats` ps
  LEFT JOIN `prodigy-ranking.algorithm.DL_all_leagues` al
    ON LOWER(TRIM(REPLACE(REPLACE(ps.latestStats_team_league_name, ' ', '-'), '_', '-'))) =
       LOWER(TRIM(REPLACE(REPLACE(al.league_name, ' ', '-'), '_', '-')))
  GROUP BY ps.id
),

-- ============================================================================
-- F14: Team Points - DISABLED AS OF 2025-12-16
-- ============================================================================
-- STATUS: DEACTIVATED - Returns 0 for all players
-- REASON: Team points temporarily disabled pending further review
-- TO RE-ENABLE: Uncomment the original query below and remove the simplified version
--
-- ORIGINAL QUERY (for re-enabling):
-- f14_data AS (
--   SELECT
--     ps.id AS player_id,
--     MAX(COALESCE(tp.points, 0)) AS f14_team_points
--   FROM `prodigy-ranking.algorithm_core.player_stats` ps
--   LEFT JOIN `prodigy-ranking.algorithm_core.DL_F14_team_points` tp
--     ON LOWER(TRIM(REGEXP_REPLACE(ps.latestStats_team_name, r' U[0-9]{2}.*| Jr.*| [0-9]$', ''))) =
--        LOWER(TRIM(REGEXP_REPLACE(tp.team_name, r' U[0-9]{2}.*| Jr.*| [0-9]$', '')))
--   GROUP BY ps.id
-- ),
-- ============================================================================
f14_data AS (
  SELECT
    id AS player_id,
    0 AS f14_team_points  -- DISABLED: All team points set to 0
  FROM `prodigy-ranking.algorithm_core.player_stats`
),

-- F15: International Points (CAPPED AT 1000 per config)
-- FIX 2026-01-08: Added GROUP BY to prevent duplicates for players with multiple tournament entries
f15_data AS (
  SELECT
    matched_player_id AS player_id,
    MAX(LEAST(total_international_points, 1000)) AS f15_international_points
  FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`
  GROUP BY matched_player_id
),

-- F16: College Commitment Points
f16_data AS (
  SELECT
    player_id,
    factor_16_commitment_points AS f16_commitment_points
  FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
),

-- F17: Draft Points - FROM FIXED DL_F17_draft_points
f17_data AS (
  SELECT
    player_id,
    points AS f17_draft_points
  FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
),

-- F18: Weekly Points Delta
-- FIX 2026-01-08: Added GROUP BY to prevent duplicates
f18_data AS (
  SELECT
    player_id,
    MAX(factor_18_points) AS f18_weekly_points_delta
  FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
  GROUP BY player_id
),

-- F19: Weekly Assists Delta
-- FIX 2026-01-08: Added GROUP BY to prevent duplicates
f19_data AS (
  SELECT
    player_id,
    MAX(factor_19_points) AS f19_weekly_assists_delta
  FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
  GROUP BY player_id
),

-- F20: Playing Up Points
f20_data AS (
  SELECT
    player_id,
    points AS f20_playing_up_points
  FROM `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`
),

-- F21: Tournament Points
f21_data AS (
  SELECT
    player_id,
    points AS f21_tournament_points
  FROM `prodigy-ranking.algorithm_core.DL_F21_tournament_points`
),

-- F22: Manual Points
f22_data AS (
  SELECT
    player_id,
    points AS f22_manual_points
  FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`
),

-- F23: ProdigyLikes Points
f23_data AS (
  SELECT
    player_id,
    points AS f23_prodigylikes_points
  FROM `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`
),

-- F24: Card Sales Points
f24_data AS (
  SELECT
    player_id,
    points AS f24_card_sales_points
  FROM `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`
),

-- F26: Weight Points (Physical Factor)
f26_data AS (
  SELECT
    player_id,
    factor_26_weight_points AS f26_weight_points
  FROM `prodigy-ranking.algorithm_core.PT_F26_weight`
),

-- F27: BMI Points (Physical Factor)
f27_data AS (
  SELECT
    player_id,
    factor_27_bmi_points AS f27_bmi_points
  FROM `prodigy-ranking.algorithm_core.PT_F27_bmi`
),

-- F25: Weekly EP Views Points (Trending/Visibility Factor)
-- FIX 2026-01-08: Added GROUP BY to prevent duplicates
f25_data AS (
  SELECT
    player_id,
    MAX(factor_25_points) AS f25_weekly_views
  FROM `prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta`
  GROUP BY player_id
)

-- Combine everything with proper JOINs to the fixed source tables
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

  -- Performance Factors (F01-F12)
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

  -- Direct Load Factors (F13-F24) - FROM FIXED SOURCE TABLES
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
  COALESCE(f26.f26_weight_points, 0) AS f26_weight_points,
  COALESCE(f27.f27_bmi_points, 0) AS f27_bmi_points,
  COALESCE(f25.f25_weekly_views, 0) AS f25_weekly_views,

  -- Calculate performance total (F01-F12)
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

  -- Calculate direct load total (F13-F24)
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
    COALESCE(f24.f24_card_sales_points, 0) +
    COALESCE(f26.f26_weight_points, 0) +
    COALESCE(f27.f27_bmi_points, 0) +
    COALESCE(f25.f25_weekly_views, 0)
  ) AS direct_load_total,

  -- Calculate total points
  (
    -- Performance
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
    -- Direct Load
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
    COALESCE(f24.f24_card_sales_points, 0) +
    COALESCE(f26.f26_weight_points, 0) +
    COALESCE(f27.f27_bmi_points, 0) +
    COALESCE(f25.f25_weekly_views, 0)
  ) AS total_points,

  CURRENT_TIMESTAMP() AS calculated_at,
  'v3.3-main-league-file' AS algorithm_version

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
LEFT JOIN f26_data f26 ON bp.player_id = f26.player_id
LEFT JOIN f27_data f27 ON bp.player_id = f27.player_id
LEFT JOIN f25_data f25 ON bp.player_id = f25.player_id;

-- ============================================================================
-- REBUILD player_cumulative_points WITH F31-F37 RATINGS
-- ============================================================================
-- VERSION: v3.0-with-ratings
--
-- This is the CANONICAL rebuild script that includes:
--   - All factor points (F01-F28)
--   - All rating calculations (F31-F37) computed directly in the table
--   - Raw per-game stats for performance calculation transparency
--
-- IMPORTANT: This is the single source of truth for all algorithm data.
--
-- CHANGES in v3.0:
--   - Added F31 (Performance Rating) calculation
--   - Added F32 (Level Rating) from DL_league_category_points lookup
--   - Added F33-F37 rating calculations
--   - Added raw per-game stats columns for debugging/transparency
--   - Added EP views raw count for visibility calculation
--
-- ============================================================================

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_cumulative_points` AS

WITH base_players AS (
  -- Get all unique players from player_stats as the base
  -- Exclude female players (teams with "(W)" suffix)
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
    height_metrics AS height_cm,
    weight_metrics AS weight_kg
  FROM `prodigy-ranking.algorithm_core.player_stats`
  WHERE COALESCE(latestStats_teamName, latestStats_team_name) NOT LIKE '%(W)%'
),

-- =============================================================================
-- PERFORMANCE FACTORS (F01-F12) - Points AND Raw Stats
-- =============================================================================

-- F01: EP Views - both points and raw count
f01_data AS (
  SELECT
    player_id,
    MAX(factor_1_epv_points) AS f01_views,
    MAX(ep_views) AS ep_views_raw  -- Raw count for F33 visibility
  FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
  GROUP BY player_id
),

-- F02: Height
f02_data AS (
  SELECT player_id, MAX(factor_2_h_points) AS f02_height
  FROM `prodigy-ranking.algorithm_core.PT_F02_H`
  GROUP BY player_id
),

-- F03: Forward Current Goals - points AND per-game rate
f03_data AS (
  SELECT
    player_id,
    MAX(factor_3_current_goals_points) AS f03_current_goals_f,
    MAX(goals_per_game) AS f03_goals_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
  GROUP BY player_id
),

-- F04: Defender Current Goals - points AND per-game rate
f04_data AS (
  SELECT
    player_id,
    MAX(factor_4_current_goals_points) AS f04_current_goals_d,
    MAX(goals_per_game) AS f04_goals_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
  GROUP BY player_id
),

-- F05: Current Assists - points AND per-game rate
f05_data AS (
  SELECT
    player_id,
    MAX(factor_5_current_assists_points) AS f05_current_assists,
    MAX(assists_per_game) AS f05_assists_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
  GROUP BY player_id
),

-- F06: Goalie Current GAA - points AND raw GAA
f06_data AS (
  SELECT
    player_id,
    MAX(factor_6_cgaa_points) AS f06_current_gaa,
    MAX(goals_against_average) AS f06_gaa_raw  -- Raw GAA for F31
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
  GROUP BY player_id
),

-- F07: Goalie Current Save % - points AND raw SVP
f07_data AS (
  SELECT
    player_id,
    MAX(factor_7_csv_points) AS f07_current_svp,
    MAX(save_percentage) AS f07_svp_raw  -- Raw save % for F31 (0-100 scale)
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
  GROUP BY player_id
),

-- F08: Forward Last Season Goals - points AND per-game rate
f08_data AS (
  SELECT
    player_id,
    MAX(factor_8_lgpgf_points) AS f08_last_goals_f,
    MAX(last_goals_per_game) AS f08_goals_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
  GROUP BY player_id
),

-- F09: Defender Last Season Goals - points AND per-game rate
f09_data AS (
  SELECT
    player_id,
    MAX(factor_9_lgpgd_points) AS f09_last_goals_d,
    MAX(last_goals_per_game) AS f09_goals_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
  GROUP BY player_id
),

-- F10: Last Season Assists - points AND per-game rate
f10_data AS (
  SELECT
    player_id,
    MAX(factor_10_lapg_points) AS f10_last_assists,
    MAX(last_assists_per_game) AS f10_assists_per_game  -- Raw rate for F31
  FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
  GROUP BY player_id
),

-- F11: Goalie Last Season GAA - points AND raw GAA
f11_data AS (
  SELECT
    player_id,
    MAX(factor_11_lgaa_points) AS f11_last_gaa,
    MAX(last_season_gaa) AS f11_gaa_raw  -- Raw GAA for F31
  FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
  GROUP BY player_id
),

-- F12: Goalie Last Season Save % - points AND raw SVP
f12_data AS (
  SELECT
    player_id,
    MAX(factor_12_lsv_points) AS f12_last_svp,
    MAX(last_season_svp) AS f12_svp_raw  -- Raw save % for F31 (0-100 scale)
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`
  GROUP BY player_id
),

-- =============================================================================
-- DIRECT LOAD FACTORS (F13-F28)
-- =============================================================================

-- =============================================================================
-- F13: LEAGUE POINTS (CANONICAL SOURCE - SAME AS F32)
-- =============================================================================
-- Source: ALGO_ LEAGUE POINTS (1).xlsx - Column I "league points"
-- Table: DL_F32_league_level_points (1,123 leagues)
-- This is the SINGLE SOURCE OF TRUTH for both F13 and F32:
--   - F13 uses: league_points_f13 (Column I)
--   - F32 uses: level_category_points (Column J)
--
-- DEPRECATED tables (do not use for F13):
--   - algorithm_core.DL_all_leagues (old, replaced by this canonical source)
-- =============================================================================
f13_data AS (
  SELECT
    ps.id AS player_id,
    MAX(COALESCE(lp.league_points_f13, 0)) AS f13_league_points
  FROM `prodigy-ranking.algorithm_core.player_stats` ps
  LEFT JOIN `prodigy-ranking.algorithm_core.DL_F32_league_level_points` lp
    ON LOWER(REPLACE(COALESCE(ps.latestStats_league_name, ps.latestStats_team_league_name), ' ', '-')) =
       LOWER(REPLACE(lp.league_name, ' ', '-'))
    OR LOWER(REPLACE(REPLACE(COALESCE(ps.latestStats_league_name, ps.latestStats_team_league_name), ' ', '-'), '-(w)', '')) =
       LOWER(REPLACE(lp.league_name, ' ', '-'))
  GROUP BY ps.id
),

-- F14: Team Points
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

-- F15: International Points
f15_data AS (
  SELECT
    matched_player_id AS player_id,
    MAX(total_international_points) AS f15_international_points
  FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`
  GROUP BY matched_player_id
),

-- F16: College Commitment Points
f16_data AS (
  SELECT player_id, MAX(factor_16_commitment_points) AS f16_commitment_points
  FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
  GROUP BY player_id
),

-- F17: Draft Points
f17_data AS (
  SELECT player_id, MAX(points) AS f17_draft_points
  FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
  GROUP BY player_id
),

-- F18: Weekly Points Delta
f18_data AS (
  SELECT player_id, MAX(factor_18_points) AS f18_weekly_points_delta
  FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
  GROUP BY player_id
),

-- F19: Weekly Assists Delta
f19_data AS (
  SELECT player_id, MAX(factor_19_points) AS f19_weekly_assists_delta
  FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
  GROUP BY player_id
),

-- F20: Playing Up Points
f20_data AS (
  SELECT player_id, MAX(points) AS f20_playing_up_points
  FROM `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`
  GROUP BY player_id
),

-- F21: Tournament Points
f21_data AS (
  SELECT player_id, MAX(points) AS f21_tournament_points
  FROM `prodigy-ranking.algorithm_core.DL_F21_tournament_points`
  GROUP BY player_id
),

-- F22: Manual Points
f22_data AS (
  SELECT player_id, MAX(points) AS f22_manual_points
  FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`
  GROUP BY player_id
),

-- F23: ProdigyLikes Points
f23_data AS (
  SELECT player_id, MAX(points) AS f23_prodigylikes_points
  FROM `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`
  GROUP BY player_id
),

-- F24: Card Sales Points
f24_data AS (
  SELECT player_id, MAX(points) AS f24_card_sales_points
  FROM `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`
  GROUP BY player_id
),

-- F25: Weekly Views Delta
f25_data AS (
  SELECT player_id, MAX(factor_25_points) AS f25_weekly_views
  FROM `prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta`
  GROUP BY player_id
),

-- F26: Weight Points
f26_data AS (
  SELECT player_id, MAX(factor_26_weight_points) AS f26_weight_points
  FROM `prodigy-ranking.algorithm_core.PT_F26_weight`
  GROUP BY player_id
),

-- F27: BMI Points
f27_data AS (
  SELECT player_id, MAX(factor_27_bmi_points) AS f27_bmi_points
  FROM `prodigy-ranking.algorithm_core.PT_F27_bmi`
  GROUP BY player_id
),

-- F28: NHL Scouting Points + Rank/List
f28_data AS (
  SELECT
    player_id,
    MAX(factor_28_nhl_scouting_points) AS f28_nhl_scouting_points,
    MAX(nhl_scouting_rank) AS nhl_scouting_rank,
    MAX(list_type) AS nhl_scouting_list
  FROM `prodigy-ranking.algorithm_core.PT_F28_NHLSR`
  GROUP BY player_id
),

-- =============================================================================
-- F32: LEVEL RATING LOOKUP (CANONICAL SOURCE - SAME AS F13)
-- =============================================================================
-- Source: ALGO_ LEAGUE POINTS (1).xlsx - Column J "level category points"
-- Table: DL_F32_league_level_points (1,123 leagues)
--
-- IMPORTANT: F13 and F32 use the SAME source table:
--   - F13 uses: league_points_f13 (Column I) - for ranking algorithm
--   - F32 uses: level_category_points (Column J) - for card ratings
--
-- NORMALIZATION: Join normalizes league names by:
--   1. Converting to lowercase
--   2. Replacing spaces with dashes
--   3. Stripping "(w)" suffix for women's leagues to match base league
--
-- DEPRECATED tables (do not use):
--   - algorithm.DL_league_category_points (old F32 source)
--   - algorithm_core.DL_all_leagues (old F13 source)
-- =============================================================================
league_tiers AS (
  SELECT
    LOWER(REPLACE(league_name, ' ', '-')) AS normalized_league_name,
    level_category_points AS level_rating
  FROM `prodigy-ranking.algorithm_core.DL_F32_league_level_points`
),

-- =============================================================================
-- COMBINE ALL DATA
-- =============================================================================
combined AS (
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
    bp.height_cm,
    bp.weight_kg,

    -- Factor Points (F01-F28)
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
    COALESCE(f25.f25_weekly_views, 0.0) AS f25_weekly_views,
    COALESCE(f26.f26_weight_points, 0.0) AS f26_weight_points,
    COALESCE(f27.f27_bmi_points, 0.0) AS f27_bmi_points,
    COALESCE(f28.f28_nhl_scouting_points, 0.0) AS f28_nhl_scouting_points,
    f28.nhl_scouting_rank,
    f28.nhl_scouting_list,

    -- Raw per-game stats for F31 Performance calculation
    COALESCE(f01.ep_views_raw, 0) AS ep_views_raw,
    COALESCE(f03.f03_goals_per_game, 0.0) AS f03_goals_per_game,
    COALESCE(f04.f04_goals_per_game, 0.0) AS f04_goals_per_game,
    COALESCE(f05.f05_assists_per_game, 0.0) AS f05_assists_per_game,
    COALESCE(f06.f06_gaa_raw, 0.0) AS f06_gaa_raw,
    COALESCE(f07.f07_svp_raw, 0.0) AS f07_svp_raw,
    COALESCE(f08.f08_goals_per_game, 0.0) AS f08_goals_per_game,
    COALESCE(f09.f09_goals_per_game, 0.0) AS f09_goals_per_game,
    COALESCE(f10.f10_assists_per_game, 0.0) AS f10_assists_per_game,
    COALESCE(f11.f11_gaa_raw, 0.0) AS f11_gaa_raw,
    COALESCE(f12.f12_svp_raw, 0.0) AS f12_svp_raw,

    -- F32: Level Rating from lookup table
    COALESCE(lt.level_rating,
      -- Fallback scaling if league not in lookup
      CASE
        WHEN COALESCE(f13.f13_league_points, 0) >= 4000 THEN 95 + CAST((COALESCE(f13.f13_league_points, 0) - 4000) / 125.0 AS INT64)
        WHEN COALESCE(f13.f13_league_points, 0) >= 3000 THEN 80 + CAST((COALESCE(f13.f13_league_points, 0) - 3000) / 66.7 AS INT64)
        WHEN COALESCE(f13.f13_league_points, 0) >= 2000 THEN 60 + CAST((COALESCE(f13.f13_league_points, 0) - 2000) / 50.0 AS INT64)
        WHEN COALESCE(f13.f13_league_points, 0) >= 1000 THEN 40 + CAST((COALESCE(f13.f13_league_points, 0) - 1000) / 50.0 AS INT64)
        WHEN COALESCE(f13.f13_league_points, 0) >= 500 THEN 20 + CAST((COALESCE(f13.f13_league_points, 0) - 500) / 25.0 AS INT64)
        WHEN COALESCE(f13.f13_league_points, 0) > 0 THEN 1 + CAST(COALESCE(f13.f13_league_points, 0) / 26.3 AS INT64)
        ELSE 1
      END
    ) AS f32_level_rating

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
  LEFT JOIN f25_data f25 ON bp.player_id = f25.player_id
  LEFT JOIN f26_data f26 ON bp.player_id = f26.player_id
  LEFT JOIN f27_data f27 ON bp.player_id = f27.player_id
  LEFT JOIN f28_data f28 ON bp.player_id = f28.player_id
  -- F32 Level Rating: Join with normalization (spaces->dashes, strip (w) suffix)
  LEFT JOIN league_tiers lt ON
    LOWER(REPLACE(REPLACE(bp.current_league, ' ', '-'), '-(w)', '')) = lt.normalized_league_name
    OR LOWER(REPLACE(bp.current_league, ' ', '-')) = lt.normalized_league_name
)

-- =============================================================================
-- FINAL OUTPUT WITH ALL RATINGS (F31-F37)
-- =============================================================================
SELECT
  player_id,
  player_name,
  position,
  birth_year,
  nationality_name,
  current_team,
  current_league,
  current_season,
  team_country,
  height_cm,
  weight_kg,

  -- Factor Points (F01-F28)
  f01_views,
  f02_height,
  f03_current_goals_f,
  f04_current_goals_d,
  f05_current_assists,
  f06_current_gaa,
  f07_current_svp,
  f08_last_goals_f,
  f09_last_goals_d,
  f10_last_assists,
  f11_last_gaa,
  f12_last_svp,
  f13_league_points,
  f14_team_points,
  f15_international_points,
  f16_commitment_points,
  f17_draft_points,
  f18_weekly_points_delta,
  f19_weekly_assists_delta,
  f20_playing_up_points,
  f21_tournament_points,
  f22_manual_points,
  f23_prodigylikes_points,
  f24_card_sales_points,
  f25_weekly_views,
  f26_weight_points,
  f27_bmi_points,
  f28_nhl_scouting_points,
  nhl_scouting_rank,
  nhl_scouting_list,

  -- Raw per-game stats (for transparency/debugging)
  ep_views_raw,
  f03_goals_per_game,
  f04_goals_per_game,
  f05_assists_per_game,
  f06_gaa_raw,
  f07_svp_raw,
  f08_goals_per_game,
  f09_goals_per_game,
  f10_assists_per_game,
  f11_gaa_raw,
  f12_svp_raw,

  -- =========================================================================
  -- F31: PERFORMANCE RATING (0-99)
  -- Forwards: IF 0.7*(F03+F05) + 0.3*(F08+F10) >= 1.0 THEN 99 ELSE ROUND(98 * combined)
  -- Defenders: IF combined >= 0.8 THEN 99 ELSE ROUND(98 * combined / 0.8)
  -- Goalies: Average of GAA rating and SVP rating
  -- =========================================================================
  CASE
    WHEN position = 'F' THEN
      CASE
        -- Has current season data
        WHEN f03_goals_per_game + f05_assists_per_game > 0 THEN
          CASE
            WHEN 0.7 * (f03_goals_per_game + f05_assists_per_game) + 0.3 * (f08_goals_per_game + f10_assists_per_game) >= 1.0 THEN 99
            ELSE GREATEST(0, CAST(ROUND(98 * (0.7 * (f03_goals_per_game + f05_assists_per_game) + 0.3 * (f08_goals_per_game + f10_assists_per_game))) AS INT64))
          END
        -- No current season: use 70% of last season
        ELSE
          CASE
            WHEN 0.7 * (f08_goals_per_game + f10_assists_per_game) >= 1.0 THEN 99
            ELSE GREATEST(0, CAST(ROUND(98 * 0.7 * (f08_goals_per_game + f10_assists_per_game)) AS INT64))
          END
      END

    WHEN position = 'D' THEN
      CASE
        -- Has current season data
        WHEN f04_goals_per_game + f05_assists_per_game > 0 THEN
          CASE
            WHEN 0.7 * (f04_goals_per_game + f05_assists_per_game) + 0.3 * (f09_goals_per_game + f10_assists_per_game) >= 0.8 THEN 99
            ELSE GREATEST(0, CAST(ROUND(98 * (0.7 * (f04_goals_per_game + f05_assists_per_game) + 0.3 * (f09_goals_per_game + f10_assists_per_game)) / 0.8) AS INT64))
          END
        -- No current season: use 70% of last season
        ELSE
          CASE
            WHEN 0.7 * (f09_goals_per_game + f10_assists_per_game) >= 0.8 THEN 99
            ELSE GREATEST(0, CAST(ROUND(98 * 0.7 * (f09_goals_per_game + f10_assists_per_game) / 0.8) AS INT64))
          END
      END

    WHEN position = 'G' THEN
      LEAST(99, GREATEST(0, CAST(ROUND((
        -- GAA rating (lower is better)
        CASE
          WHEN f06_gaa_raw > 0 THEN
            CASE
              WHEN 0.7 * f06_gaa_raw + 0.3 * f11_gaa_raw <= 5 THEN 0.1 + 98 * (1 - (0.7 * f06_gaa_raw + 0.3 * f11_gaa_raw) / 5)
              ELSE 0
            END
          WHEN f11_gaa_raw > 0 THEN
            CASE
              WHEN 0.7 * f11_gaa_raw <= 5 THEN 0.1 + 98 * (1 - 0.7 * f11_gaa_raw / 5)
              ELSE 0
            END
          ELSE 0
        END
        +
        -- SVP rating (higher is better, 0-100 scale)
        CASE
          WHEN f07_svp_raw > 0 THEN
            CASE
              WHEN 0.7 * f07_svp_raw + 0.3 * f12_svp_raw >= 88.0 THEN 0.1 + 98 * ((0.7 * f07_svp_raw + 0.3 * f12_svp_raw - 50) / 49.9)
              ELSE 0
            END
          WHEN f12_svp_raw > 0 THEN
            CASE
              WHEN 0.7 * f12_svp_raw >= 88.0 THEN 0.1 + 98 * ((0.7 * f12_svp_raw - 50) / 49.9)
              ELSE 0
            END
          ELSE 0
        END
      ) / 2) AS INT64)))

    ELSE 0
  END AS f31_performance_rating,

  -- F32: Level Rating (already calculated in combined CTE)
  CAST(LEAST(99, GREATEST(1, f32_level_rating)) AS INT64) AS f32_level_rating,

  -- =========================================================================
  -- F33: VISIBILITY RATING (0-99)
  -- Linear: 100-15000 views maps to 0-99
  -- =========================================================================
  CASE
    WHEN ep_views_raw < 100 THEN 0
    WHEN ep_views_raw >= 15000 THEN 99
    ELSE CAST(ROUND(99.0 * (ep_views_raw - 100) / 14900) AS INT64)
  END AS f33_visibility_rating,

  -- =========================================================================
  -- F34: PHYSICAL RATING (0-99)
  -- Formula: (F02 + F26 + F27) / 600 * 99
  -- =========================================================================
  CAST(LEAST(99, GREATEST(0, ROUND((LEAST(f02_height, 200) + f26_weight_points + f27_bmi_points) / 600.0 * 99))) AS INT64) AS f34_physical_rating,

  -- =========================================================================
  -- F35: ACHIEVEMENTS RATING (0-99)
  -- Formula: IF (F15+F16+F17+F21+F22) >= 1500 THEN 99 ELSE ROUND(99 * sum / 1500)
  -- =========================================================================
  CASE
    WHEN f15_international_points + f16_commitment_points + f17_draft_points + f21_tournament_points + f22_manual_points >= 1500 THEN 99
    ELSE CAST(ROUND(99.0 * (f15_international_points + f16_commitment_points + f17_draft_points + f21_tournament_points + f22_manual_points) / 1500) AS INT64)
  END AS f35_achievements_rating,

  -- =========================================================================
  -- F36: TRENDING RATING (0-99)
  -- Skaters: IF (F18+F19+F25) >= 250 THEN 99 ELSE ROUND(99 * sum / 250)
  -- Goalies: IF F25 >= 50 THEN 99 ELSE ROUND(99 * F25 / 50)
  -- =========================================================================
  CASE
    WHEN position IN ('F', 'D') THEN
      CASE
        WHEN f18_weekly_points_delta + f19_weekly_assists_delta + f25_weekly_views >= 250 THEN 99
        ELSE CAST(ROUND(99.0 * (f18_weekly_points_delta + f19_weekly_assists_delta + f25_weekly_views) / 250) AS INT64)
      END
    WHEN position = 'G' THEN
      CASE
        WHEN f25_weekly_views >= 50 THEN 99
        ELSE CAST(ROUND(99.0 * f25_weekly_views / 50) AS INT64)
      END
    ELSE 0
  END AS f36_trending_rating,

  -- Calculate totals
  (f01_views + f02_height + f03_current_goals_f + f04_current_goals_d + f05_current_assists +
   f06_current_gaa + f07_current_svp + f08_last_goals_f + f09_last_goals_d + f10_last_assists +
   f11_last_gaa + f12_last_svp) AS performance_total,

  (f13_league_points + f14_team_points + f15_international_points + f16_commitment_points +
   f17_draft_points + f18_weekly_points_delta + f19_weekly_assists_delta + f20_playing_up_points +
   f21_tournament_points + f22_manual_points + f23_prodigylikes_points + f24_card_sales_points +
   f25_weekly_views + f26_weight_points + f27_bmi_points + f28_nhl_scouting_points) AS direct_load_total,

  (f01_views + f02_height + f03_current_goals_f + f04_current_goals_d + f05_current_assists +
   f06_current_gaa + f07_current_svp + f08_last_goals_f + f09_last_goals_d + f10_last_assists +
   f11_last_gaa + f12_last_svp + f13_league_points + f14_team_points + f15_international_points +
   f16_commitment_points + f17_draft_points + f18_weekly_points_delta + f19_weekly_assists_delta +
   f20_playing_up_points + f21_tournament_points + f22_manual_points + f23_prodigylikes_points +
   f24_card_sales_points + f25_weekly_views + f26_weight_points + f27_bmi_points +
   f28_nhl_scouting_points) AS total_points,

  CURRENT_TIMESTAMP() AS calculated_at,
  'v3.0-with-ratings' AS algorithm_version

FROM combined;


-- =============================================================================
-- After rebuilding, update the VIEW to read stored ratings instead of calculating
-- =============================================================================
-- Run create_ea_ratings_view_v5.sql after this to update the view
-- The view will now simply SELECT from this table's pre-computed ratings
-- =============================================================================

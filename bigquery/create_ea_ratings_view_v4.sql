-- =====================================================================
-- EA SPORTS-STYLE PLAYER RATINGS VIEW - VERSION 4.0
-- =====================================================================
-- Updated: 2026-01-08
--
-- MAJOR CHANGE: Complete rewrite of PERFORMANCE rating calculation
--
-- OLD METHOD (v3.x):
--   - Used pre-calculated factor POINTS (f03, f04, f05, etc.)
--   - Summed points together
--   - Applied percentile-based curve to convert to 1-99
--
-- NEW METHOD (v4.0) - Per David's specification:
--   - Uses RAW per-game statistics from PT factor tables
--   - Applies 0.7/0.3 weighting (current season 70%, past season 30%)
--   - Position-specific threshold-based conversion to 0-99
--
-- PERFORMANCE FORMULAS (0-99 scale):
--
--   Forwards (F):
--     combined = 0.7 × (current_goals_pg + current_assists_pg)
--              + 0.3 × (past_goals_pg + past_assists_pg)
--     IF combined >= 1.0 THEN 99
--     ELSE ROUND(98 × combined)
--
--   Defensemen (D):
--     combined = 0.7 × (current_goals_pg + current_assists_pg)
--              + 0.3 × (past_goals_pg + past_assists_pg)
--     IF combined >= 0.8 THEN 99
--     ELSE ROUND(98 × combined / 0.8)
--
--   Goalies (G):
--     gaa_score = 0.7 × current_GAA + 0.3 × past_GAA
--     svp_score = 0.7 × current_save_pct + 0.3 × past_save_pct
--
--     gaa_rating = IF gaa_score <= 5 THEN (0.1 + 98 × (1 - gaa_score/5)) ELSE 0
--     svp_rating = IF svp_score >= 0.880 THEN (0.1 + 98 × ((svp_score × 1000 - 500) / 499)) ELSE 0
--
--     performance = ROUND((gaa_rating + svp_rating) / 2)
--
-- Other categories unchanged from v3.1:
--   - Level (70%)       - Direct league tier mapping
--   - Visibility (19%)  - EP views + ProdigyLikes
--   - Physical (5%)     - Height + Weight + BMI
--   - Achievements (3%) - International, draft, college, tournaments
--   - Trending (0%)     - Weekly momentum (not used)
-- =====================================================================

CREATE OR REPLACE VIEW `prodigy-ranking.algorithm_core.player_card_ratings` AS

WITH
-- Step 1: Get league tier ratings from lookup table
league_tiers AS (
  SELECT
    league_name,
    level_category_points as league_tier_rating
  FROM `prodigy-ranking.algorithm.DL_league_category_points`
),

-- Step 2: Get F26/F27 physical data
physical_data AS (
  SELECT
    w.player_id,
    COALESCE(w.factor_26_weight_points, 0) as f26_weight_points,
    COALESCE(b.factor_27_bmi_points, 0) as f27_bmi_points
  FROM `prodigy-ranking.algorithm_core.PT_F26_weight` w
  FULL OUTER JOIN `prodigy-ranking.algorithm_core.PT_F27_bmi` b
    ON w.player_id = b.player_id
),

-- Step 3: Get RAW per-game stats for PERFORMANCE calculation
-- Forward current goals per game
f03_raw AS (
  SELECT player_id, current_goals_per_game AS current_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
),
-- Defensemen current goals per game
f04_raw AS (
  SELECT player_id, current_goals_per_game AS current_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
),
-- Current assists per game (all skaters)
f05_raw AS (
  SELECT player_id, current_assists_per_game AS current_assists_pg
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
),
-- Goalie current GAA
f06_raw AS (
  SELECT player_id, goals_against_average AS current_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
),
-- Goalie current save percentage
f07_raw AS (
  SELECT player_id, save_percentage AS current_svp
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
),
-- Forward last season goals per game
f08_raw AS (
  SELECT player_id, last_goals_per_game AS past_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
),
-- Defensemen last season goals per game
f09_raw AS (
  SELECT player_id, last_goals_per_game AS past_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
),
-- Last season assists per game (all skaters)
f10_raw AS (
  SELECT player_id, last_assists_per_game AS past_assists_pg
  FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
),
-- Goalie last season GAA
f11_raw AS (
  SELECT player_id, last_season_gaa AS past_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
),
-- Goalie last season save percentage
f12_raw AS (
  SELECT player_id, last_season_svp AS past_svp
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`
),

-- Step 4: Calculate raw category scores with NEW PERFORMANCE FORMULA
raw_scores AS (
  SELECT
    p.player_id,
    p.player_name,
    p.position,
    p.birth_year,
    p.nationality_name,
    p.current_team,
    p.current_league,
    p.team_country,
    p.total_points,

    -- =========================================================================
    -- PERFORMANCE: NEW FORMULA using raw per-game stats with 0.7/0.3 weighting
    -- =========================================================================
    CASE
      WHEN p.position = 'F' THEN
        -- Forwards: combined = 0.7*(current_goals+current_assists) + 0.3*(past_goals+past_assists)
        0.7 * (COALESCE(f03.current_goals_pg, 0) + COALESCE(f05.current_assists_pg, 0)) +
        0.3 * (COALESCE(f08.past_goals_pg, 0) + COALESCE(f10.past_assists_pg, 0))
      WHEN p.position = 'D' THEN
        -- Defensemen: same formula
        0.7 * (COALESCE(f04.current_goals_pg, 0) + COALESCE(f05.current_assists_pg, 0)) +
        0.3 * (COALESCE(f09.past_goals_pg, 0) + COALESCE(f10.past_assists_pg, 0))
      ELSE 0  -- Goalies handled separately
    END AS skater_combined,

    -- Goalie intermediate scores
    -- GAA is stored as actual value (e.g., 2.95)
    CASE WHEN p.position = 'G' THEN
      0.7 * COALESCE(f06.current_gaa, 0) + 0.3 * COALESCE(f11.past_gaa, 0)
    ELSE NULL END AS goalie_gaa_score,

    -- Save percentage is stored as whole number (e.g., 90.0 = 90%)
    -- Convert to decimal by dividing by 100 (90.0 -> 0.900)
    CASE WHEN p.position = 'G' THEN
      0.7 * (COALESCE(f07.current_svp, 0) / 100.0) + 0.3 * (COALESCE(f12.past_svp, 0) / 100.0)
    ELSE NULL END AS goalie_svp_score,

    -- LEVEL: Uses lookup table if available, otherwise scales F13 league points
    CASE
      WHEN lt.league_tier_rating IS NOT NULL THEN lt.league_tier_rating
      WHEN COALESCE(p.f13_league_points, 0) >= 4000 THEN 95 + CAST((COALESCE(p.f13_league_points, 0) - 4000) / 125.0 AS INT64)
      WHEN COALESCE(p.f13_league_points, 0) >= 3000 THEN 80 + CAST((COALESCE(p.f13_league_points, 0) - 3000) / 66.7 AS INT64)
      WHEN COALESCE(p.f13_league_points, 0) >= 2000 THEN 60 + CAST((COALESCE(p.f13_league_points, 0) - 2000) / 50.0 AS INT64)
      WHEN COALESCE(p.f13_league_points, 0) >= 1000 THEN 40 + CAST((COALESCE(p.f13_league_points, 0) - 1000) / 50.0 AS INT64)
      WHEN COALESCE(p.f13_league_points, 0) >= 500 THEN 20 + CAST((COALESCE(p.f13_league_points, 0) - 500) / 25.0 AS INT64)
      WHEN COALESCE(p.f13_league_points, 0) > 0 THEN 1 + CAST(COALESCE(p.f13_league_points, 0) / 26.3 AS INT64)
      ELSE 1
    END AS level_tier_rating,

    -- Keep level_raw for reference
    COALESCE(p.f13_league_points, 0) + COALESCE(p.f14_team_points, 0) AS level_raw,

    -- VISIBILITY: Views + ProdigyLikes
    COALESCE(p.f01_views, 0) + COALESCE(p.f23_prodigylikes_points, 0) AS visibility_raw,

    -- ACHIEVEMENTS: International (capped) + College + Draft + Tournaments
    LEAST(COALESCE(p.f15_international_points, 0), 1000) +
    COALESCE(p.f16_commitment_points, 0) +
    COALESCE(p.f17_draft_points, 0) +
    COALESCE(p.f21_tournament_points, 0) AS achievements_raw,

    -- TRENDING: Weekly deltas
    COALESCE(p.f18_weekly_points_delta, 0) + COALESCE(p.f19_weekly_assists_delta, 0) AS trending_raw,

    -- PHYSICAL: Height (capped) + Weight + BMI
    LEAST(COALESCE(p.f02_height, 0), 200) +
    COALESCE(pd.f26_weight_points, 0) +
    COALESCE(pd.f27_bmi_points, 0) AS physical_raw,

    -- Keep individual factors for reference
    COALESCE(p.f01_views, 0) AS f01_views,
    LEAST(COALESCE(p.f02_height, 0), 200) AS f02_height,
    COALESCE(p.f13_league_points, 0) AS f13_league_points,
    COALESCE(p.f14_team_points, 0) AS f14_team_points,
    LEAST(COALESCE(p.f15_international_points, 0), 1000) AS f15_international_points,
    COALESCE(p.f16_commitment_points, 0) AS f16_commitment_points,
    COALESCE(p.f17_draft_points, 0) AS f17_draft_points,
    COALESCE(pd.f26_weight_points, 0) AS f26_weight_points,
    COALESCE(pd.f27_bmi_points, 0) AS f27_bmi_points,

    -- Raw per-game stats for debugging
    COALESCE(f03.current_goals_pg, 0) AS current_goals_pg_f,
    COALESCE(f04.current_goals_pg, 0) AS current_goals_pg_d,
    COALESCE(f05.current_assists_pg, 0) AS current_assists_pg,
    COALESCE(f08.past_goals_pg, 0) AS past_goals_pg_f,
    COALESCE(f09.past_goals_pg, 0) AS past_goals_pg_d,
    COALESCE(f10.past_assists_pg, 0) AS past_assists_pg,
    COALESCE(f06.current_gaa, 0) AS current_gaa,
    COALESCE(f07.current_svp, 0) / 100.0 AS current_svp,  -- Convert to decimal (90.0 -> 0.900)
    COALESCE(f11.past_gaa, 0) AS past_gaa,
    COALESCE(f12.past_svp, 0) / 100.0 AS past_svp,  -- Convert to decimal

    p.calculated_at,
    p.algorithm_version

  FROM `prodigy-ranking.algorithm_core.player_cumulative_points` p
  LEFT JOIN league_tiers lt ON LOWER(p.current_league) = lt.league_name
  LEFT JOIN physical_data pd ON p.player_id = pd.player_id
  -- Raw stats joins
  LEFT JOIN f03_raw f03 ON p.player_id = f03.player_id
  LEFT JOIN f04_raw f04 ON p.player_id = f04.player_id
  LEFT JOIN f05_raw f05 ON p.player_id = f05.player_id
  LEFT JOIN f06_raw f06 ON p.player_id = f06.player_id
  LEFT JOIN f07_raw f07 ON p.player_id = f07.player_id
  LEFT JOIN f08_raw f08 ON p.player_id = f08.player_id
  LEFT JOIN f09_raw f09 ON p.player_id = f09.player_id
  LEFT JOIN f10_raw f10 ON p.player_id = f10.player_id
  LEFT JOIN f11_raw f11 ON p.player_id = f11.player_id
  LEFT JOIN f12_raw f12 ON p.player_id = f12.player_id
  WHERE p.total_points > 0
),

-- Step 5: Calculate percentile ranks for non-performance categories
percentile_ranks AS (
  SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY visibility_raw) * 100 AS visibility_pct,
    PERCENT_RANK() OVER (ORDER BY achievements_raw) * 100 AS achievements_pct,
    PERCENT_RANK() OVER (ORDER BY trending_raw) * 100 AS trending_pct,
    PERCENT_RANK() OVER (ORDER BY physical_raw) * 100 AS physical_pct
  FROM raw_scores
),

-- Step 6: Convert to EA-style ratings (0-99 scale)
ea_ratings AS (
  SELECT
    *,

    -- =========================================================================
    -- PERFORMANCE RATING: NEW DIRECT THRESHOLD FORMULA (not percentile-based)
    -- =========================================================================
    CASE
      -- FORWARDS: IF combined >= 1.0 THEN 99 ELSE ROUND(98 × combined)
      WHEN position = 'F' THEN
        CASE
          WHEN skater_combined >= 1.0 THEN 99
          ELSE CAST(ROUND(98 * skater_combined) AS INT64)
        END

      -- DEFENSEMEN: IF combined >= 0.8 THEN 99 ELSE ROUND(98 × combined / 0.8)
      WHEN position = 'D' THEN
        CASE
          WHEN skater_combined >= 0.8 THEN 99
          ELSE CAST(ROUND(98 * skater_combined / 0.8) AS INT64)
        END

      -- GOALIES: Complex formula with GAA and SVP
      -- Note: Some source data has invalid save percentages (>100%), so we cap svp_score at 1.0
      WHEN position = 'G' THEN
        LEAST(99, GREATEST(0, CAST(ROUND((
          -- gaa_rating = IF gaa_score <= 5 THEN (0.1 + 98 × (1 - gaa_score/5)) ELSE 0
          CASE
            WHEN goalie_gaa_score <= 5 AND goalie_gaa_score > 0 THEN 0.1 + 98 * (1 - goalie_gaa_score / 5)
            WHEN goalie_gaa_score = 0 THEN 99  -- Perfect GAA
            ELSE 0
          END
          +
          -- svp_rating = IF svp_score >= 0.880 THEN (0.1 + 98 × ((svp_score × 1000 - 500) / 499)) ELSE 0
          -- Cap svp_score at 1.0 to handle bad data
          CASE
            WHEN LEAST(goalie_svp_score, 1.0) >= 0.880 THEN 0.1 + 98 * ((LEAST(goalie_svp_score, 1.0) * 1000 - 500) / 499)
            ELSE 0
          END
        ) / 2) AS INT64)))  -- Average of GAA and SVP ratings, capped at 0-99

      ELSE 0
    END AS performance_rating,

    -- Level Rating: DIRECT TIER MAPPING (unchanged)
    CAST(GREATEST(1, level_tier_rating) AS INT64) AS level_rating,

    -- Visibility Rating (percentile-based curve, 1-99 scale)
    CAST(GREATEST(1, CASE
      WHEN visibility_pct >= 99.9 THEN 99
      WHEN visibility_pct >= 99 THEN 95 + (visibility_pct - 99) * 4
      WHEN visibility_pct >= 95 THEN 90 + (visibility_pct - 95) * 1.25
      WHEN visibility_pct >= 80 THEN 75 + (visibility_pct - 80) * 1
      WHEN visibility_pct >= 50 THEN 50 + (visibility_pct - 50) * 0.83
      WHEN visibility_pct >= 20 THEN 25 + (visibility_pct - 20) * 0.83
      ELSE 1 + visibility_pct * 1.2
    END) AS INT64) AS visibility_rating,

    -- Achievements Rating (percentile-based curve, 1-99 scale)
    CAST(GREATEST(1, CASE
      WHEN achievements_pct >= 99.9 THEN 99
      WHEN achievements_pct >= 99 THEN 95 + (achievements_pct - 99) * 4
      WHEN achievements_pct >= 95 THEN 90 + (achievements_pct - 95) * 1.25
      WHEN achievements_pct >= 80 THEN 75 + (achievements_pct - 80) * 1
      WHEN achievements_pct >= 50 THEN 50 + (achievements_pct - 50) * 0.83
      WHEN achievements_pct >= 20 THEN 25 + (achievements_pct - 20) * 0.83
      ELSE 1 + achievements_pct * 1.2
    END) AS INT64) AS achievements_rating,

    -- Trending Rating (percentile-based curve, 1-99 scale)
    CAST(GREATEST(1, CASE
      WHEN trending_pct >= 99.9 THEN 99
      WHEN trending_pct >= 99 THEN 95 + (trending_pct - 99) * 4
      WHEN trending_pct >= 95 THEN 90 + (trending_pct - 95) * 1.25
      WHEN trending_pct >= 80 THEN 75 + (trending_pct - 80) * 1
      WHEN trending_pct >= 50 THEN 50 + (trending_pct - 50) * 0.83
      WHEN trending_pct >= 20 THEN 25 + (trending_pct - 20) * 0.83
      ELSE 1 + trending_pct * 1.2
    END) AS INT64) AS trending_rating,

    -- Physical Rating: FORMULA-BASED (1-99 scale)
    CAST(
      GREATEST(1, LEAST(99,
        1 + (physical_raw / 600.0) * 98
      ))
    AS INT64) AS physical_rating

  FROM percentile_ranks
)

-- Final output with category weights
-- Performance 3%, Level 70%, Visibility 19%, Physical 5%, Achievements 3%, Trending 0%
SELECT
  player_id,
  player_name,
  position,
  birth_year,
  nationality_name,
  current_team,
  current_league,
  team_country,
  total_points,

  -- Overall Rating with weights
  LEAST(99, GREATEST(1, CAST(
    performance_rating * 0.03 +
    level_rating * 0.70 +
    visibility_rating * 0.19 +
    physical_rating * 0.05 +
    achievements_rating * 0.03 +
    trending_rating * 0.00
  AS INT64))) AS overall_rating,

  -- Category Ratings
  performance_rating,
  level_rating,
  visibility_rating,
  achievements_rating,
  trending_rating,
  physical_rating,

  -- Abbreviations for compact display
  performance_rating AS perf,
  level_rating AS lvl,
  visibility_rating AS vis,
  achievements_rating AS ach,
  trending_rating AS trd,
  physical_rating AS phy,

  -- Raw intermediate values for debugging
  ROUND(skater_combined, 4) AS skater_combined_ppg,
  ROUND(goalie_gaa_score, 4) AS goalie_gaa_weighted,
  ROUND(goalie_svp_score, 4) AS goalie_svp_weighted,

  -- Raw per-game stats
  ROUND(current_goals_pg_f, 3) AS current_goals_pg_f,
  ROUND(current_goals_pg_d, 3) AS current_goals_pg_d,
  ROUND(current_assists_pg, 3) AS current_assists_pg,
  ROUND(past_goals_pg_f, 3) AS past_goals_pg_f,
  ROUND(past_goals_pg_d, 3) AS past_goals_pg_d,
  ROUND(past_assists_pg, 3) AS past_assists_pg,
  ROUND(current_gaa, 3) AS current_gaa,
  ROUND(current_svp, 4) AS current_svp,
  ROUND(past_gaa, 3) AS past_gaa,
  ROUND(past_svp, 4) AS past_svp,

  -- Other raw scores
  ROUND(level_raw, 2) AS level_raw,
  ROUND(visibility_raw, 2) AS visibility_raw,
  ROUND(achievements_raw, 2) AS achievements_raw,
  ROUND(trending_raw, 2) AS trending_raw,
  ROUND(physical_raw, 2) AS physical_raw,

  -- Key factors
  f01_views,
  f02_height,
  f13_league_points,
  f14_team_points,
  f15_international_points,
  f16_commitment_points,
  f17_draft_points,
  f26_weight_points,
  f27_bmi_points,

  -- Metadata
  calculated_at,
  algorithm_version,
  'v4.0-performance-formula' AS ratings_version,
  CURRENT_TIMESTAMP() AS ratings_generated_at

FROM ea_ratings
ORDER BY overall_rating DESC, total_points DESC;

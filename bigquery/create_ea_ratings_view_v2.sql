-- =====================================================================
-- EA SPORTS-STYLE PLAYER RATINGS VIEW - VERSION 2.0
-- =====================================================================
-- Updated: 2025-12-18
-- Changes from v1:
--   1. Fixed category weights to match spreadsheet spec
--   2. Level rating now uses direct league tier mapping (not percentile)
--   3. Physical rating now includes F26 (Weight) + F27 (BMI)
--   4. F02 Height capped at 200 max points
--   5. F15 International capped at 1000 max points
--
-- Categories & Weights (per spreadsheet):
--   1. Performance (15%) - Goals, assists, goalie stats
--   2. Level (35%)       - Direct league tier mapping (NHL=99, CHL=95, etc.)
--   3. Visibility (20%)  - EP views + ProdigyLikes
--   4. Physical (15%)    - Height + Weight + BMI formula
--   5. Achievements (10%)- International, draft, college, tournaments
--   6. Trending (5%)     - Weekly momentum
--
-- Rating Scale (EA Sports style):
--   99: NHL only (elite superstars)
--   95: CHL (OHL, WHL, QMJHL), KHL, top EU leagues
--   90-94: Top junior/pro leagues
--   80-89: Strong leagues
--   70-79: Above average
--   60-69: Average players
--   50-59: Below average
--   40-49: Lowest rated
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

-- Step 3: Calculate raw category scores for each player with caps applied
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

    -- PERFORMANCE: Position-specific stats (unchanged)
    CASE
      WHEN p.position = 'F' THEN
        COALESCE(p.f03_current_goals_f, 0) + COALESCE(p.f05_current_assists, 0) +
        COALESCE(p.f08_last_goals_f, 0) + COALESCE(p.f10_last_assists, 0)
      WHEN p.position = 'D' THEN
        COALESCE(p.f04_current_goals_d, 0) + COALESCE(p.f05_current_assists, 0) +
        COALESCE(p.f09_last_goals_d, 0) + COALESCE(p.f10_last_assists, 0)
      ELSE -- Goalie
        COALESCE(p.f06_current_gaa, 0) + COALESCE(p.f07_current_svp, 0) +
        COALESCE(p.f11_last_gaa, 0) + COALESCE(p.f12_last_svp, 0)
    END AS performance_raw,

    -- LEVEL: Now uses direct tier rating from lookup table
    COALESCE(lt.league_tier_rating, 40) AS level_tier_rating,

    -- Keep level_raw for reference (F13 + F14)
    COALESCE(p.f13_league_points, 0) + COALESCE(p.f14_team_points, 0) AS level_raw,

    -- VISIBILITY: Views + ProdigyLikes
    COALESCE(p.f01_views, 0) + COALESCE(p.f23_prodigylikes_points, 0) AS visibility_raw,

    -- ACHIEVEMENTS: International (capped at 1000) + College + Draft + Tournaments
    LEAST(COALESCE(p.f15_international_points, 0), 1000) +
    COALESCE(p.f16_commitment_points, 0) +
    COALESCE(p.f17_draft_points, 0) +
    COALESCE(p.f21_tournament_points, 0) AS achievements_raw,

    -- TRENDING: Weekly deltas
    COALESCE(p.f18_weekly_points_delta, 0) + COALESCE(p.f19_weekly_assists_delta, 0) AS trending_raw,

    -- PHYSICAL: Height (capped at 200) + Weight + BMI
    -- Formula: ((F02 + F26 + F27) / 600) * 100 = percentage of max possible
    LEAST(COALESCE(p.f02_height, 0), 200) AS f02_height_capped,
    COALESCE(pd.f26_weight_points, 0) AS f26_weight_points,
    COALESCE(pd.f27_bmi_points, 0) AS f27_bmi_points,

    -- Physical raw is sum of all three factors
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

    p.calculated_at,
    p.algorithm_version

  FROM `prodigy-ranking.algorithm_core.player_cumulative_points` p
  LEFT JOIN league_tiers lt ON LOWER(p.current_league) = lt.league_name
  LEFT JOIN physical_data pd ON p.player_id = pd.player_id
  WHERE p.total_points > 0
),

-- Step 4: Calculate percentile ranks for categories that use percentile-based ratings
percentile_ranks AS (
  SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY performance_raw) * 100 AS performance_pct,
    -- Level uses direct tier rating, not percentile
    PERCENT_RANK() OVER (ORDER BY visibility_raw) * 100 AS visibility_pct,
    PERCENT_RANK() OVER (ORDER BY achievements_raw) * 100 AS achievements_pct,
    PERCENT_RANK() OVER (ORDER BY trending_raw) * 100 AS trending_pct,
    -- Physical uses formula-based rating
    PERCENT_RANK() OVER (ORDER BY physical_raw) * 100 AS physical_pct
  FROM raw_scores
),

-- Step 5: Convert to EA-style ratings (40-99 scale)
ea_ratings AS (
  SELECT
    *,

    -- Performance Rating (percentile-based curve)
    CAST(CASE
      WHEN performance_pct >= 99.9 THEN 99
      WHEN performance_pct >= 99 THEN 95 + (performance_pct - 99) * 4
      WHEN performance_pct >= 95 THEN 90 + (performance_pct - 95) * 1
      WHEN performance_pct >= 80 THEN 80 + (performance_pct - 80) * 0.67
      WHEN performance_pct >= 50 THEN 70 + (performance_pct - 50) * 0.33
      WHEN performance_pct >= 20 THEN 60 + (performance_pct - 20) * 0.33
      ELSE 40 + performance_pct * 1
    END AS INT64) AS performance_rating,

    -- Level Rating: DIRECT TIER MAPPING (no percentile)
    -- Uses level_category_points from DL_league_category_points directly
    CAST(level_tier_rating AS INT64) AS level_rating,

    -- Visibility Rating (percentile-based curve)
    CAST(CASE
      WHEN visibility_pct >= 99.9 THEN 99
      WHEN visibility_pct >= 99 THEN 95 + (visibility_pct - 99) * 4
      WHEN visibility_pct >= 95 THEN 90 + (visibility_pct - 95) * 1
      WHEN visibility_pct >= 80 THEN 80 + (visibility_pct - 80) * 0.67
      WHEN visibility_pct >= 50 THEN 70 + (visibility_pct - 50) * 0.33
      WHEN visibility_pct >= 20 THEN 60 + (visibility_pct - 20) * 0.33
      ELSE 40 + visibility_pct * 1
    END AS INT64) AS visibility_rating,

    -- Achievements Rating (percentile-based curve)
    CAST(CASE
      WHEN achievements_pct >= 99.9 THEN 99
      WHEN achievements_pct >= 99 THEN 95 + (achievements_pct - 99) * 4
      WHEN achievements_pct >= 95 THEN 90 + (achievements_pct - 95) * 1
      WHEN achievements_pct >= 80 THEN 80 + (achievements_pct - 80) * 0.67
      WHEN achievements_pct >= 50 THEN 70 + (achievements_pct - 50) * 0.33
      WHEN achievements_pct >= 20 THEN 60 + (achievements_pct - 20) * 0.33
      ELSE 40 + achievements_pct * 1
    END AS INT64) AS achievements_rating,

    -- Trending Rating (percentile-based curve)
    CAST(CASE
      WHEN trending_pct >= 99.9 THEN 99
      WHEN trending_pct >= 99 THEN 95 + (trending_pct - 99) * 4
      WHEN trending_pct >= 95 THEN 90 + (trending_pct - 95) * 1
      WHEN trending_pct >= 80 THEN 80 + (trending_pct - 80) * 0.67
      WHEN trending_pct >= 50 THEN 70 + (trending_pct - 50) * 0.33
      WHEN trending_pct >= 20 THEN 60 + (trending_pct - 20) * 0.33
      ELSE 40 + trending_pct * 1
    END AS INT64) AS trending_rating,

    -- Physical Rating: FORMULA-BASED
    -- ((F02 + F26 + F27) / 600) * 100, then scaled to 40-99
    -- Max possible: 200 + 150 + 250 = 600 points
    CAST(
      GREATEST(40, LEAST(99,
        40 + (physical_raw / 600.0) * 59  -- Scale 0-600 to 40-99
      ))
    AS INT64) AS physical_rating

  FROM percentile_ranks
)

-- Final output: Calculate overall rating with CORRECTED category weights
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

  -- Overall Rating with CORRECTED WEIGHTS from spreadsheet:
  -- PER*0.15 + LEV*0.35 + VIS*0.20 + PHY*0.15 + ACH*0.10 + TRE*0.05
  LEAST(99, CAST(
    performance_rating * 0.15 +
    level_rating * 0.35 +
    visibility_rating * 0.20 +
    physical_rating * 0.15 +
    achievements_rating * 0.10 +
    trending_rating * 0.05
  AS INT64)) AS overall_rating,

  -- Category Ratings (for card display)
  performance_rating,
  level_rating,
  visibility_rating,
  achievements_rating,
  trending_rating,
  physical_rating,

  -- Category abbreviations for compact display
  performance_rating AS perf,
  level_rating AS lvl,
  visibility_rating AS vis,
  achievements_rating AS ach,
  trending_rating AS trd,
  physical_rating AS phy,

  -- Raw scores (for debugging/analysis)
  ROUND(performance_raw, 2) AS performance_raw,
  ROUND(level_raw, 2) AS level_raw,
  ROUND(visibility_raw, 2) AS visibility_raw,
  ROUND(achievements_raw, 2) AS achievements_raw,
  ROUND(trending_raw, 2) AS trending_raw,
  ROUND(physical_raw, 2) AS physical_raw,

  -- Key underlying factors (for transparency to admins)
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
  CURRENT_TIMESTAMP() AS ratings_generated_at

FROM ea_ratings
ORDER BY overall_rating DESC, total_points DESC;

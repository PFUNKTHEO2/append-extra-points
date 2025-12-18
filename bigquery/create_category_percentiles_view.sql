-- ============================================================================
-- CREATE CATEGORY PERCENTILES VIEW - v2.0
-- ============================================================================
-- Updated 2025-12-18: Level now uses DIRECT TIER MAPPING from DL_league_category_points
-- instead of percentile-based calculation. This ensures NHL=99, CHL/NL=95, etc.
--
-- Adds percentile rankings (0-100) for each category within peer groups
-- Peer group = same birth_year + position
--
-- Category → Factor Mapping:
-- | Category     | Factors                           | Formula                                        |
-- |--------------|-----------------------------------|------------------------------------------------|
-- | Performance  | F03-F12                           | PERCENT_RANK of f03+...+f12                    |
-- | Level        | Direct from league tier           | DL_league_category_points.level_category_points|
-- | Visibility   | F01, F23, F24, F25                | PERCENT_RANK of f01+f23+f24+f25               |
-- | Achievements | F15-F17, F21, F22                 | PERCENT_RANK of f15+f16+f17+f21+f22           |
-- | Physical     | F02, F26, F27                     | PERCENT_RANK of f02+f26+f27                   |
-- | Trending     | F18, F19                          | PERCENT_RANK of f18+f19                       |
-- ============================================================================

-- Drop existing view if it exists
DROP VIEW IF EXISTS `prodigy-ranking.algorithm_core.player_category_percentiles`;

-- Create the percentiles view
CREATE VIEW `prodigy-ranking.algorithm_core.player_category_percentiles` AS

-- Get league tier ratings from lookup table
WITH league_tiers AS (
  SELECT
    league_name,
    level_category_points as league_tier_rating
  FROM `prodigy-ranking.algorithm.DL_league_category_points`
),

category_sums AS (
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

    -- Performance: F03-F12 (skating stats - current + last season)
    COALESCE(p.f03_current_goals_f, 0) +
    COALESCE(p.f04_current_goals_d, 0) +
    COALESCE(p.f05_current_assists, 0) +
    COALESCE(p.f06_current_gaa, 0) +
    COALESCE(p.f07_current_svp, 0) +
    COALESCE(p.f08_last_goals_f, 0) +
    COALESCE(p.f09_last_goals_d, 0) +
    COALESCE(p.f10_last_assists, 0) +
    COALESCE(p.f11_last_gaa, 0) +
    COALESCE(p.f12_last_svp, 0) AS performance_sum,

    -- Level: Get direct tier rating from lookup table (NOT percentile)
    COALESCE(lt.league_tier_rating, 40) AS level_tier_rating,

    -- Keep level_sum for reference (F13 + F14)
    COALESCE(p.f13_league_points, 0) +
    COALESCE(p.f14_team_points, 0) AS level_sum,

    -- Visibility: F01 + F23 + F24 (views + prodigy likes + card sales)
    COALESCE(p.f01_views, 0) +
    COALESCE(p.f23_prodigylikes_points, 0) +
    COALESCE(p.f24_card_sales_points, 0) AS visibility_sum,

    -- Achievements: F15 + F16 + F17 + F21 + F22 (international, commitment, draft, tournament, manual)
    COALESCE(p.f15_international_points, 0) +
    COALESCE(p.f16_commitment_points, 0) +
    COALESCE(p.f17_draft_points, 0) +
    COALESCE(p.f21_tournament_points, 0) +
    COALESCE(p.f22_manual_points, 0) AS achievements_sum,

    -- Physical: F02 + F26 + F27 (height + weight + BMI)
    COALESCE(p.f02_height, 0) +
    COALESCE(p.f26_weight_points, 0) +
    COALESCE(p.f27_bmi_points, 0) AS physical_sum,

    -- Trending: F18 + F19 (weekly deltas)
    COALESCE(p.f18_weekly_points_delta, 0) +
    COALESCE(p.f19_weekly_assists_delta, 0) AS trending_sum

  FROM `prodigy-ranking.algorithm_core.player_cumulative_points` p
  LEFT JOIN league_tiers lt ON
    -- Normalize league name: lowercase, replace spaces with hyphens, remove parentheses
    REGEXP_REPLACE(REGEXP_REPLACE(LOWER(p.current_league), r'[() ]', '-'), r'-+', '-') = lt.league_name
    OR LOWER(p.current_league) = lt.league_name
    OR REGEXP_REPLACE(LOWER(p.current_league), r' ', '-') = lt.league_name
  WHERE p.birth_year IS NOT NULL AND p.position IS NOT NULL
),

percentile_calculations AS (
  SELECT
    *,

    -- Performance percentile (within birth_year + position)
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY performance_sum
    ) * 100) AS performance_percentile,

    -- Level: USE DIRECT TIER RATING (NOT percentile)
    -- This ensures NHL=99, CHL/NL=95, etc. regardless of peer group
    level_tier_rating AS level_percentile,

    -- Visibility percentile
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY visibility_sum
    ) * 100) AS visibility_percentile,

    -- Achievements percentile
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY achievements_sum
    ) * 100) AS achievements_percentile,

    -- Physical percentile
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY physical_sum
    ) * 100) AS physical_percentile,

    -- Trending percentile
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY trending_sum
    ) * 100) AS trending_percentile,

    -- Overall percentile (based on total_points)
    ROUND(PERCENT_RANK() OVER (
      PARTITION BY birth_year, position
      ORDER BY total_points
    ) * 100) AS overall_percentile

  FROM category_sums
)

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

  -- Category sums (raw values)
  ROUND(performance_sum, 2) AS performance_sum,
  ROUND(level_sum, 2) AS level_sum,
  ROUND(visibility_sum, 2) AS visibility_sum,
  ROUND(achievements_sum, 2) AS achievements_sum,
  ROUND(physical_sum, 2) AS physical_sum,
  ROUND(trending_sum, 2) AS trending_sum,

  -- Percentiles (0-100, where 85 means "top 15%")
  CAST(performance_percentile AS INT64) AS performance_percentile,
  CAST(level_percentile AS INT64) AS level_percentile,
  CAST(visibility_percentile AS INT64) AS visibility_percentile,
  CAST(achievements_percentile AS INT64) AS achievements_percentile,
  CAST(physical_percentile AS INT64) AS physical_percentile,
  CAST(trending_percentile AS INT64) AS trending_percentile,
  CAST(overall_percentile AS INT64) AS overall_percentile,

  CURRENT_TIMESTAMP() AS calculated_at

FROM percentile_calculations;

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- Run this after creating the view to verify percentiles are working:
/*
SELECT
  player_name,
  position,
  birth_year,
  total_points,
  performance_percentile,
  level_percentile,
  visibility_percentile,
  achievements_percentile,
  physical_percentile,
  trending_percentile,
  overall_percentile
FROM `prodigy-ranking.algorithm_core.player_category_percentiles`
WHERE birth_year = 2008 AND position = 'F'
ORDER BY total_points DESC
LIMIT 20;
*/

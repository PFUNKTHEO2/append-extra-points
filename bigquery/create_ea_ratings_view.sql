-- =====================================================================
-- EA SPORTS-STYLE PLAYER RATINGS VIEW
-- =====================================================================
-- Creates a view with 6 category ratings (0-99 scale) + overall rating
--
-- Categories:
--   1. Performance (35%) - Goals, assists, goalie stats
--   2. Level (25%)       - League + team quality
--   3. Visibility (10%)  - EP views + ProdigyLikes
--   4. Achievements (15%)- International, draft, college, tournaments
--   5. Trending (5%)     - Weekly momentum
--   6. Physical (10%)    - Height
--
-- Rating Scale (EA Sports style):
--   99: Top 0.1% (elite superstars)
--   90-98: Top 1-5% (stars)
--   80-89: Top 10-20% (very good)
--   70-79: Top 30-50% (above average)
--   60-69: Average players
--   50-59: Below average
--   40-49: Lowest rated
-- =====================================================================

CREATE OR REPLACE VIEW `prodigy-ranking.algorithm_core.player_card_ratings` AS

WITH
-- Step 1: Calculate raw category scores for each player
raw_scores AS (
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

    -- PERFORMANCE: Position-specific stats
    CASE
      WHEN position = 'F' THEN
        COALESCE(f03_current_goals_f, 0) + COALESCE(f05_current_assists, 0) +
        COALESCE(f08_last_goals_f, 0) + COALESCE(f10_last_assists, 0)
      WHEN position = 'D' THEN
        COALESCE(f04_current_goals_d, 0) + COALESCE(f05_current_assists, 0) +
        COALESCE(f09_last_goals_d, 0) + COALESCE(f10_last_assists, 0)
      ELSE -- Goalie
        COALESCE(f06_current_gaa, 0) + COALESCE(f07_current_svp, 0) +
        COALESCE(f11_last_gaa, 0) + COALESCE(f12_last_svp, 0)
    END AS performance_raw,

    -- LEVEL: League + Team quality
    COALESCE(f13_league_points, 0) + COALESCE(f14_team_points, 0) AS level_raw,

    -- VISIBILITY: Views + ProdigyLikes
    COALESCE(f01_views, 0) + COALESCE(f23_prodigylikes_points, 0) AS visibility_raw,

    -- ACHIEVEMENTS: International + College + Draft + Tournaments
    COALESCE(f15_international_points, 0) + COALESCE(f16_commitment_points, 0) +
    COALESCE(f17_draft_points, 0) + COALESCE(f21_tournament_points, 0) AS achievements_raw,

    -- TRENDING: Weekly deltas
    COALESCE(f18_weekly_points_delta, 0) + COALESCE(f19_weekly_assists_delta, 0) AS trending_raw,

    -- PHYSICAL: Height
    COALESCE(f02_height, 0) AS physical_raw,

    -- Keep individual factors for reference
    COALESCE(f01_views, 0) AS f01_views,
    COALESCE(f02_height, 0) AS f02_height,
    COALESCE(f13_league_points, 0) AS f13_league_points,
    COALESCE(f14_team_points, 0) AS f14_team_points,
    COALESCE(f15_international_points, 0) AS f15_international_points,
    COALESCE(f16_commitment_points, 0) AS f16_commitment_points,
    COALESCE(f17_draft_points, 0) AS f17_draft_points,

    calculated_at,
    algorithm_version

  FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
  WHERE total_points > 0
),

-- Step 2: Calculate percentile ranks for each category
percentile_ranks AS (
  SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY performance_raw) * 100 AS performance_pct,
    PERCENT_RANK() OVER (ORDER BY level_raw) * 100 AS level_pct,
    PERCENT_RANK() OVER (ORDER BY visibility_raw) * 100 AS visibility_pct,
    PERCENT_RANK() OVER (ORDER BY achievements_raw) * 100 AS achievements_pct,
    PERCENT_RANK() OVER (ORDER BY trending_raw) * 100 AS trending_pct,
    PERCENT_RANK() OVER (ORDER BY physical_raw) * 100 AS physical_pct
  FROM raw_scores
),

-- Step 3: Convert percentiles to EA-style ratings (40-99 scale)
-- Using a curve that makes 99 rare and clusters average players around 65-70
ea_ratings AS (
  SELECT
    *,

    -- Performance Rating
    CAST(CASE
      WHEN performance_pct >= 99.9 THEN 99
      WHEN performance_pct >= 99 THEN 95 + (performance_pct - 99) * 4
      WHEN performance_pct >= 95 THEN 90 + (performance_pct - 95) * 1
      WHEN performance_pct >= 80 THEN 80 + (performance_pct - 80) * 0.67
      WHEN performance_pct >= 50 THEN 70 + (performance_pct - 50) * 0.33
      WHEN performance_pct >= 20 THEN 60 + (performance_pct - 20) * 0.33
      ELSE 40 + performance_pct * 1
    END AS INT64) AS performance_rating,

    -- Level Rating
    CAST(CASE
      WHEN level_pct >= 99.9 THEN 99
      WHEN level_pct >= 99 THEN 95 + (level_pct - 99) * 4
      WHEN level_pct >= 95 THEN 90 + (level_pct - 95) * 1
      WHEN level_pct >= 80 THEN 80 + (level_pct - 80) * 0.67
      WHEN level_pct >= 50 THEN 70 + (level_pct - 50) * 0.33
      WHEN level_pct >= 20 THEN 60 + (level_pct - 20) * 0.33
      ELSE 40 + level_pct * 1
    END AS INT64) AS level_rating,

    -- Visibility Rating
    CAST(CASE
      WHEN visibility_pct >= 99.9 THEN 99
      WHEN visibility_pct >= 99 THEN 95 + (visibility_pct - 99) * 4
      WHEN visibility_pct >= 95 THEN 90 + (visibility_pct - 95) * 1
      WHEN visibility_pct >= 80 THEN 80 + (visibility_pct - 80) * 0.67
      WHEN visibility_pct >= 50 THEN 70 + (visibility_pct - 50) * 0.33
      WHEN visibility_pct >= 20 THEN 60 + (visibility_pct - 20) * 0.33
      ELSE 40 + visibility_pct * 1
    END AS INT64) AS visibility_rating,

    -- Achievements Rating
    CAST(CASE
      WHEN achievements_pct >= 99.9 THEN 99
      WHEN achievements_pct >= 99 THEN 95 + (achievements_pct - 99) * 4
      WHEN achievements_pct >= 95 THEN 90 + (achievements_pct - 95) * 1
      WHEN achievements_pct >= 80 THEN 80 + (achievements_pct - 80) * 0.67
      WHEN achievements_pct >= 50 THEN 70 + (achievements_pct - 50) * 0.33
      WHEN achievements_pct >= 20 THEN 60 + (achievements_pct - 20) * 0.33
      ELSE 40 + achievements_pct * 1
    END AS INT64) AS achievements_rating,

    -- Trending Rating
    CAST(CASE
      WHEN trending_pct >= 99.9 THEN 99
      WHEN trending_pct >= 99 THEN 95 + (trending_pct - 99) * 4
      WHEN trending_pct >= 95 THEN 90 + (trending_pct - 95) * 1
      WHEN trending_pct >= 80 THEN 80 + (trending_pct - 80) * 0.67
      WHEN trending_pct >= 50 THEN 70 + (trending_pct - 50) * 0.33
      WHEN trending_pct >= 20 THEN 60 + (trending_pct - 20) * 0.33
      ELSE 40 + trending_pct * 1
    END AS INT64) AS trending_rating,

    -- Physical Rating
    CAST(CASE
      WHEN physical_pct >= 99.9 THEN 99
      WHEN physical_pct >= 99 THEN 95 + (physical_pct - 99) * 4
      WHEN physical_pct >= 95 THEN 90 + (physical_pct - 95) * 1
      WHEN physical_pct >= 80 THEN 80 + (physical_pct - 80) * 0.67
      WHEN physical_pct >= 50 THEN 70 + (physical_pct - 50) * 0.33
      WHEN physical_pct >= 20 THEN 60 + (physical_pct - 20) * 0.33
      ELSE 40 + physical_pct * 1
    END AS INT64) AS physical_rating

  FROM percentile_ranks
)

-- Final output: Calculate overall rating with category weights
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

  -- Overall Rating (weighted average, capped at 99)
  LEAST(99, CAST(
    performance_rating * 0.35 +
    level_rating * 0.25 +
    achievements_rating * 0.15 +
    visibility_rating * 0.10 +
    physical_rating * 0.10 +
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

  -- Metadata
  calculated_at,
  algorithm_version,
  CURRENT_TIMESTAMP() AS ratings_generated_at

FROM ea_ratings
ORDER BY overall_rating DESC, total_points DESC;

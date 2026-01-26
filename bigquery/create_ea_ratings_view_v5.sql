-- =====================================================================
-- CANONICAL PLAYER RATINGS VIEW - VERSION 5.0
-- =====================================================================
--
-- ██████╗ ███████╗███████╗██╗███╗   ██╗██╗████████╗██╗██╗   ██╗███████╗
-- ██╔══██╗██╔════╝██╔════╝██║████╗  ██║██║╚══██╔══╝██║██║   ██║██╔════╝
-- ██║  ██║█████╗  █████╗  ██║██╔██╗ ██║██║   ██║   ██║██║   ██║█████╗
-- ██║  ██║██╔══╝  ██╔══╝  ██║██║╚██╗██║██║   ██║   ██║╚██╗ ██╔╝██╔══╝
-- ██████╔╝███████╗██║     ██║██║ ╚████║██║   ██║   ██║ ╚████╔╝ ███████╗
-- ╚═════╝ ╚══════╝╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝   ╚═╝   ╚═╝  ╚═══╝  ╚══════╝
--
-- THIS IS THE SINGLE SOURCE OF TRUTH FOR ALL RATING CALCULATIONS (F31-F37)
--
-- Created: 2026-01-26
-- Author: Algorithm Team
--
-- =====================================================================
-- IMPORTANT: RATINGS ARE PRE-COMPUTED IN player_cumulative_points TABLE
-- =====================================================================
--
-- The ratings (F31-F37) are now calculated and stored directly in the
-- player_cumulative_points table by rebuild_cumulative_with_ratings.sql
--
-- This view simply reads the stored values and adds the F37 overall rating.
--
-- To update ratings:
--   1. Run rebuild_cumulative_with_ratings.sql to rebuild the table
--   2. This view will automatically reflect the new values
--
-- =====================================================================
-- DEPRECATION NOTICE
-- =====================================================================
--
-- The following files/views are DEPRECATED and should NOT be used:
--   - create_ea_ratings_view.sql (v1)
--   - create_ea_ratings_view_v2.sql (v2)
--   - create_ea_ratings_view_v3.sql (v3)
--   - create_ea_ratings_view_v4.sql (v4.x)
--   - Any hardcoded rating calculations in API code
--   - Any frontend rating calculations
--
-- ALL rating logic is now in rebuild_cumulative_with_ratings.sql
--
-- =====================================================================
-- CANONICAL FORMULAS (stored in player_cumulative_points)
-- =====================================================================
--
-- F31 - PERFORMANCE RATING (0-99)
--   Forwards: IF 0.7*(F03+F05) + 0.3*(F08+F10) >= 1.0 THEN 99 ELSE 98*combined
--   Defenders: IF combined >= 0.8 THEN 99 ELSE 98*combined/0.8
--   Goalies: Average of GAA rating + SVP rating
--
-- F32 - LEVEL RATING (0-99)
--   Direct lookup from DL_league_category_points table
--
-- F33 - VISIBILITY RATING (0-99)
--   IF views < 100 THEN 0, ELSE IF views >= 15000 THEN 99, ELSE linear
--
-- F34 - PHYSICAL RATING (0-99)
--   (F02 + F26 + F27) / 600 * 99
--
-- F35 - ACHIEVEMENTS RATING (0-99)
--   IF (F15+F16+F17+F21+F22) >= 1500 THEN 99 ELSE 99*sum/1500
--
-- F36 - TRENDING RATING (0-99)
--   Skaters: IF (F18+F19+F25) >= 250 THEN 99 ELSE 99*sum/250
--   Goalies: IF F25 >= 50 THEN 99 ELSE 99*F25/50
--
-- F37 - OVERALL RATING (0-99)
--   3% Performance + 70% Level + 19% Visibility + 5% Physical + 3% Achievements
--
-- =====================================================================

CREATE OR REPLACE VIEW `prodigy-ranking.algorithm_core.player_card_ratings` AS

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

  -- =========================================================================
  -- F37 - OVERALL RATING (weighted composite)
  -- 3% Performance + 70% Level + 19% Visibility + 5% Physical + 3% Achievements
  -- =========================================================================
  LEAST(99, GREATEST(1, CAST(
    f31_performance_rating * 0.03 +
    f32_level_rating * 0.70 +
    f33_visibility_rating * 0.19 +
    f34_physical_rating * 0.05 +
    f35_achievements_rating * 0.03
  AS INT64))) AS overall_rating,

  -- Pre-computed ratings from player_cumulative_points
  f31_performance_rating AS performance_rating,
  f32_level_rating AS level_rating,
  f33_visibility_rating AS visibility_rating,
  f34_physical_rating AS physical_rating,
  f35_achievements_rating AS achievements_rating,
  f36_trending_rating AS trending_rating,

  -- Compact aliases for card display
  f31_performance_rating AS perf,
  f32_level_rating AS lvl,
  f33_visibility_rating AS vis,
  f34_physical_rating AS phy,
  f35_achievements_rating AS ach,
  f36_trending_rating AS trd,

  -- Raw per-game stats for debugging
  f03_goals_per_game AS current_goals_pg_f,
  f04_goals_per_game AS current_goals_pg_d,
  f05_assists_per_game AS current_assists_pg,
  f08_goals_per_game AS past_goals_pg_f,
  f09_goals_per_game AS past_goals_pg_d,
  f10_assists_per_game AS past_assists_pg,
  f06_gaa_raw AS current_gaa,
  f07_svp_raw AS current_svp,
  f11_gaa_raw AS past_gaa,
  f12_svp_raw AS past_svp,

  -- Raw data for transparency
  ep_views_raw,
  LEAST(f02_height, 200) + f26_weight_points + f27_bmi_points AS physical_sum,
  f15_international_points + f16_commitment_points + f17_draft_points + f21_tournament_points + f22_manual_points AS achievements_sum,
  CASE
    WHEN position IN ('F', 'D') THEN f18_weekly_points_delta + f19_weekly_assists_delta + f25_weekly_views
    ELSE f25_weekly_views
  END AS trending_sum,

  -- Individual factors for reference
  f01_views,
  f02_height,
  f13_league_points,
  f14_team_points,
  f15_international_points,
  f16_commitment_points,
  f17_draft_points,
  f18_weekly_points_delta,
  f19_weekly_assists_delta,
  f21_tournament_points,
  f22_manual_points,
  f25_weekly_views,
  f26_weight_points,
  f27_bmi_points,

  -- Metadata
  calculated_at,
  algorithm_version,
  'v5.0-canonical' AS ratings_version,
  CURRENT_TIMESTAMP() AS ratings_generated_at

FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE total_points > 0
ORDER BY total_points DESC;


-- =============================================================================
-- FORMULA REFERENCE TABLE (for documentation)
-- =============================================================================
--
-- +--------+---------------------+--------------------------------------------------+-------+--------+
-- | Factor | Name                | Formula                                          | Max   | Weight |
-- +--------+---------------------+--------------------------------------------------+-------+--------+
-- | F31    | Performance Rating  | See position-specific formulas in rebuild script | 99    | 3%     |
-- | F32    | Level Rating        | DL_league_category_points lookup                 | 99    | 70%    |
-- | F33    | Visibility Rating   | (views - 100) / 14900 * 99 [100-15000 range]     | 99    | 19%    |
-- | F34    | Physical Rating     | (F02 + F26 + F27) / 600 * 99                     | 99    | 5%     |
-- | F35    | Achievements Rating | (F15+F16+F17+F21+F22) / 1500 * 99                | 99    | 3%     |
-- | F36    | Trending Rating     | Skaters: (F18+F19+F25)/250*99, Goalies: F25/50*99| 99    | 0%     |
-- | F37    | Overall Rating      | Weighted sum of F31-F35                          | 99    | N/A    |
-- +--------+---------------------+--------------------------------------------------+-------+--------+
--
-- =============================================================================

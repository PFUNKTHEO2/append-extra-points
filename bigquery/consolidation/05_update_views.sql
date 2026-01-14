-- ============================================================================
-- UPDATE VIEWS TO USE player_rankings instead of player_cumulative_points
-- ============================================================================

-- Update player_card_ratings view
CREATE OR REPLACE VIEW `prodigy-ranking.algorithm_core.player_card_ratings` AS
WITH
league_tiers AS (
  SELECT
    league_name,
    level_category_points as league_tier_rating
  FROM `prodigy-ranking.algorithm.DL_league_category_points`
),

physical_data AS (
  SELECT
    w.player_id,
    COALESCE(w.factor_26_weight_points, 0) as f26_weight_points,
    COALESCE(b.factor_27_bmi_points, 0) as f27_bmi_points
  FROM `prodigy-ranking.algorithm_core.PT_F26_weight` w
  FULL OUTER JOIN `prodigy-ranking.algorithm_core.PT_F27_bmi` b
    ON w.player_id = b.player_id
),

f03_raw AS (
  SELECT player_id, current_goals_per_game AS current_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
),
f04_raw AS (
  SELECT player_id, current_goals_per_game AS current_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
),
f05_raw AS (
  SELECT player_id, current_assists_per_game AS current_assists_pg
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
),
f06_raw AS (
  SELECT player_id, goals_against_average AS current_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
),
f07_raw AS (
  SELECT player_id, save_percentage AS current_svp
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
),
f08_raw AS (
  SELECT player_id, last_goals_per_game AS past_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
),
f09_raw AS (
  SELECT player_id, last_goals_per_game AS past_goals_pg
  FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD`
),
f10_raw AS (
  SELECT player_id, last_assists_per_game AS past_assists_pg
  FROM `prodigy-ranking.algorithm_core.PT_F10_LAPG`
),
f11_raw AS (
  SELECT player_id, last_season_gaa AS past_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA`
),
f12_raw AS (
  SELECT player_id, last_season_svp AS past_svp
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSV`
),
f01_raw AS (
  SELECT player_id, ep_views
  FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
),

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

    CASE
      WHEN p.position = 'F' THEN
        0.7 * (COALESCE(f03.current_goals_pg, 0) + COALESCE(f05.current_assists_pg, 0)) +
        0.3 * (COALESCE(f08.past_goals_pg, 0) + COALESCE(f10.past_assists_pg, 0))
      WHEN p.position = 'D' THEN
        0.7 * (COALESCE(f04.current_goals_pg, 0) + COALESCE(f05.current_assists_pg, 0)) +
        0.3 * (COALESCE(f09.past_goals_pg, 0) + COALESCE(f10.past_assists_pg, 0))
      ELSE 0
    END AS skater_combined,

    CASE WHEN p.position = 'G' THEN
      0.7 * COALESCE(f06.current_gaa, 0) + 0.3 * COALESCE(f11.past_gaa, 0)
    ELSE NULL END AS goalie_gaa_score,

    CASE WHEN p.position = 'G' THEN
      0.7 * (COALESCE(f07.current_svp, 0) / 100.0) + 0.3 * (COALESCE(f12.past_svp, 0) / 100.0)
    ELSE NULL END AS goalie_svp_score,

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

    COALESCE(p.f13_league_points, 0) + COALESCE(p.f14_team_points, 0) AS level_raw,
    COALESCE(f01.ep_views, 0) AS ep_views_raw,
    COALESCE(p.f01_views, 0) + COALESCE(p.f23_prodigylikes_points, 0) AS visibility_raw,

    LEAST(COALESCE(p.f15_international_points, 0), 1000) +
    COALESCE(p.f16_commitment_points, 0) +
    COALESCE(p.f17_draft_points, 0) +
    COALESCE(p.f21_tournament_points, 0) AS achievements_raw,

    COALESCE(p.f18_weekly_points_delta, 0) + COALESCE(p.f19_weekly_assists_delta, 0) AS trending_raw,

    LEAST(COALESCE(p.f02_height, 0), 200) +
    COALESCE(pd.f26_weight_points, 0) +
    COALESCE(pd.f27_bmi_points, 0) AS physical_raw,

    COALESCE(p.f01_views, 0) AS f01_views,
    LEAST(COALESCE(p.f02_height, 0), 200) AS f02_height,
    COALESCE(p.f13_league_points, 0) AS f13_league_points,
    COALESCE(p.f14_team_points, 0) AS f14_team_points,
    LEAST(COALESCE(p.f15_international_points, 0), 1000) AS f15_international_points,
    COALESCE(p.f16_commitment_points, 0) AS f16_commitment_points,
    COALESCE(p.f17_draft_points, 0) AS f17_draft_points,
    COALESCE(pd.f26_weight_points, 0) AS f26_weight_points,
    COALESCE(pd.f27_bmi_points, 0) AS f27_bmi_points,

    COALESCE(f03.current_goals_pg, 0) AS current_goals_pg_f,
    COALESCE(f04.current_goals_pg, 0) AS current_goals_pg_d,
    COALESCE(f05.current_assists_pg, 0) AS current_assists_pg,
    COALESCE(f08.past_goals_pg, 0) AS past_goals_pg_f,
    COALESCE(f09.past_goals_pg, 0) AS past_goals_pg_d,
    COALESCE(f10.past_assists_pg, 0) AS past_assists_pg,
    COALESCE(f06.current_gaa, 0) AS current_gaa,
    COALESCE(f07.current_svp, 0) / 100.0 AS current_svp,
    COALESCE(f11.past_gaa, 0) AS past_gaa,
    COALESCE(f12.past_svp, 0) / 100.0 AS past_svp,

    p.calculated_at,
    p.algorithm_version

  FROM `prodigy-ranking.algorithm_core.player_rankings` p
  LEFT JOIN league_tiers lt ON LOWER(p.current_league) = lt.league_name
  LEFT JOIN physical_data pd ON p.player_id = pd.player_id
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
  LEFT JOIN f01_raw f01 ON p.player_id = f01.player_id
  WHERE p.total_points > 0
),

percentile_ranks AS (
  SELECT
    *,
    PERCENT_RANK() OVER (ORDER BY visibility_raw) * 100 AS visibility_pct,
    PERCENT_RANK() OVER (ORDER BY achievements_raw) * 100 AS achievements_pct,
    PERCENT_RANK() OVER (ORDER BY trending_raw) * 100 AS trending_pct,
    PERCENT_RANK() OVER (ORDER BY physical_raw) * 100 AS physical_pct
  FROM raw_scores
),

ea_ratings AS (
  SELECT
    *,

    CASE
      WHEN position = 'F' THEN
        CASE
          WHEN skater_combined >= 1.0 THEN 99
          ELSE CAST(ROUND(98 * skater_combined) AS INT64)
        END
      WHEN position = 'D' THEN
        CASE
          WHEN skater_combined >= 0.8 THEN 99
          ELSE CAST(ROUND(98 * skater_combined / 0.8) AS INT64)
        END
      WHEN position = 'G' THEN
        LEAST(99, GREATEST(0, CAST(ROUND((
          CASE
            WHEN goalie_gaa_score <= 5 AND goalie_gaa_score > 0 THEN 0.1 + 98 * (1 - goalie_gaa_score / 5)
            WHEN goalie_gaa_score = 0 THEN 99
            ELSE 0
          END
          +
          CASE
            WHEN LEAST(goalie_svp_score, 1.0) >= 0.880 THEN 0.1 + 98 * ((LEAST(goalie_svp_score, 1.0) * 1000 - 500) / 499)
            ELSE 0
          END
        ) / 2) AS INT64)))
      ELSE 0
    END AS performance_rating,

    CAST(GREATEST(1, level_tier_rating) AS INT64) AS level_rating,
    CAST(LEAST(99, GREATEST(0, ROUND(ep_views_raw * 99.0 / 15000))) AS INT64) AS visibility_rating,

    CAST(GREATEST(1, CASE
      WHEN achievements_pct >= 99.9 THEN 99
      WHEN achievements_pct >= 99 THEN 95 + (achievements_pct - 99) * 4
      WHEN achievements_pct >= 95 THEN 90 + (achievements_pct - 95) * 1.25
      WHEN achievements_pct >= 80 THEN 75 + (achievements_pct - 80) * 1
      WHEN achievements_pct >= 50 THEN 50 + (achievements_pct - 50) * 0.83
      WHEN achievements_pct >= 20 THEN 25 + (achievements_pct - 20) * 0.83
      ELSE 1 + achievements_pct * 1.2
    END) AS INT64) AS achievements_rating,

    CAST(GREATEST(1, CASE
      WHEN trending_pct >= 99.9 THEN 99
      WHEN trending_pct >= 99 THEN 95 + (trending_pct - 99) * 4
      WHEN trending_pct >= 95 THEN 90 + (trending_pct - 95) * 1.25
      WHEN trending_pct >= 80 THEN 75 + (trending_pct - 80) * 1
      WHEN trending_pct >= 50 THEN 50 + (trending_pct - 50) * 0.83
      WHEN trending_pct >= 20 THEN 25 + (trending_pct - 20) * 0.83
      ELSE 1 + trending_pct * 1.2
    END) AS INT64) AS trending_rating,

    CAST(LEAST(99, GREATEST(0, ROUND(physical_raw / 600.0 * 99))) AS INT64) AS physical_rating

  FROM percentile_ranks
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

  LEAST(99, GREATEST(1, CAST(
    performance_rating * 0.03 +
    level_rating * 0.70 +
    visibility_rating * 0.19 +
    physical_rating * 0.05 +
    achievements_rating * 0.03 +
    trending_rating * 0.00
  AS INT64))) AS overall_rating,

  performance_rating,
  level_rating,
  visibility_rating,
  achievements_rating,
  trending_rating,
  physical_rating,

  performance_rating AS perf,
  level_rating AS lvl,
  visibility_rating AS vis,
  achievements_rating AS ach,
  trending_rating AS trd,
  physical_rating AS phy,

  ROUND(skater_combined, 4) AS skater_combined_ppg,
  ROUND(goalie_gaa_score, 4) AS goalie_gaa_weighted,
  ROUND(goalie_svp_score, 4) AS goalie_svp_weighted,

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

  ROUND(level_raw, 2) AS level_raw,
  ep_views_raw,
  ROUND(visibility_raw, 2) AS visibility_raw,
  ROUND(achievements_raw, 2) AS achievements_raw,
  ROUND(trending_raw, 2) AS trending_raw,
  ROUND(physical_raw, 2) AS physical_raw,

  f01_views,
  f02_height,
  f13_league_points,
  f14_team_points,
  f15_international_points,
  f16_commitment_points,
  f17_draft_points,
  f26_weight_points,
  f27_bmi_points,

  calculated_at,
  algorithm_version,
  'v4.2-linear-physical' AS ratings_version,
  CURRENT_TIMESTAMP() AS ratings_generated_at

FROM ea_ratings
ORDER BY overall_rating DESC, total_points DESC;

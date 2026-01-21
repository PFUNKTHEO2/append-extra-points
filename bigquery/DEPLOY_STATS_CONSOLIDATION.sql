-- ============================================================================
-- DEPLOYMENT SCRIPT: Player Stats Consolidation
-- ============================================================================
-- This script deploys the player stats consolidation migration.
-- Run each section in order in the BigQuery Console.
--
-- EXECUTION ORDER:
--   1. Create v_latest_player_stats view
--   2. Refresh Performance Factors (F03-F12)
--   3. Rebuild player_cumulative_points (uses view for base stats)
--   4. Verify results
--
-- CREATED: 2026-01-21
-- ============================================================================


-- ============================================================================
-- STEP 1: CREATE v_latest_player_stats VIEW
-- ============================================================================
-- This view derives "latest stats" from player_season_stats, replacing
-- the denormalized player_stats.latestStats_* columns

CREATE OR REPLACE VIEW `prodigy-ranking.algorithm_core.v_latest_player_stats` AS
WITH ranked_stats AS (
  SELECT
    pss.*,
    ROW_NUMBER() OVER (
      PARTITION BY pss.player_id
      ORDER BY
        -- League tier prioritization (higher tier = lower number = preferred)
        CASE
          -- Tier 1: Top professional leagues
          WHEN pss.league_name IN ('NHL','AHL','KHL','SHL','Liiga','NL','DEL','ICEHL','Extraliga') THEN 1
          -- Tier 2: Major junior and college
          WHEN pss.league_name IN ('OHL','WHL','QMJHL','USHL','USDP','NCAA') THEN 2
          -- Tier 3: Top junior leagues
          WHEN pss.league_name IN ('MHL','J20 Nationell','U20 SM-liiga','SuperElit') THEN 3
          -- Tier 4: All other leagues
          ELSE 4
        END,
        -- Tiebreaker: More games played = primary league
        pss.gp DESC
    ) AS rank
  FROM `prodigy-ranking.algorithm_core.player_season_stats` pss
  WHERE pss.season_start_year = 2025
    AND pss.gp IS NOT NULL
    AND pss.gp >= 1
)
SELECT
  -- Identity fields
  CAST(player_id AS STRING) as id,
  player_id,

  -- Season context
  season_slug,
  season_start_year,

  -- Team/League info
  team_name,
  team_id,
  league_name,
  league_slug,

  -- Skater stats
  gp,
  goals,
  assists,
  points,
  pim,
  plus_minus,

  -- Goalie stats
  gaa,
  svp,

  -- Metadata
  loadts
FROM ranked_stats
WHERE rank = 1;

-- Verify view creation
SELECT COUNT(*) as player_count FROM `prodigy-ranking.algorithm_core.v_latest_player_stats`;


-- ============================================================================
-- STEP 2: REFRESH PERFORMANCE FACTORS (F03-F12)
-- ============================================================================
-- Run REFRESH_ALL_PERFORMANCE_FACTORS.sql in a separate query
-- Or execute the individual refresh scripts in order:
--   - refresh_PT_F03_CGPGF.sql
--   - refresh_PT_F04_CGPGD.sql
--   - refresh_PT_F05_CAPG.sql
--   - (F06-F12 already use player_season_stats)


-- ============================================================================
-- STEP 3: REBUILD player_cumulative_points (UPDATED FOR VIEW)
-- ============================================================================
-- This version uses v_latest_player_stats for current season data
-- instead of player_stats.latestStats_* columns

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_cumulative_points` AS

WITH base_players AS (
  -- Get all unique players with their latest stats from the view
  -- Player metadata (name, position, yearOfBirth, nationality) from player_stats
  -- Latest season stats from v_latest_player_stats view
  SELECT DISTINCT
    pm.id AS player_id,
    pm.name AS player_name,
    pm.position,
    pm.yearOfBirth AS birth_year,
    pm.nationality_name,
    COALESCE(v.team_name, pm.latestStats_team_name) AS current_team,
    COALESCE(v.league_name, pm.latestStats_team_league_name) AS current_league,
    COALESCE(v.season_slug, pm.latestStats_season_slug) AS current_season,
    pm.latestStats_team_league_country_name AS team_country
  FROM `prodigy-ranking.algorithm_core.player_stats` pm
  LEFT JOIN `prodigy-ranking.algorithm_core.v_latest_player_stats` v
    ON pm.id = v.player_id
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
  SELECT player_id, factor_3_cgpgf_points AS f03_goals_forward
  FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
),

f04_data AS (
  SELECT player_id, factor_4_cgpgd_points AS f04_goals_defense
  FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
),

f05_data AS (
  SELECT player_id, factor_5_capg_points AS f05_assists
  FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
),

f06_data AS (
  SELECT player_id, factor_6_gaa_points AS f06_gaa
  FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
),

f07_data AS (
  SELECT player_id, factor_7_svp_points AS f07_svp
  FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
),

f08_data AS (
  SELECT player_id, factor_8_lgpgf_points AS f08_last_goals_forward
  FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
),

f09_data AS (
  SELECT player_id, factor_9_lgpgd_points AS f09_last_goals_defense
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
  SELECT player_id, factor_12_lsvp_points AS f12_last_svp
  FROM `prodigy-ranking.algorithm_core.PT_F12_LSVP`
),

-- Direct Load Factors (F13-F28)
f13_data AS (
  -- League Points with deduplication
  SELECT
    p.id AS player_id,
    MAX(l.total_points) AS f13_league
  FROM `prodigy-ranking.algorithm_core.player_stats` p
  LEFT JOIN `prodigy-ranking.algorithm.DL_all_leagues` l
    ON LOWER(COALESCE(
         (SELECT v2.league_name FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v2 WHERE v2.player_id = p.id LIMIT 1),
         p.latestStats_team_league_name
       )) = LOWER(l.league_name)
  GROUP BY p.id
),

f14_data AS (
  -- Team Points (currently disabled - returns 0)
  SELECT
    p.id AS player_id,
    0 AS f14_team  -- F14 disabled as of 2025-12-16
  FROM `prodigy-ranking.algorithm_core.player_stats` p
),

f15_data AS (
  SELECT player_id, LEAST(COALESCE(total_international_points, 0), 1000) AS f15_international
  FROM `prodigy-ranking.algorithm_core.PT_F15_IP`
),

f16_data AS (
  SELECT player_id, COALESCE(college_commitment_points, 0) AS f16_college
  FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
),

f17_data AS (
  SELECT player_id, COALESCE(total_draft_points, 0) AS f17_draft
  FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
),

f18_data AS (
  SELECT player_id, COALESCE(points, 0) AS f18_manual
  FROM `prodigy-ranking.algorithm_core.DL_F18_manual_points`
),

f19_data AS (
  SELECT player_id, COALESCE(points, 0) AS f19_adjustment
  FROM `prodigy-ranking.algorithm_core.DL_F19_adjustment_points`
),

f20_data AS (
  SELECT player_id, COALESCE(points, 0) AS f20_tournament
  FROM `prodigy-ranking.algorithm_core.DL_F20_tournament_points`
),

f21_data AS (
  SELECT player_id, COALESCE(factor_21_aha_points, 0) AS f21_aha
  FROM `prodigy-ranking.algorithm_core.DL_F21_aha_points`
),

f22_data AS (
  SELECT player_id, COALESCE(factor_22_ahl_points, 0) AS f22_ahl
  FROM `prodigy-ranking.algorithm_core.DL_F22_ahl_affiliate_points`
),

f23_data AS (
  SELECT player_id, COALESCE(points, 0) AS f23_bonus
  FROM `prodigy-ranking.algorithm_core.DL_F23_bonus_points`
),

f24_data AS (
  SELECT player_id, COALESCE(points, 0) AS f24_penalty
  FROM `prodigy-ranking.algorithm_core.DL_F24_penalty_points`
),

f25_data AS (
  SELECT player_id, COALESCE(factor_25_wv_points, 0) AS f25_weekly_views
  FROM `prodigy-ranking.algorithm_core.PT_F25_WV`
),

f26_data AS (
  SELECT player_id, COALESCE(factor_26_w_points, 0) AS f26_weight
  FROM `prodigy-ranking.algorithm_core.PT_F26_W`
),

f27_data AS (
  SELECT player_id, COALESCE(factor_27_bmi_points, 0) AS f27_bmi
  FROM `prodigy-ranking.algorithm_core.PT_F27_BMI`
),

f28_data AS (
  SELECT player_id, COALESCE(factor_28_ncs_points, 0) AS f28_nhl_scouting
  FROM `prodigy-ranking.algorithm_core.DL_F28_nhl_central_scouting`
)

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

  -- Performance Factor Points (F01-F12)
  COALESCE(f01.f01_views, 0) AS f01_views_points,
  COALESCE(f02.f02_height, 0) AS f02_height_points,
  COALESCE(f03.f03_goals_forward, 0) AS f03_goals_forward_points,
  COALESCE(f04.f04_goals_defense, 0) AS f04_goals_defense_points,
  COALESCE(f05.f05_assists, 0) AS f05_assists_points,
  COALESCE(f06.f06_gaa, 0) AS f06_gaa_points,
  COALESCE(f07.f07_svp, 0) AS f07_svp_points,
  COALESCE(f08.f08_last_goals_forward, 0) AS f08_last_goals_forward_points,
  COALESCE(f09.f09_last_goals_defense, 0) AS f09_last_goals_defense_points,
  COALESCE(f10.f10_last_assists, 0) AS f10_last_assists_points,
  COALESCE(f11.f11_last_gaa, 0) AS f11_last_gaa_points,
  COALESCE(f12.f12_last_svp, 0) AS f12_last_svp_points,

  -- Direct Load Factor Points (F13-F28)
  COALESCE(f13.f13_league, 0) AS f13_league_points,
  COALESCE(f14.f14_team, 0) AS f14_team_points,
  COALESCE(f15.f15_international, 0) AS f15_international_points,
  COALESCE(f16.f16_college, 0) AS f16_college_points,
  COALESCE(f17.f17_draft, 0) AS f17_draft_points,
  COALESCE(f18.f18_manual, 0) AS f18_manual_points,
  COALESCE(f19.f19_adjustment, 0) AS f19_adjustment_points,
  COALESCE(f20.f20_tournament, 0) AS f20_tournament_points,
  COALESCE(f21.f21_aha, 0) AS f21_aha_points,
  COALESCE(f22.f22_ahl, 0) AS f22_ahl_affiliate_points,
  COALESCE(f23.f23_bonus, 0) AS f23_bonus_points,
  COALESCE(f24.f24_penalty, 0) AS f24_penalty_points,
  COALESCE(f25.f25_weekly_views, 0) AS f25_weekly_views_points,
  COALESCE(f26.f26_weight, 0) AS f26_weight_points,
  COALESCE(f27.f27_bmi, 0) AS f27_bmi_points,
  COALESCE(f28.f28_nhl_scouting, 0) AS f28_nhl_scouting_points,

  -- Performance Total (F01-F12)
  ROUND(
    COALESCE(f01.f01_views, 0) +
    COALESCE(f02.f02_height, 0) +
    COALESCE(f03.f03_goals_forward, 0) +
    COALESCE(f04.f04_goals_defense, 0) +
    COALESCE(f05.f05_assists, 0) +
    COALESCE(f06.f06_gaa, 0) +
    COALESCE(f07.f07_svp, 0) +
    COALESCE(f08.f08_last_goals_forward, 0) +
    COALESCE(f09.f09_last_goals_defense, 0) +
    COALESCE(f10.f10_last_assists, 0) +
    COALESCE(f11.f11_last_gaa, 0) +
    COALESCE(f12.f12_last_svp, 0)
  , 2) AS performance_total,

  -- Direct Load Total (F13-F28)
  ROUND(
    COALESCE(f13.f13_league, 0) +
    COALESCE(f14.f14_team, 0) +
    COALESCE(f15.f15_international, 0) +
    COALESCE(f16.f16_college, 0) +
    COALESCE(f17.f17_draft, 0) +
    COALESCE(f18.f18_manual, 0) +
    COALESCE(f19.f19_adjustment, 0) +
    COALESCE(f20.f20_tournament, 0) +
    COALESCE(f21.f21_aha, 0) +
    COALESCE(f22.f22_ahl, 0) +
    COALESCE(f23.f23_bonus, 0) +
    COALESCE(f24.f24_penalty, 0) +
    COALESCE(f25.f25_weekly_views, 0) +
    COALESCE(f26.f26_weight, 0) +
    COALESCE(f27.f27_bmi, 0) +
    COALESCE(f28.f28_nhl_scouting, 0)
  , 2) AS direct_load_total,

  -- Grand Total
  ROUND(
    COALESCE(f01.f01_views, 0) + COALESCE(f02.f02_height, 0) +
    COALESCE(f03.f03_goals_forward, 0) + COALESCE(f04.f04_goals_defense, 0) +
    COALESCE(f05.f05_assists, 0) + COALESCE(f06.f06_gaa, 0) +
    COALESCE(f07.f07_svp, 0) + COALESCE(f08.f08_last_goals_forward, 0) +
    COALESCE(f09.f09_last_goals_defense, 0) + COALESCE(f10.f10_last_assists, 0) +
    COALESCE(f11.f11_last_gaa, 0) + COALESCE(f12.f12_last_svp, 0) +
    COALESCE(f13.f13_league, 0) + COALESCE(f14.f14_team, 0) +
    COALESCE(f15.f15_international, 0) + COALESCE(f16.f16_college, 0) +
    COALESCE(f17.f17_draft, 0) + COALESCE(f18.f18_manual, 0) +
    COALESCE(f19.f19_adjustment, 0) + COALESCE(f20.f20_tournament, 0) +
    COALESCE(f21.f21_aha, 0) + COALESCE(f22.f22_ahl, 0) +
    COALESCE(f23.f23_bonus, 0) + COALESCE(f24.f24_penalty, 0) +
    COALESCE(f25.f25_weekly_views, 0) + COALESCE(f26.f26_weight, 0) +
    COALESCE(f27.f27_bmi, 0) + COALESCE(f28.f28_nhl_scouting, 0)
  , 2) AS total_points,

  CURRENT_TIMESTAMP() AS loadts

FROM base_players bp
LEFT JOIN f01_data f01 ON CAST(bp.player_id AS STRING) = f01.player_id
LEFT JOIN f02_data f02 ON CAST(bp.player_id AS STRING) = f02.player_id
LEFT JOIN f03_data f03 ON CAST(bp.player_id AS STRING) = f03.player_id
LEFT JOIN f04_data f04 ON CAST(bp.player_id AS STRING) = f04.player_id
LEFT JOIN f05_data f05 ON CAST(bp.player_id AS STRING) = f05.player_id
LEFT JOIN f06_data f06 ON CAST(bp.player_id AS STRING) = f06.player_id
LEFT JOIN f07_data f07 ON CAST(bp.player_id AS STRING) = f07.player_id
LEFT JOIN f08_data f08 ON CAST(bp.player_id AS STRING) = f08.player_id
LEFT JOIN f09_data f09 ON CAST(bp.player_id AS STRING) = f09.player_id
LEFT JOIN f10_data f10 ON CAST(bp.player_id AS STRING) = f10.player_id
LEFT JOIN f11_data f11 ON CAST(bp.player_id AS STRING) = f11.player_id
LEFT JOIN f12_data f12 ON CAST(bp.player_id AS STRING) = f12.player_id
LEFT JOIN f13_data f13 ON bp.player_id = f13.player_id
LEFT JOIN f14_data f14 ON bp.player_id = f14.player_id
LEFT JOIN f15_data f15 ON CAST(bp.player_id AS STRING) = f15.player_id
LEFT JOIN f16_data f16 ON CAST(bp.player_id AS STRING) = f16.player_id
LEFT JOIN f17_data f17 ON CAST(bp.player_id AS STRING) = f17.player_id
LEFT JOIN f18_data f18 ON CAST(bp.player_id AS STRING) = f18.player_id
LEFT JOIN f19_data f19 ON CAST(bp.player_id AS STRING) = f19.player_id
LEFT JOIN f20_data f20 ON CAST(bp.player_id AS STRING) = f20.player_id
LEFT JOIN f21_data f21 ON CAST(bp.player_id AS STRING) = f21.player_id
LEFT JOIN f22_data f22 ON CAST(bp.player_id AS STRING) = f22.player_id
LEFT JOIN f23_data f23 ON CAST(bp.player_id AS STRING) = f23.player_id
LEFT JOIN f24_data f24 ON CAST(bp.player_id AS STRING) = f24.player_id
LEFT JOIN f25_data f25 ON CAST(bp.player_id AS STRING) = f25.player_id
LEFT JOIN f26_data f26 ON CAST(bp.player_id AS STRING) = f26.player_id
LEFT JOIN f27_data f27 ON CAST(bp.player_id AS STRING) = f27.player_id
LEFT JOIN f28_data f28 ON CAST(bp.player_id AS STRING) = f28.player_id;


-- ============================================================================
-- STEP 4: VERIFY RESULTS
-- ============================================================================

-- Check row count
SELECT
  'player_cumulative_points' as table_name,
  COUNT(*) as row_count,
  COUNT(DISTINCT player_id) as unique_players
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`;

-- Check view stats coverage
SELECT
  'v_latest_player_stats' as view_name,
  COUNT(*) as players_with_current_stats
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats`;

-- Sample top 10 by total points
SELECT
  player_id, player_name, position, birth_year,
  current_team, current_league,
  performance_total, direct_load_total, total_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
ORDER BY total_points DESC
LIMIT 10;

-- Compare performance factor coverage
SELECT
  position,
  COUNT(*) as total_players,
  SUM(CASE WHEN f03_goals_forward_points > 0 THEN 1 ELSE 0 END) as with_f03,
  SUM(CASE WHEN f04_goals_defense_points > 0 THEN 1 ELSE 0 END) as with_f04,
  SUM(CASE WHEN f05_assists_points > 0 THEN 1 ELSE 0 END) as with_f05,
  SUM(CASE WHEN f06_gaa_points > 0 THEN 1 ELSE 0 END) as with_f06,
  SUM(CASE WHEN f07_svp_points > 0 THEN 1 ELSE 0 END) as with_f07
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
GROUP BY position
ORDER BY position;


-- ============================================================================
-- STEP 5 (OPTIONAL): Trigger Supabase Sync
-- ============================================================================
-- After verifying results, trigger the Cloud Function to sync to Supabase:
-- curl -X POST https://us-central1-prodigy-ranking.cloudfunctions.net/sync-rankings
-- Or use the admin dashboard sync button

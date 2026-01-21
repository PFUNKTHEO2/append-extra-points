-- ============================================================================
-- View: v_latest_player_stats
-- Purpose: Consolidates "latest stats" from player_season_stats as single source of truth
-- Replaces: player_stats.latestStats_* columns
-- Created: 2026-01-21
-- ============================================================================
--
-- This view derives the most recent season stats for each player using:
-- 1. Current season filter (2025 season_start_year)
-- 2. League prioritization (NHL/AHL/KHL > CHL/USHL > Junior > Other)
-- 3. Games played tiebreaker (more GP = primary league)
--
-- Usage:
--   SELECT * FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` WHERE player_id = 123
--
-- Joins with player_metadata for full player info:
--   SELECT p.name, p.position, v.goals, v.assists
--   FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
--   JOIN `prodigy-ranking.algorithm_core.player_metadata` p ON v.player_id = p.id
-- ============================================================================

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

-- ============================================================================
-- Column Mapping Reference (old player_stats → new v_latest_player_stats)
-- ============================================================================
-- player_stats.latestStats_regularStats_G    → v_latest_player_stats.goals
-- player_stats.latestStats_regularStats_A    → v_latest_player_stats.assists
-- player_stats.latestStats_regularStats_TP   → v_latest_player_stats.points
-- player_stats.latestStats_regularStats_PIM  → v_latest_player_stats.pim
-- player_stats.latestStats_regularStats_PM   → v_latest_player_stats.plus_minus
-- player_stats.latestStats_regularStats_GP   → v_latest_player_stats.gp
-- player_stats.latestStats_regularStats_GAA  → v_latest_player_stats.gaa
-- player_stats.latestStats_regularStats_SVP  → v_latest_player_stats.svp
-- player_stats.latestStats_team_name         → v_latest_player_stats.team_name
-- player_stats.latestStats_league_name       → v_latest_player_stats.league_name
-- ============================================================================

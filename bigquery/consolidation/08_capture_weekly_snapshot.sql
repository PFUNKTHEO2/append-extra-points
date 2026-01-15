-- ============================================================================
-- CAPTURE WEEKLY STATS SNAPSHOT
-- ============================================================================
-- Run this BEFORE refreshing EP data each week to capture current stats.
-- This enables delta calculations for F18, F19, F25.
--
-- Usage: Run manually or schedule to run before weekly EP refresh
-- ============================================================================

-- Insert current stats for all players
INSERT INTO `prodigy-ranking.algorithm_core.weekly_stats_snapshot`
(player_id, snapshot_date, goals, assists, views, games_played)
SELECT
  id AS player_id,
  CURRENT_DATE() AS snapshot_date,
  SAFE_CAST(latestStats_regularStats_G AS INT64) AS goals,
  SAFE_CAST(latestStats_regularStats_A AS INT64) AS assists,
  views,
  SAFE_CAST(latestStats_regularStats_GP AS INT64) AS games_played
FROM `prodigy-ranking.algorithm_core.player_stats`
WHERE id IS NOT NULL;

-- Verify snapshot was captured
SELECT
  snapshot_date,
  COUNT(*) as players_captured,
  SUM(goals) as total_goals,
  SUM(assists) as total_assists,
  SUM(views) as total_views
FROM `prodigy-ranking.algorithm_core.weekly_stats_snapshot`
WHERE snapshot_date = CURRENT_DATE()
GROUP BY snapshot_date;

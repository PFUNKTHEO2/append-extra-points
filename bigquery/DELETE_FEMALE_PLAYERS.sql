-- ============================================================================
-- DELETE FEMALE PLAYERS FROM ALL TABLES
-- ============================================================================
-- Generated: January 14, 2026
-- STATUS: COMPLETED
--
-- Female players are identified by team names containing "(W)"
-- Total affected: ~1,726 players across multiple tables
--
-- EXECUTION RESULTS:
--   BigQuery player_cumulative_points: 1,726 deleted ✓
--   BigQuery player_stats: 1,726 deleted ✓
--   BigQuery player_season_stats_staging: 4,605 deleted ✓
--   Supabase player_rankings: 1,726 deleted ✓
--
-- PREVENTION: rebuild_cumulative_with_fixes.sql v2.9 now excludes females
-- ============================================================================

-- ============================================================================
-- STEP 1: CREATE BACKUPS (Safety first!)
-- ============================================================================

-- Backup female players from player_stats
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_female_backup_20260114` AS
SELECT *
FROM `prodigy-ranking.algorithm_core.player_stats`
WHERE COALESCE(latestStats_teamName, latestStats_team_name) LIKE '%(W)%';

-- Backup female players from player_cumulative_points
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_cumulative_points_female_backup_20260114` AS
SELECT *
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_team LIKE '%(W)%';

-- Backup female season stats
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_season_stats_female_backup_20260114` AS
SELECT *
FROM `prodigy-ranking.algorithm_staging.player_season_stats_staging`
WHERE team_name LIKE '%(W)%';


-- ============================================================================
-- STEP 2: GET PLAYER IDs TO DELETE (for Supabase sync)
-- ============================================================================

-- Export list of female player IDs (run this to get IDs for Supabase deletion)
-- SELECT player_id FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
-- WHERE current_team LIKE '%(W)%';


-- ============================================================================
-- STEP 3: DELETE FROM BIGQUERY TABLES
-- ============================================================================

-- Delete from player_cumulative_points (output table)
DELETE FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_team LIKE '%(W)%';

-- Delete from player_stats (source table)
DELETE FROM `prodigy-ranking.algorithm_core.player_stats`
WHERE COALESCE(latestStats_teamName, latestStats_team_name) LIKE '%(W)%';

-- Delete from player_season_stats (historical stats)
DELETE FROM `prodigy-ranking.algorithm_staging.player_season_stats_staging`
WHERE team_name LIKE '%(W)%';


-- ============================================================================
-- STEP 4: VERIFY DELETIONS
-- ============================================================================

-- Verify no female players remain
-- SELECT
--   'player_stats' as table_name,
--   COUNT(*) as remaining_female
-- FROM `prodigy-ranking.algorithm_core.player_stats`
-- WHERE COALESCE(latestStats_teamName, latestStats_team_name) LIKE '%(W)%'
-- UNION ALL
-- SELECT 'player_cumulative_points', COUNT(*)
-- FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
-- WHERE current_team LIKE '%(W)%';


-- ============================================================================
-- STEP 5: UPDATE REBUILD SQL TO EXCLUDE FEMALES
-- ============================================================================
-- Add this WHERE clause to base_players CTE in rebuild_cumulative_with_fixes.sql:
--
-- WHERE COALESCE(latestStats_teamName, latestStats_team_name) NOT LIKE '%(W)%'
--
-- This will prevent female players from being included in future rebuilds.
-- ============================================================================

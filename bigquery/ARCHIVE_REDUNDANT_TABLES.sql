-- ============================================================================
-- ARCHIVE REDUNDANT TABLES FROM algorithm_core
-- ============================================================================
-- Generated: January 14, 2026
--
-- This script moves backup and staging tables from algorithm_core to
-- algorithm_archive to clean up the dataset.
--
-- EXECUTION: Run in BigQuery Console section by section
-- ============================================================================

-- ============================================================================
-- STEP 1: Verify algorithm_archive dataset exists
-- ============================================================================
-- If not, create it first:
-- CREATE SCHEMA IF NOT EXISTS `prodigy-ranking.algorithm_archive`;


-- ============================================================================
-- STEP 2: BACKUP TABLES - Copy to archive then drop from core
-- ============================================================================

-- DL_F13 backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_20251120_210337` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251120_210337`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_20251207` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251207`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_20251216` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251216`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_20251216_085325` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251216_085325`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_pre_fix` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_pre_fix`;

-- DL_F14 backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F14_team_points_backup_20251121_092810` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F14_team_points_backup_20251121_092810`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F14_team_points_backup_20251121_092834` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F14_team_points_backup_20251121_092834`;

-- DL_F17 backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F17_draft_points_backup_20251120_205403` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points_backup_20251120_205403`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F17_draft_points_backup_20251120_210337` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points_backup_20251120_210337`;

-- DL_F22 backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F22_manual_points_backup_20251120_221752` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points_backup_20251120_221752`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F22_manual_points_backup_20251120_221924` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points_backup_20251120_221924`;

-- DL_all_leagues backup
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_all_leagues_backup_20260103` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_all_leagues_backup_20260103`;

-- PT factor backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F04_CGPGD_backup_20251208_v2` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD_backup_20251208_v2`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F06_CGAA_backup_20251119` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA_backup_20251119`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F06_CGAA_backup_20251208` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA_backup_20251208`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F07_CSV_backup_20251208` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F07_CSV_backup_20251208`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F09_LGPGD_backup_20251208_v2` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F09_LGPGD_backup_20251208_v2`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F11_LGAA_backup_20251208` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F11_LGAA_backup_20251208`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F12_LSV_backup_20251208` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F12_LSV_backup_20251208`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F18_weekly_points_delta_backup_20251221_065047` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta_backup_20251221_065047`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F19_weekly_assists_delta_backup_20251221_065047` AS
SELECT * FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta_backup_20251221_065047`;

-- player_cumulative_points backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_cumulative_points_backup_20251117` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251117`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_cumulative_points_backup_20251120_210337` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251120_210337`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_cumulative_points_backup_20251208_goalie_fix` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251208_goalie_fix`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_cumulative_points_backup_20260106_f15` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20260106_f15`;

-- player_stats backups
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_backup_20260108_200147` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_stats_backup_20260108_200147`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_backup_20260108_220118` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_stats_backup_20260108_220118`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_backup_20260109_130619` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_stats_backup_20260109_130619`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_backup_20260109_142123` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_stats_backup_20260109_142123`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.player_stats_backup_20260109_200541` AS
SELECT * FROM `prodigy-ranking.algorithm_core.player_stats_backup_20260109_200541`;


-- ============================================================================
-- STEP 3: Staging tables - Move to algorithm_staging or archive
-- ============================================================================

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_staging` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_staging`;

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_staging_20251216` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_staging_20251216`;


-- ============================================================================
-- STEP 4: DROP TABLES FROM algorithm_core
-- ============================================================================
-- IMPORTANT: Only run after verifying copies were successful in archive!
-- ============================================================================

-- Verify counts match before dropping
-- Run verification queries for each table before proceeding

-- DROP statements (uncomment when ready):

/*
-- DL_F13 backups
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251120_210337`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251207`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251216`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251216_085325`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_pre_fix`;

-- DL_F14 backups
DROP TABLE `prodigy-ranking.algorithm_core.DL_F14_team_points_backup_20251121_092810`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F14_team_points_backup_20251121_092834`;

-- DL_F17 backups
DROP TABLE `prodigy-ranking.algorithm_core.DL_F17_draft_points_backup_20251120_205403`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F17_draft_points_backup_20251120_210337`;

-- DL_F22 backups
DROP TABLE `prodigy-ranking.algorithm_core.DL_F22_manual_points_backup_20251120_221752`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F22_manual_points_backup_20251120_221924`;

-- DL_all_leagues backup
DROP TABLE `prodigy-ranking.algorithm_core.DL_all_leagues_backup_20260103`;

-- PT factor backups
DROP TABLE `prodigy-ranking.algorithm_core.PT_F04_CGPGD_backup_20251208_v2`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F06_CGAA_backup_20251119`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F06_CGAA_backup_20251208`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F07_CSV_backup_20251208`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F09_LGPGD_backup_20251208_v2`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F11_LGAA_backup_20251208`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F12_LSV_backup_20251208`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta_backup_20251221_065047`;
DROP TABLE `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta_backup_20251221_065047`;

-- player_cumulative_points backups
DROP TABLE `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251117`;
DROP TABLE `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251120_210337`;
DROP TABLE `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20251208_goalie_fix`;
DROP TABLE `prodigy-ranking.algorithm_core.player_cumulative_points_backup_20260106_f15`;

-- player_stats backups
DROP TABLE `prodigy-ranking.algorithm_core.player_stats_backup_20260108_200147`;
DROP TABLE `prodigy-ranking.algorithm_core.player_stats_backup_20260108_220118`;
DROP TABLE `prodigy-ranking.algorithm_core.player_stats_backup_20260109_130619`;
DROP TABLE `prodigy-ranking.algorithm_core.player_stats_backup_20260109_142123`;
DROP TABLE `prodigy-ranking.algorithm_core.player_stats_backup_20260109_200541`;

-- Staging tables
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_staging`;
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_staging_20251216`;
*/


-- ============================================================================
-- STEP 5: VERIFICATION - Run after archival
-- ============================================================================

-- Count tables remaining in algorithm_core (should be ~65-70 after cleanup)
-- SELECT COUNT(*) as table_count
-- FROM `prodigy-ranking.algorithm_core.INFORMATION_SCHEMA.TABLES`;

-- List remaining tables
-- SELECT table_name, table_type
-- FROM `prodigy-ranking.algorithm_core.INFORMATION_SCHEMA.TABLES`
-- ORDER BY table_name;

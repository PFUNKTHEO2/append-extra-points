-- ============================================================================
-- ARCHIVE TABLES THAT HAVE BEEN CONSOLIDATED
-- ============================================================================
-- These tables have been merged into player_external_factors
-- Archive them before deletion for rollback safety
-- ============================================================================

-- DL_F15: International Points (→ player_external_factors.international_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F15_international_points_final_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`;

-- DL_F17: Draft Points (→ player_external_factors.draft_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F17_draft_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`;

-- PT_F16_CP: Commitment Points (→ player_external_factors.commitment_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.PT_F16_CP_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.PT_F16_CP`;

-- DL_F22: Manual Points (→ player_external_factors.manual_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F22_manual_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`;

-- DL_F20: Playing Up Points (→ player_external_factors.playing_up_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F20_playing_up_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`;

-- DL_F21: Tournament Points (→ player_external_factors.tournament_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F21_tournament_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F21_tournament_points`;

-- DL_F23: ProdigyLikes Points (→ player_external_factors.prodigylikes_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F23_prodigylikes_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`;

-- DL_F24: Card Sales Points (→ player_external_factors.card_sales_points)
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F24_card_sales_points_20260114`
AS SELECT * FROM `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`;

-- ============================================================================
-- VERIFY ARCHIVES BEFORE DELETION
-- ============================================================================
-- Uncomment and run after verifying archives are complete
-- ============================================================================
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F15_international_points_final`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F17_draft_points`;
-- DROP TABLE `prodigy-ranking.algorithm_core.PT_F16_CP`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F22_manual_points`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F21_tournament_points`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`;
-- DROP TABLE `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`;

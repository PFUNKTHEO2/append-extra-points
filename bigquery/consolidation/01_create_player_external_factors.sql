-- ============================================================================
-- CONSOLIDATION PHASE 1: Create player_external_factors table
-- ============================================================================
-- This table consolidates all player-keyed external data into ONE table:
-- - DL_F15_international_points_final → international_points
-- - DL_F17_draft_points → draft_points
-- - PT_F16_CP → commitment_points
-- - DL_F22_manual_points → manual_points
-- - DL_F20, DL_F21, DL_F23, DL_F24 → reserved columns (currently empty)
-- ============================================================================

-- Create the consolidated external factors table
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.player_external_factors` (
  player_id INT64 NOT NULL,
  international_points FLOAT64 DEFAULT 0,
  draft_points FLOAT64 DEFAULT 0,
  commitment_points FLOAT64 DEFAULT 0,
  manual_points FLOAT64 DEFAULT 0,
  tournament_points FLOAT64 DEFAULT 0,
  playing_up_points FLOAT64 DEFAULT 0,
  prodigylikes_points FLOAT64 DEFAULT 0,
  card_sales_points FLOAT64 DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- Add primary key constraint
ALTER TABLE `prodigy-ranking.algorithm_core.player_external_factors`
ADD PRIMARY KEY (player_id) NOT ENFORCED;

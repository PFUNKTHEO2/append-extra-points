-- ============================================================================
-- CREATE WEEKLY STATS SNAPSHOT TABLE
-- ============================================================================
-- This table stores weekly snapshots of player stats for delta calculations:
--   F18: Weekly Goals Delta (40 pts/goal, max 200)
--   F19: Weekly Assists Delta (25 pts/assist, max 125)
--   F25: Weekly EP Views Delta (1 pt/view, max 200)
-- ============================================================================

CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.weekly_stats_snapshot` (
  player_id INT64 NOT NULL,
  snapshot_date DATE NOT NULL,
  goals INT64,           -- Current season goals at snapshot time
  assists INT64,         -- Current season assists at snapshot time
  views INT64,           -- EP views at snapshot time
  games_played INT64,    -- Games played (for reference)
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY snapshot_date
CLUSTER BY player_id
OPTIONS (
  description = 'Weekly stats snapshots for calculating F18/F19/F25 deltas',
  labels = [('purpose', 'algorithm'), ('version', '2026_01_14')]
);

-- Create index-like clustering for efficient lookups
-- BigQuery uses clustering instead of indexes

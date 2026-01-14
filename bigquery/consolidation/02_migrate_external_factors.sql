-- ============================================================================
-- CONSOLIDATION PHASE 1: Migrate data into player_external_factors
-- ============================================================================
-- Merges data from multiple source tables into the consolidated table
-- Uses FULL OUTER JOIN to capture all players from all sources
-- ============================================================================

-- First, let's see what we're working with
-- SELECT 'DL_F15' as source, COUNT(DISTINCT matched_player_id) as players FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`
-- UNION ALL SELECT 'DL_F17', COUNT(DISTINCT player_id) FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
-- UNION ALL SELECT 'PT_F16', COUNT(DISTINCT player_id) FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
-- UNION ALL SELECT 'DL_F22', COUNT(DISTINCT player_id) FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`;

-- Populate the consolidated table
INSERT INTO `prodigy-ranking.algorithm_core.player_external_factors`
(player_id, international_points, draft_points, commitment_points, manual_points,
 tournament_points, playing_up_points, prodigylikes_points, card_sales_points, updated_at)

WITH
-- F15: International Points
f15 AS (
  SELECT
    matched_player_id AS player_id,
    MAX(total_international_points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F15_international_points_final`
  WHERE matched_player_id IS NOT NULL
  GROUP BY matched_player_id
),

-- F17: Draft Points
f17 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F16: Commitment Points
f16 AS (
  SELECT
    player_id,
    MAX(factor_16_commitment_points) AS points
  FROM `prodigy-ranking.algorithm_core.PT_F16_CP`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F22: Manual Points
f22 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F22_manual_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F21: Tournament Points (currently empty but include for completeness)
f21 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F21_tournament_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F20: Playing Up Points (currently empty)
f20 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F20_playing_up_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F23: ProdigyLikes Points (currently empty)
f23 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- F24: Card Sales Points (currently empty)
f24 AS (
  SELECT
    player_id,
    MAX(points) AS points
  FROM `prodigy-ranking.algorithm_core.DL_F24_card_sales_points`
  WHERE player_id IS NOT NULL
  GROUP BY player_id
),

-- Get all unique player IDs across all sources
all_players AS (
  SELECT DISTINCT player_id FROM f15
  UNION DISTINCT SELECT player_id FROM f17
  UNION DISTINCT SELECT player_id FROM f16
  UNION DISTINCT SELECT player_id FROM f22
  UNION DISTINCT SELECT player_id FROM f21
  UNION DISTINCT SELECT player_id FROM f20
  UNION DISTINCT SELECT player_id FROM f23
  UNION DISTINCT SELECT player_id FROM f24
)

SELECT
  ap.player_id,
  COALESCE(f15.points, 0) AS international_points,
  COALESCE(f17.points, 0) AS draft_points,
  COALESCE(f16.points, 0) AS commitment_points,
  COALESCE(f22.points, 0) AS manual_points,
  COALESCE(f21.points, 0) AS tournament_points,
  COALESCE(f20.points, 0) AS playing_up_points,
  COALESCE(f23.points, 0) AS prodigylikes_points,
  COALESCE(f24.points, 0) AS card_sales_points,
  CURRENT_TIMESTAMP() AS updated_at
FROM all_players ap
LEFT JOIN f15 ON ap.player_id = f15.player_id
LEFT JOIN f17 ON ap.player_id = f17.player_id
LEFT JOIN f16 ON ap.player_id = f16.player_id
LEFT JOIN f22 ON ap.player_id = f22.player_id
LEFT JOIN f21 ON ap.player_id = f21.player_id
LEFT JOIN f20 ON ap.player_id = f20.player_id
LEFT JOIN f23 ON ap.player_id = f23.player_id
LEFT JOIN f24 ON ap.player_id = f24.player_id;

-- Verify the migration
-- SELECT
--   COUNT(*) as total_rows,
--   SUM(CASE WHEN international_points > 0 THEN 1 ELSE 0 END) as with_international,
--   SUM(CASE WHEN draft_points > 0 THEN 1 ELSE 0 END) as with_draft,
--   SUM(CASE WHEN commitment_points > 0 THEN 1 ELSE 0 END) as with_commitment,
--   SUM(CASE WHEN manual_points > 0 THEN 1 ELSE 0 END) as with_manual
-- FROM `prodigy-ranking.algorithm_core.player_external_factors`;

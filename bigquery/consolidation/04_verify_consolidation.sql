-- ============================================================================
-- VERIFICATION: Compare player_rankings vs player_cumulative_points
-- ============================================================================
-- Run this AFTER running 03_rebuild_player_rankings_consolidated.sql
-- to verify the new consolidated output matches the existing data.
-- ============================================================================

-- ============================================================================
-- CHECK 1: Row counts
-- ============================================================================
SELECT
  'player_cumulative_points (old)' AS table_name,
  COUNT(*) AS row_count
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
UNION ALL
SELECT
  'player_rankings (new)' AS table_name,
  COUNT(*) AS row_count
FROM `prodigy-ranking.algorithm_core.player_rankings`;


-- ============================================================================
-- CHECK 2: Top 20 players comparison
-- ============================================================================
WITH old_top AS (
  SELECT player_id, player_name, total_points AS old_total
  FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
  ORDER BY total_points DESC
  LIMIT 20
),
new_top AS (
  SELECT player_id, player_name, total_points AS new_total
  FROM `prodigy-ranking.algorithm_core.player_rankings`
  ORDER BY total_points DESC
  LIMIT 20
)
SELECT
  COALESCE(o.player_id, n.player_id) AS player_id,
  COALESCE(o.player_name, n.player_name) AS player_name,
  o.old_total,
  n.new_total,
  ROUND(ABS(COALESCE(o.old_total, 0) - COALESCE(n.new_total, 0)), 2) AS diff
FROM old_top o
FULL OUTER JOIN new_top n ON o.player_id = n.player_id
ORDER BY COALESCE(o.old_total, n.new_total) DESC;


-- ============================================================================
-- CHECK 3: Factor-by-factor comparison (sample of 100 players)
-- ============================================================================
WITH comparison AS (
  SELECT
    o.player_id,
    o.player_name,
    o.f01_views AS old_f01, n.f01_views AS new_f01,
    o.f02_height AS old_f02, n.f02_height AS new_f02,
    o.f03_current_goals_f AS old_f03, n.f03_current_goals_f AS new_f03,
    o.f13_league_points AS old_f13, n.f13_league_points AS new_f13,
    o.f15_international_points AS old_f15, n.f15_international_points AS new_f15,
    o.total_points AS old_total, n.total_points AS new_total
  FROM `prodigy-ranking.algorithm_core.player_cumulative_points` o
  INNER JOIN `prodigy-ranking.algorithm_core.player_rankings` n ON o.player_id = n.player_id
  ORDER BY o.total_points DESC
  LIMIT 100
)
SELECT
  'F01 Views' AS factor,
  ROUND(AVG(ABS(old_f01 - new_f01)), 2) AS avg_diff,
  MAX(ABS(old_f01 - new_f01)) AS max_diff,
  SUM(CASE WHEN ABS(old_f01 - new_f01) > 1 THEN 1 ELSE 0 END) AS diff_count
FROM comparison
UNION ALL
SELECT 'F02 Height', ROUND(AVG(ABS(old_f02 - new_f02)), 2), MAX(ABS(old_f02 - new_f02)), SUM(CASE WHEN ABS(old_f02 - new_f02) > 1 THEN 1 ELSE 0 END) FROM comparison
UNION ALL
SELECT 'F03 Goals F', ROUND(AVG(ABS(old_f03 - new_f03)), 2), MAX(ABS(old_f03 - new_f03)), SUM(CASE WHEN ABS(old_f03 - new_f03) > 1 THEN 1 ELSE 0 END) FROM comparison
UNION ALL
SELECT 'F13 League', ROUND(AVG(ABS(old_f13 - new_f13)), 2), MAX(ABS(old_f13 - new_f13)), SUM(CASE WHEN ABS(old_f13 - new_f13) > 1 THEN 1 ELSE 0 END) FROM comparison
UNION ALL
SELECT 'F15 Intl', ROUND(AVG(ABS(old_f15 - new_f15)), 2), MAX(ABS(old_f15 - new_f15)), SUM(CASE WHEN ABS(old_f15 - new_f15) > 1 THEN 1 ELSE 0 END) FROM comparison
UNION ALL
SELECT 'TOTAL', ROUND(AVG(ABS(old_total - new_total)), 2), MAX(ABS(old_total - new_total)), SUM(CASE WHEN ABS(old_total - new_total) > 1 THEN 1 ELSE 0 END) FROM comparison;


-- ============================================================================
-- CHECK 4: Players missing from one table or the other
-- ============================================================================
SELECT
  'In OLD but not NEW' AS status,
  COUNT(*) AS count
FROM `prodigy-ranking.algorithm_core.player_cumulative_points` o
LEFT JOIN `prodigy-ranking.algorithm_core.player_rankings` n ON o.player_id = n.player_id
WHERE n.player_id IS NULL
UNION ALL
SELECT
  'In NEW but not OLD' AS status,
  COUNT(*) AS count
FROM `prodigy-ranking.algorithm_core.player_rankings` n
LEFT JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` o ON n.player_id = o.player_id
WHERE o.player_id IS NULL;


-- ============================================================================
-- CHECK 5: Distribution of differences
-- ============================================================================
SELECT
  CASE
    WHEN ABS(o.total_points - n.total_points) = 0 THEN 'Exact match'
    WHEN ABS(o.total_points - n.total_points) < 1 THEN 'Diff < 1'
    WHEN ABS(o.total_points - n.total_points) < 10 THEN 'Diff 1-10'
    WHEN ABS(o.total_points - n.total_points) < 100 THEN 'Diff 10-100'
    ELSE 'Diff > 100'
  END AS difference_range,
  COUNT(*) AS player_count
FROM `prodigy-ranking.algorithm_core.player_cumulative_points` o
INNER JOIN `prodigy-ranking.algorithm_core.player_rankings` n ON o.player_id = n.player_id
GROUP BY difference_range
ORDER BY MIN(ABS(o.total_points - n.total_points));


-- ============================================================================
-- CHECK 6: External factors migration verification
-- ============================================================================
SELECT
  'player_external_factors' AS table_name,
  COUNT(*) AS total_rows,
  SUM(CASE WHEN international_points > 0 THEN 1 ELSE 0 END) AS with_international,
  SUM(CASE WHEN draft_points > 0 THEN 1 ELSE 0 END) AS with_draft,
  SUM(CASE WHEN commitment_points > 0 THEN 1 ELSE 0 END) AS with_commitment,
  SUM(CASE WHEN manual_points > 0 THEN 1 ELSE 0 END) AS with_manual
FROM `prodigy-ranking.algorithm_core.player_external_factors`;

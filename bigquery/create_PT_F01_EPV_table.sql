-- Create PT_F01_EPV (Factor 1 - Elite Prospects Views) table
-- Scoring system:
--   - 0 points for views < 100
--   - 2,000 points for views >= 30,000
--   - Linear distribution between 100 and 30,000 views
--   - Formula: (views - 100) * (2000 / 29900)

CREATE OR REPLACE TABLE `prodigy-ranking.algorithm.PT_F01_EPV` AS

SELECT
  id AS player_id,
  name AS player_name,
  yearOfBirth AS birth_year,
  position,
  views AS ep_views,
  nationality_name AS nationality,
  CASE
    WHEN views < 100 THEN 0
    WHEN views >= 30000 THEN 2000
    ELSE (views - 100) * (2000.0 / 29900.0)
  END AS factor_1_epv_points
FROM `prodigy-ranking.algorithm_core.player_stats`
WHERE views IS NOT NULL
ORDER BY factor_1_epv_points DESC;

-- Verify the table creation
SELECT
  COUNT(*) as total_players,
  ROUND(SUM(factor_1_epv_points), 2) as total_points,
  ROUND(AVG(factor_1_epv_points), 2) as avg_points,
  ROUND(MAX(factor_1_epv_points), 2) as max_points,
  ROUND(MIN(factor_1_epv_points), 2) as min_points
FROM `prodigy-ranking.algorithm.PT_F01_EPV`;

-- View top 20 players by EP Views points
SELECT
  player_name,
  birth_year,
  position,
  nationality,
  ep_views,
  ROUND(factor_1_epv_points, 2) as f1_points
FROM `prodigy-ranking.algorithm.PT_F01_EPV`
ORDER BY factor_1_epv_points DESC
LIMIT 20;

-- Distribution by point ranges
SELECT
  CASE
    WHEN factor_1_epv_points = 0 THEN '0 points (< 100 views)'
    WHEN factor_1_epv_points >= 2000 THEN '2,000 points (>= 30,000 views)'
    WHEN factor_1_epv_points < 500 THEN '1-499 points'
    WHEN factor_1_epv_points < 1000 THEN '500-999 points'
    WHEN factor_1_epv_points < 1500 THEN '1,000-1,499 points'
    ELSE '1,500-1,999 points'
  END as point_range,
  COUNT(*) as player_count,
  ROUND(SUM(factor_1_epv_points), 2) as total_points
FROM `prodigy-ranking.algorithm.PT_F01_EPV`
GROUP BY point_range
ORDER BY MIN(factor_1_epv_points);

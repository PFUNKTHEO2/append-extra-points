-- ============================================================================
-- Create PT_F28_NHLSR Table - Factor 28 NHL Scouting Report
-- ============================================================================
--
-- PURPOSE: Create Factor 28 (NHL Central Scouting Mid-Term Rankings) table
--          following the standard PT_F** schema pattern
--
-- SOURCE: NHL Central Scouting Mid-Term Rankings 2025/2026
--         - North American Skaters (225 players, including 1 Limited Viewing)
--         - North American Goalies (37 players)
--         - International Skaters (128 players)
--         - International Goalies (20 players)
--
-- POINTS FORMULA:
--   - First place in each list: 1000 points
--   - Last place in each list: 500 points
--   - Linear interpolation in between
--
-- USAGE:
-- 1. First run create_f28_nhl_scouting.py to upload matched data
-- 2. Or manually upload F28_nhl_scouting_matched.csv as F28_import
-- 3. Then run this SQL to verify/create the final table
-- ============================================================================

-- Verify the uploaded data
SELECT
  list_type,
  COUNT(*) as player_count,
  MIN(factor_28_nhl_scouting_points) as min_points,
  MAX(factor_28_nhl_scouting_points) as max_points,
  ROUND(AVG(factor_28_nhl_scouting_points), 1) as avg_points
FROM `prodigy-ranking.algorithm_core.PT_F28_NHLSR`
GROUP BY list_type
ORDER BY list_type;

-- Top 20 players by F28 points
SELECT
  player_name,
  list_type,
  nhl_scouting_rank,
  team,
  position,
  factor_28_nhl_scouting_points
FROM `prodigy-ranking.algorithm_core.PT_F28_NHLSR`
ORDER BY factor_28_nhl_scouting_points DESC
LIMIT 20;

-- Distribution by position
SELECT
  position,
  COUNT(*) as player_count,
  ROUND(AVG(factor_28_nhl_scouting_points), 1) as avg_points,
  MIN(factor_28_nhl_scouting_points) as min_points,
  MAX(factor_28_nhl_scouting_points) as max_points
FROM `prodigy-ranking.algorithm_core.PT_F28_NHLSR`
GROUP BY position
ORDER BY player_count DESC;

-- ============================================================================
-- FIXES FOR PRODIGYCHAIN ALGORITHM DATA ISSUES
-- ============================================================================
-- Issue #1: Draft points exceeding 300 (max is 1300, should be 300)
-- Issue #2: OHL players getting only 150 points (should get 1000 points)
-- ============================================================================

-- ============================================================================
-- ISSUE #1: DRAFT POINTS FIX
-- ============================================================================
-- Problem: Players are getting up to 1,300 draft points when max should be 300
-- Root Cause: The DL_F17_draft_points table has points values of 1300, 1299, 1298...
--             These appear to be based directly on draft position
-- Affected: 796 players with draft points > 300
-- ============================================================================

-- Option 1A: Scale all draft points proportionally (1300 -> 300)
-- This maintains the relative differences between draft picks
UPDATE `prodigy-ranking.algorithm_core.DL_F17_draft_points`
SET points = CAST(ROUND(points * 300.0 / 1300.0, 0) AS INT64)
WHERE points > 300;

-- Option 1B: Cap all draft points at 300 (preserves high values, loses granularity)
UPDATE `prodigy-ranking.algorithm_core.DL_F17_draft_points`
SET points = 300
WHERE points > 300;

-- Option 1C: Create a proper draft point scale based on pick position
-- This creates a more sophisticated scaling system
-- Assuming pick #1 = 300 points, decreasing gradually
-- Formula: 300 - (best_draft_pick - 1) * scale_factor
-- For 300 points spread across ~300 picks: scale_factor ≈ 1
UPDATE `prodigy-ranking.algorithm_core.DL_F17_draft_points`
SET points = CASE
  WHEN best_draft_pick = 1 THEN 300
  WHEN best_draft_pick <= 10 THEN 300 - (best_draft_pick - 1) * 5  -- Top 10: 300 to 255
  WHEN best_draft_pick <= 30 THEN 255 - (best_draft_pick - 10) * 3 -- 11-30: 255 to 195
  WHEN best_draft_pick <= 60 THEN 195 - (best_draft_pick - 30) * 2 -- 31-60: 195 to 135
  WHEN best_draft_pick <= 100 THEN 135 - (best_draft_pick - 60) * 1 -- 61-100: 135 to 95
  WHEN best_draft_pick <= 200 THEN GREATEST(50, 95 - (best_draft_pick - 100) * 0.45) -- 101-200: 95 to 50
  ELSE GREATEST(10, 50 - (best_draft_pick - 200) * 0.2) -- 201+: 50 to 10
END
WHERE points > 300;

-- RECOMMENDED: Option 1A (proportional scaling)
-- This is the simplest and maintains relative differences


-- ============================================================================
-- ISSUE #2: OHL LEAGUE POINTS FIX
-- ============================================================================
-- Problem: OHL (Ontario Hockey League) teams getting only 150 points instead of 1000
-- Root Cause: The DL_F13_league_points table has:
--   - "ohl" (lowercase) = 150 points, USA, Tier 7 (WRONG - this is a different league)
--   - Missing "OHL" (uppercase) entry for the real Ontario Hockey League
--   - QMJHL and WHL both correctly have 1000 points as Tier 1 Canadian leagues
-- Affected: 290+ OHL players from teams like Windsor Spitfires, London Knights, etc.
-- Expected: OHL should be 1000 points (same as QMJHL and WHL)
-- ============================================================================

-- Option 2A: Insert missing OHL entry (RECOMMENDED)
-- This adds the proper Ontario Hockey League entry
INSERT INTO `prodigy-ranking.algorithm_core.DL_F13_league_points`
(league_name, points, season, is_active, updated_at, nation, tier, number_of_teams)
VALUES
('OHL', 1000, '2024-2025', TRUE, CURRENT_TIMESTAMP(), 'Canada', 1, 17);

-- Option 2B: Update existing lowercase "ohl" entry if it's actually meant to be OHL
-- WARNING: Only use this if you're sure the lowercase "ohl" was meant to be Ontario Hockey League
UPDATE `prodigy-ranking.algorithm_core.DL_F13_league_points`
SET
  points = 1000,
  nation = 'Canada',
  tier = 1,
  number_of_teams = 17,
  updated_at = CURRENT_TIMESTAMP()
WHERE league_name = 'ohl';

-- RECOMMENDED: Option 2A (Insert new entry)
-- Then verify the lowercase "ohl" is actually a different minor league


-- ============================================================================
-- AFTER APPLYING FIXES: REBUILD player_cumulative_points
-- ============================================================================
-- The player_cumulative_points table needs to be recalculated
-- Run your algorithm's rebuild/recalculation process to propagate these changes
-- to the player_cumulative_points table

-- You can verify the fixes with these queries:

-- Verify Draft Points Fix:
SELECT
  MAX(points) as max_draft_points,
  MIN(points) as min_draft_points,
  AVG(points) as avg_draft_points,
  COUNT(*) as total_players
FROM `prodigy-ranking.algorithm_core.DL_F17_draft_points`
WHERE points > 0;

-- Verify OHL League Points Fix:
SELECT *
FROM `prodigy-ranking.algorithm_core.DL_F13_league_points`
WHERE league_name IN ('OHL', 'ohl', 'QMJHL', 'WHL')
ORDER BY points DESC;

-- Check affected players after rebuild:
SELECT
  COUNT(*) as ohl_players,
  AVG(f13_league_points) as avg_league_points,
  MIN(f13_league_points) as min_league_points,
  MAX(f13_league_points) as max_league_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_league = 'OHL';


-- ============================================================================
-- IMPACT ANALYSIS
-- ============================================================================
-- Issue #1 Impact:
--   - 796 players will have their draft points reduced from 300-1300 range to 0-300 range
--   - Total points for these players will decrease proportionally
--   - Rankings may shift for players with high draft points

-- Issue #2 Impact:
--   - 290+ OHL players will gain 850 points (1000 - 150)
--   - This is a significant boost that will improve their rankings considerably
--   - OHL players will now be on par with QMJHL and WHL players

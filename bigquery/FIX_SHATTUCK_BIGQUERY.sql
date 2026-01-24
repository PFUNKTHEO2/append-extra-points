-- Fix Shattuck St. Mary's in BigQuery for NEPSAC GameDay
-- One-off update for Dexter exhibition games (Jan 23-24, 2026)

-- 1. Add Shattuck to nepsac_teams (if not exists)
INSERT INTO `prodigy-ranking.algorithm_core.nepsac_teams`
  (team_id, team_name, short_name, division, logo_url, venue, city, state, is_active)
VALUES
  ('shattuck-st-marys', 'Shattuck St. Mary''s', 'Shattuck', 'Non-NEPSAC', NULL, 'Shattuck St. Mary''s Arena', 'Faribault', 'MN', TRUE)
ON DUPLICATE KEY UPDATE team_name = 'Shattuck St. Mary''s';

-- Alternative for BigQuery (MERGE):
MERGE INTO `prodigy-ranking.algorithm_core.nepsac_teams` AS target
USING (SELECT 'shattuck-st-marys' as team_id) AS source
ON target.team_id = source.team_id
WHEN NOT MATCHED THEN
  INSERT (team_id, team_name, short_name, division, logo_url, venue, city, state, is_active)
  VALUES ('shattuck-st-marys', 'Shattuck St. Mary''s', 'Shattuck', 'Non-NEPSAC', NULL, 'Shattuck St. Mary''s Arena', 'Faribault', 'MN', TRUE);

-- 2. Add Shattuck to nepsac_team_rankings with normalized OVR
MERGE INTO `prodigy-ranking.algorithm_core.nepsac_team_rankings` AS target
USING (SELECT 'shattuck-st-marys' as team_id, '2025-26' as season) AS source
ON target.team_id = source.team_id AND target.season = source.season
WHEN NOT MATCHED THEN
  INSERT (team_id, season, rank, team_ovr, avg_prodigy_points, total_prodigy_points, max_prodigy_points, roster_size, matched_players, match_rate)
  VALUES ('shattuck-st-marys', '2025-26', NULL, 88, 2900, 58000, 4500, 22, 0, 0)
WHEN MATCHED THEN
  UPDATE SET team_ovr = 88, avg_prodigy_points = 2900;

-- 3. Update schedule predictions for Dexter @ Shattuck games
UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule`
SET
  predicted_winner_id = 'dexter',
  prediction_confidence = 54
WHERE
  (home_team_id = 'shattuck-st-marys' OR away_team_id = 'shattuck-st-marys')
  AND season = '2025-26';

-- 4. Verify the updates
SELECT
  game_date,
  away_team_id,
  home_team_id,
  predicted_winner_id,
  prediction_confidence
FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
WHERE home_team_id = 'shattuck-st-marys' OR away_team_id = 'shattuck-st-marys';

SELECT * FROM `prodigy-ranking.algorithm_core.nepsac_teams` WHERE team_id = 'shattuck-st-marys';
SELECT * FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings` WHERE team_id = 'shattuck-st-marys';

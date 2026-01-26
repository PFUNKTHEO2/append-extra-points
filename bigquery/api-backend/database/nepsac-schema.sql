-- NEPSAC Database Schema
-- Tables for managing NEPSAC prep school hockey data
-- Created: 2026-01-20

-- =============================================================================
-- NEPSAC Teams Table
-- =============================================================================
-- Stores all NEPSAC prep school hockey teams with their metadata
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_teams` (
  team_id STRING NOT NULL,
  team_name STRING NOT NULL,
  short_name STRING,
  division STRING,  -- 'Large School', 'Small School', 'Independent', etc.
  logo_url STRING,
  primary_color STRING,
  secondary_color STRING,
  venue STRING,
  city STRING,
  state STRING,
  ep_team_id INT64,  -- Link to EliteProspects team ID if available
  mhr_team_id STRING,  -- Link to MyHockeyRankings team ID if available
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- NEPSAC Rosters Table
-- =============================================================================
-- Links players to their NEPSAC teams with roster-specific info
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_rosters` (
  roster_id STRING NOT NULL,
  team_id STRING NOT NULL,
  player_id INT64,  -- Links to player_cumulative_points.player_id
  roster_name STRING NOT NULL,  -- Name as listed on roster (may differ from DB)
  position STRING,  -- F, D, G
  grad_year INT64,
  jersey_number STRING,
  season STRING NOT NULL,  -- '2025-26'
  is_captain BOOL DEFAULT FALSE,
  is_active BOOL DEFAULT TRUE,
  match_confidence FLOAT64,  -- 0-1 score of name match confidence
  image_url STRING,  -- Cached from players table
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- NEPSAC Schedule Table
-- =============================================================================
-- Game schedule with predictions and results
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_schedule` (
  game_id STRING NOT NULL,
  season STRING NOT NULL,
  game_date DATE NOT NULL,
  game_time STRING,
  day_of_week STRING,  -- 'Monday', 'Tuesday', etc.
  away_team_id STRING NOT NULL,
  home_team_id STRING NOT NULL,
  venue STRING,
  city STRING,
  status STRING DEFAULT 'scheduled',  -- scheduled, in_progress, final, postponed, cancelled
  away_score INT64,
  home_score INT64,
  overtime BOOL DEFAULT FALSE,
  shootout BOOL DEFAULT FALSE,
  predicted_winner_id STRING,
  prediction_confidence INT64,  -- 50-99 percent
  prediction_method STRING DEFAULT 'prodigy_points',  -- How prediction was calculated
  notes STRING,
  source_url STRING,  -- Where schedule was scraped from
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- NEPSAC Standings Table
-- =============================================================================
-- Current season standings by team
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_standings` (
  standing_id STRING NOT NULL,
  team_id STRING NOT NULL,
  season STRING NOT NULL,
  division STRING,
  wins INT64 DEFAULT 0,
  losses INT64 DEFAULT 0,
  ties INT64 DEFAULT 0,
  overtime_losses INT64 DEFAULT 0,
  goals_for INT64 DEFAULT 0,
  goals_against INT64 DEFAULT 0,
  goal_differential INT64 DEFAULT 0,
  points INT64 DEFAULT 0,  -- Standings points (typically 2 for W, 1 for T/OTL)
  win_pct FLOAT64 DEFAULT 0.0,
  games_played INT64 DEFAULT 0,
  streak STRING,  -- 'W3', 'L1', etc.
  last_10 STRING,  -- '7-2-1'
  home_record STRING,  -- '5-1-0'
  away_record STRING,  -- '4-2-1'
  last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- NEPSAC Team Rankings Table
-- =============================================================================
-- ProdigyPoints-based team rankings (calculated from roster)
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_team_rankings` (
  ranking_id STRING NOT NULL,
  team_id STRING NOT NULL,
  season STRING NOT NULL,
  rank INT64,
  roster_size INT64,
  matched_players INT64,  -- How many roster players matched to DB
  match_rate FLOAT64,  -- matched_players / roster_size
  avg_prodigy_points FLOAT64,
  total_prodigy_points FLOAT64,
  max_prodigy_points FLOAT64,
  min_prodigy_points FLOAT64,
  median_prodigy_points FLOAT64,
  top_player_id INT64,  -- Player with highest points
  top_player_name STRING,
  team_ovr INT64,  -- EA Sports style rating (70-99)
  calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- NEPSAC Game Predictions Log
-- =============================================================================
-- Historical predictions for accuracy tracking
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_predictions_log` (
  prediction_id STRING NOT NULL,
  game_id STRING NOT NULL,
  predicted_at TIMESTAMP NOT NULL,
  predicted_winner_id STRING,
  prediction_confidence INT64,
  away_team_points FLOAT64,  -- Team avg points at time of prediction
  home_team_points FLOAT64,
  actual_winner_id STRING,  -- Filled in after game
  was_correct BOOL,  -- True if prediction matched result
  margin_of_victory INT64  -- Score difference
);

-- =============================================================================
-- NEPSAC Game Performers Table
-- =============================================================================
-- Per-game scoring stats for individual players (for GameDay Top Performers)
-- Data source: Manual entry, Elite Prospects box scores, or team websites
CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_game_performers` (
  performer_id STRING NOT NULL,
  game_id STRING NOT NULL,  -- Links to nepsac_schedule.game_id
  game_date DATE NOT NULL,
  player_id INT64,  -- Links to player_cumulative_points.player_id (may be NULL if unmatched)
  roster_name STRING NOT NULL,  -- Name as it appears in box score
  team_id STRING NOT NULL,  -- Links to nepsac_teams.team_id
  position STRING,  -- F, D, G

  -- Skater stats
  goals INT64 DEFAULT 0,
  assists INT64 DEFAULT 0,
  points INT64 DEFAULT 0,  -- goals + assists (computed for convenience)
  plus_minus INT64,
  pim INT64,  -- Penalty minutes
  shots INT64,

  -- Goalie stats
  saves INT64,
  goals_against INT64,
  shots_faced INT64,
  save_pct FLOAT64,
  is_shutout BOOL DEFAULT FALSE,
  is_win BOOL,
  is_loss BOOL,
  is_otl BOOL,  -- Overtime loss

  -- Metadata
  is_star_of_game BOOL DEFAULT FALSE,  -- First/Second/Third star
  star_rank INT64,  -- 1, 2, or 3
  source STRING,  -- 'manual', 'elite_prospects', 'neutral_zone', 'team_website'
  notes STRING,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
);

-- =============================================================================
-- Indexes (for query performance)
-- =============================================================================
-- Note: BigQuery doesn't use traditional indexes, but clustering can help

-- Cluster nepsac_schedule by date and season for efficient filtering
-- ALTER TABLE `prodigy-ranking.algorithm_core.nepsac_schedule`
-- CLUSTER BY game_date, season;

-- Cluster nepsac_rosters by team for roster lookups
-- ALTER TABLE `prodigy-ranking.algorithm_core.nepsac_rosters`
-- CLUSTER BY team_id, season;

-- =============================================================================
-- Sample Data Queries
-- =============================================================================

-- Get all games for a specific date
-- SELECT
--   s.game_id, s.game_time, s.venue,
--   away.team_name as away_team, home.team_name as home_team,
--   s.predicted_winner_id, s.prediction_confidence
-- FROM `prodigy-ranking.algorithm_core.nepsac_schedule` s
-- JOIN `prodigy-ranking.algorithm_core.nepsac_teams` away ON s.away_team_id = away.team_id
-- JOIN `prodigy-ranking.algorithm_core.nepsac_teams` home ON s.home_team_id = home.team_id
-- WHERE s.game_date = '2026-01-21'
-- ORDER BY s.game_time;

-- Get team roster with player stats
-- SELECT
--   r.roster_name, r.position, r.grad_year,
--   p.total_points, p.overall_rating
-- FROM `prodigy-ranking.algorithm_core.nepsac_rosters` r
-- LEFT JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` p
--   ON r.player_id = p.player_id
-- WHERE r.team_id = 'avon-old-farms'
--   AND r.season = '2025-26'
-- ORDER BY p.total_points DESC
-- LIMIT 6;

-- Get team standings with ranking
-- SELECT
--   t.team_name,
--   st.wins, st.losses, st.ties, st.win_pct,
--   tr.rank, tr.avg_prodigy_points, tr.team_ovr
-- FROM `prodigy-ranking.algorithm_core.nepsac_teams` t
-- JOIN `prodigy-ranking.algorithm_core.nepsac_standings` st ON t.team_id = st.team_id
-- JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` tr ON t.team_id = tr.team_id
-- WHERE st.season = '2025-26' AND tr.season = '2025-26'
-- ORDER BY tr.rank;

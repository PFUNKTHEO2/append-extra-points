-- =============================================================================
-- NEPSAC Predictions Schema for Supabase (PostgreSQL)
-- For Ace & Scouty GameDay App
-- =============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================================================
-- NEPSAC Teams
-- =============================================================================
CREATE TABLE IF NOT EXISTS nepsac_teams (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_id TEXT UNIQUE NOT NULL,  -- 'avon-old-farms', 'salisbury-school', etc.
  team_name TEXT NOT NULL,
  short_name TEXT,
  division TEXT,  -- 'Elite 8', 'Large School', 'Small School'
  logo_url TEXT,
  primary_color TEXT,
  secondary_color TEXT,
  venue TEXT,
  city TEXT,
  state TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- NEPSAC Games (Schedule + Results)
-- =============================================================================
CREATE TABLE IF NOT EXISTS nepsac_games (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  game_id TEXT UNIQUE NOT NULL,  -- 'game_0001', etc.
  season TEXT NOT NULL DEFAULT '2025-26',
  game_date DATE NOT NULL,
  game_time TEXT,

  -- Teams
  away_team_id TEXT NOT NULL REFERENCES nepsac_teams(team_id),
  home_team_id TEXT NOT NULL REFERENCES nepsac_teams(team_id),
  away_record TEXT,  -- '10-1-0' at time of game
  home_record TEXT,

  -- Venue
  venue TEXT,
  city TEXT,

  -- Game Status & Results
  status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'in_progress', 'final', 'postponed', 'cancelled')),
  away_score INTEGER,
  home_score INTEGER,
  is_overtime BOOLEAN DEFAULT FALSE,
  is_shootout BOOLEAN DEFAULT FALSE,

  -- Our Prediction
  predicted_winner_id TEXT REFERENCES nepsac_teams(team_id),
  prediction_confidence INTEGER CHECK (prediction_confidence >= 50 AND prediction_confidence <= 99),
  prediction_tier TEXT CHECK (prediction_tier IN ('Very High', 'High', 'Medium', 'Low', 'Toss-up')),

  -- Prediction Factors (stored as JSONB for flexibility)
  prediction_factors JSONB,

  -- Result tracking
  actual_winner_id TEXT REFERENCES nepsac_teams(team_id),  -- NULL for ties
  is_tie BOOLEAN DEFAULT FALSE,
  prediction_correct BOOLEAN,  -- TRUE=correct, FALSE=wrong, NULL=tie or not played

  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Prediction Model Weights History
-- =============================================================================
CREATE TABLE IF NOT EXISTS nepsac_model_weights (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  version TEXT NOT NULL,  -- 'v1.0', 'v2.0'
  effective_date DATE NOT NULL,

  -- Weights (must sum to 1.0)
  mhr_rating DECIMAL(4,3) NOT NULL,
  top_player DECIMAL(4,3) NOT NULL,
  recent_form DECIMAL(4,3) NOT NULL,
  home_advantage DECIMAL(4,3) NOT NULL,
  prodigy_points DECIMAL(4,3) NOT NULL,
  head_to_head DECIMAL(4,3) NOT NULL,
  expert_rank DECIMAL(4,3) NOT NULL,
  goal_diff DECIMAL(4,3) NOT NULL,
  win_pct DECIMAL(4,3) NOT NULL,

  -- Home factor
  home_factor DECIMAL(4,3) NOT NULL DEFAULT 0.58,

  -- Performance notes
  notes TEXT,
  accuracy_at_update DECIMAL(5,2),  -- Accuracy % when this version was created

  is_active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Daily Prediction Summary (Aggregated stats by date)
-- =============================================================================
CREATE TABLE IF NOT EXISTS nepsac_daily_summary (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  game_date DATE UNIQUE NOT NULL,

  total_games INTEGER DEFAULT 0,
  games_predicted INTEGER DEFAULT 0,
  games_completed INTEGER DEFAULT 0,

  correct_predictions INTEGER DEFAULT 0,
  incorrect_predictions INTEGER DEFAULT 0,
  ties INTEGER DEFAULT 0,

  accuracy DECIMAL(5,2),  -- Percentage (ties excluded from calculation)

  -- Breakdown by confidence tier
  very_high_correct INTEGER DEFAULT 0,
  very_high_total INTEGER DEFAULT 0,
  high_correct INTEGER DEFAULT 0,
  high_total INTEGER DEFAULT 0,
  medium_correct INTEGER DEFAULT 0,
  medium_total INTEGER DEFAULT 0,
  low_correct INTEGER DEFAULT 0,
  low_total INTEGER DEFAULT 0,
  tossup_correct INTEGER DEFAULT 0,
  tossup_total INTEGER DEFAULT 0,

  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================================================
-- Overall Stats (Single row, updated after each game day)
-- =============================================================================
CREATE TABLE IF NOT EXISTS nepsac_overall_stats (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  season TEXT NOT NULL DEFAULT '2025-26',

  total_predictions INTEGER DEFAULT 0,
  correct_predictions INTEGER DEFAULT 0,
  incorrect_predictions INTEGER DEFAULT 0,
  ties INTEGER DEFAULT 0,

  overall_accuracy DECIMAL(5,2),

  -- By tier
  very_high_accuracy DECIMAL(5,2),
  high_accuracy DECIMAL(5,2),
  medium_accuracy DECIMAL(5,2),
  low_accuracy DECIMAL(5,2),
  tossup_accuracy DECIMAL(5,2),

  -- Best/worst streaks
  current_streak INTEGER DEFAULT 0,  -- Positive = winning streak, negative = losing
  best_streak INTEGER DEFAULT 0,
  worst_streak INTEGER DEFAULT 0,

  last_updated TIMESTAMPTZ DEFAULT NOW(),

  UNIQUE(season)
);

-- =============================================================================
-- Indexes for Performance
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_games_date ON nepsac_games(game_date);
CREATE INDEX IF NOT EXISTS idx_games_status ON nepsac_games(status);
CREATE INDEX IF NOT EXISTS idx_games_season ON nepsac_games(season);
CREATE INDEX IF NOT EXISTS idx_games_away_team ON nepsac_games(away_team_id);
CREATE INDEX IF NOT EXISTS idx_games_home_team ON nepsac_games(home_team_id);

-- =============================================================================
-- Row Level Security (RLS) Policies
-- =============================================================================
-- Enable RLS
ALTER TABLE nepsac_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE nepsac_games ENABLE ROW LEVEL SECURITY;
ALTER TABLE nepsac_model_weights ENABLE ROW LEVEL SECURITY;
ALTER TABLE nepsac_daily_summary ENABLE ROW LEVEL SECURITY;
ALTER TABLE nepsac_overall_stats ENABLE ROW LEVEL SECURITY;

-- Public read access (anyone can view)
CREATE POLICY "Public read access" ON nepsac_teams FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nepsac_games FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nepsac_model_weights FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nepsac_daily_summary FOR SELECT USING (true);
CREATE POLICY "Public read access" ON nepsac_overall_stats FOR SELECT USING (true);

-- Only authenticated/service role can write
CREATE POLICY "Service write access" ON nepsac_teams FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service write access" ON nepsac_games FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service write access" ON nepsac_model_weights FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service write access" ON nepsac_daily_summary FOR ALL USING (auth.role() = 'service_role');
CREATE POLICY "Service write access" ON nepsac_overall_stats FOR ALL USING (auth.role() = 'service_role');

-- =============================================================================
-- Trigger to update timestamps
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_nepsac_games_updated_at
  BEFORE UPDATE ON nepsac_games
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_nepsac_teams_updated_at
  BEFORE UPDATE ON nepsac_teams
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Function to recalculate daily summary after game update
-- =============================================================================
CREATE OR REPLACE FUNCTION recalculate_daily_summary(target_date DATE)
RETURNS VOID AS $$
DECLARE
  stats RECORD;
BEGIN
  -- Calculate stats for the date
  SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE predicted_winner_id IS NOT NULL) as predicted,
    COUNT(*) FILTER (WHERE status = 'final') as completed,
    COUNT(*) FILTER (WHERE prediction_correct = true) as correct,
    COUNT(*) FILTER (WHERE prediction_correct = false) as incorrect,
    COUNT(*) FILTER (WHERE is_tie = true) as ties,
    COUNT(*) FILTER (WHERE prediction_tier = 'Very High' AND prediction_correct = true) as vh_correct,
    COUNT(*) FILTER (WHERE prediction_tier = 'Very High' AND prediction_correct IS NOT NULL) as vh_total,
    COUNT(*) FILTER (WHERE prediction_tier = 'High' AND prediction_correct = true) as h_correct,
    COUNT(*) FILTER (WHERE prediction_tier = 'High' AND prediction_correct IS NOT NULL) as h_total,
    COUNT(*) FILTER (WHERE prediction_tier = 'Medium' AND prediction_correct = true) as m_correct,
    COUNT(*) FILTER (WHERE prediction_tier = 'Medium' AND prediction_correct IS NOT NULL) as m_total,
    COUNT(*) FILTER (WHERE prediction_tier = 'Low' AND prediction_correct = true) as l_correct,
    COUNT(*) FILTER (WHERE prediction_tier = 'Low' AND prediction_correct IS NOT NULL) as l_total,
    COUNT(*) FILTER (WHERE prediction_tier = 'Toss-up' AND prediction_correct = true) as t_correct,
    COUNT(*) FILTER (WHERE prediction_tier = 'Toss-up' AND prediction_correct IS NOT NULL) as t_total
  INTO stats
  FROM nepsac_games
  WHERE game_date = target_date;

  -- Upsert daily summary
  INSERT INTO nepsac_daily_summary (
    game_date, total_games, games_predicted, games_completed,
    correct_predictions, incorrect_predictions, ties, accuracy,
    very_high_correct, very_high_total, high_correct, high_total,
    medium_correct, medium_total, low_correct, low_total,
    tossup_correct, tossup_total
  ) VALUES (
    target_date, stats.total, stats.predicted, stats.completed,
    stats.correct, stats.incorrect, stats.ties,
    CASE WHEN (stats.correct + stats.incorrect) > 0
         THEN ROUND(100.0 * stats.correct / (stats.correct + stats.incorrect), 1)
         ELSE NULL END,
    stats.vh_correct, stats.vh_total, stats.h_correct, stats.h_total,
    stats.m_correct, stats.m_total, stats.l_correct, stats.l_total,
    stats.t_correct, stats.t_total
  )
  ON CONFLICT (game_date) DO UPDATE SET
    total_games = EXCLUDED.total_games,
    games_predicted = EXCLUDED.games_predicted,
    games_completed = EXCLUDED.games_completed,
    correct_predictions = EXCLUDED.correct_predictions,
    incorrect_predictions = EXCLUDED.incorrect_predictions,
    ties = EXCLUDED.ties,
    accuracy = EXCLUDED.accuracy,
    very_high_correct = EXCLUDED.very_high_correct,
    very_high_total = EXCLUDED.very_high_total,
    high_correct = EXCLUDED.high_correct,
    high_total = EXCLUDED.high_total,
    medium_correct = EXCLUDED.medium_correct,
    medium_total = EXCLUDED.medium_total,
    low_correct = EXCLUDED.low_correct,
    low_total = EXCLUDED.low_total,
    tossup_correct = EXCLUDED.tossup_correct,
    tossup_total = EXCLUDED.tossup_total,
    updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Insert current model weights (v2.0)
-- =============================================================================
INSERT INTO nepsac_model_weights (
  version, effective_date,
  mhr_rating, top_player, recent_form, home_advantage,
  prodigy_points, head_to_head, expert_rank, goal_diff, win_pct,
  home_factor, notes, accuracy_at_update, is_active
) VALUES (
  'v2.0', '2026-01-22',
  0.30, 0.15, 0.15, 0.12,
  0.10, 0.08, 0.05, 0.03, 0.02,
  0.58, 'Recalibrated from Jan 21 results. MHR+TopPlayer boosted, Expert/GoalDiff/WinPct reduced.', 75.0, TRUE
) ON CONFLICT DO NOTHING;

-- Initial v1.0 for history
INSERT INTO nepsac_model_weights (
  version, effective_date,
  mhr_rating, top_player, recent_form, home_advantage,
  prodigy_points, head_to_head, expert_rank, goal_diff, win_pct,
  home_factor, notes, is_active
) VALUES (
  'v1.0', '2026-01-19',
  0.25, 0.05, 0.15, 0.08,
  0.15, 0.05, 0.10, 0.10, 0.07,
  0.55, 'Initial weights - theory based', FALSE
) ON CONFLICT DO NOTHING;

-- =============================================================================
-- Initialize overall stats for 2025-26 season
-- =============================================================================
INSERT INTO nepsac_overall_stats (season)
VALUES ('2025-26')
ON CONFLICT (season) DO NOTHING;

-- =============================================================================
-- NEPSAC Game Performers (Per-game scoring stats)
-- =============================================================================
-- Stores individual player stats from each game for Top Performers feature
CREATE TABLE IF NOT EXISTS nepsac_game_performers (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  performer_id TEXT UNIQUE NOT NULL,  -- '{game_id}_{sequence}'
  game_id TEXT NOT NULL REFERENCES nepsac_games(game_id),
  game_date DATE NOT NULL,
  player_id BIGINT,  -- Links to player DB (may be NULL if unmatched)
  roster_name TEXT NOT NULL,
  team_id TEXT NOT NULL REFERENCES nepsac_teams(team_id),
  position TEXT CHECK (position IN ('F', 'D', 'G')),

  -- Skater stats
  goals INTEGER DEFAULT 0,
  assists INTEGER DEFAULT 0,
  points INTEGER DEFAULT 0,  -- goals + assists
  plus_minus INTEGER,
  pim INTEGER,  -- Penalty minutes
  shots INTEGER,

  -- Goalie stats
  saves INTEGER,
  goals_against INTEGER,
  shots_faced INTEGER,
  save_pct DECIMAL(5,3),
  is_shutout BOOLEAN DEFAULT FALSE,
  is_win BOOLEAN,
  is_loss BOOLEAN,
  is_otl BOOLEAN,  -- Overtime loss

  -- Recognition
  is_star_of_game BOOLEAN DEFAULT FALSE,
  star_rank INTEGER CHECK (star_rank IN (1, 2, 3)),  -- 1st, 2nd, 3rd star

  -- Metadata
  source TEXT DEFAULT 'manual' CHECK (source IN ('manual', 'elite_prospects', 'neutral_zone', 'team_website')),
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_performers_game_date ON nepsac_game_performers(game_date);
CREATE INDEX IF NOT EXISTS idx_performers_game_id ON nepsac_game_performers(game_id);
CREATE INDEX IF NOT EXISTS idx_performers_team_id ON nepsac_game_performers(team_id);
CREATE INDEX IF NOT EXISTS idx_performers_player_id ON nepsac_game_performers(player_id);

-- Enable RLS
ALTER TABLE nepsac_game_performers ENABLE ROW LEVEL SECURITY;

-- Public read access
CREATE POLICY "Public read access" ON nepsac_game_performers FOR SELECT USING (true);

-- Service role write access
CREATE POLICY "Service write access" ON nepsac_game_performers FOR ALL USING (auth.role() = 'service_role');

-- Trigger for updated_at
CREATE TRIGGER update_nepsac_game_performers_updated_at
  BEFORE UPDATE ON nepsac_game_performers
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

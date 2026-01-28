-- ============================================================
-- Player Rankings Table for Fast API Lookups
-- ============================================================
-- This table mirrors BigQuery player_cumulative_points for sub-100ms queries.
-- Synced from BigQuery after each algorithm run.
--
-- Run this in Supabase SQL Editor to create the table.
-- ============================================================

-- Drop existing table if recreating
-- DROP TABLE IF EXISTS player_rankings;

-- Create the player_rankings table
CREATE TABLE IF NOT EXISTS player_rankings (
    -- Primary key
    player_id INTEGER PRIMARY KEY,

    -- Basic info
    player_name TEXT NOT NULL,
    position VARCHAR(2) NOT NULL,  -- F, D, G
    birth_year INTEGER NOT NULL,
    nationality_name TEXT,
    current_team TEXT,
    current_league TEXT,
    team_country TEXT,
    current_season TEXT,

    -- Points (main ranking factors)
    total_points NUMERIC(10,2) DEFAULT 0,
    performance_total NUMERIC(10,2) DEFAULT 0,
    direct_load_total NUMERIC(10,2) DEFAULT 0,

    -- All factor columns (f01-f28)
    f01_views NUMERIC(10,2) DEFAULT 0,
    f02_height NUMERIC(10,2) DEFAULT 0,
    f03_current_goals_f NUMERIC(10,2) DEFAULT 0,
    f04_current_goals_d NUMERIC(10,2) DEFAULT 0,
    f05_current_assists NUMERIC(10,2) DEFAULT 0,
    f06_current_gaa NUMERIC(10,2) DEFAULT 0,
    f07_current_svp NUMERIC(10,2) DEFAULT 0,
    f08_last_goals_f NUMERIC(10,2) DEFAULT 0,
    f09_last_goals_d NUMERIC(10,2) DEFAULT 0,
    f10_last_assists NUMERIC(10,2) DEFAULT 0,
    f11_last_gaa NUMERIC(10,2) DEFAULT 0,
    f12_last_svp NUMERIC(10,2) DEFAULT 0,
    f13_league_points NUMERIC(10,2) DEFAULT 0,
    f14_team_points NUMERIC(10,2) DEFAULT 0,
    f15_international_points NUMERIC(10,2) DEFAULT 0,
    f16_commitment_points NUMERIC(10,2) DEFAULT 0,
    f17_draft_points NUMERIC(10,2) DEFAULT 0,
    f18_weekly_points_delta NUMERIC(10,2) DEFAULT 0,
    f19_weekly_assists_delta NUMERIC(10,2) DEFAULT 0,
    f20_playing_up_points NUMERIC(10,2) DEFAULT 0,
    f21_tournament_points NUMERIC(10,2) DEFAULT 0,
    f22_manual_points NUMERIC(10,2) DEFAULT 0,
    f23_prodigylikes_points NUMERIC(10,2) DEFAULT 0,
    f24_card_sales_points NUMERIC(10,2) DEFAULT 0,
    f25_weekly_views NUMERIC(10,2) DEFAULT 0,
    f26_weight_points NUMERIC(10,2) DEFAULT 0,
    f27_bmi_points NUMERIC(10,2) DEFAULT 0,
    f28_nhl_scouting_points NUMERIC(10,2) DEFAULT 0,

    -- Physical measurements (raw values for BMI tool)
    height_cm INTEGER,
    weight_kg INTEGER,

    -- NHL Central Scouting (only populated for ~400 players on their lists)
    nhl_scouting_rank INTEGER,         -- Rank on Central Scouting list
    nhl_scouting_list TEXT,            -- NA_SKATERS, NA_GOALIES, INTL_SKATERS, INTL_GOALIES

    -- Rating columns (0-99 scale, EA Sports style)
    overall_rating INTEGER DEFAULT 0,
    performance_rating INTEGER DEFAULT 0,
    level_rating INTEGER DEFAULT 0,
    visibility_rating INTEGER DEFAULT 0,
    achievements_rating INTEGER DEFAULT 0,
    trending_rating INTEGER DEFAULT 0,
    physical_rating INTEGER DEFAULT 0,
    -- Compact rating aliases
    perf INTEGER DEFAULT 0,
    lvl INTEGER DEFAULT 0,
    vis INTEGER DEFAULT 0,
    ach INTEGER DEFAULT 0,
    trd INTEGER DEFAULT 0,
    phy INTEGER DEFAULT 0,

    -- Percentile columns (0-100 scale)
    performance_percentile NUMERIC(5,2) DEFAULT 0,
    level_percentile NUMERIC(5,2) DEFAULT 0,
    visibility_percentile NUMERIC(5,2) DEFAULT 0,
    achievements_percentile NUMERIC(5,2) DEFAULT 0,
    physical_percentile NUMERIC(5,2) DEFAULT 0,
    trending_percentile NUMERIC(5,2) DEFAULT 0,
    overall_percentile NUMERIC(5,2) DEFAULT 0,

    -- Pre-computed ranks (computed in BigQuery during sync for performance)
    world_rank INTEGER,       -- Rank within birth_year + position
    country_rank INTEGER,     -- Rank within birth_year + position + nationality

    -- Metadata
    calculated_at TIMESTAMP,
    algorithm_version TEXT,
    synced_at TIMESTAMP DEFAULT NOW(),

    -- Timestamps
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- INDEXES for fast queries
-- ============================================================

-- Fast lookup by player_id (already covered by PRIMARY KEY)

-- Rankings queries (birth_year + position + total_points)
CREATE INDEX IF NOT EXISTS idx_rankings_lookup
ON player_rankings (birth_year, position, total_points DESC);

-- Country-specific rankings
CREATE INDEX IF NOT EXISTS idx_rankings_country
ON player_rankings (birth_year, position, nationality_name, total_points DESC);

-- Search by name (case-insensitive)
CREATE INDEX IF NOT EXISTS idx_player_name_search
ON player_rankings (LOWER(player_name));

-- Sync status
CREATE INDEX IF NOT EXISTS idx_synced_at
ON player_rankings (synced_at DESC);

-- Pre-computed ranks for fast rank-based queries
CREATE INDEX IF NOT EXISTS idx_world_rank
ON player_rankings (birth_year, position, world_rank);

CREATE INDEX IF NOT EXISTS idx_country_rank
ON player_rankings (birth_year, position, nationality_name, country_rank);

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

-- Enable RLS
ALTER TABLE player_rankings ENABLE ROW LEVEL SECURITY;

-- Allow public read access (no auth required for viewing rankings)
CREATE POLICY "Allow public read access" ON player_rankings
    FOR SELECT
    USING (true);

-- Only service role can insert/update (sync script)
CREATE POLICY "Service role can insert" ON player_rankings
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Service role can update" ON player_rankings
    FOR UPDATE
    USING (true);

-- ============================================================
-- TRIGGER: Auto-update updated_at timestamp
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_player_rankings_updated_at
    BEFORE UPDATE ON player_rankings
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- HELPER VIEW: Rankings with pre-computed ranks
-- ============================================================
-- NOTE: world_rank and country_rank are now pre-computed in BigQuery during sync
-- for much better query performance (was computing dynamically with ROW_NUMBER)

CREATE OR REPLACE VIEW vw_player_rankings AS
SELECT * FROM player_rankings;

-- ============================================================
-- GRANT PERMISSIONS
-- ============================================================

-- Grant read access to anon and authenticated users
GRANT SELECT ON player_rankings TO anon;
GRANT SELECT ON player_rankings TO authenticated;
GRANT SELECT ON vw_player_rankings TO anon;
GRANT SELECT ON vw_player_rankings TO authenticated;

-- Service role has full access (for sync)
GRANT ALL ON player_rankings TO service_role;

-- ============================================================
-- COMMENTS
-- ============================================================

COMMENT ON TABLE player_rankings IS 'Player rankings synced from BigQuery for fast API lookups';
COMMENT ON COLUMN player_rankings.player_id IS 'Unique player ID (matches BigQuery)';
COMMENT ON COLUMN player_rankings.total_points IS 'Total algorithm points (used for ranking)';
COMMENT ON COLUMN player_rankings.synced_at IS 'When this record was last synced from BigQuery';

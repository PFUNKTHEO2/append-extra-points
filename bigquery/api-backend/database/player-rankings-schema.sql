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

    -- Points (main ranking factors)
    total_points NUMERIC(10,2) DEFAULT 0,
    performance_total NUMERIC(10,2) DEFAULT 0,
    direct_load_total NUMERIC(10,2) DEFAULT 0,

    -- Key factors for display
    f01_views NUMERIC(10,2) DEFAULT 0,
    f02_height NUMERIC(10,2) DEFAULT 0,
    f13_league_points NUMERIC(10,2) DEFAULT 0,
    f14_team_points NUMERIC(10,2) DEFAULT 0,
    f15_international_points NUMERIC(10,2) DEFAULT 0,
    f16_commitment_points NUMERIC(10,2) DEFAULT 0,
    f17_draft_points NUMERIC(10,2) DEFAULT 0,
    f22_manual_points NUMERIC(10,2) DEFAULT 0,

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
-- HELPER VIEW: Rankings with computed rank
-- ============================================================

CREATE OR REPLACE VIEW vw_player_rankings AS
SELECT
    *,
    ROW_NUMBER() OVER (
        PARTITION BY birth_year, position
        ORDER BY total_points DESC
    ) as world_rank,
    ROW_NUMBER() OVER (
        PARTITION BY birth_year, position, nationality_name
        ORDER BY total_points DESC
    ) as country_rank
FROM player_rankings;

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

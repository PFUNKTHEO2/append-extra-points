#!/usr/bin/env python3
"""
Import NeutralZone NEPSAC rosters as the definitive source of truth.
Uses SQL-based matching for speed.
"""

import csv
from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

# Team name mapping from CSV to BigQuery team_id
TEAM_MAP = {
    'Albany Academy': 'albany-academy',
    'Andover': 'andover',
    'Austin Prep': 'austin-prep',
    'Avon Old Farms': 'avon-old-farms',
    'BB&N': 'bb-n',
    'Belmont Hill': 'belmont-hill',
    'Berkshire School': 'berkshire',
    'Berwick': 'berwick',
    'Brewster': 'brewster',
    'Brooks School': 'brooks-school',
    'Brunswick': 'brunswick',
    'Canterbury': 'canterbury',
    'Choate Rosemary Hall': 'choate',
    'Cushing Academy': 'cushing',
    'Deerfield Academy': 'deerfield',
    'Dexter': 'dexter',
    'Exeter': 'exeter',
    'Frederick Gunn': 'frederick-gunn',
    'Governors Academy': 'governors-academy',
    'Groton': 'groton',
    'Hebron': 'hebron',
    'Holderness': 'holderness',
    'Hoosac': 'hoosac',
    'Hotchkiss School': 'hotchkiss-school',
    'Kent School': 'kent-school',
    'Kents Hill': 'kents-hill',
    'Kimball Union': 'kimball-union',
    'Lawrence Academy': 'lawrence-academy',
    'Lawrenceville School': 'lawrenceville-school',
    'Loomis Chaffee': 'loomis-chaffee',
    'Middlesex': 'middlesex',
    'Millbrook': 'millbrook',
    'Milton Academy': 'milton-academy',
    'New Hampton': 'new-hampton',
    'NMH': 'nmh',
    'Noble & Greenough': 'noble-greenough',
    'North Yarmouth': 'north-yarmouth',
    'Pingree': 'pingree',
    'Pomfret': 'pomfret',
    'Proctor Academy': 'proctor-academy',
    'Rivers School': 'rivers-school',
    'Roxbury Latin': 'roxbury-latin',
    'Salisbury School': 'salisbury-school',
    'St. Georges': 'st-georges',
    'St. Marks': 'st-marks',
    "St. Paul's School": 'st-paul-s-school',
    "St. Sebastian's": 'st-sebastian-s',
    'Tabor': 'tabor',
    'Taft': 'taft',
    'Thayer Academy': 'thayer-academy',
    'Tilton': 'tilton',
    'Vermont Academy': 'vermont-academy',
    'Westminster': 'westminster',
    'Wilbraham & Monson': 'wilbraham-monson',
    'Williston-Northampton': 'williston-northampton',
    'Winchendon': 'winchendon',
    'Worcester Academy': 'worcester-academy',
}

def load_csv(filepath):
    """Load and deduplicate the NeutralZone CSV."""
    rows = []
    seen = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['team'] == 'team':
                continue

            team = row['team']
            player_name = row['player_name']
            if not player_name:
                continue

            key = (team, player_name)
            # Keep row with more data
            if key not in seen or (row.get('gp') and not seen[key].get('gp')):
                seen[key] = row

    return list(seen.values())

def create_staging_table(rows):
    """Create and populate staging table."""
    print("Creating staging table...")

    # Drop if exists
    client.query("DROP TABLE IF EXISTS `prodigy-ranking.algorithm_core.nepsac_staging`").result()

    # Create table
    create_query = '''
    CREATE TABLE `prodigy-ranking.algorithm_core.nepsac_staging` (
        team_name STRING,
        team_id STRING,
        player_name STRING,
        first_name STRING,
        last_name STRING,
        jersey_number INT64,
        position STRING,
        height STRING,
        weight FLOAT64,
        shot STRING,
        grad_year INT64,
        hometown STRING,
        nz_rank INT64,
        gp INT64,
        goals INT64,
        assists INT64,
        points INT64,
        ppg FLOAT64
    )
    '''
    client.query(create_query).result()

    # Prepare rows
    staging_rows = []
    for row in rows:
        team_name = row['team']
        team_id = TEAM_MAP.get(team_name)
        if not team_id:
            continue

        def safe_int(val):
            try:
                return int(float(val)) if val else None
            except:
                return None

        def safe_float(val):
            try:
                return float(val) if val else None
            except:
                return None

        staging_rows.append({
            'team_name': team_name,
            'team_id': team_id,
            'player_name': row['player_name'],
            'first_name': row.get('first_name', ''),
            'last_name': row.get('last_name', ''),
            'jersey_number': safe_int(row.get('jersey_number')),
            'position': row.get('position', ''),
            'height': row.get('height', ''),
            'weight': safe_float(row.get('weight')),
            'shot': row.get('shot', ''),
            'grad_year': safe_int(row.get('grad_year')),
            'hometown': row.get('hometown', ''),
            'nz_rank': safe_int(row.get('rank')),
            'gp': safe_int(row.get('gp')),
            'goals': safe_int(row.get('goals')),
            'assists': safe_int(row.get('assists')),
            'points': safe_int(row.get('points')),
            'ppg': safe_float(row.get('ppg')),
        })

    # Insert in batches
    print(f"Inserting {len(staging_rows)} rows into staging...")
    table_id = 'prodigy-ranking.algorithm_core.nepsac_staging'
    batch_size = 500
    for i in range(0, len(staging_rows), batch_size):
        batch = staging_rows[i:i+batch_size]
        errors = client.insert_rows_json(table_id, batch)
        if errors:
            print(f"Batch {i//batch_size + 1} errors: {errors[:2]}")

    print("Staging table populated!")
    return len(staging_rows)

def run_sql_matching():
    """Use SQL to match players to Elite Prospects IDs."""
    print("\nRunning SQL-based fuzzy matching...")

    # Match using exact name match first, then normalized name match
    match_query = '''
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_matched` AS
    WITH exact_matches AS (
        -- Exact name matches
        SELECT
            s.*,
            p.player_id,
            'exact' as match_type,
            1.0 as match_confidence
        FROM `prodigy-ranking.algorithm_core.nepsac_staging` s
        JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` p
            ON LOWER(TRIM(s.player_name)) = LOWER(TRIM(p.player_name))
    ),
    normalized_matches AS (
        -- Normalized name matches (remove special chars)
        SELECT
            s.*,
            p.player_id,
            'normalized' as match_type,
            0.95 as match_confidence
        FROM `prodigy-ranking.algorithm_core.nepsac_staging` s
        JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` p
            ON REGEXP_REPLACE(LOWER(s.player_name), r'[^a-z ]', '') =
               REGEXP_REPLACE(LOWER(p.player_name), r'[^a-z ]', '')
        WHERE NOT EXISTS (
            SELECT 1 FROM exact_matches e
            WHERE e.team_id = s.team_id AND e.player_name = s.player_name
        )
    ),
    first_last_matches AS (
        -- Match by first_name + last_name
        SELECT
            s.*,
            p.player_id,
            'first_last' as match_type,
            0.9 as match_confidence
        FROM `prodigy-ranking.algorithm_core.nepsac_staging` s
        JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` p
            ON LOWER(TRIM(CONCAT(s.first_name, ' ', s.last_name))) = LOWER(TRIM(p.player_name))
        WHERE s.first_name IS NOT NULL AND s.first_name != ''
            AND NOT EXISTS (
                SELECT 1 FROM exact_matches e
                WHERE e.team_id = s.team_id AND e.player_name = s.player_name
            )
            AND NOT EXISTS (
                SELECT 1 FROM normalized_matches n
                WHERE n.team_id = s.team_id AND n.player_name = s.player_name
            )
    ),
    unmatched AS (
        -- Unmatched players
        SELECT
            s.*,
            CAST(NULL AS INT64) as player_id,
            'unmatched' as match_type,
            CAST(NULL AS FLOAT64) as match_confidence
        FROM `prodigy-ranking.algorithm_core.nepsac_staging` s
        WHERE NOT EXISTS (
            SELECT 1 FROM exact_matches e
            WHERE e.team_id = s.team_id AND e.player_name = s.player_name
        )
        AND NOT EXISTS (
            SELECT 1 FROM normalized_matches n
            WHERE n.team_id = s.team_id AND n.player_name = s.player_name
        )
        AND NOT EXISTS (
            SELECT 1 FROM first_last_matches f
            WHERE f.team_id = s.team_id AND f.player_name = s.player_name
        )
    )
    SELECT * FROM exact_matches
    UNION ALL
    SELECT * FROM normalized_matches
    UNION ALL
    SELECT * FROM first_last_matches
    UNION ALL
    SELECT * FROM unmatched
    '''
    client.query(match_query).result()
    print("Matching complete!")

    # Show match stats
    stats_query = '''
    SELECT
        match_type,
        COUNT(*) as count
    FROM `prodigy-ranking.algorithm_core.nepsac_matched`
    GROUP BY match_type
    ORDER BY count DESC
    '''
    print("\n=== MATCH STATISTICS ===")
    for row in client.query(stats_query).result():
        print(f"  {row.match_type}: {row.count}")

def populate_final_tables():
    """Populate the final roster and stats tables."""
    print("\nPopulating final tables...")

    # Clear and populate nepsac_rosters
    print("Updating nepsac_rosters...")
    client.query("TRUNCATE TABLE `prodigy-ranking.algorithm_core.nepsac_rosters`").result()

    roster_query = '''
    INSERT INTO `prodigy-ranking.algorithm_core.nepsac_rosters`
        (team_id, player_id, roster_name, position, grad_year, jersey_number, season, is_active, match_confidence)
    SELECT
        team_id,
        CAST(player_id AS FLOAT64),
        player_name,
        position,
        CAST(grad_year AS FLOAT64),
        CAST(jersey_number AS STRING),
        '2025-26',
        TRUE,
        match_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_matched`
    '''
    client.query(roster_query).result()

    # Create and populate nepsac_player_stats
    print("Creating nepsac_player_stats table...")
    create_stats_query = '''
    CREATE TABLE IF NOT EXISTS `prodigy-ranking.algorithm_core.nepsac_player_stats` (
        team_id STRING,
        player_id INT64,
        player_name STRING,
        position STRING,
        season STRING,
        gp INT64,
        goals INT64,
        assists INT64,
        points INT64,
        ppg FLOAT64,
        nz_rank INT64,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
    )
    '''
    client.query(create_stats_query).result()

    print("Populating nepsac_player_stats...")
    client.query("DELETE FROM `prodigy-ranking.algorithm_core.nepsac_player_stats` WHERE season = '2025-26'").result()

    stats_insert_query = '''
    INSERT INTO `prodigy-ranking.algorithm_core.nepsac_player_stats`
        (team_id, player_id, player_name, position, season, gp, goals, assists, points, ppg, nz_rank)
    SELECT
        team_id,
        CAST(player_id AS INT64),
        player_name,
        position,
        '2025-26',
        gp,
        goals,
        assists,
        points,
        ppg,
        nz_rank
    FROM `prodigy-ranking.algorithm_core.nepsac_matched`
    WHERE gp IS NOT NULL
    '''
    client.query(stats_insert_query).result()

    print("Final tables populated!")

def cleanup():
    """Clean up temporary tables."""
    print("\nCleaning up...")
    client.query("DROP TABLE IF EXISTS `prodigy-ranking.algorithm_core.nepsac_staging`").result()
    client.query("DROP TABLE IF EXISTS `prodigy-ranking.algorithm_core.nepsac_matched`").result()
    print("Cleanup complete!")

def verify():
    """Verify the import."""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)

    # Roster counts
    roster_query = '''
    SELECT team_id, COUNT(*) as count
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
    GROUP BY team_id
    ORDER BY team_id
    '''
    print("\n=== ROSTER COUNTS BY TEAM ===")
    total = 0
    for row in client.query(roster_query).result():
        print(f"  {row.team_id}: {row.count}")
        total += row.count
    print(f"\nTotal players: {total}")

    # Match rate
    match_query = '''
    SELECT
        COUNT(*) as total,
        COUNTIF(player_id IS NOT NULL) as matched,
        ROUND(COUNTIF(player_id IS NOT NULL) / COUNT(*) * 100, 1) as match_pct
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
    '''
    result = list(client.query(match_query).result())[0]
    print(f"\n=== ELITE PROSPECTS ID MATCH RATE ===")
    print(f"  Total: {result.total}")
    print(f"  Matched: {result.matched} ({result.match_pct}%)")

    # Stats counts
    stats_query = '''
    SELECT COUNT(*) as count, SUM(goals) as total_goals, SUM(points) as total_points
    FROM `prodigy-ranking.algorithm_core.nepsac_player_stats`
    WHERE season = '2025-26'
    '''
    result2 = list(client.query(stats_query).result())[0]
    print(f"\n=== STATS SUMMARY ===")
    print(f"  Players with stats: {result2.count}")
    print(f"  Total goals: {result2.total_goals}")
    print(f"  Total points: {result2.total_points}")

    # Sample unmatched
    unmatched_query = '''
    SELECT roster_name, team_id
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26' AND player_id IS NULL
    LIMIT 10
    '''
    print(f"\n=== SAMPLE UNMATCHED PLAYERS ===")
    for row in client.query(unmatched_query).result():
        print(f"  {row.roster_name} ({row.team_id})")

if __name__ == '__main__':
    import sys

    csv_path = 'neutralzone_prep_boys_hockey_data_clean.csv'

    print("="*60)
    print("NEPSAC ROSTER IMPORT FROM NEUTRALZONE")
    print("="*60)

    # Load CSV
    print(f"\nLoading {csv_path}...")
    rows = load_csv(csv_path)
    print(f"Loaded {len(rows)} unique players")

    if '--apply' not in sys.argv:
        print("\n" + "="*60)
        print("DRY RUN - Run with --apply to execute")
        print("="*60)

        # Show sample
        print("\nSample data:")
        for r in rows[:5]:
            print(f"  {r['player_name']} ({r['team']}): GP={r.get('gp')}, G={r.get('goals')}, A={r.get('assists')}")
        exit(0)

    # Execute import
    create_staging_table(rows)
    run_sql_matching()
    populate_final_tables()
    cleanup()
    verify()

    print("\n" + "="*60)
    print("IMPORT COMPLETE!")
    print("="*60)

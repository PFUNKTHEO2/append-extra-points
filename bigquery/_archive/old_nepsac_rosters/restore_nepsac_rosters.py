#!/usr/bin/env python3
"""
Restore NEPSAC rosters from the original CSV file.
This will clear the nepsac_rosters table and re-import from the CSV,
ensuring each player is only on ONE team.
"""

import csv
from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

# Team name mapping from CSV to BigQuery team_id
TEAM_MAP = {
    'Andover': 'andover',
    'Albany Academy': 'albany-academy',
    'Austin Prep': 'austin-prep',
    'Avon Old Farms': 'avon-old-farms',
    'BB&N': 'bb-n',
    'Belmont Hill': 'belmont-hill',
    'Berkshire': 'berkshire',
    'Berwick': 'berwick',
    'Brewster': 'brewster',
    'Brooks': 'brooks-school',
    'Brooks School': 'brooks-school',
    'Brunswick': 'brunswick',
    'Canterbury': 'canterbury',
    'Choate': 'choate',
    'Cushing': 'cushing',
    'Deerfield': 'deerfield',
    'Dexter': 'dexter',
    'Exeter': 'exeter',
    'Frederick Gunn': 'frederick-gunn',
    "Governor's Academy": 'governors-academy',
    'Governors Academy': 'governors-academy',
    'Groton': 'groton',
    'Hebron': 'hebron',
    'Holderness': 'holderness',
    'Hotchkiss': 'hotchkiss-school',
    'Hotchkiss School': 'hotchkiss-school',
    'Kent': 'kent-school',
    'Kent School': 'kent-school',
    'Kents Hill': 'kents-hill',
    'Kimball Union': 'kimball-union',
    'Lawrence': 'lawrence-academy',
    'Lawrence Academy': 'lawrence-academy',
    'Lawrenceville': 'lawrenceville-school',
    'Lawrenceville School': 'lawrenceville-school',
    'Loomis': 'loomis-chaffee',
    'Loomis Chaffee': 'loomis-chaffee',
    'Middlesex': 'middlesex',
    'Millbrook': 'millbrook',
    'Milton': 'milton-academy',
    'Milton Academy': 'milton-academy',
    'Mount St. Charles': 'mount-st-charles',
    'New Hampton': 'new-hampton',
    'NMH': 'nmh',
    'Nobles': 'noble-greenough',
    'Noble & Greenough': 'noble-greenough',
    'North Yarmouth': 'north-yarmouth',
    'Pingree': 'pingree',
    'Pomfret': 'pomfret',
    'Portsmouth Abbey': 'portsmouth-abbey',
    'Proctor': 'proctor-academy',
    'Proctor Academy': 'proctor-academy',
    'Rivers': 'rivers-school',
    'Rivers School': 'rivers-school',
    'Salisbury': 'salisbury-school',
    'Salisbury School': 'salisbury-school',
    'Shattuck-St. Mary\'s': 'shattuck-st-mary-s',
    'St. George\'s': 'st-georges',
    'St. Georges': 'st-georges',
    "St. Mark's": 'st-marks',
    'St. Marks': 'st-marks',
    "St. Paul's": 'st-paul-s-school',
    "St. Paul's School": 'st-paul-s-school',
    "St. Sebastian's": 'st-sebastian-s',
    'Tabor': 'tabor',
    'Taft': 'taft',
    'Thayer': 'thayer-academy',
    'Thayer Academy': 'thayer-academy',
    'The Hill School': 'the-hill-school',
    'Tilton': 'tilton',
    'Vermont Academy': 'vermont-academy',
    'Westminster': 'westminster',
    'Wilbraham & Monson': 'wilbraham-monson',
    'Williston': 'williston-northampton',
    'Williston-Northampton': 'williston-northampton',
    'Winchendon': 'winchendon',
    'Worcester': 'worcester-academy',
    'Worcester Academy': 'worcester-academy',
}

def load_player_mapping():
    """Load player name to ID mapping from existing data."""
    query = '''
    SELECT player_id, player_name
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    WHERE player_name IS NOT NULL
    '''
    mapping = {}
    for row in client.query(query).result():
        # Normalize name for matching
        name_normalized = row.player_name.lower().strip()
        mapping[name_normalized] = row.player_id
    print(f"Loaded {len(mapping)} player name -> ID mappings")
    return mapping

def load_existing_roster_mapping():
    """Load existing roster player_id to team mapping."""
    query = '''
    SELECT DISTINCT
        CAST(player_id AS INT64) as player_id,
        team_id,
        roster_name
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
      AND player_id IS NOT NULL
    '''
    mapping = {}
    for row in client.query(query).result():
        if row.player_id not in mapping:
            mapping[row.player_id] = {
                'team_id': row.team_id,
                'name': row.roster_name
            }
    print(f"Loaded {len(mapping)} existing roster mappings")
    return mapping

def clear_current_season_rosters():
    """Clear current season rosters."""
    query = '''
    DELETE FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
    '''
    print("Clearing current season rosters...")
    client.query(query).result()
    print("Cleared!")

def import_from_csv(csv_path, player_mapping, existing_roster):
    """Import rosters from CSV file."""
    rows_to_insert = []

    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row['team']
            team_id = TEAM_MAP.get(team_name)
            if not team_id:
                print(f"WARNING: Unknown team '{team_name}', skipping")
                continue

            player_name = row['name']
            if not player_name:
                continue

            # Try to find player_id
            name_normalized = player_name.lower().strip()
            player_id = player_mapping.get(name_normalized)

            # Parse other fields
            try:
                jersey_number = int(row['number']) if row.get('number') else None
            except ValueError:
                jersey_number = None

            position = row.get('position', '')
            height = row.get('height', '')
            weight = row.get('weight', '')
            shot = row.get('shot', '')
            grad_year = row.get('grad_year', '')
            hometown = row.get('hometown', '')
            dob = row.get('dob', '')

            roster_row = {
                'team_id': team_id,
                'player_id': float(player_id) if player_id else None,
                'roster_name': player_name,
                'jersey_number': str(jersey_number) if jersey_number else None,
                'position': position,
                'season': '2025-26',
                'is_active': True,
            }
            rows_to_insert.append(roster_row)

    print(f"\nPrepared {len(rows_to_insert)} roster entries to insert")
    return rows_to_insert

def insert_rosters(rows):
    """Insert roster rows into BigQuery."""
    if not rows:
        print("No rows to insert!")
        return

    table_id = 'prodigy-ranking.algorithm_core.nepsac_rosters'

    # Insert in batches
    batch_size = 500
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        errors = client.insert_rows_json(table_id, batch)
        if errors:
            print(f"Batch {i//batch_size + 1} errors: {errors[:3]}...")
        else:
            print(f"Inserted batch {i//batch_size + 1} ({len(batch)} rows)")

def verify_import():
    """Verify the import worked."""
    query = '''
    SELECT
        team_id,
        COUNT(*) as player_count
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
    GROUP BY team_id
    ORDER BY team_id
    '''
    print("\n=== ROSTER COUNTS AFTER IMPORT ===")
    total = 0
    for row in client.query(query).result():
        print(f"{row.team_id}: {row.player_count}")
        total += row.player_count
    print(f"\nTotal: {total} players across all teams")

    # Check for duplicates
    dup_query = '''
    SELECT COUNT(*) as dup_count
    FROM (
        SELECT roster_name
        FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
        WHERE season = '2025-26'
        GROUP BY roster_name
        HAVING COUNT(DISTINCT team_id) > 1
    )
    '''
    result = list(client.query(dup_query).result())[0]
    print(f"\nPlayers on multiple teams: {result.dup_count}")

if __name__ == '__main__':
    import sys

    csv_path = 'nepsac_all_rosters_combined.csv'

    if '--apply' not in sys.argv:
        print("DRY RUN - No changes will be made")
        print("Run with --apply to execute the import")
        print(f"\nWill import from: {csv_path}")

        # Just count rows
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            teams = {}
            for row in reader:
                team = row['team']
                teams[team] = teams.get(team, 0) + 1

        print(f"\nTeams in CSV ({len(teams)} total):")
        for team, count in sorted(teams.items()):
            team_id = TEAM_MAP.get(team, '???')
            print(f"  {team} ({team_id}): {count} players")
        exit(0)

    # Load mappings
    player_mapping = load_player_mapping()
    existing_roster = load_existing_roster_mapping()

    # Clear current rosters
    clear_current_season_rosters()

    # Import from CSV
    rows = import_from_csv(csv_path, player_mapping, existing_roster)

    # Insert
    insert_rosters(rows)

    # Verify
    verify_import()

    print("\nDone!")

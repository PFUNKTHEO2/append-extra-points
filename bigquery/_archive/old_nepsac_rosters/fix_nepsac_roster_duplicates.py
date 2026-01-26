#!/usr/bin/env python3
"""
Fix NEPSAC Roster Duplicates

Problem: Some players are assigned to multiple teams in nepsac_rosters table.
Solution: Use player_cumulative_points.current_team as source of truth.
"""

from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

def find_duplicate_players():
    """Find players assigned to multiple teams."""
    query = '''
    SELECT
        CAST(player_id AS INT64) as player_id,
        ARRAY_AGG(DISTINCT team_id) as teams,
        COUNT(DISTINCT team_id) as team_count
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
      AND player_id IS NOT NULL
    GROUP BY player_id
    HAVING COUNT(DISTINCT team_id) > 1
    ORDER BY team_count DESC
    '''
    results = list(client.query(query).result())
    print(f"\n=== PLAYERS ON MULTIPLE TEAMS: {len(results)} ===\n")

    duplicates = []
    for row in results:
        print(f"Player {row.player_id}: {row.team_count} teams - {list(row.teams)}")
        duplicates.append({
            'player_id': int(row.player_id),
            'teams': list(row.teams)
        })

    return duplicates

def get_correct_teams(player_ids):
    """Get correct team from player_cumulative_points."""
    if not player_ids:
        return {}

    player_list = ', '.join([str(p) for p in player_ids])
    query = f'''
    SELECT
        player_id,
        current_team,
        player_name
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    WHERE player_id IN ({player_list})
    '''

    correct_teams = {}
    for row in client.query(query).result():
        correct_teams[row.player_id] = {
            'team': row.current_team,
            'name': row.player_name
        }

    return correct_teams

def map_team_name_to_id(team_name):
    """Map full team name to nepsac_rosters team_id format."""
    if not team_name:
        return None

    # Common mappings
    mappings = {
        'Deerfield Academy': 'deerfield',
        'Westminster School': 'westminster',
        'Kimball Union Academy': 'kimball-union',
        'Kents Hill School': 'kents-hill',
        'North Yarmouth Academy': 'north-yarmouth',
        'Canterbury School': 'canterbury',
        'Worcester Academy': 'worcester-academy',
        'Avon Old Farms': 'avon-old-farms',
        'Salisbury School': 'salisbury-school',
        'Cushing Academy': 'cushing-academy',
        'NMH': 'nmh',
        'Northfield Mount Hermon': 'nmh',
        'Proctor Academy': 'proctor-academy',
        'New Hampton School': 'new-hampton',
        'Brewster Academy': 'brewster',
        'Holderness School': 'holderness',
        'Vermont Academy': 'vermont-academy',
        'Tilton School': 'tilton',
        'Phillips Exeter Academy': 'exeter',
        'Phillips Academy Andover': 'andover',
        'Belmont Hill School': 'belmont-hill',
        'Brooks School': 'brooks-school',
        'Groton School': 'groton',
        'Loomis Chaffee': 'loomis-chaffee',
        'Taft School': 'taft',
        'Choate Rosemary Hall': 'choate',
        'Kent School': 'kent-school',
        'Hotchkiss School': 'hotchkiss-school',
        'Berkshire School': 'berkshire',
        'Millbrook School': 'millbrook',
        "St. George's School": 'st-georges',
        "St. Mark's School": 'st-marks',
        "St. Paul's School": 'st-paul-s-school',
        "St. Sebastian's School": 'st-sebastian-s',
        'Tabor Academy': 'tabor',
        'Thayer Academy': 'thayer-academy',
        'Nobles': 'noble-greenough',
        'Noble and Greenough School': 'noble-greenough',
        'Milton Academy': 'milton-academy',
        'BB&N': 'bb-n',
        'Buckingham Browne & Nichols': 'bb-n',
        'Middlesex School': 'middlesex',
        'Rivers School': 'rivers-school',
        'Lawrence Academy': 'lawrence-academy',
        "Governor's Academy": 'governors-academy',
        'Pomfret School': 'pomfret',
        'Frederick Gunn School': 'frederick-gunn',
        'Trinity-Pawling School': 'trinity-pawling',
        'Williston Northampton': 'williston-northampton',
        'Pingree School': 'pingree',
        'Berwick Academy': 'berwick',
        'Hebron Academy': 'hebron',
        'Winchendon School': 'winchendon',
        'Hoosac School': 'hoosac',
        'Portsmouth Abbey': 'portsmouth-abbey',
        'Austin Prep': 'austin-prep',
        'Roxbury Latin': 'roxbury-latin',
    }

    # Direct lookup
    if team_name in mappings:
        return mappings[team_name]

    # Try lowercase slug conversion
    slug = team_name.lower().replace(' ', '-').replace("'", '').replace('.', '')
    return slug

def fix_duplicates(duplicates, correct_teams, dry_run=True):
    """Remove incorrect team assignments."""

    print(f"\n=== {'DRY RUN - ' if dry_run else ''}FIXING DUPLICATES ===\n")

    fixes = []
    unfixable = []

    for dup in duplicates:
        player_id = dup['player_id']
        current_teams = dup['teams']

        if player_id not in correct_teams:
            print(f"WARNING: Player {player_id} not found in player_cumulative_points")
            unfixable.append(player_id)
            continue

        correct_team_name = correct_teams[player_id]['team']
        player_name = correct_teams[player_id]['name']
        correct_team_id = map_team_name_to_id(correct_team_name)

        if not correct_team_id:
            print(f"WARNING: Cannot map team '{correct_team_name}' for {player_name} ({player_id})")
            unfixable.append(player_id)
            continue

        # Determine which teams to remove
        teams_to_remove = [t for t in current_teams if t != correct_team_id]

        if not teams_to_remove:
            # Maybe the correct team uses a different format
            print(f"INFO: Player {player_name} ({player_id}) - correct team '{correct_team_id}' not in {current_teams}")
            # Try to find a match
            for t in current_teams:
                if correct_team_id in t or t in correct_team_id:
                    teams_to_remove = [x for x in current_teams if x != t]
                    correct_team_id = t
                    break

        if teams_to_remove:
            print(f"Player {player_name} ({player_id}):")
            print(f"  Correct team: {correct_team_id} (from: {correct_team_name})")
            print(f"  Remove from: {teams_to_remove}")

            fixes.append({
                'player_id': player_id,
                'player_name': player_name,
                'keep_team': correct_team_id,
                'remove_teams': teams_to_remove
            })

    print(f"\n=== SUMMARY ===")
    print(f"Players to fix: {len(fixes)}")
    print(f"Unfixable: {len(unfixable)}")

    if not dry_run and fixes:
        print("\n=== EXECUTING DELETES ===\n")
        for fix in fixes:
            for team in fix['remove_teams']:
                delete_query = f'''
                DELETE FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
                WHERE player_id = {fix['player_id']}
                AND team_id = '{team}'
                AND season = '2025-26'
                '''
                print(f"Deleting {fix['player_name']} from {team}...")
                client.query(delete_query).result()

        print(f"\nDeleted {sum(len(f['remove_teams']) for f in fixes)} incorrect roster entries")

    return fixes, unfixable

def verify_fix():
    """Verify no more duplicates exist."""
    query = '''
    SELECT COUNT(*) as dup_count
    FROM (
        SELECT player_id
        FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
        WHERE season = '2025-26'
        GROUP BY player_id
        HAVING COUNT(DISTINCT team_id) > 1
    )
    '''
    result = list(client.query(query).result())[0]
    print(f"\n=== VERIFICATION ===")
    print(f"Players still on multiple teams: {result.dup_count}")
    return result.dup_count == 0

if __name__ == '__main__':
    import sys

    dry_run = '--apply' not in sys.argv

    # Step 1: Find duplicates
    duplicates = find_duplicate_players()

    if not duplicates:
        print("\nNo duplicates found!")
        exit(0)

    # Step 2: Get correct teams
    player_ids = [d['player_id'] for d in duplicates]
    correct_teams = get_correct_teams(player_ids)

    print(f"\n=== CORRECT TEAMS FROM player_cumulative_points ===\n")
    for pid, info in correct_teams.items():
        print(f"  {info['name']} ({pid}): {info['team']}")

    # Step 3: Fix duplicates
    fixes, unfixable = fix_duplicates(duplicates, correct_teams, dry_run=dry_run)

    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN COMPLETE - No changes made")
        print("Run with --apply to execute the fixes")
        print("="*60)
    else:
        # Verify
        verify_fix()

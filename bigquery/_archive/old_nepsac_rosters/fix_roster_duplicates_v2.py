#!/usr/bin/env python3
"""
Fix NEPSAC roster duplicates v2.

Strategy:
1. Find all players who appear on multiple teams
2. Check their current_team in player_cumulative_points
3. If current_team matches a NEPSAC school, keep only that assignment
4. If current_team doesn't match, keep first alphabetical team (best effort)
"""

from google.cloud import bigquery
from collections import defaultdict

client = bigquery.Client(project='prodigy-ranking')

# Mapping from player_cumulative_points team names to nepsac_rosters team_id
TEAM_NAME_TO_ID = {
    'Deerfield Academy': 'deerfield',
    'Westminster School': 'westminster',
    'Kimball Union Academy': 'kimball-union',
    'Kents Hill School': 'kents-hill',
    'Canterbury School': 'canterbury',
    'Worcester Academy': 'worcester-academy',
    'Choate Rosemary Hall': 'choate',
    "St. George's School": 'st-georges',
    'Groton School': 'groton',
    'Rivers School': 'rivers-school',
    'Hebron Academy': 'hebron',
    'Salisbury School': 'salisbury-school',
    'Brewster Academy': 'brewster',
    'Holderness School': 'holderness',
}

def find_duplicates():
    """Find players on multiple teams by name."""
    query = '''
    SELECT
        roster_name,
        ARRAY_AGG(STRUCT(team_id, player_id)) as entries,
        COUNT(DISTINCT team_id) as team_count
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
      AND roster_name IS NOT NULL
    GROUP BY roster_name
    HAVING COUNT(DISTINCT team_id) > 1
    ORDER BY team_count DESC
    '''
    duplicates = []
    for row in client.query(query).result():
        entries = [{'team_id': e['team_id'], 'player_id': e['player_id']} for e in row.entries]
        duplicates.append({
            'name': row.roster_name,
            'entries': entries,
            'team_count': row.team_count
        })
    return duplicates

def get_correct_teams(player_names):
    """Get correct team from player_cumulative_points."""
    if not player_names:
        return {}

    # Get all players with NEPSAC teams
    query = '''
    SELECT player_name, current_team
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    WHERE current_team IN (
        'Deerfield Academy', 'Westminster School', 'Kimball Union Academy',
        'Kents Hill School', 'Canterbury School', 'Worcester Academy',
        'Choate Rosemary Hall', "St. George's School", 'Groton School',
        'Rivers School', 'Hebron Academy', 'Salisbury School',
        'Brewster Academy', 'Holderness School'
    )
    '''

    correct_teams = {}
    for row in client.query(query).result():
        team_id = TEAM_NAME_TO_ID.get(row.current_team)
        if team_id and row.player_name in player_names:
            correct_teams[row.player_name] = team_id

    return correct_teams

def fix_duplicates(duplicates, correct_teams, dry_run=True):
    """Remove incorrect team assignments."""

    print(f"\n=== {'DRY RUN - ' if dry_run else ''}FIXING DUPLICATES ===\n")

    deletions = []

    for dup in duplicates:
        name = dup['name']
        entries = dup['entries']
        teams = [e['team_id'] for e in entries]

        # Check if we have a correct team
        correct_team = correct_teams.get(name)

        if correct_team and correct_team in teams:
            # Keep correct team, remove others
            teams_to_remove = [t for t in teams if t != correct_team]
            print(f"{name}: Keep {correct_team}, remove from {teams_to_remove}")
        else:
            # No correct team found, keep alphabetically first
            teams_sorted = sorted(teams)
            teams_to_remove = teams_sorted[1:]  # Remove all except first
            print(f"{name}: No match found, keeping {teams_sorted[0]}, remove from {teams_to_remove}")

        for team in teams_to_remove:
            deletions.append({
                'name': name,
                'team': team
            })

    print(f"\n=== SUMMARY ===")
    print(f"Duplicates found: {len(duplicates)}")
    print(f"Entries to delete: {len(deletions)}")

    if not dry_run and deletions:
        print("\n=== EXECUTING DELETES ===\n")
        for d in deletions:
            # Escape single quotes in name
            escaped_name = d['name'].replace("'", "''")
            query = f'''
            DELETE FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
            WHERE roster_name = '{escaped_name}'
              AND team_id = '{d['team']}'
              AND season = '2025-26'
            '''
            client.query(query).result()
            print(f"Deleted {d['name']} from {d['team']}")

        print(f"\nDeleted {len(deletions)} duplicate entries")

    return deletions

def verify_fix():
    """Verify no more duplicates exist."""
    query = '''
    SELECT COUNT(*) as dup_count
    FROM (
        SELECT roster_name
        FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
        WHERE season = '2025-26'
        GROUP BY roster_name
        HAVING COUNT(DISTINCT team_id) > 1
    )
    '''
    result = list(client.query(query).result())[0]
    print(f"\n=== VERIFICATION ===")
    print(f"Players still on multiple teams: {result.dup_count}")
    return result.dup_count == 0

def show_roster_counts():
    """Show roster counts by team."""
    query = '''
    SELECT team_id, COUNT(*) as count
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
    WHERE season = '2025-26'
    GROUP BY team_id
    ORDER BY team_id
    '''
    print("\n=== ROSTER COUNTS ===")
    for row in client.query(query).result():
        print(f"{row.team_id}: {row.count}")

if __name__ == '__main__':
    import sys

    dry_run = '--apply' not in sys.argv

    # Step 1: Find duplicates
    duplicates = find_duplicates()
    print(f"Found {len(duplicates)} players on multiple teams")

    if not duplicates:
        print("No duplicates found!")
        exit(0)

    # Step 2: Get correct teams
    player_names = [d['name'] for d in duplicates]
    correct_teams = get_correct_teams(player_names)
    print(f"Found correct teams for {len(correct_teams)} players")

    # Step 3: Fix duplicates
    deletions = fix_duplicates(duplicates, correct_teams, dry_run=dry_run)

    if dry_run:
        print("\n" + "="*60)
        print("DRY RUN COMPLETE - No changes made")
        print("Run with --apply to execute the fixes")
        print("="*60)
    else:
        verify_fix()
        show_roster_counts()

"""
Sync Prodigy Power Rankings to BigQuery

Updates the nepsac_team_rankings.rank column with our performance-based
power rankings instead of roster-based rankings.

The power rankings prioritize:
- Performance factors (70%): JSPR, NEHJ, Performance ELO, MHR, Win %, Form
- Roster factors (30%): Avg ProdigyPoints, Top Player, Roster Depth

Usage:
    python sync_power_rankings_to_bigquery.py [--dry-run]

Options:
    --dry-run   Show what would be updated without making changes

Created: 2026-01-26
"""

import os
import csv
import json
import sys
from datetime import datetime
from google.cloud import bigquery

# Configuration
PROJECT_ID = 'prodigy-ranking'
DATASET_ID = 'algorithm_core'
TABLE_ID = 'nepsac_team_rankings'
SEASON = '2025-26'

# File paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
POWER_RANKINGS_CSV = os.path.join(BASE_DIR, 'nepsac_power_rankings.csv')
POWER_RANKINGS_JSON = os.path.join(BASE_DIR, 'nepsac_power_rankings.json')

# Team ID mapping (team name -> team_id)
def create_team_id(team_name):
    """Convert team name to URL-friendly team_id"""
    if not team_name:
        return None
    # Lowercase, replace spaces with hyphens, remove special chars
    team_id = team_name.lower().strip()
    team_id = team_id.replace(' ', '-')
    team_id = team_id.replace("'", '')
    team_id = team_id.replace('.', '')
    team_id = team_id.replace('&', 'and')
    return team_id


def load_power_rankings(filepath):
    """Load power rankings from CSV file."""
    rankings = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team_name = row['team'].strip()
            team_id = create_team_id(team_name)

            rankings[team_id] = {
                'team_name': team_name,
                'power_rank': int(row['rank']),
                'power_score': float(row['score']),
                'jspr_rank': row['jspr_rank'],
                'nehj_rank': row['nehj_rank'],
                'perf_rank': row['perf_rank'],
                'mhr_rank': row['mhr_rank'],
                'record': row['record'],
                'win_pct': float(row['win_pct']) if row['win_pct'] else 0,
            }

    return rankings


def get_existing_rankings(client, dry_run=False):
    """Get existing team rankings from BigQuery."""
    query = f"""
    SELECT team_id, rank, avg_prodigy_points, team_ovr
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE season = '{SEASON}'
    """

    if dry_run:
        print(f"\nWould query: {query[:100]}...")
        return {}

    results = client.query(query).result()
    existing = {}
    for row in results:
        existing[row.team_id] = {
            'current_rank': row.rank,
            'avg_points': row.avg_prodigy_points,
            'team_ovr': row.team_ovr,
        }
    return existing


def update_rankings(client, power_rankings, existing_rankings, dry_run=False):
    """Update BigQuery with new power rankings."""
    updates = []

    for team_id, data in power_rankings.items():
        if team_id in existing_rankings:
            old_rank = existing_rankings[team_id]['current_rank']
            new_rank = data['power_rank']

            if old_rank != new_rank:
                updates.append({
                    'team_id': team_id,
                    'team_name': data['team_name'],
                    'old_rank': old_rank,
                    'new_rank': new_rank,
                    'power_score': data['power_score'],
                })

    if not updates:
        print("\nNo ranking changes needed.")
        return

    print(f"\n{'='*60}")
    print(f"RANKING UPDATES ({len(updates)} teams)")
    print(f"{'='*60}")
    print(f"{'Team':<25} {'Old Rank':<10} {'New Rank':<10} {'Change':<10}")
    print(f"{'-'*60}")

    for u in sorted(updates, key=lambda x: x['new_rank']):
        change = u['old_rank'] - u['new_rank'] if u['old_rank'] else 'NEW'
        change_str = f"+{change}" if isinstance(change, int) and change > 0 else str(change)
        print(f"{u['team_name']:<25} {u['old_rank'] or 'NR':<10} {u['new_rank']:<10} {change_str:<10}")

    if dry_run:
        print(f"\n[DRY RUN] Would update {len(updates)} rankings in BigQuery")
        return

    # Execute updates
    print(f"\nUpdating {len(updates)} rankings in BigQuery...")

    for u in updates:
        query = f"""
        UPDATE `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
        SET rank = {u['new_rank']},
            calculated_at = CURRENT_TIMESTAMP()
        WHERE team_id = '{u['team_id']}'
          AND season = '{SEASON}'
        """
        client.query(query).result()

    print(f"Successfully updated {len(updates)} rankings!")


def main():
    dry_run = '--dry-run' in sys.argv

    print("="*60)
    print("PRODIGY POWER RANKINGS SYNC TO BIGQUERY")
    print("="*60)

    if dry_run:
        print("\n[DRY RUN MODE - No changes will be made]")

    # Load power rankings
    print(f"\nLoading power rankings from {POWER_RANKINGS_CSV}...")
    power_rankings = load_power_rankings(POWER_RANKINGS_CSV)
    print(f"  Loaded {len(power_rankings)} teams")

    # Show top 10
    print("\nTop 10 Power Rankings:")
    for team_id, data in sorted(power_rankings.items(), key=lambda x: x[1]['power_rank'])[:10]:
        print(f"  #{data['power_rank']}: {data['team_name']} (Score: {data['power_score']})")

    # Connect to BigQuery
    if not dry_run:
        print("\nConnecting to BigQuery...")
        client = bigquery.Client(project=PROJECT_ID)
    else:
        client = None

    # Get existing rankings
    print(f"\nFetching existing rankings from BigQuery...")
    existing_rankings = get_existing_rankings(client, dry_run)
    if existing_rankings:
        print(f"  Found {len(existing_rankings)} existing team rankings")

    # Update rankings
    update_rankings(client, power_rankings, existing_rankings, dry_run)

    print("\n" + "="*60)
    print("SYNC COMPLETE")
    print("="*60)


if __name__ == '__main__':
    main()

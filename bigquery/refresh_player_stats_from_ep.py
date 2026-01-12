#!/usr/bin/env python3
"""
Refresh Player Stats from Elite Prospects API
==============================================
Updates the player_stats table with current data from Elite Prospects.

This script:
1. Fetches all players for birth years 2008-2012 from EP API
2. Updates the prodigy-ranking.algorithm_core.player_stats table
3. Creates a backup before updating

Usage:
    python refresh_player_stats_from_ep.py              # Full refresh
    python refresh_player_stats_from_ep.py --test       # Test with 1 birth year
    python refresh_player_stats_from_ep.py --year 2008  # Single year only
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time
import sys
import argparse
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Users/phili/AppData/Roaming/gcloud/application_default_credentials.json'

# Configuration
API_KEY = "EmmrXHpydfr14MVUdFxZyCCczQ3wqghc"
BASE_URL = "https://api.eliteprospects.com/v1"
PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"
TABLE = "player_stats"

# Target birth years
TARGET_YEARS = [2007, 2008, 2009, 2010, 2011, 2012]

def log(message, level="INFO"):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{timestamp} [{level}] {message}")

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def test_api_connection():
    """Test if the EP API is accessible"""
    log("Testing EP API connection...")
    url = f"{BASE_URL}/players"
    params = {
        'apiKey': API_KEY,
        'yearOfBirth': 2008,
        'gender': 'male',
        'limit': 1
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        if response.status_code == 200:
            data = response.json()
            count = data.get('_meta', {}).get('totalRecords', 0)
            log(f"API connection successful. Sample query returned {count} total players.")
            return True
        else:
            log(f"API error: {response.status_code} - {response.text}", "ERROR")
            return False
    except Exception as e:
        log(f"API connection failed: {e}", "ERROR")
        return False

def fetch_players_for_year(birth_year, limit=None):
    """Fetch all players for a specific birth year from EP API"""
    players = []
    offset = 0
    page_size = 100

    log(f"Fetching {birth_year}-born players...")

    while True:
        params = {
            'apiKey': API_KEY,
            'yearOfBirth': birth_year,
            'gender': 'male',
            'limit': page_size,
            'offset': offset
        }

        try:
            # Retry logic for transient errors
            max_retries = 3
            for retry in range(max_retries):
                response = requests.get(f"{BASE_URL}/players", params=params, timeout=60)

                if response.status_code == 200:
                    break
                elif response.status_code >= 500:
                    log(f"API error {response.status_code} at offset {offset}, retry {retry+1}/{max_retries}", "WARN")
                    time.sleep(5 * (retry + 1))  # Exponential backoff
                else:
                    log(f"API error at offset {offset}: {response.status_code}", "ERROR")
                    break

            if response.status_code != 200:
                log(f"Failed after {max_retries} retries at offset {offset}", "ERROR")
                break

            data = response.json()
            page_players = data.get('data', [])

            if not page_players:
                break

            players.extend(page_players)
            offset += page_size

            # Progress update every 1000 players
            if len(players) % 1000 == 0:
                log(f"  ... {len(players)} players fetched so far")

            # Rate limiting
            time.sleep(0.5)

            # Check if we have all players
            total_count = data.get('_meta', {}).get('totalRecords', 0)
            if offset >= total_count:
                break

            # Optional limit for testing
            if limit and len(players) >= limit:
                break

        except Exception as e:
            log(f"Error at offset {offset}: {e}", "ERROR")
            time.sleep(2)
            continue

    log(f"  Completed {birth_year}: {len(players)} players")
    return players

def flatten_player(player):
    """Flatten nested EP API player data"""
    flat = {
        'id': player.get('id'),
        'name': player.get('name'),
        'firstName': player.get('firstName'),
        'lastName': player.get('lastName'),
        'position': player.get('position'),
        'yearOfBirth': player.get('yearOfBirth'),
        'dateOfBirth': player.get('dateOfBirth'),
        'age': player.get('age'),
        'placeOfBirth': player.get('placeOfBirth'),
        'youthTeam': player.get('youthTeam'),
        'nationality_name': player.get('nationality', {}).get('name') if player.get('nationality') else None,
        'nationality_slug': player.get('nationality', {}).get('slug') if player.get('nationality') else None,
        'height': player.get('height'),
        'weight': player.get('weight'),
        'gender': player.get('gender'),
        'status': player.get('status'),
        'playerType': player.get('playerType'),
        'catches': player.get('shoots'),  # shoots/catches
        'views': player.get('views'),
        'imageUrl': player.get('imageUrl'),
        'eliteprospectsUrlPath': player.get('eliteprospectsUrlPath'),
        'updatedAt': player.get('updatedAt'),
    }

    # Latest stats
    latest = player.get('latestStats', {}) or {}
    flat['latestStats_season_slug'] = latest.get('season', {}).get('slug') if latest.get('season') else None
    flat['latestStats_season_startYear'] = latest.get('season', {}).get('startYear') if latest.get('season') else None
    flat['latestStats_season_endYear'] = latest.get('season', {}).get('endYear') if latest.get('season') else None
    flat['latestStats_team_name'] = latest.get('team', {}).get('name') if latest.get('team') else None
    flat['latestStats_team_id'] = latest.get('team', {}).get('id') if latest.get('team') else None
    flat['latestStats_team_league_name'] = latest.get('team', {}).get('league', {}).get('name') if latest.get('team', {}).get('league') else None
    flat['latestStats_team_league_slug'] = latest.get('team', {}).get('league', {}).get('slug') if latest.get('team', {}).get('league') else None

    # Regular stats
    reg = latest.get('regularStats', {}) or {}
    flat['latestStats_regularStats_GP'] = reg.get('GP')
    flat['latestStats_regularStats_G'] = reg.get('G')
    flat['latestStats_regularStats_A'] = reg.get('A')
    flat['latestStats_regularStats_PTS'] = reg.get('PTS')
    flat['latestStats_regularStats_PIM'] = reg.get('PIM')
    flat['latestStats_regularStats_PM'] = reg.get('PM')
    flat['latestStats_regularStats_GAA'] = reg.get('GAA')
    flat['latestStats_regularStats_SVP'] = reg.get('SVP')
    flat['latestStats_regularStats_SO'] = reg.get('SO')
    flat['latestStats_regularStats_W'] = reg.get('W')
    flat['latestStats_regularStats_L'] = reg.get('L')

    # Metadata
    flat['loadts'] = datetime.now()

    return flat

def backup_current_table(client):
    """Create a backup of the current player_stats table"""
    backup_name = f"{TABLE}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    log(f"Creating backup: {backup_name}")

    query = f"""
    CREATE TABLE `{PROJECT_ID}.{DATASET}.{backup_name}` AS
    SELECT * FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """

    try:
        client.query(query).result()
        log(f"Backup created: {backup_name}")
        return backup_name
    except Exception as e:
        log(f"Backup failed: {e}", "ERROR")
        return None

def update_player_stats(df, client):
    """Update the player_stats table using MERGE to preserve views column"""
    table_id = f"{PROJECT_ID}.{DATASET}.{TABLE}"
    staging_table = f"{PROJECT_ID}.{DATASET}.{TABLE}_staging"

    log(f"Uploading {len(df)} players via MERGE (preserving views)...")

    # Upload to staging table first
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',
        autodetect=True
    )

    job = client.load_table_from_dataframe(df, staging_table, job_config=job_config)
    job.result()
    log(f"Staging table created with {len(df)} rows")

    # MERGE: Update existing players with matching columns only, preserve views
    # Note: Target has height_imperial/height_metrics, source has height
    merge_query = f"""
    MERGE `{table_id}` AS target
    USING `{staging_table}` AS source
    ON target.id = CAST(source.id AS INT64)
    WHEN MATCHED THEN UPDATE SET
        target.name = source.name,
        target.firstName = source.firstName,
        target.lastName = source.lastName,
        target.position = source.position,
        -- NOTE: yearOfBirth NOT updated - EP batch API doesn't return it, preserve existing
        target.dateOfBirth = source.dateOfBirth,
        target.age = CAST(source.age AS INT64),
        target.placeOfBirth = source.placeOfBirth,
        target.youthTeam = source.youthTeam,
        target.nationality_name = source.nationality_name,
        target.nationality_slug = source.nationality_slug,
        target.gender = source.gender,
        target.status = source.status,
        target.playerType = source.playerType,
        target.catches = source.catches,
        target.imageUrl = source.imageUrl,
        target.eliteprospectsUrlPath = source.eliteprospectsUrlPath,
        target.updatedAt = source.updatedAt,
        target.latestStats_season_slug = source.latestStats_season_slug,
        target.latestStats_season_startYear = CAST(source.latestStats_season_startYear AS INT64),
        target.latestStats_season_endYear = CAST(source.latestStats_season_endYear AS INT64),
        target.latestStats_team_name = source.latestStats_team_name,
        target.latestStats_team_id = CAST(source.latestStats_team_id AS INT64),
        target.latestStats_team_league_name = source.latestStats_team_league_name,
        target.latestStats_team_league_slug = source.latestStats_team_league_slug,
        target.latestStats_regularStats_GP = CAST(source.latestStats_regularStats_GP AS INT64),
        target.latestStats_regularStats_G = CAST(source.latestStats_regularStats_G AS STRING),
        target.latestStats_regularStats_A = CAST(source.latestStats_regularStats_A AS STRING),
        target.latestStats_regularStats_PTS = CAST(source.latestStats_regularStats_PTS AS STRING),
        target.latestStats_regularStats_PIM = CAST(source.latestStats_regularStats_PIM AS STRING),
        target.latestStats_regularStats_PM = CAST(source.latestStats_regularStats_PM AS STRING),
        target.latestStats_regularStats_GAA = CAST(source.latestStats_regularStats_GAA AS FLOAT64),
        target.latestStats_regularStats_SVP = CAST(source.latestStats_regularStats_SVP AS FLOAT64),
        target.latestStats_regularStats_SO = CAST(source.latestStats_regularStats_SO AS INT64),
        target.latestStats_regularStats_W = CAST(source.latestStats_regularStats_W AS INT64),
        target.latestStats_regularStats_L = CAST(source.latestStats_regularStats_L AS INT64),
        target.loadts = source.loadts
        -- NOTE: views is NOT updated here - preserved from existing data
        -- NOTE: height/weight not updated - schema mismatch (target has height_imperial/metrics)
    """
    # Note: NOT MATCHED clause removed - we only update existing players
    # New players would need full schema which we don't have in staging

    result = client.query(merge_query).result()
    log(f"MERGE complete - existing players updated")

    # Get stats
    stats_query = f"""
    SELECT COUNT(*) as total, MAX(loadts) as last_load FROM `{table_id}`
    """
    df_stats = client.query(stats_query).to_dataframe()
    log(f"Table has {df_stats.iloc[0]['total']} players, last load: {df_stats.iloc[0]['last_load']}")

    # Check how many new players in staging but not in target
    new_check = f"""
    SELECT COUNT(*) as new_players
    FROM `{staging_table}` s
    LEFT JOIN `{table_id}` t ON CAST(s.id AS INT64) = t.id
    WHERE t.id IS NULL
    """
    df_new = client.query(new_check).to_dataframe()
    new_count = df_new.iloc[0]['new_players']
    if new_count > 0:
        log(f"Note: {new_count} new players in EP not added (schema mismatch)")

    # Clean up staging table
    client.delete_table(staging_table, not_found_ok=True)
    log("Staging table deleted")

def main():
    parser = argparse.ArgumentParser(description='Refresh player stats from Elite Prospects')
    parser.add_argument('--test', action='store_true', help='Test mode - only fetch 2008 birth year')
    parser.add_argument('--year', type=int, help='Fetch specific birth year only')
    parser.add_argument('--no-backup', action='store_true', help='Skip backup')
    args = parser.parse_args()

    log("=" * 70)
    log("ELITE PROSPECTS PLAYER STATS REFRESH")
    log("=" * 70)

    # Test API connection
    if not test_api_connection():
        log("API connection failed. Exiting.", "ERROR")
        return 1

    # Determine which years to fetch
    if args.year:
        years = [args.year]
    elif args.test:
        years = [2008]
    else:
        years = TARGET_YEARS

    log(f"Target birth years: {years}")

    # Fetch all players
    all_players = []
    for year in years:
        players = fetch_players_for_year(year)
        all_players.extend(players)

    log(f"Total players fetched: {len(all_players)}")

    if len(all_players) == 0:
        log("No players fetched. Exiting.", "ERROR")
        return 1

    # Flatten player data
    log("Flattening player data...")
    flat_players = [flatten_player(p) for p in all_players]
    df = pd.DataFrame(flat_players)

    log(f"DataFrame created: {len(df)} rows, {len(df.columns)} columns")

    # Connect to BigQuery
    client = get_client()

    # Create backup
    if not args.no_backup:
        backup_name = backup_current_table(client)
        if not backup_name:
            log("Backup failed. Continuing anyway...", "WARN")

    # Update table
    update_player_stats(df, client)

    log("=" * 70)
    log("REFRESH COMPLETE")
    log(f"Players updated: {len(df)}")
    log("=" * 70)

    # Verify
    verify_query = f"""
    SELECT COUNT(*) as cnt, MAX(loadts) as last_load
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
    """
    result = client.query(verify_query).to_dataframe()
    log(f"Verification: {result.iloc[0]['cnt']} players, last load: {result.iloc[0]['last_load']}")

    return 0

if __name__ == '__main__':
    sys.exit(main())

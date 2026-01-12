#!/usr/bin/env python3
"""
Add New Players from Elite Prospects
=====================================
Fetches players from EP API and adds only those not already in BigQuery.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time
import sys

API_KEY = "EmmrXHpydfr14MVUdFxZyCCczQ3wqghc"
BASE_URL = "https://api.eliteprospects.com/v1"
PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"
TABLE = "player_stats"

TARGET_YEARS = [2007, 2008, 2009, 2010, 2011, 2012]

def log(msg):
    print(f"{datetime.now().strftime('%H:%M:%S')} {msg}", flush=True)

def get_existing_ids(client):
    """Get all existing player IDs from BigQuery"""
    query = f"SELECT DISTINCT id FROM `{PROJECT_ID}.{DATASET}.{TABLE}`"
    df = client.query(query).to_dataframe()
    return set(df['id'].tolist())

def fetch_new_players(existing_ids):
    """Fetch players from EP that don't exist in our table"""
    new_players = []

    for year in TARGET_YEARS:
        log(f"Fetching {year}-born players...")
        offset = 0
        year_new = 0

        while True:
            params = {
                'apiKey': API_KEY,
                'yearOfBirth': year,
                'gender': 'male',
                'limit': 100,
                'offset': offset
            }

            try:
                response = requests.get(f"{BASE_URL}/players", params=params, timeout=60)
                if response.status_code != 200:
                    log(f"  API error: {response.status_code}")
                    break

                data = response.json()
                players = data.get('data', [])

                if not players:
                    break

                for p in players:
                    if p.get('id') not in existing_ids:
                        new_players.append(p)
                        year_new += 1

                offset += 100
                total = data.get('_meta', {}).get('totalRecords', 0)

                if offset >= total:
                    break

                time.sleep(0.3)

            except Exception as e:
                log(f"  Error: {e}")
                time.sleep(2)
                continue

        log(f"  {year}: {year_new} new players found")

    return new_players

def flatten_player(p):
    """Flatten player data to match target schema"""
    latest = p.get('latestStats', {}) or {}
    team = latest.get('team', {}) or {}
    league = team.get('league', {}) or {}
    reg = latest.get('regularStats', {}) or {}
    season = latest.get('season', {}) or {}
    nationality = p.get('nationality', {}) or {}

    return {
        'id': p.get('id'),
        'firstName': p.get('firstName'),
        'lastName': p.get('lastName'),
        'name': p.get('name'),
        'gender': p.get('gender'),
        'status': p.get('status'),
        'playerType': p.get('playerType'),
        'position': p.get('position'),
        'catches': p.get('shoots'),
        'yearOfBirth': p.get('yearOfBirth'),
        'dateOfBirth': p.get('dateOfBirth'),
        'age': p.get('age'),
        'placeOfBirth': p.get('placeOfBirth'),
        'youthTeam': p.get('youthTeam'),
        'nationality_slug': nationality.get('slug'),
        'nationality_name': nationality.get('name'),
        'height_imperial': p.get('height'),  # STRING in target
        'weight_imperial': None,  # INT64 in target - skip, EP returns string
        'views': 0,  # New players start with 0 views
        'imageUrl': p.get('imageUrl'),
        'eliteprospectsUrlPath': p.get('eliteprospectsUrlPath'),
        'updatedAt': p.get('updatedAt'),
        'latestStats_season_slug': season.get('slug'),
        'latestStats_season_startYear': season.get('startYear'),
        'latestStats_season_endYear': season.get('endYear'),
        'latestStats_team_id': team.get('id'),
        'latestStats_team_name': team.get('name'),
        'latestStats_team_league_slug': league.get('slug'),
        'latestStats_team_league_name': league.get('name'),
        'latestStats_regularStats_GP': reg.get('GP'),
        'latestStats_regularStats_G': str(reg.get('G')) if reg.get('G') is not None else None,
        'latestStats_regularStats_A': str(reg.get('A')) if reg.get('A') is not None else None,
        'latestStats_regularStats_PTS': str(reg.get('PTS')) if reg.get('PTS') is not None else None,
        'latestStats_regularStats_PIM': str(reg.get('PIM')) if reg.get('PIM') is not None else None,
        'latestStats_regularStats_PM': str(reg.get('PM')) if reg.get('PM') is not None else None,
        'latestStats_regularStats_GAA': reg.get('GAA'),
        'latestStats_regularStats_SVP': reg.get('SVP'),
        'latestStats_regularStats_SO': reg.get('SO'),
        'latestStats_regularStats_W': reg.get('W'),
        'latestStats_regularStats_L': reg.get('L'),
        'loadts': datetime.now(),
    }

def insert_new_players(players, client):
    """Insert new players into BigQuery"""
    if not players:
        log("No new players to insert")
        return 0

    # Flatten player data
    records = [flatten_player(p) for p in players]
    df = pd.DataFrame(records)

    log(f"Inserting {len(df)} new players...")

    # Upload to staging table
    staging = f"{PROJECT_ID}.{DATASET}.new_players_staging"
    job_config = bigquery.LoadJobConfig(
        write_disposition='WRITE_TRUNCATE',
        autodetect=True
    )
    job = client.load_table_from_dataframe(df, staging, job_config=job_config)
    job.result()
    log("Staging table created")

    # Insert into main table (excluding weight_imperial which is INT64 but EP returns string)
    insert_query = f"""
    INSERT INTO `{PROJECT_ID}.{DATASET}.{TABLE}` (
        id, firstName, lastName, name, gender, status, playerType, position, catches,
        yearOfBirth, dateOfBirth, age, placeOfBirth, youthTeam, nationality_slug, nationality_name,
        height_imperial, views, imageUrl, eliteprospectsUrlPath, updatedAt,
        latestStats_season_slug, latestStats_season_startYear, latestStats_season_endYear,
        latestStats_team_id, latestStats_team_name, latestStats_team_league_slug, latestStats_team_league_name,
        latestStats_regularStats_GP, latestStats_regularStats_G, latestStats_regularStats_A,
        latestStats_regularStats_PTS, latestStats_regularStats_PIM, latestStats_regularStats_PM,
        latestStats_regularStats_GAA, latestStats_regularStats_SVP, latestStats_regularStats_SO,
        latestStats_regularStats_W, latestStats_regularStats_L, loadts
    )
    SELECT
        CAST(id AS INT64), firstName, lastName, name, gender, status, playerType, position, catches,
        CAST(yearOfBirth AS INT64), dateOfBirth, CAST(age AS INT64), placeOfBirth, youthTeam,
        nationality_slug, nationality_name, height_imperial,
        CAST(views AS INT64), imageUrl, eliteprospectsUrlPath, updatedAt,
        latestStats_season_slug, CAST(latestStats_season_startYear AS INT64),
        CAST(latestStats_season_endYear AS INT64),
        CAST(latestStats_team_id AS INT64), latestStats_team_name,
        latestStats_team_league_slug, latestStats_team_league_name,
        CAST(latestStats_regularStats_GP AS INT64), latestStats_regularStats_G, latestStats_regularStats_A,
        latestStats_regularStats_PTS, latestStats_regularStats_PIM, latestStats_regularStats_PM,
        CAST(latestStats_regularStats_GAA AS FLOAT64), CAST(latestStats_regularStats_SVP AS FLOAT64),
        CAST(latestStats_regularStats_SO AS INT64),
        CAST(latestStats_regularStats_W AS INT64), CAST(latestStats_regularStats_L AS INT64),
        CAST(loadts AS TIMESTAMP)
    FROM `{staging}`
    """

    client.query(insert_query).result()
    log("Insert complete")

    # Cleanup
    client.delete_table(staging, not_found_ok=True)

    return len(df)

def main():
    log("=" * 60)
    log("ADD NEW PLAYERS FROM ELITE PROSPECTS")
    log("=" * 60)

    client = bigquery.Client(project=PROJECT_ID)

    # Get existing IDs
    log("Getting existing player IDs...")
    existing_ids = get_existing_ids(client)
    log(f"Existing players: {len(existing_ids)}")

    # Fetch new players
    new_players = fetch_new_players(existing_ids)
    log(f"Total new players found: {len(new_players)}")

    if not new_players:
        log("No new players to add!")
        return 0

    # Insert new players
    inserted = insert_new_players(new_players, client)

    # Verify
    verify = f"SELECT COUNT(*) as cnt FROM `{PROJECT_ID}.{DATASET}.{TABLE}`"
    result = client.query(verify).to_dataframe()
    log(f"Total players now: {result.iloc[0]['cnt']}")

    log("=" * 60)
    log(f"COMPLETE - Added {inserted} new players")
    log("=" * 60)

    return 0

if __name__ == '__main__':
    sys.exit(main())

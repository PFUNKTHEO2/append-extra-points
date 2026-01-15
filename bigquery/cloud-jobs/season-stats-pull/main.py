#!/usr/bin/env python3
"""
Cloud Run Job: Pull All Player Season Stats from Elite Prospects API
=====================================================================
Fetches season-by-season stats for all players and stores in BigQuery.

This runs as a Cloud Run Job - designed to run for hours/days continuously.
Progress is tracked in BigQuery so it can resume if restarted.
"""

import requests
import pandas as pd
from google.cloud import bigquery
from datetime import datetime
import time
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
API_KEY = os.environ.get('EP_API_KEY', 'EmmrXHpydfr14MVUdFxZyCCczQ3wqghc')
BASE_URL = "https://api.eliteprospects.com/v1"
PROJECT_ID = os.environ.get('GCP_PROJECT', 'prodigy-ranking')
DATASET = "algorithm_core"
STATS_TABLE = "player_season_stats"
PROGRESS_TABLE = "season_stats_progress"

# Rate limiting
REQUESTS_PER_SECOND = 1.5  # Conservative to avoid rate limits
BATCH_SIZE = 100  # Save to BigQuery every N players
CHECKPOINT_INTERVAL = 500  # Log checkpoint every N players

def get_client():
    return bigquery.Client(project=PROJECT_ID)

def ensure_tables_exist(client):
    """Create tables if they don't exist"""

    # Stats table schema
    stats_schema = [
        bigquery.SchemaField("player_id", "INTEGER"),
        bigquery.SchemaField("stat_id", "INTEGER"),
        bigquery.SchemaField("season_slug", "STRING"),
        bigquery.SchemaField("season_start_year", "INTEGER"),
        bigquery.SchemaField("season_end_year", "INTEGER"),
        bigquery.SchemaField("stats_type", "STRING"),
        bigquery.SchemaField("status", "STRING"),
        bigquery.SchemaField("team_id", "INTEGER"),
        bigquery.SchemaField("team_name", "STRING"),
        bigquery.SchemaField("team_status", "STRING"),
        bigquery.SchemaField("league_slug", "STRING"),
        bigquery.SchemaField("league_name", "STRING"),
        bigquery.SchemaField("league_level", "STRING"),
        bigquery.SchemaField("league_country", "STRING"),
        bigquery.SchemaField("gp", "INTEGER"),
        bigquery.SchemaField("goals", "INTEGER"),
        bigquery.SchemaField("assists", "INTEGER"),
        bigquery.SchemaField("points", "INTEGER"),
        bigquery.SchemaField("pim", "INTEGER"),
        bigquery.SchemaField("plus_minus", "INTEGER"),
        bigquery.SchemaField("ppg", "FLOAT"),
        bigquery.SchemaField("gaa", "FLOAT"),
        bigquery.SchemaField("svp", "FLOAT"),
        bigquery.SchemaField("wins", "INTEGER"),
        bigquery.SchemaField("losses", "INTEGER"),
        bigquery.SchemaField("shutouts", "INTEGER"),
        bigquery.SchemaField("saves", "INTEGER"),
        bigquery.SchemaField("goals_against", "INTEGER"),
        bigquery.SchemaField("has_postseason", "BOOLEAN"),
        bigquery.SchemaField("postseason_gp", "INTEGER"),
        bigquery.SchemaField("postseason_goals", "INTEGER"),
        bigquery.SchemaField("postseason_assists", "INTEGER"),
        bigquery.SchemaField("postseason_points", "INTEGER"),
        bigquery.SchemaField("jersey_number", "STRING"),
        bigquery.SchemaField("player_role", "STRING"),
        bigquery.SchemaField("loaded_at", "TIMESTAMP"),
    ]

    # Progress tracking table schema
    progress_schema = [
        bigquery.SchemaField("player_id", "INTEGER"),
        bigquery.SchemaField("status", "STRING"),  # 'completed', 'no_stats', 'error'
        bigquery.SchemaField("records_found", "INTEGER"),
        bigquery.SchemaField("processed_at", "TIMESTAMP"),
    ]

    for table_name, schema in [(STATS_TABLE, stats_schema), (PROGRESS_TABLE, progress_schema)]:
        table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"
        table = bigquery.Table(table_id, schema=schema)
        try:
            client.create_table(table)
            logger.info(f"Created table {table_id}")
        except Exception as e:
            if "Already Exists" in str(e):
                logger.info(f"Table {table_id} already exists")
            else:
                logger.error(f"Error creating table: {e}")

def get_all_player_ids(client):
    """Get all player IDs from player_rankings table"""
    query = f"""
    SELECT DISTINCT player_id
    FROM `{PROJECT_ID}.{DATASET}.player_rankings`
    WHERE player_id IS NOT NULL
    ORDER BY player_id
    """
    df = client.query(query).to_dataframe()
    return df['player_id'].tolist()

def get_completed_player_ids(client):
    """Get player IDs that have already been processed"""
    query = f"""
    SELECT DISTINCT player_id
    FROM `{PROJECT_ID}.{DATASET}.{PROGRESS_TABLE}`
    WHERE status IN ('completed', 'no_stats')
    """
    try:
        df = client.query(query).to_dataframe()
        return set(df['player_id'].tolist())
    except:
        return set()

def fetch_player_stats(player_id):
    """Fetch season stats for a single player from EP API"""
    url = f"{BASE_URL}/players/{player_id}/stats"
    params = {'apiKey': API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            return response.json().get('data', [])
        elif response.status_code == 404:
            return []  # Player not found
        elif response.status_code == 429:
            logger.warning(f"Rate limited, sleeping 60s...")
            time.sleep(60)
            return fetch_player_stats(player_id)  # Retry
        else:
            logger.warning(f"API error for player {player_id}: {response.status_code}")
            return None

    except Exception as e:
        logger.error(f"Request error for player {player_id}: {e}")
        return None

def safe_int(val):
    if val is None or val == '' or val == '-':
        return None
    try:
        return int(val)
    except:
        return None

def safe_float(val):
    if val is None or val == '' or val == '-':
        return None
    try:
        return float(val)
    except:
        return None

def flatten_season_stat(player_id, stat):
    """Flatten a single season stat record"""
    season = stat.get('season', {}) or {}
    team = stat.get('team', {}) or {}
    league = team.get('league', {}) or {}
    reg = stat.get('regularStats', {}) or {}
    post = stat.get('postseasonStats', {}) or {}

    return {
        'player_id': player_id,
        'stat_id': stat.get('id'),
        'season_slug': season.get('slug'),
        'season_start_year': season.get('startYear'),
        'season_end_year': season.get('endYear'),
        'stats_type': stat.get('statsType'),
        'status': stat.get('status'),
        'team_id': team.get('id'),
        'team_name': team.get('name'),
        'team_status': team.get('status'),
        'league_slug': league.get('slug'),
        'league_name': league.get('name'),
        'league_level': league.get('leagueLevel'),
        'league_country': league.get('country', {}).get('name') if league.get('country') else None,
        'gp': safe_int(reg.get('GP')),
        'goals': safe_int(reg.get('G')),
        'assists': safe_int(reg.get('A')),
        'points': safe_int(reg.get('PTS')),
        'pim': safe_int(reg.get('PIM')),
        'plus_minus': safe_int(reg.get('PM')),
        'ppg': safe_float(reg.get('PPG')),
        'gaa': safe_float(reg.get('GAA')),
        'svp': safe_float(reg.get('SVP')),
        'wins': safe_int(reg.get('W')),
        'losses': safe_int(reg.get('L')),
        'shutouts': safe_int(reg.get('SO')),
        'saves': safe_int(reg.get('SVS')),
        'goals_against': safe_int(reg.get('GA')),
        'has_postseason': bool(post),
        'postseason_gp': safe_int(post.get('GP')) if post else None,
        'postseason_goals': safe_int(post.get('G')) if post else None,
        'postseason_assists': safe_int(post.get('A')) if post else None,
        'postseason_points': safe_int(post.get('PTS')) if post else None,
        'jersey_number': str(stat.get('jerseyNumber')) if stat.get('jerseyNumber') is not None else None,
        'player_role': stat.get('playerRole'),
        'loaded_at': datetime.utcnow()
    }

def upload_stats_batch(client, records):
    """Upload batch of stats records to BigQuery"""
    if not records:
        return 0

    df = pd.DataFrame(records)
    table_id = f"{PROJECT_ID}.{DATASET}.{STATS_TABLE}"

    job_config = bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

    return len(records)

def upload_progress_batch(client, progress_records):
    """Upload progress tracking records"""
    if not progress_records:
        return

    df = pd.DataFrame(progress_records)
    table_id = f"{PROJECT_ID}.{DATASET}.{PROGRESS_TABLE}"

    job_config = bigquery.LoadJobConfig(write_disposition='WRITE_APPEND')
    job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
    job.result()

def main():
    logger.info("=" * 70)
    logger.info("ELITE PROSPECTS SEASON STATS CLOUD JOB")
    logger.info("=" * 70)

    client = get_client()

    # Ensure tables exist
    ensure_tables_exist(client)

    # Get all player IDs
    logger.info("Fetching player IDs from player_rankings...")
    all_player_ids = get_all_player_ids(client)
    logger.info(f"Total players in system: {len(all_player_ids):,}")

    # Get already completed player IDs
    completed_ids = get_completed_player_ids(client)
    logger.info(f"Already completed: {len(completed_ids):,}")

    # Filter to remaining players
    remaining_ids = [pid for pid in all_player_ids if pid not in completed_ids]
    logger.info(f"Remaining to process: {len(remaining_ids):,}")

    if not remaining_ids:
        logger.info("All players already processed!")
        return

    # Process players
    stats_batch = []
    progress_batch = []
    total_records = 0
    processed = 0
    start_time = datetime.now()

    for i, player_id in enumerate(remaining_ids):
        # Fetch stats from API
        stats = fetch_player_stats(player_id)

        if stats is None:
            # API error - record and continue
            progress_batch.append({
                'player_id': player_id,
                'status': 'error',
                'records_found': 0,
                'processed_at': datetime.utcnow()
            })
        elif len(stats) == 0:
            # No stats found
            progress_batch.append({
                'player_id': player_id,
                'status': 'no_stats',
                'records_found': 0,
                'processed_at': datetime.utcnow()
            })
        else:
            # Process stats
            for stat in stats:
                record = flatten_season_stat(player_id, stat)
                stats_batch.append(record)

            progress_batch.append({
                'player_id': player_id,
                'status': 'completed',
                'records_found': len(stats),
                'processed_at': datetime.utcnow()
            })
            total_records += len(stats)

        processed += 1

        # Upload batch
        if len(stats_batch) >= BATCH_SIZE * 7:  # ~7 records per player average
            upload_stats_batch(client, stats_batch)
            upload_progress_batch(client, progress_batch)
            stats_batch = []
            progress_batch = []

        # Log checkpoint
        if processed % CHECKPOINT_INTERVAL == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = len(remaining_ids) - processed
            eta_hours = remaining / rate / 3600 if rate > 0 else 0

            logger.info(f"Progress: {processed:,}/{len(remaining_ids):,} ({processed/len(remaining_ids)*100:.1f}%) | "
                       f"Records: {total_records:,} | Rate: {rate:.1f}/sec | ETA: {eta_hours:.1f}h")

        # Rate limiting
        time.sleep(1 / REQUESTS_PER_SECOND)

    # Final upload
    if stats_batch:
        upload_stats_batch(client, stats_batch)
    if progress_batch:
        upload_progress_batch(client, progress_batch)

    elapsed = (datetime.now() - start_time).total_seconds()
    logger.info("=" * 70)
    logger.info("JOB COMPLETE")
    logger.info(f"Processed: {processed:,} players")
    logger.info(f"Total records: {total_records:,}")
    logger.info(f"Time: {elapsed/3600:.1f} hours")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()

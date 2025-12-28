"""
Sync Player Rankings from BigQuery to Supabase
===============================================
This script syncs player_cumulative_points from BigQuery to Supabase
for fast API lookups. Run after algorithm recalculates rankings.

Usage:
    python sync_rankings_to_supabase.py
    python sync_rankings_to_supabase.py --full    # Full sync (truncate + insert)
    python sync_rankings_to_supabase.py --delta   # Delta sync (upsert changed records)
"""

import pandas as pd
from supabase import create_client, Client
from google.cloud import bigquery
import sys
import time
from datetime import datetime

# Configuration
SUPABASE_URL = "https://xqkwvywcxmnfimkubtyo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhxa3d2eXdjeG1uZmlta3VidHlvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxOTQzNTU2NywiZXhwIjoyMDM1MDExNTY3fQ.I2u4shTCxEt-1nJCNZKcl1DV91flxB5KrJ4NDcl_hWw"

BQ_PROJECT_ID = "prodigy-ranking"
BQ_DATASET_ID = "algorithm_core"
BQ_TABLE_ID = "player_cumulative_points"

# Columns from player_cumulative_points (base table)
BASE_COLUMNS = [
    "player_id",
    "player_name",
    "position",
    "birth_year",
    "nationality_name",
    "current_team",
    "current_league",
    "team_country",
    "current_season",
    "total_points",
    "performance_total",
    "direct_load_total",
    "f01_views",
    "f02_height",
    "f03_current_goals_f",
    "f04_current_goals_d",
    "f05_current_assists",
    "f06_current_gaa",
    "f07_current_svp",
    "f08_last_goals_f",
    "f09_last_goals_d",
    "f10_last_assists",
    "f11_last_gaa",
    "f12_last_svp",
    "f13_league_points",
    "f14_team_points",
    "f15_international_points",
    "f16_commitment_points",
    "f17_draft_points",
    "f18_weekly_points_delta",
    "f19_weekly_assists_delta",
    "f20_playing_up_points",
    "f21_tournament_points",
    "f22_manual_points",
    "f23_prodigylikes_points",
    "f24_card_sales_points",
    "f26_weight_points",
    "f27_bmi_points",
    "calculated_at",
    "algorithm_version"
]

# EA-style rating columns (from player_card_ratings view)
RATING_COLUMNS = [
    "overall_rating",
    "performance_rating",
    "level_rating",
    "visibility_rating",
    "achievements_rating",
    "trending_rating",
    "physical_rating",
    "perf",
    "lvl",
    "vis",
    "ach",
    "trd",
    "phy"
]

# Percentile columns for radar charts (from player_category_percentiles view)
PERCENTILE_COLUMNS = [
    "performance_percentile",
    "level_percentile",
    "visibility_percentile",
    "achievements_percentile",
    "physical_percentile",
    "trending_percentile",
    "overall_percentile"
]


def setup_connections():
    """Set up Supabase and BigQuery connections"""
    print("Setting up connections...")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("  Supabase connected")

    bq_client = bigquery.Client(project=BQ_PROJECT_ID)
    print("  BigQuery connected")

    return supabase, bq_client


def get_bigquery_data(bq_client, limit=None):
    """Extract player data from BigQuery with ratings and percentiles"""
    print(f"\nExtracting data from BigQuery...")

    # Build column SQL for base table
    base_sql_parts = []
    for col in BASE_COLUMNS:
        if col in ["total_points", "performance_total", "direct_load_total"]:
            base_sql_parts.append(f"ROUND(p.{col}, 2) as {col}")
        elif col.startswith("f") and col[1:3].isdigit():
            base_sql_parts.append(f"ROUND(COALESCE(p.{col}, 0), 2) as {col}")
        else:
            base_sql_parts.append(f"p.{col}")

    # Add rating columns from card_ratings view
    rating_sql_parts = [f"COALESCE(r.{col}, 0) as {col}" for col in RATING_COLUMNS]

    # Add percentile columns from category_percentiles view
    percentile_sql_parts = [f"COALESCE(pct.{col}, 0) as {col}" for col in PERCENTILE_COLUMNS]

    all_columns = ", ".join(base_sql_parts + rating_sql_parts + percentile_sql_parts)

    query = f"""
        SELECT {all_columns}
        FROM `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}` p
        LEFT JOIN `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.player_card_ratings` r
            ON p.player_id = r.player_id
        LEFT JOIN `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.player_category_percentiles` pct
            ON p.player_id = pct.player_id
        ORDER BY p.total_points DESC
        {"LIMIT " + str(limit) if limit else ""}
    """

    start_time = time.time()
    df = bq_client.query(query).to_dataframe()
    elapsed = time.time() - start_time

    print(f"  Extracted {len(df):,} records in {elapsed:.1f}s")
    return df


def prepare_data_for_supabase(df):
    """Prepare DataFrame for Supabase insertion"""
    print("\nPreparing data for Supabase...")

    # Convert timestamps to ISO format strings
    if 'calculated_at' in df.columns:
        df['calculated_at'] = pd.to_datetime(df['calculated_at']).dt.strftime('%Y-%m-%dT%H:%M:%S')

    # Convert all numeric columns to float (handles Decimal types from BigQuery)
    for col in df.columns:
        if df[col].dtype == 'object':
            # Check if it's a Decimal column by looking at first non-null value
            first_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if first_val is not None and hasattr(first_val, 'as_tuple'):
                # It's a Decimal, convert to float
                df[col] = df[col].apply(lambda x: float(x) if x is not None and hasattr(x, 'as_tuple') else x)

        # Now handle NaN/None
        if df[col].dtype == 'float64' or str(df[col].dtype).startswith('float'):
            df[col] = df[col].fillna(0).round(2)
        elif df[col].dtype == 'object':
            df[col] = df[col].fillna('')

    # Ensure player_id is integer
    df['player_id'] = df['player_id'].astype(int)

    # Add sync timestamp
    df['synced_at'] = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')

    print(f"  Data prepared: {len(df):,} records, {len(df.columns)} columns")
    return df


def sync_to_supabase(supabase, df, batch_size=500):
    """Sync data to Supabase player_rankings table using upsert"""
    print(f"\nSyncing {len(df):,} records to Supabase...")

    records = df.to_dict('records')
    total_batches = (len(records) + batch_size - 1) // batch_size

    success_count = 0
    error_count = 0
    start_time = time.time()

    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = i // batch_size + 1

        try:
            # Upsert (insert or update on conflict)
            result = supabase.table('player_rankings').upsert(
                batch,
                on_conflict='player_id'
            ).execute()

            success_count += len(batch)

            # Progress update every 10 batches
            if batch_num % 10 == 0 or batch_num == total_batches:
                elapsed = time.time() - start_time
                rate = success_count / elapsed if elapsed > 0 else 0
                print(f"  Batch {batch_num}/{total_batches}: {success_count:,} records ({rate:.0f}/sec)")

        except Exception as e:
            error_count += len(batch)
            print(f"  ERROR in batch {batch_num}: {str(e)[:100]}")

            # Try individual inserts for failed batch
            for record in batch:
                try:
                    supabase.table('player_rankings').upsert(
                        record,
                        on_conflict='player_id'
                    ).execute()
                    success_count += 1
                    error_count -= 1
                except:
                    pass

    elapsed = time.time() - start_time
    print(f"\nSync complete:")
    print(f"  Success: {success_count:,} records")
    print(f"  Errors:  {error_count:,} records")
    print(f"  Time:    {elapsed:.1f}s ({success_count/elapsed:.0f} records/sec)")

    return success_count, error_count


def verify_sync(supabase, bq_client):
    """Verify sync by comparing counts and sample data"""
    print("\nVerifying sync...")

    # Get BigQuery count
    bq_query = f"SELECT COUNT(*) as cnt FROM `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.{BQ_TABLE_ID}`"
    bq_count = bq_client.query(bq_query).to_dataframe().iloc[0]['cnt']

    # Get Supabase count
    result = supabase.table('player_rankings').select('player_id', count='exact').execute()
    sb_count = result.count

    print(f"  BigQuery records:  {bq_count:,}")
    print(f"  Supabase records:  {sb_count:,}")

    if bq_count == sb_count:
        print("  Status: VERIFIED - counts match!")
        return True
    else:
        diff = bq_count - sb_count
        print(f"  Status: MISMATCH - difference of {diff:,} records")
        return False


def get_sync_status(supabase):
    """Get current sync status"""
    try:
        result = supabase.table('player_rankings').select(
            'synced_at'
        ).order('synced_at', desc=True).limit(1).execute()

        if result.data:
            last_sync = result.data[0]['synced_at']
            print(f"Last sync: {last_sync}")
            return last_sync
    except Exception as e:
        print(f"Could not get sync status: {e}")
    return None


def main():
    """Main sync function"""
    print("=" * 60)
    print("PLAYER RANKINGS SYNC: BigQuery -> Supabase")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Parse args
    full_sync = '--full' in sys.argv
    delta_sync = '--delta' in sys.argv
    test_mode = '--test' in sys.argv

    if test_mode:
        print("\n*** TEST MODE: Only syncing 1000 records ***\n")

    try:
        # Setup
        supabase, bq_client = setup_connections()

        # Check current status
        get_sync_status(supabase)

        # Extract from BigQuery
        limit = 1000 if test_mode else None
        df = get_bigquery_data(bq_client, limit=limit)

        if df.empty:
            print("No data to sync!")
            return

        # Prepare data
        df = prepare_data_for_supabase(df)

        # Sync to Supabase
        success, errors = sync_to_supabase(supabase, df)

        # Verify
        if not test_mode:
            verify_sync(supabase, bq_client)

        print("\n" + "=" * 60)
        print("SYNC COMPLETE")
        print("=" * 60)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

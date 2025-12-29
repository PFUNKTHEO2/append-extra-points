"""
Sync Player Rankings from BigQuery to Supabase
Cloud Run Job version - runs as a containerized job
"""

import os
import pandas as pd
from supabase import create_client, Client
from google.cloud import bigquery
import time
from datetime import datetime, timezone

# Configuration from environment variables
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xqkwvywcxmnfimkubtyo.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

BQ_PROJECT_ID = "prodigy-ranking"
BQ_DATASET_ID = "algorithm_core"

# Columns from player_cumulative_points (base table)
BASE_COLUMNS = [
    "player_id", "player_name", "position", "birth_year", "nationality_name",
    "current_team", "current_league", "team_country", "current_season",
    "total_points", "performance_total", "direct_load_total",
    "f01_views", "f02_height", "f03_current_goals_f", "f04_current_goals_d",
    "f05_current_assists", "f06_current_gaa", "f07_current_svp",
    "f08_last_goals_f", "f09_last_goals_d", "f10_last_assists",
    "f11_last_gaa", "f12_last_svp", "f13_league_points", "f14_team_points",
    "f15_international_points", "f16_commitment_points", "f17_draft_points",
    "f18_weekly_points_delta", "f19_weekly_assists_delta", "f20_playing_up_points",
    "f21_tournament_points", "f22_manual_points", "f23_prodigylikes_points",
    "f24_card_sales_points", "f25_weekly_views", "f26_weight_points", "f27_bmi_points",
    "calculated_at", "algorithm_version"
]

# EA-style rating columns
RATING_COLUMNS = [
    "overall_rating", "performance_rating", "level_rating", "visibility_rating",
    "achievements_rating", "trending_rating", "physical_rating",
    "perf", "lvl", "vis", "ach", "trd", "phy"
]

# Percentile columns for radar charts
PERCENTILE_COLUMNS = [
    "performance_percentile", "level_percentile", "visibility_percentile",
    "achievements_percentile", "physical_percentile", "trending_percentile",
    "overall_percentile"
]


def setup_connections():
    """Set up Supabase and BigQuery connections"""
    print("Setting up connections...")

    if not SUPABASE_KEY:
        raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable required")

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("  Supabase connected")

    bq_client = bigquery.Client(project=BQ_PROJECT_ID)
    print("  BigQuery connected")

    return supabase, bq_client


def get_bigquery_data(bq_client):
    """Extract player data from BigQuery with ratings and percentiles"""
    print("\nExtracting data from BigQuery...")

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
        FROM `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.player_cumulative_points` p
        LEFT JOIN `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.player_card_ratings` r
            ON p.player_id = r.player_id
        LEFT JOIN `{BQ_PROJECT_ID}.{BQ_DATASET_ID}.player_category_percentiles` pct
            ON p.player_id = pct.player_id
        ORDER BY p.total_points DESC
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
            first_val = df[col].dropna().iloc[0] if len(df[col].dropna()) > 0 else None
            if first_val is not None and hasattr(first_val, 'as_tuple'):
                df[col] = df[col].apply(lambda x: float(x) if x is not None and hasattr(x, 'as_tuple') else x)

        if df[col].dtype == 'float64' or str(df[col].dtype).startswith('float'):
            df[col] = df[col].fillna(0).round(2)
        elif df[col].dtype == 'object':
            df[col] = df[col].fillna('')

    # Ensure player_id is integer
    df['player_id'] = df['player_id'].astype(int)

    # Add sync timestamp
    df['synced_at'] = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')

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
            result = supabase.table('player_rankings').upsert(
                batch,
                on_conflict='player_id'
            ).execute()

            success_count += len(batch)

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


def main():
    """Main sync function"""
    print("=" * 60)
    print("PLAYER RANKINGS SYNC: BigQuery -> Supabase")
    print("=" * 60)
    print(f"Started at: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")

    try:
        supabase, bq_client = setup_connections()
        df = get_bigquery_data(bq_client)

        if df.empty:
            print("No data to sync!")
            return

        df = prepare_data_for_supabase(df)
        success, errors = sync_to_supabase(supabase, df)

        print("\n" + "=" * 60)
        print(f"SYNC COMPLETE - {success:,} records synced")
        print("=" * 60)

        # Exit with error if too many failures
        if errors > 100:
            exit(1)

    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)


if __name__ == "__main__":
    main()

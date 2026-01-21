"""
NEPSAC Full Database Refresh
============================
Updates player_season_stats with fresh EP data for the current season,
then refreshes performance factors and rebuilds cumulative points.

Updated: 2026-01-21 - Migrated to v_latest_player_stats view architecture
- Stats are now written to player_season_stats (source of truth)
- v_latest_player_stats view automatically derives "latest" stats
- player_stats is used for metadata only (name, position, yearOfBirth)
"""

import os
import csv
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"


def log(message: str, level: str = "INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")


def load_ep_comparison_data(filepath: str):
    """Load the EP comparison data with fresh stats."""
    players = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('ep_found', '').lower() == 'true' and row.get('player_id'):
                player = {
                    'player_id': int(row['player_id']),
                    'ep_gp': int(row.get('ep_gp', 0) or 0),
                    'ep_goals': int(row.get('ep_goals', 0) or 0),
                    'ep_assists': int(row.get('ep_assists', 0) or 0),
                    'ep_points': int(row.get('ep_points', 0) or 0),
                    'ep_team': row.get('ep_team', ''),
                    'ep_league': row.get('ep_league', ''),
                }
                players.append(player)
    return players


def update_player_season_stats(players, client):
    """
    Update player_season_stats with fresh EP data for current season.
    This is the new approach - write to player_season_stats, not player_stats.latestStats.
    The v_latest_player_stats view will automatically reflect the changes.
    """
    log(f"Updating player_season_stats for {len(players)} players...")

    # Create temp table with updates
    temp_table = f"{PROJECT_ID}.{DATASET}.temp_season_stats_update"

    # Schema for temp table
    schema = [
        bigquery.SchemaField("player_id", "INT64"),
        bigquery.SchemaField("gp", "INT64"),
        bigquery.SchemaField("goals", "INT64"),
        bigquery.SchemaField("assists", "INT64"),
        bigquery.SchemaField("points", "INT64"),
        bigquery.SchemaField("team_name", "STRING"),
        bigquery.SchemaField("league_name", "STRING"),
    ]

    # Create temp table
    table_ref = bigquery.Table(temp_table, schema=schema)
    table_ref = client.create_table(table_ref, exists_ok=True)

    # Prepare records
    records = []
    for p in players:
        records.append({
            'player_id': p['player_id'],
            'gp': p['ep_gp'],
            'goals': p['ep_goals'],
            'assists': p['ep_assists'],
            'points': p['ep_points'],
            'team_name': p['ep_team'],
            'league_name': p['ep_league'],
        })

    # Insert into temp table
    log("Inserting fresh stats into temp table...")
    errors = client.insert_rows_json(temp_table, records)
    if errors:
        log(f"Errors inserting: {errors[:5]}", "ERROR")
        return 0

    # MERGE into player_season_stats for current season (2025-2026)
    # This updates existing records or inserts new ones
    log("Merging into player_season_stats for 2025-2026 season...")
    merge_query = f"""
    MERGE `{PROJECT_ID}.{DATASET}.player_season_stats` pss
    USING (
        SELECT
            src.player_id,
            src.gp,
            src.goals,
            src.assists,
            src.points,
            src.team_name,
            src.league_name,
            ROW_NUMBER() OVER (PARTITION BY src.player_id ORDER BY src.points DESC, src.gp DESC) as rn
        FROM `{temp_table}` src
    ) src
    ON pss.player_id = src.player_id
       AND pss.season_start_year = 2025
       AND pss.team_name = src.team_name
       AND src.rn = 1
    WHEN MATCHED THEN UPDATE SET
        pss.gp = src.gp,
        pss.goals = src.goals,
        pss.assists = src.assists,
        pss.points = src.points,
        pss.loadts = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED AND src.rn = 1 THEN INSERT
        (player_id, season_slug, season_start_year, team_name, league_name,
         gp, goals, assists, points, loadts)
    VALUES
        (src.player_id, '2025-2026', 2025, src.team_name, src.league_name,
         src.gp, src.goals, src.assists, src.points, CURRENT_TIMESTAMP())
    """

    job = client.query(merge_query)
    result = job.result()
    affected = job.num_dml_affected_rows

    log(f"Merged {affected} player_season_stats records")

    # Clean up temp table
    client.delete_table(temp_table, not_found_ok=True)

    return affected


def refresh_performance_factors(client):
    """
    Refresh the performance factor tables (F03-F05) for current season.
    Now uses v_latest_player_stats view instead of player_stats.latestStats_*.
    """
    log("Refreshing performance factors F03, F04, F05 using v_latest_player_stats view...")

    # F03: Current Goals Per Game - Forwards
    # Uses v_latest_player_stats view joined with player_stats for metadata
    f03_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F03_CGPGF` AS
    SELECT
      pm.id AS player_id,
      pm.name AS player_name,
      pm.position,
      pm.yearOfBirth AS birth_year,
      v.season_slug AS current_season,
      v.season_start_year AS season_year,
      v.team_name AS current_team,
      v.league_name AS current_league,
      CAST(v.gp AS INT64) AS games_played,
      CAST(v.goals AS INT64) AS goals,
      ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64),
            CAST(v.gp AS FLOAT64)), 4) AS goals_per_game,
      LEAST(ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64),
            CAST(v.gp AS FLOAT64)) / 2.0 * 500, 2), 500.0) AS factor_3_current_goals_points,
      CURRENT_TIMESTAMP() AS calculated_at,
      'v2.5-nepsac' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
    INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
    WHERE pm.position = 'F'
      AND CAST(v.gp AS INT64) >= 5
      AND v.goals IS NOT NULL
    """

    job = client.query(f03_query)
    job.result()
    log("F03 (Current Goals Forwards) refreshed")

    # F04: Current Goals Per Game - Defensemen
    f04_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F04_CGPGD` AS
    SELECT
      pm.id AS player_id,
      pm.name AS player_name,
      pm.position,
      pm.yearOfBirth AS birth_year,
      v.season_slug AS current_season,
      v.season_start_year AS season_year,
      v.team_name AS current_team,
      v.league_name AS current_league,
      CAST(v.gp AS INT64) AS games_played,
      CAST(v.goals AS INT64) AS goals,
      ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64),
            CAST(v.gp AS FLOAT64)), 4) AS goals_per_game,
      LEAST(ROUND(SAFE_DIVIDE(CAST(v.goals AS FLOAT64),
            CAST(v.gp AS FLOAT64)) / 1.5 * 500, 2), 500.0) AS factor_4_current_goals_points,
      CURRENT_TIMESTAMP() AS calculated_at,
      'v2.5-nepsac' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
    INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
    WHERE pm.position = 'D'
      AND CAST(v.gp AS INT64) >= 5
      AND v.goals IS NOT NULL
    """

    job = client.query(f04_query)
    job.result()
    log("F04 (Current Goals Defensemen) refreshed")

    # F05: Current Assists Per Game - All Skaters
    f05_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F05_CAPG` AS
    SELECT
      pm.id AS player_id,
      pm.name AS player_name,
      pm.position,
      pm.yearOfBirth AS birth_year,
      v.season_slug AS current_season,
      v.season_start_year AS season_year,
      v.team_name AS current_team,
      v.league_name AS current_league,
      CAST(v.gp AS INT64) AS games_played,
      CAST(v.assists AS INT64) AS assists,
      ROUND(SAFE_DIVIDE(CAST(v.assists AS FLOAT64),
            CAST(v.gp AS FLOAT64)), 4) AS assists_per_game,
      LEAST(ROUND(SAFE_DIVIDE(CAST(v.assists AS FLOAT64),
            CAST(v.gp AS FLOAT64)) / 2.5 * 500, 2), 500.0) AS factor_5_current_assists_points,
      CURRENT_TIMESTAMP() AS calculated_at,
      'v2.5-nepsac' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
    INNER JOIN `prodigy-ranking.algorithm_core.player_stats` pm ON v.player_id = pm.id
    WHERE pm.position IN ('F', 'D')
      AND CAST(v.gp AS INT64) >= 5
      AND v.assists IS NOT NULL
    """

    job = client.query(f05_query)
    job.result()
    log("F05 (Current Assists) refreshed")


def rebuild_cumulative_points(client):
    """
    Rebuild player_cumulative_points table with updated factors.
    This is a simplified rebuild that updates the performance factors.
    """
    log("Rebuilding player_cumulative_points with fresh performance factors...")

    # Update performance factors in cumulative points table
    update_query = """
    UPDATE `prodigy-ranking.algorithm_core.player_cumulative_points` pc
    SET
        f03_current_goals_f = COALESCE(f03.factor_3_current_goals_points, 0),
        performance_total = COALESCE(f03.factor_3_current_goals_points, pc.f03_current_goals_f, 0) +
                           COALESCE(pc.f04_current_goals_d, 0) +
                           COALESCE(pc.f05_current_assists, 0) +
                           COALESCE(pc.f06_current_gaa, 0) +
                           COALESCE(pc.f07_current_svp, 0) +
                           COALESCE(pc.f08_last_goals_f, 0) +
                           COALESCE(pc.f09_last_goals_d, 0) +
                           COALESCE(pc.f10_last_assists, 0) +
                           COALESCE(pc.f11_last_gaa, 0) +
                           COALESCE(pc.f12_last_svp, 0),
        calculated_at = CURRENT_TIMESTAMP()
    FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF` f03
    WHERE pc.player_id = f03.player_id
    """

    job = client.query(update_query)
    job.result()
    f03_updated = job.num_dml_affected_rows
    log(f"Updated F03 for {f03_updated} forwards")

    # Update F04 for defensemen
    update_query_f04 = """
    UPDATE `prodigy-ranking.algorithm_core.player_cumulative_points` pc
    SET
        f04_current_goals_d = COALESCE(f04.factor_4_current_goals_points, 0),
        performance_total = COALESCE(pc.f03_current_goals_f, 0) +
                           COALESCE(f04.factor_4_current_goals_points, pc.f04_current_goals_d, 0) +
                           COALESCE(pc.f05_current_assists, 0) +
                           COALESCE(pc.f06_current_gaa, 0) +
                           COALESCE(pc.f07_current_svp, 0) +
                           COALESCE(pc.f08_last_goals_f, 0) +
                           COALESCE(pc.f09_last_goals_d, 0) +
                           COALESCE(pc.f10_last_assists, 0) +
                           COALESCE(pc.f11_last_gaa, 0) +
                           COALESCE(pc.f12_last_svp, 0),
        calculated_at = CURRENT_TIMESTAMP()
    FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD` f04
    WHERE pc.player_id = f04.player_id
    """

    job = client.query(update_query_f04)
    job.result()
    f04_updated = job.num_dml_affected_rows
    log(f"Updated F04 for {f04_updated} defensemen")

    # Update F05 for all skaters
    update_query_f05 = """
    UPDATE `prodigy-ranking.algorithm_core.player_cumulative_points` pc
    SET
        f05_current_assists = COALESCE(f05.factor_5_current_assists_points, 0),
        performance_total = COALESCE(pc.f03_current_goals_f, 0) +
                           COALESCE(pc.f04_current_goals_d, 0) +
                           COALESCE(f05.factor_5_current_assists_points, pc.f05_current_assists, 0) +
                           COALESCE(pc.f06_current_gaa, 0) +
                           COALESCE(pc.f07_current_svp, 0) +
                           COALESCE(pc.f08_last_goals_f, 0) +
                           COALESCE(pc.f09_last_goals_d, 0) +
                           COALESCE(pc.f10_last_assists, 0) +
                           COALESCE(pc.f11_last_gaa, 0) +
                           COALESCE(pc.f12_last_svp, 0),
        calculated_at = CURRENT_TIMESTAMP()
    FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG` f05
    WHERE pc.player_id = f05.player_id
    """

    job = client.query(update_query_f05)
    job.result()
    f05_updated = job.num_dml_affected_rows
    log(f"Updated F05 for {f05_updated} skaters")

    # Recalculate total_points
    log("Recalculating total_points...")
    total_query = """
    UPDATE `prodigy-ranking.algorithm_core.player_cumulative_points`
    SET total_points = COALESCE(performance_total, 0) + COALESCE(direct_load_total, 0)
    WHERE TRUE
    """

    job = client.query(total_query)
    job.result()
    log(f"Recalculated total_points for all players")

    return f03_updated + f04_updated + f05_updated


def verify_refresh(client, sample_player_ids):
    """Verify the refresh by checking sample players."""
    ids_str = ','.join(str(pid) for pid in sample_player_ids[:5])

    query = f"""
    SELECT
        pc.player_id,
        pc.player_name,
        pc.f03_current_goals_f,
        pc.f04_current_goals_d,
        pc.f05_current_assists,
        pc.performance_total,
        pc.total_points,
        pc.calculated_at
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points` pc
    WHERE pc.player_id IN ({ids_str})
    ORDER BY pc.total_points DESC
    """

    results = client.query(query).result()
    return [dict(row) for row in results]


def main():
    print("=" * 70)
    print("NEPSAC FULL DATABASE REFRESH")
    print("Using v_latest_player_stats view architecture")
    print("=" * 70)

    client = bigquery.Client(project=PROJECT_ID)

    # Load fresh EP data
    csv_path = os.path.join(os.path.dirname(__file__), "nepsac_ep_comparison.csv")
    log(f"Loading fresh EP stats from {csv_path}...")
    players = load_ep_comparison_data(csv_path)
    log(f"Loaded {len(players)} players with fresh EP data")

    # Step 1: Update player_season_stats (new approach)
    log("\n" + "=" * 50)
    log("STEP 1: Updating player_season_stats (source of truth)")
    log("=" * 50)
    updated = update_player_season_stats(players, client)

    # Step 2: Refresh performance factors (now uses v_latest_player_stats view)
    log("\n" + "=" * 50)
    log("STEP 2: Refreshing performance factors (F03-F05) via view")
    log("=" * 50)
    refresh_performance_factors(client)

    # Step 3: Rebuild cumulative points
    log("\n" + "=" * 50)
    log("STEP 3: Rebuilding cumulative points")
    log("=" * 50)
    total_updated = rebuild_cumulative_points(client)

    # Step 4: Verify
    log("\n" + "=" * 50)
    log("STEP 4: Verification")
    log("=" * 50)
    player_ids = [p['player_id'] for p in players]
    verified = verify_refresh(client, player_ids)

    log("Sample verified records:")
    for v in verified:
        log(f"  {v['player_name']}: F03={v['f03_current_goals_f']}, F05={v['f05_current_assists']}, "
            f"Perf={v['performance_total']}, Total={v['total_points']}")

    print("\n" + "=" * 70)
    print("REFRESH COMPLETE!")
    print(f"  - Updated {updated} player_season_stats records")
    print(f"  - Refreshed performance factors via v_latest_player_stats view")
    print(f"  - Updated {total_updated} cumulative points records")
    print("=" * 70)


if __name__ == "__main__":
    main()

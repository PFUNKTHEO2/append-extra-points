#!/usr/bin/env python3
"""
Weekly Delta Pipeline for F18/F19/F25
======================================
This pipeline calculates weekly changes in goals, assists, and EP views,
then updates the corresponding factor tables.

Updated: 2026-01-21 - Migrated to v_latest_player_stats view architecture
- Snapshots now taken from v_latest_player_stats view (derived from player_season_stats)
- player_stats is used only for metadata (name, position, yearOfBirth, views)

Schedule: Run weekly (e.g., Monday morning after EliteProspects data refresh)

Steps:
1. Create a snapshot of current v_latest_player_stats + player_stats metadata
2. Calculate deltas by comparing to previous week's snapshot
3. Update PT_F18 (goals: 40 pts/goal, max 200)
4. Update PT_F19 (assists: 25 pts/assist, max 125)
5. Update PT_F25 (views: 1 pt/view, no cap)
6. Rebuild player_cumulative_points

Usage:
    python weekly_delta_pipeline.py                    # Full pipeline
    python weekly_delta_pipeline.py --snapshot-only    # Just take snapshot
    python weekly_delta_pipeline.py --delta-only       # Calculate deltas (skip snapshot)
    python weekly_delta_pipeline.py --dry-run          # Show what would be done
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
import argparse
import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


class WeeklyDeltaPipeline:
    def __init__(self, project_id='prodigy-ranking', dataset='algorithm_core', dry_run=False):
        self.project_id = project_id
        self.dataset = dataset
        self.dry_run = dry_run
        self.client = bigquery.Client(project=project_id)
        self.timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.snapshot_id = f"snapshot-{datetime.now().strftime('%Y-%m-%d')}"

    def log(self, message, level='INFO'):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        prefix = '[DRY-RUN] ' if self.dry_run else ''
        print(f"{timestamp} [{level}] {prefix}{message}")

    def execute_query(self, query, description=""):
        """Execute a query, respecting dry-run mode"""
        if self.dry_run:
            self.log(f"Would execute: {description}")
            self.log(f"Query preview: {query[:200]}...")
            return None
        else:
            self.log(f"Executing: {description}")
            job = self.client.query(query)
            result = job.result()
            return result

    def get_latest_snapshot(self):
        """Get the most recent snapshot ID from player_stats_history"""
        query = f"""
        SELECT snapshot_id, MAX(snapshot_date) as snapshot_date
        FROM `{self.project_id}.{self.dataset}.player_stats_history`
        GROUP BY snapshot_id
        ORDER BY snapshot_date DESC
        LIMIT 1
        """
        result = self.client.query(query).to_dataframe()
        if len(result) > 0:
            return result.iloc[0]['snapshot_id'], result.iloc[0]['snapshot_date']
        return None, None

    def step1_create_snapshot(self):
        """
        Step 1: Create a snapshot of current stats from v_latest_player_stats view
        combined with player_stats metadata.

        This is the new approach - stats come from player_season_stats (via view),
        metadata comes from player_stats.
        """
        self.log("=" * 70)
        self.log("STEP 1: Creating weekly snapshot from v_latest_player_stats view")
        self.log("=" * 70)

        # Check if today's snapshot already exists
        existing_check = f"""
        SELECT COUNT(*) as cnt
        FROM `{self.project_id}.{self.dataset}.player_stats_history`
        WHERE snapshot_id = '{self.snapshot_id}'
        """
        result = self.client.query(existing_check).to_dataframe()
        if result.iloc[0]['cnt'] > 0:
            self.log(f"Snapshot {self.snapshot_id} already exists, skipping creation", "WARN")
            return self.snapshot_id

        # Get current week boundaries
        today = datetime.now().date()
        week_start = today - timedelta(days=today.weekday())  # Monday
        week_end = week_start + timedelta(days=6)  # Sunday

        # Create snapshot from v_latest_player_stats view joined with player_stats metadata
        # This replaces the old approach of reading from player_stats.latestStats_* columns
        snapshot_query = f"""
        INSERT INTO `{self.project_id}.{self.dataset}.player_stats_history`
        (snapshot_id, snapshot_date, snapshot_week_start, snapshot_week_end,
         player_id, player_name, position, yearofbirth, season_slug,
         season_start_year, season_end_year, team_id, team_name,
         league_slug, league_name, regular_GP, regular_G, regular_G_numeric,
         regular_A, regular_A_numeric, regular_PTS, regular_PTS_numeric,
         regular_PM, regular_PIM, regular_PPG, regular_GAA, regular_SVP,
         regular_SO, regular_W, regular_L, regular_T, regular_TOI,
         views, source_loadts, created_at)
        SELECT
            '{self.snapshot_id}' as snapshot_id,
            CURRENT_TIMESTAMP() as snapshot_date,
            DATE('{week_start}') as snapshot_week_start,
            DATE('{week_end}') as snapshot_week_end,
            CAST(v.player_id AS INT64) as player_id,
            pm.name as player_name,
            pm.position,
            pm.yearOfBirth as yearofbirth,
            v.season_slug as season_slug,
            v.season_start_year as season_start_year,
            CAST(v.season_start_year AS INT64) + 1 as season_end_year,
            v.team_id as team_id,
            v.team_name as team_name,
            v.league_slug as league_slug,
            v.league_name as league_name,
            CAST(v.gp AS INT64) as regular_GP,
            CAST(v.goals AS STRING) as regular_G,
            CAST(v.goals AS NUMERIC) as regular_G_numeric,
            CAST(v.assists AS STRING) as regular_A,
            CAST(v.assists AS NUMERIC) as regular_A_numeric,
            CAST(v.points AS STRING) as regular_PTS,
            CAST(v.points AS NUMERIC) as regular_PTS_numeric,
            CAST(v.plus_minus AS STRING) as regular_PM,
            CAST(v.pim AS STRING) as regular_PIM,
            CAST(SAFE_DIVIDE(v.points, v.gp) AS STRING) as regular_PPG,
            v.gaa as regular_GAA,
            v.svp as regular_SVP,
            NULL as regular_SO,  -- Not in view, add if needed
            NULL as regular_W,
            NULL as regular_L,
            NULL as regular_T,
            NULL as regular_TOI,
            pm.views,
            v.loadts as source_loadts,
            CURRENT_TIMESTAMP() as created_at
        FROM `{self.project_id}.{self.dataset}.v_latest_player_stats` v
        INNER JOIN `{self.project_id}.{self.dataset}.player_stats` pm
            ON v.player_id = pm.id
        """

        self.execute_query(snapshot_query, f"Creating snapshot {self.snapshot_id} from v_latest_player_stats view")

        # Verify snapshot creation
        if not self.dry_run:
            verify = f"""
            SELECT COUNT(*) as cnt
            FROM `{self.project_id}.{self.dataset}.player_stats_history`
            WHERE snapshot_id = '{self.snapshot_id}'
            """
            result = self.client.query(verify).to_dataframe()
            count = result.iloc[0]['cnt']
            self.log(f"Snapshot {self.snapshot_id} created with {count:,} players")

        return self.snapshot_id

    def step2_calculate_deltas(self):
        """Step 2: Calculate deltas between current and previous snapshot"""
        self.log("=" * 70)
        self.log("STEP 2: Calculating weekly deltas")
        self.log("=" * 70)

        # Get the two most recent snapshots
        snapshots_query = f"""
        SELECT DISTINCT snapshot_id, MAX(snapshot_date) as snapshot_date
        FROM `{self.project_id}.{self.dataset}.player_stats_history`
        GROUP BY snapshot_id
        ORDER BY snapshot_date DESC
        LIMIT 2
        """
        snapshots = self.client.query(snapshots_query).to_dataframe()

        if len(snapshots) < 2:
            self.log("Not enough snapshots for delta calculation (need at least 2)", "ERROR")
            return None

        current_snapshot = snapshots.iloc[0]['snapshot_id']
        previous_snapshot = snapshots.iloc[1]['snapshot_id']

        self.log(f"Comparing: {previous_snapshot} -> {current_snapshot}")

        # Calculate deltas and store in player_stats_delta
        delta_query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset}.player_stats_delta` AS
        WITH current_data AS (
            SELECT *
            FROM `{self.project_id}.{self.dataset}.player_stats_history`
            WHERE snapshot_id = '{current_snapshot}'
        ),
        previous_data AS (
            SELECT *
            FROM `{self.project_id}.{self.dataset}.player_stats_history`
            WHERE snapshot_id = '{previous_snapshot}'
        )
        SELECT
            CONCAT('{previous_snapshot}', '_to_', '{current_snapshot}') as delta_id,
            CURRENT_TIMESTAMP() as calculation_timestamp,
            '{previous_snapshot}' as snapshot_from_id,
            p.snapshot_date as snapshot_from_date,
            '{current_snapshot}' as snapshot_to_id,
            c.snapshot_date as snapshot_to_date,
            TIMESTAMP_DIFF(c.snapshot_date, p.snapshot_date, DAY) as days_between,
            c.player_id,
            c.player_name,
            c.position,
            c.yearofbirth,
            c.season_slug,
            c.team_name,
            c.league_name,
            -- Previous stats
            COALESCE(p.regular_GP, 0) as from_regular_GP,
            COALESCE(p.regular_G_numeric, 0) as from_regular_G,
            COALESCE(p.regular_A_numeric, 0) as from_regular_A,
            COALESCE(p.regular_PTS_numeric, 0) as from_regular_PTS,
            p.regular_GAA as from_regular_GAA,
            p.regular_SVP as from_regular_SVP,
            COALESCE(p.views, 0) as from_views,
            -- Current stats
            COALESCE(c.regular_GP, 0) as to_regular_GP,
            COALESCE(c.regular_G_numeric, 0) as to_regular_G,
            COALESCE(c.regular_A_numeric, 0) as to_regular_A,
            COALESCE(c.regular_PTS_numeric, 0) as to_regular_PTS,
            c.regular_GAA as to_regular_GAA,
            c.regular_SVP as to_regular_SVP,
            COALESCE(c.views, 0) as to_views,
            -- Deltas
            COALESCE(c.regular_GP, 0) - COALESCE(p.regular_GP, 0) as delta_GP,
            COALESCE(c.regular_G_numeric, 0) - COALESCE(p.regular_G_numeric, 0) as delta_G,
            COALESCE(c.regular_A_numeric, 0) - COALESCE(p.regular_A_numeric, 0) as delta_A,
            COALESCE(c.regular_PTS_numeric, 0) - COALESCE(p.regular_PTS_numeric, 0) as delta_PTS,
            COALESCE(c.views, 0) - COALESCE(p.views, 0) as delta_views
        FROM current_data c
        LEFT JOIN previous_data p ON c.player_id = p.player_id
        """

        self.execute_query(delta_query, "Calculating weekly deltas")

        # Show delta summary
        if not self.dry_run:
            summary = f"""
            SELECT
                COUNT(*) as total_players,
                SUM(CASE WHEN delta_G > 0 THEN 1 ELSE 0 END) as players_with_goals,
                SUM(CASE WHEN delta_A > 0 THEN 1 ELSE 0 END) as players_with_assists,
                SUM(CASE WHEN delta_views > 0 THEN 1 ELSE 0 END) as players_with_views,
                MAX(delta_G) as max_goals,
                MAX(delta_A) as max_assists,
                MAX(delta_views) as max_views
            FROM `{self.project_id}.{self.dataset}.player_stats_delta`
            """
            result = self.client.query(summary).to_dataframe()
            self.log(f"Delta summary:")
            self.log(f"  Total players: {result.iloc[0]['total_players']:,}")
            self.log(f"  Players with goals: {result.iloc[0]['players_with_goals']:,}")
            self.log(f"  Players with assists: {result.iloc[0]['players_with_assists']:,}")
            self.log(f"  Players with view increases: {result.iloc[0]['players_with_views']:,}")

        return True

    def step3_update_f18_goals(self):
        """Step 3a: Update PT_F18 weekly goals (40 pts/goal, max 200)"""
        self.log("=" * 70)
        self.log("STEP 3a: Updating PT_F18 (Weekly Goals: 40 pts/goal, max 200)")
        self.log("=" * 70)

        f18_query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset}.PT_F18_weekly_points_delta` AS
        SELECT
            player_id,
            player_name,
            position,
            yearofbirth,
            season_slug,
            team_name,
            league_name,
            snapshot_to_date as last_update_date,
            from_regular_G as previous_points,
            to_regular_G as current_points,
            GREATEST(delta_G, 0) as points_added_this_week,
            delta_GP as games_added_this_week,
            -- F18: 40 points per goal, capped at 200
            LEAST(GREATEST(CAST(delta_G AS NUMERIC), 0) * 40, 200) as factor_18_points,
            CURRENT_TIMESTAMP() as calculated_at,
            'v2.8-pipeline' as algorithm_version
        FROM `{self.project_id}.{self.dataset}.player_stats_delta`
        WHERE position IN ('F', 'D')  -- Only forwards and defenders score goals
        """

        self.execute_query(f18_query, "Updating PT_F18_weekly_points_delta")

        if not self.dry_run:
            verify = f"""
            SELECT COUNT(*) as cnt,
                   SUM(CASE WHEN factor_18_points > 0 THEN 1 ELSE 0 END) as with_points,
                   MAX(factor_18_points) as max_pts
            FROM `{self.project_id}.{self.dataset}.PT_F18_weekly_points_delta`
            """
            result = self.client.query(verify).to_dataframe()
            self.log(f"F18 updated: {result.iloc[0]['cnt']:,} players, {result.iloc[0]['with_points']:,} with points, max: {result.iloc[0]['max_pts']}")

    def step3_update_f19_assists(self):
        """Step 3b: Update PT_F19 weekly assists (25 pts/assist, max 125)"""
        self.log("=" * 70)
        self.log("STEP 3b: Updating PT_F19 (Weekly Assists: 25 pts/assist, max 125)")
        self.log("=" * 70)

        f19_query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset}.PT_F19_weekly_assists_delta` AS
        SELECT
            player_id,
            player_name,
            position,
            yearofbirth,
            season_slug,
            team_name,
            league_name,
            snapshot_to_date as last_update_date,
            from_regular_A as previous_assists,
            to_regular_A as current_assists,
            GREATEST(delta_A, 0) as assists_added_this_week,
            delta_GP as games_added_this_week,
            -- F19: 25 points per assist, capped at 125
            LEAST(GREATEST(CAST(delta_A AS NUMERIC), 0) * 25, 125) as factor_19_points,
            CURRENT_TIMESTAMP() as calculated_at,
            'v2.8-pipeline' as algorithm_version
        FROM `{self.project_id}.{self.dataset}.player_stats_delta`
        WHERE position IN ('F', 'D')  -- Only forwards and defenders get assists
        """

        self.execute_query(f19_query, "Updating PT_F19_weekly_assists_delta")

        if not self.dry_run:
            verify = f"""
            SELECT COUNT(*) as cnt,
                   SUM(CASE WHEN factor_19_points > 0 THEN 1 ELSE 0 END) as with_points,
                   MAX(factor_19_points) as max_pts
            FROM `{self.project_id}.{self.dataset}.PT_F19_weekly_assists_delta`
            """
            result = self.client.query(verify).to_dataframe()
            self.log(f"F19 updated: {result.iloc[0]['cnt']:,} players, {result.iloc[0]['with_points']:,} with points, max: {result.iloc[0]['max_pts']}")

    def step3_update_f25_views(self):
        """Step 3c: Update PT_F25 weekly EP views (1 pt/view, no cap)"""
        self.log("=" * 70)
        self.log("STEP 3c: Updating PT_F25 (Weekly EP Views: 1 pt/view, no cap)")
        self.log("=" * 70)

        f25_query = f"""
        CREATE OR REPLACE TABLE `{self.project_id}.{self.dataset}.PT_F25_weekly_views_delta` AS
        SELECT
            player_id,
            player_name,
            position,
            yearofbirth,
            season_slug,
            team_name,
            league_name,
            snapshot_to_date as last_update_date,
            from_views as previous_views,
            to_views as current_views,
            GREATEST(delta_views, 0) as views_added_this_week,
            -- F25: 1 point per view, capped at 200
            LEAST(GREATEST(CAST(delta_views AS NUMERIC), 0), 200) as factor_25_points,
            CURRENT_TIMESTAMP() as calculated_at,
            'v2.8-pipeline' as algorithm_version
        FROM `{self.project_id}.{self.dataset}.player_stats_delta`
        """

        self.execute_query(f25_query, "Updating PT_F25_weekly_views_delta")

        if not self.dry_run:
            verify = f"""
            SELECT COUNT(*) as cnt,
                   SUM(CASE WHEN factor_25_points > 0 THEN 1 ELSE 0 END) as with_points,
                   MAX(factor_25_points) as max_pts,
                   SUM(factor_25_points) as total_pts
            FROM `{self.project_id}.{self.dataset}.PT_F25_weekly_views_delta`
            """
            result = self.client.query(verify).to_dataframe()
            self.log(f"F25 updated: {result.iloc[0]['cnt']:,} players, {result.iloc[0]['with_points']:,} with points, max: {result.iloc[0]['max_pts']}, total: {result.iloc[0]['total_pts']:,}")

    def step4_rebuild_cumulative(self):
        """Step 4: Rebuild player_cumulative_points with updated factors"""
        self.log("=" * 70)
        self.log("STEP 4: Rebuilding player_cumulative_points")
        self.log("=" * 70)

        # Read the rebuild SQL from file
        rebuild_sql_path = 'rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql'
        try:
            with open(rebuild_sql_path, 'r') as f:
                rebuild_sql = f.read()
            self.execute_query(rebuild_sql, "Rebuilding player_cumulative_points")

            if not self.dry_run:
                verify = f"""
                SELECT COUNT(*) as cnt,
                       MAX(total_points) as max_total,
                       AVG(total_points) as avg_total
                FROM `{self.project_id}.{self.dataset}.player_cumulative_points`
                """
                result = self.client.query(verify).to_dataframe()
                self.log(f"Cumulative rebuilt: {result.iloc[0]['cnt']:,} players, max: {result.iloc[0]['max_total']:.0f}, avg: {result.iloc[0]['avg_total']:.0f}")
        except FileNotFoundError:
            self.log(f"Rebuild SQL file not found: {rebuild_sql_path}", "ERROR")
            self.log("Skipping cumulative rebuild - run manually if needed", "WARN")

    def run_full_pipeline(self):
        """Run the complete weekly delta pipeline"""
        start_time = datetime.now()
        self.log("=" * 70)
        self.log("WEEKLY DELTA PIPELINE - STARTING")
        self.log(f"Using v_latest_player_stats view architecture")
        self.log(f"Timestamp: {self.timestamp}")
        self.log(f"Dry Run: {self.dry_run}")
        self.log("=" * 70)

        try:
            # Step 1: Create snapshot
            self.step1_create_snapshot()

            # Step 2: Calculate deltas
            self.step2_calculate_deltas()

            # Step 3: Update factor tables
            self.step3_update_f18_goals()
            self.step3_update_f19_assists()
            self.step3_update_f25_views()

            # Step 4: Rebuild cumulative
            self.step4_rebuild_cumulative()

            # Summary
            elapsed = (datetime.now() - start_time).total_seconds()
            self.log("=" * 70)
            self.log("PIPELINE COMPLETE")
            self.log(f"Elapsed time: {elapsed:.1f} seconds")
            self.log("=" * 70)

            return True

        except Exception as e:
            self.log(f"Pipeline failed: {str(e)}", "ERROR")
            raise

    def run_snapshot_only(self):
        """Only create a snapshot, don't calculate deltas"""
        self.log("Running snapshot-only mode")
        self.step1_create_snapshot()

    def run_delta_only(self):
        """Calculate deltas and update factors (assumes snapshot exists)"""
        self.log("Running delta-only mode (skipping snapshot)")
        self.step2_calculate_deltas()
        self.step3_update_f18_goals()
        self.step3_update_f19_assists()
        self.step3_update_f25_views()
        self.step4_rebuild_cumulative()


def main():
    parser = argparse.ArgumentParser(description='Weekly Delta Pipeline for F18/F19/F25')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without executing')
    parser.add_argument('--snapshot-only', action='store_true', help='Only create snapshot, skip delta calculation')
    parser.add_argument('--delta-only', action='store_true', help='Skip snapshot, only calculate deltas')

    args = parser.parse_args()

    pipeline = WeeklyDeltaPipeline(dry_run=args.dry_run)

    if args.snapshot_only:
        pipeline.run_snapshot_only()
    elif args.delta_only:
        pipeline.run_delta_only()
    else:
        pipeline.run_full_pipeline()


if __name__ == "__main__":
    main()

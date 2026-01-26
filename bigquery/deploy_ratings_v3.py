"""
Deploy the canonical v3.0 ratings to BigQuery.

This script:
1. Rebuilds player_cumulative_points with F31-F36 ratings stored in the table
2. Updates the player_card_ratings view to read stored ratings + compute F37

Usage:
    python deploy_ratings_v3.py
"""

from google.cloud import bigquery
import os
import time

def deploy_ratings():
    """Deploy the v3.0 ratings to BigQuery."""

    client = bigquery.Client(project='prodigy-ranking')
    script_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 70)
    print("DEPLOYING CANONICAL RATINGS v3.0")
    print("=" * 70)
    print()
    print("This will:")
    print("  1. Rebuild player_cumulative_points with F31-F36 ratings")
    print("  2. Update player_card_ratings view to read stored ratings")
    print()
    print("Rating formulas (from spec):")
    print("  F31 Performance: 0.7*current + 0.3*last season per-game stats")
    print("  F32 Level: DL_league_category_points lookup")
    print("  F33 Visibility: Linear 100-15000 EP views -> 0-99")
    print("  F34 Physical: (F02+F26+F27)/600*99")
    print("  F35 Achievements: (F15+F16+F17+F21+F22)/1500*99")
    print("  F36 Trending: Skaters (F18+F19+F25)/250*99, Goalies F25/50*99")
    print("  F37 Overall: 3%F31 + 70%F32 + 19%F33 + 5%F34 + 3%F35")
    print()

    # Step 1: Rebuild the cumulative table with ratings
    print("-" * 70)
    print("STEP 1: Rebuilding player_cumulative_points table...")
    print("-" * 70)

    rebuild_sql_file = os.path.join(script_dir, 'rebuild_cumulative_with_ratings.sql')
    with open(rebuild_sql_file, 'r', encoding='utf-8') as f:
        rebuild_sql = f.read()

    print("Executing table rebuild (this may take a few minutes)...")
    start_time = time.time()

    job = client.query(rebuild_sql)
    job.result()  # Wait for completion

    elapsed = time.time() - start_time
    print(f"Table rebuilt in {elapsed:.1f} seconds")
    print()

    # Step 2: Update the view
    print("-" * 70)
    print("STEP 2: Updating player_card_ratings view...")
    print("-" * 70)

    view_sql_file = os.path.join(script_dir, 'create_ea_ratings_view_v5.sql')
    with open(view_sql_file, 'r', encoding='utf-8') as f:
        view_sql = f.read()

    print("Executing view update...")
    job = client.query(view_sql)
    job.result()
    print("View updated!")
    print()

    # Step 3: Verify deployment
    print("-" * 70)
    print("STEP 3: Verifying deployment...")
    print("-" * 70)

    # Check table has the new columns
    table_check_query = """
    SELECT
        COUNT(*) as total_players,
        COUNTIF(f31_performance_rating IS NOT NULL) as has_f31,
        COUNTIF(f32_level_rating IS NOT NULL) as has_f32,
        COUNTIF(f33_visibility_rating IS NOT NULL) as has_f33,
        COUNTIF(f34_physical_rating IS NOT NULL) as has_f34,
        COUNTIF(f35_achievements_rating IS NOT NULL) as has_f35,
        COUNTIF(f36_trending_rating IS NOT NULL) as has_f36
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    """

    result = client.query(table_check_query).result()
    for row in result:
        print(f"  Total players: {row.total_players:,}")
        print(f"  Players with F31 (Performance): {row.has_f31:,}")
        print(f"  Players with F32 (Level): {row.has_f32:,}")
        print(f"  Players with F33 (Visibility): {row.has_f33:,}")
        print(f"  Players with F34 (Physical): {row.has_f34:,}")
        print(f"  Players with F35 (Achievements): {row.has_f35:,}")
        print(f"  Players with F36 (Trending): {row.has_f36:,}")
    print()

    # Check view averages
    view_check_query = """
    SELECT
        COUNT(*) as total_players,
        ROUND(AVG(overall_rating), 1) as avg_overall,
        ROUND(AVG(performance_rating), 1) as avg_performance,
        ROUND(AVG(level_rating), 1) as avg_level,
        ROUND(AVG(visibility_rating), 1) as avg_visibility,
        ROUND(AVG(physical_rating), 1) as avg_physical,
        ROUND(AVG(achievements_rating), 1) as avg_achievements,
        ROUND(AVG(trending_rating), 1) as avg_trending,
        MAX(ratings_version) as version
    FROM `prodigy-ranking.algorithm_core.player_card_ratings`
    """

    print("View statistics:")
    result = client.query(view_check_query).result()
    for row in result:
        print(f"  Version: {row.version}")
        print(f"  Total players in view: {row.total_players:,}")
        print()
        print("  Average ratings:")
        print(f"    Overall (F37):      {row.avg_overall}")
        print(f"    Performance (F31):  {row.avg_performance}")
        print(f"    Level (F32):        {row.avg_level}")
        print(f"    Visibility (F33):   {row.avg_visibility}")
        print(f"    Physical (F34):     {row.avg_physical}")
        print(f"    Achievements (F35): {row.avg_achievements}")
        print(f"    Trending (F36):     {row.avg_trending}")

    print()
    print("=" * 70)
    print("DEPLOYMENT COMPLETE")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  1. Trigger sync to Supabase (automatic daily or manual)")
    print("  2. Verify frontend displays correct ratings")
    print()

if __name__ == '__main__':
    deploy_ratings()

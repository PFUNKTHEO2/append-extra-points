"""
Deploy the updated EA ratings view v2 to BigQuery
"""
from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

# Read the SQL file
with open('create_ea_ratings_view_v2.sql', 'r') as f:
    sql = f.read()

print("Deploying updated EA ratings view v2...")
print("=" * 60)

try:
    # Execute the CREATE OR REPLACE VIEW statement
    job = client.query(sql)
    job.result()  # Wait for completion

    print("SUCCESS: View deployed successfully!")
    print()

    # Verify the view was created and check some stats
    verify_query = """
    SELECT
      COUNT(*) as total_players,
      COUNT(CASE WHEN level_rating = 99 THEN 1 END) as level_99,
      COUNT(CASE WHEN level_rating = 95 THEN 1 END) as level_95,
      ROUND(AVG(overall_rating), 1) as avg_overall,
      ROUND(AVG(level_rating), 1) as avg_level,
      ROUND(AVG(physical_rating), 1) as avg_physical,
      MAX(physical_rating) as max_physical,
      MAX(f15_international_points) as max_f15,
      MAX(f02_height) as max_f02
    FROM `prodigy-ranking.algorithm_core.player_card_ratings`
    """

    result = client.query(verify_query).to_dataframe()

    print("=== Verification Results ===")
    print(f"Total Players Rated: {result['total_players'].values[0]:,}")
    print(f"Players with Level = 99: {result['level_99'].values[0]}")
    print(f"Players with Level = 95: {result['level_95'].values[0]}")
    print(f"Avg Overall Rating: {result['avg_overall'].values[0]}")
    print(f"Avg Level Rating: {result['avg_level'].values[0]}")
    print(f"Avg Physical Rating: {result['avg_physical'].values[0]}")
    print(f"Max Physical Rating: {result['max_physical'].values[0]}")
    print(f"Max F15 International Points: {result['max_f15'].values[0]} (capped at 1000)")
    print(f"Max F02 Height Points: {result['max_f02'].values[0]} (capped at 200)")

    # Check NHL players specifically
    nhl_query = """
    SELECT player_name, current_league, level_rating, overall_rating, physical_rating
    FROM `prodigy-ranking.algorithm_core.player_card_ratings`
    WHERE current_league = 'NHL'
    """
    nhl_result = client.query(nhl_query).to_dataframe()
    print()
    print("=== NHL Players (should all have Level = 99) ===")
    print(nhl_result.to_string())

    # Check weight distribution
    weight_query = """
    SELECT
      CASE
        WHEN level_rating = 99 THEN 'NHL (99)'
        WHEN level_rating = 95 THEN 'CHL/KHL (95)'
        WHEN level_rating = 91 THEN 'Tier 3 (91)'
        WHEN level_rating = 87 THEN 'Tier 4 (87)'
        ELSE 'Other'
      END as tier,
      COUNT(*) as player_count,
      ROUND(AVG(overall_rating), 1) as avg_overall,
      ROUND(AVG(performance_rating), 1) as avg_perf,
      ROUND(AVG(physical_rating), 1) as avg_phys
    FROM `prodigy-ranking.algorithm_core.player_card_ratings`
    GROUP BY 1
    ORDER BY avg_overall DESC
    """
    weight_result = client.query(weight_query).to_dataframe()
    print()
    print("=== Rating Distribution by League Tier ===")
    print(weight_result.to_string())

except Exception as e:
    print(f"ERROR: {e}")
    raise

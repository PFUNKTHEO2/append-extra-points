from google.cloud import bigquery
import pandas as pd

# Connect to BigQuery
client = bigquery.Client(project="prodigy-ranking")

print("=" * 80)
print("VERIFYING FACTOR 14 REBUILD WITH NEW TEAM POINTS DATA")
print("=" * 80)
print()

# ============================================================================
# CHECK 1: Player Count Investigation
# ============================================================================
print("CHECK 1: Investigating Player Count")
print("-" * 80)

player_count_query = """
SELECT
  COUNT(*) as total_rows,
  COUNT(DISTINCT player_id) as unique_players
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""

player_count = client.query(player_count_query).to_dataframe()
print(player_count.to_string(index=False))
print()

if player_count['total_rows'].values[0] != player_count['unique_players'].values[0]:
    print("[WARNING] Total rows != unique players - There are DUPLICATES!")
    print()

    # Check for duplicates
    dup_query = """
    SELECT
      player_id,
      player_name,
      COUNT(*) as duplicate_count
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    GROUP BY player_id, player_name
    HAVING COUNT(*) > 1
    ORDER BY duplicate_count DESC
    LIMIT 10
    """

    duplicates = client.query(dup_query).to_dataframe()
    print("Sample of duplicate players:")
    print(duplicates.to_string(index=False))
    print()
else:
    print("[OK] No duplicates found - player count is correct")
    print()

# ============================================================================
# CHECK 2: Factor 14 Team Points Coverage
# ============================================================================
print("=" * 80)
print("CHECK 2: Factor 14 Team Points Coverage")
print("-" * 80)

f14_coverage_query = """
SELECT
  COUNT(DISTINCT player_id) as total_players,
  COUNT(DISTINCT CASE WHEN f14_team_points > 0 THEN player_id END) as players_with_f14,
  ROUND(COUNT(DISTINCT CASE WHEN f14_team_points > 0 THEN player_id END) * 100.0 / COUNT(DISTINCT player_id), 2) as coverage_percent,
  ROUND(AVG(f14_team_points), 2) as avg_f14_points,
  MIN(f14_team_points) as min_f14,
  MAX(f14_team_points) as max_f14,
  SUM(f14_team_points) as total_f14_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""

f14_coverage = client.query(f14_coverage_query).to_dataframe()
print("Factor 14 Coverage:")
print(f14_coverage.to_string(index=False))
print()

# ============================================================================
# CHECK 3: Test Specific Teams from Investigation
# ============================================================================
print("=" * 80)
print("CHECK 3: Testing Specific Teams")
print("-" * 80)

test_teams_query = """
WITH test_cases AS (
  SELECT DISTINCT
    player_id,
    player_name,
    current_team,
    f14_team_points
  FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
  WHERE current_team IN (
    'Guelph Storm',
    'Växjö Lakers HC U16 2',
    'Edmonton Jr. Oilers U18 AAA',
    'USNTDP Juniors',
    'Boston Univ.'
  )
)
SELECT
  current_team,
  COUNT(*) as player_count,
  MIN(f14_team_points) as min_points,
  MAX(f14_team_points) as max_points,
  ROUND(AVG(f14_team_points), 2) as avg_points,
  CASE
    WHEN MIN(f14_team_points) > 0 THEN '[MATCHED]'
    ELSE '[NO MATCH]'
  END as status
FROM test_cases
GROUP BY current_team
ORDER BY avg_points DESC
"""

test_teams = client.query(test_teams_query).to_dataframe()
print("Test Cases (from F14 investigation):")
print(test_teams.to_string(index=False))
print()

# ============================================================================
# CHECK 4: Top Teams by Player Count
# ============================================================================
print("=" * 80)
print("CHECK 4: Top Teams by Player Count")
print("-" * 80)

top_teams_query = """
SELECT DISTINCT
  current_team,
  current_league,
  COUNT(*) as player_count,
  ROUND(AVG(f14_team_points), 2) as avg_f14_points,
  CASE
    WHEN AVG(f14_team_points) > 0 THEN '[Has Points]'
    ELSE '[Zero Points]'
  END as points_status
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_team IS NOT NULL
GROUP BY current_team, current_league
ORDER BY player_count DESC
LIMIT 20
"""

top_teams = client.query(top_teams_query).to_dataframe()
print("Top 20 teams by player count:")
print(top_teams.to_string(index=False))
print()

# ============================================================================
# CHECK 5: Major Leagues Coverage (CHL, USHL, NCAA)
# ============================================================================
print("=" * 80)
print("CHECK 5: Major Leagues Team Points Coverage")
print("-" * 80)

major_leagues_query = """
SELECT
  CASE
    WHEN current_league = 'OHL' THEN 'OHL (Ontario Hockey League)'
    WHEN current_league = 'WHL' THEN 'WHL (Western Hockey League)'
    WHEN current_league = 'QMJHL' THEN 'QMJHL (Quebec Major Junior)'
    WHEN current_league = 'USHL' THEN 'USHL (United States Hockey League)'
    WHEN current_league LIKE '%NCAA%' THEN 'NCAA (College Hockey)'
    ELSE 'Other Major Leagues'
  END as league_group,
  COUNT(DISTINCT player_id) as total_players,
  COUNT(DISTINCT CASE WHEN f14_team_points > 0 THEN player_id END) as players_with_f14,
  ROUND(COUNT(DISTINCT CASE WHEN f14_team_points > 0 THEN player_id END) * 100.0 / COUNT(DISTINCT player_id), 2) as coverage_percent,
  ROUND(AVG(f14_team_points), 2) as avg_f14_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_league IN ('OHL', 'WHL', 'QMJHL', 'USHL')
   OR current_league LIKE '%NCAA%'
GROUP BY league_group
ORDER BY total_players DESC
"""

major_leagues = client.query(major_leagues_query).to_dataframe()
print("Major Leagues Coverage:")
print(major_leagues.to_string(index=False))
print()

# ============================================================================
# CHECK 6: Matching Examples
# ============================================================================
print("=" * 80)
print("CHECK 6: Normalized Matching Examples")
print("-" * 80)

matching_examples_query = """
SELECT DISTINCT
  current_team,
  f14_team_points,
  LOWER(TRIM(REGEXP_REPLACE(current_team, r' U[0-9]{2}.*| Jr.*| [0-9]$', ''))) as normalized_team_name
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE current_team LIKE '%U16%'
   OR current_team LIKE '%U17%'
   OR current_team LIKE '%U18%'
   OR current_team LIKE '%Jr.%'
ORDER BY f14_team_points DESC
LIMIT 15
"""

matching_examples = client.query(matching_examples_query).to_dataframe()
print("Age Group Suffix Matching Examples:")
print(matching_examples.to_string(index=False))
print()

# ============================================================================
# CHECK 7: Compare with Previous Backup
# ============================================================================
print("=" * 80)
print("CHECK 7: Comparison with Previous Rebuild")
print("-" * 80)

try:
    comparison_query = """
    WITH current_data AS (
      SELECT
        COUNT(DISTINCT player_id) as total_players,
        COUNT(DISTINCT CASE WHEN f14_team_points > 0 THEN player_id END) as players_with_f14,
        ROUND(AVG(f14_team_points), 2) as avg_f14,
        SUM(f14_team_points) as total_f14_points
      FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
    )
    SELECT
      total_players,
      players_with_f14,
      ROUND(players_with_f14 * 100.0 / total_players, 2) as coverage_percent,
      avg_f14,
      total_f14_points
    FROM current_data
    """

    comparison = client.query(comparison_query).to_dataframe()
    print("Current State:")
    print(comparison.to_string(index=False))
    print()

    print("Expected Results (from testing):")
    print("  - Coverage: ~55% (up from 25.3%)")
    print("  - Players with F14: ~90,000+ (up from 41,753)")
    print("  - Additional points: ~29 million")
    print()

except Exception as e:
    print(f"Could not retrieve comparison data: {e}")
    print()

# ============================================================================
# SUMMARY
# ============================================================================
print("=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)
print()

unique_players = player_count['unique_players'].values[0]
players_with_f14 = f14_coverage['players_with_f14'].values[0]
coverage_pct = f14_coverage['coverage_percent'].values[0]
avg_f14 = f14_coverage['avg_f14_points'].values[0]

print(f"Total unique players: {unique_players:,}")
print(f"Players with F14 points: {players_with_f14:,} ({coverage_pct}%)")
print(f"Average F14 points: {avg_f14:.2f}")
print()

if coverage_pct >= 50:
    print("[SUCCESS] Coverage meets expectations (>50%)")
else:
    print("[WARNING] Coverage below expectations")
    print(f"   Expected: ~55%, Actual: {coverage_pct}%")

print()
print("Key Findings:")
print("  1. Check for duplicate players above")
print("  2. Review test cases for specific teams")
print("  3. Verify major league coverage")
print()

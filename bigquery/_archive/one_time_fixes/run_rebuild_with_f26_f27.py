"""
Run the cumulative rebuild with F26 (Weight) and F27 (BMI) physical factors
"""

from google.cloud import bigquery

client = bigquery.Client()

print("="*60)
print("Rebuilding player_cumulative_points with F26/F27...")
print("="*60)

# Read and execute the rebuild SQL
with open("rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql", "r") as f:
    rebuild_sql = f.read()

job = client.query(rebuild_sql)
job.result()
print("Rebuild complete!")

# Verify the new columns exist
print("\n" + "="*60)
print("Verifying F26 and F27 columns in player_cumulative_points...")
print("="*60)

verify_sql = """
SELECT
  COUNT(*) as total_players,
  SUM(CASE WHEN f26_weight_points > 0 THEN 1 ELSE 0 END) as with_f26,
  SUM(CASE WHEN f27_bmi_points > 0 THEN 1 ELSE 0 END) as with_f27,
  SUM(CASE WHEN f26_weight_points > 0 AND f27_bmi_points > 0 THEN 1 ELSE 0 END) as with_both,
  ROUND(AVG(CASE WHEN f26_weight_points > 0 THEN f26_weight_points END), 1) as avg_f26,
  ROUND(AVG(CASE WHEN f27_bmi_points > 0 THEN f27_bmi_points END), 1) as avg_f27,
  MAX(f26_weight_points) as max_f26,
  MAX(f27_bmi_points) as max_f27
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""
result = client.query(verify_sql).to_dataframe()
row = result.iloc[0]
print(f"Total Players: {int(row['total_players']):,}")
print(f"With F26 (Weight) Points: {int(row['with_f26']):,}")
print(f"With F27 (BMI) Points: {int(row['with_f27']):,}")
print(f"With Both F26+F27: {int(row['with_both']):,}")
print(f"Avg F26: {row['avg_f26']}, Max F26: {int(row['max_f26'])}")
print(f"Avg F27: {row['avg_f27']}, Max F27: {int(row['max_f27'])}")

# Distribution by birth year
print("\n" + "="*60)
print("F26/F27 Distribution by Birth Year (2007-2010):")
print("="*60)
dist_sql = """
SELECT
  birth_year,
  COUNT(*) as total,
  SUM(CASE WHEN f26_weight_points > 0 THEN 1 ELSE 0 END) as with_f26,
  SUM(CASE WHEN f27_bmi_points > 0 THEN 1 ELSE 0 END) as with_f27,
  ROUND(AVG(f26_weight_points), 1) as avg_f26,
  ROUND(AVG(f27_bmi_points), 1) as avg_f27
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE birth_year BETWEEN 2007 AND 2010
GROUP BY birth_year
ORDER BY birth_year
"""
result = client.query(dist_sql).to_dataframe()
print(f"{'Year':<6} {'Total':>10} {'With F26':>10} {'With F27':>10} {'Avg F26':>8} {'Avg F27':>8}")
for _, row in result.iterrows():
    print(f"{int(row['birth_year']):<6} {int(row['total']):>10,} {int(row['with_f26']):>10,} {int(row['with_f27']):>10,} {row['avg_f26']:>8} {row['avg_f27']:>8}")

# Sample top players with physical points
print("\n" + "="*60)
print("Sample Top 2008 Players with Physical Points:")
print("="*60)
sample_sql = """
SELECT
  player_name,
  position,
  f26_weight_points,
  f27_bmi_points,
  f26_weight_points + f27_bmi_points as physical_total,
  total_points
FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
WHERE birth_year = 2008
  AND f26_weight_points > 0
  AND f27_bmi_points > 0
ORDER BY f26_weight_points + f27_bmi_points DESC
LIMIT 10
"""
result = client.query(sample_sql).to_dataframe()
for _, row in result.iterrows():
    print(f"  {row['player_name']}: F26={int(row['f26_weight_points'])}, F27={int(row['f27_bmi_points'])}, Total Physical={int(row['physical_total'])} ({row['position']}) - Total Points: {int(row['total_points'])}")

# Check algorithm version
print("\n" + "="*60)
print("Verify Algorithm Version:")
version_sql = """
SELECT DISTINCT algorithm_version FROM `prodigy-ranking.algorithm_core.player_cumulative_points`
"""
result = client.query(version_sql).to_dataframe()
print(f"Algorithm Version: {result.iloc[0]['algorithm_version']}")

print("\n" + "="*60)
print("DONE! F26 and F27 are now included in player_cumulative_points.")
print("="*60)

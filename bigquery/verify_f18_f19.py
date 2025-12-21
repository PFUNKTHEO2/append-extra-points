#!/usr/bin/env python3
"""
Verify F18 and F19 Weekly Points Calculations
==============================================
F18: 40 pts/goal, max 200
F19: 25 pts/assist, max 125
"""

from google.cloud import bigquery
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

client = bigquery.Client(project='prodigy-ranking')

print('='*70)
print('VERIFYING F18 AND F19 CALCULATIONS')
print('='*70)

# F18 Verification
print('\n[F18] Weekly Goals - 40 pts/goal, max 200')
print('-'*70)

f18_query = """
SELECT
  points_added_this_week as goals,
  factor_18_points as points_assigned,
  points_added_this_week * 40 as expected_raw,
  LEAST(points_added_this_week * 40, 200) as expected_capped,
  CASE
    WHEN factor_18_points = LEAST(points_added_this_week * 40, 200) THEN 'CORRECT'
    ELSE 'WRONG'
  END as status
FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
WHERE points_added_this_week > 0
ORDER BY points_added_this_week DESC
LIMIT 15
"""
f18_result = client.query(f18_query).to_dataframe()
print(f18_result.to_string(index=False))

# F18 Distribution
print('\n[F18] Distribution Summary:')
f18_dist = """
SELECT
  points_added_this_week as goals,
  COUNT(*) as num_players,
  MIN(factor_18_points) as min_pts,
  MAX(factor_18_points) as max_pts,
  LEAST(points_added_this_week * 40, 200) as expected_pts
FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
WHERE points_added_this_week > 0
GROUP BY points_added_this_week
ORDER BY points_added_this_week
"""
f18_dist_result = client.query(f18_dist).to_dataframe()
print(f18_dist_result.to_string(index=False))

# F19 Verification
print('\n' + '='*70)
print('[F19] Weekly Assists - 25 pts/assist, max 125')
print('-'*70)

f19_query = """
SELECT
  assists_added_this_week as assists,
  factor_19_points as points_assigned,
  assists_added_this_week * 25 as expected_raw,
  LEAST(assists_added_this_week * 25, 125) as expected_capped,
  CASE
    WHEN factor_19_points = LEAST(assists_added_this_week * 25, 125) THEN 'CORRECT'
    ELSE 'WRONG'
  END as status
FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
WHERE assists_added_this_week > 0
ORDER BY assists_added_this_week DESC
LIMIT 15
"""
f19_result = client.query(f19_query).to_dataframe()
print(f19_result.to_string(index=False))

# F19 Distribution
print('\n[F19] Distribution Summary:')
f19_dist = """
SELECT
  assists_added_this_week as assists,
  COUNT(*) as num_players,
  MIN(factor_19_points) as min_pts,
  MAX(factor_19_points) as max_pts,
  LEAST(assists_added_this_week * 25, 125) as expected_pts
FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
WHERE assists_added_this_week > 0
GROUP BY assists_added_this_week
ORDER BY assists_added_this_week
"""
f19_dist_result = client.query(f19_dist).to_dataframe()
print(f19_dist_result.to_string(index=False))

# Check for any incorrect values
print('\n' + '='*70)
print('VALIDATION CHECK - Any incorrect calculations?')
print('-'*70)

validation = """
SELECT
  'F18' as factor,
  COUNT(*) as incorrect_count
FROM `prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta`
WHERE points_added_this_week > 0
  AND factor_18_points != LEAST(points_added_this_week * 40, 200)

UNION ALL

SELECT
  'F19' as factor,
  COUNT(*) as incorrect_count
FROM `prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta`
WHERE assists_added_this_week > 0
  AND factor_19_points != LEAST(assists_added_this_week * 25, 125)
"""
val_result = client.query(validation).to_dataframe()
print(val_result.to_string(index=False))

# Summary
print('\n' + '='*70)
print('EXPECTED POINT VALUES:')
print('-'*70)
print('F18 (Goals):')
print('  1 goal  = 40 pts')
print('  2 goals = 80 pts')
print('  3 goals = 120 pts')
print('  4 goals = 160 pts')
print('  5+ goals = 200 pts (CAPPED)')
print('')
print('F19 (Assists):')
print('  1 assist  = 25 pts')
print('  2 assists = 50 pts')
print('  3 assists = 75 pts')
print('  4 assists = 100 pts')
print('  5+ assists = 125 pts (CAPPED)')
print('='*70)

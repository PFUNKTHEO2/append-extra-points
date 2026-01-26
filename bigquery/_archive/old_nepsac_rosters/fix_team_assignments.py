#!/usr/bin/env python3
"""Fix team assignments for players with known correct teams."""

from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

# Players who should be on Vermont Academy (currently on kents-hill due to alphabetical)
vermont_players = [
    'Brady Mulloy', 'Harrison Ooten', 'Hayden Postles', 'Kevin Summers',
    'Mathys Paradis', 'Xander Robertson'
]

# Check current assignments
check_query = """
SELECT roster_name, team_id
FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
WHERE season = '2025-26'
  AND roster_name IN ('Colin O\\'Leary', 'Brady Mulloy', 'Harrison Ooten',
                      'Hayden Postles', 'Kevin Summers', 'Mathys Paradis', 'Xander Robertson')
ORDER BY roster_name
"""
print('Current assignments for players with known correct teams:')
for row in client.query(check_query).result():
    print(f'  {row.roster_name}: {row.team_id}')

# Fix Colin O'Leary: rivers-school -> st-paul-s-school
print("\nFixing Colin O'Leary...")
client.query("""
UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
SET team_id = 'st-paul-s-school'
WHERE roster_name = "Colin O'Leary" AND season = '2025-26'
""").result()

# Fix Vermont Academy players: kents-hill -> vermont-academy
print('Fixing Vermont Academy players...')
for player in vermont_players:
    query = f"""
    UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
    SET team_id = 'vermont-academy'
    WHERE roster_name = "{player}" AND season = '2025-26'
    """
    client.query(query).result()
    print(f'  Fixed {player}')

# Verify
print('\nVerified assignments:')
for row in client.query(check_query).result():
    print(f'  {row.roster_name}: {row.team_id}')

# Show final team counts
print('\n=== FINAL ROSTER COUNTS ===')
count_query = """
SELECT team_id, COUNT(*) as count
FROM `prodigy-ranking.algorithm_core.nepsac_rosters`
WHERE season = '2025-26'
GROUP BY team_id
ORDER BY team_id
"""
total = 0
for row in client.query(count_query).result():
    print(f'  {row.team_id}: {row.count}')
    total += row.count
print(f'\nTotal: {total}')

print('\nDone!')

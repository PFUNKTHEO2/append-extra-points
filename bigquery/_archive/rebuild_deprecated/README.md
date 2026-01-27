# Deprecated Rebuild Scripts

**Deprecated Date:** 2026-01-26

These scripts were deprecated in favor of the canonical rebuild script.

## Current Active Script

**`rebuild_cumulative_with_ratings.sql`** - The CANONICAL rebuild script that includes:
- All factor points (F01-F28)
- All rating calculations (F31-F37)
- Raw per-game stats for transparency
- Uses correct table names (DL_F32_league_level_points for F13/F32)

## Deprecated Files

| File | Reason |
|------|--------|
| `rebuild_cumulative_after_goalie_fix.py` | One-time goalie fix, superseded |
| `rebuild_cumulative_with_fixes.sql` | Superseded by `rebuild_cumulative_with_ratings.sql` |
| `rebuild_cumulative_with_fixes_BACKUP_20251121.sql` | Old backup file |
| `rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql` | Superseded version |
| `rebuild_cumulative_with_new_f15.py` | References deprecated table `DL_F13_league_points` |

## Usage

To rebuild player_cumulative_points, run:

```python
from google.cloud import bigquery
client = bigquery.Client(project='prodigy-ranking')

with open('rebuild_cumulative_with_ratings.sql', 'r') as f:
    sql = f.read()

client.query(sql).result()
```

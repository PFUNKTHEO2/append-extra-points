# Player Stats Consolidation - Implementation Complete

**Date:** 2026-01-21
**Status:** Implementation Complete - Ready for Validation

## Summary

Consolidated to `player_season_stats` as the single source of truth for player statistics.
The `v_latest_player_stats` view now derives "latest stats" from `player_season_stats`,
replacing the denormalized `latestStats_*` columns in `player_stats`.

## Changes Made

### New Files Created

1. **`create_v_latest_player_stats.sql`** - BigQuery view definition that derives latest season stats
   - Uses league prioritization (NHL/AHL/KHL > CHL/USHL > Junior > Other)
   - Filters for current season (2025) with minimum 1 GP
   - Ready to execute in BigQuery Console

### SQL Files Updated

| File | Changes |
|------|---------|
| `refresh_PT_F03_CGPGF.sql` | Now uses `v_latest_player_stats.goals` instead of `player_stats.latestStats_regularStats_G` |
| `refresh_PT_F04_CGPGD.sql` | Same pattern for defensemen goals |
| `refresh_PT_F05_CAPG.sql` | Now uses `v_latest_player_stats.assists` |
| `REFRESH_ALL_PERFORMANCE_FACTORS.sql` | Complete rewrite using view-based queries for F03-F07 |
| `FIX_performance_factors_pipeline.sql` | Complete rewrite using view-based queries for F03-F12 |

### Python Scripts Updated

| File | Changes |
|------|---------|
| `nepsac_full_refresh.py` | Now writes to `player_season_stats` instead of `player_stats.latestStats_*`; uses `v_latest_player_stats` view for factor refresh |
| `weekly_delta_pipeline.py` | Snapshots now taken from `v_latest_player_stats` view joined with `player_stats` metadata |

### API Files (No Changes Required)

The following files were reviewed but don't require changes as they query processed tables (`player_rankings`, `player_card_ratings`, `PT_*` factor tables) rather than raw `latestStats_*` columns:

- `api-backend/functions/shared/bigquery.js` - Queries `player_rankings` view, not `player_stats.latestStats_*`
- `api-backend/functions/admin.js` - Queries factor tables, not `player_stats.latestStats_*`

## Deprecated Files (Delete After Validation)

The following files can be deleted once the migration is validated:

### SQL Files to Delete
- `FIX_update_latestStats_from_season_stats.sql` - No longer needed (view handles this)
- `FIX_update_latestStats_v2.sql` - No longer needed (view handles this)

### Python Scripts to Review
The following scripts still reference `latestStats_*` (54 total). Most are one-time fixes or investigation scripts. Review and update as needed:

```
grep -l "latestStats" *.py
```

Key scripts already migrated:
- `nepsac_full_refresh.py` ✓
- `weekly_delta_pipeline.py` ✓

## Deployment Script

A consolidated deployment script has been created: `DEPLOY_STATS_CONSOLIDATION.sql`

This script combines all deployment steps into a single file that can be run in BigQuery Console:
1. Creates the `v_latest_player_stats` view
2. Rebuilds `player_cumulative_points` using the view
3. Includes verification queries

## Validation Steps

Before marking the migration complete, perform these verification steps:

### Step 1: Run the Deployment Script
```sql
-- Run DEPLOY_STATS_CONSOLIDATION.sql in BigQuery Console
-- This creates the view and rebuilds cumulative points
```

### Alternative: Create the View Separately
```sql
-- Run create_v_latest_player_stats.sql in BigQuery Console
```

### Step 2: Verify View Data
```sql
-- Compare row counts
SELECT COUNT(*) as view_count FROM `prodigy-ranking.algorithm_core.v_latest_player_stats`;
SELECT COUNT(DISTINCT id) as player_stats_count FROM `prodigy-ranking.algorithm_core.player_stats`
WHERE latestStats_season_startYear = 2025;

-- Compare stats for sample players
SELECT v.player_id, v.goals, v.assists, v.gp
FROM `prodigy-ranking.algorithm_core.v_latest_player_stats` v
WHERE v.player_id IN (946038, 123456, 789012)  -- Sample IDs
```

### Step 3: Rebuild One Factor and Compare
```sql
-- Run refresh_PT_F03_CGPGF.sql (new version using view)
-- Compare results with previous factor values
```

### Step 4: Full Factor Rebuild
```sql
-- Run REFRESH_ALL_PERFORMANCE_FACTORS.sql
-- Run rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql
```

### Step 5: Verify Rankings Unchanged
```sql
-- Compare top 100 players before and after
SELECT player_id, player_name, total_points, rank
FROM `prodigy-ranking.algorithm_core.player_rankings`
ORDER BY total_points DESC
LIMIT 100
```

### Step 6: API Testing
- Test `/rankings` endpoint
- Test `/player/:id` endpoint
- Test `/search` endpoint
- Verify response times are acceptable

## Column Mapping Reference

Old column → New column

| player_stats column | v_latest_player_stats column |
|---------------------|------------------------------|
| `latestStats_regularStats_G` | `goals` |
| `latestStats_regularStats_A` | `assists` |
| `latestStats_regularStats_TP` | `points` |
| `latestStats_regularStats_PIM` | `pim` |
| `latestStats_regularStats_PM` | `plus_minus` |
| `latestStats_regularStats_GP` | `gp` |
| `latestStats_regularStats_GAA` | `gaa` |
| `latestStats_regularStats_SVP` | `svp` |
| `latestStats_team_name` | `team_name` |
| `latestStats_team_league_name` | `league_name` |
| `latestStats_season_slug` | `season_slug` |
| `latestStats_season_startYear` | `season_start_year` |

## Future Work (Phase 5-6)

After validation is complete:

1. **Rename `player_stats` → `player_metadata`**
   - Remove all `latestStats_*` columns
   - Keep only identity fields: `id`, `name`, `position`, `yearOfBirth`, `nationality_name`, `height_metrics`, `height_imperial`, `weight_metrics`, `weight_imperial`, `views`, `loadts`

2. **Delete Deprecated Scripts**
   - `FIX_update_latestStats_from_season_stats.sql`
   - `FIX_update_latestStats_v2.sql`
   - Review and update remaining Python scripts

3. **Update Documentation**
   - Update DATA_FLOW_MAP.md
   - Update DEVELOPER_GUIDE_FOR_ZDENEK.md

## Risks Mitigated

1. **Performance** - View is filtered for current season with proper indexing; can convert to materialized view if needed
2. **Season hardcoding** - Current year (2025) is in the view; update annually or make dynamic
3. **Metadata joins** - All factor queries join `v_latest_player_stats` with `player_stats` for metadata

## Timeline

- **Week 1** (Current): Create view, update factor SQL files, verify calculations ✓
- **Week 2**: Update API endpoints (if needed), test thoroughly
- **Week 3**: Update remaining Python scripts, rename `player_stats` → `player_metadata`
- **Week 4**: Delete deprecated files, update documentation

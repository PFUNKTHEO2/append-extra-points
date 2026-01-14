# Algorithm Core Consolidation - Execution Guide

## Overview
This consolidation reduces algorithm_core from 104 tables to 8 essential tables.

## Status: COMPLETED (2026-01-14)

### What Was Done
1. Created `player_external_factors` table consolidating 8 DL_ tables
2. Created `player_rankings` table with inline F01-F12 calculations
3. Updated views (`player_card_ratings`, `player_category_percentiles`)
4. Updated sync.js and related API files to use `player_rankings`
5. Archived consolidated tables to `algorithm_archive`

### Key Improvements
- **League matching improved**: 139,563 additional players now get league points
- **NULL team filter**: 14,838 players with NULL teams excluded (data quality)
- **Simplified architecture**: External factors in one table

---

## Execution Order (For Reference)

### Step 1: Create New Structure - DONE
```sql
-- 1a. Create player_external_factors table
-- Run: 01_create_player_external_factors.sql

-- 1b. Migrate data into player_external_factors
-- Run: 02_migrate_external_factors.sql
```

### Step 2: Test Consolidated Rebuild - DONE
```sql
-- 2a. Run the new consolidated rebuild (creates player_rankings)
-- Run: 03_rebuild_player_rankings_consolidated.sql

-- 2b. Compare output to current player_cumulative_points
-- Run: 04_verify_consolidation.sql
```

### Step 3: Update Sync - DONE
- Modified `api-backend/functions/sync.js` to use `player_rankings`
- Modified `api-backend/functions/admin.js`
- Modified `api-backend/functions/shared/bigquery.js`

### Step 4: Update Views - DONE
```sql
-- Run: 05_update_views.sql
```

### Step 5: Archive Old Tables - DONE
```sql
-- Run: 06_archive_consolidated_tables.sql
-- Tables archived to algorithm_archive with 20260114 suffix
```

---

## Files in This Directory

| File | Purpose | Status |
|------|---------|--------|
| `01_create_player_external_factors.sql` | Creates consolidated external factors table | DONE |
| `02_migrate_external_factors.sql` | Migrates data from DL_F15, DL_F17, PT_F16, DL_F22 | DONE |
| `03_rebuild_player_rankings_consolidated.sql` | New rebuild with inline calculations | DONE |
| `04_verify_consolidation.sql` | Compares new vs old output | DONE |
| `05_update_views.sql` | Updates card_ratings view to use player_rankings | DONE |
| `06_archive_consolidated_tables.sql` | Archives consolidated tables | DONE |

---

## Current Table Structure

### Primary Tables (algorithm_core)
| Table | Rows | Purpose |
|-------|------|---------|
| `player_stats` | 174,407 | EP source data |
| `player_rankings` | 159,569 | Master output (replaces player_cumulative_points) |
| `player_external_factors` | 2,927 | Consolidated external data (F15-F24) |
| `DL_all_leagues` | 1,048 | League tier points |

### Views
| View | Purpose |
|------|---------|
| `player_card_ratings` | EA-style 0-99 ratings |
| `player_category_percentiles` | Percentile rankings |

---

## Rollback
If issues occur:
1. Original `player_cumulative_points` table is preserved
2. All backups in `algorithm_archive` (dated 20260114)
3. Git history has original rebuild SQL

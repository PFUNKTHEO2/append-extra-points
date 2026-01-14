# Algorithm Audit Report - January 14, 2026

## Executive Summary

This audit documents all tables in `algorithm_core`, identifies source of truth tables for each factor, documents formulas, and recommends tables for archival.

**Current State:**
- **104 tables/views** in `algorithm_core`
- **24 active factors** (F01-F24) used in cumulative points
- **3 additional factors** (F25-F27) defined but NOT in cumulative calculation
- **~40 backup/staging tables** recommended for archival

---

## 1. Active Source of Truth Tables

### Main Output Table
| Table | Purpose | Row Count |
|-------|---------|-----------|
| `player_cumulative_points` | **FINAL OUTPUT** - All 24 factors aggregated | ~161,886 |

### Base Data Tables (Source of Truth)
| Table | Purpose | Used By |
|-------|---------|---------|
| `player_stats` | Primary player data, views, current season stats | F01, F02, F03-F07, F13, F14, base players |
| `player_season_stats` | Historical season data | F08-F12 (last season factors) |
| `player_stats_history` | Historical snapshots | Trending calculations |
| `player_stats_delta` | Weekly stat changes | F18, F19, F25 |

---

## 2. Factor Tables - Source of Truth

### Performance Factors (F01-F12) - PT_ Tables

| Factor | Table (Source of Truth) | Formula | Max Pts | Position |
|--------|------------------------|---------|---------|----------|
| **F01** | `PT_F01_EPV` | `((views - 100) / 29900) * 2000` | 2,000 | ALL |
| **F02** | `PT_F02_H` | Metric: `(height_cm - 175) * 25`; Imperial: `((inches - 65) / 11) * 500` | 500 | ALL |
| **F03** | `PT_F03_CGPGF` | `(goals_per_game / 2.0) * 500` | 500 | F only |
| **F04** | `PT_F04_CGPGD` | `(goals_per_game / 1.5) * 500` | 500 | D only |
| **F05** | `PT_F05_CAPG` | `(assists_per_game / 2.5) * 500` | 500 | F, D |
| **F06** | `PT_F06_CGAA` | `((3.5 - GAA) / 3.5) * 500` (inverted) | 500 | G only |
| **F07** | `PT_F07_CSV` | `((save_pct - 70) / 30) * 300` | 300 | G only |
| **F08** | `PT_F08_LGPGF` | `(goals_per_game / 2.0) * 300` | 300 | F only |
| **F09** | `PT_F09_LGPGD` | `(goals_per_game / 1.5) * 300` | 300 | D only |
| **F10** | `PT_F10_LAPG` | `(assists_per_game / 2.5) * 300` | 300 | F, D |
| **F11** | `PT_F11_LGAA` | `((3.5 - GAA) / 3.5) * 300` (inverted) | 300 | G only |
| **F12** | `PT_F12_LSV` | `((save_pct - 70) / 30) * 200` | 200 | G only |

**Data Sources:**
- F01-F07: `player_stats.latestStats` (2025-2026 season, min 5 GP)
- F08-F12: `algorithm_staging.player_season_stats_staging` (2024-2025 season)

### Direct Load Factors (F13-F24) - DL_ Tables

| Factor | Table (Source of Truth) | Join Method | Max Pts | Status |
|--------|------------------------|-------------|---------|--------|
| **F13** | `DL_F13_league_points` | Normalized league name match | 4,500 | Active |
| **F14** | `DL_F14_team_points` | Normalized team name match | 700 | **DISABLED** |
| **F15** | `DL_F15_international_points_final` | `matched_player_id` | 1,000 | Active |
| **F16** | `PT_F16_CP` | `player_id` | 500 | Active |
| **F17** | `DL_F17_draft_points` | `player_id` | 300 | Active |
| **F18** | `PT_F18_weekly_points_delta` | `player_id` | 200 | Active |
| **F19** | `PT_F19_weekly_assists_delta` | `player_id` | 125 | Active |
| **F20** | `DL_F20_playing_up_points` | `player_id` | 300 | Empty |
| **F21** | `DL_F21_tournament_points` | `player_id` | 500 | Empty |
| **F22** | `DL_F22_manual_points` | `player_id` | No cap | Active (87 rows) |
| **F23** | `DL_F23_prodigylikes_points` | `player_id` | 500 | Empty |
| **F24** | `DL_F24_card_sales_points` | `player_id` | 500 | Empty |

### NOT IN CUMULATIVE - Additional Factors

| Factor | Table | Purpose | Status |
|--------|-------|---------|--------|
| F25 | `PT_F25_weekly_views_delta` | Weekly EP views change | Defined, NOT aggregated |
| F26 | `PT_F26_weight` | Weight scoring | Defined, NOT aggregated |
| F27 | `PT_F27_bmi` | BMI scoring | Defined, NOT aggregated |

---

## 3. Reference/Config Tables (Keep)

| Table | Purpose |
|-------|---------|
| `DL_algorithm_config` | Factor configuration (24 rows) |
| `DL_all_leagues` | League reference data |
| `DL_all_teams` | Team reference data |
| `algorithm_league_quality_slugs` | League tier mapping |
| `algorithm_team_value` | Team point values |
| `EP_TEAMS_ALL` | Elite Prospects team data |

---

## 4. Views (Keep)

| View | Purpose |
|------|---------|
| `vw_rankings_worldwide` | Global rankings |
| `vw_rankings_north_american` | NA-scoped rankings |
| `vw_rankings_by_nationality` | Country-specific rankings |
| `player_cumulative_points_ranked` | Ranked output |
| `player_card_ratings` | EA Sports-style 0-99 ratings |
| `player_category_percentiles` | Category percentiles |
| `player_score_view` | Score breakdown |
| `player_league_points` | League points view |
| `EP_views_trending` | Trending views |
| `international_points_detail_view` | IP detail |
| `top_100_international_points` | Top IP players |

---

## 5. Tables Recommended for ARCHIVAL

### Backup Tables (Move to `algorithm_archive`)

These are point-in-time backups that should be archived:

```
DL_F13_league_points_backup_20251120_210337
DL_F13_league_points_backup_20251207
DL_F13_league_points_backup_20251216
DL_F13_league_points_backup_20251216_085325
DL_F13_league_points_backup_pre_fix
DL_F14_team_points_backup_20251121_092810
DL_F14_team_points_backup_20251121_092834
DL_F17_draft_points_backup_20251120_205403
DL_F17_draft_points_backup_20251120_210337
DL_F22_manual_points_backup_20251120_221752
DL_F22_manual_points_backup_20251120_221924
DL_all_leagues_backup_20260103
PT_F04_CGPGD_backup_20251208_v2
PT_F06_CGAA_backup_20251119
PT_F06_CGAA_backup_20251208
PT_F07_CSV_backup_20251208
PT_F09_LGPGD_backup_20251208_v2
PT_F11_LGAA_backup_20251208
PT_F12_LSV_backup_20251208
PT_F18_weekly_points_delta_backup_20251221_065047
PT_F19_weekly_assists_delta_backup_20251221_065047
player_cumulative_points_backup_20251117
player_cumulative_points_backup_20251120_210337
player_cumulative_points_backup_20251208_goalie_fix
player_cumulative_points_backup_20260106_f15
player_stats_backup_20260108_200147
player_stats_backup_20260108_220118
player_stats_backup_20260109_130619
player_stats_backup_20260109_142123
player_stats_backup_20260109_200541
```

**Total: 29 backup tables**

### Staging Tables (Move to `algorithm_staging` or Archive)

```
DL_F13_league_points_staging
DL_F13_league_points_staging_20251216
```

**Total: 2 staging tables**

### Potentially Redundant Tables (Review Before Archive)

| Table | Concern | Recommendation |
|-------|---------|----------------|
| `PT_F15_IP` | Duplicate of DL_F15? | Verify usage, archive if unused |
| `PT_F18_weekly_goal_points` | Seems redundant with PT_F18_weekly_points_delta | Verify, archive if unused |
| `PT_F19_weekly_assist_points` | Seems redundant with PT_F19_weekly_assists_delta | Verify, archive if unused |
| `PT_F20_weekly_views_points` | Seems related to F25 | Verify, archive if unused |
| `player_cumulative_points_export` | Export snapshot | Archive if not in use |
| `international_points_matched` | Old matching table | Verify, archive if superseded |
| `international_points_summary_stats` | Summary stats | Archive if not in use |
| `priority_players_for_stats` | Pipeline helper | Archive if not in use |

**Total: 8 tables to review**

---

## 6. Cumulative Points Calculation

**File:** `rebuild_cumulative_with_fixes.sql`
**Version:** v2.6-fully-deduped

### Algorithm Flow
```
base_players (from player_stats)
    |
    +-- LEFT JOIN f01_data (PT_F01_EPV)
    +-- LEFT JOIN f02_data (PT_F02_H)
    +-- LEFT JOIN f03_data (PT_F03_CGPGF)
    +-- LEFT JOIN f04_data (PT_F04_CGPGD)
    +-- LEFT JOIN f05_data (PT_F05_CAPG)
    +-- LEFT JOIN f06_data (PT_F06_CGAA)
    +-- LEFT JOIN f07_data (PT_F07_CSV)
    +-- LEFT JOIN f08_data (PT_F08_LGPGF)
    +-- LEFT JOIN f09_data (PT_F09_LGPGD)
    +-- LEFT JOIN f10_data (PT_F10_LAPG)
    +-- LEFT JOIN f11_data (PT_F11_LGAA)
    +-- LEFT JOIN f12_data (PT_F12_LSV)
    +-- LEFT JOIN f13_data (player_stats + DL_F13_league_points)
    +-- LEFT JOIN f14_data (player_stats + DL_F14_team_points)
    +-- LEFT JOIN f15_data (DL_F15_international_points_final)
    +-- LEFT JOIN f16_data (PT_F16_CP)
    +-- LEFT JOIN f17_data (DL_F17_draft_points)
    +-- LEFT JOIN f18_data (PT_F18_weekly_points_delta)
    +-- LEFT JOIN f19_data (PT_F19_weekly_assists_delta)
    +-- LEFT JOIN f20_data (DL_F20_playing_up_points)
    +-- LEFT JOIN f21_data (DL_F21_tournament_points)
    +-- LEFT JOIN f22_data (DL_F22_manual_points)
    +-- LEFT JOIN f23_data (DL_F23_prodigylikes_points)
    +-- LEFT JOIN f24_data (DL_F24_card_sales_points)
    |
    v
performance_total = SUM(F01-F12)
direct_load_total = SUM(F13-F24)
total_points = performance_total + direct_load_total
```

### Deduplication Strategy
- All factor CTEs use `MAX() + GROUP BY player_id`
- F13: Normalized league name matching (LOWER, TRIM, REPLACE)
- F14: Normalized team name (removes U16, Jr, age suffixes)

---

## 7. Known Issues

| Issue | Factor | Description |
|-------|--------|-------------|
| F14 Disabled | F14 | Team points returns 0 for all players (intentionally disabled Dec 2025) |
| F15 Exceeds Max | F15 | Some players have >1000 points (max configured is 1000) |
| Empty Tables | F20, F21, F23, F24 | No data loaded |
| F25-F27 Not Used | F25-F27 | Defined but not included in cumulative calculation |

---

## 8. Archival Script

Run this SQL to move backup tables to archive:

```sql
-- Create backup copies in archive dataset
CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_archive.DL_F13_league_points_backup_20251120_210337` AS
SELECT * FROM `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251120_210337`;

-- Repeat for each backup table...

-- Then drop from algorithm_core
DROP TABLE `prodigy-ranking.algorithm_core.DL_F13_league_points_backup_20251120_210337`;
-- Repeat for each...
```

---

## 9. Summary

### Tables to KEEP in algorithm_core (38 tables + 11 views)

**Active Factor Tables (24):**
- PT_F01_EPV through PT_F12_LSV (12 PT tables)
- DL_F13 through DL_F24 (12 DL tables)
- PT_F16_CP, PT_F18, PT_F19

**Metadata Tables (12):**
- All _metadata tables for PT factors

**Base Data (4):**
- player_stats, player_season_stats, player_stats_history, player_stats_delta

**Reference (6):**
- DL_algorithm_config, DL_all_leagues, DL_all_teams, algorithm_league_quality_slugs, algorithm_team_value, EP_TEAMS_ALL

**Output (2):**
- player_cumulative_points, player_cumulative_points_export

### Tables to ARCHIVE (31 backup + 2 staging = 33 tables)
See Section 5 for complete list.

### Tables to REVIEW (8 tables)
See Section 5 "Potentially Redundant" for review recommendations.

---

*Report generated: January 14, 2026*
*Algorithm version: v2.6-fully-deduped*

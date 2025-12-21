# Algorithm Factor Audit Report
**Date:** 2025-12-21
**Algorithm Version:** v2.8-f25-weekly-views
**Total Players:** 161,893

---

## Executive Summary

This audit documents all 27 algorithm factors, their formulas, data sources, and current state in BigQuery.

### Key Findings
- **21 factors** are calculating correctly within configured limits
- **1 issue identified:** F15 (International Points) exceeds configured max of 1000 (actual max: 1902.9)
- **5 factors** have no data: F14 (disabled), F20, F21, F23, F24

---

## Part 1: Algorithm Configuration (DL_algorithm_config)

| Factor | Name | Max Pts | Min Val | Max Val | Calc Type | Position |
|--------|------|---------|---------|---------|-----------|----------|
| F01 | EP Views | 2000 | 100 | 30000 | linear | ALL |
| F02 | Height | 200 | - | - | physical_standards | ALL |
| F03 | Current GPG (F) | 500 | 0 | 2.0 | linear | F |
| F04 | Current GPG (D) | 500 | 0 | 1.5 | linear | D |
| F05 | Current APG | 500 | 0 | 2.5 | linear | F,D |
| F06 | Current GAA | 500 | 0 | 3.5 | inverted_linear | G |
| F07 | Current SV% | 300 | .699 | .990 | linear | G |
| F08 | Past GPG (F) | 300 | 0 | 2.0 | linear | F |
| F09 | Past GPG (D) | 300 | 0 | 1.5 | linear | D |
| F10 | Past APG | 300 | 0 | 2.5 | linear | F,D |
| F11 | Past GAA | 300 | 0 | 3.5 | inverted_linear | G |
| F12 | Past SV% | 200 | .699 | .990 | linear | G |
| F13 | League Points | 4500 | - | - | tiered | ALL |
| F14 | Team Points | 700 | - | - | lookup | ALL |
| F15 | International | 1000 | - | - | lookup | ALL |
| F16 | Commitment | 500 | - | - | lookup | ALL |
| F17 | Draft Points | 300 | - | - | lookup | ALL |
| F18 | Weekly Goals | 200 | 0 | 5 | per_event | F,D |
| F19 | Weekly Assists | 125 | 0 | 5 | per_event | F,D |
| F20 | Playing Up | 300 | - | - | lookup | ALL |
| F21 | Tournament | 500 | - | - | lookup | ALL |
| F22 | Manual Points | NO CAP | - | - | lookup | ALL |
| F23 | ProdigyLikes | 500 | - | - | lookup | ALL |
| F24 | Card Sales | 500 | - | - | lookup | ALL |
| F25 | Weekly EP Views | 200 | 0 | 200 | per_event | ALL |
| F26 | Weight | 150 | - | - | physical_standards | ALL |
| F27 | BMI | 250 | - | - | physical_standards | ALL |

---

## Part 2: Factor Formulas and Data Sources

### F01: Elite Prospects Views
- **Max Points:** 2000
- **Source Table:** `PT_F01_EPV`
- **Data Source:** `player_stats.views`
- **Formula:**
  ```
  IF views <= 100 THEN 0
  ELSE IF views >= 30000 THEN 2000
  ELSE ((views - 100) / 29900) * 2000
  ```
- **Current State:** 96,275 players with non-zero points, max 2000

### F02: Height Points
- **Max Points:** 200
- **Source Table:** `PT_F02_H`
- **Data Source:** `player_stats.height`, `DL_physical_standards`
- **Formula:** Physical standards lookup based on position and birth year
- **Current State:** 46,156 players with non-zero points, max 200

### F03: Current Season Goals Per Game (Forwards)
- **Max Points:** 500
- **Source Table:** `PT_F03_CGPGF`
- **Data Source:** `player_stats.latestStats_regularStats_G`, `latestStats_regularStats_GP`
- **Formula:**
  ```
  IF games < 5 THEN 0
  ELSE IF (goals/games) >= 2.0 THEN 500
  ELSE (goals/games) / 2.0 * 500
  ```
- **Position Filter:** Forwards only
- **Current State:** 48,028 players with non-zero points, max 500

### F04: Current Season Goals Per Game (Defenders)
- **Max Points:** 500
- **Source Table:** `PT_F04_CGPGD`
- **Data Source:** Same as F03
- **Formula:**
  ```
  IF games < 5 THEN 0
  ELSE IF (goals/games) >= 1.5 THEN 500
  ELSE (goals/games) / 1.5 * 500
  ```
- **Position Filter:** Defenders only
- **Current State:** 18,220 players with non-zero points, max 500

### F05: Current Season Assists Per Game
- **Max Points:** 500
- **Source Table:** `PT_F05_CAPG`
- **Data Source:** `player_stats.latestStats_regularStats_A`, `latestStats_regularStats_GP`
- **Formula:**
  ```
  IF games < 5 THEN 0
  ELSE IF (assists/games) >= 2.5 THEN 500
  ELSE (assists/games) / 2.5 * 500
  ```
- **Position Filter:** Forwards and Defenders
- **Current State:** 77,112 players with non-zero points, max 500

### F06: Current Season Goals Against Average (Goalies)
- **Max Points:** 500
- **Source Table:** `PT_F06_CGAA`
- **Data Source:** `player_stats.latestStats_regularStats_GAA`
- **Formula:** (INVERTED - lower GAA = more points)
  ```
  IF games < 5 THEN 0
  ELSE IF GAA >= 3.5 THEN 0
  ELSE IF GAA = 0 THEN 500
  ELSE (1 - (GAA / 3.5)) * 500
  ```
- **Position Filter:** Goalies only
- **Current State:** 4,464 players with non-zero points, max 500

### F07: Current Season Save Percentage (Goalies)
- **Max Points:** 300
- **Source Table:** `PT_F07_CSV`
- **Data Source:** `player_stats.latestStats_regularStats_SVP`
- **Formula:**
  ```
  IF games < 5 THEN 0
  ELSE IF SVP <= .699 THEN 0
  ELSE IF SVP >= .990 THEN 300
  ELSE ((SVP*1000 - 699) / 291) * 300
  ```
- **Position Filter:** Goalies only
- **Current State:** 4,922 players with non-zero points, max 300

### F08-F12: Past Season Performance
Same formulas as F03-F07 but using previous season stats from `player_stats_history`:
- **F08:** Past GPG (Forwards) - max 300
- **F09:** Past GPG (Defenders) - max 300
- **F10:** Past APG - max 300
- **F11:** Past GAA (Goalies) - max 300, inverted
- **F12:** Past SV% (Goalies) - max 200

### F13: League Points
- **Max Points:** 4500
- **Source Table:** `DL_F13_league_points`
- **Data Source:** Tiered lookup by league name
- **Formula:** Direct lookup, case-insensitive match
- **Top Leagues:**
  - NHL: 4500 pts
  - OHL, WHL, QMJHL, SHL, KHL, Liiga, etc.: 3600 pts
  - Mestis: 3100 pts
- **Current State:** 139,836 players with non-zero points, max 4500

### F14: Team Points (DISABLED)
- **Max Points:** 700
- **Source Table:** `DL_F14_team_points`
- **Status:** DISABLED as of 2025-12-16
- **Current Behavior:** Returns 0 for all players
- **Current State:** 0 players with points

### F15: International Selection Points
- **Max Points:** 1000 (CONFIGURED)
- **Source Table:** `DL_F15_international_points_final`
- **Data Source:** National team selection records
- **Formula:** Lookup by matched_player_id
- **ISSUE:** Max actual value is 1902.9 - EXCEEDS CONFIGURED MAX
- **Current State:** 1,557 players with non-zero points

### F16: College Commitment Points
- **Max Points:** 500
- **Source Table:** `PT_F16_CP`
- **Data Source:** College commitment rankings
- **Formula:** Points based on committed college ranking
- **Current State:** 776 players with non-zero points, range 250-500

### F17: Draft Points
- **Max Points:** 300
- **Source Table:** `DL_F17_draft_points`
- **Data Source:** CHL/USHL draft records
- **Formula:** Points based on draft round/pick
- **Current State:** 796 players with non-zero points, range 139-300

### F18: Weekly Goals Delta
- **Max Points:** 200
- **Source Table:** `PT_F18_weekly_points_delta`
- **Data Source:** Weekly snapshot delta of goals
- **Formula:**
  ```
  LEAST(goals_added_this_week * 40, 200)
  ```
- **Breakdown:**
  - 1 goal = 40 pts
  - 2 goals = 80 pts
  - 3 goals = 120 pts
  - 4 goals = 160 pts
  - 5+ goals = 200 pts (capped)
- **Current State:** 14,158 players with non-zero points, max 200

### F19: Weekly Assists Delta
- **Max Points:** 125
- **Source Table:** `PT_F19_weekly_assists_delta`
- **Data Source:** Weekly snapshot delta of assists
- **Formula:**
  ```
  LEAST(assists_added_this_week * 25, 125)
  ```
- **Breakdown:**
  - 1 assist = 25 pts
  - 2 assists = 50 pts
  - 3 assists = 75 pts
  - 4 assists = 100 pts
  - 5+ assists = 125 pts (capped)
- **Current State:** 17,638 players with non-zero points, max 125

### F20: Playing Up Points
- **Max Points:** 300
- **Source Table:** `DL_F20_playing_up_points`
- **Current State:** 0 records (empty table)

### F21: Tournament Points
- **Max Points:** 500
- **Source Table:** `DL_F21_tournament_points`
- **Current State:** 0 records (empty table)

### F22: Manual Points
- **Max Points:** NO CAP (admin override)
- **Source Table:** `DL_F22_manual_points`
- **Current State:** 87 players with points, range 60-250

### F23: ProdigyLikes Points
- **Max Points:** 500
- **Source Table:** `DL_F23_prodigylikes_points`
- **Current State:** 0 records (empty table)

### F24: Card Sales Points
- **Max Points:** 500
- **Source Table:** `DL_F24_card_sales_points`
- **Current State:** 0 records (empty table)

### F25: Weekly EP Views Delta
- **Max Points:** 200
- **Source Table:** `PT_F25_weekly_views_delta`
- **Data Source:** Weekly snapshot delta of views
- **Formula:**
  ```
  LEAST(views_added_this_week, 200)
  ```
- **Current State:** 161,697 players with non-zero points, max 200

### F26: Weight Points
- **Max Points:** 150
- **Source Table:** `PT_F26_weight`
- **Data Source:** `player_stats.weight`, `DL_physical_standards`
- **Formula:** Physical standards lookup
- **Current State:** 36,202 players with non-zero points, max 150

### F27: BMI Points
- **Max Points:** 250
- **Source Table:** `PT_F27_bmi`
- **Data Source:** Calculated from height and weight
- **Formula:** Physical standards lookup for BMI = weight(kg) / height(m)^2
- **Current State:** 60,639 players with non-zero points, max 250

---

## Part 3: Max Value Validation

| Factor | Config Max | Actual Max | Status |
|--------|------------|------------|--------|
| F01 | 2000 | 2000.0 | OK |
| F02 | 200 | 200.0 | OK |
| F03 | 500 | 500.0 | OK |
| F04 | 500 | 500.0 | OK |
| F05 | 500 | 500.0 | OK |
| F06 | 500 | 500.0 | OK |
| F07 | 300 | 300.0 | OK |
| F08 | 300 | 300.0 | OK |
| F09 | 300 | 300.0 | OK |
| F10 | 300 | 300.0 | OK |
| F11 | 300 | 300.0 | OK |
| F12 | 200 | 200.0 | OK |
| F13 | 4500 | 4500.0 | OK |
| F14 | 700 | 0.0 | OK (disabled) |
| F15 | 1000 | 1902.9 | **EXCEEDS** |
| F16 | 500 | 500.0 | OK |
| F17 | 300 | 300.0 | OK |
| F18 | 200 | 200.0 | OK |
| F19 | 125 | 125.0 | OK |
| F25 | 200 | 200.0 | OK |
| F26 | 150 | 150.0 | OK |
| F27 | 250 | 250.0 | OK |

---

## Part 4: Issues and Discrepancies

### Issue 1: F15 International Points Exceeds Max
**Severity:** Medium

The F15 factor has a configured max_points of 1000 in `DL_algorithm_config`, but actual values in `player_cumulative_points` reach 1902.9 points.

**Top Players Exceeding Max:**
| Player | Intl Pts | League |
|--------|----------|--------|
| Carson Carels | 1902.9 | WHL |
| Ryan Lin | 1753.9 | USHS-MI |
| Keaton Verhoeff | 1630.4 | NCAA |
| Viggo Bjorck | 1484.0 | SHL |
| Viktor Klingsell | 1477.4 | U20 Nationell |

**Recommendation:** Either:
1. Apply a cap of 1000 to F15 in the calculation
2. Update the config to reflect the actual max (if intentional)

### Issue 2: Empty Data Tables
The following tables have 0 records:
- `DL_F20_playing_up_points` (F20)
- `DL_F21_tournament_points` (F21)
- `DL_F23_prodigylikes_points` (F23)
- `DL_F24_card_sales_points` (F24)

These factors contribute 0 points to all players.

### Issue 3: F14 Team Points Disabled
F14 is intentionally disabled and returns 0 for all players. The `DL_F14_team_points` table has 10,067 teams with points up to 700, but the cumulative rebuild ignores this data.

---

## Part 5: Data Flow Summary

```
player_stats (source)
       |
       v
+------------------+
| PT_F01 - PT_F12  |  Performance factors
| (calculated)     |  from player_stats
+------------------+
       |
       +---> DL_F13_league_points (lookup by league)
       +---> DL_F14_team_points (DISABLED)
       +---> DL_F15_international_points_final (lookup by player_id)
       +---> PT_F16_CP (college commitment)
       +---> DL_F17_draft_points (lookup by player_id)
       +---> PT_F18_weekly_points_delta (weekly goals)
       +---> PT_F19_weekly_assists_delta (weekly assists)
       +---> DL_F20-F24 (various lookups)
       +---> PT_F25_weekly_views_delta (weekly views)
       +---> PT_F26_weight (physical)
       +---> PT_F27_bmi (physical)
       |
       v
+---------------------------+
| player_cumulative_points  |
| (final aggregation)       |
+---------------------------+
```

---

## Part 6: Recommended Actions

1. **Cap F15 at 1000** - Apply LEAST(international_points, 1000) in the cumulative rebuild or update the source data
2. **Review empty tables** - Determine if F20, F21, F23, F24 should have data
3. **Document F14 status** - Add clear documentation about why F14 is disabled
4. **Regular audits** - Run this audit weekly to catch discrepancies early

---

*Report generated: 2025-12-21*
*Script: full_factor_audit.py*

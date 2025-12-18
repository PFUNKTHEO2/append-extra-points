# ProdigyChain Algorithm & Rating Audit Report

**Generated:** 2025-12-18
**Database:** prodigy-ranking (BigQuery)
**Total Players in Database:** 163,568

---

## EXECUTIVE SUMMARY

### Key Discrepancies Found

1. **Rating Weights Mismatch** - Current implementation uses different weights than spreadsheet spec
2. **F02 Height Max Points Exceeded** - Max 500 pts found vs 200 pts expected
3. **F15 International Points Exceeded** - Max 1,903 pts found vs 1,000 pts expected
4. **Level Rating Calculation** - Uses percentile-based approach vs direct league tier mapping
5. **Physical Rating Missing F26/F27** - Currently only uses F02 Height, should include Weight & BMI

---

## PART 1: ALGORITHM FACTORS (F01-F27)

### Factor Coverage Summary

| Factor | Description | Players w/Points | Coverage | Avg Pts | Max Pts | Expected Max | Status |
|--------|-------------|------------------|----------|---------|---------|--------------|--------|
| F01 | Elite Prospects Views | 97,745 | 59.8% | 81.86 | 2,000 | 2,000 | OK |
| F02 | Height Points | 38,924 | 23.8% | 187.57 | 500 | 200 | **EXCEEDS** |
| F03 | Current GPG (F) | 22,903 | 14.0% | 84.30 | 500 | 500 | OK |
| F04 | Current GPG (D) | 15,875 | 9.7% | 57.67 | 500 | 500 | OK |
| F05 | Current APG (F/D) | 37,436 | 22.9% | 71.44 | 500 | 500 | OK |
| F06 | Current GAA (G) | 3,762 | 2.3% | 159.20 | 500 | 500 | OK |
| F07 | Current SV% (G) | 4,398 | 2.7% | 186.74 | 300 | 300 | OK |
| F08 | Last Season GPG (F) | 55,344 | 33.8% | 57.30 | 300 | 300 | OK |
| F09 | Last Season GPG (D) | 22,830 | 14.0% | 34.53 | 300 | 300 | OK |
| F10 | Last Season APG (F/D) | 89,117 | 54.5% | 44.82 | 300 | 300 | OK |
| F11 | Last GAA (G) | 1,522 | 0.9% | 95.66 | 300 | 300 | OK |
| F12 | Last SV% (G) | 1,640 | 1.0% | 119.78 | 200 | 200 | OK |
| F13 | League Points | 138,590 | 84.7% | 1,535.96 | 4,500 | 4,500 | OK |
| F14 | Team Points | 58,339 | 35.7% | 360.23 | 700 | 700 | OK |
| F15 | International Points | 1,609 | 1.0% | 389.10 | 1,903 | 1,000 | **EXCEEDS** |
| F16 | Commitment Points | 809 | 0.5% | 303.03 | 500 | 500 | OK |
| F17 | Draft Points | 820 | 0.5% | 262.14 | 300 | 300 | OK |
| F18 | Weekly Goals Delta | 13,487 | 8.2% | 2.15 | 38 | 200 | OK |
| F19 | Weekly Assists Delta | 10,126 | 6.2% | 1.71 | 21 | 125 | OK |
| F20 | Playing Up Points | 0 | 0.0% | - | 0 | 300 | NOT IMPLEMENTED |
| F21 | Tournament Points | 0 | 0.0% | - | 0 | ??? | NOT IMPLEMENTED |
| F22 | Manual Points | 92 | 0.1% | 157.39 | 250 | N/A | OK |
| F23 | ProdigyLikes Points | 0 | 0.0% | - | 0 | 500 | NOT IMPLEMENTED |
| F24 | Card Sales Points | 0 | 0.0% | - | 0 | 500 | NOT IMPLEMENTED |
| F25 | Weekly EP Views | TBD | TBD | TBD | TBD | 1 | TBD |
| F26 | Weight Points | 33,504 | 20.7% | 61.07 | 150 | 150 | OK |
| F27 | BMI Points | 59,942 | 37.0% | 97.12 | 250 | 250 | OK |

### Data Sources

| Factor | Source Table | Dataset |
|--------|--------------|---------|
| F01 | PT_F01_EPV | algorithm_core |
| F02 | PT_F02_H | algorithm_core |
| F03-F05 | PT_F03_CGPGF, PT_F04_CGPGD, PT_F05_CAPG | algorithm_core |
| F06-F07 | PT_F06_CGAA, PT_F07_CSV | algorithm_core |
| F08-F10 | PT_F08_LGPGF, PT_F09_LGPGD, PT_F10_LAPG | algorithm_core |
| F11-F12 | PT_F11_LGAA, PT_F12_LSV | algorithm_core |
| F13 | DL_F13_league_points | algorithm_core |
| F14 | DL_F14_team_points | algorithm_core |
| F15 | DL_F15_international_points_final | algorithm_core |
| F16 | PT_F16_CP | algorithm_core |
| F17 | DL_F17_draft_points | algorithm_core |
| F18 | PT_F18_weekly_goal_points | algorithm_core |
| F19 | PT_F19_weekly_assist_points | algorithm_core |
| F20 | DL_F20_playing_up_points | algorithm_core (empty) |
| F21 | DL_F21_tournament_points | algorithm_core (empty) |
| F22 | DL_F22_manual_points | algorithm_core |
| F23 | DL_F23_prodigylikes_points | algorithm_core (empty) |
| F24 | DL_F24_card_sales_points | algorithm_core (empty) |
| F26 | PT_F26_weight | algorithm_core |
| F27 | PT_F27_bmi | algorithm_core |

### Cumulative Points Table

**Location:** `prodigy-ranking.algorithm.player_cumulative_points`

All factors are joined and summed into:
- `performance_total` = F01 + F02 + F03-F12
- `direct_load_total` = F13 + F14 + F15 + F16 + F17 + F18 + F19 + F20 + F21 + F22 + F23 + F24
- `total_points` = performance_total + direct_load_total

**Note:** F26 and F27 are NOT currently included in total_points calculation in cumulative table.

---

## PART 2: EA-STYLE CARD RATINGS (0-99 Scale)

### Rating Distribution Summary

| Category | Avg | Min | Max | Players >= 95 | Players = 99 |
|----------|-----|-----|-----|---------------|--------------|
| Overall | 53.1 | 28 | 96 | 11 | 0 |
| Performance | 64.4 | 40 | 99 | 1,564 | varies |
| Level | 64.5 | 8 | 99 | 1,063 | 3 |
| Visibility | 3.4 | 1 | 99 | 390 | varies |
| Physical | 56.7 | 40 | 99 | 1,542 | varies |
| Achievements | 41.0 | 40 | 99 | 1,557 | varies |
| Trending | 44.3 | 40 | 99 | 1,327 | varies |

**Total Players Rated:** 156,309

### Current Implementation vs Spreadsheet Specification

#### Weight Comparison

| Category | Current Weight | Spreadsheet Weight | Discrepancy |
|----------|---------------|-------------------|-------------|
| Performance | 35% | 15% | **-20%** |
| Level | 25% | 35% | **+10%** |
| Visibility | 10% | 20% | **+10%** |
| Physical | 10% | 15% | **+5%** |
| Achievements | 15% | 10% | **-5%** |
| Trending | 5% | 5% | OK |

#### Calculation Method Comparison

| Category | Current Method | Spreadsheet Specification | Match? |
|----------|---------------|---------------------------|--------|
| Performance | Percentile-based (F03-F12 sum) | Percentile of factor totals | YES |
| Level | Percentile-based (F13+F14 sum) | Direct league tier mapping (NHL=99, CHL=95) | **NO** |
| Visibility | Percentile-based (F01+F23 sum) | EP views linear (same as F01) | PARTIAL |
| Physical | Percentile-based (F02 only) | Calculated: ((F02+F26+F27)/600)*100 | **NO** |
| Achievements | Percentile-based (F15+F16+F17+F21) | "Coming soon" | N/A |
| Trending | Percentile-based (F18+F19 sum) | "Coming soon" | N/A |

### Level Rating - Detailed Analysis

The spreadsheet specifies Level rating should use **direct league tier mapping**:

| League Tier | Expected Rating |
|-------------|-----------------|
| NHL | 99 |
| OHL, WHL, QMJHL, KHL, Liiga, Czechia | 95 |
| AHL, SHL, etc. | 91 |
| U20 leagues | 87 |
| etc. | ... |

**Current Implementation Results (from data):**
- 3 players with Level = 99 (all NHL players)
- WHL, OHL, QMJHL players = 95
- U20 leagues = 87

The current percentile-based approach **happens to produce similar results** to the intended tier-based approach because higher-tier leagues have more league points, but this is coincidental and may not produce consistent results.

**Existing Tier Table:** `DL_league_category_points` contains direct level_category_points mappings (8-99) that could be used for direct mapping instead of percentile calculation.

### Level Rating by League (Sample)

| League | Player Count | Avg Level Rating | Max Level Rating |
|--------|--------------|------------------|------------------|
| NHL | 3 | 99.0 | 99 |
| WHL | 376 | 95.0 | 95 |
| OHL | 332 | 95.0 | 95 |
| QMJHL | 270 | 95.0 | 95 |
| QC Int PW | 1,177 | 91.0 | 91 |
| Czechia U20 | 285 | 87.0 | 87 |
| USHL | 235 | 87.0 | 87 |
| OJHL | 378 | 87.0 | 87 |
| USHS-MA | 2,177 | 82.0 | 82 |
| USHS-MI | 1,373 | 82.0 | 82 |

---

## PART 3: DISCREPANCIES & ISSUES

### Critical Issues

1. **F02 Height Points Exceeds Max**
   - Found: 500 max points
   - Expected: 200 max points
   - Impact: Inflates performance_total and affects rankings

2. **F15 International Points Exceeds Max**
   - Found: 1,903 max points
   - Expected: 1,000 max points
   - Impact: Some international players have inflated scores

3. **Rating Weight Mismatch**
   - Level should be weighted higher (35% vs current 25%)
   - Performance should be weighted lower (15% vs current 35%)
   - This significantly affects overall ratings

4. **Physical Rating Missing Factors**
   - Current: Only uses F02 (Height)
   - Should be: ((F02 + F26 + F27) / 600) * 100
   - F26 and F27 exist in separate tables but not integrated

### Implementation Gaps

| Factor | Status | Notes |
|--------|--------|-------|
| F20 Playing Up | NOT IMPLEMENTED | 0 players have points |
| F21 Tournament | NOT IMPLEMENTED | 0 players have points |
| F23 ProdigyLikes | NOT IMPLEMENTED | 0 players have points |
| F24 Card Sales | NOT IMPLEMENTED | 0 players have points |
| F25 Weekly Views | PARTIAL | Table exists but not in cumulative |

### Data Quality Notes

- Goalie coverage (F06, F07, F11, F12) is low (~1-3%) due to position-specific factors
- F26/F27 have ~20-37% coverage (depends on height/weight data availability)
- 15% of players have no league points (missing league mapping)

---

## PART 4: RECOMMENDATIONS

### Immediate Fixes

1. **Update Rating Weights** to match spreadsheet:
   ```sql
   OVERALL = PER*0.15 + LEV*0.35 + VIS*0.20 + PHY*0.15 + ACH*0.10 + TRE*0.05
   ```

2. **Change Level Rating Calculation** to use direct tier mapping:
   ```sql
   -- Use DL_league_category_points.level_category_points directly
   level_rating = level_category_points (from league lookup)
   ```

3. **Update Physical Rating Calculation**:
   ```sql
   physical_rating = ((F02 + F26 + F27) / 600) * 100
   -- Then apply EA-style curve
   ```

4. **Cap F02 Height** at 200 max points per spreadsheet
5. **Cap F15 International** at 1,000 max points per spreadsheet

### Medium-Term

1. Integrate F26/F27 into player_cumulative_points total
2. Implement F20 (Playing Up) points calculation
3. Implement F21 (Tournament) points tracking
4. Add F25 (Weekly EP Views) to cumulative total

### Long-Term

1. Build F23 (ProdigyLikes) tracking system
2. Build F24 (Card Sales) tracking system
3. Implement decay logic for weekly points (50%, 40%, 30%... per spreadsheet)

---

## PART 5: TECHNICAL REFERENCE

### Key Tables

| Table | Location | Purpose |
|-------|----------|---------|
| player_cumulative_points | algorithm.* & algorithm_core.* | Master player data with all factors |
| player_card_ratings | algorithm_core.* | VIEW with EA-style ratings |
| DL_league_category_points | algorithm.* | League tier to rating mapping |
| PT_F* | algorithm_core.* | Individual factor point tables |
| DL_F* | algorithm_core.* | Dimension/lookup tables |

### Rating View Location

`prodigy-ranking.algorithm_core.player_card_ratings` (VIEW)

Defined in: `create_ea_ratings_view.sql`

### API Endpoints

- `getPlayer` - Returns player with factors F01-F27
- `getCardRatings` - Returns EA-style ratings
- `getCardRatingsBatch` - Batch ratings retrieval
- `getPlayerPhysical` - Height/Weight/BMI data

---

## APPENDIX: Spreadsheet Factor Definitions

| # | Factor | F | D | G | Max Pts | Distribution |
|---|--------|---|---|---|---------|--------------|
| 1 | EP Views | Y | Y | Y | 2000 | Linear (100-30000) |
| 2 | Height | Y | Y | Y | 200 | By birth year & position |
| 3 | Current GPG | Y | N | N | 500 | Linear (0-2) |
| 4 | Current GPG | N | Y | N | 500 | Linear (0-1.5) |
| 5 | Current APG | Y | Y | N | 500 | Linear (0-2.5) |
| 6 | Current GAA | N | N | Y | 500 | Linear (0-3.5) |
| 7 | Current SV% | N | N | Y | 300 | Linear (699-990) |
| 8 | Last GPG | Y | N | N | 300 | Linear (0-2) |
| 9 | Last GPG | N | Y | N | 300 | Linear (0-1.5) |
| 10 | Last APG | Y | Y | N | 300 | Linear (0-2.5) |
| 11 | Last GAA | N | N | Y | 300 | Linear (0-3.5) |
| 12 | Last SV% | N | N | Y | 200 | Linear (699-990) |
| 13 | League | Y | Y | Y | 4500 | By tiers |
| 14 | Team | Y | Y | Y | 700 | Direct |
| 15 | International | Y | Y | Y | 1000 | Direct |
| 16 | Commitment | Y | Y | Y | 500 | Direct |
| 17 | Draft | Y | Y | Y | 300 | Direct |
| 18 | Weekly Goals | Y | Y | N | 40 (200 limit) | Calculated |
| 19 | Weekly Assists | Y | Y | N | 25 (125 limit) | Calculated |
| 20 | Playing Up | Y | Y | Y | 300 | Via league pts |
| 21 | Tournament | Y | Y | Y | ??? | Direct |
| 22 | Manual | Y | Y | Y | N/A | Direct |
| 23 | ProdigyLikes | Y | Y | Y | 500 | TBD |
| 24 | Card Sales | Y | Y | Y | 500 | TBD |
| 25 | Weekly Views | Y | Y | Y | 1 | Calculated |
| 26 | Weight | Y | Y | Y | 150 | By birth year & position |
| 27 | BMI | Y | Y | Y | 250 | By birth year & position |

---

*Report generated by Claude Code for ProdigyChain Algorithm Audit*

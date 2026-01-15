# Algorithm 2026.01.14 Implementation Plan

## Source of Truth
**Document**: `Algorithm 2026.14.01.xlsx` (sheet: "rankings 2026-01-14")
**Date**: 2026-01-14

---

## Summary of Changes Required

| Priority | Change | Impact |
|----------|--------|--------|
| HIGH | F02 Height max 500 → 200 | All players with height data |
| MEDIUM | Implement F18 Weekly Goals | F/D players with goal deltas |
| MEDIUM | Implement F19 Weekly Assists | F/D players with assist deltas |
| LOW | Implement F25 Weekly EP Views | All players |
| HIGH | F26/F27 Physical Standards | Requires Admin Portal tables |
| MEDIUM | Update F35 Achievements formula | Uses direct calculation vs percentile |
| MEDIUM | Update F36 Trending formula | Uses direct calculation vs percentile |

---

## Detailed Analysis

### Factor Changes (F01-F27)

#### F02 Height - CHANGE REQUIRED
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Max Points | **200** | 500 | REDUCE |
| Source | Physical Standards tables | height_cm/height_inches | Need table reference |
| Distribution | Linear by birth year & position | Simple linear | Update formula |

**Note**: Spec says "different by birth year & position - Physical Standards in Admin Portal". We need access to these physical standards tables.

#### F07 Current Season Save Percentage
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Max Points | 300 | 300 | OK |
| Min Value | 699 | 70 (%) | CHECK scale |
| Max Value | 1000 | 100 (%) | CHECK scale |

**Note**: Spec uses 699-1000 scale (likely savePct * 1000). Current uses 70-100% scale. These are equivalent if source data stores as 0.899 (89.9%) which becomes 899.

#### F18 Weekly Points - Goals - NEW
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Points per goal | 40 | 0 (not implemented) | IMPLEMENT |
| Max Points | 200 | N/A | Cap at 200 |
| Position | F, D only | N/A | Filter by position |
| Max delta | 5 goals | N/A | Cap goal delta at 5 |

**Formula**: `MIN(goal_delta * 40, 200)` where `goal_delta = MIN(current_goals - previous_goals, 5)`

**Requirement**: Need to store previous week's stats to calculate delta.

#### F19 Weekly Points - Assists - NEW
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Points per assist | 25 | 0 (not implemented) | IMPLEMENT |
| Max Points | 125 | N/A | Cap at 125 |
| Position | F, D only | N/A | Filter by position |
| Max delta | 5 assists | N/A | Cap assist delta at 5 |

**Formula**: `MIN(assist_delta * 25, 125)` where `assist_delta = MIN(current_assists - previous_assists, 5)`

**Requirement**: Need to store previous week's stats to calculate delta.

#### F25 Weekly EP Views - CLARIFIED
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Points per view | 1 | 0 (not implemented) | IMPLEMENT |
| Max Points | 200 | N/A | Cap at 200 |
| Position | F, D, G (all) | N/A | All positions |

**Formula**: `MIN(view_delta, 200)` where `view_delta = current_views - previous_views`

**Requirement**: Need to store previous week's EP views to calculate delta.

#### F26 Weight - BLOCKED
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Max Points | 150 | 0 (not implemented) | IMPLEMENT |
| Source | Physical Standards | weight_lbs/weight_kg | Need tables |
| Distribution | Linear by birth year & position | N/A | Need tables |

**Status**: "this needs to be solved" - Blocked on Physical Standards tables in Admin Portal.

#### F27 BMI - BLOCKED
| Attribute | New Spec | Current | Action |
|-----------|----------|---------|--------|
| Max Points | 250 | 0 (not implemented) | IMPLEMENT |
| Source | Physical Standards | calculated from h/w | Need tables |
| Distribution | Linear by birth year & position | N/A | Need tables |

**Status**: "this needs to be solved" - Blocked on Physical Standards tables in Admin Portal.

---

### Rating Formulas (F31-F37)

#### F31 Performance Rating - REVIEW
**New Spec Formula (by position)**:

**Forwards**:
```
IF(0.7*(F03+F05) + 0.3*(F08+F10) >= 1; 99; ROUND(98 * (0.7*(F03+F05) + 0.3*(F08+F10))); 0))
```
Note: Using raw stats (goals_pg + assists_pg), not points.

**Defenders**:
```
IF(0.7*(F04+F05) + 0.3*(F09+F10) >= 0.8; 99; ROUND(98 * (0.7*(F04+F05) + 0.3*(F09+F10)) / 0.8; 0))
```

**Goalies**:
```
ROUND((
  IF(0.7*F06 + 0.3*F11 >= 5; 0.1 + 98*(1-(0.7*F06+0.3*F07)/5)) +
  IF(0.7*F07 + 0.3*F12 <= 500; 0.1 + 98*((0.7*F07+0.3*F12)-500)/499)
) / 2; 0)
```
Note: F07 appears in both components - this seems like an error in the spec.

**Current Implementation**: Using similar weighted formula with raw stats. Need to verify exact implementation matches.

#### F32 Level Rating - OK
```
From league table (level_category_points / league_tier_rating)
```
**Current**: Using DL_league_category_points table. Matches spec.

#### F33 Visibility Rating - OK
```
Linear 0-99 from 100-15000 EP views
IF views < 100: 0
IF views > 15000: 99
ELSE: ROUND(99 * (views - 100) / (15000 - 100))
```
**Current**: `ep_views * 99 / 15000` - Close but not exact (doesn't subtract 100 baseline).

**Action**: Update to match spec exactly.

#### F34 Physical Rating - OK
```
(F02 + F26 + F27) / 600 * 99
```
**Current**: `(f02_height + f26_weight + f27_bmi) / 600 * 99` - Matches spec.

#### F35 Achievements Rating - CHANGE REQUIRED
**New Spec**:
```
IF((F15 + F16 + F17 + F21 + F22) >= 1500; 99; ROUND(99 * (F15 + F16 + F17 + F21 + F22) / 1500; 0))
```

**Current**: Using percentile-based calculation. Need to change to direct formula.

#### F36 Trending Rating - CHANGE REQUIRED
**New Spec**:

For Forwards/Defenders:
```
IF((F18 + F19 + F25) >= 250; 99; ROUND(99 * (F18 + F19 + F25) / 250; 0))
```

For Goalies:
```
IF(F25 >= 50; 99; ROUND(99 * F25 / 50; 0))
```

**Current**: Using percentile-based calculation. Need to change to direct formula.

#### F37 Overall Rating - OK (but note F36 = 0%)
```
F31 * 0.03 + F32 * 0.70 + F33 * 0.19 + F34 * 0.05 + F35 * 0.03
```
**Note**: F36 (Trending) is NOT included in the Overall Rating calculation per the spec!

**Current**: `F31*0.03 + F32*0.70 + F33*0.19 + F34*0.05 + F35*0.03 + F36*0.00` - Matches (F36 weight = 0).

---

## Implementation Phases

### Phase 1: Immediate Changes (Can Do Now)
1. **F02 Height**: Reduce max from 500 to 200
2. **F33 Visibility**: Update formula to subtract 100 baseline
3. **F35 Achievements**: Change from percentile to direct formula

### Phase 2: Infrastructure Requirements
1. **Create weekly stats snapshot table** for F18, F19, F25 deltas
2. **Get Physical Standards tables** from Admin Portal for F26, F27

### Phase 3: Implement Delta Factors
1. **F18 Weekly Goals**: Implement once snapshot table exists
2. **F19 Weekly Assists**: Implement once snapshot table exists
3. **F25 Weekly EP Views**: Implement once snapshot table exists
4. **F36 Trending**: Update formula once F18, F19, F25 are working

### Phase 4: Physical Factors
1. **F26 Weight**: Implement once Physical Standards tables available
2. **F27 BMI**: Implement once Physical Standards tables available

---

## Questions for Stakeholder

1. **F26/F27 Physical Standards**: Where are these tables? Do they exist in Admin Portal?

2. **F31 Goalie Formula**: The spec shows F07 appearing twice in different components. Is this correct?

3. **Weekly Snapshot**: How often should we capture stat snapshots for delta calculations?
   - Daily?
   - Weekly (before API refresh)?

---

## SQL Changes Summary

### rebuild_player_rankings_consolidated.sql
```sql
-- F02: Change max from 500 to 200
LEAST(GREATEST((height_cm - 175) * 25, 0), 200)  -- was 500

-- F18: Add weekly goals calculation (once infrastructure ready)
CASE
  WHEN position IN ('F', 'D') THEN
    LEAST(LEAST(COALESCE(goal_delta, 0), 5) * 40, 200)
  ELSE 0
END AS f18_weekly_goals

-- F19: Add weekly assists calculation
CASE
  WHEN position IN ('F', 'D') THEN
    LEAST(LEAST(COALESCE(assist_delta, 0), 5) * 25, 125)
  ELSE 0
END AS f19_weekly_assists

-- F25: Add weekly EP views calculation (all positions)
LEAST(GREATEST(COALESCE(current_views - previous_views, 0), 0), 200) AS f25_weekly_views
```

### 05_update_views.sql (player_card_ratings)
```sql
-- F33 Visibility: Update to match spec exactly
CASE
  WHEN ep_views_raw < 100 THEN 0
  WHEN ep_views_raw >= 15000 THEN 99
  ELSE CAST(ROUND(99.0 * (ep_views_raw - 100) / 14900) AS INT64)
END AS visibility_rating

-- F35 Achievements: Change to direct formula
CASE
  WHEN (f15_international_points + f16_commitment_points + f17_draft_points +
        f21_tournament_points + f22_manual_points) >= 1500 THEN 99
  ELSE CAST(ROUND(99.0 * (f15_international_points + f16_commitment_points +
        f17_draft_points + f21_tournament_points + f22_manual_points) / 1500) AS INT64)
END AS achievements_rating

-- F36 Trending: Change to direct formula (once F18, F19, F25 implemented)
CASE
  WHEN position IN ('F', 'D') THEN
    CASE
      WHEN (f18_weekly_goals + f19_weekly_assists + f25_weekly_views) >= 250 THEN 99
      ELSE CAST(ROUND(99.0 * (f18_weekly_goals + f19_weekly_assists + f25_weekly_views) / 250) AS INT64)
    END
  WHEN position = 'G' THEN
    CASE
      WHEN f25_weekly_views >= 50 THEN 99
      ELSE CAST(ROUND(99.0 * f25_weekly_views / 50) AS INT64)
    END
  ELSE 0
END AS trending_rating
```

---

## File Changes Required

| File | Changes |
|------|---------|
| `03_rebuild_player_rankings_consolidated.sql` | F02 max 200, add F18/F19/F25 structure |
| `05_update_views.sql` | F33, F35, F36 formula updates |
| New: `weekly_stats_snapshot.sql` | Create snapshot table for deltas |
| New: `capture_weekly_snapshot.sql` | Script to capture weekly stats |

---

## Estimated Impact

| Change | Players Affected | Point Impact |
|--------|------------------|--------------|
| F02 200 → was 500 | ~66,000 (38% with height) | -300 max reduction |
| F33 Visibility fix | All ~159,000 | Minor (baseline adjustment) |
| F35 Achievements | ~1,600 (1% with achievements) | May increase/decrease |
| F36 Trending | 0 until F18/F19/F25 implemented | No current impact |

---

## Next Steps

1. **IMMEDIATE**: Apply Phase 1 changes (F02, F33, F35)
2. **DECISION**: Clarify F25 max points question
3. **INFRASTRUCTURE**: Create weekly snapshot system for delta calculations
4. **BLOCKED**: Wait for Physical Standards tables for F26/F27

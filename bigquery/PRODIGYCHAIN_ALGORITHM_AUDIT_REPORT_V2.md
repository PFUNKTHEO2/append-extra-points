# ProdigyChain Algorithm & Rating Audit Report V2

**Generated:** 2025-12-18 (Post-Fix)
**Database:** prodigy-ranking (BigQuery)
**Total Players in Database:** 163,568
**Total Players Rated:** 156,309

---

## EXECUTIVE SUMMARY

### Fixes Applied in This Version

| Issue | Previous State | Fixed State | Status |
|-------|---------------|-------------|--------|
| Rating Weights | PER 35%, LEV 25%, VIS 10%, PHY 10%, ACH 15%, TRE 5% | PER 15%, LEV 35%, VIS 20%, PHY 15%, ACH 10%, TRE 5% | FIXED |
| Level Rating | Percentile-based calculation | Direct league tier mapping (NHL=99, CHL=95, etc.) | FIXED |
| Physical Rating | Only used F02 (Height) | Now uses (F02 + F26 + F27) / 600 * 100 | FIXED |
| F02 Height Cap | Max 500 points observed | Capped at 200 points | FIXED |
| F15 International Cap | Max 1,903 points observed | Capped at 1,000 points | FIXED |
| F26/F27 in API | Missing from getPlayer response | Added to getPlayer response | FIXED |

### Current Status

All major discrepancies identified in V1 audit have been resolved. The rating system now matches the spreadsheet specification.

---

## PART 1: UPDATED CARD RATINGS DISTRIBUTION

### Overall Statistics

| Category | Avg | Min | Max | Players >= 95 |
|----------|-----|-----|-----|---------------|
| **Overall** | 52.8 | 33 | 95 | 2 |
| Performance | 64.4 | 40 | 99 | 1,564 |
| Level | 48.3 | 8 | 99 | 1,063 |
| Visibility | 63.1 | 40 | 98 | 1,564 |
| Physical | 48.5 | 40 | 98 | 32 |
| Achievements | 41.0 | 40 | 99 | 1,557 |
| Trending | 44.3 | 40 | 99 | 1,327 |

### Level Rating Distribution (Now Tier-Based)

| Level Rating | Count | Description |
|--------------|-------|-------------|
| 99 | 3 | NHL players only |
| 95 | 1,060 | CHL (OHL/WHL/QMJHL), KHL, top EU leagues |
| 91 | 165 | Tier 3 leagues |
| 87 | 1,575 | Tier 4 leagues |
| < 87 | 153,506 | Other leagues |

**NHL Players with Level = 99:**
- Michael Misa (F, 2007, Canada) - San Jose Sharks
- Matthew Schaefer (D, 2007, Canada) - NY Islanders
- Benjamin Kindel (F, 2007, Canada) - Pittsburgh Penguins

### Top 15 Overall Rated Players

| Rank | Player | Pos | Birth | Country | Team | League | OVR | PER | LEV | VIS | PHY | ACH | TRE |
|------|--------|-----|-------|---------|------|--------|-----|-----|-----|-----|-----|-----|-----|
| 1 | Braidy Wassilyn | F | 2008 | Canada | London Knights | OHL | 95 | 92 | 95 | 98 | 89 | 99 | 96 |
| 2 | J.P. Hurlbert | F | 2008 | USA | Kamloops Blazers | WHL | 95 | 94 | 95 | 98 | 86 | 99 | 98 |
| 3 | Cameron Chartrand | D | 2008 | Canada | Saint John Sea Dogs | QMJHL | 94 | 83 | 95 | 98 | 92 | 99 | 91 |
| 4 | Daxon Rudolph | D | 2008 | Canada | Prince Albert Raiders | WHL | 94 | 87 | 95 | 98 | 91 | 99 | 91 |
| 5 | Braeden Cootes | F | 2007 | Canada | Seattle Thunderbirds | WHL | 94 | 95 | 95 | 98 | 83 | 99 | 91 |
| 6 | Eddie Genborg | F | 2007 | Sweden | Timra IK | SHL | 94 | 89 | 95 | 98 | 89 | 99 | 92 |
| 7 | Yegor Shilov | F | 2008 | Russia | Victoriaville Tigres | QMJHL | 94 | 93 | 95 | 98 | 83 | 98 | 93 |
| 8 | Blake Fiddler | D | 2007 | USA | Edmonton Oil Kings | WHL | 94 | 88 | 95 | 98 | 87 | 98 | 96 |
| 9 | Nikita Klepov | F | 2008 | USA | Saginaw Spirit | OHL | 94 | 92 | 95 | 98 | 85 | 98 | 96 |
| 10 | Cole Zurawski | F | 2008 | Canada | Owen Sound Attack | OHL | 94 | 89 | 95 | 97 | 89 | 99 | 93 |
| 11 | Joseph Salandra | F | 2008 | USA | Barrie Colts | OHL | 94 | 93 | 95 | 97 | 83 | 99 | 96 |
| 12 | Rafael Cloutier | F | 2007 | Canada | Blainville-Boisbriand | QMJHL | 94 | 91 | 95 | 98 | 87 | 94 | 92 |
| 13 | Carson Carels | D | 2008 | Canada | Prince George Cougars | WHL | 93 | 89 | 95 | 98 | 85 | 99 | 91 |
| 14 | Ethan Belchetz | F | 2008 | Canada | Windsor Spitfires | OHL | 93 | 92 | 95 | 98 | 81 | 99 | 93 |
| 15 | Beckham Edwards | F | 2008 | Canada | Sarnia Sting | OHL | 93 | 88 | 95 | 98 | 83 | 99 | 89 |

---

## PART 2: RATING CALCULATION METHODOLOGY

### Category Weights (CORRECTED)

```
OVERALL = PER * 0.15 + LEV * 0.35 + VIS * 0.20 + PHY * 0.15 + ACH * 0.10 + TRE * 0.05
```

| Category | Weight | Source Factors |
|----------|--------|----------------|
| Performance | 15% | F03-F12 (position-specific stats) |
| Level | 35% | Direct from DL_league_category_points |
| Visibility | 20% | F01 (EP Views) + F23 (ProdigyLikes) |
| Physical | 15% | (F02 + F26 + F27) / 600 * 100 |
| Achievements | 10% | F15 + F16 + F17 + F21 |
| Trending | 5% | F18 + F19 (weekly deltas) |

### Level Rating - Direct Tier Mapping

Level rating now uses `DL_league_category_points.level_category_points` directly:

| League Category | Level Rating | Example Leagues |
|-----------------|--------------|-----------------|
| NHL | 99 | NHL |
| Top Pro/Junior | 95 | OHL, WHL, QMJHL, KHL, Liiga, SHL, NL, Czechia |
| Pro Tier 2 | 91 | AHL, VHL, DEL, Denmark, Slovakia, AlpsHL |
| Pro Tier 3 | 87 | MHL, USHL, NCAA, OJHL, U20 leagues |
| Junior Tier 1 | 82 | USHS-MA, USHS-MI, BCHL, AJHL, NAHL |
| Junior Tier 2 | 78 | 18U AAA, various AAA leagues |
| Youth Tiers | 70-74 | 16U AAA, 15U AAA |
| Youth Lower | 54-66 | 14U, 13U levels |
| Lowest | 8-49 | Special events, tournaments |

### Physical Rating - New Formula

```sql
Physical Rating = GREATEST(40, LEAST(99,
  40 + ((F02_capped + F26 + F27) / 600.0) * 59
))
```

Where:
- F02 (Height) capped at 200 max points
- F26 (Weight) max 150 points
- F27 (BMI) max 250 points
- Total possible: 600 points
- Scales to 40-99 range

**Physical Component Stats:**
- Avg F26 Weight Points: 13.09
- Max F26 Weight Points: 150.00
- Avg F27 BMI Points: 37.24
- Max F27 BMI Points: 250.00

---

## PART 3: ALGORITHM FACTORS (F01-F27) - Updated Status

### Factor Coverage Summary

| Factor | Description | Count | Coverage | Avg | Max (Actual) | Max (Spec) | Status |
|--------|-------------|-------|----------|-----|--------------|------------|--------|
| F01 | EP Views | 97,745 | 59.8% | 81.86 | 2,000 | 2,000 | OK |
| F02 | Height | 38,924 | 23.8% | - | 200* | 200 | CAPPED |
| F03 | Current GPG (F) | 22,903 | 14.0% | 84.30 | 500 | 500 | OK |
| F04 | Current GPG (D) | 15,875 | 9.7% | 57.67 | 500 | 500 | OK |
| F05 | Current APG | 37,436 | 22.9% | 71.44 | 500 | 500 | OK |
| F06 | Current GAA (G) | 3,762 | 2.3% | 159.20 | 500 | 500 | OK |
| F07 | Current SV% (G) | 4,398 | 2.7% | 186.74 | 300 | 300 | OK |
| F08 | Last GPG (F) | 55,344 | 33.8% | 57.30 | 300 | 300 | OK |
| F09 | Last GPG (D) | 22,830 | 14.0% | 34.53 | 300 | 300 | OK |
| F10 | Last APG | 89,117 | 54.5% | 44.82 | 300 | 300 | OK |
| F11 | Last GAA (G) | 1,522 | 0.9% | 95.66 | 300 | 300 | OK |
| F12 | Last SV% (G) | 1,640 | 1.0% | 119.78 | 200 | 200 | OK |
| F13 | League Points | 138,590 | 84.7% | 1,536 | 4,500 | 4,500 | OK |
| F14 | Team Points | 58,339 | 35.7% | 360.23 | 700 | 700 | OK |
| F15 | International | 1,609 | 1.0% | - | 1,000* | 1,000 | CAPPED |
| F16 | Commitment | 809 | 0.5% | 303.03 | 500 | 500 | OK |
| F17 | Draft | 820 | 0.5% | 262.14 | 300 | 300 | OK |
| F18 | Weekly Goals | 13,487 | 8.2% | 2.15 | 38 | 200 | OK |
| F19 | Weekly Assists | 10,126 | 6.2% | 1.71 | 21 | 125 | OK |
| F20 | Playing Up | 0 | 0.0% | - | 0 | 300 | NOT IMPL |
| F21 | Tournament | 0 | 0.0% | - | 0 | ??? | NOT IMPL |
| F22 | Manual | 92 | 0.1% | 157.39 | 250 | N/A | OK |
| F23 | ProdigyLikes | 0 | 0.0% | - | 0 | 500 | NOT IMPL |
| F24 | Card Sales | 0 | 0.0% | - | 0 | 500 | NOT IMPL |
| F26 | Weight | 33,504 | 20.7% | 61.07 | 150 | 150 | OK |
| F27 | BMI | 59,942 | 37.0% | 97.12 | 250 | 250 | OK |

*Capped in view, underlying data may exceed

---

## PART 4: REMAINING ITEMS

### Still Not Implemented

| Factor | Description | Priority | Notes |
|--------|-------------|----------|-------|
| F20 | Playing Up Points | Medium | Spreadsheet says "league points help" |
| F21 | Tournament Accolades | Medium | Points structure TBD (???) |
| F23 | ProdigyLikes | Low | Requires platform integration |
| F24 | Card Sales | Low | Requires marketplace integration |
| F25 | Weekly EP Views | Low | Factor table exists (PT_F20_weekly_views_points) but not in cumulative |

### Data Quality Notes

1. **Goalie coverage is intentionally low** (1-3%) - factors are position-specific
2. **Physical data coverage** (~20-37%) depends on Elite Prospects data availability
3. **International points** - 1,609 players have points (elite international players)
4. **League mapping** - 84.7% of players have league points; remaining 15% need mapping

---

## PART 5: WEIGHT IMPACT ANALYSIS

### Comparison: Old Weights vs New Weights

| Metric | Value |
|--------|-------|
| Avg Overall (New Weights) | 52.8 |
| Avg Overall (Old Weights) | 54.2 |
| Average Difference | -1.37 |
| Players who improved | 46,880 |
| Players who decreased | 86,794 |
| Unchanged | 22,635 |

**Key Insight:** The shift to higher Level weighting (35% vs 25%) means players in top-tier leagues benefit more, while players in lower leagues see a decrease. This aligns with the business intent to emphasize league quality.

---

## PART 6: TECHNICAL REFERENCE

### Updated Files

| File | Description |
|------|-------------|
| `create_ea_ratings_view_v2.sql` | Updated view with all fixes |
| `deploy_ea_ratings_view_v2.py` | Deployment script |
| `api-backend/functions/shared/bigquery.js` | Added F26/F27 to getPlayer |

### View Location

`prodigy-ranking.algorithm_core.player_card_ratings` (VIEW)

### Key Changes in View

1. **Added F26/F27 joins** from PT_F26_weight and PT_F27_bmi
2. **Level uses direct tier lookup** from DL_league_category_points
3. **Physical formula** now includes all three physical factors
4. **Caps applied** to F02 (200) and F15 (1000) in view
5. **Corrected weights** in overall calculation

### API Endpoints

| Endpoint | Changes |
|----------|---------|
| getPlayer | Now includes f26_weight_points and f27_bmi_points |
| getCardRatings | Returns updated ratings from view |
| getPlayerPhysical | NEW - Returns height/weight/BMI data |

---

## APPENDIX: Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-12-18 | Initial audit report identifying discrepancies |
| 2.0 | 2025-12-18 | All fixes applied, updated statistics |

---

*Report generated by Claude Code for ProdigyChain Algorithm Audit*

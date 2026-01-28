# NEPSAC Rankings & Predictions - Technical Documentation

## Overview

This document explains how power rankings, team OVR ratings, and all six tournament probabilities are calculated in the Prodigy PowerGrid system.

---

## 1. Power Rankings (Positions 1-57)

Power rankings are a **composite score** from multiple ranking sources.

### Data Source
- File: `nepsac_power_rankings.csv`
- Table: `algorithm_core.nepsac_team_rankings`

### Ranking Components

| Source | Weight | Description |
|--------|--------|-------------|
| **JSPR** | Part of 70% | Junior Scouts Power Rankings |
| **NEHJ** | Part of 70% | New England Hockey Journal Expert Rankings |
| **Performance ELO** | Part of 70% | ELO rating based on actual game results |
| **MHR** | Part of 70% | MyHockeyRankings |
| **Win %** | Part of 70% | Current season win percentage |
| **Recent Form** | Part of 70% | Last 5 games performance |
| **Roster Average** | 30% | Average Prodigy Points across roster |

### Example
```
#1 Dexter: Score 92.4
   JSPR: #3, NEHJ: #1, Performance: #1, MHR: #2
   Record: 16-1-2 (89.5%), Form: 5-0-0
   Roster Avg: 9,808.1 points
```

---

## 2. Team OVR Rating (70-99 Scale)

### Formula
```
OVR = 70 + ((avgProdigyPoints - 750) / 2200) × 29
```

### Explanation
- Minimum OVR: 70 (for teams with avg points ≤ 750)
- Maximum OVR: 99 (for teams with avg points ≥ 2950)
- Linear scaling between these bounds

### Code Location
- `powergrid.js` - calculated from `avg_prodigy_points` field

---

## 3. NEPSAC Playoff Structure

Understanding the playoff structure is critical for probability calculations:

### Three Tournaments (Mutually Exclusive)

1. **Elite 8 Tournament**
   - Top 8 teams OVERALL (Large + Small combined by power rank)
   - These 8 teams compete for Elite 8 Championship
   - Teams in Elite 8 do NOT play in division tournaments

2. **Large School Tournament**
   - Large schools (enrollment ≥ 225) who MISSED Elite 8
   - Top 8 Large schools not in Elite 8 get bids
   - Compete for Large School Championship

3. **Small School Tournament**
   - Small schools (enrollment < 225) who MISSED Elite 8
   - Top 8 Small schools not in Elite 8 get bids
   - Compete for Small School Championship

### Key Principle
**A team can only be in ONE tournament.** Making Elite 8 means you cannot be in your division tournament.

---

## 4. Six Probability Calculations

Each team has 6 probabilities calculated:

| Probability | Description |
|-------------|-------------|
| `elite8Bid` | Chance of being top 8 overall |
| `elite8Champ` | Chance of winning Elite 8 Championship |
| `largeSchoolBid` | Chance of making Large tournament (if missed Elite 8) |
| `largeSchoolChamp` | Chance of winning Large School Championship |
| `smallSchoolBid` | Chance of making Small tournament (if missed Elite 8) |
| `smallSchoolChamp` | Chance of winning Small School Championship |

---

### 4.1 Elite 8 Bid Probability

**Code Location:** `powergrid.js:187-204` (`calculateElite8BidProb`)

**Method:** Position-based formula by current power rank

| Power Rank | Probability |
|------------|-------------|
| 1 | 99% |
| 2 | 97% |
| 3 | 95% |
| 4 | 93% |
| 5 | 90% |
| 6 | 80% |
| 7 | 70% |
| 8 | 60% |
| 9 | 45% |
| 10 | 35% |
| 11 | 25% |
| 12 | 15% |
| 13 | 10% |
| 14 | 8% |
| 15 | 6% |
| 16 | 4% |
| 17+ | <3% (decreasing) |

---

### 4.2 Elite 8 Championship Probability

**Code Location:** `powergrid.js:210-226` (`calculateElite8ChampProb`)

**Method:** Softmax over OVR ratings of contenders (ranks 1-12)

**Formula:**
```
P(team wins Elite 8) = exp(OVR / 10) / Σ exp(OVR_i / 10)
```

Where the sum is over all teams ranked 1-12.

**Constraints:**
- Teams ranked > 12: Fixed 0.1% probability
- Maximum probability capped at 35%

**Why Softmax?**
- Provides smooth probability distribution
- Higher OVR = exponentially higher win probability
- All probabilities sum to ~100%

---

### 4.3 Division Bid Probability

**Code Location:** `powergrid.js:242-286` (`calculateDivisionBidProb`)

**Method:** Conditional probability calculation

**Formula:**
```
P(division tournament) = P(miss Elite 8) × P(make division | missed Elite 8)
```

**Example: Dexter (#1 overall, Large School)**
- P(miss Elite 8) = 1 - 99% = 1%
- P(make Large School | missed Elite 8) = 99% (they're best Large school)
- P(Large School tournament) = 1% × 99% ≈ **1%**

**Example: Westminster (#15 overall, Large School)**
- P(miss Elite 8) = 1 - 6% = 94%
- P(make Large School | missed Elite 8) = ~70% (based on class rank)
- P(Large School tournament) = 94% × 70% ≈ **66%**

**Conditional Probabilities (for teams already outside Elite 8):**

| Class Rank Among Non-Elite-8 | P(make division \| missed Elite 8) |
|------------------------------|-----------------------------------|
| 1-4 | 98%, 95%, 92%, 89% |
| 5-8 | 85%, 77%, 69%, 61% |
| 9-12 | 50%, 40%, 30%, 20% |
| 13+ | <15% (decreasing) |

---

### 4.4 Division Championship Probability

**Code Location:** `powergrid.js:298-334` (`calculateDivisionChampProb`)

**Method:** Conditional probability with softmax

**Formula:**
```
P(division champ) = P(miss Elite 8) × P(make division | missed) × P(win | in division)
```

**P(win | in division)** calculation:
- Uses softmax over OVR ratings of likely division participants
- Division contenders = teams ranked > 8 in their classification, limited to top 12
- Same softmax formula as Elite 8 Championship

**Constraints:**
- If divisionBidProb < 1%, return 0.1%
- Maximum capped at 25%

---

## 5. Game-by-Game Predictions

Individual game predictions use multiple factors:

### Inputs
1. **Power rank difference** between teams
2. **OVR difference** between teams
3. **Home ice advantage** (slight boost to home team)
4. **Recent form** (last 5 games)

### Confidence Tiers

| Tier | Confidence Range | Meaning |
|------|------------------|---------|
| Very High | 70%+ | Large rank/OVR gap |
| High | 65-69% | Significant advantage |
| Medium | 58-64% | Clear favorite |
| Low | 52-57% | Slight edge |
| Toss-up | <52% | Coin flip |

### Code Location
- Predictions stored in: `algorithm_core.nepsac_schedule`
- Fields: `predicted_winner_id`, `prediction_confidence`

---

## 6. Data Architecture (Single Source of Truth)

```
┌──────────────────────────────────────────────────────────────┐
│                      DATA FLOW                               │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│   NEPSAC PDF ────────┐                                       │
│   (Classifications)  │                                       │
│                      ▼                                       │
│               ┌──────────────┐                               │
│               │   BigQuery   │  ◄── Single Source of Truth   │
│               │ (algorithm_  │                               │
│               │    core)     │                               │
│               └──────┬───────┘                               │
│                      │                                       │
│          ┌──────────┴──────────┐                             │
│          ▼                     ▼                             │
│   ┌──────────────┐     ┌──────────────┐                      │
│   │ Cloud Funcs  │     │  Supabase    │                      │
│   │   (APIs)     │     │  (Sync Copy) │                      │
│   └──────┬───────┘     └──────┬───────┘                      │
│          │                    │                              │
│          └────────┬───────────┘                              │
│                   ▼                                          │
│            ┌──────────────┐                                  │
│            │   Frontend   │                                  │
│            │  (/gameday)  │                                  │
│            └──────────────┘                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### BigQuery Tables

| Table | Purpose |
|-------|---------|
| `nepsac_teams` | 57 teams, classification (Large/Small), enrollment |
| `nepsac_team_rankings` | Power rank, OVR, roster stats by season |
| `nepsac_standings` | W-L-T records, goals, streaks |
| `nepsac_schedule` | Games, predictions, results |

### Classification Source
- **Official Document:** `NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf`
- **Rule:** Enrollment ≥ 225 = Large School (28 teams)
- **Rule:** Enrollment < 225 = Small School (29 teams)

---

## 7. API Endpoints

### Power Rankings
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26
```

### PowerGrid (All 6 Probabilities)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26
```

### Sync to Supabase
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/syncNepsacData?season=2025-26
```

---

## 8. Code References

| File | Function | Purpose |
|------|----------|---------|
| `powergrid.js:187` | `calculateElite8BidProb()` | Elite 8 bid probability |
| `powergrid.js:210` | `calculateElite8ChampProb()` | Elite 8 championship probability |
| `powergrid.js:242` | `calculateDivisionBidProb()` | Division bid probability |
| `powergrid.js:298` | `calculateDivisionChampProb()` | Division championship probability |
| `powergrid.js:348` | `getNepsacPowerGrid` | Main API endpoint |
| `nepsac-sync.js` | `syncNepsacData` | BigQuery → Supabase sync |

---

## 9. Important Notes

1. **Never recalculate rankings** - Use `rank` field from BigQuery as-is
2. **Probabilities are mutually exclusive** - Elite 8 OR division, not both
3. **All data changes go through BigQuery first** - Supabase is downstream
4. **Classification is official** - From NEPSAC PDF, not calculated

---

*Last Updated: 2026-01-27*

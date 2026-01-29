# NEPSAC GameDay System - Complete Technical Manual

**Version:** 1.0
**Last Updated:** January 28, 2026
**System:** Prodigy Rankings NEPSAC Module

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Architecture](#2-architecture)
3. [Data Storage](#3-data-storage)
4. [API Endpoints](#4-api-endpoints)
5. [Prediction Algorithm](#5-prediction-algorithm)
6. [American Odds Conversion](#6-american-odds-conversion)
7. [PowerGrid Tournament Probabilities](#7-powergrid-tournament-probabilities)
8. [Past Performance Tracking](#8-past-performance-tracking)
9. [Admin Portal](#9-admin-portal)
10. [Frontend Components](#10-frontend-components)
11. [Data Sync Process](#11-data-sync-process)
12. [Team Classifications](#12-team-classifications)
13. [Deployment](#13-deployment)

---

## 1. System Overview

The NEPSAC GameDay system provides real-time predictions, power rankings, and tournament probability analysis for New England Prep School Athletic Council (NEPSAC) boys ice hockey.

### Key Features
- **Game Predictions**: AI-powered win probability predictions with American odds
- **Power Rankings**: Prodigy Power Rankings combining performance and roster strength
- **PowerGrid**: Tournament probability simulator for Elite 8 and division tournaments
- **Past Performance**: Historical accuracy tracking with detailed breakdowns
- **Team Rosters**: Player-level data with ProdigyPoints ratings
- **Trading Cards**: EA Sports-style OVR ratings for players and teams

### Technology Stack
- **Backend**: Google Cloud Functions (Node.js 20)
- **Primary Database**: Google BigQuery (Single Source of Truth)
- **Frontend Database**: Supabase (PostgreSQL) - synced replica
- **Frontend**: React/TypeScript with Vite
- **Hosting**: Cloud Functions + Supabase + GitHub Pages

---

## 2. Architecture

### Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DATA SOURCES                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│  Elite Prospects API    NeutralZone Schedules    MyHockeyRankings           │
│         ↓                       ↓                        ↓                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BIGQUERY (Single Source of Truth)                         │
│                    Project: prodigy-ranking                                  │
│                    Dataset: algorithm_core                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│  nepsac_teams          nepsac_schedule        nepsac_standings               │
│  nepsac_rosters        nepsac_team_rankings   nepsac_game_performers         │
│  nepsac_predictions_log                                                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                  ↓
                    ┌─────────────┴─────────────┐
                    ↓                           ↓
┌───────────────────────────────┐   ┌───────────────────────────────────────┐
│   CLOUD FUNCTIONS (APIs)       │   │        SUPABASE (Sync Copy)           │
│   us-central1                  │   │        PostgreSQL + RLS               │
├───────────────────────────────┤   ├───────────────────────────────────────┤
│  nepsac.js (9 endpoints)       │   │  nepsac_teams                         │
│  powergrid.js (1 endpoint)     │   │  nepsac_games                         │
│  nepsac-sync.js (3 endpoints)  │   │  nepsac_game_performers               │
│  admin.js (monitoring)         │   │  nepsac_overall_stats                 │
└───────────────────────────────┘   │  nepsac_daily_summary                 │
                    ↓               └───────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND                                           │
├─────────────────────────────────────────────────────────────────────────────┤
│  React Components (BMI_UI)              Lovable.dev (Production)            │
│  - NepsacGameDay.tsx                    - aceandscouty.com                  │
│  - NepsacMatchup.tsx                    - Stories Generator                 │
│  - NepsacPastPerformance.tsx            - Admin Portal                      │
│  - NepsacPowerRankings.tsx                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### File Structure

```
bigquery/
├── api-backend/
│   ├── functions/
│   │   ├── nepsac.js           # Main NEPSAC endpoints
│   │   ├── powergrid.js        # PowerGrid tournament probabilities
│   │   ├── nepsac-sync.js      # BigQuery → Supabase sync
│   │   ├── admin.js            # Admin/monitoring endpoints
│   │   ├── index.js            # Main rankings endpoints
│   │   └── shared/
│   │       └── bigquery.js     # BigQuery client helper
│   ├── database/
│   │   ├── nepsac-schema.sql           # BigQuery schemas
│   │   └── nepsac-predictions-supabase.sql  # Supabase schemas
│   └── data/
│       └── nepsac_official_classifications.json
├── frontend-integration/
│   └── BMI_UI/
│       └── client/src/
│           ├── lib/nepsac-api.ts       # TypeScript API client
│           ├── pages/NepsacGameDay.tsx # Main GameDay page
│           └── components/nepsac/      # NEPSAC components
└── NEPSAC_SYSTEM_MANUAL.md             # This document
```

---

## 3. Data Storage

### 3.1 BigQuery Tables (Primary)

**Dataset:** `prodigy-ranking.algorithm_core`

#### `nepsac_teams`
Master table for all 57 NEPSAC member schools.

| Column | Type | Description |
|--------|------|-------------|
| team_id | STRING | Primary key (e.g., "salisbury", "dexter") |
| team_name | STRING | Full name (e.g., "Salisbury School") |
| short_name | STRING | Display name (e.g., "Salisbury") |
| classification | STRING | "Large" or "Small" |
| enrollment | INT64 | School enrollment number |
| logo_url | STRING | Team logo URL (NeutralZone) |
| card_home_url | STRING | Trading card image (home) |
| card_away_url | STRING | Trading card image (away) |
| primary_color | STRING | Hex color code |
| secondary_color | STRING | Hex color code |
| venue | STRING | Home arena name |
| city | STRING | City |
| state | STRING | State abbreviation |
| ep_team_id | INT64 | Elite Prospects team ID |
| mhr_team_id | INT64 | MyHockeyRankings team ID |

#### `nepsac_schedule`
Game schedule with predictions.

| Column | Type | Description |
|--------|------|-------------|
| game_id | STRING | Primary key (UUID) |
| season | STRING | "2025-26" |
| game_date | DATE | Game date |
| game_time | STRING | "4:30 PM" |
| day_of_week | STRING | "Wednesday" |
| away_team_id | STRING | FK to nepsac_teams |
| home_team_id | STRING | FK to nepsac_teams |
| venue | STRING | Game venue |
| city | STRING | City |
| status | STRING | scheduled/in_progress/final/postponed/cancelled |
| away_score | INT64 | Final score (null if not complete) |
| home_score | INT64 | Final score (null if not complete) |
| overtime | BOOL | Game went to overtime |
| shootout | BOOL | Game decided in shootout |
| predicted_winner_id | STRING | Team ID of predicted winner |
| prediction_confidence | INT64 | 50-99 percent |
| prediction_method | STRING | Algorithm version |

#### `nepsac_standings`
Current season standings.

| Column | Type | Description |
|--------|------|-------------|
| standing_id | STRING | Primary key |
| team_id | STRING | FK to nepsac_teams |
| season | STRING | "2025-26" |
| division | STRING | Classification |
| wins | INT64 | Win count |
| losses | INT64 | Loss count |
| ties | INT64 | Tie count |
| overtime_losses | INT64 | OT loss count |
| goals_for | INT64 | Total goals scored |
| goals_against | INT64 | Total goals allowed |
| goal_differential | INT64 | GF - GA |
| win_pct | FLOAT64 | (W + 0.5*T) / GP |
| games_played | INT64 | Total games |
| streak | STRING | "W3", "L1", etc. |
| last_10 | STRING | "7-2-1" |

#### `nepsac_team_rankings`
ProdigyPoints-based team rankings.

| Column | Type | Description |
|--------|------|-------------|
| ranking_id | STRING | Primary key |
| team_id | STRING | FK to nepsac_teams |
| season | STRING | "2025-26" |
| rank | INT64 | 1-based power ranking (SOURCE OF TRUTH) |
| roster_size | INT64 | Total players on roster |
| matched_players | INT64 | Players matched to database |
| match_rate | FLOAT64 | matched / roster_size |
| avg_prodigy_points | FLOAT64 | Average points per player |
| total_prodigy_points | FLOAT64 | Sum of all player points |
| max_prodigy_points | FLOAT64 | Top player's points |
| top_player_id | INT64 | Player ID of top player |
| top_player_name | STRING | Name of top player |
| team_ovr | INT64 | EA Sports OVR (70-99) |
| calculated_at | TIMESTAMP | Last calculation time |

#### `nepsac_rosters`
Player-team assignments.

| Column | Type | Description |
|--------|------|-------------|
| roster_id | STRING | Primary key |
| team_id | STRING | FK to nepsac_teams |
| player_id | INT64 | FK to player_cumulative_points |
| roster_name | STRING | Name as appears on roster |
| position | STRING | F, D, or G |
| grad_year | INT64 | Graduation year |
| jersey_number | STRING | Jersey number |
| season | STRING | "2025-26" |
| is_captain | BOOL | Team captain |
| is_active | BOOL | Currently active |
| match_confidence | FLOAT64 | 0-1 name match confidence |
| image_url | STRING | Player photo URL |

#### `nepsac_game_performers`
Per-game individual player statistics.

| Column | Type | Description |
|--------|------|-------------|
| performer_id | STRING | Primary key |
| game_id | STRING | FK to nepsac_schedule |
| game_date | DATE | Game date |
| player_id | INT64 | FK (may be null) |
| roster_name | STRING | Player name |
| team_id | STRING | FK to nepsac_teams |
| position | STRING | F, D, or G |
| goals | INT64 | Goals scored |
| assists | INT64 | Assists |
| points | INT64 | G + A |
| plus_minus | INT64 | Plus/minus |
| pim | INT64 | Penalty minutes |
| shots | INT64 | Shots on goal |
| saves | INT64 | Saves (goalies) |
| goals_against | INT64 | Goals against (goalies) |
| save_pct | FLOAT64 | Save percentage |
| is_shutout | BOOL | Shutout game |
| is_star_of_game | BOOL | Named star |
| star_rank | INT64 | 1, 2, or 3 |
| source | STRING | Data source |

### 3.2 Supabase Tables (Sync Copy)

Supabase mirrors BigQuery data for real-time frontend access with Row-Level Security (RLS).

**Key differences:**
- Uses UUID primary keys
- Adds `created_at`, `updated_at` timestamps
- `classification` → `division` column rename
- Adds computed fields like `prediction_correct`, `is_tie`

---

## 4. API Endpoints

**Base URL:** `https://us-central1-prodigy-ranking.cloudfunctions.net`

### 4.1 Game Schedule & Information

#### `GET /getNepsacSchedule`
Returns all games for a specific date.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| date | string | Yes | - | YYYY-MM-DD format |
| season | string | No | "2025-26" | Season identifier |

**Response:**
```json
{
  "date": "2026-01-22",
  "season": "2025-26",
  "gameCount": 5,
  "games": [
    {
      "gameId": "7a054cba-2b98-4c3c-9195-4048b95d2393",
      "gameDate": "2026-01-22",
      "gameTime": "4:00 PM",
      "dayOfWeek": "Wednesday",
      "venue": "Taft School",
      "status": "scheduled",
      "awayTeam": {
        "teamId": "taft",
        "name": "Taft School",
        "shortName": "Taft",
        "logoUrl": "https://...",
        "cardUrl": "https://...",
        "division": "Large",
        "rank": 15,
        "ovr": 78,
        "record": { "wins": 5, "losses": 3, "ties": 1 }
      },
      "homeTeam": { ... },
      "prediction": {
        "winnerId": "taft",
        "confidence": 62,
        "confidenceOdds": "-163",
        "status": "available"
      }
    }
  ]
}
```

#### `GET /getNepsacMatchup`
Returns full matchup data for a specific game.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| gameId | string | Yes | Game UUID |

**Response includes:**
- Game details (date, time, venue, prediction)
- Both teams with full stats and rankings
- Top 6 players per team with ProdigyPoints
- OVR ratings for players and teams

#### `GET /getNepsacGameDates`
Returns all dates with scheduled games.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| season | string | No | "2025-26" | Season |
| month | number | No | - | Filter by month (1-12) |

#### `GET /getNepsacPastResults`
Returns completed games with prediction accuracy.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| season | string | No | "2025-26" | Season |
| limit | number | No | 100 | Max games to return |

**Response includes:**
- Summary stats (accuracy, correct, incorrect, ties)
- Games grouped by date
- Per-game prediction results

### 4.2 Team Data

#### `GET /getNepsacTeams`
Returns all NEPSAC teams with rankings.

#### `GET /getNepsacRoster`
Returns full team roster with player stats.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| teamId | string | Yes | Team identifier |
| season | string | No | Default: "2025-26" |

#### `GET /getNepsacStandings`
Returns current standings by division.

#### `GET /getNepsacPowerRankings`
Returns Prodigy Power Rankings (top 20 teams).

**Power Ranking Formula:**
- 70% Performance: JSPR, NEHJ Expert, Performance ELO, MHR, Win%, Form
- 30% Roster: Average ProdigyPoints, Top Player, Roster Depth

### 4.3 PowerGrid

#### `GET /getNepsacPowerGrid`
Returns tournament probability simulator.

**Response includes:**
- All teams with 6 probability fields + American odds
- Current Elite 8 snapshot
- Large School contenders
- Small School contenders
- Bubble teams (ranks 7-12)

### 4.4 Player Performance

#### `GET /getNepsacTopPerformers`
Returns top individual performers for a date.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| date | string | Yes | YYYY-MM-DD |
| limit | number | No | Default: 6, Max: 20 |

#### `POST /addNepsacGamePerformers`
Admin endpoint to add game performers.

---

## 5. Prediction Algorithm

### 5.1 OVR Rating Calculation

**Player OVR (70-99 scale):**
```javascript
function calculateOVR(points, maxPoints) {
  if (!points || points <= 0) return 70;
  const normalized = Math.min(points / maxPoints, 1);
  return Math.round(70 + normalized * 29);
}
```

**Team OVR:**
```javascript
function calculateTeamOVR(avgPoints) {
  const minAvg = 750;    // Bottom threshold
  const maxAvg = 2950;   // Top threshold
  const normalized = Math.max(0, Math.min(
    (avgPoints - minAvg) / (maxAvg - minAvg), 1
  ));
  return Math.round(70 + normalized * 29);
}
```

### 5.2 Prediction Confidence

Predictions require both teams to have ranking data (`avg_prodigy_points > 0`).

**Confidence Tiers:**
| Confidence | Tier | Description |
|------------|------|-------------|
| >= 70% | Very High | Strong favorite |
| >= 65% | High | Clear favorite |
| >= 58% | Medium | Moderate favorite |
| >= 52% | Low | Slight favorite |
| 50-51% | Toss-up | Essentially even |

### 5.3 Prediction Model Weights (v2.1)

| Factor | Weight | Description |
|--------|--------|-------------|
| MHR Rating | 30% | MyHockeyRankings team rating |
| Top Player | 15% | Best player's ProdigyPoints |
| Recent Form | 15% | Last 5 games performance |
| Win Percentage | 15% | Season win rate |
| Head-to-Head | 8% | Historical matchup results |
| ProdigyPoints | 7% | Team average points |
| Home Advantage | 5% | Home ice factor |
| Expert Rank | 3% | NEHJ/JSPR rankings |
| Goal Differential | 2% | Goals for - against |

---

## 6. American Odds Conversion

### 6.1 Formula

```javascript
function probabilityToAmericanOdds(probability) {
  // Edge cases
  if (probability >= 99.9) return -10000;
  if (probability <= 0.1) return 10000;
  if (probability === 50) return 100;

  // Favorites (negative odds)
  if (probability > 50) {
    const odds = -Math.round((probability / (100 - probability)) * 100);
    return Math.max(-10000, odds);
  }

  // Underdogs (positive odds)
  const odds = Math.round(((100 - probability) / probability) * 100);
  return Math.min(10000, odds);
}
```

### 6.2 Reference Table

| Probability | American Odds | Meaning |
|-------------|---------------|---------|
| 50% | +100 | Even money |
| 55% | -122 | Slight favorite |
| 60% | -150 | Moderate favorite |
| 65% | -186 | Strong favorite |
| 70% | -233 | Heavy favorite |
| 75% | -300 | Very heavy favorite |
| 80% | -400 | Dominant favorite |
| 40% | +150 | Moderate underdog |
| 33% | +200 | 2-to-1 underdog |
| 25% | +300 | 3-to-1 underdog |

### 6.3 Reading American Odds

- **Negative (-163)**: Favorite. Bet $163 to win $100
- **Positive (+150)**: Underdog. Bet $100 to win $150

---

## 7. PowerGrid Tournament Probabilities

### 7.1 NEPSAC Playoff Structure

1. **Elite 8**: Top 8 teams OVERALL (Large + Small combined)
   - These 8 teams compete for Elite 8 Championship
   - Teams in Elite 8 do NOT play in division tournaments

2. **Large School Tournament**: Large schools who MISSED Elite 8
   - Top 8 Large schools not in Elite 8 get bids

3. **Small School Tournament**: Small schools who MISSED Elite 8
   - Top 8 Small schools not in Elite 8 get bids

### 7.2 Six Probabilities Per Team

Each team has 6 probability fields (with American odds):

| Field | Odds Field | Description |
|-------|------------|-------------|
| elite8Bid | elite8BidOdds | % chance of being top 8 overall |
| elite8Champ | elite8ChampOdds | % chance of winning Elite 8 |
| largeSchoolBid | largeSchoolBidOdds | % chance of making Large tournament |
| largeSchoolChamp | largeSchoolChampOdds | % chance of winning Large School |
| smallSchoolBid | smallSchoolBidOdds | % chance of making Small tournament |
| smallSchoolChamp | smallSchoolChampOdds | % chance of winning Small School |

**Note:** Probabilities are MUTUALLY EXCLUSIVE. High elite8Bid = Low division bid.

### 7.3 Elite 8 Bid Probability Formula

```javascript
function calculateElite8BidProb(powerRank, totalTeams) {
  if (powerRank <= 4) {
    // Top 4: Very likely (99%, 97%, 95%, 93%)
    return Math.round((0.99 - (powerRank - 1) * 0.02) * 1000) / 10;
  } else if (powerRank <= 8) {
    // 5-8: Good chance (90%, 80%, 70%, 60%)
    return Math.round((0.90 - (powerRank - 5) * 0.10) * 1000) / 10;
  } else if (powerRank <= 12) {
    // 9-12: Bubble (45%, 35%, 25%, 15%)
    return Math.round((0.45 - (powerRank - 9) * 0.10) * 1000) / 10;
  } else if (powerRank <= 16) {
    // 13-16: Long shots (10%, 8%, 6%, 4%)
    return Math.round((0.10 - (powerRank - 13) * 0.02) * 1000) / 10;
  } else {
    // 17+: Very unlikely
    return Math.max(0.5, Math.round((0.03 - (powerRank - 17) * 0.005) * 1000) / 10);
  }
}
```

### 7.4 Division Bid Probability

```javascript
// Formula: P(division) = P(miss Elite 8) × P(make division | missed Elite 8)
function calculateDivisionBidProb(team, sameClassTeams, elite8BidProb) {
  const missElite8Prob = (100 - elite8BidProb) / 100;

  // If very likely to make Elite 8, very unlikely to be in division
  if (missElite8Prob < 0.05) {
    return Math.round(missElite8Prob * 99 * 10) / 10;
  }

  // Calculate conditional probability based on class rank
  // ... (see powergrid.js for full implementation)
}
```

---

## 8. Past Performance Tracking

### 8.1 Accuracy Calculation

```javascript
const correct = games.filter(g => g.prediction_correct === true).length;
const incorrect = games.filter(g => g.prediction_correct === false).length;
const ties = games.filter(g => g.is_tie === true).length;
const total = correct + incorrect;  // Ties excluded from accuracy

const accuracy = total > 0 ? Math.round(1000 * correct / total) / 10 : null;
```

### 8.2 Prediction Result Classification

| Result | Condition |
|--------|-----------|
| Correct | predicted_winner_id === actual_winner_id |
| Incorrect | predicted_winner_id !== actual_winner_id AND not a tie |
| Tie | Final score is equal (ties don't count toward accuracy) |

### 8.3 Stored Metrics

- **Per Game:** prediction_correct, actual_winner_id, is_tie
- **Per Date:** correct, incorrect, ties, accuracy
- **Season:** total_predictions, correct, incorrect, ties, overall_accuracy

---

## 9. Admin Portal

### 9.1 Admin Endpoints (admin.js)

#### `GET /adminGetHealth`
System health check.

**Response:**
```json
{
  "status": "healthy",
  "totalPlayers": 86000,
  "rankedPlayers": 45000,
  "lastAlgorithmRun": "2026-01-28T10:00:00Z",
  "dataVersion": "2026.01.28"
}
```

#### `GET /adminGetFactors`
Returns status of all 35 ranking factors.

**For each factor:**
- Table name, factor ID, description
- Row count, last calculated timestamp
- Data status (fresh/stale/critical)
- Coverage percentage
- Active/inactive status

#### `GET /adminGetAlerts`
Detects system issues.

**Alert types:**
- Stale factor tables (>24 hours old)
- Players with zero performance but positive views
- Missing data or broken pipelines

#### `GET /adminGetPlayers`
Full player search with all 35 factors.

| Parameter | Type | Description |
|-----------|------|-------------|
| birthYear | number | Filter by birth year |
| position | string | F, D, or G |
| limit | number | Default: 50 |
| offset | number | Pagination |
| q | string | Name search |

### 9.2 Story Generation Data

The admin portal provides data for AI story generation:

**Game Data Available:**
- Matchup details with predictions
- Top performers per game
- Upset detection (when prediction_correct = false)
- Head-to-head comparisons

**Story Types:**
- Game recaps
- Weekly summaries
- Player spotlights
- Upset analysis

---

## 10. Frontend Components

### 10.1 TypeScript API Client

**File:** `frontend-integration/BMI_UI/client/src/lib/nepsac-api.ts`

Key interfaces:
```typescript
interface NepsacGame {
  gameId: string;
  prediction: {
    winnerId: string | null;
    confidence: number | null;
    confidenceOdds: string | null;  // "-163" or "+150"
  };
}

interface PowerGridTeam {
  elite8Bid: number;
  elite8BidOdds: string;
  largeSchoolBid: number;
  largeSchoolBidOdds: string;
  // ... etc
}
```

### 10.2 React Components

| Component | Purpose |
|-----------|---------|
| NepsacGameDay.tsx | Main GameDay page with game selector |
| NepsacMatchup.tsx | Full matchup view with prediction bar |
| NepsacPastPerformance.tsx | Historical results with accuracy |
| NepsacPowerRankings.tsx | Top 20 power rankings sidebar |
| NepsacTeamCard.tsx | Team card with logo and stats |
| NepsacPlayerCard.tsx | Trading card style player display |
| GameComments.tsx | User comments on games |

### 10.3 Styling

**Design System:**
- Dark theme with glassmorphism
- Gradient accents (purple, pink, cyan)
- Orbitron font for headers
- EA Sports-inspired OVR badges

---

## 11. Data Sync Process

### 11.1 Sync Endpoints

| Endpoint | Description |
|----------|-------------|
| GET /syncNepsacData | Full sync (teams + games + stats) |
| GET /syncNepsacTeams | Teams only |
| GET /syncNepsacGames | Games only (includes stats update) |

### 11.2 Sync Logic

```javascript
// 1. Fetch from BigQuery
const rows = await executeQuery(query);

// 2. Transform for Supabase schema
const games = rows.map(row => ({
  game_id: row.game_id,
  // ... transform fields
  prediction_correct: calculatePredictionCorrect(row),
  is_tie: row.away_score === row.home_score,
}));

// 3. Batch upsert to Supabase
for (let i = 0; i < games.length; i += BATCH_SIZE) {
  await supabase.from('nepsac_games')
    .upsert(batch, { onConflict: 'game_id' });
}
```

### 11.3 Sync Direction

**UNIDIRECTIONAL: BigQuery → Supabase**

- BigQuery is the Single Source of Truth
- Supabase is a read-only replica for frontend
- Never write to BigQuery from frontend

---

## 12. Team Classifications

### 12.1 Official Source

**Source Document:** NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf

### 12.2 Classification Rule

- **Large School:** Enrollment >= 225 students (28 schools)
- **Small School:** Enrollment < 225 students (29 schools)
- **Total:** 57 NEPSAC member schools

### 12.3 Complete Team List

**Large Schools (28):**
| Team | Enrollment |
|------|------------|
| Phillips Academy Andover | 585 |
| Phillips Exeter Academy | 545 |
| Brunswick School | 440 |
| Choate Rosemary Hall | 422 |
| Avon Old Farms | 401 |
| Milton Academy | 357 |
| Deerfield Academy | 355 |
| Loomis Chaffee | 351 |
| Belmont Hill School | 350 |
| Salisbury School | 306 |
| Taft School | 305 |
| Hotchkiss School | 305 |
| Northfield Mount Hermon | 304 |
| St. Sebastian's School | 285 |
| Buckingham Browne & Nichols | 280 |
| Tabor Academy | 279 |
| Thayer Academy | 276 |
| Kent School | 265 |
| St. Paul's School | 264 |
| Austin Prep | 257 |
| Dexter Southfield | 257 |
| Noble and Greenough School | 253 |
| Williston Northampton | 245 |
| Trinity-Pawling School | 240 |
| Worcester Academy | 235 |
| Cushing Academy | 226 |
| Westminster School | 225 |
| Lawrence Academy | 225 |

**Small Schools (29):**
| Team | Enrollment |
|------|------------|
| Governor's Academy | 222 |
| Middlesex School | 221 |
| Roxbury Latin School | 218 |
| Berkshire School | 217 |
| Proctor Academy | 212 |
| Rivers School | 205 |
| Kimball Union Academy | 199 |
| St. Mark's School | 193 |
| Albany Academy | 192 |
| St. George's School | 192 |
| Brooks School | 191 |
| Groton School | 189 |
| New Hampton School | 187 |
| Brewster Academy | 186 |
| Pomfret School | 183 |
| Canterbury School | 180 |
| Wilbraham & Monson Academy | 178 |
| Pingree School | 177 |
| Portsmouth Abbey School | 177 |
| Winchendon School | 170 |
| Frederick Gunn School | 170 |
| Hoosac School | 169 |
| Millbrook School | 165 |
| Holderness School | 164 |
| Berwick Academy | 143 |
| Vermont Academy | 137 |
| Hebron Academy | 117 |
| Kents Hill School | 110 |
| Tilton School | 99 |

---

## 13. Deployment

### 13.1 Cloud Functions Deployment

```bash
cd api-backend/functions

# Deploy individual function
gcloud functions deploy getNepsacSchedule \
  --gen2 \
  --runtime=nodejs20 \
  --region=us-central1 \
  --source=. \
  --entry-point=getNepsacSchedule \
  --trigger-http \
  --allow-unauthenticated \
  --memory=256MB \
  --timeout=60s

# Deploy PowerGrid (needs more memory)
gcloud functions deploy getNepsacPowerGrid \
  --gen2 \
  --runtime=nodejs20 \
  --region=us-central1 \
  --source=. \
  --entry-point=getNepsacPowerGrid \
  --trigger-http \
  --allow-unauthenticated \
  --memory=512MB \
  --timeout=60s
```

### 13.2 Function List

| Function | Memory | Timeout |
|----------|--------|---------|
| getNepsacSchedule | 256MB | 60s |
| getNepsacMatchup | 256MB | 60s |
| getNepsacPastResults | 256MB | 60s |
| getNepsacPowerGrid | 512MB | 60s |
| getNepsacTeams | 256MB | 60s |
| getNepsacRoster | 256MB | 60s |
| getNepsacStandings | 256MB | 60s |
| getNepsacPowerRankings | 256MB | 60s |
| getNepsacGameDates | 256MB | 60s |
| getNepsacTopPerformers | 256MB | 60s |
| syncNepsacData | 256MB | 120s |
| syncNepsacTeams | 256MB | 60s |
| syncNepsacGames | 256MB | 120s |

### 13.3 Environment Variables

Required in Cloud Functions:
- `BIGQUERY_PROJECT`: prodigy-ranking
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY`: Supabase service key (for sync functions)

---

## Appendix A: Quick Reference

### API Base URL
```
https://us-central1-prodigy-ranking.cloudfunctions.net
```

### Common Endpoints
```
/getNepsacSchedule?date=2026-01-22
/getNepsacMatchup?gameId={uuid}
/getNepsacPastResults?season=2025-26
/getNepsacPowerGrid
/getNepsacPowerRankings?limit=20
```

### Key Formulas

**OVR Rating:**
```
OVR = 70 + (normalized_points × 29)
Range: 70-99
```

**American Odds:**
```
Favorite (>50%): -(prob / (100-prob)) × 100
Underdog (<50%): ((100-prob) / prob) × 100
```

**Accuracy:**
```
Accuracy = Correct / (Correct + Incorrect) × 100
Note: Ties excluded
```

---

*End of NEPSAC System Manual*

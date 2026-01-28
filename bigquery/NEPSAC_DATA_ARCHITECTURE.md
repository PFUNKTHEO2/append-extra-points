# NEPSAC Data Architecture - Single Source of Truth

## Overview

All NEPSAC data originates from **BigQuery** (project: `prodigy-ranking`).
Supabase is a downstream consumer that syncs from BigQuery.

```
┌─────────────────────────────────────────────────────────────┐
│                    DATA FLOW                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   Official PDF ─────┐                                       │
│   (Classifications) │                                       │
│                     ▼                                       │
│              ┌──────────────┐                               │
│              │   BigQuery   │  ◄── Source of Truth          │
│              │ (algorithm_  │                               │
│              │    core)     │                               │
│              └──────┬───────┘                               │
│                     │                                       │
│         ┌──────────┴──────────┐                             │
│         ▼                     ▼                             │
│  ┌──────────────┐     ┌──────────────┐                      │
│  │ Cloud Funcs  │     │  Supabase    │                      │
│  │   (APIs)     │     │  (Sync Copy) │                      │
│  └──────┬───────┘     └──────┬───────┘                      │
│         │                    │                              │
│         └────────┬───────────┘                              │
│                  ▼                                          │
│           ┌──────────────┐                                  │
│           │   Frontend   │                                  │
│           │  (/gameday)  │                                  │
│           └──────────────┘                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## BigQuery Tables (Source of Truth)

### `algorithm_core.nepsac_teams`
Official list of 57 NEPSAC member schools with classifications.

| Column | Type | Description |
|--------|------|-------------|
| team_id | STRING | Unique ID (e.g., "avon-old-farms") |
| team_name | STRING | Full name |
| short_name | STRING | Display name |
| **classification** | STRING | **'Large' or 'Small'** (official) |
| **enrollment** | INT64 | School enrollment number |
| logo_url | STRING | Team logo URL |
| venue | STRING | Home arena |
| city | STRING | City |
| state | STRING | State |

### `algorithm_core.nepsac_team_rankings`
Power rankings calculated by our algorithm.

| Column | Type | Description |
|--------|------|-------------|
| team_id | STRING | Links to nepsac_teams |
| season | STRING | "2025-26" |
| **rank** | INT64 | **Official power rank (1-57)** |
| team_ovr | INT64 | OVR rating (0-99) |
| avg_prodigy_points | FLOAT64 | Avg player points |
| total_prodigy_points | FLOAT64 | Total roster points |
| top_player_name | STRING | Best player |

### `algorithm_core.nepsac_standings`
Win-loss records and performance stats.

| Column | Type | Description |
|--------|------|-------------|
| team_id | STRING | Links to nepsac_teams |
| season | STRING | "2025-26" |
| wins | INT64 | Games won |
| losses | INT64 | Games lost |
| ties | INT64 | Ties |
| win_pct | FLOAT64 | Win percentage |
| goals_for | INT64 | Total goals scored |
| goals_against | INT64 | Total goals allowed |
| streak | STRING | Current streak (e.g., "W3") |

### `algorithm_core.nepsac_schedule`
Game schedule with predictions and results.

| Column | Type | Description |
|--------|------|-------------|
| game_id | STRING | Unique game ID |
| season | STRING | "2025-26" |
| game_date | DATE | Game date |
| away_team_id | STRING | Away team |
| home_team_id | STRING | Home team |
| status | STRING | scheduled/final/etc. |
| away_score | INT64 | Away team score |
| home_score | INT64 | Home team score |
| predicted_winner_id | STRING | Our prediction |
| prediction_confidence | INT64 | 50-99% |

---

## Classification Source

**Official Document**: `NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf`

### Large Schools (28 teams, enrollment ≥ 225)
| Team | Enrollment |
|------|------------|
| Andover | 585 |
| Exeter | 545 |
| Brunswick | 440 |
| Choate | 422 |
| Avon | 401 |
| Milton | 357 |
| Deerfield | 355 |
| Loomis | 351 |
| Belmont Hill | 350 |
| Salisbury | 306 |
| Taft | 305 |
| Hotchkiss | 305 |
| NMH | 304 |
| St. Sebastian's | 285 |
| BB&N | 280 |
| Tabor | 279 |
| Thayer | 276 |
| Kent | 265 |
| St. Paul's | 264 |
| Austin Prep | 257 |
| Dexter | 257 |
| Nobles | 253 |
| Williston | 245 |
| Trinity Pawling | 240 |
| Worcester | 235 |
| Cushing | 226 |
| Westminster | 225 |
| Lawrence | 225 |

### Small Schools (29 teams, enrollment < 225)
| Team | Enrollment |
|------|------------|
| Governor's | 222 |
| Middlesex | 221 |
| Roxbury Latin | 218 |
| Berkshire | 217 |
| Proctor | 212 |
| Rivers | 205 |
| Kimball Union | 199 |
| St. Mark's | 193 |
| Albany Academy | 192 |
| St. George's | 192 |
| Brooks | 191 |
| Groton | 189 |
| New Hampton | 187 |
| Brewster | 186 |
| Pomfret | 183 |
| Canterbury | 180 |
| WMA | 178 |
| Pingree | 177 |
| Portsmouth Abbey | 177 |
| Winchendon | 170 |
| Frederick Gunn | 170 |
| Hoosac | 169 |
| Millbrook | 165 |
| Holderness | 164 |
| Berwick | 143 |
| Vermont | 137 |
| Hebron | 117 |
| Kents Hill | 110 |
| Tilton | 99 |

---

## API Endpoints

All APIs pull from BigQuery:

### Power Rankings
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26
```

### PowerGrid (Tournament Probabilities)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26
```

### Sync to Supabase (Admin)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/syncNepsacData?season=2025-26
```

---

## Supabase Tables (Synced Copy)

These tables are populated by the sync function from BigQuery:

- `nepsac_teams` - Team info (synced from BigQuery)
- `nepsac_games` - Schedule + results (synced from BigQuery)
- `nepsac_daily_summary` - Computed from nepsac_games
- `nepsac_overall_stats` - Computed from nepsac_games

---

## Deployment Commands

### Update BigQuery classifications:
```bash
bq query --use_legacy_sql=false < update_nepsac_classifications.sql
```

### Deploy PowerGrid API:
```bash
cd api-backend/functions
gcloud functions deploy getNepsacPowerGrid \
  --gen2 \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated
```

### Deploy Sync Functions:
```bash
gcloud functions deploy syncNepsacData \
  --gen2 \
  --runtime nodejs20 \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars SUPABASE_URL=...,SUPABASE_SERVICE_ROLE_KEY=...
```

---

## Important Notes

1. **Never edit Supabase NEPSAC data directly** - it will be overwritten by sync
2. **All changes should be made in BigQuery first**
3. **Run sync after BigQuery updates** to push to Supabase
4. **Classification comes from official NEPSAC PDF** - not calculated

---

*Last updated: 2026-01-27*

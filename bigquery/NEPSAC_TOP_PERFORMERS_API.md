# NEPSAC Top Performers API

## Overview

The Top Performers API provides game-day scoring data for NEPSAC players, enabling:
- GameDay stories with actual stat leaders
- Social media highlights with real performance data
- Post-game recaps showing who dominated

## Endpoints

### GET /getNepsacTopPerformers

Returns top performers for a specific game day based on actual game scoring.

**URL:** `https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacTopPerformers`

**Query Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| date | string | Yes | - | Game date (YYYY-MM-DD) |
| limit | number | No | 6 | Max performers to return (max: 20) |

**Example Request:**
```
GET /getNepsacTopPerformers?date=2026-01-24&limit=6
```

**Response (with data):**
```json
{
  "date": "2026-01-24",
  "dataAvailable": true,
  "performerCount": 6,
  "topPerformers": [
    {
      "playerId": 123456,
      "name": "Seamus McMakin",
      "position": "F",
      "imageUrl": "https://...",
      "ovr": 94,
      "prodigyPoints": 2850.5,
      "teamId": "canterbury-school",
      "teamName": "Canterbury School",
      "teamShortName": "Canterbury",
      "teamLogoUrl": "https://...",
      "gameId": "game_0045",
      "opponent": "Loomis Chaffee",
      "starRank": 1,
      "gameDayStats": {
        "goals": 2,
        "assists": 2,
        "points": 4,
        "saves": null,
        "shutout": false,
        "win": null
      }
    },
    {
      "playerId": 789012,
      "name": "John Smith",
      "position": "G",
      "imageUrl": "https://...",
      "ovr": 88,
      "prodigyPoints": 1920.3,
      "teamId": "salisbury-school",
      "teamName": "Salisbury School",
      "teamShortName": "Salisbury",
      "teamLogoUrl": "https://...",
      "gameId": "game_0046",
      "opponent": "Avon Old Farms",
      "starRank": null,
      "gameDayStats": {
        "goals": null,
        "assists": null,
        "points": null,
        "saves": 38,
        "shutout": true,
        "win": true
      }
    }
  ]
}
```

**Response (no data available):**
```json
{
  "date": "2026-01-24",
  "dataAvailable": false,
  "message": "No performer data available for this date. Box scores may not have been entered yet.",
  "topPerformers": []
}
```

### POST /addNepsacGamePerformers

Add or update game performers for a specific game (admin endpoint).

**URL:** `https://us-central1-prodigy-ranking.cloudfunctions.net/addNepsacGamePerformers`

**Request Body:**
```json
{
  "gameId": "game_0045",
  "gameDate": "2026-01-24",
  "source": "manual",
  "performers": [
    {
      "rosterName": "Seamus McMakin",
      "teamId": "canterbury-school",
      "position": "F",
      "goals": 2,
      "assists": 2,
      "playerId": 123456,
      "starRank": 1
    },
    {
      "rosterName": "John Smith",
      "teamId": "salisbury-school",
      "position": "G",
      "saves": 38,
      "isShutout": true,
      "isWin": true
    }
  ]
}
```

**Performer Object Fields:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rosterName | string | Yes | Player name as shown in box score |
| teamId | string | Yes | Team ID (e.g., "salisbury-school") |
| position | string | No | "F", "D", or "G" |
| playerId | number | No | Link to player database ID |
| goals | number | No | Goals scored (skaters) |
| assists | number | No | Assists (skaters) |
| plusMinus | number | No | +/- rating |
| pim | number | No | Penalty minutes |
| shots | number | No | Shots on goal |
| saves | number | No | Saves (goalies) |
| goalsAgainst | number | No | Goals allowed (goalies) |
| shotsFaced | number | No | Total shots faced (goalies) |
| savePct | number | No | Save percentage (0.000-1.000) |
| isShutout | boolean | No | Shutout game (goalies) |
| isWin | boolean | No | Win credit (goalies) |
| isLoss | boolean | No | Loss credit (goalies) |
| isOtl | boolean | No | OT loss credit (goalies) |
| isStarOfGame | boolean | No | Named star of game |
| starRank | number | No | 1, 2, or 3 for stars |
| notes | string | No | Additional notes |

**Response:**
```json
{
  "success": true,
  "gameId": "game_0045",
  "gameDate": "2026-01-24",
  "performersAdded": 2,
  "message": "Successfully added 2 performers for game game_0045"
}
```

## Scoring Logic

### Skaters
Ranked by total points (goals + assists), with goals as tiebreaker:
```
score = points * 100 + goals
```

### Goalies
Shutouts get highest priority, then sorted by saves:
```
score = (shutout ? 1000 : 0) + saves
```

## Data Sources

Performer data can come from multiple sources:

1. **Manual Entry** (`source: "manual"`)
   - Admin enters stats via POST endpoint
   - Best for immediate post-game entry

2. **Elite Prospects** (`source: "elite_prospects"`)
   - Scraped from EP box scores when available
   - Usually available 24-48 hours after game

3. **Neutral Zone** (`source: "neutral_zone"`)
   - Scraped from prepschoolhockey.neutralzone.net
   - Most comprehensive NEPSAC source

4. **Team Websites** (`source: "team_website"`)
   - Individual school athletic sites
   - Variable availability and format

## Database Schema

### BigQuery Table
```sql
CREATE TABLE `prodigy-ranking.algorithm_core.nepsac_game_performers` (
  performer_id STRING NOT NULL,
  game_id STRING NOT NULL,
  game_date DATE NOT NULL,
  player_id INT64,
  roster_name STRING NOT NULL,
  team_id STRING NOT NULL,
  position STRING,
  goals INT64 DEFAULT 0,
  assists INT64 DEFAULT 0,
  points INT64 DEFAULT 0,
  plus_minus INT64,
  pim INT64,
  shots INT64,
  saves INT64,
  goals_against INT64,
  shots_faced INT64,
  save_pct FLOAT64,
  is_shutout BOOL DEFAULT FALSE,
  is_win BOOL,
  is_loss BOOL,
  is_otl BOOL,
  is_star_of_game BOOL DEFAULT FALSE,
  star_rank INT64,
  source STRING,
  notes STRING,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
```

## Frontend Integration

### Example Usage (React/TypeScript)
```typescript
interface TopPerformer {
  playerId: number | null;
  name: string;
  position: string;
  imageUrl: string | null;
  ovr: number;
  teamId: string;
  teamName: string;
  teamShortName: string;
  opponent: string | null;
  starRank: number | null;
  gameDayStats: {
    goals: number | null;
    assists: number | null;
    points: number | null;
    saves: number | null;
    shutout: boolean;
    win: boolean | null;
  };
}

async function fetchTopPerformers(date: string): Promise<TopPerformer[]> {
  const response = await fetch(
    `https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacTopPerformers?date=${date}&limit=6`
  );
  const data = await response.json();

  if (!data.dataAvailable) {
    return []; // Handle gracefully - show "Data coming soon" message
  }

  return data.topPerformers;
}
```

### Fallback UI
When `dataAvailable: false`, the frontend should display a fallback message:

```tsx
{!dataAvailable ? (
  <div className="text-center p-4 bg-gray-800 rounded-lg">
    <p className="text-gray-400">
      Box scores not yet available for {date}.
    </p>
    <p className="text-sm text-gray-500 mt-2">
      Stats typically appear within 24 hours of game completion.
    </p>
  </div>
) : (
  <TopPerformersCarousel performers={topPerformers} />
)}
```

## Deployment

1. Deploy the updated Cloud Functions:
```bash
cd api-backend/functions
gcloud functions deploy getNepsacTopPerformers --runtime=nodejs18 --trigger-http --allow-unauthenticated
gcloud functions deploy addNepsacGamePerformers --runtime=nodejs18 --trigger-http --allow-unauthenticated
```

2. Create the BigQuery table:
```bash
bq query --use_legacy_sql=false < ../database/nepsac-schema.sql
```

3. Create the Supabase table (if using Supabase as secondary):
```bash
psql $SUPABASE_DB_URL < ../database/nepsac-predictions-supabase.sql
```

## Future Enhancements

1. **Automated Scraping** - Build a scraper for Neutral Zone box scores
2. **EP Integration** - Auto-pull from Elite Prospects API when available
3. **Admin UI** - Web form for easy manual entry
4. **Player Matching** - Auto-match roster names to player IDs
5. **Historical Stats** - Track player performance across all games

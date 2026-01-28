# 🚀 ProdigyRanking API Endpoints

**Last Updated:** January 28, 2026
**Status:** ✅ All 16+ functions deployed and live
**Region:** us-central1

---

## 📊 Algorithm API (Rankings)

### 1. Get Player by ID
**Endpoint:** `https://getplayer-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?player_id=879926`
**Example:**
```
https://getplayer-u4ztvt4wva-uc.a.run.app?player_id=879926
```

**Response:**
```json
{
  "player_id": 879926,
  "player_name": "Max Penkin",
  "position": "F",
  "birth_year": 2009,
  "total_points": 4505.73,
  "f01_views": 2000,
  ...
}
```

---

### 2. Search Players
**Endpoint:** `https://searchplayers-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?q=Max&limit=10`
**Example:**
```
https://searchplayers-u4ztvt4wva-uc.a.run.app?q=Max&limit=5
```

**Response:**
```json
{
  "query": "Max",
  "count": 5,
  "players": [...]
}
```

---

### 3. Get Homepage Stats
**Endpoint:** `https://getstats-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Example:**
```
https://getstats-u4ztvt4wva-uc.a.run.app
```

**Response:**
```json
{
  "totalPlayers": 161886,
  "totalLeagues": 875,
  "totalCountries": 87,
  "lastUpdated": "2025-01-15..."
}
```

---

### 4. Get Rankings
**Endpoint:** `https://getrankings-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?birthYear=2009&scope=worldwide&position=F&limit=250`
**Example:**
```
https://getrankings-u4ztvt4wva-uc.a.run.app?birthYear=2009&scope=worldwide&position=F&limit=10
```

**Scope Options:**
- `worldwide` - All players
- `north_american` - Canada + USA only
- `{country}` - Specific country (e.g., `canada`, `sweden`)

**Response:**
```json
{
  "birth_year": 2009,
  "position": "F",
  "scope": "worldwide",
  "count": 10,
  "players": [
    {
      "rank": 1,
      "player_id": 879926,
      "player_name": "Max Penkin",
      "total_points": 4505.73,
      ...
    }
  ]
}
```

---

### 5. Get Rankings Metadata
**Endpoint:** `https://getrankingsmetadata-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Example:**
```
https://getrankingsmetadata-u4ztvt4wva-uc.a.run.app
```

**Response:**
```json
{
  "exported_at": "2025-11-16...",
  "birth_years": [2011, 2010, 2009, 2008, 2007],
  "positions": ["D", "F", "G"],
  "countries": ["Canada", "USA", "Sweden", ...]
}
```

---

## 🛒 Marketplace API (Trading Cards)

### 6. Register Card
**Endpoint:** `https://registercard-u4ztvt4wva-uc.a.run.app`
**Method:** POST
**Headers:** `X-User-ID: user@example.com`
**Body:**
```json
{
  "card_id": "PR2025-879926-001-00042",
  "serial_number": 42,
  "verification_code": "VERIFY-42-XYZ",
  "condition_grade": "MINT"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Card registered successfully!",
  "card_id": "PR2025-879926-001-00042",
  "series_id": "PR2025-879926-001",
  "registered_at": "2025-11-17..."
}
```

---

### 7. Get Card Market Data
**Endpoint:** `https://getcardmarketdata-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?series_id=PR2025-879926-001`
**Example:**
```
https://getcardmarketdata-u4ztvt4wva-uc.a.run.app?series_id=PR2025-879926-001
```

**Response:**
```json
{
  "series_id": "PR2025-879926-001",
  "player_name": "Max Penkin",
  "card_type": "ROOKIE",
  "rarity": "SUPER_RARE",
  "total_minted": 100,
  "total_registered": 1,
  "floor_price": 149.99,
  "active_listings": 1,
  ...
}
```

---

### 8. Get My Card Value (ROI)
**Endpoint:** `https://getmycardvalue-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Headers:** `X-User-ID: user@example.com`
**Query Params:** `?card_id=PR2025-879926-001-00042`
**Example:**
```
https://getmycardvalue-u4ztvt4wva-uc.a.run.app?card_id=PR2025-879926-001-00042
```

**Response:**
```json
{
  "card_id": "PR2025-879926-001-00042",
  "player_name": "Max Penkin",
  "serial_number": 42,
  "purchase_price": 50.00,
  "current_market_value": 149.99,
  "absolute_gain": 99.99,
  "roi_percentage": 199.98,
  "days_held": 30
}
```

---

### 9. Get My Portfolio
**Endpoint:** `https://getmyportfolio-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Headers:** `X-User-ID: user@example.com`
**Example:**
```
https://getmyportfolio-u4ztvt4wva-uc.a.run.app
```

**Response:**
```json
{
  "user_id": "user@example.com",
  "total_cards": 5,
  "total_invested": 500.00,
  "current_value": 750.00,
  "total_gain": 250.00,
  "portfolio_roi": 50.00,
  "cards": [...]
}
```

---

### 10. Get Market Leaderboard
**Endpoint:** `https://getmarketleaderboard-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?limit=10`
**Example:**
```
https://getmarketleaderboard-u4ztvt4wva-uc.a.run.app?limit=10
```

**Response:**
```json
{
  "leaderboard": [
    {
      "series_id": "PR2025-879926-001",
      "player_name": "Max Penkin",
      "average_sale_price": 149.99,
      "floor_price": 149.99,
      ...
    }
  ]
}
```

---

### 11. Get Trending Cards
**Endpoint:** `https://gettrendingcards-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?limit=10`
**Example:**
```
https://gettrendingcards-u4ztvt4wva-uc.a.run.app?limit=10
```

**Response:**
```json
{
  "trending": [
    {
      "series_id": "PR2025-879926-001",
      "player_name": "Max Penkin",
      "price_change_30d": 25.5,
      ...
    }
  ]
}
```

---

### 12. Search Marketplace
**Endpoint:** `https://searchmarketplace-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:**
- `player_name=Max`
- `card_type=ROOKIE`
- `rarity=SUPER_RARE`
- `min_price=50`
- `max_price=200`
- `condition=MINT`
- `sort_by=price_asc|price_desc|newest|ending_soon`
- `limit=50`

**Example:**
```
https://searchmarketplace-u4ztvt4wva-uc.a.run.app?card_type=ROOKIE&sort_by=price_asc&limit=20
```

**Response:**
```json
{
  "filters": {...},
  "count": 1,
  "listings": [
    {
      "listing_id": "LIST-001",
      "card_id": "PR2025-879926-001-00001",
      "player_name": "Max Penkin",
      "serial_number": 1,
      "asking_price": 149.99,
      "condition_grade": "MINT",
      ...
    }
  ]
}
```

---

## 🏒 NEPSAC GameDay & PowerGrid API

### 13. Get NEPSAC PowerGrid
**Endpoint:** `https://getnepsacpowergrid-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?season=2025-26`
**Version:** v5 (with American Odds)

**Example:**
```
https://getnepsacpowergrid-u4ztvt4wva-uc.a.run.app?season=2025-26
```

**Response includes 6 probabilities with American odds for each team:**

| Field | Description | Odds Field |
|-------|-------------|------------|
| `elite8Bid` | % chance to make Elite 8 (top 8 overall) | `elite8BidOdds` |
| `elite8Champ` | % chance to win Elite 8 Championship | `elite8ChampOdds` |
| `largeSchoolBid` | % chance to make Large School tournament | `largeSchoolBidOdds` |
| `largeSchoolChamp` | % chance to win Large School Championship | `largeSchoolChampOdds` |
| `smallSchoolBid` | % chance to make Small School tournament | `smallSchoolBidOdds` |
| `smallSchoolChamp` | % chance to win Small School Championship | `smallSchoolChampOdds` |

**American Odds Format:**
- **Negative** (`-300`): Favorite. Bet $300 to win $100.
- **Positive** (`+300`): Underdog. Bet $100 to win $300.
- Odds are capped at `-10000` (99.9%+) and `+10000` (<0.1%)

**Sample Response:**
```json
{
  "season": "2025-26",
  "generated": "2026-01-28",
  "_metadata": {
    "version": "v5",
    "oddsFormat": {
      "description": "American odds format included for all probabilities"
    }
  },
  "teams": [
    {
      "powerRank": 1,
      "teamId": "dexter",
      "name": "Dexter Southfield",
      "classification": "Large",
      "elite8Bid": 99,
      "elite8BidOdds": "-9900",
      "elite8Champ": 24.8,
      "elite8ChampOdds": "-33",
      "largeSchoolBid": 1,
      "largeSchoolBidOdds": "+9900",
      "largeSchoolChamp": 0.3,
      "largeSchoolChampOdds": "+10000"
    }
  ],
  "currentElite8": [...],
  "largeSchoolContenders": [...],
  "smallSchoolContenders": [...],
  "bubbleTeams": [...],
  "summary": {
    "totalTeams": 57,
    "largeSchools": 28,
    "smallSchools": 29
  }
}
```

**Data Sources (BigQuery - Single Source of Truth):**
- `algorithm_core.nepsac_teams` - Team info, classification
- `algorithm_core.nepsac_team_rankings` - Power rankings, OVR ratings
- `algorithm_core.nepsac_standings` - W-L-T records, goals

---

### 14. Get NEPSAC Schedule
**Endpoint:** `https://getnepsacschedule-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?date=2026-01-28` or `?week=current`

**Example:**
```
https://getnepsacschedule-u4ztvt4wva-uc.a.run.app?date=2026-01-28
```

**Response includes predictions with status:**
```json
{
  "games": [
    {
      "gameId": "game-123",
      "gameDate": "2026-01-28",
      "awayTeam": {...},
      "homeTeam": {...},
      "prediction": {
        "winnerId": "salisbury",
        "confidence": 65,
        "status": "available"
      }
    },
    {
      "gameId": "game-456",
      "prediction": {
        "winnerId": null,
        "confidence": null,
        "status": "Missing Data",
        "reason": "Both teams lack ranking data"
      }
    }
  ]
}
```

---

### 15. Get NEPSAC Team
**Endpoint:** `https://getnepsacteam-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Query Params:** `?team_id=salisbury`

---

### 16. Sync NEPSAC Data
**Endpoint:** `https://syncnepsacdata-u4ztvt4wva-uc.a.run.app`
**Method:** GET
**Description:** Syncs all NEPSAC data from BigQuery to Supabase

---

## 🔧 For Loveable Frontend

### API Configuration File

Create `src/config/api.ts`:

```typescript
export const API_CONFIG = {
  // Algorithm API
  getPlayer: 'https://getplayer-u4ztvt4wva-uc.a.run.app',
  searchPlayers: 'https://searchplayers-u4ztvt4wva-uc.a.run.app',
  getStats: 'https://getstats-u4ztvt4wva-uc.a.run.app',
  getRankings: 'https://getrankings-u4ztvt4wva-uc.a.run.app',
  getRankingsMetadata: 'https://getrankingsmetadata-u4ztvt4wva-uc.a.run.app',

  // Marketplace API
  registerCard: 'https://registercard-u4ztvt4wva-uc.a.run.app',
  getCardMarketData: 'https://getcardmarketdata-u4ztvt4wva-uc.a.run.app',
  getMyCardValue: 'https://getmycardvalue-u4ztvt4wva-uc.a.run.app',
  getMyPortfolio: 'https://getmyportfolio-u4ztvt4wva-uc.a.run.app',
  getMarketLeaderboard: 'https://getmarketleaderboard-u4ztvt4wva-uc.a.run.app',
  getTrendingCards: 'https://gettrendingcards-u4ztvt4wva-uc.a.run.app',
  searchMarketplace: 'https://searchmarketplace-u4ztvt4wva-uc.a.run.app',

  // NEPSAC GameDay & PowerGrid API
  getNepsacPowerGrid: 'https://getnepsacpowergrid-u4ztvt4wva-uc.a.run.app',
  getNepsacSchedule: 'https://getnepsacschedule-u4ztvt4wva-uc.a.run.app',
  getNepsacTeam: 'https://getnepsacteam-u4ztvt4wva-uc.a.run.app',
  syncNepsacData: 'https://syncnepsacdata-u4ztvt4wva-uc.a.run.app',
};
```

### React Query Hook Example

```typescript
// src/hooks/useRankings.ts
import { useQuery } from '@tanstack/react-query';
import { API_CONFIG } from '@/config/api';

export function useRankings(birthYear: number, scope: string, position: string) {
  return useQuery({
    queryKey: ['rankings', birthYear, scope, position],
    queryFn: async () => {
      const response = await fetch(
        `${API_CONFIG.getRankings}?birthYear=${birthYear}&scope=${scope}&position=${position}&limit=250`
      );
      if (!response.ok) throw new Error('Failed to fetch rankings');
      return response.json();
    },
  });
}
```

---

## ✅ All Functions Active

All Cloud Functions are deployed and ready to use!

- **CORS Enabled:** ✓ All origins allowed
- **Authentication:** Headers for marketplace (X-User-ID)
- **Rate Limits:** Default Cloud Functions limits apply
- **Monitoring:** View logs in [Cloud Console](https://console.cloud.google.com/functions?project=prodigy-ranking)

---

## 🧪 Quick Test

Test the algorithm API:
```bash
curl "https://getstats-u4ztvt4wva-uc.a.run.app"
```

Test the marketplace API:
```bash
curl "https://getcardmarketdata-u4ztvt4wva-uc.a.run.app?series_id=PR2025-879926-001"
```

---

**Your APIs are live and ready for Loveable integration!** 🎉

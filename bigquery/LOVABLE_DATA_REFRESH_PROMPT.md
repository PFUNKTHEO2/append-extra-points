# Lovable: Ensure Latest Data for NEPSAC Rankings & PowerGrid

## Overview
Make sure the NEPSAC GameDay pages are pulling LIVE data from our APIs, not cached or stale data. Both APIs return real-time data from our BigQuery database.

---

## API Endpoints

### 1. Power Rankings API
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings
```

**Parameters:**
- `season` (required): `2025-26`
- `limit` (optional): Number of teams to return (default: all)

**Example:**
```javascript
const response = await fetch('https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26');
const data = await response.json();
// data.rankings = array of teams with rank, name, record, etc.
```

**Response Structure:**
```json
{
  "rankings": [
    {
      "rank": 1,
      "name": "Dexter",
      "record": { "wins": 15, "losses": 2, "ties": 1 },
      "winPct": 0.861,
      "goalsFor": 78,
      "goalsAgainst": 32,
      "streak": "W3"
    }
  ],
  "lastUpdated": "2026-01-27T..."
}
```

---

### 2. PowerGrid API (Playoff Probabilities)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid
```

**Parameters:**
- `season` (required): `2025-26`

**Example:**
```javascript
const response = await fetch('https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26');
const data = await response.json();
```

**Response Structure:**
```json
{
  "teams": [
    {
      "powerRank": 1,
      "name": "Dexter",
      "classification": "Large",
      "enrollment": 265,
      "ovr": 95,
      "record": { "wins": 15, "losses": 2, "ties": 1 },
      // MUTUALLY EXCLUSIVE: High Elite 8 = Low Division
      "elite8Bid": 99,        // 99% chance for Elite 8
      "elite8Champ": 12.6,    // If in Elite 8, chance to win
      "largeSchoolBid": 1,    // Only 1% (must MISS Elite 8 first!)
      "largeSchoolChamp": 0.3,
      "smallSchoolBid": 0,    // Not applicable (Large school)
      "smallSchoolChamp": 0,
      // Legacy format for backwards compatibility
      "probabilities": {
        "makeElite8": 99,
        "winElite8": 12.6,
        "makeDivision": 1,
        "winDivision": 0.3
      }
    }
  ],
  "currentElite8": [...],
  "largeSchoolContenders": [...],
  "smallSchoolContenders": [...],
  "summary": {
    "totalTeams": 55,
    "largeSchools": 28,
    "smallSchools": 27,
    "currentElite8Composition": { "large": 6, "small": 2 }
  },
  "lastUpdated": "2026-01-27T..."
}
```

---

## Implementation Requirements

### 1. Always Fetch Fresh Data
Do NOT cache API responses for more than 5 minutes. Data changes after every game.

```javascript
// Good - fetch on component mount and refresh periodically
useEffect(() => {
  const fetchData = async () => {
    const res = await fetch('...?season=2025-26');
    const data = await res.json();
    setRankings(data);
  };

  fetchData();
  const interval = setInterval(fetchData, 5 * 60 * 1000); // Refresh every 5 min
  return () => clearInterval(interval);
}, []);
```

### 2. Display Last Updated Timestamp
Show users when data was last refreshed:
```javascript
<p className="text-sm text-gray-500">
  Last updated: {new Date(data.lastUpdated).toLocaleString()}
</p>
```

### 3. Loading States
Show loading indicator while fetching:
```javascript
if (loading) return <Spinner />;
```

---

## Key Data Points to Display

### Power Rankings Page
- Rank (1-55)
- Team name
- Record (W-L-T)
- Win percentage
- Goals for/against
- Current streak

### PowerGrid Page
- Power Rank (overall 1-55)
- Team name
- Classification (Large/Small)
- OVR rating (0-99)
- Record
- **6 Probability Columns (MUTUALLY EXCLUSIVE):**
  1. Elite 8 Bid % - chance to make Elite 8 tournament
  2. Elite 8 Champ % - chance to win Elite 8 tournament
  3. Large School Bid % - chance to make Large School (ONLY if they MISS Elite 8)
  4. Large School Champ % - chance to win Large School tournament
  5. Small School Bid % - chance to make Small School (ONLY if they MISS Elite 8)
  6. Small School Champ % - chance to win Small School tournament

### Tournament Structure - MUTUALLY EXCLUSIVE
- **Elite 8**: Top 8 teams overall make this tournament
- **Large School Tournament**: Large schools who MISSED Elite 8
- **Small School Tournament**: Small schools who MISSED Elite 8

**CRITICAL**: A team CANNOT be in both Elite 8 AND their division tournament!

Example probabilities:
- **Dexter #1**: 99% Elite 8 → 1% Large School (almost certain for Elite 8)
- **Canterbury #9**: 45% Elite 8 → 54% Small School (could go either way)
- **Brunswick #13**: 10% Elite 8 → 86% Large School (likely division tournament)

---

## Verification

After implementation, verify the top 5 teams match:
1. Dexter (Large)
2. Avon Old Farms (Large)
3. Belmont Hill (Large)
4. Kimball Union (Small)
5. Tabor (Large)

If rankings don't match, there's a caching or data issue.

---

## Error Handling

```javascript
try {
  const response = await fetch(url);
  if (!response.ok) throw new Error('API error');
  const data = await response.json();
  return data;
} catch (error) {
  console.error('Failed to fetch rankings:', error);
  // Show user-friendly error message
  return null;
}
```

---

*Data Source: BigQuery `algorithm_core.nepsac_team_rankings` table*
*APIs deployed on Google Cloud Functions*
*Last updated: 2026-01-27*

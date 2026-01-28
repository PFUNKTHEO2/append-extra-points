# NEPSAC GameDay - American Odds Integration for Lovable

## Overview

The NEPSAC GameDay API now returns American-style betting odds alongside prediction percentages. This document explains how to integrate and display these odds in the Lovable frontend.

---

## API Endpoints

All endpoints are hosted at:
```
https://us-central1-prodigy-ranking.cloudfunctions.net/
```

### 1. Schedule API
```
GET /getNepsacSchedule?date=2026-01-22&season=2025-26
```

### 2. Matchup API
```
GET /getNepsacMatchup?gameId={gameId}
```

### 3. Past Results API
```
GET /getNepsacPastResults?season=2025-26&limit=200
```

### 4. PowerGrid API (Tournament Probabilities)
```
GET /getNepsacPowerGrid?season=2025-26
```

---

## Prediction Response Format

All prediction objects now include a `confidenceOdds` field:

```typescript
prediction: {
  winnerId: string | null;      // Team ID of predicted winner
  confidence: number | null;    // Percentage (0-100)
  confidenceOdds: string | null; // American odds format
  status: string;               // "available" or "Missing Data"
}
```

### Example Response
```json
{
  "prediction": {
    "winnerId": "taft",
    "confidence": 62,
    "confidenceOdds": "-163",
    "status": "available"
  }
}
```

---

## American Odds Explained

| Confidence % | Odds | Meaning |
|-------------|------|---------|
| 50% | +100 | Even odds (toss-up) |
| 55% | -122 | Slight favorite |
| 60% | -150 | Moderate favorite |
| 65% | -186 | Strong favorite |
| 70% | -233 | Heavy favorite |
| 75% | -300 | Very heavy favorite |
| 80% | -400 | Dominant favorite |

**Reading the odds:**
- **Negative odds (-163)**: Favorite. Bet $163 to win $100
- **Positive odds (+150)**: Underdog. Bet $100 to win $150

---

## TypeScript Interfaces

Update your interfaces to include the odds fields:

```typescript
// For Schedule and Matchup APIs
interface NepsacGame {
  gameId: string;
  gameDate: string;
  gameTime: string;
  awayTeam: NepsacTeam;
  homeTeam: NepsacTeam;
  prediction: {
    winnerId: string | null;
    confidence: number | null;
    confidenceOdds: string | null;  // NEW FIELD
    status?: string;
  };
}

// For Past Results API
interface NepsacPastResultGame {
  gameId: string;
  awayTeam: NepsacPastResultTeam;
  homeTeam: NepsacPastResultTeam;
  prediction: {
    winnerId: string;
    confidence: number;
    confidenceOdds: string | null;  // NEW FIELD
  };
  result: 'correct' | 'incorrect' | 'tie';
}

// For PowerGrid API
interface PowerGridTeam {
  teamId: string;
  name: string;
  elite8Bid: number;
  elite8BidOdds: string;      // NEW FIELD
  elite8Champ: number;
  elite8ChampOdds: string;    // NEW FIELD
  largeSchoolBid: number;
  largeSchoolBidOdds: string; // NEW FIELD
  largeSchoolChamp: number;
  largeSchoolChampOdds: string; // NEW FIELD
  smallSchoolBid: number;
  smallSchoolBidOdds: string; // NEW FIELD
  smallSchoolChamp: number;
  smallSchoolChampOdds: string; // NEW FIELD
}
```

---

## UI Display Recommendations

### 1. Prediction Bar / Banner

Display both percentage and odds:

```tsx
<div className="prediction-display">
  <span className="confidence-pct">{confidence}%</span>
  {confidenceOdds && (
    <span className="confidence-odds">({confidenceOdds})</span>
  )}
  <span className="predicted-team">for {predictedTeamName}</span>
</div>
```

**Styling:**
```css
.confidence-pct {
  font-size: 1.5rem;
  font-weight: bold;
  color: #22c55e; /* Green for high confidence */
}

.confidence-odds {
  font-size: 1.2rem;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.8);
  margin-left: 8px;
}
```

### 2. Game Cards (Compact View)

Show odds in the prediction badge:

```tsx
<div className="game-card-prediction">
  {confidence}% ({confidenceOdds})
</div>
```

### 3. Past Performance Results

Include odds in the result badges:

```tsx
<span className="prediction-badge">
  {confidence}% ({confidenceOdds})
</span>
```

---

## Fetching Data Example

```typescript
async function fetchSchedule(date: string): Promise<NepsacGame[]> {
  const response = await fetch(
    `https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacSchedule?date=${date}&season=2025-26`
  );
  const data = await response.json();
  return data.games;
}

// Usage
const games = await fetchSchedule('2026-01-22');
games.forEach(game => {
  console.log(`${game.awayTeam.shortName} @ ${game.homeTeam.shortName}`);
  console.log(`Prediction: ${game.prediction.confidence}% (${game.prediction.confidenceOdds})`);
});
```

---

## Component Updates Required

### 1. PredictionBar Component

```tsx
interface PredictionBarProps {
  awayTeam: Team;
  homeTeam: Team;
  predictedWinner: 'away' | 'home';
  confidence: number;
  confidenceOdds: string | null; // Add this prop
}

function PredictionBar({
  awayTeam,
  homeTeam,
  predictedWinner,
  confidence,
  confidenceOdds
}: PredictionBarProps) {
  return (
    <div className="prediction-banner">
      {/* Slider/bar visualization */}
      <div className="prediction-track">
        <div className="prediction-marker" style={{ left: `${sliderPosition}%` }}>
          {confidence}%
        </div>
      </div>

      {/* Team labels */}
      <div className="prediction-teams">
        <span>{awayTeam.shortName}</span>
        <span>{homeTeam.shortName}</span>
      </div>

      {/* Odds display - NEW */}
      {confidenceOdds && (
        <div className="odds-display">
          <span className="odds-value">{confidenceOdds}</span>
          <span className="odds-label">American Odds</span>
        </div>
      )}
    </div>
  );
}
```

### 2. GameCard Component

```tsx
function GameCard({ game, isSelected, onClick }: GameCardProps) {
  return (
    <div className={`game-card ${isSelected ? 'active' : ''}`} onClick={onClick}>
      {game.prediction.confidence && (
        <div className="game-card-prediction">
          {game.prediction.confidence}%
          {game.prediction.confidenceOdds && ` (${game.prediction.confidenceOdds})`}
        </div>
      )}
      {/* ... rest of card */}
    </div>
  );
}
```

### 3. PastResultRow Component

```tsx
function PastResultRow({ game }: { game: NepsacPastResultGame }) {
  return (
    <div className="result-row">
      {/* Team scores */}
      <div className="teams">
        <span>{game.awayTeam.shortName} {game.awayTeam.score}</span>
        <span>{game.homeTeam.shortName} {game.homeTeam.score}</span>
      </div>

      {/* Prediction with odds */}
      <div className="prediction-badge">
        {game.prediction.confidence}%
        {game.prediction.confidenceOdds && ` (${game.prediction.confidenceOdds})`}
      </div>

      {/* Result icon */}
      <ResultIcon result={game.result} />
    </div>
  );
}
```

---

## Styling for Odds Display

```css
/* Odds styling - matches the cyberpunk theme */
.odds-display {
  text-align: center;
  margin-top: 8px;
}

.odds-value {
  font-family: 'Orbitron', monospace;
  font-size: 1.1rem;
  font-weight: bold;
  color: #a0a0b0;
}

/* Negative odds (favorites) - slightly cyan tint */
.odds-value.favorite {
  color: #06b6d4;
}

/* Positive odds (underdogs) - slightly amber tint */
.odds-value.underdog {
  color: #f59e0b;
}

.odds-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-top: 2px;
}

/* Inline odds in badges */
.prediction-badge .odds {
  opacity: 0.8;
  margin-left: 4px;
}
```

---

## Testing

Test these endpoints to verify odds are returned:

1. **Schedule with predictions:**
   ```
   https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacSchedule?date=2026-01-22
   ```

2. **Single matchup:**
   ```
   https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacMatchup?gameId=7a054cba-2b98-4c3c-9195-4048b95d2393
   ```

3. **Past results:**
   ```
   https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPastResults?season=2025-26
   ```

4. **PowerGrid:**
   ```
   https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid
   ```

---

## Summary

1. **API returns `confidenceOdds`** alongside `confidence` percentage
2. **Format**: String like "-163" or "+150"
3. **Display**: Show as `62% (-163)` or similar
4. **Null handling**: Some games may have null odds if prediction unavailable
5. **All endpoints updated**: Schedule, Matchup, Past Results, PowerGrid

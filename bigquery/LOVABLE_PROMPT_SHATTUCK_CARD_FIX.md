# Fix Team Card Display for Shattuck St. Mary's

## The Problem

The Shattuck St. Mary's team card is not displaying because the game data uses the full display name "Shattuck St. Mary's" but the card lookup expects a slug ID like "shattuck-st-marys".

---

## Solution: Update team-logos.ts

Add this helper function to `src/lib/team-logos.ts`:

```typescript
/**
 * Convert display team name to team ID slug
 * Handles special cases like "Shattuck St. Mary's" -> "shattuck-st-marys"
 */
export function teamNameToId(teamName: string): string {
  // Special case mappings for non-standard names
  const specialCases: Record<string, string> = {
    "shattuck st. mary's": "shattuck-st-marys",
    "shattuck st mary's": "shattuck-st-marys",
    "shattuck st. marys": "shattuck-st-marys",
    "shattuck st marys": "shattuck-st-marys",
    "shattuck": "shattuck-st-marys",
    "bb&n": "bbn",
    "buckingham browne & nichols": "bbn",
    "nmh": "nmh",
    "northfield mount hermon": "nmh",
  };

  const normalized = teamName.toLowerCase().trim();

  // Check special cases first
  if (specialCases[normalized]) {
    return specialCases[normalized];
  }

  // Default: convert to slug format
  return normalized
    .replace(/['']/g, "")
    .replace(/&/g, "and")
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}
```

---

## Update Card Display Component

Wherever you display team cards, update the logic to handle both `team_id` fields and display name conversion:

```typescript
import { getTeamCardUrl, teamNameToId } from '@/lib/team-logos';

interface Game {
  away: string;
  home: string;
  away_id?: string;  // Optional: pre-computed team ID
  home_id?: string;  // Optional: pre-computed team ID
  // ... other fields
}

function GameCard({ game }: { game: Game }) {
  // Use pre-computed ID if available, otherwise convert display name
  const awayTeamId = game.away_id || teamNameToId(game.away);
  const homeTeamId = game.home_id || teamNameToId(game.home);

  const awayCardUrl = getTeamCardUrl(awayTeamId, false, 'left');
  const homeCardUrl = getTeamCardUrl(homeTeamId, true, 'left');

  return (
    <div className="flex items-center gap-4">
      <img
        src={awayCardUrl || '/placeholder-card.webp'}
        alt={game.away}
        className="w-32 h-32 rounded-lg"
        onError={(e) => e.currentTarget.src = '/placeholder-card.webp'}
      />
      <span className="text-2xl font-bold text-purple-400">@</span>
      <img
        src={homeCardUrl || '/placeholder-card.webp'}
        alt={game.home}
        className="w-32 h-32 rounded-lg"
        onError={(e) => e.currentTarget.src = '/placeholder-card.webp'}
      />
    </div>
  );
}
```

---

## Data Format Reference

The prediction display JSON now includes optional `away_id` and `home_id` fields for special cases:

```json
{
  "away": "Dexter",
  "home": "Shattuck St. Mary's",
  "away_id": "dexter",
  "home_id": "shattuck-st-marys",
  "pick": "dexter",
  "confidence": 54,
  "tier": "Competitive",
  "note": "Shattuck normalized to NEPSAC - elite national program (one-off game)"
}
```

---

## Shattuck Card URLs

All 4 Shattuck card variants are available:

```
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/shattuck-st-marys_home_left.webp
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/shattuck-st-marys_home_right.webp
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/shattuck-st-marys_away_left.webp
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/shattuck-st-marys_away_right.webp
```

---

## Quick Fix Checklist

1. Add `teamNameToId()` function to `team-logos.ts`
2. Update card display components to use: `game.home_id || teamNameToId(game.home)`
3. Add error handling with `onError` fallback to placeholder
4. Test with Dexter @ Shattuck St. Mary's games (Jan 23-24)

---

## Note About Shattuck

Shattuck St. Mary's is NOT a regular NEPSAC team - they are an elite national program from Minnesota. These are one-off exhibition games against Dexter. The prediction has been normalized to reflect Shattuck's true strength (54% Dexter / 46% Shattuck) rather than the default weak rating.

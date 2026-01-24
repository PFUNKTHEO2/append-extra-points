# Add Team Card Images to NEPSAC GameDay

## Task

Add team trading card images to the NEPSAC GameDay app. The card images are hosted on GitHub and need a mapping from API team IDs to image URLs.

---

## Step 1: Create Team Logos Utility

Create a new file `src/lib/team-logos.ts`:

```typescript
// Team card image mapping for NEPSAC GameDay
// Maps team_id from API to image slug used in card filenames

export const TEAM_ID_TO_IMAGE_SLUG: Record<string, string> = {
  "albany-academy": "albany-academy",
  "andover": "andover",
  "austin-prep": "austin-prep",
  "avon-old-farms": "avon-old-farms",
  "bbn": "buckingham-browne-and-nichols",
  "belmont-hill": "belmont-hill-school",
  "berkshire": "berkshire-school",
  "berwick": "berwick-academy",
  "brewster": "brewster-academy",
  "brooks": "brooks-school",
  "brunswick": "brunswick-school",
  "canterbury": "canterbury-school",
  "choate": "choate-rosemary-hall",
  "cushing": "cushing-academy",
  "deerfield": "deerfield-academy",
  "dexter": "dexter-southfield",
  "exeter": "phillips-exeter-academy",
  "frederick-gunn": "frederick-gunn-school",
  "governors": "the-governors-academy",
  "groton": "groton-school",
  "hebron": "hebron-academy",
  "holderness": "holderness-school",
  "hoosac": "hoosac-school",
  "hotchkiss": "hotchkiss-school",
  "kent": "kent-school",
  "kents-hill": "kents-hill-school",
  "kimball-union": "kimball-union-academy",
  "kingswood-oxford": "kingswood-oxford",
  "lawrence": "lawrence-academy",
  "loomis": "loomis-chaffee",
  "middlesex": "middlesex-school",
  "millbrook": "millbrook-school",
  "milton": "milton-academy",
  "new-hampton": "new-hampton-school",
  "nmh": "northfield-mount-hermon",
  "nobles": "noble-and-greenough",
  "north-yarmouth": "north-yarmouth-academy",
  "pingree": "pingree-school",
  "pomfret": "pomfret-school",
  "portsmouth-abbey": "portsmouth-abbey",
  "proctor": "proctor-academy",
  "rivers": "rivers-school",
  "roxbury-latin": "roxbury-latin",
  "salisbury": "salisbury-school",
  "st-georges": "st-georges-school",
  "st-lukes": "st-lukes-school",
  "st-marks": "st-marks-school",
  "st-pauls": "st-pauls-school",
  "st-sebastians": "st-sebastians-school",
  "tabor": "tabor-academy",
  "taft": "taft-school",
  "thayer": "thayer-academy",
  "tilton": "tilton-school",
  "trinity-pawling": "trinity-pawling-school",
  "vermont-academy": "vermont-academy",
  "westminster": "westminster-school",
  "wilbraham-monson": "wilbraham-and-monson-academy",
  "williston": "williston-northampton",
  "winchendon": "winchendon-school",
  "worcester": "worcester-academy",
};

const BASE_URL = "https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards";

/**
 * Get the card image URL for a team
 * @param teamId - The team_id from the API (e.g., "berkshire", "brooks")
 * @param isHome - Whether team is home (true) or away (false)
 * @param side - "left" or "right" side of card
 */
export function getTeamCardUrl(
  teamId: string,
  isHome: boolean,
  side: "left" | "right"
): string {
  const imageSlug = TEAM_ID_TO_IMAGE_SLUG[teamId] || teamId;
  const homeAway = isHome ? "home" : "away";
  return `${BASE_URL}/${imageSlug}_${homeAway}_${side}.webp`;
}

/**
 * Get both card URLs for a team (left and right)
 */
export function getTeamCardUrls(teamId: string, isHome: boolean) {
  return {
    left: getTeamCardUrl(teamId, isHome, "left"),
    right: getTeamCardUrl(teamId, isHome, "right"),
  };
}
```

---

## Step 2: Create TeamCard Component

Create `src/components/TeamCard.tsx`:

```tsx
import { useState } from 'react';
import { getTeamCardUrl } from '@/lib/team-logos';

interface TeamCardProps {
  teamId: string;
  teamName?: string;
  isHome: boolean;
  className?: string;
}

export default function TeamCard({ teamId, teamName, isHome, className = '' }: TeamCardProps) {
  const [imageError, setImageError] = useState(false);
  const cardUrl = getTeamCardUrl(teamId, isHome, 'left');

  if (imageError) {
    return (
      <div className={`bg-gradient-to-br from-purple-900/50 to-slate-900/50 rounded-lg flex items-center justify-center border border-purple-500/30 aspect-square ${className}`}>
        <span className="text-xl font-bold text-purple-400 uppercase">
          {teamName || teamId}
        </span>
      </div>
    );
  }

  return (
    <img
      src={cardUrl}
      alt={`${teamName || teamId} card`}
      className={`rounded-lg shadow-lg object-cover ${className}`}
      onError={() => setImageError(true)}
    />
  );
}
```

---

## Step 3: Usage Examples

### Display a single team card:
```tsx
import TeamCard from '@/components/TeamCard';

<TeamCard teamId="berkshire" isHome={true} className="w-48" />
```

### Display matchup with both teams:
```tsx
import { getTeamCardUrl } from '@/lib/team-logos';

function MatchupCards({ awayTeamId, homeTeamId }: { awayTeamId: string; homeTeamId: string }) {
  return (
    <div className="flex items-center gap-4">
      <img
        src={getTeamCardUrl(awayTeamId, false, 'left')}
        alt="Away team"
        className="w-40 rounded-lg"
      />
      <span className="text-2xl font-bold text-fuchsia-400">VS</span>
      <img
        src={getTeamCardUrl(homeTeamId, true, 'left')}
        alt="Home team"
        className="w-40 rounded-lg"
      />
    </div>
  );
}
```

---

## Image URL Format

All 60 NEPSAC teams have card images in this format:
```
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/{slug}_{home|away}_{left|right}.webp
```

### Examples:
- Berkshire (home, left): `berkshire-school_home_left.webp`
- Brooks (away, right): `brooks-school_away_right.webp`
- BB&N (home, left): `buckingham-browne-and-nichols_home_left.webp`

---

## Key Points

1. The API returns short team IDs like `"berkshire"` or `"bbn"`
2. The mapping converts these to image slugs like `"berkshire-school"` or `"buckingham-browne-and-nichols"`
3. Each team has 4 card images: home_left, home_right, away_left, away_right
4. All images are 500x500 WebP format
5. Images are hosted on GitHub and publicly accessible

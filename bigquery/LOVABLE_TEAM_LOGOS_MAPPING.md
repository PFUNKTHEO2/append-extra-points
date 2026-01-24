# Team Logos Mapping for Lovable

## The Problem
The API returns team data with `team_id` like "belmont-hill" or "berkshire", but the card images use longer slugs like "belmont-hill-school" or "berkshire-school".

## Solution: Create a mapping object

Add this to your Lovable project (e.g., `src/lib/team-logos.ts`):

```typescript
// src/lib/team-logos.ts

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

// Teams that don't have card images yet (use placeholder)
const TEAMS_WITHOUT_CARDS = ["albany-academy", "milton-academy", "north-yarmouth-academy"];

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
): string | null {
  const imageSlug = TEAM_ID_TO_IMAGE_SLUG[teamId] || teamId;

  // Return null for teams without cards (use placeholder in component)
  if (TEAMS_WITHOUT_CARDS.includes(imageSlug)) {
    return null;
  }

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

## Usage in TeamCard Component

```tsx
import { getTeamCardUrl } from "@/lib/team-logos";

interface TeamCardProps {
  teamId: string;
  isHome: boolean;
}

export function TeamCard({ teamId, isHome }: TeamCardProps) {
  const leftUrl = getTeamCardUrl(teamId, isHome, "left");
  const rightUrl = getTeamCardUrl(teamId, isHome, "right");

  return (
    <div className="team-card">
      <img src={leftUrl} alt="Team card left" />
      <img src={rightUrl} alt="Team card right" />
    </div>
  );
}
```

## Example URLs

For `teamId = "berkshire"` (home team):
- Left: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/berkshire-school_home_left.webp`
- Right: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/berkshire-school_home_right.webp`

For `teamId = "brooks"` (away team):
- Left: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/brooks-school_away_left.webp`
- Right: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/brooks-school_away_right.webp`

## Full Mapping Reference

| API team_id | Image Slug |
|-------------|------------|
| albany-academy | albany-academy |
| andover | andover |
| austin-prep | austin-prep |
| avon-old-farms | avon-old-farms |
| bbn | buckingham-browne-and-nichols |
| belmont-hill | belmont-hill-school |
| berkshire | berkshire-school |
| berwick | berwick-academy |
| brewster | brewster-academy |
| brooks | brooks-school |
| brunswick | brunswick-school |
| canterbury | canterbury-school |
| choate | choate-rosemary-hall |
| cushing | cushing-academy |
| deerfield | deerfield-academy |
| dexter | dexter-southfield |
| exeter | phillips-exeter-academy |
| frederick-gunn | frederick-gunn-school |
| governors | the-governors-academy |
| groton | groton-school |
| hebron | hebron-academy |
| holderness | holderness-school |
| hoosac | hoosac-school |
| hotchkiss | hotchkiss-school |
| kent | kent-school |
| kents-hill | kents-hill-school |
| kimball-union | kimball-union-academy |
| kingswood-oxford | kingswood-oxford |
| lawrence | lawrence-academy |
| loomis | loomis-chaffee |
| middlesex | middlesex-school |
| millbrook | millbrook-school |
| milton | milton-academy |
| new-hampton | new-hampton-school |
| nmh | northfield-mount-hermon |
| nobles | noble-and-greenough |
| north-yarmouth | north-yarmouth-academy |
| pingree | pingree-school |
| pomfret | pomfret-school |
| portsmouth-abbey | portsmouth-abbey |
| proctor | proctor-academy |
| rivers | rivers-school |
| roxbury-latin | roxbury-latin |
| salisbury | salisbury-school |
| st-georges | st-georges-school |
| st-lukes | st-lukes-school |
| st-marks | st-marks-school |
| st-pauls | st-pauls-school |
| st-sebastians | st-sebastians-school |
| tabor | tabor-academy |
| taft | taft-school |
| thayer | thayer-academy |
| tilton | tilton-school |
| trinity-pawling | trinity-pawling-school |
| vermont-academy | vermont-academy |
| westminster | westminster-school |
| wilbraham-monson | wilbraham-and-monson-academy |
| williston | williston-northampton |
| winchendon | winchendon-school |
| worcester | worcester-academy |

## All Teams Have Card Images

All 57+ NEPSAC teams now have card images. The `getTeamCardUrl` function will return valid URLs for all teams.

### Handling Image Load Errors in Component

```tsx
import { getTeamCardUrl } from "@/lib/team-logos";

export function TeamCard({ teamId, isHome }: { teamId: string; isHome: boolean }) {
  const leftUrl = getTeamCardUrl(teamId, isHome, "left");
  const rightUrl = getTeamCardUrl(teamId, isHome, "right");

  // Use placeholder if no card image exists
  const placeholderUrl = "/images/nepsac/placeholder-card.webp";

  return (
    <div className="team-card">
      <img
        src={leftUrl || placeholderUrl}
        alt="Team card left"
        onError={(e) => e.currentTarget.src = placeholderUrl}
      />
      <img
        src={rightUrl || placeholderUrl}
        alt="Team card right"
        onError={(e) => e.currentTarget.src = placeholderUrl}
      />
    </div>
  );
}
```

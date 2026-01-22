# NEPSAC GameDay Session Notes - January 21, 2026

## Project Overview

Building a NEPSAC prep school hockey GameDay application with:
- Carousel-based game navigation
- Animated team matchup cards
- ProdigyChain-style trading cards for players
- Live on theprodigychain.com via Lovable

## What Was Accomplished

### 1. Standalone HTML Prototype (COMPLETE ✓)
**File:** `bigquery/nepsac_matchup_page.html`
**Live URL:** https://pfunktheo2.github.io/append-extra-points/bigquery/nepsac_matchup_page.html

Features implemented:
- Game carousel with prev/next arrows (replaces grid)
- Keyboard navigation (arrow keys)
- Mouse wheel scrolling on carousel
- Touch swipe support
- Team card fall-in animations when switching games
- Collapsible stats and players sections
- ProdigyChain trading card design for player cards
- All 60+ NEPSAC teams with data

### 2. Lovable React Project
**Project URL:** https://lovable.dev/projects/57d76901-6c82-4013-9b6e-a71cd9b204ed
**Preview URL:** https://prodigy-rankings.lovable.app/gameday

The Lovable project already had a `/gameday` route. We're updating it to match the HTML prototype.

### 3. Documentation Created
- `bigquery/LOVABLE_NEPSAC_GAMEDAY_PROMPT.md` - Full specification for Lovable
- Complete CSS for ProdigyChain trading cards
- React component examples
- TypeScript interfaces

### 4. Assets on GitHub

**Team Logos:**
- File: `bigquery/nepsac_logos_absolute.json`
- Contains 58 team logo URLs
- Mix of GitHub raw URLs and CDN URLs

**Team Trading Cards:**
- Folder: `bigquery/nepsac-cards/`
- 232 trading card images (4 per team: home_left, home_right, away_left, away_right)
- Format: `{slug}_away_right.webp` (e.g., `choate-rosemary-hall_home_left.webp`)
- Manifest: `bigquery/nepsac-cards/manifest.json`

---

## Current Issue: Team Trading Cards Not Loading in Lovable

### The Problem
Salisbury shows correct trading card, but Choate (and likely others) shows logo fallback instead.

### Root Cause
The API returns `team.name` values that don't match the keys in `TEAM_CARD_SLUGS` mapping.

Example:
- API returns: `team.name = "Choate"` (short name)
- Map expects: `"Choate Rosemary Hall"` (full name)
- Result: Slug lookup fails, falls back to logo

### What We Tried

1. **Created `src/lib/team-logos.ts`** with:
   - `TEAM_LOGOS` - Maps team names to logo URLs
   - `TEAM_CARD_SLUGS` - Maps team names to trading card file slugs
   - `getTeamCardUrl(teamName, isHome)` - Returns trading card URL
   - `getTeamLogoUrl(teamName)` - Returns logo URL

2. **Updated `TeamCard.tsx`** fallback order:
   - First: Try trading card URL
   - Second: Try curated logo
   - Third: Try API logo
   - Fourth: Show initials

3. **Added debug logging** to see what `team.name` the API returns

4. **Added aliases** for common short names (Choate, Hebron, Exeter, etc.)

### Still Not Working
Even with aliases added, Choate still shows logo instead of trading card.

### Next Steps to Debug

1. **Check browser console** on https://prodigy-rankings.lovable.app/gameday
   - Look for `[TeamCard]` log messages
   - Find exact `team.name` value for Choate from API

2. **Verify the exact team.name** the API returns and add that exact string to `TEAM_CARD_SLUGS`

3. **Possible issues:**
   - Whitespace/encoding differences in team names
   - The aliases weren't actually saved/deployed
   - Image onError still not triggering fallback correctly

---

## Key Files & Locations

### Local Repository
```
C:\Users\phili\OneDrive\Documents\GitHub\append-extra-points\bigquery\
├── nepsac_matchup_page.html          # Working HTML prototype
├── nepsac_logos_absolute.json        # Team logo URL mapping
├── nepsac-cards/                     # Trading card images
│   ├── manifest.json                 # Slug to filename mapping
│   ├── choate-rosemary-hall_home_left.webp
│   ├── salisbury-school_home_left.webp
│   └── ... (232 total images)
├── LOVABLE_NEPSAC_GAMEDAY_PROMPT.md  # Lovable specification
└── SESSION_NOTES_NEPSAC_GAMEDAY_JAN21.md  # This file
```

### GitHub URLs
- Repo: https://github.com/PFUNKTHEO2/append-extra-points
- Trading cards base: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/`
- Example card URL: `https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/choate-rosemary-hall_home_left.webp`

### Lovable Project Files
```
src/
├── pages/GameDay.tsx                 # Main GameDay page
├── components/gameday/
│   ├── TeamCard.tsx                  # Team card component (needs fixing)
│   ├── GameCarousel.tsx              # Game carousel navigation
│   ├── PlayerCard.tsx                # Player trading cards
│   └── ...
├── lib/
│   ├── team-logos.ts                 # Logo and card slug mappings
│   └── nepsac-api.ts                 # API types and utilities
└── hooks/
    └── useNepsacApi.ts               # API hooks
```

---

## Trading Card Slug Mapping Reference

The trading cards use slugified names, NOT the API teamId:

| API team.name (varies) | Card Slug | Example File |
|------------------------|-----------|--------------|
| Choate / Choate Rosemary Hall | choate-rosemary-hall | choate-rosemary-hall_home_left.webp |
| Salisbury / Salisbury School | salisbury-school | salisbury-school_home_left.webp |
| Hebron / Hebron Academy | hebron-academy | hebron-academy_home_left.webp |
| Andover / Phillips Academy | andover | andover_home_left.webp |
| Exeter / Phillips Exeter | phillips-exeter-academy | phillips-exeter-academy_home_left.webp |
| NMH / Northfield Mount Hermon | northfield-mount-hermon | northfield-mount-hermon_home_left.webp |

Full mapping in `bigquery/nepsac-cards/manifest.json`

---

## API Information

### Endpoints (via Lovable's backend)
- `GET /getNepsacDates` - Game dates for a season
- `GET /getNepsacSchedule?date=YYYY-MM-DD` - Games for a specific date
- `GET /getNepsacMatchup` - Full matchup details including teams and players

### Team Data from API
```typescript
interface FullTeamInfo {
  teamId: string;      // e.g., "choate" or "hebron"
  name: string;        // e.g., "Choate" or "Hebron" (THE KEY FOR LOOKUP)
  shortName: string;
  logoUrl: string;     // API's logo (often incorrect/outdated)
  record: string;
  wins: number;
  losses: number;
  ties: number;
  // ... more fields
}
```

---

## Tomorrow's Action Plan

1. **Get exact API team.name values**
   - Check browser console for `[TeamCard]` logs
   - Or query the API directly to see all team names

2. **Fix the TEAM_CARD_SLUGS mapping**
   - Add exact API team.name → slug entries
   - Consider normalizing team names (lowercase, remove punctuation)

3. **Alternative approach if needed**
   - Fetch manifest.json at runtime
   - Match by fuzzy name comparison instead of exact lookup

4. **Test thoroughly**
   - Verify all 60+ teams show trading cards
   - Check both home and away positions

---

## Commits Made Today

1. `c3be29d` - Add carousel UI and ProdigyChain trading cards to NEPSAC GameDay
2. `b1716b1` - Add Lovable prompt for NEPSAC GameDay React implementation
3. `b14b36e` - Add NEPSAC team logos JSON mapping

---

## Contact/Resources

- Lovable project: https://lovable.dev/projects/57d76901-6c82-4013-9b6e-a71cd9b204ed
- GitHub Pages preview: https://pfunktheo2.github.io/append-extra-points/bigquery/nepsac_matchup_page.html
- Production target: theprodigychain.com/gameday

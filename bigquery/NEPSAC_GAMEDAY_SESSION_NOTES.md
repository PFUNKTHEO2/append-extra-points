# NEPSAC GameDay - Resume Document
## Ready to Continue - January 21, 2026

---

# QUICK START - DO THIS FIRST

## 1. Verify Images Still Work
Open in browser:
```
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/avon-old-farms_home_left.webp
```
Should show Avon Old Farms trading card. ✓ CONFIRMED WORKING

## 2. Give Lovable This Base URL
```
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/
```

## 3. Give Lovable This Helper Function
```javascript
const CARD_BASE_URL = 'https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards';

function getTeamCardUrl(teamId, isHome) {
  const variant = isHome ? 'home_left' : 'away_right';
  return `${CARD_BASE_URL}/${teamId}_${variant}.webp`;
}

// Usage:
// Away team card (facing right): getTeamCardUrl('avon-old-farms', false)
// Home team card (facing left):  getTeamCardUrl('taft-school', true)
```

---

# WHAT'S ALREADY DONE

## Backend (100% Complete)
- ✅ 6 Cloud Functions deployed and working
- ✅ BigQuery tables with NEPSAC data
- ✅ Team aliases for name matching

## Trading Cards (100% Complete)
- ✅ 228 images optimized (500x500 WebP, ~50KB each)
- ✅ Hosted on GitHub (repo is public)
- ✅ URLs confirmed working

## Lovable Project (Started)
- ✅ Full prompt provided
- ⏳ Need to configure image URLs
- ⏳ Need to test API connections

---

# API ENDPOINTS (ALL WORKING)

Base: `https://us-central1-prodigy-ranking.cloudfunctions.net`

| Endpoint | Example |
|----------|---------|
| Game Dates | `/getNepsacGameDates?season=2025-26` |
| Schedule | `/getNepsacSchedule?date=2026-01-19` |
| Matchup | `/getNepsacMatchup?gameId=game_20260119_1` |
| Teams | `/getNepsacTeams?season=2025-26` |
| Standings | `/getNepsacStandings?season=2025-26` |
| Roster | `/getNepsacRoster?teamId=avon-old-farms` |

---

# TRADING CARD URL FORMAT

**Base URL:**
```
https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/
```

**Filename pattern:** `{team-slug}_{variant}.webp`

**Team slug rules:**
- Lowercase
- Spaces → hyphens
- Remove apostrophes

| Team Name | Slug |
|-----------|------|
| Avon Old Farms | `avon-old-farms` |
| St. Paul's School | `st-pauls-school` |
| Phillips Exeter Academy | `phillips-exeter-academy` |
| Buckingham Browne and Nichols | `buckingham-browne-and-nichols` |

**Variants for matchups:**
- Away team: `_away_right.webp` (facing →)
- Home team: `_home_left.webp` (facing ←)

---

# WHAT TO DO NEXT IN LOVABLE

1. **Open your Lovable project**

2. **Find where images are configured** (likely in a component or config file)

3. **Update to use GitHub URLs:**
   - Replace `/images/teams/` with the GitHub base URL
   - Or add the helper function above

4. **Test a matchup** - trading cards should appear

5. **If API not connected yet**, add these endpoints to fetch data

---

# KEY FILES

| File | Location |
|------|----------|
| Trading Cards | `bigquery/nepsac-cards/*.webp` |
| Image Manifest | `bigquery/nepsac-cards/manifest.json` |
| Integration Plan | `bigquery/NEPSAC_DYNAMIC_INTEGRATION_PLAN.md` |
| API Code | `api-backend/functions/nepsac.js` |
| Mascot Image | `bigquery/NEPSAC Logos/ace and scouty.png` |

---

# LINKS

- **GitHub Repo:** https://github.com/PFUNKTHEO2/append-extra-points
- **Trading Cards Folder:** https://github.com/PFUNKTHEO2/append-extra-points/tree/main/bigquery/nepsac-cards
- **Lovable:** https://lovable.dev

---

# IF SOMETHING BREAKS

**Images not loading?**
- Check the URL is exactly right (case sensitive)
- Verify repo is still public: `gh repo view PFUNKTHEO2/append-extra-points --json isPrivate`

**API not responding?**
- Test directly: `https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacGameDates?season=2025-26`
- Check Cloud Functions console in GCP

**Team not found?**
- Check `bigquery/nepsac_team_aliases.json` for name mappings
- Verify team slug matches filename in nepsac-cards folder

---

*Last updated: January 21, 2026 12:45 AM*
*Status: Ready to continue in Lovable*

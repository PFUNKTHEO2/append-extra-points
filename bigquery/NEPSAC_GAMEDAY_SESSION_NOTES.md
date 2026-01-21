# NEPSAC GameDay Session Notes - January 21, 2026

## What We Accomplished

### 1. Trading Card Image Optimization
- **Source:** `NEPSAC_Trading_Cards_Complete.zip` (1.68GB, 232 high-res PNGs)
- **Optimized:** Resized from 2048px to 500px, converted to WebP
- **Result:** 228 images at ~50KB each = 11.2MB total (99.3% reduction)
- **Location:** `bigquery/nepsac-cards/` (clean path, no spaces)

### 2. GitHub Hosting Setup
- Made repo public: `PFUNKTHEO2/append-extra-points`
- Pushed optimized images to: `bigquery/nepsac-cards/`
- **Base URL for images:**
```
https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards/{teamId}_{variant}.webp?raw=true
```

### 3. Lovable Project Started
- Created project with full prompt (EA Sports style NEPSAC GameDay)
- Need to configure image URLs to use GitHub hosting

---

## Files Created/Modified

| File | Purpose |
|------|---------|
| `bigquery/nepsac-cards/*.webp` | 228 optimized trading card images |
| `bigquery/nepsac-cards/manifest.json` | Team name to image filename mapping |
| `bigquery/optimize_trading_cards.py` | Script that created optimized images |
| `bigquery/NEPSAC Logos/optimized_cards/` | Duplicate of nepsac-cards (original location) |
| `bigquery/NEPSAC Logos/optimized_trading_cards.zip` | Zipped optimized images |

---

## API Endpoints (Already Deployed)

All Cloud Functions are live at:
```
https://us-central1-prodigy-ranking.cloudfunctions.net/
```

| Endpoint | Purpose |
|----------|---------|
| `getNepsacGameDates?season=2025-26` | Get dates with scheduled games |
| `getNepsacSchedule?date=2026-01-19` | Get games for a specific date |
| `getNepsacMatchup?gameId=xxx` | Get full matchup details |
| `getNepsacTeams?season=2025-26` | Get all teams with rankings |
| `getNepsacStandings?season=2025-26` | Get current standings |
| `getNepsacRoster?teamId=xxx` | Get team roster |

---

## Trading Card URL Format

**Pattern:**
```
https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards/{team-slug}_{variant}.webp?raw=true
```

**Team slug format:** lowercase, spaces to hyphens, remove apostrophes
- "Avon Old Farms" → `avon-old-farms`
- "St. Paul's School" → `st-pauls-school`

**Variants:**
- `home_left` - Home team (facing left ←)
- `home_right` - Home team (facing right →)
- `away_left` - Away team (facing left ←)
- `away_right` - Away team (facing right →)

**For matchups use:**
- Away team: `{slug}_away_right.webp` (facing →)
- Home team: `{slug}_home_left.webp` (facing ←)

**Example:**
```
https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards/avon-old-farms_home_left.webp?raw=true
```

---

## Where We Left Off

### Issue:
- `raw.githubusercontent.com` URLs were returning 404
- `?raw=true` format should work but needs testing

### Next Steps:
1. **Test this URL in browser:**
   ```
   https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards/avon-old-farms_home_left.webp?raw=true
   ```

2. **If it works, update Lovable** with this helper function:
   ```javascript
   const CARD_BASE_URL = 'https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards';

   function getTeamCardUrl(teamId, isHome) {
     const variant = isHome ? 'home_left' : 'away_right';
     return `${CARD_BASE_URL}/${teamId}_${variant}.webp?raw=true`;
   }
   ```

3. **If URLs still don't work**, alternatives:
   - Use Google Cloud Storage (you have GCP set up)
   - Use Cloudflare R2 (free)
   - Check if GitHub needs more time for CDN propagation

---

## Lovable Project

### Full Prompt Location:
The complete Lovable prompt was provided in the conversation. Key sections:
- Design system (colors, fonts, effects)
- Component specifications (header, game selector, matchup, players)
- API integration details
- Trading card helper function

### Assets to Upload to Lovable:
1. `ace-and-scouty.png` from `NEPSAC Logos/`
2. Trading cards now hosted on GitHub (no upload needed)

---

## Quick Resume Commands

```bash
# Navigate to project
cd "C:\Users\phili\OneDrive\Documents\GitHub\append-extra-points\bigquery"

# Check git status
git status

# Test if images are accessible (open in browser)
start https://github.com/PFUNKTHEO2/append-extra-points/blob/main/bigquery/nepsac-cards/avon-old-farms_home_left.webp?raw=true

# Browse all trading cards on GitHub
start https://github.com/PFUNKTHEO2/append-extra-points/tree/main/bigquery/nepsac-cards
```

---

## Contacts/References

- **Lovable:** https://lovable.dev (your project should be saved there)
- **GitHub Repo:** https://github.com/PFUNKTHEO2/append-extra-points
- **GCP Project:** prodigy-ranking
- **Integration Plan:** `bigquery/NEPSAC_DYNAMIC_INTEGRATION_PLAN.md`

---

*Session ended: January 21, 2026 ~12:30 AM*

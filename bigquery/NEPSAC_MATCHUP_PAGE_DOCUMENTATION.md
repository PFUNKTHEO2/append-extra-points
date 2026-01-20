# NEPSAC GameDay Matchup Page - Technical Documentation

## Overview

A standalone, EA Sports-style matchup visualization page for NEPSAC (New England Preparatory School Athletic Council) hockey games. The page displays head-to-head team comparisons, player cards with ratings, game predictions, and interactive game selection.

**Live Preview:** `nepsac_matchup_page.html`
**Suggested Route for Loveable:** `/nepsac-game-day`

---

## Features

### 1. Game Selector
- Grid of clickable game cards for all games on a given date
- Shows team names, rankings, records, time, and venue
- Prediction confidence percentage badge on each card
- Active game highlighted with pink glow

### 2. Team Comparison Section
- Side-by-side team display with logos
- Team overall rating (70-99 scale, EA Sports style)
- Win-Loss-Tie record
- NEPSAC ranking badge
- Division display

### 3. ProdigyPrediction Slider
- Visual tug-of-war style indicator
- Animated marker slides toward favored team
- Percentage displayed on glowing green marker
- Team names below with favored team highlighted

### 4. Head-to-Head Stats Comparison
- Animated comparison bars for:
  - Average Points
  - Top Player Points
  - Roster Size
  - Total Points
- Cyan (away) vs Pink (home) color coding

### 5. GameDay ProdigyPicks (Player Cards)
- Top 6 players per team sorted by ProdigyPoints
- Player photos from EliteProspects (with initials fallback)
- Overall rating (OVR) in EA Sports style (70-99)
- Rating tier styling: Gold (90+), Silver (80-89), Bronze (70-79)
- Position badges (F=Red, D=Blue, G=Green)
- Point totals displayed

### 6. Branding
- Ace & Scouty mascot image at top (transparent background)
- ProdigyChain color scheme (pink/purple/cyan gradients)
- Orbitron + Rajdhani fonts
- Glassmorphism panels with blur effects

---

## File Structure

```
bigquery/
├── generate_nepsac_matchup_page.py    # Main generator script
├── nepsac_matchup_page.html           # Generated output (standalone)
├── nepsac_logos.json                  # Team name → logo path mapping
├── nepsac_school_logos/               # School logo images
│   ├── Ace_Scouty_transparent.png     # Mascot image (transparent)
│   └── [58 school logos]
├── nepsac_roster_matches.csv          # Player data with team assignments
├── nepsac_team_rankings_full.csv      # Team aggregate stats
├── nepsac_schedule_jan19.csv          # Game schedule with predictions
├── nepsac_week_jan19.json             # Standings data (W-L-T records)
└── hockey_players_LATEST_SYNC.csv     # Player images (image_url column)
```

---

## Data Sources

### 1. Team Rankings (`nepsac_team_rankings_full.csv`)
```csv
rank,team,roster_size,matched,match_rate,avg_points,total_points,max_points
1,Avon Old Farms,27,24,88.9%,2929.45,70306.88,4122.31
```

### 2. Player Roster (`nepsac_roster_matches.csv`)
```csv
roster_name,roster_team,roster_position,roster_grad_year,db_player_id,total_points
John Smith,Avon Old Farms,F,2026,123456,3500.25
```

### 3. Schedule (`nepsac_schedule_jan19.csv`)
```csv
date,away,home,time,venue,predicted_winner,confidence
2026-01-21,Vermont Academy,Williston-Northampton,2:30 PM,"Easthampton, MA",Williston-Northampton,70
```

### 4. Standings (`nepsac_week_jan19.json`)
```json
{
  "standings": [
    {"team": "Avon Old Farms", "wins": 10, "losses": 2, "ties": 1, "win_pct": 0.808}
  ]
}
```

### 5. Player Images (`hockey_players_LATEST_SYNC.csv`)
- Column: `image_url`
- Source: EliteProspects
- Example: `https://files.eliteprospects.com/layout/players/xxxxx.jpg`
- ~70% of players have photos

### 6. Team Logos (`nepsac_logos.json`)
```json
{
  "Avon Old Farms": "nepsac_school_logos/avon_old_farms_logo.png",
  "Andover": "https://cdn.example.com/andover.jpg"
}
```

---

## How to Regenerate the Page

```bash
cd bigquery
python generate_nepsac_matchup_page.py
```

**Output:**
- Creates `nepsac_matchup_page.html`
- Embeds all data as JSON (no external API calls needed)
- Page works offline once generated

---

## Rating Conversion Formulas

### Player OVR (Overall Rating)
```javascript
// Convert ProdigyPoints to 70-99 scale
OVR = 70 + (playerPoints / maxPoints) * 29
// Clamped to range [70, 99]
```

### Team OVR
```javascript
// Based on average points
const minAvg = 750;
const maxAvg = 2950;
const normalized = (avgPoints - minAvg) / (maxAvg - minAvg);
OVR = 70 + normalized * 29;
// Clamped to range [70, 99]
```

### Rating Tiers
| OVR Range | Tier | Card Border Color |
|-----------|------|-------------------|
| 90-99 | Gold | #FFD700 with glow |
| 80-89 | Silver | #C0C0C0 |
| 70-79 | Bronze | #CD7F32 |

---

## Key JavaScript Functions

```javascript
// Convert points to OVR rating
convertToOVR(points)

// Calculate team overall from avg points
calculateTeamOVR(avgPoints)

// Get rating tier class (gold/silver/bronze)
getRatingTier(ovr)

// Render team logo with initials fallback
renderCrest(team, fallbackName)

// Create player photo with image or initials
createPlayerPhoto(player)

// Create full player card HTML
createPlayerCard(player, index)

// Load a matchup when game is selected
loadMatchup(game)

// Animate stat comparison bars
animateStatBars(awayVal, homeVal, awayBarId, homeBarId)
```

---

## Styling / CSS Classes

### Key Classes
- `.glass-panel` - Glassmorphism container with blur
- `.team-crest` - Team logo container (140x140px)
- `.player-card` - Individual player card
- `.player-card.gold/.silver/.bronze` - Rating tier styling
- `.prediction-marker` - Animated prediction indicator
- `.stat-bar` - Animated comparison bar

### Color Variables
```css
--bg-dark: #0a0a0f;
--accent-pink: #d946ef;
--accent-purple: #8b5cf6;
--accent-cyan: #06b6d4;
--accent-green: #22c55e;
--gold: #ffd700;
--silver: #c0c0c0;
--bronze: #cd7f32;
```

---

## Adding New Games / Updating Schedule

1. Update `nepsac_schedule_jan19.csv` with new games
2. Ensure team names match exactly with `nepsac_team_rankings_full.csv`
3. Run `python generate_nepsac_matchup_page.py`

### Schedule CSV Format
```csv
date,away,home,time,venue,predicted_winner,confidence
2026-01-22,Team A,Team B,5:00 PM,Arena Name,Team B,65
```

---

## Adding New Team Logos

1. Add logo file to `nepsac_school_logos/` folder
2. Update `nepsac_logos.json`:
```json
{
  "Team Name": "nepsac_school_logos/filename.png"
}
```
Or use external URL:
```json
{
  "Team Name": "https://cdn.example.com/logo.png"
}
```

---

## Loveable Integration Guide

### Option 1: Embed as iframe
```jsx
<iframe
  src="/static/nepsac_matchup_page.html"
  width="100%"
  height="800px"
  frameBorder="0"
/>
```

### Option 2: Convert to React Component

The page data is already in JSON format. Key data to extract:

```javascript
// From the generated HTML
const TEAMS_DATA = { /* 58 teams */ };
const GAMES = [ /* 28 games */ ];
const MAX_POINTS = 5458.58;
```

**React component structure:**
```jsx
// components/NepsacGameDay.jsx
import { useState } from 'react';

export function NepsacGameDay({ teamsData, games, maxPoints }) {
  const [selectedGame, setSelectedGame] = useState(0);

  return (
    <div className="nepsac-container">
      <GameSelector games={games} onSelect={setSelectedGame} />
      <TeamComparison game={games[selectedGame]} teams={teamsData} />
      <PredictionSlider game={games[selectedGame]} />
      <StatsComparison game={games[selectedGame]} teams={teamsData} />
      <PlayerCards game={games[selectedGame]} teams={teamsData} />
    </div>
  );
}
```

### Required Assets for Loveable
1. `Ace_Scouty_transparent.png` - Mascot image
2. Team logos (58 files) or use CDN URLs
3. Fonts: Orbitron, Rajdhani (Google Fonts)

---

## Known Issues / Notes

1. **Team Name Matching**: Team names must match exactly between schedule, rankings, and roster files. Common mismatches:
   - "Williston-Northampton" (with hyphen)
   - "BB&N" vs "Buckingham Browne & Nichols"
   - "NMH" vs "Northfield Mount Hermon"

2. **Player Images**: ~30% of players don't have EliteProspects photos. The page falls back to initials with gradient background.

3. **Logo Paths**: Mix of local paths and external URLs. External URLs (CloudFront, S3) are used for some schools where local files had issues.

4. **Date Display**: Currently hardcoded to "WEDNESDAY, JANUARY 21, 2026". Update in generator for different dates.

---

## Future Enhancements

- [ ] Dynamic date selection
- [ ] Live score updates during games
- [ ] Historical matchup data
- [ ] Player comparison popup on card click
- [ ] Mobile-optimized layout improvements
- [ ] API endpoint for real-time data instead of embedded JSON

---

## Contact / Support

Generated by the ProdigyChain data team.
For questions about the data or implementation, reference this documentation.

---

*Last Updated: January 19, 2026*

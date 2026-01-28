# NEPSAC GameDay - React Implementation Prompt for Lovable

## Overview

Build a NEPSAC prep school hockey GameDay application with a carousel-based game selector, animated team matchup cards, prediction displays, and ProdigyChain-style trading cards for players.

## Design System

### Color Palette
```
--bg-dark: #0a0a0f
--bg-card: rgba(15, 15, 25, 0.8)
--glass-bg: rgba(255, 255, 255, 0.03)
--glass-border: rgba(255, 255, 255, 0.08)
--accent-purple: #8b5cf6
--accent-pink: #d946ef
--accent-cyan: #00AAFF
--accent-gold: #f59e0b
--text-primary: #ffffff
--text-secondary: rgba(255, 255, 255, 0.7)
--text-muted: rgba(255, 255, 255, 0.5)
```

### Typography
- Headers: Bold, white
- Body: System font stack
- Numbers/Stats: Tabular numerals

## Navigation (Shared with Past Performance)

The app has two main pages accessible via tab navigation:

| Route | Page | Description |
|-------|------|-------------|
| `/` or `/gameday` | GameDay | Predictions for upcoming games |
| `/past-performance` | Past Performance | Historical results & accuracy |

**Tab buttons in header:**
- "GAMEDAY" - active when on predictions page
- "PAST PERFORMANCE" - active when viewing results

Both pages share a common Layout component with the Ace & Scouty logo and tab navigation.

---

## Page Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  [Ace & Scouty Logo]    ACE & SCOUTY                            │
│         [GAMEDAY]  [PAST PERFORMANCE]   ← Tab Navigation        │
├─────────────────────────────────────────────────────────────────┤
│         ◀ Jan 20  [JAN 21 - 27 GAMES]  Jan 22 ▶                │
├─────────────────────────────────────────────────────────────────┤
│  ◀◀ PREV   [ AVON OLD FARMS  vs  NMH • 4:30 PM ]   NEXT ▶▶     │
│                      Game 3 of 27                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────┐              ⚔️              ┌──────────┐        │
│   │  [LOGO]  │              VS              │  [LOGO]  │        │
│   │   AVON   │                              │   NMH    │        │
│   │    89    │         PREDICTION           │    76    │        │
│   │  10-1-0  │     ════●══════════════      │  5-6-1   │        │
│   │  #3 MHR  │         AVON 70%             │ #58 MHR  │        │
│   └──────────┘                              └──────────┘        │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  [▼ Stats Comparison]  (collapsible)                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Goals/Game:  3.2 ████████░░░░ 1.8                      │    │
│  │  Goals Against: 1.2 ███░░░░░░░░░ 2.5                    │    │
│  │  Win %:        91% █████████░░░ 35%                     │    │
│  └─────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────┤
│  [▼ Top Players]  (collapsible)                                 │
│  ┌────────┐ ┌────────┐ ┌────────┐    ┌────────┐ ┌────────┐     │
│  │ 89 OVR │ │ 85 OVR │ │ 82 OVR │ vs │ 76 OVR │ │ 72 OVR │     │
│  │ Player │ │ Player │ │ Player │    │ Player │ │ Player │     │
│  │  Name  │ │  Name  │ │  Name  │    │  Name  │ │  Name  │     │
│  └────────┘ └────────┘ └────────┘    └────────┘ └────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### 1. DateNavigation
- Shows 5 date pills horizontally
- Selected date is highlighted with gradient background
- Each pill shows: day name, date, game count
- Arrow buttons on left/right to navigate dates
- Games count shown as badge

### 2. GameCarousel
- Large circular arrow buttons (◀◀ and ▶▶)
- Center strip showing current game:
  - Away team vs Home team
  - Game time and venue
  - Prediction badge (team name + percentage + confidence level)
- Counter below: "Game X of Y"
- Supports: keyboard arrows, mouse wheel scroll, touch swipe

### 3. TeamMatchup
- Two team cards side by side with VS badge in center
- **Animation**: Cards "fall in" when game changes
  - Away card slides from left with rotation
  - Home card slides from right with rotation (0.1s delay)
  - VS badge pulses on transition

**Team Card contains:**
- Team logo (150x150px)
- Team name
- Overall rating (large number)
- Record (W-L-T)
- MHR Rank (#X)
- Division badge

### 4. PredictionBar
- Horizontal bar showing win probability
- Gradient fill from away team color to home team color
- Marker/notch at prediction percentage
- Labels: team names and percentages on each end
- Confidence level badge (HIGH/MEDIUM/LOW)

### 5. StatsComparison (Collapsible)
- Toggle button with arrow icon
- Comparison bars for:
  - Goals Per Game
  - Goals Against
  - Win Percentage
  - Schedule Strength
- Each row: Away stat | visual bar | Home stat
- Bars animate on expand

### 6. PlayersSection (Collapsible)
- Two columns: Away team players | Home team players
- Header shows team name and player count
- Grid of PlayerCard components (3 per row)

### 7. PlayerCard (ProdigyChain Trading Card Style)

**Design:**
```css
/* Deep purple gradient background */
background: linear-gradient(180deg, #160033 0%, #0a0015 100%);

/* Glowing border */
border: 1px solid transparent;
background-clip: padding-box;
box-shadow:
  0 0 20px rgba(0, 170, 255, 0.3),
  inset 0 0 30px rgba(154, 77, 255, 0.1);

/* Corner decorations - circuit board style */
/* Each corner has L-shaped lines with hexagonal node */
```

**Card Layout:**
- Aspect ratio: 2.5:3.5 (trading card proportions)
- **Top-left**: OVR badge (large number with glow)
- **Center**: Player photo or initials placeholder
- **Bottom**: Info bar with:
  - Player name
  - Position badge (F=red, D=blue, G=green)
  - Points display

**Corner Decorations:**
- Each corner has circuit-board style L-shaped lines
- Small hexagonal node at corner intersection
- Cyan glow effect

**Tier-based styling:**
- Elite (90+): Cyan glow, cyan accents
- Gold (80-89): Gold glow, gold accents
- Silver (70-79): Silver glow
- Bronze (<70): Purple glow

**Hover effect:**
- Scanning line animation (diagonal line sweeps across)
- Slight scale up (1.02)
- Enhanced glow

## Animations

### Card Fall-In Animation
```css
@keyframes cardFallInFromLeft {
  0% {
    opacity: 0;
    transform: translateX(-100px) translateY(-50px) rotate(-8deg) scale(0.85);
  }
  60% {
    transform: translateX(10px) translateY(5px) rotate(2deg) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateX(0) translateY(0) rotate(0) scale(1);
  }
}

@keyframes cardFallInFromRight {
  0% {
    opacity: 0;
    transform: translateX(100px) translateY(-50px) rotate(8deg) scale(0.85);
  }
  60% {
    transform: translateX(-10px) translateY(5px) rotate(-2deg) scale(1.02);
  }
  100% {
    opacity: 1;
    transform: translateX(0) translateY(0) rotate(0) scale(1);
  }
}
```

### VS Pulse Animation
```css
@keyframes vsPulse {
  0%, 100% { transform: scale(1); filter: drop-shadow(0 0 10px rgba(139, 92, 246, 0.5)); }
  50% { transform: scale(1.15); filter: drop-shadow(0 0 25px rgba(217, 70, 239, 0.8)); }
}
```

### Scanning Line (for player cards on hover)
```css
@keyframes scanLine {
  0% { transform: translateX(-100%) translateY(-100%) rotate(45deg); }
  100% { transform: translateX(200%) translateY(200%) rotate(45deg); }
}
```

## Data Structures

### Team Data
```typescript
interface Team {
  name: string;
  rating: number;        // 0-100 overall rating
  rank: number;          // MHR ranking
  record: string;        // "10-1-0"
  wins: number;
  losses: number;
  ties: number;
  division: string;      // "Elite", "ISL", "Founders", etc.
  logo?: string;         // URL to logo image
  players: Player[];
}
```

### Player Data
```typescript
interface Player {
  name: string;
  position: string;      // "F", "D", "G", "F/D"
  points: number;        // Raw points for OVR calculation
  photo?: string;        // URL to player photo
  epId?: string;         // Elite Prospects ID
}
```

### Game Data
```typescript
interface Game {
  awayTeam: string;
  homeTeam: string;
  time: string;          // "4:30 PM"
  venue?: string;
  prediction: {
    winner: string;
    percentage: number;  // 0-100
    confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  };
}
```

### Schedule Data
```typescript
interface ScheduleByDate {
  [date: string]: Game[];  // "2026-01-21": [...]
}
```

## Key Interactions

1. **Date Selection**: Click date pill → load games for that date → select first game
2. **Game Navigation**:
   - Click arrows or use keyboard ←→
   - Mouse wheel on carousel
   - Touch swipe on mobile
   - Wraps around (last → first, first → last)
3. **Game Selection**: Triggers team card animations, updates all displays
4. **Collapsible Sections**: Click header to expand/collapse, save preference to localStorage

## API Integration

The app should fetch data from these endpoints (or use static JSON for demo):

```
GET /api/nepsac/schedule?date=2026-01-21
GET /api/nepsac/teams
GET /api/nepsac/predictions?date=2026-01-21
GET /api/nepsac/players?team=avon-old-farms
```

For player photos, use Elite Prospects:
```
https://files.eliteprospects.com/layout/players/{epId}.jpg
```

## Mobile Responsiveness

- Stack team cards vertically on screens < 768px
- Larger touch targets for carousel arrows
- Swipe gestures for game navigation
- Collapsible sections default to collapsed on mobile
- Player cards: 2 per row on tablet, 1 per row on mobile

## Glass Morphism Styling

All panels use glass morphism effect:
```css
.glass-panel {
  background: rgba(255, 255, 255, 0.03);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
```

## File Structure Suggestion

```
src/
├── components/
│   ├── DateNavigation.tsx
│   ├── GameCarousel.tsx
│   ├── TeamMatchup.tsx
│   ├── TeamCard.tsx
│   ├── PredictionBar.tsx
│   ├── StatsComparison.tsx
│   ├── PlayersSection.tsx
│   ├── PlayerCard.tsx
│   └── CollapsibleSection.tsx
├── hooks/
│   ├── useGameNavigation.ts
│   ├── useKeyboardNav.ts
│   └── useSwipeGesture.ts
├── data/
│   ├── teams.ts
│   ├── schedule.ts
│   └── predictions.ts
├── styles/
│   ├── globals.css
│   ├── animations.css
│   └── trading-card.css
├── types/
│   └── index.ts
└── pages/
    └── GameDay.tsx
```

## Implementation Priority

1. **Phase 1**: Static layout with team matchup display
2. **Phase 2**: Game carousel with navigation
3. **Phase 3**: Animations (card fall-in, VS pulse)
4. **Phase 4**: Collapsible sections
5. **Phase 5**: Player trading cards
6. **Phase 6**: API integration
7. **Phase 7**: Mobile optimization

## Reference

The original implementation is at:
https://pfunktheo2.github.io/append-extra-points/bigquery/nepsac_matchup_page.html

Use this as the visual reference for exact styling and behavior.

---

## Appendix: Complete Trading Card CSS

Copy this CSS exactly for the ProdigyChain trading card design:

```css
/* ========================================
   PRODIGYCHAIN TRADING CARD DESIGN
   ======================================== */

.player-card {
    --card-cyan: #00AAFF;
    --card-purple: #9A4DFF;
    --card-pink: #FF1493;
    --card-bg-dark: #160033;
    --card-bg-darker: #0a0015;

    position: relative;
    background: linear-gradient(180deg, var(--card-bg-dark) 0%, var(--card-bg-darker) 100%);
    border-radius: 16px;
    padding: 0;
    text-align: center;
    overflow: hidden;
    cursor: pointer;
    transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.4s ease;
    aspect-ratio: 2.5 / 3.5;
    min-height: 220px;
}

/* Hexagonal honeycomb background pattern */
.player-card::before {
    content: '';
    position: absolute;
    inset: 0;
    background-image:
        radial-gradient(circle at 25% 25%, rgba(154, 77, 255, 0.1) 0%, transparent 50%),
        radial-gradient(circle at 75% 75%, rgba(0, 170, 255, 0.1) 0%, transparent 50%);
    background-size: 100% 100%;
    opacity: 0.8;
    z-index: 0;
}

/* Circuit board side borders */
.player-card::after {
    content: '';
    position: absolute;
    inset: 0;
    border: 2px solid transparent;
    border-radius: 16px;
    background: linear-gradient(180deg, var(--card-cyan), var(--card-purple), var(--card-cyan)) border-box;
    -webkit-mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
    mask: linear-gradient(#fff 0 0) padding-box, linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    z-index: 10;
    pointer-events: none;
}

.player-card:hover {
    transform: translateY(-8px) scale(1.05);
    box-shadow:
        0 20px 50px rgba(0, 170, 255, 0.3),
        0 0 30px rgba(154, 77, 255, 0.4),
        inset 0 0 20px rgba(0, 170, 255, 0.1);
}

/* Corner decorations */
.player-card .corner {
    position: absolute;
    width: 30px;
    height: 30px;
    z-index: 11;
    pointer-events: none;
}

.player-card .corner::before,
.player-card .corner::after {
    content: '';
    position: absolute;
    background: var(--card-cyan);
    box-shadow: 0 0 8px var(--card-cyan), 0 0 15px var(--card-purple);
}

.player-card .corner-tl { top: 8px; left: 8px; }
.player-card .corner-tr { top: 8px; right: 8px; }
.player-card .corner-bl { bottom: 8px; left: 8px; }
.player-card .corner-br { bottom: 8px; right: 8px; }

.player-card .corner-tl::before { width: 15px; height: 2px; top: 0; left: 0; }
.player-card .corner-tl::after { width: 2px; height: 15px; top: 0; left: 0; }
.player-card .corner-tr::before { width: 15px; height: 2px; top: 0; right: 0; }
.player-card .corner-tr::after { width: 2px; height: 15px; top: 0; right: 0; }
.player-card .corner-bl::before { width: 15px; height: 2px; bottom: 0; left: 0; }
.player-card .corner-bl::after { width: 2px; height: 15px; bottom: 0; left: 0; }
.player-card .corner-br::before { width: 15px; height: 2px; bottom: 0; right: 0; }
.player-card .corner-br::after { width: 2px; height: 15px; bottom: 0; right: 0; }

/* Hexagon node accents on corners */
.player-card .corner-node {
    position: absolute;
    width: 8px;
    height: 8px;
    background: var(--card-purple);
    clip-path: polygon(50% 0%, 100% 25%, 100% 75%, 50% 100%, 0% 75%, 0% 25%);
    box-shadow: 0 0 10px var(--card-purple);
    z-index: 12;
}

.player-card .corner-tl .corner-node { top: -2px; left: -2px; }
.player-card .corner-tr .corner-node { top: -2px; right: -2px; }
.player-card .corner-bl .corner-node { bottom: -2px; left: -2px; }
.player-card .corner-br .corner-node { bottom: -2px; right: -2px; }

/* Card content wrapper */
.player-card-content {
    position: relative;
    z-index: 5;
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 12px 10px 10px;
}

/* OVR Rating - Top left badge */
.player-ovr {
    position: absolute;
    top: 10px;
    left: 10px;
    font-family: 'Orbitron', sans-serif;
    font-size: 1.4rem;
    font-weight: 900;
    z-index: 15;
    padding: 4px 8px;
    background: rgba(0, 0, 0, 0.7);
    border-radius: 8px;
    border: 1px solid;
    text-shadow: 0 0 10px currentColor;
}

.player-card.gold .player-ovr {
    color: #ffd700;
    border-color: #ffd700;
    box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
}

.player-card.silver .player-ovr {
    color: #c0c0c0;
    border-color: #c0c0c0;
    box-shadow: 0 0 12px rgba(192, 192, 192, 0.4);
}

.player-card.bronze .player-ovr {
    color: #cd7f32;
    border-color: #cd7f32;
    box-shadow: 0 0 10px rgba(205, 127, 50, 0.4);
}

/* Tier glow effects */
.player-card.gold {
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.4), inset 0 0 30px rgba(255, 215, 0, 0.1);
}

.player-card.gold::after {
    background: linear-gradient(180deg, #ffd700, #b8860b, #ffd700) border-box;
}

.player-card.silver {
    box-shadow: 0 0 20px rgba(192, 192, 192, 0.3), inset 0 0 25px rgba(192, 192, 192, 0.1);
}

.player-card.silver::after {
    background: linear-gradient(180deg, #c0c0c0, #808080, #c0c0c0) border-box;
}

.player-card.bronze {
    box-shadow: 0 0 15px rgba(205, 127, 50, 0.3), inset 0 0 20px rgba(205, 127, 50, 0.1);
}

.player-card.bronze::after {
    background: linear-gradient(180deg, #cd7f32, #8b4513, #cd7f32) border-box;
}

/* Player photo - Large and prominent */
.player-photo {
    flex: 1;
    width: 100%;
    min-height: 100px;
    margin: 0 0 8px 0;
    background: linear-gradient(135deg, rgba(154, 77, 255, 0.3), rgba(0, 170, 255, 0.3));
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
    position: relative;
}

.player-photo::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(180deg, transparent 60%, rgba(0, 0, 0, 0.8) 100%);
    z-index: 1;
    pointer-events: none;
}

.player-photo img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    object-position: top center;
}

.player-photo .initials {
    font-family: 'Orbitron', sans-serif;
    font-size: 2.5rem;
    font-weight: 900;
    color: white;
    text-shadow: 0 0 20px var(--card-cyan), 0 4px 8px rgba(0, 0, 0, 0.5);
    background: linear-gradient(135deg, var(--card-cyan), var(--card-purple));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

/* Player info bar - Bottom of card */
.player-info-bar {
    background: linear-gradient(90deg, rgba(0, 170, 255, 0.15), rgba(154, 77, 255, 0.15));
    border-top: 1px solid rgba(0, 170, 255, 0.3);
    padding: 8px 6px;
    border-radius: 0 0 12px 12px;
    margin: 0 -10px -10px;
}

.player-name {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.75rem;
    font-weight: 700;
    margin-bottom: 6px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    color: #fff;
    text-shadow: 0 0 10px rgba(0, 170, 255, 0.5);
    letter-spacing: 0.5px;
}

.player-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 6px;
}

.player-position {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 3px 10px;
    border-radius: 4px;
    font-family: 'Orbitron', sans-serif;
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1px;
    border: 1px solid;
}

.player-position.F {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.3), rgba(220, 38, 38, 0.3));
    border-color: #ef4444;
    color: #ef4444;
    text-shadow: 0 0 8px #ef4444;
}

.player-position.D {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.3), rgba(37, 99, 235, 0.3));
    border-color: #3b82f6;
    color: #3b82f6;
    text-shadow: 0 0 8px #3b82f6;
}

.player-position.G {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.3), rgba(22, 163, 74, 0.3));
    border-color: #22c55e;
    color: #22c55e;
    text-shadow: 0 0 8px #22c55e;
}

.player-points {
    font-family: 'Orbitron', sans-serif;
    font-size: 0.6rem;
    font-weight: 600;
    color: #00AAFF;
    text-shadow: 0 0 8px #00AAFF;
    letter-spacing: 0.5px;
}

.player-points-label {
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.5rem;
}

/* Scanning line animation on hover */
.player-card:hover .player-photo::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--card-cyan), transparent);
    animation: scanLine 1.5s ease-in-out infinite;
    z-index: 2;
}

@keyframes scanLine {
    0% { top: 0; opacity: 0; }
    50% { opacity: 1; }
    100% { top: 100%; opacity: 0; }
}

/* Glowing pulse on gold cards */
.player-card.gold::before {
    animation: goldPulse 2s ease-in-out infinite;
}

@keyframes goldPulse {
    0%, 100% { opacity: 0.8; }
    50% { opacity: 1; }
}
```

## PlayerCard React Component

```tsx
interface PlayerCardProps {
  player: {
    name: string;
    position: string;
    points: number;
    photo?: string;
    epId?: string;
  };
  index: number;
}

function PlayerCard({ player, index }: PlayerCardProps) {
  // Convert points to OVR (60-99 scale)
  const ovr = Math.min(99, Math.max(60, Math.round(60 + (player.points / 50000) * 39)));

  // Determine tier
  const tier = ovr >= 90 ? 'gold' : ovr >= 80 ? 'silver' : 'bronze';

  // Get position class
  const positionClass = player.position.split('/')[0].trim();

  // Format points
  const formattedPoints = Math.round(player.points).toLocaleString();

  // Get initials for fallback
  const initials = player.name.split(' ').map(n => n[0]).join('').slice(0, 2);

  // Photo URL
  const photoUrl = player.epId
    ? `https://files.eliteprospects.com/layout/players/${player.epId}.jpg`
    : null;

  return (
    <div
      className={`player-card ${tier}`}
      style={{ animationDelay: `${index * 0.1}s` }}
    >
      {/* Corner decorations */}
      <div className="corner corner-tl"><div className="corner-node" /></div>
      <div className="corner corner-tr"><div className="corner-node" /></div>
      <div className="corner corner-bl"><div className="corner-node" /></div>
      <div className="corner corner-br"><div className="corner-node" /></div>

      {/* OVR Badge */}
      <div className="player-ovr">{ovr}</div>

      {/* Card content */}
      <div className="player-card-content">
        <div className="player-photo">
          {photoUrl ? (
            <img
              src={photoUrl}
              alt={player.name}
              onError={(e) => {
                e.currentTarget.style.display = 'none';
                e.currentTarget.nextElementSibling?.classList.remove('hidden');
              }}
            />
          ) : null}
          <span className={`initials ${photoUrl ? 'hidden' : ''}`}>{initials}</span>
        </div>

        <div className="player-info-bar">
          <div className="player-name">{player.name}</div>
          <div className="player-meta">
            <div className={`player-position ${positionClass}`}>
              {player.position}
            </div>
            <div className="player-points">
              <span>{formattedPoints}</span>
              <span className="player-points-label"> PTS</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
```

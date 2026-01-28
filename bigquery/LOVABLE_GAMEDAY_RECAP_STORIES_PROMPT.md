# LOVABLE PROMPT: NEPSAC GameDay Recap Instagram Stories Generator

## Overview

Build an Instagram Stories generator for NEPSAC GameDay recaps that creates a series of 9:16 vertical story frames showcasing daily game results, prediction accuracy, top performers, and key storylines. The stories should be shareable, visually striking, and incorporate existing ProdigyChain player cards and team logos.

---

## Design System (MUST FOLLOW EXACTLY)

### Color Palette
```css
--bg-dark: #0a0a0f
--bg-card: rgba(15, 15, 25, 0.95)
--glass-bg: rgba(255, 255, 255, 0.03)
--glass-border: rgba(255, 255, 255, 0.08)
--accent-purple: #8b5cf6
--accent-pink: #d946ef
--accent-cyan: #00AAFF
--accent-gold: #ffd700
--accent-green: #22c55e
--accent-red: #ef4444
--text-primary: #ffffff
--text-secondary: rgba(255, 255, 255, 0.7)
--text-muted: rgba(255, 255, 255, 0.5)
```

### Typography
```css
/* Headers */
font-family: 'Orbitron', sans-serif;
font-weight: 900;

/* Body */
font-family: 'Rajdhani', sans-serif;
font-weight: 600;

/* Stats/Numbers */
font-family: 'Orbitron', monospace;
font-variant-numeric: tabular-nums;
```

### Character Personas (Ace & Scouty)

**SCOUTY** (The Algorithm)
- Color: #00D4FF (cyan)
- Icon: Robot/AI icon
- Voice: Data-driven, confident, analytical
- Quote style: "The data never lies."

**ACE** (The Insider)
- Color: #FF4444 (red)
- Icon: Playing card/spade
- Voice: Cynical, insider knowledge, personality-driven
- Quote style: "My sources told me..."

---

## Story Sequence (8-10 Stories)

### Story 1: THE HOOK (Opening)
**Duration:** 5 seconds
**Purpose:** Grab attention, show big number

**Layout:**
```
┌─────────────────────────────────┐
│                                 │
│     [Ace & Scouty Logo]         │
│                                 │
│    ━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                 │
│         GAMEDAY RECAP           │
│      ═══════════════════        │
│                                 │
│    ┌─────────────────────┐      │
│    │                     │      │
│    │   [LARGE NUMBER]    │      │
│    │       16            │      │
│    │      GAMES          │      │
│    │                     │      │
│    └─────────────────────┘      │
│                                 │
│      JANUARY 24, 2026           │
│                                 │
│     TAP TO SEE RESULTS →        │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Pulsing glow animation on game count
- Date in gradient text (pink → purple)
- Subtle ice texture overlay
- Swipe indicator at bottom

---

### Story 2: PREDICTION SCOREBOARD
**Duration:** 8 seconds
**Purpose:** Show model accuracy

**Layout:**
```
┌─────────────────────────────────┐
│      MODEL PERFORMANCE          │
│    ════════════════════════     │
│                                 │
│   ┌───────────┬───────────┐     │
│   │  CORRECT  │   WRONG   │     │
│   │    ✓      │     ✗     │     │
│   │   12      │     2     │     │
│   └───────────┴───────────┘     │
│                                 │
│   ┌─────────────────────────┐   │
│   │    ACCURACY: 85.7%      │   │
│   │  ████████████████░░░░   │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │  + 2 TIES (no pick)     │   │
│   └─────────────────────────┘   │
│                                 │
│   SEASON: 29-12-3 (70.7%)       │
│                                 │
│        [Scouty Avatar]          │
│   "Another winning day."        │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Animated counter for correct/wrong
- Progress bar fills with green gradient
- Scouty quote bubble with cyan glow
- Pulsing checkmark animations

---

### Story 3: UPSET OF THE DAY
**Duration:** 10 seconds
**Purpose:** Highlight biggest surprise result

**Layout:**
```
┌─────────────────────────────────┐
│      🚨 UPSET ALERT 🚨          │
│                                 │
│   ┌─────────────────────────┐   │
│   │     [WINNER LOGO]       │   │
│   │        TAFT             │   │
│   │       (4-9-0)           │   │
│   │                         │   │
│   │    ══════════════       │   │
│   │         4               │   │
│   │    ══════════════       │   │
│   │                         │   │
│   │    [LOSER LOGO]         │   │
│   │     CANTERBURY          │   │
│   │      (11-4-2)           │   │
│   │         1               │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │  MODEL PICKED: Canterbury│   │
│   │  CONFIDENCE: 72% (-257)  │   │
│   └─────────────────────────┘   │
│                                 │
│        [Ace Avatar]             │
│   "Any given Saturday..."       │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Red/orange alert border animation
- Underdog team highlighted in gold
- Loser team in muted colors
- Ace quote with red glow

---

### Story 4: BLOWOUTS CAROUSEL
**Duration:** 12 seconds (auto-advance through 4 games)
**Purpose:** Show dominant performances

**Layout:**
```
┌─────────────────────────────────┐
│       💥 BLOWOUTS 💥            │
│        (1 of 4)                 │
│                                 │
│   ┌─────────────────────────┐   │
│   │                         │   │
│   │   [WINNER TEAM CARD]    │   │
│   │      WINCHENDON         │   │
│   │         9               │   │
│   │                         │   │
│   │   ──────────────────    │   │
│   │                         │   │
│   │   [LOSER TEAM CARD]     │   │
│   │      KENTS HILL         │   │
│   │         1               │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│   MARGIN: +8 GOALS              │
│   SHOTS: 50-17                  │
│                                 │
│   ● ○ ○ ○  ← Progress dots      │
│                                 │
└─────────────────────────────────┘
```

**Games to show:**
1. Winchendon 9-1 Kents Hill (+8)
2. Deerfield 8-2 Choate (+6)
3. Andover 6-2 Nobles (+4)
4. Williston 6-1 NMH (+5)

**Elements:**
- Team cards with logos (use NepsacTeamCard component style)
- Auto-advancing carousel
- Progress dots at bottom
- Winner card has gold glow

---

### Story 5: TOP PERFORMERS (Star Players)
**Duration:** 15 seconds
**Purpose:** Highlight best individual performances

**Layout:**
```
┌─────────────────────────────────┐
│        ⭐ STARS OF THE DAY ⭐    │
│                                 │
│   ┌────────┬────────┬────────┐  │
│   │[PLAYER]│[PLAYER]│[PLAYER]│  │
│   │ CARD 1 │ CARD 2 │ CARD 3 │  │
│   │        │        │        │  │
│   │ Small  │ Alvarez│Needham │  │
│   │ 2G-1A  │ 2G-1A  │ 2G-1A  │  │
│   └────────┴────────┴────────┘  │
│                                 │
│   ┌────────┬────────┬────────┐  │
│   │[PLAYER]│[PLAYER]│[PLAYER]│  │
│   │ CARD 4 │ CARD 5 │ CARD 6 │  │
│   │        │        │        │  │
│   │Burlock │ Patton │Carolan │  │
│   │  2G    │  2G    │  2G    │  │
│   └────────┴────────┴────────┘  │
│                                 │
│   [Tap any card to see profile] │
│                                 │
└─────────────────────────────────┘
```

**Player Cards (ProdigyChain Trading Card Style):**
```css
/* Use exact trading card CSS from LOVABLE_NEPSAC_GAMEDAY_PROMPT.md */
.player-card {
    background: linear-gradient(180deg, #160033 0%, #0a0015 100%);
    border: 2px solid transparent;
    background-clip: padding-box;
    box-shadow: 0 0 20px rgba(0, 170, 255, 0.3);
    aspect-ratio: 2.5 / 3.5;
}
```

**Elements:**
- 6 mini player cards in 2x3 grid
- Each card shows: photo/initials, name, game stats
- OVR badge in corner
- Position badge (F=red, D=blue, G=green)
- Staggered entrance animation
- Cards glow on tap

---

### Story 6: SHUTOUT SPOTLIGHT
**Duration:** 8 seconds
**Purpose:** Celebrate goaltender performances

**Layout:**
```
┌─────────────────────────────────┐
│      🧱 BRICK WALLS 🧱          │
│         SHUTOUTS                │
│                                 │
│   ┌─────────────────────────┐   │
│   │    [GOALIE CARD]        │   │
│   │                         │   │
│   │   BLAKE TRUCHON         │   │
│   │     ST. PAUL'S          │   │
│   │                         │   │
│   │   ┌───────────────┐     │   │
│   │   │  20 SAVES     │     │   │
│   │   │  SHUTOUT      │     │   │
│   │   └───────────────┘     │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │    [GOALIE CARD]        │   │
│   │  TORRES / ROSENFELD     │   │
│   │      RIVERS             │   │
│   │   COMBINED SHUTOUT      │   │
│   │     24 SAVES            │   │
│   └─────────────────────────┘   │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Goalie cards with green position badge
- Save count prominently displayed
- "SHUTOUT" badge with gold glow
- Ice wall texture background effect

---

### Story 7: TIES (Goalie Battles)
**Duration:** 8 seconds
**Purpose:** Show competitive draws

**Layout:**
```
┌─────────────────────────────────┐
│       🤝 TOO CLOSE TO CALL      │
│            2 TIES               │
│                                 │
│   ┌─────────────────────────┐   │
│   │ BERKSHIRE  1 - 1  AVON  │   │
│   │ [LOGO]     ═══    [LOGO]│   │
│   │                         │   │
│   │ Phillipps    Noonan     │   │
│   │  30/31       25/26      │   │
│   │  .968%       .962%      │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │ ROXBURY  2 - 2  PORTSMOUTH│  │
│   │ LATIN    ═══    ABBEY   │   │
│   │ [LOGO]          [LOGO]  │   │
│   │                         │   │
│   │ Theo Lee: 2 goals       │   │
│   │ (not enough)            │   │
│   └─────────────────────────┘   │
│                                 │
│   No prediction = No pick       │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Split card design (50/50)
- Both team logos visible
- Goalie stats comparison
- Neutral gray/silver color scheme

---

### Story 8: FULL SCOREBOARD (Scrollable Grid)
**Duration:** User-controlled
**Purpose:** Complete results reference

**Layout:**
```
┌─────────────────────────────────┐
│     📊 ALL RESULTS 📊           │
│      January 24, 2026           │
│                                 │
│   ┌─────────────────────────┐   │
│   │ ✓ Salisbury    6-2 Kent │   │
│   │ ✓ Winchendon  9-1 K.Hill│   │
│   │ ✓ Groton     5-2 Midsx  │   │
│   │ ✓ KUA        5-3 Cushing│   │
│   │ ✓ Hotchkiss  5-1 Exeter │   │
│   │ ✓ Rivers     4-0 BB&N   │   │
│   │ ✓ Belm.Hill  4-2 Tabor  │   │
│   │ ✓ Deerfield  8-2 Choate │   │
│   │ ✓ Williston  6-1 NMH    │   │
│   │ ✓ St.Paul's  5-0 Vt.Acad│   │
│   │ ✓ Andover    6-2 Nobles │   │
│   │ ✓ Tilton     3-2 Proctor│   │
│   │ ✗ Taft       4-1 Cantbry│   │
│   │ ✓ St.Seb's   3-1 Gov's  │   │
│   │ ═ Berkshire  1-1 Avon   │   │
│   │ ═ Rox.Latin  2-2 Ports. │   │
│   └─────────────────────────┘   │
│                                 │
│   ✓ Correct  ✗ Wrong  ═ Tie    │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Scrollable list within frame
- Color-coded results (green ✓, red ✗, gray ═)
- Winner team name bolded
- Compact but readable

---

### Story 9: ACE & SCOUTY COMMENTARY
**Duration:** 10 seconds
**Purpose:** Entertaining recap, personality

**Layout:**
```
┌─────────────────────────────────┐
│                                 │
│   ┌─────────────────────────┐   │
│   │   [SCOUTY AVATAR]       │   │
│   │                         │   │
│   │  "85.7% on the day.     │   │
│   │   The model sees        │   │
│   │   patterns humans       │   │
│   │   can't detect.         │   │
│   │   Taft was noise."      │   │
│   │                         │   │
│   └─────────────────────────┘   │
│           ↕                     │
│   ┌─────────────────────────┐   │
│   │   [ACE AVATAR]          │   │
│   │                         │   │
│   │  "Noise? Canterbury     │   │
│   │   was 11-4-2! My        │   │
│   │   sources said their    │   │
│   │   goalie was off.       │   │
│   │   Should've listened."  │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│   Follow @ProdigyChain for      │
│   tomorrow's predictions        │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Speech bubbles with character colors
- Avatars with glow effects
- Back-and-forth dialogue format
- CTA at bottom

---

### Story 10: CTA + TOMORROW'S PREVIEW
**Duration:** 8 seconds
**Purpose:** Drive engagement, tease next day

**Layout:**
```
┌─────────────────────────────────┐
│                                 │
│      [Ace & Scouty Logo]        │
│                                 │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━     │
│                                 │
│     TOMORROW: JANUARY 25        │
│                                 │
│   ┌─────────────────────────┐   │
│   │                         │   │
│   │      12 GAMES           │   │
│   │    PREDICTIONS READY    │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │  🔥 FEATURED MATCHUP 🔥 │   │
│   │                         │   │
│   │  [TEAM]  vs  [TEAM]     │   │
│   │                         │   │
│   └─────────────────────────┘   │
│                                 │
│   ┌─────────────────────────┐   │
│   │    SEE PREDICTIONS      │   │
│   │  theprodigychain.com    │   │
│   └─────────────────────────┘   │
│                                 │
│   SWIPE UP ↑                    │
│                                 │
└─────────────────────────────────┘
```

**Elements:**
- Animated "SWIPE UP" indicator
- Tomorrow's game count
- Featured matchup tease
- Link sticker to website

---

## Component Specifications

### Team Card (Stories Version)
```typescript
interface StoryTeamCard {
  teamId: string;
  name: string;
  logo: string;         // URL from GitHub repo
  record: string;       // "10-5-2"
  score?: number;       // Game score if result
  isWinner?: boolean;   // Gold glow if true
  isLoser?: boolean;    // Muted if true
}
```

**Sizing for Stories:**
- Full width: 280px x 120px
- Grid item: 140px x 100px
- Mini: 80px x 60px

### Player Card (Stories Version)
```typescript
interface StoryPlayerCard {
  name: string;
  team: string;
  position: 'F' | 'D' | 'G';
  ovr: number;
  imageUrl?: string;
  gameStats: {
    goals?: number;
    assists?: number;
    saves?: number;
    shutout?: boolean;
  };
}
```

**Sizing for Stories:**
- Featured: 180px x 250px
- Grid (2x3): 100px x 140px
- Mini: 60px x 85px

### Logo URLs
```typescript
// Base URL for team logos
const LOGO_BASE = 'https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards';

// Pattern: {team-slug}_logo.png
// Examples:
// salisbury-school_logo.png
// avon-old-farms_logo.png
// st-pauls-school_logo.png
```

---

## Animations

### Entry Animations
```css
/* Card fall-in from top */
@keyframes fallIn {
  0% {
    opacity: 0;
    transform: translateY(-50px) scale(0.8);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Score reveal */
@keyframes scoreReveal {
  0% {
    opacity: 0;
    transform: scale(0);
  }
  50% {
    transform: scale(1.2);
  }
  100% {
    opacity: 1;
    transform: scale(1);
  }
}

/* Checkmark pop */
@keyframes checkPop {
  0% {
    transform: scale(0) rotate(-45deg);
  }
  70% {
    transform: scale(1.3) rotate(10deg);
  }
  100% {
    transform: scale(1) rotate(0);
  }
}

/* Progress bar fill */
@keyframes fillBar {
  0% { width: 0%; }
  100% { width: var(--target-width); }
}

/* Pulsing glow */
@keyframes pulse {
  0%, 100% {
    box-shadow: 0 0 20px var(--glow-color);
  }
  50% {
    box-shadow: 0 0 40px var(--glow-color);
  }
}
```

### Stagger Delays
```css
/* For grid items */
.grid-item:nth-child(1) { animation-delay: 0.1s; }
.grid-item:nth-child(2) { animation-delay: 0.2s; }
.grid-item:nth-child(3) { animation-delay: 0.3s; }
/* ... etc */
```

---

## Data Input Format

The generator should accept this JSON structure:

```typescript
interface GameDayRecapData {
  date: string;                    // "2026-01-24"
  totalGames: number;

  predictions: {
    correct: number;
    wrong: number;
    ties: number;
    accuracy: number;             // 0-100
    seasonRecord: string;         // "29-12-3"
    seasonAccuracy: number;
  };

  games: Array<{
    gameId: string;
    awayTeam: TeamInfo;
    homeTeam: TeamInfo;
    awayScore: number;
    homeScore: number;
    predictedWinner: string;      // team_id
    predictionConfidence: number;
    predictionConfidenceOdds: string;  // American odds: "-150" or "+200"
    predictionCorrect: boolean | null;  // null for ties
    isTie: boolean;
    isUpset: boolean;
    margin: number;
  }>;

  topPerformers: Array<{
    player: PlayerInfo;
    gameStats: string;            // "2G-1A"
    team: string;
  }>;

  shutouts: Array<{
    goalie: string;
    team: string;
    saves: number;
    isShared?: boolean;
  }>;

  upsetOfDay?: {
    game: GameInfo;
    underdog: TeamInfo;
    favorite: TeamInfo;
    modelConfidence: number;
    modelConfidenceOdds: string;  // American odds: "-245" for heavy favorite upset
  };

  blowouts: Array<{
    game: GameInfo;
    margin: number;
  }>;

  tomorrowPreview?: {
    gameCount: number;
    featuredMatchup?: {
      away: string;
      home: string;
    };
  };
}

interface TeamInfo {
  teamId: string;
  name: string;
  shortName: string;
  logo: string;
  record: string;
  ovr?: number;
}

interface PlayerInfo {
  name: string;
  position: string;
  team: string;
  ovr: number;
  imageUrl?: string;
}
```

---

## Export Formats

### Static Images
- Format: PNG or WebP
- Dimensions: 1080x1920px (9:16)
- Quality: High (no compression artifacts)
- Include bleed area for Instagram cropping

### Animated Stories
- Format: MP4 or WebM
- Dimensions: 1080x1920px
- Duration: 5-15 seconds per story
- FPS: 30
- Audio: None (silent)

### Share Package
Generate a ZIP containing:
```
gameday_recap_2026-01-24/
├── story_01_hook.png
├── story_02_scoreboard.png
├── story_03_upset.png
├── story_04_blowouts.mp4
├── story_05_top_performers.png
├── story_06_shutouts.png
├── story_07_ties.png
├── story_08_full_results.png
├── story_09_commentary.png
├── story_10_cta.png
├── metadata.json
└── captions.txt
```

---

## Sample Data (January 24, 2026)

```json
{
  "date": "2026-01-24",
  "totalGames": 16,
  "predictions": {
    "correct": 12,
    "wrong": 2,
    "ties": 2,
    "accuracy": 85.7,
    "seasonRecord": "29-12-3",
    "seasonAccuracy": 70.7
  },
  "upsetOfDay": {
    "winner": "taft",
    "winnerName": "Taft",
    "winnerRecord": "4-9-0",
    "winnerScore": 4,
    "loser": "canterbury",
    "loserName": "Canterbury",
    "loserRecord": "11-4-2",
    "loserScore": 1,
    "modelPick": "canterbury",
    "modelConfidence": 72,
    "modelConfidenceOdds": "-257"
  },
  "blowouts": [
    { "winner": "Winchendon", "loser": "Kents Hill", "score": "9-1", "margin": 8 },
    { "winner": "Deerfield", "loser": "Choate", "score": "8-2", "margin": 6 },
    { "winner": "Williston", "loser": "NMH", "score": "6-1", "margin": 5 },
    { "winner": "Andover", "loser": "Nobles", "score": "6-2", "margin": 4 }
  ],
  "topPerformers": [
    { "name": "Alex Small", "team": "Andover", "position": "F", "stats": "2G-1A" },
    { "name": "Matteo Alvarez", "team": "Deerfield", "position": "F", "stats": "2G-1A" },
    { "name": "Jameson Needham", "team": "St. Sebastian's", "position": "F", "stats": "2G-1A" },
    { "name": "Nate Burlock", "team": "Salisbury", "position": "F", "stats": "2G" },
    { "name": "Aidan Patton", "team": "Hotchkiss", "position": "F", "stats": "2G" },
    { "name": "Matthew Carolan", "team": "Belmont Hill", "position": "F", "stats": "2G" }
  ],
  "shutouts": [
    { "goalie": "Blake Truchon", "team": "St. Paul's", "saves": 20, "shared": false },
    { "goalie": "Torres/Rosenfeld", "team": "Rivers", "saves": 24, "shared": true }
  ],
  "ties": [
    { "away": "Berkshire", "home": "Avon Old Farms", "score": "1-1" },
    { "away": "Roxbury Latin", "home": "Portsmouth Abbey", "score": "2-2" }
  ]
}
```

---

## Implementation Checklist

### Phase 1: Core Layout
- [ ] Story frame container (1080x1920)
- [ ] Header component with logo
- [ ] Typography setup (Orbitron, Rajdhani)
- [ ] Color system variables

### Phase 2: Story Templates
- [ ] Hook story (game count)
- [ ] Scoreboard story (accuracy)
- [ ] Upset story (alert style)
- [ ] Blowouts carousel
- [ ] Top performers grid
- [ ] Shutouts spotlight
- [ ] Ties display
- [ ] Full results list
- [ ] Commentary bubbles
- [ ] CTA story

### Phase 3: Components
- [ ] StoryTeamCard (3 sizes)
- [ ] StoryPlayerCard (3 sizes)
- [ ] ResultRow (with icon)
- [ ] ProgressBar (animated)
- [ ] CharacterBubble (Ace/Scouty)
- [ ] ScoreDisplay (animated reveal)

### Phase 4: Animations
- [ ] Entry animations (fall-in, scale)
- [ ] Progress bar fill
- [ ] Checkmark pop
- [ ] Carousel auto-advance
- [ ] Pulsing glows

### Phase 5: Export
- [ ] PNG export function
- [ ] MP4 export for animated stories
- [ ] ZIP package generator
- [ ] Caption text generator

---

## Admin UI Integration

Add a new section to `/admin/stories`:

```
┌─────────────────────────────────────────────────────────────┐
│  NEPSAC GAMEDAY STORIES                                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Select Date: [  January 24, 2026  ▼]                      │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  PREVIEW                                            │   │
│  │                                                     │   │
│  │  [Story 1] [Story 2] [Story 3] ... [Story 10]      │   │
│  │                                                     │   │
│  │  ◄                    ●                        ►    │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Story Count: 10                                            │
│  Total Duration: ~90 seconds                                │
│                                                             │
│  [Generate Stories]  [Download ZIP]  [Copy to Clipboard]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Success Metrics

- Stories should be visually consistent with existing ProdigyChain brand
- Load time < 2 seconds for preview
- Export time < 30 seconds for full package
- All text readable at Instagram compression
- Works on mobile admin interface

---

*This prompt creates a complete Instagram Stories workflow for NEPSAC GameDay recaps, incorporating the existing visual design system, player cards, team logos, and Ace & Scouty personalities.*

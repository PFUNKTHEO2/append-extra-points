# Instagram Stories Generator for NEPSAC GameDay

## Overview

Create an admin page at `/admin/stories` that generates Instagram Story images (1080x1920px) from our NEPSAC prediction data. This tool lets us quickly create shareable social media content showcasing our prediction accuracy and game previews.

---

## Instagram Story Specifications

- **Dimensions:** 1080 x 1920 pixels (9:16 aspect ratio)
- **Safe Zone:** Keep important content between Y: 250px and Y: 1670px (avoid top/bottom 250px)
- **Format:** Export as PNG
- **Style:** Dark theme matching our GameDay page, bold typography, high contrast

---

## Page Structure

### Route: `/admin/stories`

This should be a protected/hidden admin page (not in main navigation).

### Layout:
```
┌────────────────────────────────────────────────────────────────────┐
│  SOCIAL MEDIA GENERATOR                              [Admin Nav]   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────┐    ┌────────────────────────────────┐    │
│  │ CONTROLS            │    │ PREVIEW                        │    │
│  │                     │    │                                │    │
│  │ Story Type:         │    │  ┌────────────────────────┐   │    │
│  │ [Recap ▼]           │    │  │                        │   │    │
│  │                     │    │  │   1080 x 1920          │   │    │
│  │ Date:               │    │  │   Story Preview        │   │    │
│  │ [Jan 23, 2026]      │    │  │   (scaled to fit)      │   │    │
│  │                     │    │  │                        │   │    │
│  │ Game (for preview): │    │  │                        │   │    │
│  │ [Berkshire @ Kent]  │    │  │                        │   │    │
│  │                     │    │  │                        │   │    │
│  │ [Generate]          │    │  │                        │   │    │
│  │ [Download PNG]      │    │  └────────────────────────┘   │    │
│  │ [Download All]      │    │                                │    │
│  └─────────────────────┘    └────────────────────────────────┘    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Story Templates

### 1. Daily Recap Story

Shows results from a completed game day.

```tsx
// Component: DailyRecapStory
// Data needed: date, correct count, incorrect count, accuracy, list of games with results

<div className="story-container" style={{ width: 1080, height: 1920, background: 'linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%)' }}>
  {/* Header - Brand */}
  <div className="pt-[280px] text-center">
    <img src="/ace-scouty-logo.png" className="w-32 mx-auto" />
    <h1 className="text-[64px] font-black text-white tracking-wider">NEPSAC PICKS</h1>
  </div>

  {/* Date */}
  <div className="mt-8 text-center">
    <p className="text-[36px] text-purple-400 font-bold tracking-[8px]">JANUARY 23, 2026</p>
  </div>

  {/* Big Stats */}
  <div className="mt-16 text-center">
    <p className="text-[180px] font-black text-white leading-none">8/11</p>
    <p className="text-[48px] text-emerald-400 font-bold tracking-wider">CORRECT</p>
  </div>

  {/* Accuracy */}
  <div className="mt-8 text-center">
    <p className="text-[96px] font-black text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">72.7%</p>
    <p className="text-[32px] text-white/60 tracking-[4px]">ACCURACY</p>
  </div>

  {/* Results List */}
  <div className="mt-12 px-16 space-y-4">
    {games.slice(0, 5).map(game => (
      <div className="flex items-center justify-between text-[28px]">
        <span className={game.correct ? 'text-emerald-400' : 'text-red-400'}>
          {game.correct ? '✓' : '✗'}
        </span>
        <span className="text-white">{game.winner} def. {game.loser}</span>
        <span className="text-white/50">{game.score}</span>
      </div>
    ))}
  </div>

  {/* Footer CTA */}
  <div className="absolute bottom-[280px] left-0 right-0 text-center">
    <p className="text-[28px] text-white/60">Follow for daily predictions</p>
    <p className="text-[32px] text-purple-400 font-bold">@theprodigychain</p>
  </div>
</div>
```

### 2. Game Preview Story

Shows a single matchup prediction before the game.

```tsx
// Component: GamePreviewStory
// Data needed: awayTeam, homeTeam, prediction, confidence

<div className="story-container" style={{ width: 1080, height: 1920, background: 'linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%)' }}>
  {/* Header */}
  <div className="pt-[280px] text-center">
    <p className="text-[32px] text-purple-400 tracking-[8px]">NEPSAC GAMEDAY</p>
    <h1 className="text-[48px] font-black text-white mt-2">TODAY'S MATCHUP</h1>
  </div>

  {/* Away Team Card */}
  <div className="mt-12 flex flex-col items-center">
    <img
      src={getTeamCardUrl(awayTeam.teamId, false, 'left')}
      className="w-[400px] h-[400px] rounded-2xl shadow-2xl"
    />
    <p className="text-[36px] font-bold text-white mt-4">{awayTeam.shortName}</p>
    <p className="text-[28px] text-cyan-400">{awayTeam.ovr} OVR • {awayTeam.record}</p>
  </div>

  {/* VS */}
  <div className="my-8 text-center">
    <span className="text-[64px] font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-400">VS</span>
  </div>

  {/* Home Team Card */}
  <div className="flex flex-col items-center">
    <img
      src={getTeamCardUrl(homeTeam.teamId, true, 'left')}
      className="w-[400px] h-[400px] rounded-2xl shadow-2xl"
    />
    <p className="text-[36px] font-bold text-white mt-4">{homeTeam.shortName}</p>
    <p className="text-[28px] text-fuchsia-400">{homeTeam.ovr} OVR • {homeTeam.record}</p>
  </div>

  {/* Prediction */}
  <div className="mt-12 text-center">
    <p className="text-[28px] text-white/60 tracking-wider">OUR PICK</p>
    <p className="text-[56px] font-black text-emerald-400">{predictedWinner.shortName}</p>
    <p className="text-[36px] text-white/80">{confidence}% CONFIDENCE</p>
  </div>

  {/* Footer */}
  <div className="absolute bottom-[280px] left-0 right-0 text-center">
    <p className="text-[24px] text-white/40">Powered by ProdigyPoints AI</p>
  </div>
</div>
```

### 3. Season Stats Story

Shows overall season performance.

```tsx
// Component: SeasonStatsStory
// Data needed: overall stats from nepsac_overall_stats table

<div className="story-container" style={{ width: 1080, height: 1920, background: 'linear-gradient(180deg, #0a0a1a 0%, #1a1a2e 100%)' }}>
  {/* Header */}
  <div className="pt-[280px] text-center">
    <img src="/ace-scouty-logo.png" className="w-40 mx-auto" />
    <h1 className="text-[56px] font-black text-white mt-4">SEASON STATS</h1>
    <p className="text-[28px] text-purple-400 tracking-[4px]">2025-26 NEPSAC</p>
  </div>

  {/* Main Stat */}
  <div className="mt-20 text-center">
    <p className="text-[200px] font-black text-transparent bg-clip-text bg-gradient-to-b from-emerald-400 to-emerald-600 leading-none">
      {accuracy}%
    </p>
    <p className="text-[40px] text-white/80 tracking-wider">OVERALL ACCURACY</p>
  </div>

  {/* Stats Grid */}
  <div className="mt-16 flex justify-center gap-16">
    <div className="text-center">
      <p className="text-[96px] font-black text-emerald-400">{correct}</p>
      <p className="text-[28px] text-white/60">CORRECT</p>
    </div>
    <div className="text-center">
      <p className="text-[96px] font-black text-red-400">{incorrect}</p>
      <p className="text-[28px] text-white/60">MISSED</p>
    </div>
  </div>

  {/* Total Games */}
  <div className="mt-12 text-center">
    <p className="text-[48px] font-bold text-white">{total} PREDICTIONS</p>
  </div>

  {/* Streak or highlight */}
  <div className="mt-16 mx-16 p-8 bg-white/5 rounded-2xl border border-purple-500/30 text-center">
    <p className="text-[32px] text-purple-400">🔥 Current Streak: 5 Correct</p>
  </div>

  {/* Footer */}
  <div className="absolute bottom-[280px] left-0 right-0 text-center">
    <p className="text-[32px] text-white/60">Daily picks at</p>
    <p className="text-[40px] text-purple-400 font-bold">theprodigychain.com</p>
  </div>
</div>
```

---

## Data Fetching

Use the existing Supabase connection:

```typescript
// Fetch daily results
const { data: games } = await supabase
  .from('nepsac_games')
  .select(`
    *,
    away_team:nepsac_teams!away_team_id(team_name, short_name),
    home_team:nepsac_teams!home_team_id(team_name, short_name)
  `)
  .eq('game_date', selectedDate)
  .eq('status', 'final');

// Fetch overall stats
const { data: stats } = await supabase
  .from('nepsac_overall_stats')
  .select('*')
  .eq('season', '2025-26')
  .single();
```

---

## Export to PNG

Use `html-to-image` library to export the story as PNG:

```bash
npm install html-to-image
```

```typescript
import { toPng } from 'html-to-image';

const downloadStory = async () => {
  const element = document.getElementById('story-preview');
  if (!element) return;

  const dataUrl = await toPng(element, {
    width: 1080,
    height: 1920,
    pixelRatio: 1,
  });

  const link = document.createElement('a');
  link.download = `nepsac-story-${date}.png`;
  link.href = dataUrl;
  link.click();
};
```

---

## Color Palette

Use consistent colors matching the GameDay theme:

```css
--background: #0a0a1a;
--card-bg: #1a1a2e;
--purple-primary: #a855f7;
--pink-accent: #ec4899;
--cyan-away: #06b6d4;
--fuchsia-home: #d946ef;
--emerald-correct: #10b981;
--red-incorrect: #ef4444;
--text-primary: #ffffff;
--text-secondary: rgba(255, 255, 255, 0.6);
```

---

## Typography

Use bold, impactful fonts:

```css
font-family: 'Orbitron', sans-serif; /* For headers/numbers */
font-family: 'Rajdhani', sans-serif; /* For body text */
```

---

## Admin Navigation

Add link to stories generator in admin sidebar or header:

```tsx
<Link href="/admin/stories">
  <Button variant="ghost">
    <Instagram className="w-4 h-4 mr-2" />
    Story Generator
  </Button>
</Link>
```

---

## Summary

1. Create `/admin/stories` page
2. Add story type selector (Recap, Preview, Stats)
3. Add date picker and game selector
4. Render story at 1080x1920 in preview (scaled down to fit)
5. Use `html-to-image` to export as PNG
6. Match dark theme and branding from GameDay
7. Fetch data from Supabase (nepsac_games, nepsac_overall_stats)
8. Include team card images using `getTeamCardUrl()` from team-logos.ts

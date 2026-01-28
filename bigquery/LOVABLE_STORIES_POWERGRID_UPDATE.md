# Lovable: PowerGrid Integration for /gameday and /admin/stories

## CRITICAL UPDATE - MUTUALLY EXCLUSIVE PROBABILITIES

The PowerGrid API now returns **mutually exclusive tournament probabilities**:

- **Elite 8**: Top 8 teams overall make this tournament
- **Large School Tournament**: Large schools who MISSED Elite 8
- **Small School Tournament**: Small schools who MISSED Elite 8

**A team CANNOT be in both Elite 8 AND their division tournament!**

Example:
- Dexter #1: 99% Elite 8 bid → only 1% Large School bid
- Canterbury #9: 45% Elite 8 bid → 54% Small School bid

---

## APIs to Use

### 1. Power Rankings (for team rankings, OVR ratings)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26
```

### 2. PowerGrid (for tournament probabilities)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26
```

---

## 6 Probability Fields Per Team

```typescript
interface TeamProbabilities {
  elite8Bid: number;        // % chance to make Elite 8 (top 8 overall)
  elite8Champ: number;      // % chance to WIN Elite 8 (if they make it)
  largeSchoolBid: number;   // % chance for Large School tournament (if MISS Elite 8)
  largeSchoolChamp: number; // % chance to WIN Large School tournament
  smallSchoolBid: number;   // % chance for Small School tournament (if MISS Elite 8)
  smallSchoolChamp: number; // % chance to WIN Small School tournament
}
```

**Key insight**: `elite8Bid + largeSchoolBid` should roughly equal ~100% for Large schools (minus ties/edge cases).

---

## What to Add to Stories

### Game Preview Story - Add Tournament Stakes
When showing a matchup, include the teams' current tournament positioning:

```tsx
// Fetch both APIs
const [rankings, powergrid] = await Promise.all([
  fetch('...getNepsacPowerRankings?season=2025-26').then(r => r.json()),
  fetch('...getNepsacPowerGrid?season=2025-26').then(r => r.json())
]);

// Find team data
const awayTeamData = powergrid.teams.find(t => t.name.includes(awayTeam.name));
const homeTeamData = powergrid.teams.find(t => t.name.includes(homeTeam.name));

// Display in story
<div className="tournament-stakes">
  <p className="text-[24px] text-white/70">PLAYOFF PICTURE</p>

  {/* Away Team */}
  <div className="flex justify-between">
    <span>{awayTeam.shortName}</span>
    <span>#{awayTeamData.powerRank} • Elite 8: {awayTeamData.elite8Bid}%</span>
  </div>

  {/* Home Team */}
  <div className="flex justify-between">
    <span>{homeTeam.shortName}</span>
    <span>#{homeTeamData.powerRank} • Elite 8: {homeTeamData.elite8Bid}%</span>
  </div>
</div>
```

### Daily Recap Story - Add Playoff Impact
Show how results affected tournament odds:

```tsx
<div className="playoff-impact mt-8">
  <p className="text-[28px] text-purple-400">ELITE 8 PICTURE</p>

  {/* Current Elite 8 */}
  <div className="grid grid-cols-2 gap-2 mt-4">
    {powergrid.currentElite8.map((team, i) => (
      <div key={team.name} className="text-[20px]">
        <span className="text-white/50">#{i+1}</span>
        <span className="text-white ml-2">{team.name}</span>
        <span className="text-emerald-400 ml-2">{team.elite8Champ}%</span>
      </div>
    ))}
  </div>
</div>
```

### New Story Type: Tournament Race
Add a new story showing current tournament standings:

```tsx
// Story: Tournament Race
<div className="story-container" style={{ width: 1080, height: 1920, background: '#0a0a1a' }}>
  {/* Header */}
  <div className="pt-[280px] text-center">
    <h1 className="text-[56px] font-black text-white">TOURNAMENT RACE</h1>
    <p className="text-[28px] text-purple-400">Current Playoff Picture</p>
  </div>

  {/* Elite 8 Section */}
  <div className="mt-12 px-8">
    <p className="text-[32px] text-gold-400 font-bold">ELITE 8</p>
    <div className="mt-4 space-y-3">
      {powergrid.currentElite8.map((team, i) => (
        <div className="flex items-center justify-between bg-white/5 rounded-lg p-3">
          <div className="flex items-center gap-3">
            <span className="text-[24px] text-white/50 w-8">#{i+1}</span>
            <span className="text-[24px] text-white">{team.name}</span>
            <span className="text-[18px] text-white/50">({team.classification})</span>
          </div>
          <div className="text-right">
            <span className="text-[20px] text-emerald-400">{team.elite8Bid}%</span>
          </div>
        </div>
      ))}
    </div>
  </div>

  {/* Bubble Teams */}
  <div className="mt-8 px-8">
    <p className="text-[28px] text-orange-400 font-bold">ON THE BUBBLE</p>
    <div className="mt-4 grid grid-cols-2 gap-2">
      {powergrid.teams.slice(8, 12).map(team => (
        <div className="text-[20px] text-white/70">
          #{team.powerRank} {team.name} ({team.elite8Bid}%)
        </div>
      ))}
    </div>
  </div>

  {/* Footer */}
  <div className="absolute bottom-[280px] left-0 right-0 text-center">
    <p className="text-[24px] text-white/50">Updated after every game</p>
  </div>
</div>
```

---

## Key Data Points from PowerGrid

For each team, you have access to:

```typescript
interface TeamData {
  powerRank: number;      // Overall rank (1-55)
  name: string;
  classification: 'Large' | 'Small';
  ovr: number;            // Overall rating (0-99)
  record: { wins: number, losses: number, ties: number };

  // Tournament Probabilities (%)
  elite8Bid: number;      // Chance to make Elite 8
  elite8Champ: number;    // Chance to WIN Elite 8
  largeSchoolBid: number; // Chance to make Large School tourney
  largeSchoolChamp: number;
  smallSchoolBid: number; // Chance to make Small School tourney
  smallSchoolChamp: number;
}
```

---

## Current Rankings (VERIFY THESE)

Top 5 should be:
1. **Dexter** (Large)
2. **Avon Old Farms** (Large)
3. **Belmont Hill** (Large)
4. **Kimball Union** (Small)
5. **Tabor** (Large)

If the stories show different rankings, there's a data source issue.

---

## Implementation Checklist

- [ ] Add PowerGrid API fetch to stories generator
- [ ] Add Power Rankings API fetch for team data
- [ ] Update Game Preview Story with tournament stakes
- [ ] Update Daily Recap Story with playoff impact
- [ ] Add new "Tournament Race" story template
- [ ] Verify top 5 teams match expected rankings
- [ ] Show Elite 8 bid % on matchup previews
- [ ] Show championship odds for top teams

---

*This ensures social media content reflects our LIVE rankings and playoff probabilities.*

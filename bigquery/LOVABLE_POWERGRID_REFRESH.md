# Lovable: Refresh PowerGrid & Rankings Data

## IMMEDIATE ACTION REQUIRED

Update `/gameday` and `/admin/stories` to pull from the LIVE APIs with correct tournament logic.

---

## Data Source Locations

| Layer | Location |
|-------|----------|
| **API Endpoint** | `GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26` |
| **Database** | BigQuery `algorithm_core.nepsac_team_rankings` |
| **Frontend Transform** | `src/lib/nepsac-api.ts` → `fetchPowerGrid()` function |
| **React Hook** | `src/hooks/useNepsacApi.ts` → `usePowerGrid()` hook |

---

## API Endpoints

### Power Rankings
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26
```

### PowerGrid (Tournament Probabilities)
```
GET https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26
```

---

## CRITICAL: Mutually Exclusive Tournaments

The NEPSAC playoff has THREE separate tournaments. A team can only be in ONE:

| Tournament | Who Qualifies |
|------------|---------------|
| **Elite 8** | Top 8 teams overall (any classification) |
| **Large School** | Large schools who MISSED Elite 8 |
| **Small School** | Small schools who MISSED Elite 8 |

**If a team makes Elite 8, they do NOT play in Large/Small School tournament!**

---

## Current Top 10 Probabilities (VERIFY THESE)

| Rank | Team | Elite 8 Bid | Division Bid |
|------|------|-------------|--------------|
| #1 | Dexter (L) | 99% | 1% Large |
| #2 | Avon Old Farms (L) | 97% | 3% Large |
| #3 | Belmont Hill (L) | 95% | 5% Large |
| #4 | Kimball Union (S) | 93% | 7% Small |
| #5 | Tabor (L) | 90% | 10% Large |
| #6 | Salisbury (L) | 80% | 19% Large |
| #7 | St. Marks (S) | 70% | 29% Small |
| #8 | Hotchkiss (L) | 60% | 38% Large |
| #9 | Canterbury (S) | 45% | 54% Small |
| #10 | Thayer (L) | 35% | 64% Large |

**Notice**: Elite 8 + Division ≈ 100% (mutually exclusive)

---

## Response Fields Per Team

```typescript
{
  powerRank: number,        // Overall rank (1-55)
  name: string,
  classification: "Large" | "Small",
  ovr: number,              // 0-99 rating

  // MUTUALLY EXCLUSIVE PROBABILITIES
  elite8Bid: number,        // % chance for Elite 8
  elite8Champ: number,      // % chance to WIN Elite 8
  largeSchoolBid: number,   // % chance for Large tournament (if MISS Elite 8)
  largeSchoolChamp: number, // % chance to WIN Large tournament
  smallSchoolBid: number,   // % chance for Small tournament (if MISS Elite 8)
  smallSchoolChamp: number, // % chance to WIN Small tournament
}
```

---

## Display Logic for /gameday

### For teams ranked 1-8 (Elite 8 contenders):
Show Elite 8 probabilities prominently:
```
Dexter (#1) - 99% Elite 8 Bid | 12.6% Championship
```

### For teams ranked 9+ (Division contenders):
Show their division tournament probabilities:
```
Canterbury (#9, Small) - 54% Small School Bid | 5.2% Championship
Thayer (#10, Large) - 64% Large School Bid | 6.3% Championship
```

---

## Display Logic for /admin/stories

When generating social media stories:

1. **Game Preview**: Show each team's most likely tournament path
   - Top 8: "Elite 8 contender (99% bid)"
   - Others: "Large/Small School contender (64% bid)"

2. **Tournament Race Story**: Show current Elite 8 + bubble teams

3. **After Games**: Show how results affected tournament odds

---

## CRITICAL FIX: Use Flat Fields

The API returns probabilities as **flat fields at root level**, NOT nested under `probabilities`:

```typescript
// WRONG - Do NOT use nested probabilities object:
const elite8Bid = team.probabilities?.elite8Bid ?? 0;  // ❌

// CORRECT - Use flat fields directly:
const elite8Bid = team.elite8Bid ?? 0;  // ✅
const largeSchoolBid = team.largeSchoolBid ?? 0;  // ✅
```

---

## Fetch Code Example

```typescript
// Using the hook (recommended)
import { usePowerGrid } from '@/hooks/useNepsacApi';

const { data, loading, error } = usePowerGrid('2025-26');

// Or direct fetch
import { fetchPowerGrid, getMainTournament } from '@/lib/nepsac-api';

const powergrid = await fetchPowerGrid('2025-26');

// Display team's primary tournament path
powergrid.teams.forEach(team => {
  const tournament = getMainTournament(team);
  console.log(`${team.name}: ${tournament.bid}% ${tournament.name} bid`);
});
```

---

## Verification Checklist

After refresh, confirm:
- [ ] Rankings show: #1 Dexter, #2 Avon Old Farms, #3 Belmont Hill
- [ ] Dexter shows ~99% Elite 8, ~1% Large School (NOT both high!)
- [ ] Canterbury (#9) shows ~45% Elite 8, ~54% Small School
- [ ] Teams outside Elite 8 show higher division tournament %

---

*Last updated: 2026-01-27*
*Data source: BigQuery algorithm_core.nepsac_team_rankings*

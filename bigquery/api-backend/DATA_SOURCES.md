# API Data Sources - CRITICAL REFERENCE

> **READ THIS BEFORE MODIFYING ANY API FUNCTIONS**

This document defines the **single source of truth** for all data used in the API.
**DO NOT** create alternative calculations or rankings that override these sources.

---

## NEPSAC Rankings

### Source of Truth
```
Table: algorithm_core.nepsac_team_rankings
Field: rank
```

### Usage
```javascript
// CORRECT - Use the rank from the database
const teams = await executeQuery(`
  SELECT rank, team_name, ...
  FROM nepsac_team_rankings
  ORDER BY rank ASC
`);
teams.forEach(t => t.powerRank = t.rank); // Use DB rank

// WRONG - Do not recalculate rankings
teams.forEach(t => t.powerScore = calculateMyOwnScore(t));
teams.sort((a,b) => b.powerScore - a.powerScore); // NO!
teams.forEach((t,i) => t.powerRank = i + 1); // NO!
```

### API Endpoints Using This Data
- `getNepsacPowerRankings` - Returns official rankings
- `getNepsacPowerGrid` - Uses rankings for probability calculations

### Bug History
- **2026-01-27 (v2)**: PowerGrid was recalculating its own "powerScore" and
  re-sorting teams, producing different rankings than official. Fixed in v3.

---

## Player Rankings

### Source of Truth
```
Table: player_cumulative_points
View: v_ea_card_ratings
```

### Usage
Rankings come from the cumulative points system. Do not recalculate.

---

## School Classifications (Large/Small)

### Source of Truth
```
File: GameDay/NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf
```

### Rule
- **Large School**: Enrollment >= 225
- **Small School**: Enrollment < 225

### Implementation
Classifications are hardcoded in `powergrid.js` as `LARGE_SCHOOLS` and `SMALL_SCHOOLS`
objects. When adding new schools:
1. Check the PDF for official enrollment
2. Add to appropriate object
3. Include name variations

---

## Golden Rules

1. **Rankings come from the database** - Never recalculate or re-sort
2. **One source of truth per data type** - Document it here
3. **Comment your data sources** - Add notes in code about where data comes from
4. **Test against known values** - After changes, verify top teams match expectations

---

## Verification Commands

### Check NEPSAC Rankings
```bash
node -e "fetch('https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerRankings?season=2025-26&limit=10').then(r=>r.json()).then(d=>d.rankings.forEach((t,i)=>console.log('#'+(i+1)+' '+t.name)))"
```

Expected output (as of Jan 2026):
```
#1 Dexter
#2 Avon Old Farms
#3 Belmont Hill
...
```

### Check PowerGrid Uses Same Rankings
```bash
node -e "fetch('https://us-central1-prodigy-ranking.cloudfunctions.net/getNepsacPowerGrid?season=2025-26').then(r=>r.json()).then(d=>d.teams.slice(0,5).forEach(t=>console.log('#'+t.powerRank+' '+t.name)))"
```

Output should match the rankings above.

---

*Last updated: 2026-01-27*
*If you modify data sources, UPDATE THIS DOCUMENT*

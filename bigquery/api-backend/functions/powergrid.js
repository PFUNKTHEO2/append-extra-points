/**
 * Prodigy PowerGrid API v3
 *
 * ============================================================================
 * CRITICAL: DATA SOURCE DOCUMENTATION
 * ============================================================================
 *
 * This function uses the OFFICIAL NEPSAC Power Rankings from:
 *   - Table: algorithm_core.nepsac_team_rankings
 *   - Field: rank (this is the source of truth)
 *
 * DO NOT recalculate or re-sort rankings. The rank field from BigQuery
 * is computed by the established ranking algorithm and must be used as-is.
 *
 * Previous bug (v2): Function was recalculating its own "powerScore" and
 * re-sorting teams, which produced different rankings than the official ones.
 *
 * ============================================================================
 * NEPSAC PLAYOFF STRUCTURE
 * ============================================================================
 *
 * 1. ELITE 8: Top 8 teams OVERALL (Large + Small combined) get bids
 *    - These 8 teams compete for the Elite 8 Championship
 *    - Teams in Elite 8 do NOT play in division tournaments
 *
 * 2. LARGE SCHOOL TOURNAMENT: Large schools who MISSED Elite 8
 *    - Top 8 Large schools not in Elite 8 get bids
 *    - Compete for Large School Championship
 *
 * 3. SMALL SCHOOL TOURNAMENT: Small schools who MISSED Elite 8
 *    - Top 8 Small schools not in Elite 8 get bids
 *    - Compete for Small School Championship
 *
 * ============================================================================
 * 6 PROBABILITIES PER TEAM
 * ============================================================================
 *
 * 1. elite8Bid      - Chance of being top 8 overall
 * 2. elite8Champ    - Chance of winning Elite 8 Championship
 * 3. largeSchoolBid - Chance of making Large tournament (if missed Elite 8)
 * 4. largeSchoolChamp - Chance of winning Large School Championship
 * 5. smallSchoolBid - Chance of making Small tournament (if missed Elite 8)
 * 6. smallSchoolChamp - Chance of winning Small School Championship
 *
 * Note: A team will have values in EITHER Elite 8 columns OR their division
 * columns, since making Elite 8 means they don't play in division tournament.
 *
 * ============================================================================
 */

const functions = require('@google-cloud/functions-framework');
const cors = require('cors');
const { executeQuery } = require('./shared/bigquery');

const corsMiddleware = cors({ origin: true });

function withCors(handler) {
  return (req, res) => {
    corsMiddleware(req, res, () => handler(req, res));
  };
}

function errorResponse(res, statusCode, message) {
  return res.status(statusCode).json({
    error: message,
    timestamp: new Date().toISOString()
  });
}

// ============================================================================
// SCHOOL CLASSIFICATION DATA - DEFINITIVE LIST
// Source: NEPSAC Boys Ice Hockey Classification 2025-26
// Large School = enrollment >= 225 (28 schools)
// Small School = enrollment < 225 (29 schools)
//
// THIS IS THE OFFICIAL LIST. Only these 57 schools are in NEPSAC Boys Hockey.
// Teams not on this list (e.g., Hill School, Lawrenceville, Mount St. Charles,
// North Yarmouth) are NOT NEPSAC members and should be excluded from rankings.
// ============================================================================

const LARGE_SCHOOLS = {
  // 28 Large Schools (enrollment >= 225)
  'andover': 585, 'phillips andover': 585, 'phillips academy': 585,
  'exeter': 545, 'phillips exeter': 545,
  'brunswick': 440,
  'choate': 422, 'choate rosemary': 422,
  'avon': 401, 'avon old farms': 401,
  'milton': 357, 'milton academy': 357,
  'deerfield': 355, 'deerfield academy': 355,
  'loomis': 351, 'loomis chaffee': 351,
  'belmont hill': 350,
  'salisbury': 306, 'salisbury school': 306,
  'taft': 305, 'taft school': 305,
  'hotchkiss': 305, 'hotchkiss school': 305,
  'nmh': 304, 'northfield mount hermon': 304, 'northfield': 304,
  'st. sebastian': 285, 'st sebastian': 285, "st. sebastian's": 285,
  'bb&n': 280, 'buckingham': 280, 'buckingham browne': 280,
  'tabor': 279, 'tabor academy': 279,
  'thayer': 276, 'thayer academy': 276,
  'kent': 265, 'kent school': 265,
  'st. paul': 264, 'st paul': 264, "st. paul's": 264, "st paul's": 264,
  'austin prep': 257, 'austin preparatory': 257,
  'dexter': 257, 'dexter southfield': 257,
  'noble': 253, 'noble & greenough': 253, 'noble and greenough': 253,
  'williston': 245, 'williston northampton': 245, 'williston-northampton': 245,
  'trinity pawling': 240, 'trinity-pawling': 240,
  'worcester': 235, 'worcester academy': 235,
  'cushing': 226, 'cushing academy': 226,
  'westminster': 225, 'westminster school': 225,
  'lawrence': 225, 'lawrence academy': 225,
};

const SMALL_SCHOOLS = {
  // 29 Small Schools (enrollment < 225)
  'governor': 222, 'governors': 222, "governor's": 222, 'governors academy': 222,
  'middlesex': 221, 'middlesex school': 221,
  'roxbury latin': 218, 'roxbury': 218,
  'berkshire': 217, 'berkshire school': 217,
  'proctor': 212, 'proctor academy': 212,
  'rivers': 205, 'rivers school': 205,
  'kimball union': 199, 'kimball union academy': 199,
  'st. mark': 193, 'st mark': 193, 'st marks': 193, "st. mark's": 193, "st mark's": 193,
  'albany': 192, 'albany academy': 192,
  'st. george': 192, 'st george': 192, 'st georges': 192, "st. george's": 192,
  'brooks': 191, 'brooks school': 191,
  'groton': 189, 'groton school': 189,
  'new hampton': 187, 'new hampton school': 187,
  'brewster': 186, 'brewster academy': 186,
  'pomfret': 183, 'pomfret school': 183,
  'canterbury': 180, 'canterbury school': 180,
  'wma': 178, 'wilbraham': 178, 'wilbraham & monson': 178, 'wilbraham and monson': 178,
  'pingree': 177, 'pingree school': 177,
  'portsmouth abbey': 177,
  'winchendon': 170, 'winchendon school': 170,
  'frederick gunn': 170, 'gunnery': 170,
  'hoosac': 169, 'hoosac school': 169,
  'millbrook': 165, 'millbrook school': 165,
  'holderness': 164, 'holderness school': 164,
  'berwick': 143, 'berwick academy': 143,
  'vermont': 137, 'vermont academy': 137,
  'hebron': 117, 'hebron academy': 117,
  'kents hill': 110, 'kents hill school': 110,  // NOTE: Small school, NOT Large!
  'tilton': 99, 'tilton school': 99,
};

function classifySchool(teamName) {
  const nameLower = teamName.toLowerCase().trim();

  // Sort keys by length (longest first) to ensure "kents hill" matches before "kent"
  const largeKeys = Object.keys(LARGE_SCHOOLS).sort((a, b) => b.length - a.length);
  const smallKeys = Object.keys(SMALL_SCHOOLS).sort((a, b) => b.length - a.length);

  // Check SMALL schools first for specific cases like "Kents Hill"
  // (which would otherwise match "Kent" in Large)
  for (const key of smallKeys) {
    if (nameLower.includes(key) || key.includes(nameLower)) {
      return { classification: 'Small', enrollment: SMALL_SCHOOLS[key] };
    }
  }

  for (const key of largeKeys) {
    if (nameLower.includes(key) || key.includes(nameLower)) {
      return { classification: 'Large', enrollment: LARGE_SCHOOLS[key] };
    }
  }

  return { classification: 'Unknown', enrollment: 0 };
}

// ============================================================================
// PROBABILITY CALCULATIONS
// ============================================================================

/**
 * Calculate probability of making Elite 8 (top 8 overall)
 * Based on current power rank position
 */
function calculateElite8BidProb(powerRank, totalTeams) {
  if (powerRank <= 4) {
    // Top 4: Very likely to make it
    return Math.round((0.99 - (powerRank - 1) * 0.02) * 1000) / 10; // 99%, 97%, 95%, 93%
  } else if (powerRank <= 8) {
    // 5-8: Good chance, on the bubble
    return Math.round((0.90 - (powerRank - 5) * 0.10) * 1000) / 10; // 90%, 80%, 70%, 60%
  } else if (powerRank <= 12) {
    // 9-12: Bubble teams
    return Math.round((0.45 - (powerRank - 9) * 0.10) * 1000) / 10; // 45%, 35%, 25%, 15%
  } else if (powerRank <= 16) {
    // 13-16: Long shots
    return Math.round((0.10 - (powerRank - 13) * 0.02) * 1000) / 10; // 10%, 8%, 6%, 4%
  } else {
    // 17+: Very unlikely
    return Math.max(0.5, Math.round((0.03 - (powerRank - 17) * 0.005) * 1000) / 10);
  }
}

/**
 * Calculate probability of winning Elite 8 Championship
 * Uses softmax over OVR ratings of likely Elite 8 participants
 */
function calculateElite8ChampProb(team, allTeams) {
  // Only teams likely to make Elite 8 can win it
  const elite8Contenders = allTeams.filter(t => t.powerRank <= 12);

  if (team.powerRank > 12) {
    return 0.1; // Very small chance if not a contender
  }

  // Softmax based on OVR
  const ovrs = elite8Contenders.map(t => t.ovr);
  const expOvrs = ovrs.map(o => Math.exp(o / 10));
  const totalExp = expOvrs.reduce((a, b) => a + b, 0);
  const myExp = Math.exp(team.ovr / 10);

  const prob = (myExp / totalExp) * 100;
  return Math.round(Math.min(35, Math.max(0.1, prob)) * 10) / 10;
}

/**
 * Calculate probability of making Division tournament
 *
 * IMPORTANT: This is the FINAL probability which factors in:
 * 1. Probability of MISSING Elite 8 (must miss to play in division)
 * 2. Probability of making division tournament GIVEN they missed Elite 8
 *
 * Formula: P(division) = P(miss Elite 8) × P(make division | missed Elite 8)
 *
 * Example: Dexter (#1 overall, #1 Large)
 * - P(miss Elite 8) = 1% (they're almost certain to make Elite 8)
 * - P(make Large School | missed Elite 8) = 99% (they're best Large school)
 * - P(Large School tournament) = 1% × 99% = ~1%
 */
function calculateDivisionBidProb(team, sameClassTeams, allTeams, elite8BidProb) {
  // Probability of missing Elite 8
  const missElite8Prob = (100 - elite8BidProb) / 100;

  // If very likely to make Elite 8, very unlikely to be in division tournament
  if (missElite8Prob < 0.05) {
    // Less than 5% chance of missing Elite 8
    return Math.round(missElite8Prob * 99 * 10) / 10; // Near 0%
  }

  // Find this team's rank among teams of same classification
  const classRank = sameClassTeams.findIndex(t => t.teamId === team.teamId) + 1;

  // Calculate P(make division | missed Elite 8)
  // This depends on their class rank among teams who might miss Elite 8
  // Count how many same-class teams are ahead and likely to ALSO miss Elite 8

  let conditionalDivisionProb;

  // Teams outside current Elite 8 (powerRank > 8) have high conditional prob
  if (team.powerRank > 8) {
    // Already outside Elite 8, so conditional prob based on class rank among non-Elite-8
    const nonElite8ClassTeams = sameClassTeams.filter(t => t.powerRank > 8);
    const rankAmongNonElite8 = nonElite8ClassTeams.findIndex(t => t.teamId === team.teamId) + 1;

    if (rankAmongNonElite8 <= 4) {
      conditionalDivisionProb = 0.98 - (rankAmongNonElite8 - 1) * 0.03;
    } else if (rankAmongNonElite8 <= 8) {
      conditionalDivisionProb = 0.85 - (rankAmongNonElite8 - 5) * 0.08;
    } else if (rankAmongNonElite8 <= 12) {
      conditionalDivisionProb = 0.50 - (rankAmongNonElite8 - 9) * 0.10;
    } else {
      conditionalDivisionProb = Math.max(0.05, 0.15 - (rankAmongNonElite8 - 13) * 0.03);
    }
  } else {
    // Currently in Elite 8 range - if they miss, they'd be top of division
    // But probability of missing is already low, so this is a small slice
    conditionalDivisionProb = 0.95; // If they somehow miss Elite 8, they'd likely make division
  }

  // Final probability = P(miss Elite 8) × P(make division | missed)
  const finalProb = missElite8Prob * conditionalDivisionProb * 100;

  return Math.round(Math.max(0.1, Math.min(99, finalProb)) * 10) / 10;
}

/**
 * Calculate probability of winning Division Championship
 *
 * IMPORTANT: This is conditional on:
 * 1. Missing Elite 8
 * 2. Making the division tournament
 * 3. Winning the division tournament
 *
 * Formula: P(division champ) = P(miss Elite 8) × P(make division | missed) × P(win | in division)
 */
function calculateDivisionChampProb(team, sameClassTeams, elite8BidProb, divisionBidProb) {
  // If very low chance of being in division tournament, very low chance of winning it
  if (divisionBidProb < 1) {
    return 0.1;
  }

  // Find teams likely to be in the division tournament (those outside Elite 8 range)
  const divisionContenders = sameClassTeams.filter(t => t.powerRank > 8).slice(0, 12);

  if (divisionContenders.length === 0) {
    return 0.1;
  }

  // Check if this team is among division contenders
  const isContender = divisionContenders.some(t => t.teamId === team.teamId);

  if (!isContender) {
    // Team is in Elite 8 range - if they somehow end up in division, factor that in
    // Their championship prob is already reduced by low divisionBidProb
    const conditionalWinProb = 25; // If they somehow fall to division, they'd be favored
    return Math.round((divisionBidProb / 100) * conditionalWinProb * 10) / 10;
  }

  // Softmax based on OVR among division contenders
  const ovrs = divisionContenders.map(t => t.ovr);
  const expOvrs = ovrs.map(o => Math.exp(o / 10));
  const totalExp = expOvrs.reduce((a, b) => a + b, 0);
  const myExp = Math.exp(team.ovr / 10);

  // Conditional probability of winning given they're in the tournament
  const conditionalWinProb = (myExp / totalExp) * 100;

  // Scale by probability of being in the tournament
  const finalProb = (divisionBidProb / 100) * conditionalWinProb;

  return Math.round(Math.min(25, Math.max(0.1, finalProb)) * 10) / 10;
}

/**
 * GET /getNepsacPowerGrid
 * Returns PowerGrid with 6 probabilities per team
 *
 * IMPORTANT: Uses actual power rankings from nepsac_team_rankings.rank
 * DO NOT recalculate or re-sort rankings!
 */
functions.http('getNepsacPowerGrid', withCors(async (req, res) => {
  try {
    const { season = '2025-26' } = req.query;

    // Query teams ORDERED BY ACTUAL RANK (r.rank is source of truth)
    const query = `
      SELECT
        t.team_id,
        t.team_name,
        t.short_name,
        t.division,
        t.logo_url,
        r.rank,
        r.team_ovr,
        r.avg_prodigy_points,
        r.total_prodigy_points,
        r.max_prodigy_points,
        r.roster_size,
        r.matched_players,
        r.top_player_name,
        s.wins,
        s.losses,
        s.ties,
        s.win_pct,
        s.goals_for,
        s.goals_against,
        s.goal_differential,
        s.streak,
        s.games_played
      FROM \`prodigy-ranking.algorithm_core.nepsac_teams\` t
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` r
        ON t.team_id = r.team_id AND r.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_standings\` s
        ON t.team_id = s.team_id AND s.season = '${season}'
      WHERE r.rank IS NOT NULL
      ORDER BY r.rank ASC
      LIMIT 60
    `;

    const rows = await executeQuery(query);

    // Process teams - USE THE ACTUAL RANK FROM DATABASE
    const teams = rows.map(row => {
      const { classification, enrollment } = classifySchool(row.team_name);

      return {
        teamId: row.team_id,
        name: row.team_name,
        shortName: row.short_name,
        logoUrl: row.logo_url,
        division: row.division,
        classification,
        enrollment,
        // CRITICAL: Use actual rank from database, not recalculated
        powerRank: row.rank,
        ovr: row.team_ovr || 70,
        record: {
          wins: row.wins || 0,
          losses: row.losses || 0,
          ties: row.ties || 0,
          gamesPlayed: row.games_played || 0,
          winPct: Math.round((row.win_pct || 0) * 1000) / 10,
        },
        stats: {
          avgPoints: Math.round(row.avg_prodigy_points || 0),
          totalPoints: Math.round(row.total_prodigy_points || 0),
          maxPoints: Math.round(row.max_prodigy_points || 0),
          rosterSize: row.roster_size || 0,
          matchedPlayers: row.matched_players || 0,
          topPlayer: row.top_player_name,
        },
        performance: {
          goalsFor: row.goals_for || 0,
          goalsAgainst: row.goals_against || 0,
          goalDiff: row.goal_differential || 0,
          streak: row.streak || '-',
        },
      };
    });

    // Teams are already sorted by rank from the query
    // DO NOT re-sort!

    // Separate by classification (maintaining power rank order)
    const largeTeams = teams.filter(t => t.classification === 'Large');
    const smallTeams = teams.filter(t => t.classification === 'Small');

    // Assign class ranks (within classification, by power rank order)
    largeTeams.forEach((team, i) => { team.classRank = i + 1; });
    smallTeams.forEach((team, i) => { team.classRank = i + 1; });

    // Calculate all 6 probabilities for each team
    // IMPORTANT: Probabilities are MUTUALLY EXCLUSIVE
    // - Teams either make Elite 8 OR go to their division tournament
    // - Division tournament probs factor in probability of MISSING Elite 8
    teams.forEach(team => {
      // Elite 8 probabilities (available to all teams)
      team.elite8Bid = calculateElite8BidProb(team.powerRank, teams.length);
      team.elite8Champ = calculateElite8ChampProb(team, teams);

      // Division probabilities (depends on classification)
      // These are CONDITIONAL on missing Elite 8
      if (team.classification === 'Large') {
        team.largeSchoolBid = calculateDivisionBidProb(team, largeTeams, teams, team.elite8Bid);
        team.largeSchoolChamp = calculateDivisionChampProb(team, largeTeams, team.elite8Bid, team.largeSchoolBid);
        team.smallSchoolBid = 0;
        team.smallSchoolChamp = 0;
        team.divisionName = 'Large School';
      } else if (team.classification === 'Small') {
        team.smallSchoolBid = calculateDivisionBidProb(team, smallTeams, teams, team.elite8Bid);
        team.smallSchoolChamp = calculateDivisionChampProb(team, smallTeams, team.elite8Bid, team.smallSchoolBid);
        team.largeSchoolBid = 0;
        team.largeSchoolChamp = 0;
        team.divisionName = 'Small School';
      } else {
        team.largeSchoolBid = 0;
        team.largeSchoolChamp = 0;
        team.smallSchoolBid = 0;
        team.smallSchoolChamp = 0;
        team.divisionName = 'Unknown';
      }
    });

    // Identify current Elite 8 (top 8 by power rank)
    const currentElite8 = teams.slice(0, 8);
    const elite8Large = currentElite8.filter(t => t.classification === 'Large').length;
    const elite8Small = currentElite8.filter(t => t.classification === 'Small').length;

    // Large School Tournament contenders (Large teams outside Elite 8)
    const largeSchoolContenders = largeTeams.filter(t => t.powerRank > 8).slice(0, 12);

    // Small School Tournament contenders (Small teams outside Elite 8)
    const smallSchoolContenders = smallTeams.filter(t => t.powerRank > 8).slice(0, 12);

    // Build response
    res.json({
      season,
      generated: new Date().toISOString().split('T')[0],

      // Data source documentation
      _metadata: {
        dataSource: 'algorithm_core.nepsac_team_rankings',
        rankField: 'rank',
        note: 'Rankings are from official power rankings. DO NOT recalculate.',
        version: 'v3',
      },

      // All teams sorted by ACTUAL power rank
      teams: teams.map(t => ({
        powerRank: t.powerRank,
        classRank: t.classRank,
        teamId: t.teamId,
        name: t.name,
        shortName: t.shortName,
        logoUrl: t.logoUrl,
        classification: t.classification,
        divisionName: t.divisionName,
        enrollment: t.enrollment,
        ovr: t.ovr,
        record: t.record,
        // 6 probabilities - Elite 8 vs Division are MUTUALLY EXCLUSIVE
        // High elite8Bid means LOW division bid (and vice versa)
        elite8Bid: t.elite8Bid,
        elite8Champ: t.elite8Champ,
        largeSchoolBid: t.largeSchoolBid || 0,
        largeSchoolChamp: t.largeSchoolChamp || 0,
        smallSchoolBid: t.smallSchoolBid || 0,
        smallSchoolChamp: t.smallSchoolChamp || 0,
        // Legacy probabilities object for backwards compatibility
        probabilities: {
          makeElite8: t.elite8Bid,
          winElite8: t.elite8Champ,
          makeDivision: t.classification === 'Large' ? t.largeSchoolBid : t.smallSchoolBid,
          winDivision: t.classification === 'Large' ? t.largeSchoolChamp : t.smallSchoolChamp,
        },
      })),

      // Current Elite 8 snapshot
      currentElite8: currentElite8.map(t => ({
        powerRank: t.powerRank,
        teamId: t.teamId,
        name: t.name,
        shortName: t.shortName,
        logoUrl: t.logoUrl,
        classification: t.classification,
        ovr: t.ovr,
        record: t.record,
        elite8Bid: t.elite8Bid,
        elite8Champ: t.elite8Champ,
      })),

      // Large School Tournament contenders (teams who would play if they miss Elite 8)
      largeSchoolContenders: largeSchoolContenders.map(t => ({
        powerRank: t.powerRank,
        classRank: t.classRank,
        teamId: t.teamId,
        name: t.name,
        shortName: t.shortName,
        logoUrl: t.logoUrl,
        ovr: t.ovr,
        record: t.record,
        largeSchoolBid: t.largeSchoolBid,
        largeSchoolChamp: t.largeSchoolChamp,
      })),

      // Small School Tournament contenders
      smallSchoolContenders: smallSchoolContenders.map(t => ({
        powerRank: t.powerRank,
        classRank: t.classRank,
        teamId: t.teamId,
        name: t.name,
        shortName: t.shortName,
        logoUrl: t.logoUrl,
        ovr: t.ovr,
        record: t.record,
        smallSchoolBid: t.smallSchoolBid,
        smallSchoolChamp: t.smallSchoolChamp,
      })),

      // Bubble teams (ranks 7-12, could go either way)
      bubbleTeams: teams.slice(6, 12).map(t => ({
        powerRank: t.powerRank,
        teamId: t.teamId,
        name: t.name,
        classification: t.classification,
        ovr: t.ovr,
        record: t.record,
        elite8Bid: t.elite8Bid,
      })),

      summary: {
        totalTeams: teams.length,
        largeSchools: largeTeams.length,
        smallSchools: smallTeams.length,
        currentElite8Composition: {
          large: elite8Large,
          small: elite8Small,
        },
      },
    });

  } catch (error) {
    console.error('getNepsacPowerGrid error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

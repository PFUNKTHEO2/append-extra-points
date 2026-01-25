/**
 * NEPSAC API Endpoints - Cloud Functions
 * Endpoints for serving NEPSAC prep hockey data
 *
 * Endpoints:
 * - getNepsacSchedule: Get games for a specific date
 * - getNepsacMatchup: Get full matchup data for a game
 * - getNepsacTeams: Get all teams with rankings
 * - getNepsacStandings: Get current standings
 * - getNepsacRoster: Get team roster with player stats
 * - getNepsacGameDates: Get all dates with scheduled games
 */

const functions = require('@google-cloud/functions-framework');
const cors = require('cors');
const { executeQuery } = require('./shared/bigquery');

// Enable CORS for all functions
const corsMiddleware = cors({ origin: true });

/**
 * Helper function to wrap endpoints with CORS
 */
function withCors(handler) {
  return (req, res) => {
    corsMiddleware(req, res, () => handler(req, res));
  };
}

/**
 * Helper function for error responses
 */
function errorResponse(res, statusCode, message) {
  return res.status(statusCode).json({
    error: message,
    timestamp: new Date().toISOString()
  });
}

// Convert ProdigyPoints to EA Sports style OVR (70-99)
function calculateOVR(points, maxPoints) {
  if (!points || points <= 0) return 70;
  const normalized = Math.min(points / maxPoints, 1);
  return Math.round(70 + normalized * 29);
}

// Calculate team OVR from avg points
function calculateTeamOVR(avgPoints) {
  const minAvg = 750;
  const maxAvg = 2950;
  const normalized = Math.max(0, Math.min((avgPoints - minAvg) / (maxAvg - minAvg), 1));
  return Math.round(70 + normalized * 29);
}

// Parse BigQuery value (handles {value: x} objects)
function parseValue(val, defaultVal = 0) {
  if (val === null || val === undefined) return defaultVal;
  if (typeof val === 'object' && val.value !== undefined) return val.value;
  return val;
}

/**
 * GET /getNepsacSchedule
 * Returns all games for a specific date with team info and predictions
 *
 * Query params:
 * - date: YYYY-MM-DD (required)
 * - season: string (default: '2025-26')
 */
functions.http('getNepsacSchedule', withCors(async (req, res) => {
  try {
    const { date, season = '2025-26' } = req.query;

    if (!date) {
      return errorResponse(res, 400, 'date parameter is required (YYYY-MM-DD)');
    }

    const query = `
      SELECT
        s.game_id,
        s.game_date,
        s.game_time,
        s.day_of_week,
        s.venue,
        s.city,
        s.status,
        s.away_score,
        s.home_score,
        s.predicted_winner_id,
        s.prediction_confidence,
        s.away_team_id,
        away.team_name as away_team_name,
        away.short_name as away_short_name,
        away.logo_url as away_logo_url,
        away.division as away_division,
        away_rank.rank as away_rank,
        away_rank.avg_prodigy_points as away_avg_points,
        away_rank.team_ovr as away_ovr,
        away_st.wins as away_wins,
        away_st.losses as away_losses,
        away_st.ties as away_ties,
        s.home_team_id,
        home.team_name as home_team_name,
        home.short_name as home_short_name,
        home.logo_url as home_logo_url,
        home.division as home_division,
        home_rank.rank as home_rank,
        home_rank.avg_prodigy_points as home_avg_points,
        home_rank.team_ovr as home_ovr,
        home_st.wins as home_wins,
        home_st.losses as home_losses,
        home_st.ties as home_ties
      FROM \`prodigy-ranking.algorithm_core.nepsac_schedule\` s
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` away
        ON s.away_team_id = away.team_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` home
        ON s.home_team_id = home.team_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` away_rank
        ON s.away_team_id = away_rank.team_id AND away_rank.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` home_rank
        ON s.home_team_id = home_rank.team_id AND home_rank.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_standings\` away_st
        ON s.away_team_id = away_st.team_id AND away_st.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_standings\` home_st
        ON s.home_team_id = home_st.team_id AND home_st.season = '${season}'
      WHERE s.game_date = '${date}' AND s.season = '${season}'
      ORDER BY s.game_time
    `;

    const rows = await executeQuery(query);

    const games = rows.map(row => {
      // Check if both teams have ranking data - if not, don't show prediction
      const awayHasData = parseValue(row.away_avg_points, 0) > 0;
      const homeHasData = parseValue(row.home_avg_points, 0) > 0;
      const hasSufficientData = awayHasData && homeHasData;

      return {
        gameId: row.game_id,
        gameDate: parseValue(row.game_date),
        gameTime: row.game_time,
        dayOfWeek: row.day_of_week,
        venue: row.venue,
        city: row.city,
        status: row.status,
        score: row.status === 'final' ? {
          away: row.away_score,
          home: row.home_score
        } : null,
        awayTeam: {
          teamId: row.away_team_id,
          name: row.away_team_name,
          shortName: row.away_short_name,
          logoUrl: row.away_logo_url,
          division: row.away_division,
          rank: row.away_rank,
          ovr: row.away_ovr || calculateTeamOVR(parseValue(row.away_avg_points, 1500)),
          record: {
            wins: row.away_wins || 0,
            losses: row.away_losses || 0,
            ties: row.away_ties || 0
          }
        },
        homeTeam: {
          teamId: row.home_team_id,
          name: row.home_team_name,
          shortName: row.home_short_name,
          logoUrl: row.home_logo_url,
          division: row.home_division,
          rank: row.home_rank,
          ovr: row.home_ovr || calculateTeamOVR(parseValue(row.home_avg_points, 1500)),
          record: {
            wins: row.home_wins || 0,
            losses: row.home_losses || 0,
            ties: row.home_ties || 0
          }
        },
        // Only show prediction if both teams have ranking data
        prediction: hasSufficientData ? {
          winnerId: row.predicted_winner_id,
          confidence: row.prediction_confidence
        } : {
          winnerId: null,
          confidence: null
        }
      };
    });

    res.json({
      date,
      season,
      gameCount: games.length,
      games
    });

  } catch (error) {
    console.error('getNepsacSchedule error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacMatchup
 * Returns full matchup data for a single game including rosters
 *
 * Query params:
 * - gameId: string (required)
 */
functions.http('getNepsacMatchup', withCors(async (req, res) => {
  try {
    const { gameId } = req.query;

    if (!gameId) {
      return errorResponse(res, 400, 'gameId parameter is required');
    }

    // Get game info
    const gameQuery = `
      SELECT
        s.*,
        away.team_name as away_team_name,
        away.logo_url as away_logo_url,
        away.division as away_division,
        home.team_name as home_team_name,
        home.logo_url as home_logo_url,
        home.division as home_division
      FROM \`prodigy-ranking.algorithm_core.nepsac_schedule\` s
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` away ON s.away_team_id = away.team_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` home ON s.home_team_id = home.team_id
      WHERE s.game_id = '${gameId}'
      LIMIT 1
    `;

    const gameRows = await executeQuery(gameQuery);

    if (gameRows.length === 0) {
      return errorResponse(res, 404, 'Game not found');
    }

    const game = gameRows[0];
    const season = game.season;

    // Get team rankings
    const rankQuery = `
      SELECT team_id, rank, roster_size, matched_players, match_rate,
             avg_prodigy_points, total_prodigy_points, max_prodigy_points, team_ovr
      FROM \`prodigy-ranking.algorithm_core.nepsac_team_rankings\`
      WHERE team_id IN ('${game.away_team_id}', '${game.home_team_id}') AND season = '${season}'
    `;

    // Get standings
    const standingsQuery = `
      SELECT team_id, wins, losses, ties, goals_for, goals_against, streak
      FROM \`prodigy-ranking.algorithm_core.nepsac_standings\`
      WHERE team_id IN ('${game.away_team_id}', '${game.home_team_id}') AND season = '${season}'
    `;

    // Get rosters with player points and season stats (top 6 each)
    // Use subquery to get only the best stats row per player (most games played)
    const rosterQuery = `
      WITH ranked_stats AS (
        SELECT
          player_id,
          gp,
          goals,
          assists,
          points,
          gaa,
          svp,
          ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY gp DESC) as rn
        FROM \`prodigy-ranking.algorithm_core.player_season_stats\`
        WHERE season_start_year = 2025
          AND league_name = 'USHS-Prep'
      )
      SELECT
        r.team_id,
        r.roster_name,
        r.position,
        r.grad_year,
        r.jersey_number,
        r.player_id,
        r.image_url,
        COALESCE(p.total_points, 0) as total_points,
        -- Season stats from player_season_stats (USHS-Prep = NEPSAC in Elite Prospects)
        s.gp as games_played,
        s.goals,
        s.assists,
        s.points as season_points,
        s.gaa,
        s.svp as save_pct
      FROM \`prodigy-ranking.algorithm_core.nepsac_rosters\` r
      LEFT JOIN \`prodigy-ranking.algorithm_core.player_cumulative_points\` p
        ON r.player_id = p.player_id
      LEFT JOIN ranked_stats s
        ON r.player_id = s.player_id
        AND s.rn = 1
      WHERE r.team_id IN ('${game.away_team_id}', '${game.home_team_id}')
        AND r.season = '${season}'
        AND r.is_active = TRUE
      ORDER BY p.total_points DESC
    `;

    // Run queries
    const [rankRows, standingsRows, rosterRows] = await Promise.all([
      executeQuery(rankQuery),
      executeQuery(standingsQuery),
      executeQuery(rosterQuery)
    ]);

    // Build lookup maps
    const rankMap = {};
    rankRows.forEach(r => rankMap[r.team_id] = r);

    const standingsMap = {};
    standingsRows.forEach(s => standingsMap[s.team_id] = s);

    // Get max points for OVR calculation
    const maxPoints = Math.max(
      ...rosterRows.map(p => parseValue(p.total_points, 0)),
      1
    );

    // Split rosters by team
    const awayRoster = rosterRows
      .filter(p => p.team_id === game.away_team_id)
      .slice(0, 6)
      .map(p => {
        const points = parseValue(p.total_points, 0);
        return {
          playerId: p.player_id,
          name: p.roster_name,
          position: p.position,
          gradYear: p.grad_year,
          jerseyNumber: p.jersey_number,
          imageUrl: p.image_url,
          prodigyPoints: Math.round(points * 100) / 100,
          ovr: calculateOVR(points, maxPoints),
          // Season stats
          stats: {
            gp: p.games_played,
            goals: p.goals,
            assists: p.assists,
            points: p.season_points,
            gaa: p.gaa ? Math.round(p.gaa * 100) / 100 : null,
            savePct: p.save_pct ? Math.round(p.save_pct * 1000) / 1000 : null
          }
        };
      });

    const homeRoster = rosterRows
      .filter(p => p.team_id === game.home_team_id)
      .slice(0, 6)
      .map(p => {
        const points = parseValue(p.total_points, 0);
        return {
          playerId: p.player_id,
          name: p.roster_name,
          position: p.position,
          gradYear: p.grad_year,
          jerseyNumber: p.jersey_number,
          imageUrl: p.image_url,
          prodigyPoints: Math.round(points * 100) / 100,
          ovr: calculateOVR(points, maxPoints),
          // Season stats
          stats: {
            gp: p.games_played,
            goals: p.goals,
            assists: p.assists,
            points: p.season_points,
            gaa: p.gaa ? Math.round(p.gaa * 100) / 100 : null,
            savePct: p.save_pct ? Math.round(p.save_pct * 1000) / 1000 : null
          }
        };
      });

    // Build team objects
    const awayRank = rankMap[game.away_team_id] || {};
    const awayStandings = standingsMap[game.away_team_id] || {};
    const homeRank = rankMap[game.home_team_id] || {};
    const homeStandings = standingsMap[game.home_team_id] || {};

    // Check if both teams have ranking data - if not, don't show prediction
    const awayHasData = parseValue(awayRank.avg_prodigy_points, 0) > 0;
    const homeHasData = parseValue(homeRank.avg_prodigy_points, 0) > 0;
    const hasSufficientData = awayHasData && homeHasData;

    const response = {
      game: {
        gameId: game.game_id,
        date: parseValue(game.game_date),
        time: game.game_time,
        dayOfWeek: game.day_of_week,
        venue: game.venue,
        city: game.city,
        status: game.status,
        score: game.status === 'final' ? {
          away: game.away_score,
          home: game.home_score
        } : null,
        // Only show prediction if both teams have ranking data
        prediction: hasSufficientData ? {
          winnerId: game.predicted_winner_id,
          confidence: game.prediction_confidence
        } : {
          winnerId: null,
          confidence: null
        }
      },
      awayTeam: {
        teamId: game.away_team_id,
        name: game.away_team_name,
        logoUrl: game.away_logo_url,
        division: game.away_division,
        rank: awayRank.rank,
        ovr: awayRank.team_ovr || calculateTeamOVR(parseValue(awayRank.avg_prodigy_points, 1500)),
        record: {
          wins: awayStandings.wins || 0,
          losses: awayStandings.losses || 0,
          ties: awayStandings.ties || 0
        },
        stats: {
          avgPoints: Math.round(parseValue(awayRank.avg_prodigy_points, 0) * 100) / 100,
          totalPoints: Math.round(parseValue(awayRank.total_prodigy_points, 0) * 100) / 100,
          maxPoints: Math.round(parseValue(awayRank.max_prodigy_points, 0) * 100) / 100,
          rosterSize: awayRank.roster_size || 0,
          matchedPlayers: awayRank.matched_players || 0,
          matchRate: Math.round(parseValue(awayRank.match_rate, 0) * 1000) / 10
        },
        goalsFor: awayStandings.goals_for || 0,
        goalsAgainst: awayStandings.goals_against || 0,
        streak: awayStandings.streak,
        topPlayers: awayRoster
      },
      homeTeam: {
        teamId: game.home_team_id,
        name: game.home_team_name,
        logoUrl: game.home_logo_url,
        division: game.home_division,
        rank: homeRank.rank,
        ovr: homeRank.team_ovr || calculateTeamOVR(parseValue(homeRank.avg_prodigy_points, 1500)),
        record: {
          wins: homeStandings.wins || 0,
          losses: homeStandings.losses || 0,
          ties: homeStandings.ties || 0
        },
        stats: {
          avgPoints: Math.round(parseValue(homeRank.avg_prodigy_points, 0) * 100) / 100,
          totalPoints: Math.round(parseValue(homeRank.total_prodigy_points, 0) * 100) / 100,
          maxPoints: Math.round(parseValue(homeRank.max_prodigy_points, 0) * 100) / 100,
          rosterSize: homeRank.roster_size || 0,
          matchedPlayers: homeRank.matched_players || 0,
          matchRate: Math.round(parseValue(homeRank.match_rate, 0) * 1000) / 10
        },
        goalsFor: homeStandings.goals_for || 0,
        goalsAgainst: homeStandings.goals_against || 0,
        streak: homeStandings.streak,
        topPlayers: homeRoster
      },
      maxPoints: Math.round(maxPoints * 100) / 100
    };

    res.json(response);

  } catch (error) {
    console.error('getNepsacMatchup error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacTeams
 * Returns all NEPSAC teams with rankings
 *
 * Query params:
 * - season: string (default: '2025-26')
 * - division: string (optional filter)
 */
functions.http('getNepsacTeams', withCors(async (req, res) => {
  try {
    const { season = '2025-26', division } = req.query;

    let query = `
      SELECT
        t.team_id,
        t.team_name,
        t.short_name,
        t.division,
        t.logo_url,
        t.venue,
        t.city,
        t.state,
        r.rank,
        r.roster_size,
        r.matched_players,
        r.match_rate,
        r.avg_prodigy_points,
        r.total_prodigy_points,
        r.max_prodigy_points,
        r.team_ovr,
        r.top_player_name,
        s.wins,
        s.losses,
        s.ties,
        s.win_pct,
        s.streak
      FROM \`prodigy-ranking.algorithm_core.nepsac_teams\` t
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` r
        ON t.team_id = r.team_id AND r.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_standings\` s
        ON t.team_id = s.team_id AND s.season = '${season}'
    `;

    if (division) {
      query += ` WHERE t.division = '${division}'`;
    }

    query += ` ORDER BY r.rank ASC NULLS LAST, r.avg_prodigy_points DESC`;

    const rows = await executeQuery(query);

    const teams = rows.map(row => ({
      teamId: row.team_id,
      name: row.team_name,
      shortName: row.short_name,
      division: row.division,
      logoUrl: row.logo_url,
      venue: row.venue,
      city: row.city,
      state: row.state,
      rank: row.rank,
      ovr: row.team_ovr || calculateTeamOVR(parseValue(row.avg_prodigy_points, 1500)),
      record: {
        wins: row.wins || 0,
        losses: row.losses || 0,
        ties: row.ties || 0,
        winPct: Math.round(parseValue(row.win_pct, 0) * 1000) / 10
      },
      streak: row.streak,
      stats: {
        rosterSize: row.roster_size || 0,
        matchedPlayers: row.matched_players || 0,
        matchRate: Math.round(parseValue(row.match_rate, 0) * 1000) / 10,
        avgPoints: Math.round(parseValue(row.avg_prodigy_points, 0) * 100) / 100,
        totalPoints: Math.round(parseValue(row.total_prodigy_points, 0) * 100) / 100,
        maxPoints: Math.round(parseValue(row.max_prodigy_points, 0) * 100) / 100,
        topPlayer: row.top_player_name
      }
    }));

    res.json({
      season,
      teamCount: teams.length,
      teams
    });

  } catch (error) {
    console.error('getNepsacTeams error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacStandings
 * Returns current standings sorted by division/points
 *
 * Query params:
 * - season: string (default: '2025-26')
 * - division: string (optional filter)
 */
functions.http('getNepsacStandings', withCors(async (req, res) => {
  try {
    const { season = '2025-26', division } = req.query;

    let query = `
      SELECT
        t.team_id,
        t.team_name,
        t.short_name,
        t.logo_url,
        s.division,
        s.wins,
        s.losses,
        s.ties,
        s.overtime_losses,
        s.points,
        s.win_pct,
        s.games_played,
        s.goals_for,
        s.goals_against,
        s.goal_differential,
        s.streak,
        s.last_10,
        s.home_record,
        s.away_record,
        r.rank as prodigy_rank,
        r.team_ovr
      FROM \`prodigy-ranking.algorithm_core.nepsac_standings\` s
      JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` t ON s.team_id = t.team_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` r
        ON s.team_id = r.team_id AND r.season = s.season
      WHERE s.season = '${season}'
    `;

    if (division && division !== 'all') {
      query += ` AND s.division = '${division}'`;
    }

    query += ` ORDER BY s.division, s.points DESC, s.win_pct DESC, s.goal_differential DESC`;

    const rows = await executeQuery(query);

    // Group by division
    const standingsByDivision = {};
    rows.forEach(row => {
      const div = row.division || 'Other';
      if (!standingsByDivision[div]) {
        standingsByDivision[div] = [];
      }
      standingsByDivision[div].push({
        teamId: row.team_id,
        name: row.team_name,
        shortName: row.short_name,
        logoUrl: row.logo_url,
        prodigyRank: row.prodigy_rank,
        ovr: row.team_ovr,
        wins: row.wins || 0,
        losses: row.losses || 0,
        ties: row.ties || 0,
        otLosses: row.overtime_losses || 0,
        points: row.points || 0,
        winPct: Math.round(parseValue(row.win_pct, 0) * 1000) / 10,
        gamesPlayed: row.games_played || 0,
        goalsFor: row.goals_for || 0,
        goalsAgainst: row.goals_against || 0,
        goalDiff: row.goal_differential || 0,
        streak: row.streak,
        last10: row.last_10,
        homeRecord: row.home_record,
        awayRecord: row.away_record
      });
    });

    res.json({
      season,
      divisions: Object.keys(standingsByDivision),
      standings: standingsByDivision
    });

  } catch (error) {
    console.error('getNepsacStandings error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacRoster
 * Returns full team roster with player stats
 *
 * Query params:
 * - teamId: string (required)
 * - season: string (default: '2025-26')
 */
functions.http('getNepsacRoster', withCors(async (req, res) => {
  try {
    const { teamId, season = '2025-26' } = req.query;

    if (!teamId) {
      return errorResponse(res, 400, 'teamId parameter is required');
    }

    // Get team info
    const teamQuery = `
      SELECT
        t.team_id,
        t.team_name,
        t.short_name,
        t.logo_url,
        t.division,
        t.venue,
        r.rank,
        r.team_ovr,
        r.avg_prodigy_points,
        r.total_prodigy_points,
        r.max_prodigy_points,
        r.roster_size,
        r.matched_players,
        s.wins,
        s.losses,
        s.ties
      FROM \`prodigy-ranking.algorithm_core.nepsac_teams\` t
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_team_rankings\` r
        ON t.team_id = r.team_id AND r.season = '${season}'
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_standings\` s
        ON t.team_id = s.team_id AND s.season = '${season}'
      WHERE t.team_id = '${teamId}'
      LIMIT 1
    `;

    // Get roster with season stats
    // Use subquery to get only the best stats row per player (most games played)
    const rosterQuery = `
      WITH ranked_stats AS (
        SELECT
          player_id,
          gp,
          goals,
          assists,
          points,
          gaa,
          svp,
          ROW_NUMBER() OVER (PARTITION BY player_id ORDER BY gp DESC) as rn
        FROM \`prodigy-ranking.algorithm_core.player_season_stats\`
        WHERE season_start_year = 2025
          AND league_name = 'USHS-Prep'
      )
      SELECT
        r.roster_name,
        r.position,
        r.grad_year,
        r.jersey_number,
        r.player_id,
        r.image_url,
        r.is_captain,
        r.match_confidence,
        COALESCE(p.total_points, 0) as total_points,
        p.birth_year,
        p.nationality_name,
        p.current_team as db_team,
        p.current_league as db_league,
        -- Season stats from player_season_stats (USHS-Prep = NEPSAC in Elite Prospects)
        s.gp as games_played,
        s.goals,
        s.assists,
        s.points as season_points,
        s.gaa,
        s.svp as save_pct
      FROM \`prodigy-ranking.algorithm_core.nepsac_rosters\` r
      LEFT JOIN \`prodigy-ranking.algorithm_core.player_cumulative_points\` p
        ON r.player_id = p.player_id
      LEFT JOIN ranked_stats s
        ON r.player_id = s.player_id
        AND s.rn = 1
      WHERE r.team_id = '${teamId}' AND r.season = '${season}' AND r.is_active = TRUE
      ORDER BY p.total_points DESC NULLS LAST, r.position, r.roster_name
    `;

    const [teamRows, rosterRows] = await Promise.all([
      executeQuery(teamQuery),
      executeQuery(rosterQuery)
    ]);

    if (teamRows.length === 0) {
      return errorResponse(res, 404, 'Team not found');
    }

    const team = teamRows[0];
    const maxPoints = Math.max(
      ...rosterRows.map(p => parseValue(p.total_points, 0)),
      1
    );

    const players = rosterRows.map(row => {
      const points = parseValue(row.total_points, 0);
      return {
        playerId: row.player_id,
        name: row.roster_name,
        position: row.position,
        gradYear: row.grad_year,
        jerseyNumber: row.jersey_number,
        isCaptain: row.is_captain,
        imageUrl: row.image_url,
        matchConfidence: Math.round(parseValue(row.match_confidence, 0) * 100),
        prodigyPoints: Math.round(points * 100) / 100,
        ovr: calculateOVR(points, maxPoints),
        birthYear: row.birth_year,
        nationality: row.nationality_name,
        dbTeam: row.db_team,
        dbLeague: row.db_league,
        // Season stats
        stats: {
          gp: row.games_played,
          goals: row.goals,
          assists: row.assists,
          points: row.season_points,
          gaa: row.gaa ? Math.round(row.gaa * 100) / 100 : null,
          savePct: row.save_pct ? Math.round(row.save_pct * 1000) / 1000 : null
        }
      };
    });

    // Group by position
    const forwards = players.filter(p => p.position === 'F');
    const defensemen = players.filter(p => p.position === 'D');
    const goalies = players.filter(p => p.position === 'G');

    res.json({
      team: {
        teamId: team.team_id,
        name: team.team_name,
        shortName: team.short_name,
        logoUrl: team.logo_url,
        division: team.division,
        venue: team.venue,
        rank: team.rank,
        ovr: team.team_ovr || calculateTeamOVR(parseValue(team.avg_prodigy_points, 1500)),
        record: {
          wins: team.wins || 0,
          losses: team.losses || 0,
          ties: team.ties || 0
        },
        stats: {
          avgPoints: Math.round(parseValue(team.avg_prodigy_points, 0) * 100) / 100,
          totalPoints: Math.round(parseValue(team.total_prodigy_points, 0) * 100) / 100,
          maxPoints: Math.round(parseValue(team.max_prodigy_points, 0) * 100) / 100,
          rosterSize: team.roster_size || 0,
          matchedPlayers: team.matched_players || 0
        }
      },
      season,
      playerCount: players.length,
      maxPoints: Math.round(maxPoints * 100) / 100,
      roster: {
        forwards,
        defensemen,
        goalies,
        all: players
      }
    });

  } catch (error) {
    console.error('getNepsacRoster error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacPastResults
 * Returns completed games with prediction accuracy tracking
 *
 * Query params:
 * - season: string (default: '2025-26')
 * - startDate: string (optional YYYY-MM-DD, defaults to season start)
 * - endDate: string (optional YYYY-MM-DD, defaults to today)
 * - limit: number (optional, max games to return, default 100)
 */
functions.http('getNepsacPastResults', withCors(async (req, res) => {
  try {
    const { season = '2025-26', startDate, endDate, limit = 100 } = req.query;

    const query = `
      SELECT
        s.game_id,
        s.game_date,
        s.game_time,
        s.day_of_week,
        s.status,
        s.away_score,
        s.home_score,
        s.predicted_winner_id,
        s.prediction_confidence,
        s.away_team_id,
        away.team_name as away_team_name,
        away.short_name as away_short_name,
        s.home_team_id,
        home.team_name as home_team_name,
        home.short_name as home_short_name
      FROM \`prodigy-ranking.algorithm_core.nepsac_schedule\` s
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` away
        ON s.away_team_id = away.team_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.nepsac_teams\` home
        ON s.home_team_id = home.team_id
      WHERE s.season = '${season}'
        AND s.status = 'final'
        AND s.predicted_winner_id IS NOT NULL
        ${startDate ? `AND s.game_date >= '${startDate}'` : ''}
        ${endDate ? `AND s.game_date <= '${endDate}'` : ''}
      ORDER BY s.game_date DESC, s.game_time
      LIMIT ${parseInt(limit)}
    `;

    const rows = await executeQuery(query);

    // Process results and calculate accuracy
    let correct = 0;
    let incorrect = 0;
    let ties = 0;
    const gamesByDate = {};

    rows.forEach(row => {
      const awayScore = parseInt(row.away_score) || 0;
      const homeScore = parseInt(row.home_score) || 0;
      const predictedWinnerId = row.predicted_winner_id;

      // Determine actual winner
      let actualWinnerId = null;
      let isTie = false;
      if (awayScore > homeScore) {
        actualWinnerId = row.away_team_id;
      } else if (homeScore > awayScore) {
        actualWinnerId = row.home_team_id;
      } else {
        isTie = true;
      }

      // Calculate prediction result
      let predictionResult;
      if (isTie) {
        predictionResult = 'tie';
        ties++;
      } else if (predictedWinnerId === actualWinnerId) {
        predictionResult = 'correct';
        correct++;
      } else {
        predictionResult = 'incorrect';
        incorrect++;
      }

      // Get date string for grouping
      const dateStr = parseValue(row.game_date);
      if (!gamesByDate[dateStr]) {
        gamesByDate[dateStr] = {
          date: dateStr,
          dayOfWeek: row.day_of_week,
          games: [],
          correct: 0,
          incorrect: 0,
          ties: 0
        };
      }

      // Update date stats
      if (predictionResult === 'correct') gamesByDate[dateStr].correct++;
      else if (predictionResult === 'incorrect') gamesByDate[dateStr].incorrect++;
      else gamesByDate[dateStr].ties++;

      // Add game to date
      gamesByDate[dateStr].games.push({
        gameId: row.game_id,
        gameTime: row.game_time,
        awayTeam: {
          teamId: row.away_team_id,
          name: row.away_team_name,
          shortName: row.away_short_name,
          score: awayScore,
          isWinner: awayScore > homeScore,
          wasPredicted: predictedWinnerId === row.away_team_id
        },
        homeTeam: {
          teamId: row.home_team_id,
          name: row.home_team_name,
          shortName: row.home_short_name,
          score: homeScore,
          isWinner: homeScore > awayScore,
          wasPredicted: predictedWinnerId === row.home_team_id
        },
        prediction: {
          winnerId: predictedWinnerId,
          confidence: row.prediction_confidence
        },
        result: predictionResult,
        isTie
      });
    });

    // Convert to sorted array
    const dates = Object.values(gamesByDate).sort((a, b) =>
      new Date(b.date) - new Date(a.date)
    );

    // Calculate overall stats
    const totalGames = correct + incorrect + ties;
    const accuracy = totalGames > 0 ? Math.round((correct / (totalGames - ties)) * 1000) / 10 : 0;

    res.json({
      season,
      summary: {
        totalGames,
        correct,
        incorrect,
        ties,
        accuracy, // Percentage (excludes ties from denominator)
        record: `${correct}-${incorrect}${ties > 0 ? `-${ties}` : ''}`
      },
      dateCount: dates.length,
      dates
    });

  } catch (error) {
    console.error('getNepsacPastResults error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * GET /getNepsacGameDates
 * Returns all dates that have scheduled games
 *
 * Query params:
 * - season: string (default: '2025-26')
 * - month: number (optional, 1-12)
 */
functions.http('getNepsacGameDates', withCors(async (req, res) => {
  try {
    const { season = '2025-26', month } = req.query;

    let query = `
      SELECT
        game_date,
        COUNT(*) as game_count,
        MIN(game_time) as first_game,
        MAX(game_time) as last_game
      FROM \`prodigy-ranking.algorithm_core.nepsac_schedule\`
      WHERE season = '${season}'
        AND status != 'cancelled'
    `;

    if (month) {
      query += ` AND EXTRACT(MONTH FROM game_date) = ${parseInt(month)}`;
    }

    query += ` GROUP BY game_date ORDER BY game_date`;

    const rows = await executeQuery(query);

    const dates = rows.map(row => ({
      date: parseValue(row.game_date),
      gameCount: row.game_count,
      firstGame: row.first_game,
      lastGame: row.last_game
    }));

    res.json({
      season,
      dateCount: dates.length,
      dates
    });

  } catch (error) {
    console.error('getNepsacGameDates error:', error);
    return errorResponse(res, 500, error.message);
  }
}));

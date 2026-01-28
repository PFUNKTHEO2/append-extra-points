/**
 * NEPSAC Data Sync: BigQuery → Supabase
 *
 * ============================================================================
 * SINGLE SOURCE OF TRUTH: BigQuery
 * ============================================================================
 *
 * BigQuery is the authoritative source for all NEPSAC data:
 * - nepsac_teams: Team info, classification, enrollment
 * - nepsac_team_rankings: Power rankings, OVR ratings
 * - nepsac_standings: W-L-T records, goals
 * - nepsac_schedule: Game schedule and predictions
 * - nepsac_game_performers: Per-game player stats
 *
 * This function syncs that data to Supabase for frontend use.
 *
 * ============================================================================
 */

const functions = require('@google-cloud/functions-framework');
const cors = require('cors');
const { executeQuery } = require('./shared/bigquery');
const { createClient } = require('@supabase/supabase-js');

const corsMiddleware = cors({ origin: true });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

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

/**
 * Sync NEPSAC Teams from BigQuery to Supabase
 * Source: algorithm_core.nepsac_teams
 */
async function syncTeams(supabase) {
  console.log('Syncing NEPSAC teams...');

  const query = `
    SELECT
      team_id,
      team_name,
      short_name,
      classification,
      enrollment,
      logo_url,
      primary_color,
      secondary_color,
      venue,
      city,
      state
    FROM \`prodigy-ranking.algorithm_core.nepsac_teams\`
    WHERE classification IN ('Large', 'Small')
    ORDER BY enrollment DESC
  `;

  const rows = await executeQuery(query);
  console.log(`Fetched ${rows.length} teams from BigQuery`);

  // Transform for Supabase schema
  const teams = rows.map(row => ({
    team_id: row.team_id,
    team_name: row.team_name,
    short_name: row.short_name,
    division: row.classification,  // Supabase uses 'division' for classification
    logo_url: row.logo_url,
    primary_color: row.primary_color,
    secondary_color: row.secondary_color,
    venue: row.venue,
    city: row.city,
    state: row.state,
    updated_at: new Date().toISOString(),
  }));

  // Upsert to Supabase
  const { error } = await supabase
    .from('nepsac_teams')
    .upsert(teams, { onConflict: 'team_id' });

  if (error) {
    throw new Error(`Teams sync error: ${error.message}`);
  }

  return teams.length;
}

/**
 * Sync NEPSAC Games/Schedule from BigQuery to Supabase
 * Source: algorithm_core.nepsac_schedule
 */
async function syncGames(supabase, season = '2025-26') {
  console.log(`Syncing NEPSAC games for ${season}...`);

  const query = `
    SELECT
      game_id,
      season,
      game_date,
      game_time,
      away_team_id,
      home_team_id,
      venue,
      city,
      status,
      away_score,
      home_score,
      overtime AS is_overtime,
      shootout AS is_shootout,
      predicted_winner_id,
      prediction_confidence
    FROM \`prodigy-ranking.algorithm_core.nepsac_schedule\`
    WHERE season = '${season}'
    ORDER BY game_date, game_time
  `;

  const rows = await executeQuery(query);
  console.log(`Fetched ${rows.length} games from BigQuery`);

  // Transform for Supabase schema
  const games = rows.map(row => {
    // Determine actual winner and prediction correctness
    let actualWinnerId = null;
    let isTie = false;
    let predictionCorrect = null;

    if (row.status === 'final' && row.away_score !== null && row.home_score !== null) {
      if (row.away_score > row.home_score) {
        actualWinnerId = row.away_team_id;
      } else if (row.home_score > row.away_score) {
        actualWinnerId = row.home_team_id;
      } else {
        isTie = true;
      }

      // Determine if prediction was correct
      if (isTie) {
        predictionCorrect = null;  // Ties don't count
      } else if (row.predicted_winner_id === actualWinnerId) {
        predictionCorrect = true;
      } else {
        predictionCorrect = false;
      }
    }

    // Map confidence to tier
    let predictionTier = 'Toss-up';
    if (row.prediction_confidence >= 70) predictionTier = 'Very High';
    else if (row.prediction_confidence >= 65) predictionTier = 'High';
    else if (row.prediction_confidence >= 58) predictionTier = 'Medium';
    else if (row.prediction_confidence >= 52) predictionTier = 'Low';

    return {
      game_id: row.game_id,
      season: row.season,
      game_date: row.game_date,
      game_time: row.game_time,
      away_team_id: row.away_team_id,
      home_team_id: row.home_team_id,
      venue: row.venue,
      city: row.city,
      status: row.status || 'scheduled',
      away_score: row.away_score,
      home_score: row.home_score,
      is_overtime: row.is_overtime || false,
      is_shootout: row.is_shootout || false,
      predicted_winner_id: row.predicted_winner_id,
      prediction_confidence: row.prediction_confidence,
      prediction_tier: predictionTier,
      actual_winner_id: actualWinnerId,
      is_tie: isTie,
      prediction_correct: predictionCorrect,
      updated_at: new Date().toISOString(),
    };
  });

  // Batch upsert to Supabase
  const BATCH_SIZE = 100;
  let synced = 0;

  for (let i = 0; i < games.length; i += BATCH_SIZE) {
    const batch = games.slice(i, i + BATCH_SIZE);
    const { error } = await supabase
      .from('nepsac_games')
      .upsert(batch, { onConflict: 'game_id' });

    if (error) {
      console.error(`Games batch ${i} error:`, error.message);
    } else {
      synced += batch.length;
    }
  }

  return synced;
}

/**
 * Sync overall prediction stats
 */
async function syncOverallStats(supabase, season = '2025-26') {
  console.log('Calculating overall stats...');

  // Get all completed games
  const { data: games, error } = await supabase
    .from('nepsac_games')
    .select('*')
    .eq('season', season)
    .eq('status', 'final');

  if (error) {
    throw new Error(`Stats query error: ${error.message}`);
  }

  const correct = games.filter(g => g.prediction_correct === true).length;
  const incorrect = games.filter(g => g.prediction_correct === false).length;
  const ties = games.filter(g => g.is_tie === true).length;
  const total = correct + incorrect;  // Ties excluded

  const accuracy = total > 0 ? Math.round(1000 * correct / total) / 10 : null;

  const stats = {
    season,
    total_predictions: games.length,
    correct_predictions: correct,
    incorrect_predictions: incorrect,
    ties: ties,
    overall_accuracy: accuracy,
    last_updated: new Date().toISOString(),
  };

  const { error: upsertError } = await supabase
    .from('nepsac_overall_stats')
    .upsert(stats, { onConflict: 'season' });

  if (upsertError) {
    console.error('Stats upsert error:', upsertError.message);
  }

  return stats;
}

/**
 * Main sync endpoint: Sync all NEPSAC data from BigQuery to Supabase
 */
functions.http('syncNepsacData', withCors(async (req, res) => {
  console.log('Starting NEPSAC BigQuery → Supabase sync...');
  const startTime = Date.now();

  try {
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase credentials not configured');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false }
    });

    const season = req.query.season || '2025-26';
    const results = {};

    // Sync teams
    results.teams = await syncTeams(supabase);

    // Sync games
    results.games = await syncGames(supabase, season);

    // Update overall stats
    results.stats = await syncOverallStats(supabase, season);

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);

    res.status(200).json({
      success: true,
      message: `NEPSAC sync complete in ${elapsed}s`,
      season,
      results,
      timestamp: new Date().toISOString(),
      _metadata: {
        source: 'BigQuery (algorithm_core)',
        destination: 'Supabase (nepsac_*)',
        note: 'BigQuery is the single source of truth',
      },
    });

  } catch (error) {
    console.error('NEPSAC sync failed:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * Sync just teams (quick update)
 */
functions.http('syncNepsacTeams', withCors(async (req, res) => {
  try {
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase credentials not configured');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false }
    });

    const count = await syncTeams(supabase);

    res.status(200).json({
      success: true,
      message: `Synced ${count} NEPSAC teams`,
      count,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Teams sync failed:', error);
    return errorResponse(res, 500, error.message);
  }
}));

/**
 * Sync just games (after results update)
 */
functions.http('syncNepsacGames', withCors(async (req, res) => {
  try {
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase credentials not configured');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false }
    });

    const season = req.query.season || '2025-26';
    const count = await syncGames(supabase, season);

    // Also update stats
    const stats = await syncOverallStats(supabase, season);

    res.status(200).json({
      success: true,
      message: `Synced ${count} NEPSAC games`,
      count,
      stats,
      timestamp: new Date().toISOString(),
    });

  } catch (error) {
    console.error('Games sync failed:', error);
    return errorResponse(res, 500, error.message);
  }
}));

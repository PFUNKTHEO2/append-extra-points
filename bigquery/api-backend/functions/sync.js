/**
 * Sync Rankings from BigQuery to Supabase
 * Triggered by Cloud Scheduler for automated daily sync
 */

const { BigQuery } = require('@google-cloud/bigquery');
const { createClient } = require('@supabase/supabase-js');

const bigquery = new BigQuery({ projectId: 'prodigy-ranking' });

const SUPABASE_URL = process.env.SUPABASE_URL;
const SUPABASE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY;

// All columns to sync
const BASE_COLUMNS = [
  'player_id', 'player_name', 'position', 'birth_year', 'nationality_name',
  'current_team', 'current_league', 'team_country', 'current_season',
  'total_points', 'performance_total', 'direct_load_total',
  'f01_views', 'f02_height', 'f03_current_goals_f', 'f04_current_goals_d',
  'f05_current_assists', 'f06_current_gaa', 'f07_current_svp',
  'f08_last_goals_f', 'f09_last_goals_d', 'f10_last_assists',
  'f11_last_gaa', 'f12_last_svp', 'f13_league_points', 'f14_team_points',
  'f15_international_points', 'f16_commitment_points', 'f17_draft_points',
  'f18_weekly_points_delta', 'f19_weekly_assists_delta', 'f20_playing_up_points',
  'f21_tournament_points', 'f22_manual_points', 'f23_prodigylikes_points',
  'f24_card_sales_points', 'f25_weekly_views', 'f26_weight_points', 'f27_bmi_points',
  'calculated_at', 'algorithm_version'
];
// NOTE: f28_nhl_scouting_points excluded until Supabase column is added

const RATING_COLUMNS = [
  'overall_rating', 'performance_rating', 'level_rating', 'visibility_rating',
  'achievements_rating', 'trending_rating', 'physical_rating',
  'perf', 'lvl', 'vis', 'ach', 'trd', 'phy'
];

const PERCENTILE_COLUMNS = [
  'performance_percentile', 'level_percentile', 'visibility_percentile',
  'achievements_percentile', 'physical_percentile', 'trending_percentile',
  'overall_percentile'
];

// Pre-computed rank columns (computed in BigQuery, not Supabase view)
const RANK_COLUMNS = [
  'world_rank', 'country_rank'
];

/**
 * Main sync function - triggered by Cloud Scheduler
 */
exports.syncRankings = async (req, res) => {
  console.log('Starting BigQuery → Supabase sync...');
  const startTime = Date.now();

  try {
    // Validate environment
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase credentials not configured');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false }
    });

    // Build query
    const baseColsSql = BASE_COLUMNS.map(col => {
      if (['total_points', 'performance_total', 'direct_load_total'].includes(col)) {
        return `ROUND(p.${col}, 2) as ${col}`;
      } else if (col.startsWith('f') && /^f\d{2}/.test(col)) {
        return `ROUND(COALESCE(p.${col}, 0), 2) as ${col}`;
      }
      return `p.${col}`;
    });

    const ratingColsSql = RATING_COLUMNS.map(col => `COALESCE(r.${col}, 0) as ${col}`);
    const pctColsSql = PERCENTILE_COLUMNS.map(col => `COALESCE(pct.${col}, 0) as ${col}`);

    // Pre-compute ranks in BigQuery (much faster than computing in Supabase view)
    const query = `
      WITH ranked AS (
        SELECT
          ${[...baseColsSql, ...ratingColsSql, ...pctColsSql].join(', ')},
          ROW_NUMBER() OVER (
            PARTITION BY p.birth_year, p.position
            ORDER BY p.total_points DESC
          ) as world_rank,
          ROW_NUMBER() OVER (
            PARTITION BY p.birth_year, p.position, p.nationality_name
            ORDER BY p.total_points DESC
          ) as country_rank
        FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\` p
        LEFT JOIN \`prodigy-ranking.algorithm_core.player_card_ratings\` r ON p.player_id = r.player_id
        LEFT JOIN \`prodigy-ranking.algorithm_core.player_category_percentiles\` pct ON p.player_id = pct.player_id
      )
      SELECT * FROM ranked
      ORDER BY total_points DESC
    `;

    console.log('Querying BigQuery...');
    const [rows] = await bigquery.query({ query, location: 'US' });
    console.log(`Fetched ${rows.length} players from BigQuery`);

    // Prepare records
    const now = new Date().toISOString();
    const records = rows.map(row => {
      const record = { synced_at: now };
      for (const [key, value] of Object.entries(row)) {
        if (value === null || value === undefined) {
          // Handle null values based on field type
          if (key.includes('_name') || key.includes('_team') || key.includes('_league') || key === 'algorithm_version' || key === 'current_season') {
            record[key] = '';
          } else if (key === 'calculated_at') {
            record[key] = now; // Use current time for null timestamps
          } else {
            record[key] = 0;
          }
        } else if (key === 'calculated_at') {
          // Handle calculated_at timestamp - MUST come before generic object check
          if (typeof value === 'string') {
            try {
              record[key] = new Date(value).toISOString();
            } catch (e) {
              record[key] = now;
            }
          } else if (typeof value === 'object' && value.value) {
            // BigQuery timestamp object
            record[key] = new Date(value.value).toISOString();
          } else if (value instanceof Date) {
            record[key] = value.toISOString();
          } else {
            record[key] = now;
          }
        } else if (typeof value === 'object' && value.value !== undefined) {
          // Handle BigQuery Decimal type (NOT timestamps)
          record[key] = parseFloat(value.value);
        } else if (value instanceof Date) {
          record[key] = value.toISOString();
        } else {
          record[key] = value;
        }
      }
      return record;
    });

    // Batch upsert to Supabase
    const BATCH_SIZE = 500;
    let successCount = 0;
    let errorCount = 0;

    console.log(`Syncing ${records.length} records to Supabase...`);

    for (let i = 0; i < records.length; i += BATCH_SIZE) {
      const batch = records.slice(i, i + BATCH_SIZE);
      try {
        const { error } = await supabase
          .from('player_rankings')
          .upsert(batch, { onConflict: 'player_id' });

        if (error) {
          console.error(`Batch ${Math.floor(i/BATCH_SIZE) + 1} error:`, error.message);
          errorCount += batch.length;
        } else {
          successCount += batch.length;
        }
      } catch (err) {
        console.error(`Batch ${Math.floor(i/BATCH_SIZE) + 1} exception:`, err.message);
        errorCount += batch.length;
      }

      // Progress log every 50 batches
      if ((i / BATCH_SIZE) % 50 === 0 && i > 0) {
        console.log(`Progress: ${successCount} synced, ${errorCount} errors`);
      }
    }

    const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
    const result = {
      success: true,
      message: `Sync complete: ${successCount} records in ${elapsed}s`,
      stats: {
        total: records.length,
        success: successCount,
        errors: errorCount,
        duration_seconds: parseFloat(elapsed)
      },
      timestamp: now
    };

    console.log(result.message);
    res.status(200).json(result);

  } catch (error) {
    console.error('Sync failed:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};

/**
 * Delete female players from Supabase
 * Female players are identified by team names containing "(W)"
 */
exports.deleteFemales = async (req, res) => {
  console.log('Starting female player deletion from Supabase...');

  try {
    if (!SUPABASE_URL || !SUPABASE_KEY) {
      throw new Error('Supabase credentials not configured');
    }

    const supabase = createClient(SUPABASE_URL, SUPABASE_KEY, {
      auth: { autoRefreshToken: false, persistSession: false }
    });

    // Delete players where current_team contains '(W)'
    const { data, error } = await supabase
      .from('player_rankings')
      .delete()
      .like('current_team', '%(W)%')
      .select('player_id');

    if (error) {
      throw new Error(`Supabase delete error: ${error.message}`);
    }

    const deletedCount = data ? data.length : 0;
    console.log(`Deleted ${deletedCount} female players from Supabase`);

    res.status(200).json({
      success: true,
      message: `Deleted ${deletedCount} female players from Supabase`,
      deleted_count: deletedCount,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('Delete failed:', error);
    res.status(500).json({
      success: false,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};


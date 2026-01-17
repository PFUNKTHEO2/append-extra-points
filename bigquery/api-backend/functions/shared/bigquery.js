/**
 * BigQuery Connection Utility
 * Shared module for connecting to BigQuery and executing queries
 */

const { BigQuery } = require('@google-cloud/bigquery');

// Import Supabase for fast lookups (with BigQuery fallback)
const supabaseModule = require('./supabase');

// Initialize BigQuery client
const bigquery = new BigQuery({
  projectId: 'prodigy-ranking',
  // When running locally, credentials will be picked up from GOOGLE_APPLICATION_CREDENTIALS env var
  // When deployed to Cloud Functions, it will use the service account automatically
});

// =====================================================================
// IN-MEMORY CACHE - Dramatically speeds up repeated requests
// Cloud Functions instances persist between invocations, so cache works
// =====================================================================
const cache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes in milliseconds

function getCached(key) {
  const entry = cache.get(key);
  if (!entry) return null;
  if (Date.now() > entry.expires) {
    cache.delete(key);
    return null;
  }
  return entry.data;
}

function setCache(key, data) {
  // Limit cache size to prevent memory issues
  if (cache.size > 1000) {
    // Delete oldest entries (first 100)
    const keys = Array.from(cache.keys()).slice(0, 100);
    keys.forEach(k => cache.delete(k));
  }
  cache.set(key, { data, expires: Date.now() + CACHE_TTL });
}

/**
 * Execute a BigQuery query and return results
 * @param {string} query - SQL query to execute
 * @param {object} options - Query options
 * @returns {Promise<Array>} Query results
 */
async function executeQuery(query, options = {}) {
  try {
    console.log('Executing query:', query.substring(0, 100) + '...');

    const [job] = await bigquery.createQueryJob({
      query,
      location: 'US',
      // Enable BigQuery's built-in query cache for faster repeated queries
      useQueryCache: true,
      ...options,
    });

    console.log(`Job ${job.id} started.`);

    // Wait for the query to finish
    const [rows] = await job.getQueryResults();

    console.log(`Query returned ${rows.length} rows.`);

    return rows;
  } catch (error) {
    console.error('BigQuery Error:', error);
    throw new Error(`BigQuery query failed: ${error.message}`);
  }
}

/**
 * Get a single player by player_id with pre-calculated ranks and percentiles
 * Uses Supabase for fast lookups (<50ms), falls back to BigQuery if unavailable
 * @param {number} playerId - Player ID
 * @returns {Promise<object>} Player data with world_rank, country_rank, and category percentiles
 */
async function getPlayerById(playerId) {
  // Check in-memory cache first
  const cacheKey = `player:${playerId}`;
  const cached = getCached(cacheKey);
  if (cached) {
    console.log(`Cache HIT for player ${playerId}`);
    return cached;
  }

  // Try Supabase first (fast - typically <50ms)
  if (supabaseModule.isConfigured()) {
    console.log(`Trying Supabase for player ${playerId}...`);
    const supabaseResult = await supabaseModule.getPlayerById(playerId);
    if (supabaseResult) {
      console.log(`Supabase HIT for player ${playerId}`);
      setCache(cacheKey, supabaseResult);
      return supabaseResult;
    }
    console.log(`Supabase MISS for player ${playerId}, falling back to BigQuery...`);
  }

  // Fall back to BigQuery (slow but complete)
  console.log(`Querying BigQuery for player ${playerId}...`);

  // FAST QUERY: Single table lookup, no JOINs
  // Percentiles/ratings available via separate endpoints if needed
  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      team_country,
      current_season,

      ROUND(total_points, 2) as total_points,
      ROUND(performance_total, 2) as performance_total,
      ROUND(direct_load_total, 2) as direct_load_total,

      ROUND(f01_views, 2) as f01_views,
      ROUND(f02_height, 2) as f02_height,
      ROUND(f03_current_goals_f, 2) as f03_current_goals_f,
      ROUND(f04_current_goals_d, 2) as f04_current_goals_d,
      ROUND(f05_current_assists, 2) as f05_current_assists,
      ROUND(f06_current_gaa, 2) as f06_current_gaa,
      ROUND(f07_current_svp, 2) as f07_current_svp,
      ROUND(f08_last_goals_f, 2) as f08_last_goals_f,
      ROUND(f09_last_goals_d, 2) as f09_last_goals_d,
      ROUND(f10_last_assists, 2) as f10_last_assists,
      ROUND(f11_last_gaa, 2) as f11_last_gaa,
      ROUND(f12_last_svp, 2) as f12_last_svp,
      COALESCE(f13_league_points, 0) as f13_league_points,
      COALESCE(f14_team_points, 0) as f14_team_points,
      ROUND(COALESCE(f15_international_points, 0), 2) as f15_international_points,
      COALESCE(f16_commitment_points, 0) as f16_commitment_points,
      COALESCE(f17_draft_points, 0) as f17_draft_points,
      ROUND(COALESCE(f18_weekly_points_delta, 0), 2) as f18_weekly_points_delta,
      ROUND(COALESCE(f19_weekly_assists_delta, 0), 2) as f19_weekly_assists_delta,
      COALESCE(f20_playing_up_points, 0) as f20_playing_up_points,
      COALESCE(f21_tournament_points, 0) as f21_tournament_points,
      COALESCE(f22_manual_points, 0) as f22_manual_points,
      COALESCE(f23_prodigylikes_points, 0) as f23_prodigylikes_points,
      COALESCE(f24_card_sales_points, 0) as f24_card_sales_points,
      ROUND(COALESCE(f26_weight_points, 0), 2) as f26_weight_points,
      ROUND(COALESCE(f27_bmi_points, 0), 2) as f27_bmi_points,

      calculated_at,
      algorithm_version

    FROM \`prodigy-ranking.algorithm_core.player_rankings\`
    WHERE player_id = @playerId
  `;

  const options = {
    query,
    params: { playerId: parseInt(playerId) },
  };

  const rows = await executeQuery(query, options);
  const result = rows.length > 0 ? rows[0] : null;

  // Cache the result for fast subsequent lookups
  if (result) {
    setCache(cacheKey, result);
  }

  return result;
}

/**
 * Search players by name
 * Uses Supabase for fast search, falls back to BigQuery
 * @param {string} searchQuery - Search term
 * @param {number} limit - Maximum results (default 10)
 * @returns {Promise<Array>} Matching players
 */
async function searchPlayers(searchQuery, limit = 10) {
  // Check cache
  const cacheKey = `search:${searchQuery.toLowerCase()}:${limit}`;
  const cached = getCached(cacheKey);
  if (cached) {
    console.log(`Cache HIT for search "${searchQuery}"`);
    return cached;
  }

  // Try Supabase first (fast)
  if (supabaseModule.isConfigured()) {
    console.log(`Trying Supabase for search "${searchQuery}"...`);
    const supabaseResult = await supabaseModule.searchPlayers(searchQuery, limit);
    if (supabaseResult && supabaseResult.length > 0) {
      console.log(`Supabase search returned ${supabaseResult.length} results`);
      setCache(cacheKey, supabaseResult);
      return supabaseResult;
    }
    console.log(`Supabase search empty, falling back to BigQuery...`);
  }

  // Fall back to BigQuery
  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      ROUND(total_points, 2) as total_points
    FROM \`prodigy-ranking.algorithm_core.player_rankings\`
    WHERE LOWER(player_name) LIKE LOWER(@searchQuery)
    ORDER BY total_points DESC
    LIMIT @limit
  `;

  const options = {
    query,
    params: {
      searchQuery: `%${searchQuery}%`,
      limit: parseInt(limit)
    },
  };

  const results = await executeQuery(query, options);
  setCache(cacheKey, results);
  return results;
}

/**
 * Get homepage statistics
 * @returns {Promise<object>} Stats object
 */
async function getStats() {
  const query = `
    SELECT
      COUNT(DISTINCT player_id) as total_players,
      COUNT(DISTINCT current_league) as total_leagues,
      COUNT(DISTINCT nationality_name) as total_countries,
      MAX(calculated_at) as last_updated
    FROM \`prodigy-ranking.algorithm_core.player_rankings\`
  `;

  const rows = await executeQuery(query);
  return rows[0];
}

/**
 * Get rankings for a specific birth year, scope, and position
 * Uses Supabase for fast lookups, falls back to BigQuery
 * @param {number} birthYear - Birth year (2007-2011)
 * @param {string} scope - 'worldwide', 'north_american', or country name
 * @param {string} position - 'F', 'D', or 'G'
 * @param {number} limit - Maximum results (default 250)
 * @returns {Promise<object>} Rankings data
 */
async function getRankings(birthYear, scope, position, limit = 250) {
  // Check cache
  const cacheKey = `rankings:${birthYear}:${scope}:${position}:${limit}`;
  const cached = getCached(cacheKey);
  if (cached) {
    console.log(`Cache HIT for rankings ${birthYear}/${scope}/${position}`);
    return cached;
  }

  // Try Supabase first (fast)
  if (supabaseModule.isConfigured()) {
    console.log(`Trying Supabase for rankings ${birthYear}/${scope}/${position}...`);
    const supabaseResult = await supabaseModule.getRankings(birthYear, scope, position, limit);
    if (supabaseResult && supabaseResult.players && supabaseResult.players.length > 0) {
      console.log(`Supabase rankings returned ${supabaseResult.players.length} players`);
      setCache(cacheKey, supabaseResult);
      return supabaseResult;
    }
    console.log(`Supabase rankings empty, falling back to BigQuery...`);
  }

  // Fall back to BigQuery
  let whereClause = 'WHERE birth_year = @birthYear AND position = @position';
  let params = {
    birthYear: parseInt(birthYear),
    position: position.toUpperCase(),
    limit: parseInt(limit)
  };

  // Handle scope filtering
  if (scope === 'north_american') {
    whereClause += ' AND nationality_name IN ("Canada", "USA")';
  } else if (scope === 'european') {
    // European countries - major hockey nations + established markets
    whereClause += ` AND nationality_name IN (
      "Sweden", "Finland", "Russia", "Czechia", "Switzerland", "Germany",
      "Slovakia", "Austria", "Latvia", "Belarus", "Denmark", "Norway",
      "France", "Slovenia", "Ukraine", "Poland", "Hungary", "Italy",
      "England", "Scotland", "Wales", "Netherlands", "Belgium", "Lithuania",
      "Estonia", "Croatia", "Romania", "Bulgaria", "Serbia", "Iceland"
    )`;
  } else if (scope !== 'worldwide') {
    // Assume it's a country name - capitalize first letter to match data
    const countryName = scope.charAt(0).toUpperCase() + scope.slice(1);
    whereClause += ' AND nationality_name = @country';
    params.country = countryName;
  }

  // Optimized query - only select columns needed for the rankings table
  // Factor columns are included for the expandable breakdown view
  const query = `
    SELECT
      ROW_NUMBER() OVER (ORDER BY total_points DESC) as rank,
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      ROUND(total_points, 2) as total_points,
      ROUND(performance_total, 2) as performance_total,
      ROUND(direct_load_total, 2) as direct_load_total,
      -- Factor columns for expandable breakdown
      ROUND(f01_views, 2) as f01_views,
      ROUND(f02_height, 2) as f02_height,
      ROUND(f03_current_goals_f, 2) as f03_current_goals_f,
      ROUND(f04_current_goals_d, 2) as f04_current_goals_d,
      ROUND(f05_current_assists, 2) as f05_current_assists,
      ROUND(f06_current_gaa, 2) as f06_current_gaa,
      ROUND(f07_current_svp, 2) as f07_current_svp,
      ROUND(f08_last_goals_f, 2) as f08_last_goals_f,
      ROUND(f09_last_goals_d, 2) as f09_last_goals_d,
      ROUND(f10_last_assists, 2) as f10_last_assists,
      ROUND(f11_last_gaa, 2) as f11_last_gaa,
      ROUND(f12_last_svp, 2) as f12_last_svp,
      COALESCE(f13_league_points, 0) as f13_league_points,
      COALESCE(f14_team_points, 0) as f14_team_points,
      ROUND(COALESCE(f15_international_points, 0), 2) as f15_international_points,
      COALESCE(f16_commitment_points, 0) as f16_commitment_points,
      COALESCE(f17_draft_points, 0) as f17_draft_points,
      ROUND(COALESCE(f18_weekly_points_delta, 0), 2) as f18_weekly_points_delta,
      ROUND(COALESCE(f19_weekly_assists_delta, 0), 2) as f19_weekly_assists_delta,
      COALESCE(f20_playing_up_points, 0) as f20_playing_up_points,
      COALESCE(f21_tournament_points, 0) as f21_tournament_points,
      COALESCE(f22_manual_points, 0) as f22_manual_points,
      COALESCE(f23_prodigylikes_points, 0) as f23_prodigylikes_points,
      COALESCE(f24_card_sales_points, 0) as f24_card_sales_points
    FROM \`prodigy-ranking.algorithm_core.player_rankings\`
    ${whereClause}
    ORDER BY total_points DESC
    LIMIT @limit
  `;

  const options = {
    query,
    params
  };

  const rows = await executeQuery(query, options);

  const result = {
    birth_year: birthYear,
    position: position,
    scope: scope,
    count: rows.length,
    players: rows
  };

  setCache(cacheKey, result);
  return result;
}

/**
 * Get metadata for rankings (available years, positions, countries)
 * @returns {Promise<object>} Metadata object
 */
async function getRankingsMetadata() {
  const query = `
    SELECT
      ARRAY_AGG(DISTINCT yearOfBirth ORDER BY yearOfBirth DESC) as birth_years,
      ARRAY_AGG(DISTINCT position ORDER BY position) as positions,
      ARRAY_AGG(DISTINCT nationality_name ORDER BY nationality_name) as countries,
      CURRENT_TIMESTAMP() as exported_at
    FROM \`prodigy-ranking.algorithm_core.player_stats\`
    WHERE yearOfBirth IS NOT NULL
      AND position IS NOT NULL
      AND nationality_name IS NOT NULL
  `;

  const rows = await executeQuery(query);
  return rows[0];
}

/**
 * Get EA Sports-style card ratings for a player
 * @param {number} playerId - Player ID
 * @returns {Promise<object>} Card ratings with 6 categories + overall (0-99 scale)
 */
async function getCardRatings(playerId) {
  // Check cache
  const cacheKey = `cardRatings:${playerId}`;
  const cached = getCached(cacheKey);
  if (cached) {
    console.log(`Cache HIT for card ratings ${playerId}`);
    return cached;
  }

  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      team_country,

      -- Overall and category ratings (0-99 scale)
      overall_rating,
      performance_rating,
      level_rating,
      visibility_rating,
      achievements_rating,
      trending_rating,
      physical_rating,

      -- Compact aliases for card display
      perf,
      lvl,
      vis,
      ach,
      trd,
      phy,

      -- Underlying total points (for context)
      total_points,

      -- Metadata
      ratings_generated_at

    FROM \`prodigy-ranking.algorithm_core.player_card_ratings\`
    WHERE player_id = @playerId
  `;

  const options = {
    query,
    params: { playerId: parseInt(playerId) },
  };

  const rows = await executeQuery(query, options);
  const result = rows.length > 0 ? rows[0] : null;

  if (result) {
    setCache(cacheKey, result);
  }

  return result;
}

/**
 * Get card ratings for multiple players (batch)
 * @param {Array<number>} playerIds - Array of player IDs
 * @returns {Promise<Array>} Array of card ratings
 */
async function getCardRatingsBatch(playerIds) {
  if (!playerIds || playerIds.length === 0) {
    return [];
  }

  // Limit batch size to prevent query timeout
  const limitedIds = playerIds.slice(0, 100);

  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,

      overall_rating,
      performance_rating,
      level_rating,
      visibility_rating,
      achievements_rating,
      trending_rating,
      physical_rating,

      perf, lvl, vis, ach, trd, phy,

      total_points,
      ratings_generated_at

    FROM \`prodigy-ranking.algorithm_core.player_card_ratings\`
    WHERE player_id IN UNNEST(@playerIds)
    ORDER BY overall_rating DESC
  `;

  const options = {
    query,
    params: { playerIds: limitedIds.map(id => parseInt(id)) },
  };

  return await executeQuery(query, options);
}

/**
 * Get top rated players by category or overall
 * @param {string} category - 'overall', 'performance', 'level', 'visibility', 'achievements', 'trending', 'physical'
 * @param {object} filters - Optional filters: { birthYear, position, nationality }
 * @param {number} limit - Max results (default 50)
 * @returns {Promise<Array>} Top rated players
 */
async function getTopRatedPlayers(category = 'overall', filters = {}, limit = 50) {
  const validCategories = ['overall', 'performance', 'level', 'visibility', 'achievements', 'trending', 'physical'];

  if (!validCategories.includes(category)) {
    throw new Error(`Invalid category. Must be one of: ${validCategories.join(', ')}`);
  }

  const orderColumn = category === 'overall' ? 'overall_rating' : `${category}_rating`;

  let whereClause = 'WHERE 1=1';
  const params = { limit: parseInt(limit) };

  if (filters.birthYear) {
    whereClause += ' AND birth_year = @birthYear';
    params.birthYear = parseInt(filters.birthYear);
  }

  if (filters.position) {
    whereClause += ' AND position = @position';
    params.position = filters.position.toUpperCase();
  }

  if (filters.nationality) {
    whereClause += ' AND nationality_name = @nationality';
    params.nationality = filters.nationality;
  }

  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,

      overall_rating,
      performance_rating,
      level_rating,
      visibility_rating,
      achievements_rating,
      trending_rating,
      physical_rating,

      perf, lvl, vis, ach, trd, phy,

      total_points

    FROM \`prodigy-ranking.algorithm_core.player_card_ratings\`
    ${whereClause}
    ORDER BY ${orderColumn} DESC, total_points DESC
    LIMIT @limit
  `;

  const options = { query, params };

  return await executeQuery(query, options);
}

/**
 * Get rating distribution statistics
 * @returns {Promise<object>} Distribution stats
 */
async function getRatingDistribution() {
  const query = `
    SELECT
      -- Overall distribution
      COUNTIF(overall_rating >= 95) as elite_99_95,
      COUNTIF(overall_rating >= 90 AND overall_rating < 95) as stars_90_94,
      COUNTIF(overall_rating >= 80 AND overall_rating < 90) as very_good_80_89,
      COUNTIF(overall_rating >= 70 AND overall_rating < 80) as above_avg_70_79,
      COUNTIF(overall_rating >= 60 AND overall_rating < 70) as average_60_69,
      COUNTIF(overall_rating < 60) as below_avg_under_60,

      -- Averages by category
      ROUND(AVG(overall_rating), 1) as avg_overall,
      ROUND(AVG(performance_rating), 1) as avg_performance,
      ROUND(AVG(level_rating), 1) as avg_level,
      ROUND(AVG(visibility_rating), 1) as avg_visibility,
      ROUND(AVG(achievements_rating), 1) as avg_achievements,
      ROUND(AVG(trending_rating), 1) as avg_trending,
      ROUND(AVG(physical_rating), 1) as avg_physical,

      -- Top ratings
      MAX(overall_rating) as max_overall,
      COUNT(*) as total_players

    FROM \`prodigy-ranking.algorithm_core.player_card_ratings\`
  `;

  const rows = await executeQuery(query);
  return rows[0];
}

/**
 * Get category percentiles for a player
 * Percentiles are calculated within peer group (birth_year + position)
 * @param {number} playerId - Player ID
 * @returns {Promise<object>} Percentiles for 6 categories (0-100 scale)
 */
async function getPlayerPercentiles(playerId) {
  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      team_country,
      ROUND(total_points, 2) as total_points,

      -- Category raw sums
      performance_sum,
      level_sum,
      visibility_sum,
      achievements_sum,
      physical_sum,
      trending_sum,

      -- Percentiles (0-100, where 85 means "top 15%")
      performance_percentile,
      level_percentile,
      visibility_percentile,
      achievements_percentile,
      physical_percentile,
      trending_percentile,
      overall_percentile

    FROM \`prodigy-ranking.algorithm_core.player_category_percentiles\`
    WHERE player_id = @playerId
  `;

  const options = {
    query,
    params: { playerId: parseInt(playerId) },
  };

  const rows = await executeQuery(query, options);
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Get category percentiles for multiple players (batch)
 * @param {Array<number>} playerIds - Array of player IDs
 * @returns {Promise<Array>} Array of percentile data
 */
async function getPlayerPercentilesBatch(playerIds) {
  if (!playerIds || playerIds.length === 0) {
    return [];
  }

  const limitedIds = playerIds.slice(0, 100);

  const query = `
    SELECT
      player_id,
      player_name,
      position,
      birth_year,
      nationality_name,
      current_team,
      current_league,
      ROUND(total_points, 2) as total_points,

      performance_percentile,
      level_percentile,
      visibility_percentile,
      achievements_percentile,
      physical_percentile,
      trending_percentile,
      overall_percentile

    FROM \`prodigy-ranking.algorithm_core.player_category_percentiles\`
    WHERE player_id IN UNNEST(@playerIds)
    ORDER BY total_points DESC
  `;

  const options = {
    query,
    params: { playerIds: limitedIds.map(id => parseInt(id)) },
  };

  return await executeQuery(query, options);
}

/**
 * Get physical data for a player (height, weight, BMI)
 * Returns data in both metric and imperial units for frontend display
 * @param {number} playerId - Player ID
 * @returns {Promise<object>} Physical data with metric/imperial values and BMI
 */
async function getPlayerPhysical(playerId) {
  const query = `
    SELECT
      ps.id as player_id,
      ps.name as player_name,
      ps.position,
      ps.yearOfBirth as birth_year,
      ps.nationality_name,

      -- Metric values (primary)
      ps.height_metrics as height_cm,
      ps.weight_metrics as weight_kg,

      -- Imperial values (display)
      ps.height_imperial as height_display,
      ps.weight_imperial as weight_lbs,

      -- Pre-calculated BMI from PT_F27
      bmi.bmi as bmi,
      -- Calculate BMI category
      CASE
        WHEN bmi.bmi IS NULL THEN NULL
        WHEN bmi.bmi < 18.5 THEN 'Underweight'
        WHEN bmi.bmi < 25 THEN 'Normal'
        WHEN bmi.bmi < 30 THEN 'Overweight'
        ELSE 'Obese'
      END as bmi_category,

      -- Data availability flags
      CASE
        WHEN ps.height_metrics IS NOT NULL AND ps.height_metrics > 0
         AND ps.weight_metrics IS NOT NULL AND ps.weight_metrics > 0
        THEN TRUE
        ELSE FALSE
      END as has_full_data,

      CASE
        WHEN ps.height_metrics IS NOT NULL AND ps.height_metrics > 0 THEN TRUE
        ELSE FALSE
      END as has_height,

      CASE
        WHEN ps.weight_metrics IS NOT NULL AND ps.weight_metrics > 0 THEN TRUE
        ELSE FALSE
      END as has_weight

    FROM \`prodigy-ranking.algorithm.player_stats\` ps
    LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F27_bmi\` bmi
      ON ps.id = bmi.player_id
    WHERE ps.id = @playerId
  `;

  const options = {
    query,
    params: { playerId: parseInt(playerId) },
  };

  const rows = await executeQuery(query, options);

  if (rows.length === 0) {
    return null;
  }

  const row = rows[0];

  // Parse imperial height string (e.g., "6'1\"") to feet and inches
  let feet = null;
  let inches = null;
  if (row.height_display) {
    const match = row.height_display.match(/(\d+)'(\d+)"/);
    if (match) {
      feet = parseInt(match[1]);
      inches = parseInt(match[2]);
    }
  }

  return {
    player_id: row.player_id,
    player_name: row.player_name,
    position: row.position,
    birth_year: row.birth_year,
    nationality: row.nationality_name,

    // Metric (for calculations)
    metric: {
      height_cm: row.height_cm || null,
      weight_kg: row.weight_kg || null
    },

    // Imperial (for display)
    imperial: {
      height_display: row.height_display || null,
      feet: feet,
      inches: inches,
      weight_lbs: row.weight_lbs || null
    },

    // BMI data
    bmi: row.bmi ? parseFloat(row.bmi.toFixed(1)) : null,
    bmi_category: row.bmi_category || null,

    // Data availability
    has_full_data: row.has_full_data,
    has_height: row.has_height,
    has_weight: row.has_weight
  };
}

/**
 * Get season-by-season stats for a player
 * @param {number} playerId - Player ID
 * @param {number} limit - Max seasons to return (default 10)
 * @returns {Promise<Array>} Season stats
 */
async function getPlayerSeasonStats(playerId, limit = 10) {
  const cacheKey = `seasonStats:${playerId}:${limit}`;
  const cached = getCached(cacheKey);
  if (cached) {
    console.log(`Cache HIT for season stats ${playerId}`);
    return cached;
  }

  const query = `
    SELECT
      player_id,
      season_slug as season,
      season_start_year,
      team_name,
      league_name,
      league_level,
      gp as games_played,
      goals,
      assists,
      points,
      plus_minus,
      pim,
      ppg as points_per_game,
      -- Goalie stats
      gaa,
      svp as save_pct,
      wins,
      losses,
      shutouts,
      saves,
      -- Postseason
      has_postseason,
      postseason_gp,
      postseason_goals,
      postseason_assists,
      postseason_points
    FROM \`prodigy-ranking.algorithm_core.player_season_stats\`
    WHERE player_id = @playerId
      AND season_start_year >= 2018
    ORDER BY season_start_year DESC, gp DESC
    LIMIT @limit
  `;

  const options = {
    query,
    params: {
      playerId: parseInt(playerId),
      limit: parseInt(limit)
    },
  };

  const rows = await executeQuery(query, options);

  if (rows.length > 0) {
    setCache(cacheKey, rows);
  }

  return rows;
}

module.exports = {
  bigquery,
  executeQuery,
  getPlayerById,
  searchPlayers,
  getStats,
  getRankings,
  getRankingsMetadata,
  // Card Ratings API
  getCardRatings,
  getCardRatingsBatch,
  getTopRatedPlayers,
  getRatingDistribution,
  // Category Percentiles API
  getPlayerPercentiles,
  getPlayerPercentilesBatch,
  // Physical Data API
  getPlayerPhysical,
  // Season Stats API
  getPlayerSeasonStats
};

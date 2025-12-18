/**
 * BigQuery Connection Utility
 * Shared module for connecting to BigQuery and executing queries
 */

const { BigQuery } = require('@google-cloud/bigquery');

// Initialize BigQuery client
const bigquery = new BigQuery({
  projectId: 'prodigy-ranking',
  // When running locally, credentials will be picked up from GOOGLE_APPLICATION_CREDENTIALS env var
  // When deployed to Cloud Functions, it will use the service account automatically
});

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
 * @param {number} playerId - Player ID
 * @returns {Promise<object>} Player data with world_rank, country_rank, and category percentiles
 */
async function getPlayerById(playerId) {
  // Use a single query with window functions to calculate ranks and percentiles efficiently
  const query = `
    WITH player_data AS (
      SELECT *
      FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
      WHERE player_id = @playerId
    ),
    world_ranks AS (
      SELECT
        player_id,
        ROW_NUMBER() OVER (ORDER BY total_points DESC) as world_rank
      FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
      WHERE birth_year = (SELECT birth_year FROM player_data)
        AND position = (SELECT position FROM player_data)
    ),
    country_ranks AS (
      SELECT
        player_id,
        ROW_NUMBER() OVER (ORDER BY total_points DESC) as country_rank
      FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
      WHERE birth_year = (SELECT birth_year FROM player_data)
        AND position = (SELECT position FROM player_data)
        AND nationality_name = (SELECT nationality_name FROM player_data)
    ),
    percentiles AS (
      SELECT
        player_id,
        performance_percentile,
        level_percentile,
        visibility_percentile,
        achievements_percentile,
        physical_percentile,
        trending_percentile,
        overall_percentile
      FROM \`prodigy-ranking.algorithm_core.player_category_percentiles\`
      WHERE player_id = @playerId
    )
    SELECT
      p.player_id,
      p.player_name,
      p.position,
      p.birth_year,
      p.nationality_name,
      p.current_team,
      p.current_league,
      p.team_country,
      p.current_season,

      ROUND(p.total_points, 2) as total_points,
      ROUND(p.performance_total, 2) as performance_total,
      ROUND(p.direct_load_total, 2) as direct_load_total,

      ROUND(p.f01_views, 2) as f01_views,
      ROUND(p.f02_height, 2) as f02_height,
      ROUND(p.f03_current_goals_f, 2) as f03_current_goals_f,
      ROUND(p.f04_current_goals_d, 2) as f04_current_goals_d,
      ROUND(p.f05_current_assists, 2) as f05_current_assists,
      ROUND(p.f06_current_gaa, 2) as f06_current_gaa,
      ROUND(p.f07_current_svp, 2) as f07_current_svp,
      ROUND(p.f08_last_goals_f, 2) as f08_last_goals_f,
      ROUND(p.f09_last_goals_d, 2) as f09_last_goals_d,
      ROUND(p.f10_last_assists, 2) as f10_last_assists,
      ROUND(p.f11_last_gaa, 2) as f11_last_gaa,
      ROUND(p.f12_last_svp, 2) as f12_last_svp,
      COALESCE(p.f13_league_points, 0) as f13_league_points,
      COALESCE(p.f14_team_points, 0) as f14_team_points,
      ROUND(COALESCE(p.f15_international_points, 0), 2) as f15_international_points,
      COALESCE(p.f16_commitment_points, 0) as f16_commitment_points,
      COALESCE(p.f17_draft_points, 0) as f17_draft_points,
      ROUND(COALESCE(p.f18_weekly_points_delta, 0), 2) as f18_weekly_points_delta,
      ROUND(COALESCE(p.f19_weekly_assists_delta, 0), 2) as f19_weekly_assists_delta,
      COALESCE(p.f20_playing_up_points, 0) as f20_playing_up_points,
      COALESCE(p.f21_tournament_points, 0) as f21_tournament_points,
      COALESCE(p.f22_manual_points, 0) as f22_manual_points,
      COALESCE(p.f23_prodigylikes_points, 0) as f23_prodigylikes_points,
      COALESCE(p.f24_card_sales_points, 0) as f24_card_sales_points,
      ROUND(COALESCE(p.f26_weight_points, 0), 2) as f26_weight_points,
      ROUND(COALESCE(p.f27_bmi_points, 0), 2) as f27_bmi_points,

      p.calculated_at,
      p.algorithm_version,

      -- Pre-calculated ranks
      COALESCE(wr.world_rank, 0) as world_rank,
      COALESCE(cr.country_rank, 0) as country_rank,

      -- Category percentiles (0-100, higher = better within peer group)
      COALESCE(pct.performance_percentile, 0) as performance_percentile,
      COALESCE(pct.level_percentile, 0) as level_percentile,
      COALESCE(pct.visibility_percentile, 0) as visibility_percentile,
      COALESCE(pct.achievements_percentile, 0) as achievements_percentile,
      COALESCE(pct.physical_percentile, 0) as physical_percentile,
      COALESCE(pct.trending_percentile, 0) as trending_percentile,
      COALESCE(pct.overall_percentile, 0) as overall_percentile
    FROM player_data p
    LEFT JOIN world_ranks wr ON p.player_id = wr.player_id
    LEFT JOIN country_ranks cr ON p.player_id = cr.player_id
    LEFT JOIN percentiles pct ON p.player_id = pct.player_id
  `;

  const options = {
    query,
    params: { playerId: parseInt(playerId) },
  };

  const rows = await executeQuery(query, options);
  return rows.length > 0 ? rows[0] : null;
}

/**
 * Search players by name
 * @param {string} searchQuery - Search term
 * @param {number} limit - Maximum results (default 10)
 * @returns {Promise<Array>} Matching players
 */
async function searchPlayers(searchQuery, limit = 10) {
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
    FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
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

  return await executeQuery(query, options);
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
    FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
  `;

  const rows = await executeQuery(query);
  return rows[0];
}

/**
 * Get rankings for a specific birth year, scope, and position
 * @param {number} birthYear - Birth year (2007-2011)
 * @param {string} scope - 'worldwide', 'north_american', or country name
 * @param {string} position - 'F', 'D', or 'G'
 * @param {number} limit - Maximum results (default 250)
 * @returns {Promise<object>} Rankings data
 */
async function getRankings(birthYear, scope, position, limit = 250) {
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
    FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
    ${whereClause}
    ORDER BY total_points DESC
    LIMIT @limit
  `;

  const options = {
    query,
    params
  };

  const rows = await executeQuery(query, options);

  return {
    birth_year: birthYear,
    position: position,
    scope: scope,
    count: rows.length,
    players: rows
  };
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
  return rows.length > 0 ? rows[0] : null;
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
  getPlayerPhysical
};

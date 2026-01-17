/**
 * ProdigyRanking API - Cloud Functions
 * All API endpoints for the ProdigyRanking platform
 */

const functions = require('@google-cloud/functions-framework');
const cors = require('cors');
const {
  getPlayerById,
  searchPlayers: searchPlayersDB,
  getStats: getStatsDB,
  getRankings: getRankingsDB,
  getRankingsMetadata: getRankingsMetadataDB,
  // Card Ratings
  getCardRatings: getCardRatingsDB,
  getCardRatingsBatch: getCardRatingsBatchDB,
  getTopRatedPlayers: getTopRatedPlayersDB,
  getRatingDistribution: getRatingDistributionDB,
  // Category Percentiles
  getPlayerPercentiles: getPlayerPercentilesDB,
  getPlayerPercentilesBatch: getPlayerPercentilesBatchDB,
  // Physical Data
  getPlayerPhysical: getPlayerPhysicalDB,
  getPhysicalBenchmarks: getPhysicalBenchmarksDB,
  // Season Stats
  getPlayerSeasonStats: getPlayerSeasonStatsDB
} = require('./shared/bigquery');

// Enable CORS for all functions
const corsMiddleware = cors({ origin: true });

/**
 * Cache duration settings (in seconds)
 * - Player profiles: 5 minutes (data updates infrequently)
 * - Rankings: 10 minutes (batch data, updates less often)
 * - Metadata/stats: 15 minutes (rarely changes)
 * - Search: 2 minutes (more dynamic)
 */
const CACHE_DURATIONS = {
  player: 300,      // 5 minutes
  rankings: 600,    // 10 minutes
  metadata: 900,    // 15 minutes
  search: 120,      // 2 minutes
  batch: 300,       // 5 minutes
  default: 300      // 5 minutes
};

/**
 * Set cache headers on response
 * @param {object} res - Response object
 * @param {string} cacheType - Type of cache duration to use
 */
function setCacheHeaders(res, cacheType = 'default') {
  const maxAge = CACHE_DURATIONS[cacheType] || CACHE_DURATIONS.default;
  res.set('Cache-Control', `public, max-age=${maxAge}, s-maxage=${maxAge}`);
  res.set('Vary', 'Accept-Encoding');
}

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
  // Don't cache errors
  res.set('Cache-Control', 'no-store');
  return res.status(statusCode).json({
    error: message,
    timestamp: new Date().toISOString()
  });
}

/**
 * GET /api/player/:player_id
 * Get single player by ID
 */
functions.http('getPlayer', withCors(async (req, res) => {
  try {
    const playerId = req.params.player_id || req.query.player_id;

    if (!playerId) {
      return errorResponse(res, 400, 'player_id is required');
    }

    const player = await getPlayerById(playerId);

    if (!player) {
      return errorResponse(res, 404, `Player ${playerId} not found`);
    }

    setCacheHeaders(res, 'player');
    res.json(player);
  } catch (error) {
    console.error('Error in getPlayer:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/player/:player_id/stats
 * Get season-by-season stats for a player
 */
functions.http('getPlayerStats', withCors(async (req, res) => {
  try {
    const playerId = req.params.player_id || req.query.player_id;
    const limit = parseInt(req.query.limit) || 10;

    if (!playerId) {
      return errorResponse(res, 400, 'player_id is required');
    }

    const stats = await getPlayerSeasonStatsDB(playerId, limit);

    setCacheHeaders(res, 'player');
    res.json({
      player_id: parseInt(playerId),
      count: stats.length,
      seasons: stats
    });
  } catch (error) {
    console.error('Error in getPlayerStats:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/search?q=:query&limit=10
 * Search players by name
 */
functions.http('searchPlayers', withCors(async (req, res) => {
  try {
    const query = req.query.q;
    const limit = req.query.limit || 10;

    if (!query) {
      return errorResponse(res, 400, 'query parameter "q" is required');
    }

    if (query.length < 2) {
      return errorResponse(res, 400, 'query must be at least 2 characters');
    }

    const players = await searchPlayersDB(query, limit);

    setCacheHeaders(res, 'search');
    res.json({
      query,
      count: players.length,
      players
    });
  } catch (error) {
    console.error('Error in searchPlayers:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/stats
 * Get homepage statistics
 */
functions.http('getStats', withCors(async (req, res) => {
  try {
    const stats = await getStatsDB();

    setCacheHeaders(res, 'metadata');
    res.json({
      totalPlayers: parseInt(stats.total_players),
      totalLeagues: parseInt(stats.total_leagues),
      totalCountries: parseInt(stats.total_countries),
      lastUpdated: stats.last_updated
    });
  } catch (error) {
    console.error('Error in getStats:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/rankings/:birthYear/:scope/:position
 * Get rankings for specific birth year, scope, and position
 *
 * Examples:
 * - /api/rankings/2009/worldwide/F
 * - /api/rankings/2009/north_american/D
 * - /api/rankings/2009/canada/G
 */
functions.http('getRankings', withCors(async (req, res) => {
  try {
    // Extract parameters from path (Cloud Functions with HTTP trigger)
    const pathParts = req.path.split('/').filter(p => p);

    const birthYear = pathParts[0] || req.params.birthYear || req.query.birthYear;
    const scope = pathParts[1] || req.params.scope || req.query.scope;
    const position = pathParts[2] || req.params.position || req.query.position;
    const limit = req.query.limit || 250;

    // Validation
    if (!birthYear || !scope || !position) {
      return errorResponse(res, 400, 'birthYear, scope, and position are required');
    }

    const year = parseInt(birthYear);
    if (isNaN(year) || year < 2007 || year > 2011) {
      return errorResponse(res, 400, 'birthYear must be between 2007 and 2011');
    }

    const validPositions = ['F', 'D', 'G'];
    const pos = position.toUpperCase();
    if (!validPositions.includes(pos)) {
      return errorResponse(res, 400, 'position must be F, D, or G');
    }

    const rankings = await getRankingsDB(year, scope, pos, limit);

    setCacheHeaders(res, 'rankings');
    res.json(rankings);
  } catch (error) {
    console.error('Error in getRankings:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/rankings/metadata
 * Get available years, positions, and countries
 */
functions.http('getRankingsMetadata', withCors(async (req, res) => {
  try {
    const metadata = await getRankingsMetadataDB();

    setCacheHeaders(res, 'metadata');
    res.json({
      exported_at: metadata.exported_at,
      birth_years: metadata.birth_years,
      positions: metadata.positions,
      countries: metadata.countries
    });
  } catch (error) {
    console.error('Error in getRankingsMetadata:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

// =====================================================================
// CARD RATINGS API (EA Sports-style 0-99 ratings)
// =====================================================================

/**
 * GET /api/card-ratings/:player_id
 * Get EA Sports-style card ratings for a single player
 *
 * Response includes:
 * - overall_rating (0-99)
 * - 6 category ratings: performance, level, visibility, achievements, trending, physical
 * - Compact aliases: perf, lvl, vis, ach, trd, phy
 */
functions.http('getCardRatings', withCors(async (req, res) => {
  try {
    const playerId = req.params.player_id || req.query.player_id;

    if (!playerId) {
      return errorResponse(res, 400, 'player_id is required');
    }

    const ratings = await getCardRatingsDB(playerId);

    if (!ratings) {
      return errorResponse(res, 404, `Card ratings not found for player ${playerId}`);
    }

    // Format response for frontend card display
    setCacheHeaders(res, 'player');
    res.json({
      player_id: ratings.player_id,
      player_name: ratings.player_name,
      position: ratings.position,
      birth_year: ratings.birth_year,
      nationality: ratings.nationality_name,
      team: ratings.current_team,
      league: ratings.current_league,

      // Primary rating (big number on card)
      overall: ratings.overall_rating,

      // Category ratings for radar chart / bars
      ratings: {
        performance: ratings.performance_rating,
        level: ratings.level_rating,
        visibility: ratings.visibility_rating,
        achievements: ratings.achievements_rating,
        trending: ratings.trending_rating,
        physical: ratings.physical_rating
      },

      // Compact format for card display
      compact: {
        ovr: ratings.overall_rating,
        perf: ratings.perf,
        lvl: ratings.lvl,
        vis: ratings.vis,
        ach: ratings.ach,
        trd: ratings.trd,
        phy: ratings.phy
      },

      // Metadata
      total_points: ratings.total_points,
      generated_at: ratings.ratings_generated_at
    });
  } catch (error) {
    console.error('Error in getCardRatings:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * POST /api/card-ratings/batch
 * Get card ratings for multiple players at once
 *
 * Body: { "player_ids": [123, 456, 789] }
 * Max 100 players per request
 */
functions.http('getCardRatingsBatch', withCors(async (req, res) => {
  try {
    // Support both GET with query param and POST with body
    let playerIds;

    if (req.method === 'POST' && req.body && req.body.player_ids) {
      playerIds = req.body.player_ids;
    } else if (req.query.player_ids) {
      // Parse comma-separated IDs from query string
      playerIds = req.query.player_ids.split(',').map(id => parseInt(id.trim()));
    } else {
      return errorResponse(res, 400, 'player_ids is required (POST body or comma-separated query param)');
    }

    if (!Array.isArray(playerIds) || playerIds.length === 0) {
      return errorResponse(res, 400, 'player_ids must be a non-empty array');
    }

    if (playerIds.length > 100) {
      return errorResponse(res, 400, 'Maximum 100 player_ids per request');
    }

    const ratings = await getCardRatingsBatchDB(playerIds);

    setCacheHeaders(res, 'batch');
    res.json({
      count: ratings.length,
      players: ratings.map(r => ({
        player_id: r.player_id,
        player_name: r.player_name,
        position: r.position,
        birth_year: r.birth_year,
        nationality: r.nationality_name,
        team: r.current_team,
        overall: r.overall_rating,
        compact: {
          ovr: r.overall_rating,
          perf: r.perf,
          lvl: r.lvl,
          vis: r.vis,
          ach: r.ach,
          trd: r.trd,
          phy: r.phy
        }
      }))
    });
  } catch (error) {
    console.error('Error in getCardRatingsBatch:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/card-ratings/top
 * Get top rated players, optionally filtered and sorted by category
 *
 * Query params:
 * - category: 'overall' (default), 'performance', 'level', 'visibility', 'achievements', 'trending', 'physical'
 * - birthYear: 2007-2011
 * - position: F, D, or G
 * - nationality: country name
 * - limit: 1-100 (default 50)
 */
functions.http('getTopRatedPlayers', withCors(async (req, res) => {
  try {
    const category = req.query.category || 'overall';
    const limit = Math.min(parseInt(req.query.limit) || 50, 100);

    const filters = {};
    if (req.query.birthYear) filters.birthYear = req.query.birthYear;
    if (req.query.position) filters.position = req.query.position;
    if (req.query.nationality) filters.nationality = req.query.nationality;

    const players = await getTopRatedPlayersDB(category, filters, limit);

    setCacheHeaders(res, 'rankings');
    res.json({
      category,
      filters,
      count: players.length,
      players: players.map(r => ({
        player_id: r.player_id,
        player_name: r.player_name,
        position: r.position,
        birth_year: r.birth_year,
        nationality: r.nationality_name,
        team: r.current_team,
        league: r.current_league,
        overall: r.overall_rating,
        ratings: {
          performance: r.performance_rating,
          level: r.level_rating,
          visibility: r.visibility_rating,
          achievements: r.achievements_rating,
          trending: r.trending_rating,
          physical: r.physical_rating
        },
        compact: {
          ovr: r.overall_rating,
          perf: r.perf,
          lvl: r.lvl,
          vis: r.vis,
          ach: r.ach,
          trd: r.trd,
          phy: r.phy
        }
      }))
    });
  } catch (error) {
    console.error('Error in getTopRatedPlayers:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/card-ratings/distribution
 * Get rating distribution statistics (for admin/analytics)
 */
functions.http('getRatingDistribution', withCors(async (req, res) => {
  try {
    const stats = await getRatingDistributionDB();

    setCacheHeaders(res, 'metadata');
    res.json({
      distribution: {
        elite_95_99: parseInt(stats.elite_99_95),
        stars_90_94: parseInt(stats.stars_90_94),
        very_good_80_89: parseInt(stats.very_good_80_89),
        above_avg_70_79: parseInt(stats.above_avg_70_79),
        average_60_69: parseInt(stats.average_60_69),
        below_avg_under_60: parseInt(stats.below_avg_under_60)
      },
      averages: {
        overall: parseFloat(stats.avg_overall),
        performance: parseFloat(stats.avg_performance),
        level: parseFloat(stats.avg_level),
        visibility: parseFloat(stats.avg_visibility),
        achievements: parseFloat(stats.avg_achievements),
        trending: parseFloat(stats.avg_trending),
        physical: parseFloat(stats.avg_physical)
      },
      max_overall: parseInt(stats.max_overall),
      total_players: parseInt(stats.total_players)
    });
  } catch (error) {
    console.error('Error in getRatingDistribution:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

// =====================================================================
// CATEGORY PERCENTILES API
// =====================================================================

/**
 * GET /api/percentiles/:player_id
 * Get category percentiles for a single player (within birth_year + position peer group)
 *
 * Response includes percentiles for 6 categories (0-100 scale):
 * - performance_percentile: 85 means "top 15%" in performance
 * - level_percentile: 72 means "top 28%" in level
 * - visibility_percentile: 94 means "top 6%" in visibility
 * - achievements_percentile: 68 means "top 32%" in achievements
 * - physical_percentile: 55 means "top 45%" in physical
 * - trending_percentile: 91 means "top 9%" in trending
 */
functions.http('getPlayerPercentiles', withCors(async (req, res) => {
  try {
    const playerId = req.params.player_id || req.query.player_id;

    if (!playerId) {
      return errorResponse(res, 400, 'player_id is required');
    }

    const percentiles = await getPlayerPercentilesDB(playerId);

    if (!percentiles) {
      return errorResponse(res, 404, `Percentiles not found for player ${playerId}`);
    }

    // Format response for frontend
    setCacheHeaders(res, 'player');
    res.json({
      player_id: percentiles.player_id,
      player_name: percentiles.player_name,
      position: percentiles.position,
      birth_year: percentiles.birth_year,
      nationality: percentiles.nationality_name,
      team: percentiles.current_team,
      league: percentiles.current_league,
      total_points: percentiles.total_points,

      // Percentiles (0-100, higher = better ranking within peer group)
      percentiles: {
        performance: percentiles.performance_percentile,
        level: percentiles.level_percentile,
        visibility: percentiles.visibility_percentile,
        achievements: percentiles.achievements_percentile,
        physical: percentiles.physical_percentile,
        trending: percentiles.trending_percentile,
        overall: percentiles.overall_percentile
      },

      // Category raw sums (for context)
      category_sums: {
        performance: percentiles.performance_sum,
        level: percentiles.level_sum,
        visibility: percentiles.visibility_sum,
        achievements: percentiles.achievements_sum,
        physical: percentiles.physical_sum,
        trending: percentiles.trending_sum
      },

      // Compact format for quick access
      pct: {
        perf: percentiles.performance_percentile,
        lvl: percentiles.level_percentile,
        vis: percentiles.visibility_percentile,
        ach: percentiles.achievements_percentile,
        phy: percentiles.physical_percentile,
        trd: percentiles.trending_percentile,
        ovr: percentiles.overall_percentile
      }
    });
  } catch (error) {
    console.error('Error in getPlayerPercentiles:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * POST /api/percentiles/batch
 * Get category percentiles for multiple players at once
 *
 * Body: { "player_ids": [123, 456, 789] }
 * Max 100 players per request
 */
functions.http('getPlayerPercentilesBatch', withCors(async (req, res) => {
  try {
    let playerIds;

    if (req.method === 'POST' && req.body && req.body.player_ids) {
      playerIds = req.body.player_ids;
    } else if (req.query.player_ids) {
      playerIds = req.query.player_ids.split(',').map(id => parseInt(id.trim()));
    } else {
      return errorResponse(res, 400, 'player_ids is required (POST body or comma-separated query param)');
    }

    if (!Array.isArray(playerIds) || playerIds.length === 0) {
      return errorResponse(res, 400, 'player_ids must be a non-empty array');
    }

    if (playerIds.length > 100) {
      return errorResponse(res, 400, 'Maximum 100 player_ids per request');
    }

    const percentiles = await getPlayerPercentilesBatchDB(playerIds);

    setCacheHeaders(res, 'batch');
    res.json({
      count: percentiles.length,
      players: percentiles.map(p => ({
        player_id: p.player_id,
        player_name: p.player_name,
        position: p.position,
        birth_year: p.birth_year,
        nationality: p.nationality_name,
        team: p.current_team,
        total_points: p.total_points,
        percentiles: {
          performance: p.performance_percentile,
          level: p.level_percentile,
          visibility: p.visibility_percentile,
          achievements: p.achievements_percentile,
          physical: p.physical_percentile,
          trending: p.trending_percentile,
          overall: p.overall_percentile
        },
        pct: {
          perf: p.performance_percentile,
          lvl: p.level_percentile,
          vis: p.visibility_percentile,
          ach: p.achievements_percentile,
          phy: p.physical_percentile,
          trd: p.trending_percentile,
          ovr: p.overall_percentile
        }
      }))
    });
  } catch (error) {
    console.error('Error in getPlayerPercentilesBatch:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

// =====================================================================
// PHYSICAL DATA API (Height, Weight, BMI for Player Profile)
// =====================================================================

/**
 * GET /api/physical/:player_id
 * Get physical data for a player (height, weight, BMI)
 *
 * Returns data in both metric and imperial formats for frontend display.
 * Used by the PlayerGraphic component to render the body model visualization.
 *
 * Response includes:
 * - metric: { height_cm, weight_kg }
 * - imperial: { height_display, feet, inches, weight_lbs }
 * - bmi: calculated BMI value
 * - bmi_category: Underweight/Normal/Overweight/Obese
 * - has_full_data: boolean - whether both height and weight are available
 */
functions.http('getPlayerPhysical', withCors(async (req, res) => {
  try {
    const playerId = req.params.player_id || req.query.player_id;

    if (!playerId) {
      return errorResponse(res, 400, 'player_id is required');
    }

    const physical = await getPlayerPhysicalDB(playerId);

    if (!physical) {
      return errorResponse(res, 404, `Player ${playerId} not found`);
    }

    // Return structured response for frontend consumption
    setCacheHeaders(res, 'player');
    res.json({
      player_id: physical.player_id,
      player_name: physical.player_name,
      position: physical.position,
      birth_year: physical.birth_year,
      nationality: physical.nationality,

      // Metric values (for BMI calculations)
      metric: physical.metric,

      // Imperial values (for display based on user preference)
      imperial: physical.imperial,

      // BMI data
      bmi: physical.bmi,
      bmi_category: physical.bmi_category,

      // Data availability flags
      has_full_data: physical.has_full_data,
      has_height: physical.has_height,
      has_weight: physical.has_weight,

      // Message for frontend display
      data_status: physical.has_full_data
        ? 'complete'
        : physical.has_height && !physical.has_weight
          ? 'missing_weight'
          : !physical.has_height && physical.has_weight
            ? 'missing_height'
            : 'no_data'
    });
  } catch (error) {
    console.error('Error in getPlayerPhysical:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /api/physical/benchmarks
 * Get physical benchmarks (height, weight, BMI) by birth year and position
 *
 * Returns real player averages from the database for the BMI comparison tool.
 * Data is grouped by birth year (2007-2011) and position (F, D, G).
 *
 * Response includes:
 * - avg_height, height_p25, height_p75 (25th-75th percentile range)
 * - avg_weight, weight_p25, weight_p75
 * - avg_bmi, bmi_p25, bmi_p75
 * - sample_size: number of players with valid physical data
 *
 * The BMI tool uses height_p25-p75 as the "average range" for comparison.
 */
functions.http('getPhysicalBenchmarks', withCors(async (req, res) => {
  try {
    const benchmarks = await getPhysicalBenchmarksDB();

    // Transform into a more frontend-friendly structure
    // Organized by birth year -> position
    const byYearAndPosition = {};

    for (const row of benchmarks) {
      const year = row.birth_year;
      const pos = row.position.toLowerCase();  // 'f', 'd', 'g'

      if (!byYearAndPosition[year]) {
        byYearAndPosition[year] = {};
      }

      byYearAndPosition[year][pos] = {
        sample_size: row.sample_size,
        height: {
          avg: row.avg_height,
          range: [row.height_p25, row.height_p75],
          min: row.height_min,
          max: row.height_max
        },
        weight: {
          avg: row.avg_weight,
          range: [row.weight_p25, row.weight_p75],
          min: row.weight_min,
          max: row.weight_max
        },
        bmi: {
          avg: row.avg_bmi,
          range: [row.bmi_p25, row.bmi_p75]
        }
      };
    }

    // Map birth years to age categories for the BMI tool
    // Based on 2025-2026 season: U14 = 2012, U15 = 2011, U16 = 2010, etc.
    const ageCategoryMapping = {
      2012: 'U14',
      2011: 'U15',
      2010: 'U16',
      2009: 'U17',
      2008: 'U18',
      2007: 'U19',
      2006: 'U20'
    };

    // Position mapping from API (f, d, g) to frontend (forward, defender, goalie)
    const positionMapping = {
      'f': 'forward',
      'd': 'defender',
      'g': 'goalie'
    };

    // Also provide data keyed by age category for easier frontend use
    // Uses full position names to match frontend expectations
    const byAgeCategory = {};
    for (const [year, positions] of Object.entries(byYearAndPosition)) {
      const ageCategory = ageCategoryMapping[year];
      if (ageCategory) {
        byAgeCategory[ageCategory] = {};
        for (const [posKey, data] of Object.entries(positions)) {
          const fullPosName = positionMapping[posKey] || posKey;
          byAgeCategory[ageCategory][fullPosName] = data;
        }
      }
    }

    setCacheHeaders(res, 'metadata');
    res.json({
      by_birth_year: byYearAndPosition,
      by_age_category: byAgeCategory,
      age_category_mapping: ageCategoryMapping,
      total_benchmarks: benchmarks.length,
      generated_at: new Date().toISOString()
    });
  } catch (error) {
    console.error('Error in getPhysicalBenchmarks:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

// Import marketplace functions to register them
require('./marketplace');

// Import admin functions to register them
require('./admin');

// Import blurbs functions to register them
require('./blurbs');

// Import AI blurbs functions to register them
require('./ai-blurbs');

// Import sync function for Cloud Scheduler
const { syncRankings } = require('./sync');
functions.http('syncRankings', syncRankings);

// Import Stripe payment functions
require('./stripe');

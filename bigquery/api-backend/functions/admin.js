/**
 * ProdigyRanking Admin API - Cloud Functions
 * Endpoints for the admin portal to monitor algorithm health and data
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

/**
 * GET /admin/health
 * Get overall health metrics for the algorithm
 */
functions.http('adminGetHealth', withCors(async (req, res) => {
  try {
    const query = `
      SELECT
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.player_stats\`) as total_players,
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.player_rankings\`) as ranked_players,
        (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.player_rankings\`) as last_algorithm_run,
        (SELECT MAX(loadts) FROM \`prodigy-ranking.algorithm_core.player_stats\`) as last_data_load,
        'v2.4' as algorithm_version
    `;

    const rows = await executeQuery(query);
    const data = rows[0];

    res.json({
      totalPlayers: parseInt(data.total_players) || 0,
      rankedPlayers: parseInt(data.ranked_players) || 0,
      lastAlgorithmRun: data.last_algorithm_run ? data.last_algorithm_run.value : new Date().toISOString(),
      lastDataLoad: data.last_data_load ? data.last_data_load.value : new Date().toISOString(),
      algorithmVersion: data.algorithm_version
    });
  } catch (error) {
    console.error('Error in adminGetHealth:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /admin/factors
 * Get status of all factor tables (35 factors total: F01-F28 ranking + F31-F37 rating)
 * Updated: 2026-01-19 per NEW ALGORITHM CSV
 */
functions.http('adminGetFactors', withCors(async (req, res) => {
  try {
    // Inactive factors list (per algorithm spec 2026-01-19)
    const inactiveFactors = ['F14', 'F20', 'F21', 'F22', 'F23', 'F24'];

    // Query each factor table for row count and last calculated timestamp
    const query = `
      WITH factor_stats AS (
        -- F01: EP Views (max 2000)
        SELECT 'PT_F01_EPV' as table_name, 'F01' as factor_id, 'elite prospects views' as factor_name,
          'F01 EPV: 2000 pts linear from 100-29900 views' as description,
          2000 as max_points,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as row_count,
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as last_calculated,
          (SELECT MIN(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as min_points,
          (SELECT MAX(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as max_points_actual,
          (SELECT AVG(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as avg_points
        UNION ALL
        -- F02: Height (max 200)
        SELECT 'PT_F02_H', 'F02', 'height', 'F02 H: 200 pts by position/birth year standards',
          200,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MIN(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MAX(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT AVG(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`)
        UNION ALL
        -- F03: Current Season GPG Forwards (max 500)
        SELECT 'PT_F03_CGPGF', 'F03', 'current season goals per game forwards', 'F03 CSGPGF: 500 pts linear 0-2.0 GPG',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MIN(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MAX(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT AVG(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`)
        UNION ALL
        -- F04: Current Season GPG Defenders (max 500)
        SELECT 'PT_F04_CGPGD', 'F04', 'current season goals per game defenders', 'F04 CSGPGD: 500 pts linear 0-1.5 GPG',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MIN(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MAX(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT AVG(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`)
        UNION ALL
        -- F05: Current Season APG (max 500)
        SELECT 'PT_F05_CAPG', 'F05', 'current season assists per game', 'F05 CSAPG: 500 pts linear 0-2.5 APG',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MIN(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MAX(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT AVG(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`)
        UNION ALL
        -- F06: Current Season GAA (max 500)
        SELECT 'PT_F06_CGAA', 'F06', 'current season goals against average', 'F06 CSGAA: 500 pts inverse linear 0-3.5 GAA',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MIN(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MAX(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT AVG(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`)
        UNION ALL
        -- F07: Current Season Save % (max 300)
        SELECT 'PT_F07_CSV', 'F07', 'current season save percentage', 'F07 CSSP: 300 pts linear .699-1.000 SV%',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MIN(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MAX(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT AVG(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`)
        UNION ALL
        -- F08: Past Season GPG Forwards (max 300)
        SELECT 'PT_F08_LGPGF', 'F08', 'past season goals per game forwards', 'F08 PSGPGF: 300 pts linear 0-2.0 GPG',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MIN(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MAX(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT AVG(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`)
        UNION ALL
        -- F09: Past Season GPG Defenders (max 300)
        SELECT 'PT_F09_LGPGD', 'F09', 'past season goals per game defenders', 'F09 PSGPGD: 300 pts linear 0-1.5 GPG',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MIN(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MAX(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT AVG(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`)
        UNION ALL
        -- F10: Past Season APG (max 300)
        SELECT 'PT_F10_LAPG', 'F10', 'past season assists per game', 'F10 PSAPG: 300 pts linear 0-2.5 APG',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MIN(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MAX(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT AVG(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`)
        UNION ALL
        -- F11: Past Season GAA (max 300)
        SELECT 'PT_F11_LGAA', 'F11', 'past season goals against average', 'F11 PSGAA: 300 pts inverse linear 0-3.5 GAA',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MIN(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MAX(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT AVG(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`)
        UNION ALL
        -- F12: Past Season Save % (max 200)
        SELECT 'PT_F12_LSV', 'F12', 'past season save percentage', 'F12 PSSP: 200 pts linear .699-1.000 SV%',
          200,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MIN(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MAX(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT AVG(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`)
        UNION ALL
        -- F13: League Points (max 4500) - Uses DL_all_leagues table
        SELECT 'DL_all_leagues', 'F13', 'league points', 'F13 LP: max 4500 by tier',
          4500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_all_leagues\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(league_points) FROM \`prodigy-ranking.algorithm_core.DL_all_leagues\`),
          (SELECT MAX(league_points) FROM \`prodigy-ranking.algorithm_core.DL_all_leagues\`),
          (SELECT AVG(league_points) FROM \`prodigy-ranking.algorithm_core.DL_all_leagues\`)
        UNION ALL
        -- F14: Team Points (max 700) - INACTIVE
        SELECT 'DL_F14_team_points', 'F14', 'team points', 'F14 TP: max 700 (INACTIVE - no teams table)',
          700,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MAX(imported_at) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`)
        UNION ALL
        -- F15: International Selection Points (max 1000)
        SELECT 'DL_F15_international_points_final', 'F15', 'international selection points', 'F15 IP: max 1000',
          1000,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          (SELECT MAX(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          (SELECT AVG(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`)
        UNION ALL
        -- F16: Commitment Points (max 500)
        SELECT 'PT_F16_CP', 'F16', 'commitment points', 'F16 CP: max 500',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          (SELECT MAX(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          (SELECT AVG(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`)
        UNION ALL
        -- F17: Draft Points (max 300)
        SELECT 'DL_F17_draft_points', 'F17', 'draft points', 'F17 DP: max 300',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`)
        UNION ALL
        -- F18: Weekly Points Goals (max 200 cap, 40 per goal)
        SELECT 'PT_F18_weekly_points_delta', 'F18', 'weekly points - goal', 'F18 WPG: 40pts/goal, max 200',
          200,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          (SELECT MAX(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          (SELECT AVG(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`)
        UNION ALL
        -- F19: Weekly Points Assists (max 125 cap, 25 per assist)
        SELECT 'PT_F19_weekly_assists_delta', 'F19', 'weekly points - assist', 'F19 WPA: 25pts/assist, max 125',
          125,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          (SELECT MAX(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          (SELECT AVG(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`)
        UNION ALL
        -- F20: Playing Up Category (max 300) - INACTIVE
        SELECT 'DL_F20_playing_up_points', 'F20', 'playing up category', 'F20 PUC: max 300 (INACTIVE)',
          300,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`)
        UNION ALL
        -- F21: Tournament Accolades - INACTIVE
        SELECT 'DL_F21_tournament_points', 'F21', 'tournament accolades', 'F21 TA: (INACTIVE)',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`)
        UNION ALL
        -- F22: Extra Manual Points - INACTIVE
        SELECT 'DL_F22_manual_points', 'F22', 'extra manual points', 'F22 EMP: (INACTIVE)',
          0,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`)
        UNION ALL
        -- F23: ProdigyChain Likes/Views - INACTIVE
        SELECT 'DL_F23_prodigylikes_points', 'F23', 'prodigychain likes / views', 'F23 PCL: max 500 (INACTIVE)',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`)
        UNION ALL
        -- F24: ProdigyChain Card Sales - INACTIVE
        SELECT 'DL_F24_card_sales_points', 'F24', 'prodigychain card sales', 'F24 PCCS: max 500 (INACTIVE)',
          500,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`)
        UNION ALL
        -- F25: Weekly Points EP Views (max 200)
        SELECT 'PT_F25_weekly_views_delta', 'F25', 'weekly points - EP views', 'F25 WPEPV: max 200',
          200,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_25_points) FROM \`prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta\`),
          (SELECT MAX(factor_25_points) FROM \`prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta\`),
          (SELECT AVG(factor_25_points) FROM \`prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta\`)
        UNION ALL
        -- F26: Weight (max 150)
        SELECT 'PT_F26_weight', 'F26', 'weight', 'F26 W: max 150 by position/birth year',
          150,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          (SELECT MAX(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          (SELECT AVG(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`)
        UNION ALL
        -- F27: BMI (max 250)
        SELECT 'PT_F27_bmi', 'F27', 'BMI', 'F27 BMI: max 250 by position/birth year',
          250,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          (SELECT MAX(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          (SELECT AVG(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`)
        UNION ALL
        -- F28: NHL Scouting Report (max 1000, min 500)
        SELECT 'PT_F28_NHLSR', 'F28', 'NHL Scouting Report', 'NHL Central Scouting: 500-1000 pts linear by rank',
          1000,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F28_NHLSR\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_28_nhl_scouting_points) FROM \`prodigy-ranking.algorithm_core.PT_F28_NHLSR\`),
          (SELECT MAX(factor_28_nhl_scouting_points) FROM \`prodigy-ranking.algorithm_core.PT_F28_NHLSR\`),
          (SELECT AVG(factor_28_nhl_scouting_points) FROM \`prodigy-ranking.algorithm_core.PT_F28_NHLSR\`)
      )
      SELECT
        table_name as tableName,
        factor_id as factorId,
        factor_name as factorName,
        description,
        max_points as maxPointsConfig,
        row_count as rowCount,
        last_calculated as lastCalculated,
        COALESCE(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR), 999) as hoursSinceCalc,
        CASE
          WHEN last_calculated IS NULL THEN 'stale'
          WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR) < 24 THEN 'fresh'
          WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR) < 168 THEN 'stale'
          ELSE 'critical'
        END as dataStatus,
        ROUND(COALESCE(min_points, 0), 2) as minPoints,
        ROUND(COALESCE(max_points_actual, 0), 2) as maxPoints,
        ROUND(COALESCE(avg_points, 0), 2) as avgPoints
      FROM factor_stats
      ORDER BY factor_id
    `;

    const rows = await executeQuery(query);

    // Get total players for coverage calculation
    const countQuery = `SELECT COUNT(*) as total FROM \`prodigy-ranking.algorithm_core.player_rankings\``;
    const countRows = await executeQuery(countQuery);
    const totalPlayers = parseInt(countRows[0].total) || 1;

    // Map ranking factors (F01-F28)
    const rankingFactors = rows.map(row => ({
      tableName: row.tableName,
      factorId: row.factorId,
      factorName: row.factorName,
      description: row.description,
      maxPointsConfig: parseInt(row.maxPointsConfig) || 0,
      rowCount: parseInt(row.rowCount) || 0,
      lastCalculated: row.lastCalculated ? row.lastCalculated.value : new Date().toISOString(),
      hoursSinceCalc: parseInt(row.hoursSinceCalc) || 0,
      status: row.dataStatus,  // Always use dataStatus (fresh/stale/critical) - isActive flag handles inactive state
      isActive: !inactiveFactors.includes(row.factorId),
      coverage: Math.round((parseInt(row.rowCount) / totalPlayers) * 1000) / 10,
      minPoints: parseFloat(row.minPoints) || 0,
      maxPoints: parseFloat(row.maxPoints) || 0,
      avgPoints: parseFloat(row.avgPoints) || 0,
      factorType: 'ranking'
    }));

    // Query actual statistics for Rating Factors (F31-F37) from player_card_ratings view
    const ratingStatsQuery = `
      SELECT
        COUNT(*) as total_count,
        MIN(performance_rating) as min_f31, MAX(performance_rating) as max_f31, AVG(performance_rating) as avg_f31,
        COUNTIF(performance_rating IS NOT NULL AND performance_rating > 0) as count_f31,
        MIN(level_rating) as min_f32, MAX(level_rating) as max_f32, AVG(level_rating) as avg_f32,
        COUNTIF(level_rating IS NOT NULL AND level_rating > 0) as count_f32,
        MIN(visibility_rating) as min_f33, MAX(visibility_rating) as max_f33, AVG(visibility_rating) as avg_f33,
        COUNTIF(visibility_rating IS NOT NULL AND visibility_rating > 0) as count_f33,
        MIN(physical_rating) as min_f34, MAX(physical_rating) as max_f34, AVG(physical_rating) as avg_f34,
        COUNTIF(physical_rating IS NOT NULL AND physical_rating > 0) as count_f34,
        MIN(achievements_rating) as min_f35, MAX(achievements_rating) as max_f35, AVG(achievements_rating) as avg_f35,
        COUNTIF(achievements_rating IS NOT NULL AND achievements_rating > 0) as count_f35,
        MIN(trending_rating) as min_f36, MAX(trending_rating) as max_f36, AVG(trending_rating) as avg_f36,
        COUNTIF(trending_rating IS NOT NULL AND trending_rating > 0) as count_f36,
        MIN(overall_rating) as min_f37, MAX(overall_rating) as max_f37, AVG(overall_rating) as avg_f37,
        COUNTIF(overall_rating IS NOT NULL AND overall_rating > 0) as count_f37
      FROM \`prodigy-ranking.algorithm_core.player_card_ratings\`
    `;

    let ratingStats = {
      total_count: totalPlayers,
      min_f31: 0, max_f31: 99, avg_f31: 50, count_f31: totalPlayers,
      min_f32: 0, max_f32: 99, avg_f32: 50, count_f32: totalPlayers,
      min_f33: 0, max_f33: 99, avg_f33: 50, count_f33: totalPlayers,
      min_f34: 0, max_f34: 99, avg_f34: 50, count_f34: totalPlayers,
      min_f35: 0, max_f35: 99, avg_f35: 50, count_f35: totalPlayers,
      min_f36: 0, max_f36: 99, avg_f36: 50, count_f36: totalPlayers,
      min_f37: 0, max_f37: 99, avg_f37: 50, count_f37: totalPlayers
    };

    try {
      const ratingStatsRows = await executeQuery(ratingStatsQuery);
      if (ratingStatsRows && ratingStatsRows.length > 0) {
        ratingStats = ratingStatsRows[0];
      }
    } catch (ratingErr) {
      console.warn('Could not fetch rating factor stats, using defaults:', ratingErr.message);
    }

    const ratingFactors = [
      {
        tableName: 'player_card_ratings',
        factorId: 'F31',
        factorName: 'Performance',
        description: 'F31 PER: FWD: 0.7*(F03+F05)+0.3*(F08+F10), DEF: similar with F04/F09, Goalies: GAA+SV%',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f31) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f31) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f31) || 0,
        maxPoints: parseFloat(ratingStats.max_f31) || 0,
        avgPoints: parseFloat(ratingStats.avg_f31) || 0,
        factorType: 'rating',
        formula: 'FWD: IF(0.7*(F03+F05)+0.3*(F08+F10)>=1, 99, ROUND(98*(0.7*(F03+F05)+0.3*(F08+F10))))'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F32',
        factorName: 'Level Rating',
        description: 'F32 LEV: League tier rating from league table (70% of overall)',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f32) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f32) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f32) || 0,
        maxPoints: parseFloat(ratingStats.max_f32) || 0,
        avgPoints: parseFloat(ratingStats.avg_f32) || 0,
        factorType: 'rating',
        formula: 'From league tier lookup table'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F33',
        factorName: 'Visibility Rating',
        description: 'F33 VIS: Linear 0-99 from EP Views (100-15000 range)',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f33) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f33) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f33) || 0,
        maxPoints: parseFloat(ratingStats.max_f33) || 0,
        avgPoints: parseFloat(ratingStats.avg_f33) || 0,
        factorType: 'rating',
        formula: 'Linear: 0-99 for 100-15000 EP views'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F34',
        factorName: 'Physical Rating',
        description: 'F34 PHY: (F02+F26+F27)/600*99',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f34) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f34) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f34) || 0,
        maxPoints: parseFloat(ratingStats.max_f34) || 0,
        avgPoints: parseFloat(ratingStats.avg_f34) || 0,
        factorType: 'rating',
        formula: '(F02 + F26 + F27) / 600 * 99'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F35',
        factorName: 'Achievements Rating',
        description: 'F35 ACH: (F15+F16+F17+F21+F22)/1500*99, capped at 99',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f35) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f35) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f35) || 0,
        maxPoints: parseFloat(ratingStats.max_f35) || 0,
        avgPoints: parseFloat(ratingStats.avg_f35) || 0,
        factorType: 'rating',
        formula: 'IF((F15+F16+F17+F21+F22)>=1500, 99, ROUND(99*(F15+F16+F17+F21+F22)/1500))'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F36',
        factorName: 'Trending Rating',
        description: 'F36 T: Skaters: (F18+F19+F25)/250*99, Goalies: F25/50*99',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f36) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f36) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f36) || 0,
        maxPoints: parseFloat(ratingStats.max_f36) || 0,
        avgPoints: parseFloat(ratingStats.avg_f36) || 0,
        factorType: 'rating',
        formula: 'Skaters: IF((F18+F19+F25)>=250, 99, ROUND(99*(F18+F19+F25)/250)), Goalies: IF(F25>=50, 99, ROUND(99*F25/50))'
      },
      {
        tableName: 'player_card_ratings',
        factorId: 'F37',
        factorName: 'Overall Rating',
        description: 'F37 OVR: F31*0.03 + F32*0.70 + F33*0.19 + F34*0.05 + F35*0.03',
        maxPointsConfig: 99,
        rowCount: parseInt(ratingStats.count_f37) || 0,
        lastCalculated: new Date().toISOString(),
        hoursSinceCalc: 0,
        status: 'fresh',
        isActive: true,
        coverage: Math.round((parseInt(ratingStats.count_f37) / totalPlayers) * 1000) / 10,
        minPoints: parseFloat(ratingStats.min_f37) || 0,
        maxPoints: parseFloat(ratingStats.max_f37) || 0,
        avgPoints: parseFloat(ratingStats.avg_f37) || 0,
        factorType: 'rating',
        formula: 'F31*0.03 + F32*0.70 + F33*0.19 + F34*0.05 + F35*0.03'
      }
    ];

    // Combine all factors
    const factors = [...rankingFactors, ...ratingFactors];

    res.json({
      factors,
      summary: {
        totalFactors: factors.length,
        rankingFactors: rankingFactors.length,
        ratingFactors: ratingFactors.length,
        activeFactors: factors.filter(f => f.isActive).length,
        inactiveFactors: factors.filter(f => !f.isActive).length,
        algorithmVersion: 'v3.0-2026-01-19'
      }
    });
  } catch (error) {
    console.error('Error in adminGetFactors:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /admin/coverage
 * Get coverage metrics - how many players have each type of data
 */
functions.http('adminGetCoverage', withCors(async (req, res) => {
  try {
    const query = `
      SELECT
        COUNT(*) as total_players,
        COUNTIF(f01_views > 0) as has_views,
        COUNTIF(f02_height > 0) as has_height,
        COUNTIF(f03_current_goals_f > 0 OR f04_current_goals_d > 0) as has_current_goals,
        COUNTIF(f05_current_assists > 0) as has_current_assists,
        COUNTIF(f08_last_goals_f > 0 OR f09_last_goals_d > 0) as has_last_season_goals,
        COUNTIF(f10_last_assists > 0) as has_last_season_assists,
        COUNTIF(f13_league_points > 0) as has_league_points,
        COUNTIF(f14_team_points > 0) as has_team_points,
        COUNTIF(f15_international_points > 0) as has_international_points,
        COUNTIF(f17_draft_points > 0) as has_draft_points
      FROM \`prodigy-ranking.algorithm_core.player_rankings\`
    `;

    const rows = await executeQuery(query);
    const data = rows[0];

    res.json({
      totalPlayers: parseInt(data.total_players) || 0,
      hasViews: parseInt(data.has_views) || 0,
      hasHeight: parseInt(data.has_height) || 0,
      hasCurrentGoals: parseInt(data.has_current_goals) || 0,
      hasCurrentAssists: parseInt(data.has_current_assists) || 0,
      hasLastSeasonGoals: parseInt(data.has_last_season_goals) || 0,
      hasLastSeasonAssists: parseInt(data.has_last_season_assists) || 0,
      hasLeaguePoints: parseInt(data.has_league_points) || 0,
      hasTeamPoints: parseInt(data.has_team_points) || 0,
      hasInternationalPoints: parseInt(data.has_international_points) || 0,
      hasDraftPoints: parseInt(data.has_draft_points) || 0
    });
  } catch (error) {
    console.error('Error in adminGetCoverage:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /admin/pipeline
 * Get data pipeline status
 */
functions.http('adminGetPipeline', withCors(async (req, res) => {
  try {
    const query = `
      SELECT 'Player Stats Staging' as stage_name, 'player_stats_staging' as table_name, 'algorithm_staging' as dataset,
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_staging.player_stats_staging\`) as row_count,
        (SELECT MAX(loadts) FROM \`prodigy-ranking.algorithm_staging.player_stats_staging\`) as last_updated,
        'Raw player data from EP API' as description
      UNION ALL
      SELECT 'Player Stats', 'player_stats', 'algorithm_core',
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.player_stats\`),
        (SELECT MAX(loadts) FROM \`prodigy-ranking.algorithm_core.player_stats\`),
        'Processed player statistics'
      UNION ALL
      SELECT 'Season Stats Staging', 'player_season_stats_staging', 'algorithm_staging',
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_staging.player_season_stats_staging\`),
        NULL,
        'Historical season statistics'
      UNION ALL
      SELECT 'Cumulative Points', 'player_rankings', 'algorithm_core',
        (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.player_rankings\`),
        (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.player_rankings\`),
        'Aggregated player rankings'
    `;

    const rows = await executeQuery(query);

    const stages = rows.map(row => ({
      stageName: row.stage_name,
      tableName: row.table_name,
      dataset: row.dataset,
      rowCount: parseInt(row.row_count) || 0,
      lastUpdated: row.last_updated ? row.last_updated.value : new Date().toISOString(),
      status: 'healthy',
      description: row.description
    }));

    res.json({ stages });
  } catch (error) {
    console.error('Error in adminGetPipeline:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /admin/alerts
 * Get active alerts and issues
 */
functions.http('adminGetAlerts', withCors(async (req, res) => {
  try {
    const alerts = [];

    // Check for stale factor tables
    const staleQuery = `
      SELECT 'PT_F03_CGPGF' as table_name, MAX(calculated_at) as last_calc
      FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`
      UNION ALL
      SELECT 'PT_F08_LGPGF', MAX(calculated_at)
      FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`
    `;

    const staleRows = await executeQuery(staleQuery);

    for (const row of staleRows) {
      if (row.last_calc) {
        const hoursSince = Math.floor((Date.now() - new Date(row.last_calc.value).getTime()) / (1000 * 60 * 60));
        if (hoursSince > 24) {
          alerts.push({
            id: `stale-${row.table_name}`,
            severity: hoursSince > 168 ? 'critical' : 'warning',
            category: 'stale_data',
            title: `${row.table_name} is ${hoursSince > 168 ? 'critically' : ''} stale`,
            description: `Last calculated ${hoursSince} hours ago. Consider refreshing performance factors.`,
            affectedCount: 1,
            detectedAt: new Date().toISOString()
          });
        }
      }
    }

    // Check for players with stats but 0 performance points
    const zeroPointsQuery = `
      SELECT COUNT(*) as count
      FROM \`prodigy-ranking.algorithm_core.player_rankings\` pcp
      WHERE pcp.performance_total = 0
        AND pcp.f01_views > 0
    `;

    const zeroRows = await executeQuery(zeroPointsQuery);
    const zeroCount = parseInt(zeroRows[0].count) || 0;

    if (zeroCount > 1000) {
      alerts.push({
        id: 'zero-performance',
        severity: 'info',
        category: 'data_quality',
        title: 'Players with 0 performance points',
        description: `${zeroCount.toLocaleString()} players have views but 0 performance points. This may be normal for players with <5 GP.`,
        affectedCount: zeroCount,
        detectedAt: new Date().toISOString()
      });
    }

    res.json({ alerts });
  } catch (error) {
    console.error('Error in adminGetAlerts:', error);
    return errorResponse(res, 500, 'Internal server error');
  }
}));

/**
 * GET /admin/players
 * Get players with full admin details
 */
functions.http('adminGetPlayers', withCors(async (req, res) => {
  try {
    const birthYear = req.query.birthYear || 2009;
    const position = req.query.position || 'F';
    const limit = parseInt(req.query.limit) || 50;
    const offset = parseInt(req.query.offset) || 0;
    const search = req.query.q;

    // Build WHERE clauses with proper table prefixes
    // Main query uses 'pcp.' prefix for JOINs, count query doesn't need it
    let whereClauseMain = '';
    let whereClauseCount = '';
    let params = {};

    if (search) {
      whereClauseMain = 'WHERE LOWER(pcp.player_name) LIKE LOWER(@search)';
      whereClauseCount = 'WHERE LOWER(player_name) LIKE LOWER(@search)';
      params = { search: `%${search}%`, limit, offset };
    } else {
      whereClauseMain = 'WHERE pcp.birth_year = @birthYear AND pcp.position = @position';
      whereClauseCount = 'WHERE birth_year = @birthYear AND position = @position';
      params = {
        birthYear: parseInt(birthYear),
        position: position.toUpperCase(),
        limit: limit,
        offset: offset
      };
    }

    const query = `
      SELECT
        pcp.player_id as playerId,
        pcp.player_name as playerName,
        pcp.position,
        pcp.birth_year as birthYear,
        pcp.nationality_name as nationality,
        pcp.current_team as currentTeam,
        pcp.current_league as currentLeague,
        ROUND(pcp.total_points, 2) as totalPoints,
        ROUND(pcp.performance_total, 2) as performanceTotal,
        ROUND(pcp.direct_load_total, 2) as directLoadTotal,
        ROW_NUMBER() OVER (ORDER BY pcp.total_points DESC) as rank,
        ROUND(pcp.f01_views, 2) as f01_views,
        ROUND(COALESCE(f02.factor_2_h_points, pcp.f02_height), 2) as f02_height,
        ROUND(pcp.f03_current_goals_f, 2) as f03_current_goals_f,
        ROUND(pcp.f04_current_goals_d, 2) as f04_current_goals_d,
        ROUND(pcp.f05_current_assists, 2) as f05_current_assists,
        ROUND(pcp.f06_current_gaa, 2) as f06_current_gaa,
        ROUND(pcp.f07_current_svp, 2) as f07_current_svp,
        ROUND(pcp.f08_last_goals_f, 2) as f08_last_goals_f,
        ROUND(pcp.f09_last_goals_d, 2) as f09_last_goals_d,
        ROUND(pcp.f10_last_assists, 2) as f10_last_assists,
        ROUND(pcp.f11_last_gaa, 2) as f11_last_gaa,
        ROUND(pcp.f12_last_svp, 2) as f12_last_svp,
        COALESCE(pcp.f13_league_points, 0) as f13_league_points,
        COALESCE(pcp.f14_team_points, 0) as f14_team_points,
        ROUND(COALESCE(pcp.f15_international_points, 0), 2) as f15_international_points,
        COALESCE(pcp.f16_commitment_points, 0) as f16_commitment_points,
        COALESCE(pcp.f17_draft_points, 0) as f17_draft_points,
        ROUND(COALESCE(pcp.f18_weekly_points_delta, 0), 2) as f18_weekly_points_delta,
        ROUND(COALESCE(pcp.f19_weekly_assists_delta, 0), 2) as f19_weekly_assists_delta,
        COALESCE(pcp.f20_playing_up_points, 0) as f20_playing_up_points,
        COALESCE(pcp.f21_tournament_points, 0) as f21_tournament_points,
        COALESCE(pcp.f22_manual_points, 0) as f22_manual_points,
        COALESCE(pcp.f23_prodigylikes_points, 0) as f23_prodigylikes_points,
        COALESCE(pcp.f24_card_sales_points, 0) as f24_card_sales_points,
        -- F25 Weekly Views Delta
        ROUND(COALESCE(f25.factor_25_points, 0), 2) as f25_weekly_views_delta,
        -- F26 Weight and F27 BMI
        ROUND(COALESCE(f26.factor_26_weight_points, 0), 2) as f26_weight,
        ROUND(COALESCE(f27.factor_27_bmi_points, 0), 2) as f27_bmi,
        -- F28 NHL Scouting
        ROUND(COALESCE(f28.factor_28_nhl_scouting_points, 0), 2) as f28_nhl_scouting,
        -- =========================================================================
        -- Rating Factors F31-F37: READ PRE-COMPUTED VALUES FROM TABLE
        -- These are calculated by rebuild_cumulative_with_ratings.sql
        -- Using pre-computed values ensures consistency with profile pages
        -- =========================================================================
        COALESCE(pcp.f31_performance_rating, 0) as f31_performance,
        COALESCE(pcp.f32_level_rating, 1) as f32_level,
        COALESCE(pcp.f33_visibility_rating, 0) as f33_visibility,
        COALESCE(pcp.f34_physical_rating, 0) as f34_physical,
        COALESCE(pcp.f35_achievements_rating, 0) as f35_achievements,
        COALESCE(pcp.f36_trending_rating, 0) as f36_trending,
        -- F37 Overall: Computed from F31-F35 with canonical weights
        -- 3% Performance + 70% Level + 19% Visibility + 5% Physical + 3% Achievements
        CAST(LEAST(99, GREATEST(1, ROUND(
          COALESCE(pcp.f31_performance_rating, 0) * 0.03 +
          COALESCE(pcp.f32_level_rating, 1) * 0.70 +
          COALESCE(pcp.f33_visibility_rating, 0) * 0.19 +
          COALESCE(pcp.f34_physical_rating, 0) * 0.05 +
          COALESCE(pcp.f35_achievements_rating, 0) * 0.03
        ))) AS INT64) as f37_overall,
        pcp.calculated_at as calculatedAt,
        pcp.algorithm_version as algorithmVersion
      -- Use player_cumulative_points which has pre-computed F31-F36 ratings
      FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\` pcp
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F01_EPV\` f01 ON pcp.player_id = f01.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F02_H\` f02 ON pcp.player_id = f02.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F25_weekly_views_delta\` f25 ON pcp.player_id = f25.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F26_weight\` f26 ON pcp.player_id = f26.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F27_bmi\` f27 ON pcp.player_id = f27.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F28_NHLSR\` f28 ON pcp.player_id = f28.player_id
      ${whereClauseMain}
      ORDER BY pcp.total_points DESC
      LIMIT @limit
      OFFSET @offset
    `;

    const countQuery = `
      SELECT COUNT(*) as total
      FROM \`prodigy-ranking.algorithm_core.player_cumulative_points\`
      ${whereClauseCount}
    `;

    // Execute both queries in parallel
    const [rows, countRows] = await Promise.all([
      executeQuery(query, { params }),
      executeQuery(countQuery, { params })
    ]);

    const total = parseInt(countRows[0].total) || 0;

    const players = rows.map(row => ({
      playerId: parseInt(row.playerId),
      playerName: row.playerName,
      position: row.position,
      birthYear: parseInt(row.birthYear),
      nationality: row.nationality,
      currentTeam: row.currentTeam,
      currentLeague: row.currentLeague,
      totalPoints: parseFloat(row.totalPoints) || 0,
      performanceTotal: parseFloat(row.performanceTotal) || 0,
      directLoadTotal: parseFloat(row.directLoadTotal) || 0,
      rank: parseInt(row.rank),
      f01_views: parseFloat(row.f01_views) || 0,
      f02_height: parseFloat(row.f02_height) || 0,
      f03_current_goals_f: parseFloat(row.f03_current_goals_f) || 0,
      f04_current_goals_d: parseFloat(row.f04_current_goals_d) || 0,
      f05_current_assists: parseFloat(row.f05_current_assists) || 0,
      f06_current_gaa: parseFloat(row.f06_current_gaa) || 0,
      f07_current_svp: parseFloat(row.f07_current_svp) || 0,
      f08_last_goals_f: parseFloat(row.f08_last_goals_f) || 0,
      f09_last_goals_d: parseFloat(row.f09_last_goals_d) || 0,
      f10_last_assists: parseFloat(row.f10_last_assists) || 0,
      f11_last_gaa: parseFloat(row.f11_last_gaa) || 0,
      f12_last_svp: parseFloat(row.f12_last_svp) || 0,
      f13_league_points: parseFloat(row.f13_league_points) || 0,
      f14_team_points: parseFloat(row.f14_team_points) || 0,
      f15_international_points: parseFloat(row.f15_international_points) || 0,
      f16_commitment_points: parseFloat(row.f16_commitment_points) || 0,
      f17_draft_points: parseFloat(row.f17_draft_points) || 0,
      f18_weekly_points_delta: parseFloat(row.f18_weekly_points_delta) || 0,
      f19_weekly_assists_delta: parseFloat(row.f19_weekly_assists_delta) || 0,
      f20_playing_up_points: parseFloat(row.f20_playing_up_points) || 0,
      f21_tournament_points: parseFloat(row.f21_tournament_points) || 0,
      f22_manual_points: parseFloat(row.f22_manual_points) || 0,
      f23_prodigylikes_points: parseFloat(row.f23_prodigylikes_points) || 0,
      f24_card_sales_points: parseFloat(row.f24_card_sales_points) || 0,
      f25_weekly_views_delta: parseFloat(row.f25_weekly_views_delta) || 0,
      // Physical factors F26-F28
      f26_weight: parseFloat(row.f26_weight) || 0,
      f27_bmi: parseFloat(row.f27_bmi) || 0,
      f28_nhl_scouting: parseFloat(row.f28_nhl_scouting) || 0,
      // Rating factors F31-F37
      f31_performance: parseInt(row.f31_performance) || 0,
      f32_level: parseInt(row.f32_level) || 0,
      f33_visibility: parseInt(row.f33_visibility) || 0,
      f34_physical: parseInt(row.f34_physical) || 0,
      f35_achievements: parseInt(row.f35_achievements) || 0,
      f36_trending: parseInt(row.f36_trending) || 0,
      f37_overall: parseInt(row.f37_overall) || 0,
      calculatedAt: row.calculatedAt ? row.calculatedAt.value : new Date().toISOString(),
      algorithmVersion: row.algorithmVersion || 'v2.4'
    }));

    res.json({
      players,
      total,
      page: Math.floor(offset / limit) + 1,
      pageSize: limit
    });
  } catch (error) {
    console.error('Error in adminGetPlayers:', error);
    console.error('Error stack:', error.stack);
    console.error('Request params:', {
      birthYear: req.query.birthYear,
      position: req.query.position,
      limit: req.query.limit,
      offset: req.query.offset,
      search: req.query.q
    });

    // Return more detailed error info for debugging
    return res.status(500).json({
      error: 'Database query failed',
      message: error.message || 'Unknown error',
      details: process.env.NODE_ENV !== 'production' ? error.stack : undefined,
      timestamp: new Date().toISOString(),
      params: {
        birthYear: req.query.birthYear,
        position: req.query.position,
        limit: req.query.limit,
        offset: req.query.offset
      }
    });
  }
}));

module.exports = {};

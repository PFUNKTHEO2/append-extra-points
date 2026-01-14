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
 * Get status of all factor tables
 */
functions.http('adminGetFactors', withCors(async (req, res) => {
  try {
    // Query each factor table for row count and last calculated timestamp
    const query = `
      WITH factor_stats AS (
        -- F01: EP Views
        SELECT 'PT_F01_EPV' as table_name, 'F01' as factor_id, 'EP Views' as factor_name,
          'EliteProspects profile views' as description,
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as row_count,
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as last_calculated,
          (SELECT MIN(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as min_points,
          (SELECT MAX(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as max_points,
          (SELECT AVG(factor_1_epv_points) FROM \`prodigy-ranking.algorithm_core.PT_F01_EPV\`) as avg_points
        UNION ALL
        -- F02: Height
        SELECT 'PT_F02_H', 'F02', 'Height', 'Player height bonus',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MIN(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT MAX(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`),
          (SELECT AVG(factor_2_h_points) FROM \`prodigy-ranking.algorithm_core.PT_F02_H\`)
        UNION ALL
        -- F03: Current Goals (Forwards)
        SELECT 'PT_F03_CGPGF', 'F03', 'Current Goals (F)', 'Current season goals per game - Forwards',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MIN(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT MAX(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`),
          (SELECT AVG(factor_3_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F03_CGPGF\`)
        UNION ALL
        -- F04: Current Goals (Defensemen)
        SELECT 'PT_F04_CGPGD', 'F04', 'Current Goals (D)', 'Current season goals per game - Defensemen',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MIN(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT MAX(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`),
          (SELECT AVG(factor_4_current_goals_points) FROM \`prodigy-ranking.algorithm_core.PT_F04_CGPGD\`)
        UNION ALL
        -- F05: Current Assists
        SELECT 'PT_F05_CAPG', 'F05', 'Current Assists', 'Current season assists per game',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MIN(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT MAX(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`),
          (SELECT AVG(factor_5_current_assists_points) FROM \`prodigy-ranking.algorithm_core.PT_F05_CAPG\`)
        UNION ALL
        -- F06: Current GAA (Goalies)
        SELECT 'PT_F06_CGAA', 'F06', 'Current GAA', 'Current season goals against average - Goalies',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MIN(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT MAX(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`),
          (SELECT AVG(factor_6_cgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F06_CGAA\`)
        UNION ALL
        -- F07: Current Save % (Goalies)
        SELECT 'PT_F07_CSV', 'F07', 'Current SV%', 'Current season save percentage - Goalies',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MIN(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT MAX(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`),
          (SELECT AVG(factor_7_csv_points) FROM \`prodigy-ranking.algorithm_core.PT_F07_CSV\`)
        UNION ALL
        -- F08: Last Season Goals (Forwards)
        SELECT 'PT_F08_LGPGF', 'F08', 'Last Goals (F)', 'Last season goals per game - Forwards',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MIN(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT MAX(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`),
          (SELECT AVG(factor_8_lgpgf_points) FROM \`prodigy-ranking.algorithm_core.PT_F08_LGPGF\`)
        UNION ALL
        -- F09: Last Season Goals (Defensemen)
        SELECT 'PT_F09_LGPGD', 'F09', 'Last Goals (D)', 'Last season goals per game - Defensemen',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MIN(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT MAX(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`),
          (SELECT AVG(factor_9_lgpgd_points) FROM \`prodigy-ranking.algorithm_core.PT_F09_LGPGD\`)
        UNION ALL
        -- F10: Last Season Assists
        SELECT 'PT_F10_LAPG', 'F10', 'Last Assists', 'Last season assists per game',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MIN(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT MAX(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`),
          (SELECT AVG(factor_10_lapg_points) FROM \`prodigy-ranking.algorithm_core.PT_F10_LAPG\`)
        UNION ALL
        -- F11: Last Season GAA (Goalies)
        SELECT 'PT_F11_LGAA', 'F11', 'Last GAA', 'Last season goals against average - Goalies',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MIN(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT MAX(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`),
          (SELECT AVG(factor_11_lgaa_points) FROM \`prodigy-ranking.algorithm_core.PT_F11_LGAA\`)
        UNION ALL
        -- F12: Last Season Save % (Goalies)
        SELECT 'PT_F12_LSV', 'F12', 'Last SV%', 'Last season save percentage - Goalies',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MAX(calculated_at) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MIN(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT MAX(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`),
          (SELECT AVG(factor_12_lsv_points) FROM \`prodigy-ranking.algorithm_core.PT_F12_LSV\`)
        UNION ALL
        -- F13: League Quality (no timestamp column in table)
        SELECT 'DL_F13_league_points', 'F13', 'League Quality', 'Points based on league tier',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F13_league_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F13_league_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F13_league_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F13_league_points\`)
        UNION ALL
        -- F14: Team Quality
        SELECT 'DL_F14_team_points', 'F14', 'Team Quality', 'Points based on team ranking',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MAX(imported_at) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F14_team_points\`)
        UNION ALL
        -- F15: International Points
        SELECT 'DL_F15_international_points_final', 'F15', 'International', 'International tournament points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          (SELECT MAX(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`),
          (SELECT AVG(total_international_points) FROM \`prodigy-ranking.algorithm_core.DL_F15_international_points_final\`)
        UNION ALL
        -- F16: Commitment Points
        SELECT 'PT_F16_CP', 'F16', 'Commitment', 'College/junior commitment points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          (SELECT MAX(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`),
          (SELECT AVG(factor_16_commitment_points) FROM \`prodigy-ranking.algorithm_core.PT_F16_CP\`)
        UNION ALL
        -- F17: Draft Points
        SELECT 'DL_F17_draft_points', 'F17', 'Draft', 'NHL/CHL draft position points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F17_draft_points\`)
        UNION ALL
        -- F18: Weekly Goals Delta
        SELECT 'PT_F18_weekly_points_delta', 'F18', 'Weekly Goals Delta', 'Week-over-week goal scoring change',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          (SELECT MAX(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`),
          (SELECT AVG(factor_18_points) FROM \`prodigy-ranking.algorithm_core.PT_F18_weekly_points_delta\`)
        UNION ALL
        -- F19: Weekly Assists Delta
        SELECT 'PT_F19_weekly_assists_delta', 'F19', 'Weekly Assists Delta', 'Week-over-week assist change',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          (SELECT MAX(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`),
          (SELECT AVG(factor_19_points) FROM \`prodigy-ranking.algorithm_core.PT_F19_weekly_assists_delta\`)
        UNION ALL
        -- F20: Playing Up Points
        SELECT 'DL_F20_playing_up_points', 'F20', 'Playing Up', 'Playing in older age groups bonus',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F20_playing_up_points\`)
        UNION ALL
        -- F21: Tournament Points
        SELECT 'DL_F21_tournament_points', 'F21', 'Tournament', 'Showcase/elite tournament points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F21_tournament_points\`)
        UNION ALL
        -- F22: Manual Points
        SELECT 'DL_F22_manual_points', 'F22', 'Manual', 'Manual adjustment points by admins',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F22_manual_points\`)
        UNION ALL
        -- F23: ProdigyLikes Points
        SELECT 'DL_F23_prodigylikes_points', 'F23', 'ProdigyLikes', 'Social engagement points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F23_prodigylikes_points\`)
        UNION ALL
        -- F24: Card Sales Points
        SELECT 'DL_F24_card_sales_points', 'F24', 'Card Sales', 'Trading card market value points',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          (SELECT MAX(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`),
          (SELECT AVG(points) FROM \`prodigy-ranking.algorithm_core.DL_F24_card_sales_points\`)
        UNION ALL
        -- F26: Weight Points
        SELECT 'PT_F26_weight', 'F26', 'Weight', 'Weight-based physical points (max 150)',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          (SELECT MAX(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`),
          (SELECT AVG(factor_26_weight_points) FROM \`prodigy-ranking.algorithm_core.PT_F26_weight\`)
        UNION ALL
        -- F27: BMI Points
        SELECT 'PT_F27_bmi', 'F27', 'BMI', 'Body Mass Index physical points (max 250)',
          (SELECT COUNT(*) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          CURRENT_TIMESTAMP(),
          (SELECT MIN(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          (SELECT MAX(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`),
          (SELECT AVG(factor_27_bmi_points) FROM \`prodigy-ranking.algorithm_core.PT_F27_bmi\`)
      )
      SELECT
        table_name as tableName,
        factor_id as factorId,
        factor_name as factorName,
        description,
        row_count as rowCount,
        last_calculated as lastCalculated,
        COALESCE(TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR), 999) as hoursSinceCalc,
        CASE
          WHEN last_calculated IS NULL THEN 'stale'
          WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR) < 24 THEN 'fresh'
          WHEN TIMESTAMP_DIFF(CURRENT_TIMESTAMP(), last_calculated, HOUR) < 168 THEN 'stale'
          ELSE 'critical'
        END as status,
        ROUND(COALESCE(min_points, 0), 2) as minPoints,
        ROUND(COALESCE(max_points, 0), 2) as maxPoints,
        ROUND(COALESCE(avg_points, 0), 2) as avgPoints
      FROM factor_stats
      ORDER BY factor_id
    `;

    const rows = await executeQuery(query);

    // Get total players for coverage calculation
    const countQuery = `SELECT COUNT(*) as total FROM \`prodigy-ranking.algorithm_core.player_rankings\``;
    const countRows = await executeQuery(countQuery);
    const totalPlayers = parseInt(countRows[0].total) || 1;

    const factors = rows.map(row => ({
      tableName: row.tableName,
      factorId: row.factorId,
      factorName: row.factorName,
      description: row.description,
      rowCount: parseInt(row.rowCount) || 0,
      lastCalculated: row.lastCalculated ? row.lastCalculated.value : new Date().toISOString(),
      hoursSinceCalc: parseInt(row.hoursSinceCalc) || 0,
      status: row.status,
      coverage: Math.round((parseInt(row.rowCount) / totalPlayers) * 1000) / 10,
      minPoints: parseFloat(row.minPoints) || 0,
      maxPoints: parseFloat(row.maxPoints) || 0,
      avgPoints: parseFloat(row.avgPoints) || 0
    }));

    res.json({ factors });
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
        -- F26 Weight and F27 BMI
        ROUND(COALESCE(f26.factor_26_weight_points, pcp.f26_weight_points, 0), 2) as f26_weight_points,
        ROUND(COALESCE(f27.factor_27_bmi_points, pcp.f27_bmi_points, 0), 2) as f27_bmi_points,
        -- Physical Rating: ((F02 + F26 + F27) / 600) * 100, capped 1-99
        CAST(GREATEST(1, LEAST(99, ROUND((
          COALESCE(f02.factor_2_h_points, 0) +
          COALESCE(f26.factor_26_weight_points, 0) +
          COALESCE(f27.factor_27_bmi_points, 0)
        ) / 600.0 * 100))) AS INT64) as physicalRating,
        -- Visibility Rating: Linear 1-99 from F01 views (100 to 15k range)
        CAST(CASE
          WHEN pcp.f01_views <= 100 THEN 1
          WHEN pcp.f01_views >= 15000 THEN 99
          ELSE GREATEST(1, LEAST(99, 1 + ((pcp.f01_views - 100) / (15000.0 - 100.0)) * 98))
        END AS INT64) as visibilityRating,
        pcp.calculated_at as calculatedAt,
        pcp.algorithm_version as algorithmVersion
      FROM \`prodigy-ranking.algorithm_core.player_rankings\` pcp
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F02_H\` f02 ON pcp.player_id = f02.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F26_weight\` f26 ON pcp.player_id = f26.player_id
      LEFT JOIN \`prodigy-ranking.algorithm_core.PT_F27_bmi\` f27 ON pcp.player_id = f27.player_id
      ${whereClauseMain}
      ORDER BY pcp.total_points DESC
      LIMIT @limit
      OFFSET @offset
    `;

    const countQuery = `
      SELECT COUNT(*) as total
      FROM \`prodigy-ranking.algorithm_core.player_rankings\`
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
      // New physical factors
      f26_weight_points: parseFloat(row.f26_weight_points) || 0,
      f27_bmi_points: parseFloat(row.f27_bmi_points) || 0,
      // EA-style ratings
      physicalRating: parseInt(row.physicalRating) || 1,
      visibilityRating: parseInt(row.visibilityRating) || 1,
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

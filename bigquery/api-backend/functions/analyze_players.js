const { BigQuery } = require('@google-cloud/bigquery');
const bigquery = new BigQuery({ projectId: 'prodigy-ranking' });

async function query1_playerDistribution() {
  console.log('\n=====================================================');
  console.log('QUERY 1: PLAYER DISTRIBUTION BY BIRTH YEAR AND POSITION');
  console.log('=====================================================\n');

  try {
    const query = `
      SELECT
        birth_year,
        COUNTIF(position = 'F') as forwards,
        COUNTIF(position = 'D') as defense,
        COUNTIF(position = 'G') as goalies,
        COUNT(*) as total
      FROM \`prodigy-ranking.algorithm_core.player_rankings\`
      GROUP BY birth_year
      ORDER BY birth_year
    `;

    const [rows] = await bigquery.query(query);

    console.log('Birth Year | Forwards (F) |  Defense (D) |   Goalies (G) |        Total');
    console.log('-----------|--------------|--------------|---------------|-------------');

    let totalF = 0, totalD = 0, totalG = 0, grandTotal = 0;

    rows.forEach(row => {
      const f = parseInt(row.forwards) || 0;
      const d = parseInt(row.defense) || 0;
      const g = parseInt(row.goalies) || 0;
      const t = parseInt(row.total) || 0;

      console.log(
        `${String(row.birth_year || 'NULL').padEnd(10)} | ` +
        `${String(f).padStart(12)} | ` +
        `${String(d).padStart(12)} | ` +
        `${String(g).padStart(13)} | ` +
        `${String(t).padStart(12)}`
      );

      totalF += f;
      totalD += d;
      totalG += g;
      grandTotal += t;
    });

    console.log('-----------|--------------|--------------|---------------|-------------');
    console.log(
      `TOTAL      | ` +
      `${String(totalF).padStart(12)} | ` +
      `${String(totalD).padStart(12)} | ` +
      `${String(totalG).padStart(13)} | ` +
      `${String(grandTotal).padStart(12)}`
    );

    console.log('\n');
    console.log('Percentage Distribution by Position:');
    console.log(`  Forwards:  ${((totalF/grandTotal)*100).toFixed(2)}%  (${totalF.toLocaleString()} players)`);
    console.log(`  Defense:   ${((totalD/grandTotal)*100).toFixed(2)}%  (${totalD.toLocaleString()} players)`);
    console.log(`  Goalies:   ${((totalG/grandTotal)*100).toFixed(2)}%  (${totalG.toLocaleString()} players)`);
    console.log(`\nTOTAL PLAYERS: ${grandTotal.toLocaleString()}`);

    return { totalF, totalD, totalG, grandTotal };

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

async function query2_factorCoverage(totals) {
  console.log('\n\n=====================================================');
  console.log('QUERY 2: FACTOR COVERAGE ANALYSIS');
  console.log('=====================================================\n');

  try {
    const query = `
      SELECT
        -- Total counts
        COUNT(*) as total_players,

        -- F01: Elite Prospects Views
        COUNTIF(f01_views IS NOT NULL AND f01_views > 0) as f01_count,
        COUNTIF(f01_views IS NOT NULL AND f01_views > 0 AND position = 'F') as f01_f,
        COUNTIF(f01_views IS NOT NULL AND f01_views > 0 AND position = 'D') as f01_d,
        COUNTIF(f01_views IS NOT NULL AND f01_views > 0 AND position = 'G') as f01_g,

        -- F02: Height
        COUNTIF(f02_height IS NOT NULL AND f02_height > 0) as f02_count,
        COUNTIF(f02_height IS NOT NULL AND f02_height > 0 AND position = 'F') as f02_f,
        COUNTIF(f02_height IS NOT NULL AND f02_height > 0 AND position = 'D') as f02_d,
        COUNTIF(f02_height IS NOT NULL AND f02_height > 0 AND position = 'G') as f02_g,

        -- F03: Current Goals (F)
        COUNTIF(f03_current_goals_f IS NOT NULL AND f03_current_goals_f > 0) as f03_count,
        COUNTIF(f03_current_goals_f IS NOT NULL AND f03_current_goals_f > 0 AND position = 'F') as f03_f,

        -- F04: Current Goals (D)
        COUNTIF(f04_current_goals_d IS NOT NULL AND f04_current_goals_d > 0) as f04_count,
        COUNTIF(f04_current_goals_d IS NOT NULL AND f04_current_goals_d > 0 AND position = 'D') as f04_d,

        -- F05: Current Assists
        COUNTIF(f05_current_assists IS NOT NULL AND f05_current_assists > 0) as f05_count,
        COUNTIF(f05_current_assists IS NOT NULL AND f05_current_assists > 0 AND position = 'F') as f05_f,
        COUNTIF(f05_current_assists IS NOT NULL AND f05_current_assists > 0 AND position = 'D') as f05_d,

        -- F06: Current GAA (G)
        COUNTIF(f06_current_gaa IS NOT NULL AND f06_current_gaa > 0) as f06_count,
        COUNTIF(f06_current_gaa IS NOT NULL AND f06_current_gaa > 0 AND position = 'G') as f06_g,

        -- F07: Current Save % (G)
        COUNTIF(f07_current_svp IS NOT NULL AND f07_current_svp > 0) as f07_count,
        COUNTIF(f07_current_svp IS NOT NULL AND f07_current_svp > 0 AND position = 'G') as f07_g,

        -- F08: Last Goals (F)
        COUNTIF(f08_last_goals_f IS NOT NULL AND f08_last_goals_f > 0) as f08_count,
        COUNTIF(f08_last_goals_f IS NOT NULL AND f08_last_goals_f > 0 AND position = 'F') as f08_f,

        -- F09: Last Goals (D)
        COUNTIF(f09_last_goals_d IS NOT NULL AND f09_last_goals_d > 0) as f09_count,
        COUNTIF(f09_last_goals_d IS NOT NULL AND f09_last_goals_d > 0 AND position = 'D') as f09_d,

        -- F10: Last Assists
        COUNTIF(f10_last_assists IS NOT NULL AND f10_last_assists > 0) as f10_count,
        COUNTIF(f10_last_assists IS NOT NULL AND f10_last_assists > 0 AND position = 'F') as f10_f,
        COUNTIF(f10_last_assists IS NOT NULL AND f10_last_assists > 0 AND position = 'D') as f10_d,

        -- F11: Last GAA (G)
        COUNTIF(f11_last_gaa IS NOT NULL AND f11_last_gaa > 0) as f11_count,
        COUNTIF(f11_last_gaa IS NOT NULL AND f11_last_gaa > 0 AND position = 'G') as f11_g,

        -- F12: Last Save % (G)
        COUNTIF(f12_last_svp IS NOT NULL AND f12_last_svp > 0) as f12_count,
        COUNTIF(f12_last_svp IS NOT NULL AND f12_last_svp > 0 AND position = 'G') as f12_g,

        -- F13: League Points
        COUNTIF(f13_league_points IS NOT NULL AND f13_league_points > 0) as f13_count,
        COUNTIF(f13_league_points IS NOT NULL AND f13_league_points > 0 AND position = 'F') as f13_f,
        COUNTIF(f13_league_points IS NOT NULL AND f13_league_points > 0 AND position = 'D') as f13_d,
        COUNTIF(f13_league_points IS NOT NULL AND f13_league_points > 0 AND position = 'G') as f13_g,

        -- F14: Team Points
        COUNTIF(f14_team_points IS NOT NULL AND f14_team_points > 0) as f14_count,
        COUNTIF(f14_team_points IS NOT NULL AND f14_team_points > 0 AND position = 'F') as f14_f,
        COUNTIF(f14_team_points IS NOT NULL AND f14_team_points > 0 AND position = 'D') as f14_d,
        COUNTIF(f14_team_points IS NOT NULL AND f14_team_points > 0 AND position = 'G') as f14_g,

        -- F15: International Points
        COUNTIF(f15_international_points IS NOT NULL AND f15_international_points > 0) as f15_count,
        COUNTIF(f15_international_points IS NOT NULL AND f15_international_points > 0 AND position = 'F') as f15_f,
        COUNTIF(f15_international_points IS NOT NULL AND f15_international_points > 0 AND position = 'D') as f15_d,
        COUNTIF(f15_international_points IS NOT NULL AND f15_international_points > 0 AND position = 'G') as f15_g,

        -- F16: Commitment Points
        COUNTIF(f16_commitment_points IS NOT NULL AND f16_commitment_points > 0) as f16_count,
        COUNTIF(f16_commitment_points IS NOT NULL AND f16_commitment_points > 0 AND position = 'F') as f16_f,
        COUNTIF(f16_commitment_points IS NOT NULL AND f16_commitment_points > 0 AND position = 'D') as f16_d,
        COUNTIF(f16_commitment_points IS NOT NULL AND f16_commitment_points > 0 AND position = 'G') as f16_g,

        -- F17: Draft Points
        COUNTIF(f17_draft_points IS NOT NULL AND f17_draft_points > 0) as f17_count,
        COUNTIF(f17_draft_points IS NOT NULL AND f17_draft_points > 0 AND position = 'F') as f17_f,
        COUNTIF(f17_draft_points IS NOT NULL AND f17_draft_points > 0 AND position = 'D') as f17_d,
        COUNTIF(f17_draft_points IS NOT NULL AND f17_draft_points > 0 AND position = 'G') as f17_g,

        -- F18: Weekly Points Delta
        COUNTIF(f18_weekly_points_delta IS NOT NULL AND f18_weekly_points_delta > 0) as f18_count,
        COUNTIF(f18_weekly_points_delta IS NOT NULL AND f18_weekly_points_delta > 0 AND position = 'F') as f18_f,
        COUNTIF(f18_weekly_points_delta IS NOT NULL AND f18_weekly_points_delta > 0 AND position = 'D') as f18_d,
        COUNTIF(f18_weekly_points_delta IS NOT NULL AND f18_weekly_points_delta > 0 AND position = 'G') as f18_g,

        -- F19: Weekly Assists Delta
        COUNTIF(f19_weekly_assists_delta IS NOT NULL AND f19_weekly_assists_delta > 0) as f19_count,
        COUNTIF(f19_weekly_assists_delta IS NOT NULL AND f19_weekly_assists_delta > 0 AND position = 'F') as f19_f,
        COUNTIF(f19_weekly_assists_delta IS NOT NULL AND f19_weekly_assists_delta > 0 AND position = 'D') as f19_d,

        -- F20: Playing Up Points
        COUNTIF(f20_playing_up_points IS NOT NULL AND f20_playing_up_points > 0) as f20_count,
        COUNTIF(f20_playing_up_points IS NOT NULL AND f20_playing_up_points > 0 AND position = 'F') as f20_f,
        COUNTIF(f20_playing_up_points IS NOT NULL AND f20_playing_up_points > 0 AND position = 'D') as f20_d,
        COUNTIF(f20_playing_up_points IS NOT NULL AND f20_playing_up_points > 0 AND position = 'G') as f20_g,

        -- F21: Tournament Points
        COUNTIF(f21_tournament_points IS NOT NULL AND f21_tournament_points > 0) as f21_count,
        COUNTIF(f21_tournament_points IS NOT NULL AND f21_tournament_points > 0 AND position = 'F') as f21_f,
        COUNTIF(f21_tournament_points IS NOT NULL AND f21_tournament_points > 0 AND position = 'D') as f21_d,
        COUNTIF(f21_tournament_points IS NOT NULL AND f21_tournament_points > 0 AND position = 'G') as f21_g,

        -- F22: Manual Points
        COUNTIF(f22_manual_points IS NOT NULL AND f22_manual_points > 0) as f22_count,
        COUNTIF(f22_manual_points IS NOT NULL AND f22_manual_points > 0 AND position = 'F') as f22_f,
        COUNTIF(f22_manual_points IS NOT NULL AND f22_manual_points > 0 AND position = 'D') as f22_d,
        COUNTIF(f22_manual_points IS NOT NULL AND f22_manual_points > 0 AND position = 'G') as f22_g,

        -- F23: ProdigyLikes Points
        COUNTIF(f23_prodigylikes_points IS NOT NULL AND f23_prodigylikes_points > 0) as f23_count,
        COUNTIF(f23_prodigylikes_points IS NOT NULL AND f23_prodigylikes_points > 0 AND position = 'F') as f23_f,
        COUNTIF(f23_prodigylikes_points IS NOT NULL AND f23_prodigylikes_points > 0 AND position = 'D') as f23_d,
        COUNTIF(f23_prodigylikes_points IS NOT NULL AND f23_prodigylikes_points > 0 AND position = 'G') as f23_g,

        -- F24: Card Sales Points
        COUNTIF(f24_card_sales_points IS NOT NULL AND f24_card_sales_points > 0) as f24_count,
        COUNTIF(f24_card_sales_points IS NOT NULL AND f24_card_sales_points > 0 AND position = 'F') as f24_f,
        COUNTIF(f24_card_sales_points IS NOT NULL AND f24_card_sales_points > 0 AND position = 'D') as f24_d,
        COUNTIF(f24_card_sales_points IS NOT NULL AND f24_card_sales_points > 0 AND position = 'G') as f24_g

      FROM \`prodigy-ranking.algorithm_core.player_rankings\`
    `;

    const [rows] = await bigquery.query(query);
    const data = rows[0];

    const factors = [
      { code: 'F01', name: 'Elite Prospects Views (EPV)', positions: ['F', 'D', 'G'] },
      { code: 'F02', name: 'Height (H)', positions: ['F', 'D', 'G'] },
      { code: 'F03', name: 'Current Season Goals Per Game - Forwards (CGPGF)', positions: ['F'] },
      { code: 'F04', name: 'Current Season Goals Per Game - Defense (CGPGD)', positions: ['D'] },
      { code: 'F05', name: 'Current Season Assists Per Game (CAPG)', positions: ['F', 'D'] },
      { code: 'F06', name: 'Current Season Goals Against Average - Goalies (CGAA)', positions: ['G'] },
      { code: 'F07', name: 'Current Season Save Percentage - Goalies (CSV)', positions: ['G'] },
      { code: 'F08', name: 'Past Season Goals Per Game - Forwards (LGPGF)', positions: ['F'] },
      { code: 'F09', name: 'Past Season Goals Per Game - Defense (LGPGD)', positions: ['D'] },
      { code: 'F10', name: 'Past Season Assists Per Game (LAPG)', positions: ['F', 'D'] },
      { code: 'F11', name: 'Past Season Goals Against Average - Goalies (LGAA)', positions: ['G'] },
      { code: 'F12', name: 'Past Season Save Percentage - Goalies (LSV)', positions: ['G'] },
      { code: 'F13', name: 'League Quality Points', positions: ['F', 'D', 'G'] },
      { code: 'F14', name: 'Team Quality Points', positions: ['F', 'D', 'G'] },
      { code: 'F15', name: 'International Tournament Points', positions: ['F', 'D', 'G'] },
      { code: 'F16', name: 'Commitment Points (College/Junior)', positions: ['F', 'D', 'G'] },
      { code: 'F17', name: 'Draft Selection Points', positions: ['F', 'D', 'G'] },
      { code: 'F18', name: 'Weekly Points Delta', positions: ['F', 'D', 'G'] },
      { code: 'F19', name: 'Weekly Assists Delta', positions: ['F', 'D'] },
      { code: 'F20', name: 'Playing Up Points', positions: ['F', 'D', 'G'] },
      { code: 'F21', name: 'Tournament Participation Points', positions: ['F', 'D', 'G'] },
      { code: 'F22', name: 'Manual Adjustment Points', positions: ['F', 'D', 'G'] },
      { code: 'F23', name: 'ProdigyLikes Social Engagement Points', positions: ['F', 'D', 'G'] },
      { code: 'F24', name: 'Trading Card Sales Points', positions: ['F', 'D', 'G'] }
    ];

    const coverageData = [];

    factors.forEach((factor, index) => {
      const fNum = String(index + 1).padStart(2, '0');
      const count = parseInt(data[`f${fNum}_count`]) || 0;
      const pct = (count / data.total_players * 100).toFixed(2);

      console.log(`Factor: ${factor.code}_${factor.name}`);
      console.log(`${'='.repeat(80)}`);
      console.log(`  Players with data: ${count.toLocaleString()} (${pct}% of total)`);

      if (factor.positions.includes('F')) {
        const fCount = parseInt(data[`f${fNum}_f`]) || 0;
        const fPct = totals.totalF > 0 ? (fCount / totals.totalF * 100).toFixed(2) : '0.00';
        console.log(`    Forwards:  ${fCount.toLocaleString().padStart(8)} (${fPct}% of all forwards)`);
      }

      if (factor.positions.includes('D')) {
        const dCount = parseInt(data[`f${fNum}_d`]) || 0;
        const dPct = totals.totalD > 0 ? (dCount / totals.totalD * 100).toFixed(2) : '0.00';
        console.log(`    Defense:   ${dCount.toLocaleString().padStart(8)} (${dPct}% of all defense)`);
      }

      if (factor.positions.includes('G')) {
        const gCount = parseInt(data[`f${fNum}_g`]) || 0;
        const gPct = totals.totalG > 0 ? (gCount / totals.totalG * 100).toFixed(2) : '0.00';
        console.log(`    Goalies:   ${gCount.toLocaleString().padStart(8)} (${gPct}% of all goalies)`);
      }

      console.log();

      coverageData.push({
        factor: factor.code,
        name: factor.name,
        count,
        percentage: parseFloat(pct)
      });
    });

    return coverageData;

  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

async function generateSummary(coverageData, totals) {
  console.log('\n\n=====================================================');
  console.log('SUMMARY STATISTICS & DATA QUALITY ANALYSIS');
  console.log('=====================================================\n');

  console.log('OVERALL STATISTICS:');
  console.log(`  Total Players: ${totals.grandTotal.toLocaleString()}`);
  console.log(`  Forwards:      ${totals.totalF.toLocaleString()} (${((totals.totalF/totals.grandTotal)*100).toFixed(2)}%)`);
  console.log(`  Defense:       ${totals.totalD.toLocaleString()} (${((totals.totalD/totals.grandTotal)*100).toFixed(2)}%)`);
  console.log(`  Goalies:       ${totals.totalG.toLocaleString()} (${((totals.totalG/totals.grandTotal)*100).toFixed(2)}%)`);

  const highCoverage = coverageData.filter(f => f.percentage >= 90);
  const mediumCoverage = coverageData.filter(f => f.percentage >= 50 && f.percentage < 90);
  const lowCoverage = coverageData.filter(f => f.percentage < 50);

  console.log('\n\nFACTORS BY COVERAGE LEVEL:');
  console.log('\nHIGH COVERAGE (≥90%):');
  if (highCoverage.length > 0) {
    highCoverage.sort((a, b) => b.percentage - a.percentage).forEach(f => {
      console.log(`  ${f.factor}: ${f.percentage.toFixed(2)}% (${f.count.toLocaleString()} players)`);
    });
  } else {
    console.log('  None');
  }

  console.log('\nMEDIUM COVERAGE (50-89%):');
  if (mediumCoverage.length > 0) {
    mediumCoverage.sort((a, b) => b.percentage - a.percentage).forEach(f => {
      console.log(`  ${f.factor}: ${f.percentage.toFixed(2)}% (${f.count.toLocaleString()} players)`);
    });
  } else {
    console.log('  None');
  }

  console.log('\nLOW COVERAGE (<50%):');
  if (lowCoverage.length > 0) {
    lowCoverage.sort((a, b) => b.percentage - a.percentage).forEach(f => {
      console.log(`  ${f.factor}: ${f.percentage.toFixed(2)}% (${f.count.toLocaleString()} players) ⚠️`);
    });
  } else {
    console.log('  None');
  }

  console.log('\n\nDATA QUALITY OBSERVATIONS:');
  console.log('  ✓ Factors with excellent coverage (>90%) are core data points');
  console.log('  ⚠️ Factors with low coverage (<50%) may indicate:');
  console.log('      - New features not yet fully populated');
  console.log('      - Position-specific factors (normal for specialized stats)');
  console.log('      - Data requiring manual input or external sources');
  console.log('      - Optional/advanced features with limited participation');

  const avgCoverage = coverageData.reduce((sum, f) => sum + f.percentage, 0) / coverageData.length;
  console.log(`\n  Average factor coverage across all 24 factors: ${avgCoverage.toFixed(2)}%`);
}

async function main() {
  try {
    console.log('╔═══════════════════════════════════════════════════════════════╗');
    console.log('║  PRODIGYRANKING DATABASE ANALYSIS                             ║');
    console.log('║  Player Distribution & Factor Coverage Report                 ║');
    console.log('╚═══════════════════════════════════════════════════════════════╝');

    const totals = await query1_playerDistribution();
    const coverageData = await query2_factorCoverage(totals);
    await generateSummary(coverageData, totals);

    console.log('\n\n✓ Analysis complete!');
    console.log('═'.repeat(65));

  } catch (error) {
    console.error('\n✗ Analysis failed:', error.message);
    process.exit(1);
  }
}

main();

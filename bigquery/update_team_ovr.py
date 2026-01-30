"""
Update nepsac_team_rankings.team_ovr to use performance-based formula.

New formula:
- Performance (80%): Win%, Goal Differential, Win-Loss ratio
- Roster Strength (20%): Average ProdigyPoints (tiebreaker)

OVR Scale (70-99):
- 95-99: Elite (85%+ win rate, positive GD)
- 90-94: Very good (70-84% win rate)
- 85-89: Good (55-69% win rate)
- 80-84: Average (45-54% win rate)
- 75-79: Below average (30-44% win rate)
- 70-74: Poor (<30% win rate)
"""

from google.cloud import bigquery

def main():
    client = bigquery.Client()

    # First, debug to see raw calculation values
    debug_query = """
    SELECT
        t.short_name,
        s.wins, s.losses, s.ties,
        s.games_played as gp,
        ROUND(SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played), 3) as win_pct_raw,
        s.goal_differential as gd,
        r.avg_prodigy_points,

        -- Component calculations
        ROUND(0.70 * SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played), 4) as comp1_winpct,
        ROUND(0.15 * LEAST(GREATEST((SAFE_DIVIDE(s.goal_differential, s.games_played) + 2.0) / 4.0, 0), 1), 4) as comp2_gd,
        ROUND(0.15 * LEAST(GREATEST((COALESCE(r.avg_prodigy_points, 750) - 750) / 2200.0, 0), 1), 4) as comp3_roster,

        -- Total combined
        ROUND(
          0.70 * SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played)
          + 0.15 * LEAST(GREATEST((SAFE_DIVIDE(s.goal_differential, s.games_played) + 2.0) / 4.0, 0), 1)
          + 0.15 * LEAST(GREATEST((COALESCE(r.avg_prodigy_points, 750) - 750) / 2200.0, 0), 1)
        , 4) as total_raw,

        -- Final OVR
        70 + CAST(ROUND(
          (0.70 * SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played)
          + 0.15 * LEAST(GREATEST((SAFE_DIVIDE(s.goal_differential, s.games_played) + 2.0) / 4.0, 0), 1)
          + 0.15 * LEAST(GREATEST((COALESCE(r.avg_prodigy_points, 750) - 750) / 2200.0, 0), 1))
          * 29
        ) AS INT64) as calculated_ovr

    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings` r
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` s
        ON r.team_id = s.team_id AND r.season = s.season
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` t
        ON r.team_id = t.team_id
    WHERE r.season = '2025-26' AND s.games_played >= 10
    ORDER BY SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played) DESC
    LIMIT 15
    """

    print("Debug: OVR Calculation Components")
    print("=" * 140)
    rows = list(client.query(debug_query).result())
    for row in rows:
        name = (row.short_name or "-")[:15]
        print(f"{name:<15} Record: {row.wins}-{row.losses}-{row.ties} Win%: {row.win_pct_raw:.3f} GD: {row.gd:>3} | "
              f"Comp1: {row.comp1_winpct:.4f} Comp2: {row.comp2_gd:.4f} Comp3: {row.comp3_roster:.4f} | "
              f"Total: {row.total_raw:.4f} -> OVR: {row.calculated_ovr}")

    print("\n" + "=" * 80)
    print("Analysis: The issue is that win% of 0.89 * 0.70 = 0.62, plus GD and roster")
    print("components, gives ~0.77-0.85 total, which * 29 = 22-25, so OVR = 92-95")
    print("But we're getting 99 everywhere. Let me check the actual stored values...")

    # Check actual stored values
    check_query = """
    SELECT team_id, team_ovr, avg_prodigy_points
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
    WHERE season = '2025-26'
    ORDER BY team_ovr DESC
    LIMIT 10
    """
    rows = list(client.query(check_query).result())
    print("\nCurrent stored team_ovr values:")
    for row in rows:
        print(f"  {row.team_id}: OVR={row.team_ovr}, AvgPts={row.avg_prodigy_points}")

def apply_update():
    client = bigquery.Client()

    # Apply the update using the correct formula
    update_query = """
    UPDATE `prodigy-ranking.algorithm_core.nepsac_team_rankings` r
    SET team_ovr = calc.new_ovr
    FROM (
      SELECT
        r.team_id,
        r.season,
        CASE
          WHEN COALESCE(s.games_played, 0) < 5 THEN
            -- Not enough games: use roster strength
            70 + CAST(ROUND(
              LEAST(GREATEST((COALESCE(r.avg_prodigy_points, 750) - 750) / 2200.0, 0), 1) * 29
            ) AS INT64)
          ELSE
            -- Performance-based
            70 + CAST(ROUND(
              (0.70 * SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played)
              + 0.15 * LEAST(GREATEST((SAFE_DIVIDE(s.goal_differential, s.games_played) + 2.0) / 4.0, 0), 1)
              + 0.15 * LEAST(GREATEST((COALESCE(r.avg_prodigy_points, 750) - 750) / 2200.0, 0), 1))
              * 29
            ) AS INT64)
        END as new_ovr
      FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings` r
      LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` s
        ON r.team_id = s.team_id AND r.season = s.season
      WHERE r.season = '2025-26'
    ) calc
    WHERE r.team_id = calc.team_id AND r.season = calc.season
    """

    print("Applying UPDATE query...")
    job = client.query(update_query)
    job.result()
    print(f"Updated {job.num_dml_affected_rows} rows")

    # Verify
    verify_query = """
    SELECT
        t.short_name,
        r.team_ovr as ovr,
        s.wins, s.losses, s.ties,
        ROUND(SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played) * 100, 1) as win_pct,
        s.goal_differential as gd
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings` r
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` s
        ON r.team_id = s.team_id AND r.season = s.season
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` t
        ON r.team_id = t.team_id
    WHERE r.season = '2025-26' AND s.games_played >= 10
    ORDER BY r.team_ovr DESC, SAFE_DIVIDE(s.wins + s.ties * 0.5, s.games_played) DESC
    LIMIT 20
    """
    rows = list(client.query(verify_query).result())
    print("\nVerification - Top 20 teams by new OVR:")
    print("=" * 80)
    print(f"{'Rank':<5} {'Team':<22} {'OVR':<6} {'Record':<12} {'Win%':<8} {'GD':<6}")
    print("-" * 80)
    for i, row in enumerate(rows, 1):
        record = f"{row.wins or 0}-{row.losses or 0}-{row.ties or 0}"
        print(f"{i:<5} {(row.short_name or '-')[:21]:<22} {row.ovr or 0:<6} {record:<12} {row.win_pct or 0:<8} {row.gd or 0:<6}")

if __name__ == "__main__":
    # main()  # Debug only
    apply_update()

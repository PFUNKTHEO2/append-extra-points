#!/usr/bin/env python3
"""
Recalculate PT Tables with Definitive Algorithm Values
=======================================================
Source: NEW ALGORITHM 122125.xlsx (2025-12-18)

This script recalculates all PT (Points Tables) using the definitive
min/max values from the algorithm config.

Formulas:
- Linear: points = ((value - min) / (max - min)) * max_points
- Inverted: points = ((max - value) / (max - min)) * max_points
- Capped at max_points
"""

from google.cloud import bigquery
from datetime import datetime
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


def main():
    client = bigquery.Client(project='prodigy-ranking')

    print("=" * 80)
    print("RECALCULATING PT TABLES WITH DEFINITIVE VALUES")
    print("=" * 80)

    # =========================================================================
    # F01: EP Views
    # Linear: 100 views = 0 pts, 30000 views = 2000 pts
    # =========================================================================
    print("\n[1] PT_F01_EPV (EP Views)")
    print("    Formula: Linear 100-30000 views -> 0-2000 pts")
    print("-" * 60)

    f01_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F01_EPV` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        COALESCE(ps.views, 0) AS ep_views,
        -- Linear: (views - 100) / (30000 - 100) * 2000, capped at 2000
        CASE
            WHEN COALESCE(ps.views, 0) <= 100 THEN 0.0
            WHEN COALESCE(ps.views, 0) >= 30000 THEN 2000.0
            ELSE ROUND((CAST(ps.views - 100 AS FLOAT64) / 29900.0) * 2000.0, 2)
        END AS factor_1_epv_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    """
    client.query(f01_query).result()

    # Verify
    verify = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_1_epv_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(ep_views) as max_views,
        MAX(factor_1_epv_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F01_EPV`
    """
    df = client.query(verify).to_dataframe()
    print(f"    Total: {df.iloc[0]['total']:,}, With points: {df.iloc[0]['with_points']:,}")
    print(f"    Max views: {df.iloc[0]['max_views']:,}, Max pts: {df.iloc[0]['max_pts']}")

    # =========================================================================
    # F03: Current Season Goals Per Game (Forwards)
    # Linear: 0 GPG = 0 pts, 2.0 GPG = 500 pts
    # =========================================================================
    print("\n[2] PT_F03_CGPGF (Current Goals - Forwards)")
    print("    Formula: Linear 0-2.0 GPG -> 0-500 pts (Forwards only)")
    print("-" * 60)

    f03_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F03_CGPGF` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        ps.latestStats_season_slug AS season,
        COALESCE(ps.latestStats_regularStats_GP, 0) AS games_played,
        COALESCE(SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64), 0) AS goals,
        CASE
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) >= 5
            THEN ROUND(SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64) / ps.latestStats_regularStats_GP, 4)
            ELSE 0
        END AS current_goals_per_game,
        -- Linear: GPG / 2.0 * 500, capped at 500
        CASE
            WHEN ps.position != 'F' THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) < 5 THEN 0.0
            ELSE LEAST(
                ROUND((SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64) / ps.latestStats_regularStats_GP / 2.0) * 500.0, 2),
                500.0
            )
        END AS factor_3_current_goals_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    WHERE ps.position = 'F'
    """
    client.query(f03_query).result()

    verify3 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_3_current_goals_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(current_goals_per_game) as max_gpg,
        MAX(factor_3_current_goals_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F03_CGPGF`
    """
    df3 = client.query(verify3).to_dataframe()
    print(f"    Total: {df3.iloc[0]['total']:,}, With points: {df3.iloc[0]['with_points']:,}")
    print(f"    Max GPG: {df3.iloc[0]['max_gpg']:.3f}, Max pts: {df3.iloc[0]['max_pts']}")

    # =========================================================================
    # F04: Current Season Goals Per Game (Defenders)
    # Linear: 0 GPG = 0 pts, 1.5 GPG = 500 pts
    # =========================================================================
    print("\n[3] PT_F04_CGPGD (Current Goals - Defenders)")
    print("    Formula: Linear 0-1.5 GPG -> 0-500 pts (Defenders only)")
    print("-" * 60)

    f04_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F04_CGPGD` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        ps.latestStats_season_slug AS season,
        COALESCE(ps.latestStats_regularStats_GP, 0) AS games_played,
        COALESCE(SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64), 0) AS goals,
        CASE
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) >= 5
            THEN ROUND(SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64) / ps.latestStats_regularStats_GP, 4)
            ELSE 0
        END AS current_goals_per_game,
        -- Linear: GPG / 1.5 * 500, capped at 500
        CASE
            WHEN ps.position != 'D' THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) < 5 THEN 0.0
            ELSE LEAST(
                ROUND((SAFE_CAST(ps.latestStats_regularStats_G AS FLOAT64) / ps.latestStats_regularStats_GP / 1.5) * 500.0, 2),
                500.0
            )
        END AS factor_4_current_goals_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    WHERE ps.position = 'D'
    """
    client.query(f04_query).result()

    verify4 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_4_current_goals_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(current_goals_per_game) as max_gpg,
        MAX(factor_4_current_goals_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F04_CGPGD`
    """
    df4 = client.query(verify4).to_dataframe()
    print(f"    Total: {df4.iloc[0]['total']:,}, With points: {df4.iloc[0]['with_points']:,}")
    print(f"    Max GPG: {df4.iloc[0]['max_gpg']:.3f}, Max pts: {df4.iloc[0]['max_pts']}")

    # =========================================================================
    # F05: Current Season Assists Per Game (F & D)
    # Linear: 0 APG = 0 pts, 2.5 APG = 500 pts
    # =========================================================================
    print("\n[4] PT_F05_CAPG (Current Assists)")
    print("    Formula: Linear 0-2.5 APG -> 0-500 pts (F & D)")
    print("-" * 60)

    f05_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F05_CAPG` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        ps.latestStats_season_slug AS season,
        COALESCE(ps.latestStats_regularStats_GP, 0) AS games_played,
        COALESCE(SAFE_CAST(ps.latestStats_regularStats_A AS FLOAT64), 0) AS assists,
        CASE
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) >= 5
            THEN ROUND(SAFE_CAST(ps.latestStats_regularStats_A AS FLOAT64) / ps.latestStats_regularStats_GP, 4)
            ELSE 0
        END AS current_assists_per_game,
        -- Linear: APG / 2.5 * 500, capped at 500
        CASE
            WHEN ps.position NOT IN ('F', 'D') THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) < 5 THEN 0.0
            ELSE LEAST(
                ROUND((SAFE_CAST(ps.latestStats_regularStats_A AS FLOAT64) / ps.latestStats_regularStats_GP / 2.5) * 500.0, 2),
                500.0
            )
        END AS factor_5_current_assists_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    WHERE ps.position IN ('F', 'D')
    """
    client.query(f05_query).result()

    verify5 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_5_current_assists_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(current_assists_per_game) as max_apg,
        MAX(factor_5_current_assists_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F05_CAPG`
    """
    df5 = client.query(verify5).to_dataframe()
    print(f"    Total: {df5.iloc[0]['total']:,}, With points: {df5.iloc[0]['with_points']:,}")
    print(f"    Max APG: {df5.iloc[0]['max_apg']:.3f}, Max pts: {df5.iloc[0]['max_pts']}")

    # =========================================================================
    # F06: Current Season GAA (Goalies)
    # Inverted Linear: 0 GAA = 500 pts, 3.5 GAA = 0 pts
    # =========================================================================
    print("\n[5] PT_F06_CGAA (Current GAA - Goalies)")
    print("    Formula: Inverted 0-3.5 GAA -> 500-0 pts (Goalies only)")
    print("-" * 60)

    f06_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F06_CGAA` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        ps.latestStats_season_slug AS season,
        COALESCE(ps.latestStats_regularStats_GP, 0) AS games_played,
        COALESCE(ps.latestStats_regularStats_GAA, 0) AS goals_against_average,
        -- Inverted: (3.5 - GAA) / 3.5 * 500, capped at 0-500
        CASE
            WHEN ps.position != 'G' THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) < 5 THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GAA, 0) >= 3.5 THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GAA, 0) <= 0 THEN 500.0
            ELSE ROUND((3.5 - ps.latestStats_regularStats_GAA) / 3.5 * 500.0, 2)
        END AS factor_6_cgaa_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    WHERE ps.position = 'G'
    """
    client.query(f06_query).result()

    verify6 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_6_cgaa_points > 0 THEN 1 ELSE 0 END) as with_points,
        MIN(goals_against_average) as min_gaa,
        MAX(factor_6_cgaa_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F06_CGAA`
    """
    df6 = client.query(verify6).to_dataframe()
    print(f"    Total: {df6.iloc[0]['total']:,}, With points: {df6.iloc[0]['with_points']:,}")
    print(f"    Min GAA: {df6.iloc[0]['min_gaa']:.3f}, Max pts: {df6.iloc[0]['max_pts']}")

    # =========================================================================
    # F07: Current Season Save % (Goalies)
    # Linear: .699 SV% = 0 pts, .990 SV% = 300 pts
    # =========================================================================
    print("\n[6] PT_F07_CSV (Current SV% - Goalies)")
    print("    Formula: Linear .699-.990 SV% -> 0-300 pts (Goalies only)")
    print("-" * 60)

    f07_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F07_CSV` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        ps.latestStats_season_slug AS season,
        COALESCE(ps.latestStats_regularStats_GP, 0) AS games_played,
        COALESCE(ps.latestStats_regularStats_SVP, 0) AS save_percentage,
        -- Linear: (SVP - 0.699) / (0.990 - 0.699) * 300
        -- Note: SVP is stored as decimal (e.g., 0.920) or as integer (920)
        CASE
            WHEN ps.position != 'G' THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_GP, 0) < 5 THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_SVP, 0) <= 0.699 THEN 0.0
            WHEN COALESCE(ps.latestStats_regularStats_SVP, 0) >= 0.990 THEN 300.0
            ELSE ROUND((ps.latestStats_regularStats_SVP - 0.699) / 0.291 * 300.0, 2)
        END AS factor_7_csv_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    WHERE ps.position = 'G'
    """
    client.query(f07_query).result()

    verify7 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_7_csv_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(save_percentage) as max_svp,
        MAX(factor_7_csv_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F07_CSV`
    """
    df7 = client.query(verify7).to_dataframe()
    print(f"    Total: {df7.iloc[0]['total']:,}, With points: {df7.iloc[0]['with_points']:,}")
    print(f"    Max SV%: {df7.iloc[0]['max_svp']:.3f}, Max pts: {df7.iloc[0]['max_pts']}")

    # =========================================================================
    # F08: Past Season Goals Per Game (Forwards)
    # Linear: 0 GPG = 0 pts, 2.0 GPG = 300 pts
    # =========================================================================
    print("\n[7] PT_F08_LGPGF (Past Goals - Forwards)")
    print("    Formula: Linear 0-2.0 GPG -> 0-300 pts (Forwards only)")
    print("-" * 60)

    # Note: This requires looking at previous season data
    # For now, keeping existing structure but updating the formula
    f08_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.PT_F08_LGPGF` AS
    SELECT
        ps.id AS player_id,
        ps.name AS player_name,
        ps.position,
        ps.yearOfBirth AS birth_year,
        COALESCE(psh.regular_G_numeric, 0) AS last_season_goals,
        COALESCE(psh.regular_GP, 0) AS last_season_gp,
        CASE
            WHEN COALESCE(psh.regular_GP, 0) >= 5
            THEN ROUND(psh.regular_G_numeric / psh.regular_GP, 4)
            ELSE 0
        END AS last_goals_per_game,
        -- Linear: GPG / 2.0 * 300, capped at 300
        CASE
            WHEN ps.position != 'F' THEN 0.0
            WHEN COALESCE(psh.regular_GP, 0) < 5 THEN 0.0
            ELSE LEAST(
                ROUND((psh.regular_G_numeric / psh.regular_GP / 2.0) * 300.0, 2),
                300.0
            )
        END AS factor_8_lgpgf_points,
        CURRENT_TIMESTAMP() AS calculated_at,
        'v3.0-definitive' AS algorithm_version
    FROM `prodigy-ranking.algorithm_core.player_stats` ps
    LEFT JOIN `prodigy-ranking.algorithm_core.player_stats_history` psh
        ON ps.id = psh.player_id
        AND psh.season_slug = '2024-2025'
        AND psh.snapshot_id = (
            SELECT snapshot_id
            FROM `prodigy-ranking.algorithm_core.player_stats_history`
            WHERE season_slug = '2024-2025'
            ORDER BY snapshot_date DESC
            LIMIT 1
        )
    WHERE ps.position = 'F'
    """
    client.query(f08_query).result()

    verify8 = """
    SELECT
        COUNT(*) as total,
        SUM(CASE WHEN factor_8_lgpgf_points > 0 THEN 1 ELSE 0 END) as with_points,
        MAX(last_goals_per_game) as max_gpg,
        MAX(factor_8_lgpgf_points) as max_pts
    FROM `prodigy-ranking.algorithm_core.PT_F08_LGPGF`
    """
    df8 = client.query(verify8).to_dataframe()
    print(f"    Total: {df8.iloc[0]['total']:,}, With points: {df8.iloc[0]['with_points']:,}")
    print(f"    Max GPG: {df8.iloc[0]['max_gpg']}, Max pts: {df8.iloc[0]['max_pts']}")

    # =========================================================================
    # Summary
    # =========================================================================
    print("\n" + "=" * 80)
    print("PT TABLE RECALCULATION COMPLETE")
    print("=" * 80)
    print("\nRecalculated tables:")
    print("  - PT_F01_EPV: EP Views (0-2000 pts, views 100-30000)")
    print("  - PT_F03_CGPGF: Current GPG Forwards (0-500 pts, GPG 0-2.0)")
    print("  - PT_F04_CGPGD: Current GPG Defenders (0-500 pts, GPG 0-1.5)")
    print("  - PT_F05_CAPG: Current APG (0-500 pts, APG 0-2.5)")
    print("  - PT_F06_CGAA: Current GAA (0-500 pts inverted, GAA 0-3.5)")
    print("  - PT_F07_CSV: Current SV% (0-300 pts, SV% .699-.990)")
    print("  - PT_F08_LGPGF: Past GPG Forwards (0-300 pts, GPG 0-2.0)")
    print("\nNOTE: Run rebuild_cumulative_with_fixes_v2_DEDUPLICATED.sql next!")


if __name__ == "__main__":
    main()

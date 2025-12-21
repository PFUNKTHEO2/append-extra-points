#!/usr/bin/env python3
"""
Update Algorithm Config with Definitive Values
===============================================
Source: NEW ALGORITHM 122125.xlsx, Tab: "ranking groups" (2025-12-18)

This script updates DL_algorithm_config in BigQuery with the definitive
max_points, min_value, max_value settings from David's spreadsheet.
"""

from google.cloud import bigquery
from datetime import datetime
import sys

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')


# Definitive algorithm configuration from spreadsheet
# Format: (factor_id, factor_code, factor_name, max_points, min_value, max_value,
#          calculation_type, position_filter, category, notes)
DEFINITIVE_CONFIG = [
    # F01: Elite Prospects Views
    (1, 'F01', 'EP Views', 2000, 100, 30000, 'linear', 'ALL', 'visibility',
     'Linear: 0 pts at <=100 views, 2000 pts at 30000+ views'),

    # F02: Height (physical standards based)
    (2, 'F02', 'Height', 200, None, None, 'physical_standards', 'ALL', 'physical',
     'Based on birth year & position physical standards'),

    # F03: Current Season Goals Per Game (Forwards)
    (3, 'F03', 'Current GPG (F)', 500, 0, 2, 'linear', 'F', 'performance',
     'Linear: 0 pts at 0, 500 pts at 2.0 GPG'),

    # F04: Current Season Goals Per Game (Defenders)
    (4, 'F04', 'Current GPG (D)', 500, 0, 1.5, 'linear', 'D', 'performance',
     'Linear: 0 pts at 0, 500 pts at 1.5 GPG'),

    # F05: Current Season Assists Per Game
    (5, 'F05', 'Current APG', 500, 0, 2.5, 'linear', 'F,D', 'performance',
     'Linear: 0 pts at 0, 500 pts at 2.5 APG'),

    # F06: Current Season Goals Against Average (Goalies)
    (6, 'F06', 'Current GAA', 500, 0, 3.5, 'inverted_linear', 'G', 'performance',
     'INVERTED: 500 pts at 0 GAA, 0 pts at >=3.5 GAA'),

    # F07: Current Season Save Percentage (Goalies)
    (7, 'F07', 'Current SV%', 300, 699, 990, 'linear', 'G', 'performance',
     'Linear: 0 pts at <=.699, 300 pts at .990 (stored as 699-990)'),

    # F08: Past Season Goals Per Game (Forwards) - Note: spreadsheet shows as "current season save percentage" but row 8 is for F
    (8, 'F08', 'Past GPG (F)', 300, 0, 2, 'linear', 'F', 'performance',
     'Linear: 0 pts at 0, 300 pts at 2.0 GPG'),

    # F09: Past Season Goals Per Game (Defenders)
    (9, 'F09', 'Past GPG (D)', 300, 0, 1.5, 'linear', 'D', 'performance',
     'Linear: 0 pts at 0, 300 pts at 1.5 GPG'),

    # F10: Past Season Assists Per Game
    (10, 'F10', 'Past APG', 300, 0, 2.5, 'linear', 'F,D', 'performance',
     'Linear: 0 pts at 0, 300 pts at 2.5 APG'),

    # F11: Past Season Goals Against Average (Goalies)
    (11, 'F11', 'Past GAA', 300, 0, 3.5, 'inverted_linear', 'G', 'performance',
     'INVERTED: 300 pts at 0 GAA, 0 pts at >=3.5 GAA'),

    # F12: Past Season Save Percentage (Goalies)
    (12, 'F12', 'Past SV%', 200, 699, 990, 'linear', 'G', 'performance',
     'Linear: 0 pts at <=.699, 200 pts at .990'),

    # F13: League Points
    (13, 'F13', 'League Points', 4500, None, None, 'tiered', 'ALL', 'level',
     'Tiered system based on league level'),

    # F14: Team Points
    (14, 'F14', 'Team Points', 700, None, None, 'lookup', 'ALL', 'level',
     'Points from DL_F14_team_points table'),

    # F15: International Selection Points
    (15, 'F15', 'International', 1000, None, None, 'lookup', 'ALL', 'accolades',
     'Points from DL_F15_international_points'),

    # F16: Commitment Points
    (16, 'F16', 'Commitment', 500, None, None, 'lookup', 'ALL', 'accolades',
     'Points from DL_F16_commitment_points'),

    # F17: Draft Points
    (17, 'F17', 'Draft Points', 300, None, None, 'lookup', 'ALL', 'accolades',
     'Points from DL_F17_draft_points'),

    # F18: Weekly Goals
    (18, 'F18', 'Weekly Goals', 200, 0, 5, 'per_event', 'F,D', 'trending',
     '40 pts per goal, max 200 (5 goals = max)'),

    # F19: Weekly Assists
    (19, 'F19', 'Weekly Assists', 125, 0, 5, 'per_event', 'F,D', 'trending',
     '25 pts per assist, max 125 (5 assists = max)'),

    # F20: Playing Up Category
    (20, 'F20', 'Playing Up', 300, None, None, 'lookup', 'ALL', 'level',
     'Points for playing up age category'),

    # F21: Tournament Accolades
    (21, 'F21', 'Tournament Points', 500, None, None, 'lookup', 'ALL', 'accolades',
     'Points from DL_F21_tournament_points'),

    # F22: Extra Manual Points
    (22, 'F22', 'Manual Points', None, None, None, 'lookup', 'ALL', 'accolades',
     'Admin override - no cap'),

    # F23: ProdigyChain Likes/Views
    (23, 'F23', 'ProdigyLikes', 500, 0, None, 'lookup', 'ALL', 'visibility',
     'Points from DL_F23_prodigylikes_points'),

    # F24: ProdigyChain Card Sales
    (24, 'F24', 'Card Sales', 500, 0, None, 'lookup', 'ALL', 'visibility',
     'Points from DL_F24_card_sales_points'),

    # F25: Weekly EP Views
    (25, 'F25', 'Weekly EP Views', 200, 0, 200, 'per_event', 'ALL', 'visibility',
     '1 pt per view, max 200 pts'),

    # F26: Weight
    (26, 'F26', 'Weight', 150, None, None, 'physical_standards', 'ALL', 'physical',
     'Based on birth year & position physical standards'),

    # F27: BMI
    (27, 'F27', 'BMI', 250, None, None, 'physical_standards', 'ALL', 'physical',
     'Based on birth year & position physical standards'),
]


def main():
    client = bigquery.Client(project='prodigy-ranking')

    print("=" * 80)
    print("UPDATING ALGORITHM CONFIG WITH DEFINITIVE VALUES")
    print("Source: NEW ALGORITHM 122125.xlsx (2025-12-18)")
    print("=" * 80)

    # First, get current config for comparison
    print("\n[1] Current Config in BigQuery:")
    print("-" * 80)

    current_query = """
    SELECT factor_id, factor_code, factor_name, max_points, min_value, max_value
    FROM `prodigy-ranking.algorithm_core.DL_algorithm_config`
    ORDER BY factor_id
    """
    current_df = client.query(current_query).to_dataframe()
    print(current_df.to_string(index=False))

    # Update each factor
    print("\n[2] Updating Factors:")
    print("-" * 80)

    for config in DEFINITIVE_CONFIG:
        factor_id, factor_code, factor_name, max_points, min_value, max_value, \
            calc_type, position_filter, category, notes = config

        # Build UPDATE query
        update_parts = [
            f"factor_name = '{factor_name}'",
            f"calculation_type = '{calc_type}'",
            f"position_filter = '{position_filter}'",
            f"notes = '{notes}'",
            f"updated_at = CURRENT_TIMESTAMP()"
        ]

        if max_points is not None:
            update_parts.append(f"max_points = {max_points}")
        else:
            update_parts.append("max_points = NULL")

        if min_value is not None:
            update_parts.append(f"min_value = {min_value}")
        else:
            update_parts.append("min_value = NULL")

        if max_value is not None:
            update_parts.append(f"max_value = {max_value}")
        else:
            update_parts.append("max_value = NULL")

        update_query = f"""
        UPDATE `prodigy-ranking.algorithm_core.DL_algorithm_config`
        SET {', '.join(update_parts)}
        WHERE factor_id = {factor_id}
        """

        try:
            client.query(update_query).result()
            max_str = str(max_points) if max_points else 'N/A'
            print(f"  {factor_code}: max={max_str:>5}, min={min_value}, max_val={max_value}")
        except Exception as e:
            # Factor might not exist, try INSERT
            print(f"  {factor_code}: Not found, inserting...")
            insert_query = f"""
            INSERT INTO `prodigy-ranking.algorithm_core.DL_algorithm_config`
            (factor_id, factor_code, factor_name, max_points, min_value, max_value,
             calculation_type, position_filter, notes, is_active, version_number, created_at, updated_at)
            VALUES
            ({factor_id}, '{factor_code}', '{factor_name}',
             {max_points if max_points else 'NULL'},
             {min_value if min_value else 'NULL'},
             {max_value if max_value else 'NULL'},
             '{calc_type}', '{position_filter}', '{notes}',
             TRUE, '3.0', CURRENT_TIMESTAMP(), CURRENT_TIMESTAMP())
            """
            try:
                client.query(insert_query).result()
                print(f"    Inserted successfully")
            except Exception as e2:
                print(f"    Error: {e2}")

    # Show updated config
    print("\n[3] Updated Config:")
    print("-" * 80)

    updated_df = client.query(current_query).to_dataframe()
    print(updated_df.to_string(index=False))

    # Summary of changes
    print("\n[4] Summary of Key Values:")
    print("-" * 80)
    print(f"{'Factor':<8} {'Name':<20} {'Max Pts':<10} {'Min':<10} {'Max Val':<10} {'Category'}")
    print("-" * 80)

    for config in DEFINITIVE_CONFIG:
        factor_id, factor_code, factor_name, max_points, min_value, max_value, \
            calc_type, position_filter, category, notes = config

        max_str = str(max_points) if max_points else 'N/A'
        min_str = str(min_value) if min_value else 'N/A'
        maxval_str = str(max_value) if max_value else 'N/A'

        print(f"{factor_code:<8} {factor_name:<20} {max_str:<10} {min_str:<10} {maxval_str:<10} {category}")

    print("\n" + "=" * 80)
    print("UPDATE COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()

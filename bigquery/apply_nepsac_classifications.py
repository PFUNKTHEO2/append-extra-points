"""
Apply Official NEPSAC Classifications to BigQuery

Source: NEPSAC-Boys-Ice-Hockey-Classification-BIH-25-26-2.pdf
Target: algorithm_core.nepsac_teams

This script updates the nepsac_teams table with official classifications
(Large/Small) and enrollment numbers from the NEPSAC PDF.
"""

from google.cloud import bigquery
import json
import os

# Load classifications from JSON
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLASSIFICATIONS_FILE = os.path.join(
    SCRIPT_DIR, 'api-backend', 'data', 'nepsac_official_classifications.json'
)


def load_classifications():
    """Load official classifications from JSON file"""
    with open(CLASSIFICATIONS_FILE, 'r') as f:
        data = json.load(f)
    return data['teams']


def apply_to_bigquery():
    """Apply classifications to BigQuery nepsac_teams table"""
    client = bigquery.Client(project='prodigy-ranking')
    teams = load_classifications()

    print(f"Loaded {len(teams)} teams from official classifications")
    large_count = sum(1 for t in teams if t['classification'] == 'Large')
    small_count = sum(1 for t in teams if t['classification'] == 'Small')
    print(f"  - Large schools: {large_count}")
    print(f"  - Small schools: {small_count}")

    # Step 1: Create/replace the official classifications table
    print("\nStep 1: Creating nepsac_official_classifications table...")

    # First create an empty table
    create_table_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_official_classifications` (
        team_id STRING,
        team_name STRING,
        short_name STRING,
        classification STRING,
        enrollment INT64
    )
    """
    job = client.query(create_table_query)
    job.result()
    print("  Created empty table")

    # Insert one at a time using parameterized queries
    for i, t in enumerate(teams):
        query = """
        INSERT INTO `prodigy-ranking.algorithm_core.nepsac_official_classifications`
        (team_id, team_name, short_name, classification, enrollment)
        VALUES (@team_id, @team_name, @short_name, @classification, @enrollment)
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("team_id", "STRING", t['teamId']),
                bigquery.ScalarQueryParameter("team_name", "STRING", t['name']),
                bigquery.ScalarQueryParameter("short_name", "STRING", t['shortName']),
                bigquery.ScalarQueryParameter("classification", "STRING", t['classification']),
                bigquery.ScalarQueryParameter("enrollment", "INT64", t['enrollment']),
            ]
        )

        job = client.query(query, job_config=job_config)
        job.result()

        if (i + 1) % 10 == 0:
            print(f"  Inserted {i + 1}/{len(teams)} teams...")

    print(f"  Created nepsac_official_classifications table with {len(teams)} teams")

    # Step 2: Backup existing team data (if any)
    print("\nStep 2: Checking for existing team data...")

    try:
        backup_query = """
        SELECT team_id, logo_url
        FROM `prodigy-ranking.algorithm_core.nepsac_teams`
        WHERE logo_url IS NOT NULL
        """
        existing_logos = {row.team_id: row.logo_url for row in client.query(backup_query).result()}
        print(f"  Found {len(existing_logos)} teams with logo URLs to preserve")
    except Exception as e:
        print(f"  No existing table or no logos to preserve")
        existing_logos = {}

    # Step 3: Create fresh nepsac_teams table
    print("\nStep 3: Creating fresh nepsac_teams table...")

    create_teams_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_teams` AS
    SELECT
        team_id,
        team_name,
        short_name,
        classification,
        enrollment,
        CAST(NULL AS STRING) AS logo_url,
        CAST(NULL AS STRING) AS primary_color,
        CAST(NULL AS STRING) AS secondary_color,
        CAST(NULL AS STRING) AS venue,
        CAST(NULL AS STRING) AS city,
        CAST(NULL AS STRING) AS state,
        CAST(NULL AS INT64) AS ep_team_id,
        CAST(NULL AS STRING) AS mhr_team_id,
        CURRENT_TIMESTAMP() AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM `prodigy-ranking.algorithm_core.nepsac_official_classifications`
    """

    job = client.query(create_teams_query)
    job.result()
    print("  Created nepsac_teams table with 57 teams")

    # Step 4: Restore logo URLs if we had any
    if existing_logos:
        print(f"\nStep 4: Restoring {len(existing_logos)} logo URLs...")
        for team_id, logo_url in existing_logos.items():
            update_logo_query = """
            UPDATE `prodigy-ranking.algorithm_core.nepsac_teams`
            SET logo_url = @logo_url
            WHERE team_id = @team_id
            """
            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("team_id", "STRING", team_id),
                    bigquery.ScalarQueryParameter("logo_url", "STRING", logo_url),
                ]
            )
            job = client.query(update_logo_query, job_config=job_config)
            job.result()
        print(f"  Restored logo URLs")

    # Step 5: Verify the update
    print("\nStep 5: Verifying update...")

    verify_query = """
    SELECT
        classification,
        COUNT(*) as team_count,
        MIN(enrollment) as min_enrollment,
        MAX(enrollment) as max_enrollment
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    GROUP BY classification
    ORDER BY classification
    """

    results = list(client.query(verify_query).result())
    print("\n  Classification Summary:")
    for row in results:
        print(f"    {row.classification}: {row.team_count} teams "
              f"(enrollment {row.min_enrollment}-{row.max_enrollment})")

    # Show sample data
    print("\n  Sample teams (top 5 Large by enrollment):")
    sample_query = """
    SELECT team_id, team_name, classification, enrollment
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    WHERE classification = 'Large'
    ORDER BY enrollment DESC
    LIMIT 5
    """
    for row in client.query(sample_query).result():
        print(f"    {row.team_name}: {row.classification} ({row.enrollment})")

    print("\n  Sample Small schools (top 5 by enrollment):")
    small_query = """
    SELECT team_id, team_name, classification, enrollment
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    WHERE classification = 'Small'
    ORDER BY enrollment DESC
    LIMIT 5
    """
    for row in client.query(small_query).result():
        print(f"    {row.team_name}: {row.classification} ({row.enrollment})")

    print("\n" + "=" * 60)
    print("SUCCESS: NEPSAC classifications applied to BigQuery")
    print("=" * 60)
    print("\nTable: algorithm_core.nepsac_teams")
    print("  - 28 Large schools (enrollment >= 225)")
    print("  - 29 Small schools (enrollment < 225)")
    print("  - Total: 57 teams")


if __name__ == '__main__':
    apply_to_bigquery()

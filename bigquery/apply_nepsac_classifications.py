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
    print(f"  - Large schools: {sum(1 for t in teams if t['classification'] == 'Large')}")
    print(f"  - Small schools: {sum(1 for t in teams if t['classification'] == 'Small')}")

    # Step 1: Create/replace the official classifications table
    print("\nStep 1: Creating nepsac_official_classifications table...")

    # Build VALUES clause
    values = []
    for t in teams:
        values.append(
            f"('{t['teamId']}', '{t['name'].replace(\"'\", \"''\")}', "
            f"'{t['shortName'].replace(\"'\", \"''\")}', '{t['classification']}', {t['enrollment']})"
        )

    create_query = f"""
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_official_classifications` AS
    SELECT * FROM UNNEST([
        {', '.join([
            f"STRUCT('{t['teamId']}' AS team_id, "
            f"'{t['name'].replace(chr(39), chr(39)+chr(39))}' AS team_name, "
            f"'{t['shortName'].replace(chr(39), chr(39)+chr(39))}' AS short_name, "
            f"'{t['classification']}' AS classification, "
            f"{t['enrollment']} AS enrollment)"
            for t in teams
        ])}
    ])
    """

    job = client.query(create_query)
    job.result()
    print("  Created nepsac_official_classifications table")

    # Step 2: Check if nepsac_teams has classification column
    print("\nStep 2: Checking nepsac_teams schema...")

    check_schema = """
    SELECT column_name
    FROM `prodigy-ranking.algorithm_core.INFORMATION_SCHEMA.COLUMNS`
    WHERE table_name = 'nepsac_teams'
    AND column_name IN ('classification', 'enrollment')
    """

    existing_cols = [row.column_name for row in client.query(check_schema).result()]
    print(f"  Existing columns: {existing_cols}")

    # Step 3: Update or recreate nepsac_teams
    print("\nStep 3: Updating nepsac_teams with classifications...")

    # Recreate the table with proper schema
    update_query = """
    CREATE OR REPLACE TABLE `prodigy-ranking.algorithm_core.nepsac_teams` AS
    SELECT
        c.team_id,
        c.team_name,
        c.short_name,
        c.classification,
        c.enrollment,
        t.logo_url,
        t.primary_color,
        t.secondary_color,
        t.venue,
        t.city,
        t.state,
        t.ep_team_id,
        t.mhr_team_id,
        COALESCE(t.created_at, CURRENT_TIMESTAMP()) AS created_at,
        CURRENT_TIMESTAMP() AS updated_at
    FROM `prodigy-ranking.algorithm_core.nepsac_official_classifications` c
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` t
        ON c.team_id = t.team_id
    """

    job = client.query(update_query)
    job.result()
    print("  Updated nepsac_teams table")

    # Step 4: Verify the update
    print("\nStep 4: Verifying update...")

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

    # Step 5: Show sample data
    print("\n  Sample teams:")
    sample_query = """
    SELECT team_id, team_name, classification, enrollment
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    ORDER BY enrollment DESC
    LIMIT 5
    """
    for row in client.query(sample_query).result():
        print(f"    {row.team_name}: {row.classification} ({row.enrollment})")

    print("\n" + "=" * 60)
    print("SUCCESS: NEPSAC classifications applied to BigQuery")
    print("=" * 60)


if __name__ == '__main__':
    apply_to_bigquery()

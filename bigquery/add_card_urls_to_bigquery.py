"""
Add Team Card URLs to BigQuery nepsac_teams Table

This script:
1. Adds card_home_url and card_away_url columns to nepsac_teams
2. Populates them with GitHub CDN URLs based on team_id -> image_slug mapping
3. Creates a single source of truth for all team visual assets

Card URL format:
  https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards/{slug}_{home|away}_left.webp
"""

from google.cloud import bigquery

# GitHub CDN base URL for card images
BASE_URL = "https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards"

# Mapping from team_id (in BigQuery) to image slug (in card filenames)
# This is the SINGLE SOURCE OF TRUTH for team_id -> card mapping
TEAM_ID_TO_IMAGE_SLUG = {
    # Large Schools (28)
    "andover": "andover",
    "exeter": "phillips-exeter-academy",
    "brunswick": "brunswick-school",
    "choate": "choate-rosemary-hall",
    "avon-old-farms": "avon-old-farms",
    "milton": "milton-academy",
    "deerfield": "deerfield-academy",
    "loomis": "loomis-chaffee",
    "belmont-hill": "belmont-hill-school",
    "salisbury": "salisbury-school",
    "taft": "taft-school",
    "hotchkiss": "hotchkiss-school",
    "nmh": "northfield-mount-hermon",
    "st-sebastians": "st-sebastians-school",
    "bbn": "buckingham-browne-and-nichols",
    "tabor": "tabor-academy",
    "thayer": "thayer-academy",
    "kent": "kent-school",
    "st-pauls": "st-pauls-school",
    "austin-prep": "austin-prep",
    "dexter": "dexter-southfield",
    "nobles": "noble-and-greenough",
    "williston": "williston-northampton",
    "trinity-pawling": "trinity-pawling-school",
    "worcester": "worcester-academy",
    "cushing": "cushing-academy",
    "westminster": "westminster-school",
    "lawrence": "lawrence-academy",

    # Small Schools (29)
    "governors": "the-governors-academy",
    "middlesex": "middlesex-school",
    "roxbury-latin": "roxbury-latin",
    "berkshire": "berkshire-school",
    "proctor": "proctor-academy",
    "rivers": "rivers-school",
    "kimball-union": "kimball-union-academy",
    "st-marks": "st-marks-school",
    "albany-academy": "albany-academy",
    "st-georges": "st-georges-school",
    "brooks": "brooks-school",
    "groton": "groton-school",
    "new-hampton": "new-hampton-school",
    "brewster": "brewster-academy",
    "pomfret": "pomfret-school",
    "canterbury": "canterbury-school",
    "wma": "wilbraham-and-monson-academy",
    "pingree": "pingree-school",
    "portsmouth-abbey": "portsmouth-abbey",
    "winchendon": "winchendon-school",
    "frederick-gunn": "frederick-gunn-school",
    "hoosac": "hoosac-school",
    "millbrook": "millbrook-school",
    "holderness": "holderness-school",
    "berwick": "berwick-academy",
    "vermont-academy": "vermont-academy",
    "hebron": "hebron-academy",
    "kents-hill": "kents-hill-school",
    "tilton": "tilton-school",
}


def add_card_urls_to_bigquery():
    """Add card URL columns and populate them"""
    client = bigquery.Client(project='prodigy-ranking')

    print("=" * 60)
    print("Adding Card URLs to BigQuery nepsac_teams Table")
    print("=" * 60)

    # Step 1: Add new columns if they don't exist
    print("\nStep 1: Adding card URL columns...")

    try:
        alter_query = """
        ALTER TABLE `prodigy-ranking.algorithm_core.nepsac_teams`
        ADD COLUMN IF NOT EXISTS card_home_url STRING,
        ADD COLUMN IF NOT EXISTS card_away_url STRING,
        ADD COLUMN IF NOT EXISTS image_slug STRING
        """
        job = client.query(alter_query)
        job.result()
        print("  Added columns: card_home_url, card_away_url, image_slug")
    except Exception as e:
        print(f"  Note: {e}")
        print("  Columns may already exist, continuing...")

    # Step 2: Update each team with their card URLs
    print(f"\nStep 2: Updating {len(TEAM_ID_TO_IMAGE_SLUG)} teams with card URLs...")

    updated = 0
    for team_id, image_slug in TEAM_ID_TO_IMAGE_SLUG.items():
        card_home_url = f"{BASE_URL}/{image_slug}_home_left.webp"
        card_away_url = f"{BASE_URL}/{image_slug}_away_left.webp"

        update_query = """
        UPDATE `prodigy-ranking.algorithm_core.nepsac_teams`
        SET
            card_home_url = @card_home_url,
            card_away_url = @card_away_url,
            image_slug = @image_slug,
            updated_at = CURRENT_TIMESTAMP()
        WHERE team_id = @team_id
        """

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("team_id", "STRING", team_id),
                bigquery.ScalarQueryParameter("card_home_url", "STRING", card_home_url),
                bigquery.ScalarQueryParameter("card_away_url", "STRING", card_away_url),
                bigquery.ScalarQueryParameter("image_slug", "STRING", image_slug),
            ]
        )

        job = client.query(update_query, job_config=job_config)
        result = job.result()

        if job.num_dml_affected_rows and job.num_dml_affected_rows > 0:
            updated += 1

        if updated % 10 == 0 and updated > 0:
            print(f"  Updated {updated} teams...")

    print(f"  Updated {updated} teams with card URLs")

    # Step 3: Verify the update
    print("\nStep 3: Verifying update...")

    verify_query = """
    SELECT
        COUNT(*) as total_teams,
        COUNTIF(card_home_url IS NOT NULL) as teams_with_cards,
        COUNTIF(logo_url IS NOT NULL) as teams_with_logos
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    """

    result = list(client.query(verify_query).result())[0]
    print(f"\n  Total teams: {result.total_teams}")
    print(f"  Teams with card URLs: {result.teams_with_cards}")
    print(f"  Teams with logo URLs: {result.teams_with_logos}")

    # Step 4: Show sample data
    print("\nStep 4: Sample data (first 5 teams)...")

    sample_query = """
    SELECT
        team_id,
        short_name,
        classification,
        SUBSTR(logo_url, 1, 50) as logo_url_preview,
        SUBSTR(card_home_url, -40) as card_home_preview
    FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    WHERE card_home_url IS NOT NULL
    ORDER BY enrollment DESC
    LIMIT 5
    """

    for row in client.query(sample_query).result():
        print(f"  {row.short_name} ({row.classification})")
        print(f"    Logo: {row.logo_url_preview}...")
        print(f"    Card: ...{row.card_home_preview}")

    print("\n" + "=" * 60)
    print("SUCCESS: Card URLs added to BigQuery nepsac_teams table")
    print("=" * 60)
    print("\nNew schema fields:")
    print("  - card_home_url: Home team card image URL")
    print("  - card_away_url: Away team card image URL")
    print("  - image_slug: Card filename prefix for reference")
    print("\nAPI endpoints will now return these fields automatically.")


if __name__ == '__main__':
    add_card_urls_to_bigquery()

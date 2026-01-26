"""
Populate NEPSAC Player Images from Elite Prospects
===================================================
Fetches player image URLs from Elite Prospects API and updates
the nepsac_rosters table in BigQuery.
"""

import os
import time
import requests
from datetime import datetime
from google.cloud import bigquery

# Elite Prospects API Configuration
EP_API_KEY = "EmmrXHpydfr14MVUdFxZyCCczQ3wqghc"
EP_BASE_URL = "https://api.eliteprospects.com/v1"
REQUESTS_PER_SECOND = 2  # Rate limit to avoid API throttling

# BigQuery Configuration
PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"
TABLE = "nepsac_rosters"


def log(message: str, level: str = "INFO"):
    """Print timestamped log message."""
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")


def get_nepsac_players_without_images() -> list:
    """
    Get all NEPSAC roster players that have a player_id but no image_url.
    """
    client = bigquery.Client(project=PROJECT_ID)

    query = f"""
    SELECT DISTINCT
        r.player_id,
        r.roster_name,
        r.team_id
    FROM `{PROJECT_ID}.{DATASET}.{TABLE}` r
    WHERE r.player_id IS NOT NULL
      AND r.is_active = TRUE
      AND (r.image_url IS NULL OR r.image_url = '')
    ORDER BY r.player_id
    """

    log("Querying BigQuery for NEPSAC players without images...")
    results = client.query(query).result()

    players = []
    for row in results:
        players.append({
            'player_id': row['player_id'],
            'name': row['roster_name'],
            'team_id': row['team_id']
        })

    log(f"Found {len(players)} players without images")
    return players


def fetch_player_image_url(player_id: int) -> str:
    """
    Fetch player image URL from Elite Prospects API.
    Returns empty string if no image found.
    """
    url = f"{EP_BASE_URL}/players/{player_id}"
    params = {'apiKey': EP_API_KEY}

    try:
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 200:
            data = response.json().get('data', {})
            image_url = data.get('imageUrl', '')
            return image_url if image_url else ''
        elif response.status_code == 404:
            return ''
        else:
            log(f"API error for player {player_id}: {response.status_code}", "WARN")
            return ''

    except Exception as e:
        log(f"Error fetching player {player_id}: {e}", "ERROR")
        return ''


def update_player_images_batch(updates: list):
    """
    Update image URLs in BigQuery using a batch approach.
    """
    if not updates:
        log("No updates to apply")
        return

    client = bigquery.Client(project=PROJECT_ID)

    # Build CASE statement for batch update
    case_statements = []
    player_ids = []

    for update in updates:
        player_id = update['player_id']
        image_url = update['image_url'].replace("'", "''")  # Escape quotes
        case_statements.append(f"WHEN player_id = {player_id} THEN '{image_url}'")
        player_ids.append(str(player_id))

    player_ids_str = ', '.join(player_ids)
    case_str = '\n'.join(case_statements)

    # Use ISO format string for updated_at since it's a STRING column
    now_str = datetime.utcnow().isoformat()

    query = f"""
    UPDATE `{PROJECT_ID}.{DATASET}.{TABLE}`
    SET image_url = CASE
        {case_str}
        ELSE image_url
    END,
    updated_at = '{now_str}'
    WHERE player_id IN ({player_ids_str})
    """

    log(f"Updating {len(updates)} player images in BigQuery...")
    job = client.query(query)
    job.result()  # Wait for completion
    log(f"Successfully updated {len(updates)} players")


def main():
    """Main function to populate player images."""
    log("=" * 60)
    log("NEPSAC Player Image Population Script")
    log("=" * 60)

    # Get players without images
    players = get_nepsac_players_without_images()

    if not players:
        log("All players already have images!")
        return

    # Fetch images from EP API
    updates = []
    found_count = 0
    not_found_count = 0

    log(f"\nFetching images for {len(players)} players from Elite Prospects...")
    log("This may take a few minutes due to API rate limiting.\n")

    for i, player in enumerate(players, 1):
        player_id = player['player_id']
        name = player['name']

        # Rate limiting
        time.sleep(1 / REQUESTS_PER_SECOND)

        # Fetch image URL
        image_url = fetch_player_image_url(player_id)

        if image_url:
            updates.append({
                'player_id': player_id,
                'image_url': image_url
            })
            found_count += 1
            log(f"[{i}/{len(players)}] {name}: Found image")
        else:
            not_found_count += 1
            if i % 10 == 0:  # Only log every 10th missing to reduce noise
                log(f"[{i}/{len(players)}] Progress: {found_count} found, {not_found_count} not found")

        # Batch update every 50 players
        if len(updates) >= 50:
            update_player_images_batch(updates)
            updates = []

    # Final batch update
    if updates:
        update_player_images_batch(updates)

    # Summary
    log("\n" + "=" * 60)
    log("SUMMARY")
    log("=" * 60)
    log(f"Total players processed: {len(players)}")
    log(f"Images found: {found_count}")
    log(f"Images not found: {not_found_count}")
    log(f"Success rate: {(found_count / len(players) * 100):.1f}%")
    log("=" * 60)


if __name__ == "__main__":
    main()

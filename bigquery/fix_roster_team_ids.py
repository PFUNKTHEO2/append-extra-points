"""
Fix team_id mismatches between nepsac_rosters and nepsac_teams tables.
"""
from google.cloud import bigquery

def main():
    client = bigquery.Client()

    # Find all team_ids in rosters that don't exist in teams
    print("Finding team ID mismatches...")
    query = """
    SELECT DISTINCT r.team_id as roster_team_id
    FROM `prodigy-ranking.algorithm_core.nepsac_rosters` r
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` t ON r.team_id = t.team_id
    WHERE t.team_id IS NULL
    ORDER BY r.team_id
    """
    rows = list(client.query(query).result())
    print(f"Found {len(rows)} roster team_ids with no match in nepsac_teams:")
    for row in rows:
        print(f"  - {row.roster_team_id}")

    # Get all official team IDs for reference
    print("\nOfficial team IDs in nepsac_teams:")
    query2 = """
    SELECT team_id, team_name FROM `prodigy-ranking.algorithm_core.nepsac_teams`
    ORDER BY team_id
    """
    teams = {row.team_id: row.team_name for row in client.query(query2).result()}

    # Define the mappings
    mappings = {
        "loomis-chaffee": "loomis",
        # Add more mappings as needed
    }

    # Check if any other mismatched IDs can be auto-mapped
    print("\nAttempting to find mappings for unmatched IDs...")
    for row in rows:
        roster_id = row.roster_team_id
        if roster_id in mappings:
            print(f"  {roster_id} -> {mappings[roster_id]} (predefined)")
        else:
            # Try to find a match by checking if official team_id is contained in roster_id
            found = False
            for official_id, team_name in teams.items():
                if official_id in roster_id or roster_id in official_id:
                    print(f"  {roster_id} -> {official_id} ({team_name}) (suggested)")
                    mappings[roster_id] = official_id
                    found = True
                    break
            if not found:
                print(f"  {roster_id} -> NO MATCH FOUND")

    return mappings

def apply_fixes(mappings):
    client = bigquery.Client()

    for old_id, new_id in mappings.items():
        print(f"\nUpdating {old_id} -> {new_id}...")
        query = f"""
        UPDATE `prodigy-ranking.algorithm_core.nepsac_rosters`
        SET team_id = '{new_id}'
        WHERE team_id = '{old_id}'
        """
        job = client.query(query)
        job.result()
        print(f"  Updated {job.num_dml_affected_rows} rows")

if __name__ == "__main__":
    mappings = main()

    if mappings:
        print("\n" + "="*60)
        print("Applying fixes...")
        apply_fixes(mappings)
        print("\nDone! Verify by testing the API.")

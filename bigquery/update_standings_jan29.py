"""Update NEPSAC standings from January 29, 2026 data"""
from google.cloud import bigquery
import re

client = bigquery.Client(project='prodigy-ranking')

# Full standings data as of January 29, 2026 03:43 AM Eastern
standings_data = [
    # Rank, Team, Wins, Losses, Ties, Win%, GF, GA
    (1, "Cushing Academy", 17, 1, 1, 92.11, 93, 36),
    (2, "Salisbury School", 14, 2, 2, 83.33, 65, 32),
    (3, "Avon Old Farms", 14, 3, 1, 80.56, 71, 38),
    (4, "Dexter Southfield", 15, 4, 0, 78.95, 77, 43),
    (5, "Kimball Union", 14, 4, 0, 77.78, 59, 32),
    (6, "Tabor Academy", 13, 4, 2, 73.68, 66, 45),
    (7, "Nobles", 12, 4, 1, 73.53, 48, 32),
    (8, "Kent School", 12, 4, 2, 72.22, 72, 40),
    (9, "Taft School", 12, 5, 2, 68.42, 66, 46),
    (10, "St. Sebastians", 12, 5, 1, 69.44, 68, 39),
    (11, "Belmont Hill", 10, 5, 1, 65.63, 43, 31),
    (12, "Berkshire School", 10, 5, 2, 64.71, 54, 38),
    (13, "Canterbury School", 11, 6, 1, 63.89, 77, 60),
    (14, "St. Marks School", 10, 6, 1, 61.76, 67, 51),
    (15, "Hotchkiss School", 10, 6, 2, 61.11, 56, 49),
    (16, "Groton School", 10, 6, 1, 61.76, 54, 43),
    (17, "Westminster School", 10, 7, 1, 58.33, 57, 47),
    (18, "New Hampton", 10, 7, 1, 58.33, 73, 57),
    (19, "Governors Academy", 9, 7, 2, 55.56, 58, 57),
    (20, "Pomfret School", 9, 7, 2, 55.56, 61, 55),
    (21, "Rivers School", 8, 7, 1, 53.13, 55, 53),
    (22, "Brunswick School", 7, 6, 2, 53.33, 32, 30),
    (23, "Choate Rosemary Hall", 8, 7, 2, 52.94, 50, 49),
    (24, "St. Pauls School", 8, 8, 2, 50, 60, 59),
    (25, "Andover", 7, 7, 2, 50, 48, 50),
    (26, "New Hampton School", 9, 8, 1, 52.78, 56, 54),  # This might be duplicate - using data as provided
    (27, "Loomis Chaffee", 8, 8, 2, 50, 51, 53),
    (28, "Worcester Academy", 8, 8, 1, 50, 46, 51),
    (29, "BB&N", 8, 8, 1, 50, 51, 53),
    (30, "Millbrook School", 8, 8, 1, 50, 58, 52),
    (31, "Brooks School", 7, 8, 0, 46.67, 34, 39),
    (32, "Milton Academy", 7, 8, 1, 46.88, 56, 56),
    (33, "Lawrence Academy", 7, 8, 2, 47.06, 52, 49),
    (34, "Frederick Gunn", 7, 9, 2, 44.44, 56, 59),
    (35, "Kingswood Oxford", 6, 8, 2, 43.75, 40, 50),
    (36, "Deerfield Academy", 6, 9, 3, 41.67, 54, 60),
    (37, "Middlesex School", 6, 9, 2, 41.18, 44, 51),
    (38, "Thayer Academy", 6, 9, 2, 41.18, 53, 63),
    (39, "Winchendon School", 6, 10, 2, 38.89, 49, 57),
    (40, "Exeter", 6, 10, 1, 38.24, 44, 56),
    (41, "Holderness", 5, 9, 2, 37.5, 50, 59),
    (42, "St. Georges School", 5, 10, 2, 35.29, 40, 54),
    (43, "Kents Hill", 4, 8, 1, 34.62, 30, 43),
    (44, "Tilton School", 4, 10, 2, 31.25, 43, 63),
    (45, "Williston-Northampton", 4, 10, 2, 31.25, 40, 61),
    (46, "North Yarmouth", 4, 11, 1, 28.13, 35, 52),
    (47, "Pingree School", 3, 9, 2, 28.57, 26, 45),
    (48, "St. Lukes School", 3, 10, 2, 26.67, 32, 50),
    (49, "Gunnery", 3, 11, 2, 25, 30, 55),
    (50, "Brewster Academy", 3, 11, 2, 25, 32, 61),
    (51, "Proctor Academy", 5, 14, 0, 26.32, 52, 85),
    (52, "Trinity-Pawling", 2, 7, 1, 25, 34, 48),
    (53, "Hebron", 3, 11, 2, 25, 31, 70),
    (54, "Portsmouth Abbey", 3, 11, 1, 23.33, 36, 60),
    (55, "Hoosac", 2, 8, 1, 22.73, 15, 41),
    (56, "Albany Academy", 4, 16, 1, 21.43, 36, 100),
    (57, "Vermont Academy", 3, 16, 1, 17.5, 32, 84),
    (58, "NMH", 3, 18, 0, 14.29, 44, 116),
    (59, "Wilbraham & Monson", 0, 6, 0, 0, 8, 60),
]

# Team name to team_id mapping
team_id_map = {
    "Cushing Academy": "cushing",
    "Salisbury School": "salisbury",
    "Avon Old Farms": "avon-old-farms",
    "Dexter Southfield": "dexter-southfield",
    "Kimball Union": "kimball-union",
    "Tabor Academy": "tabor",
    "Nobles": "nobles",
    "Kent School": "kent",
    "Taft School": "taft",
    "St. Sebastians": "st-sebastians",
    "Belmont Hill": "belmont-hill",
    "Berkshire School": "berkshire",
    "Canterbury School": "canterbury",
    "St. Marks School": "st-marks",
    "Hotchkiss School": "hotchkiss",
    "Groton School": "groton",
    "Westminster School": "westminster",
    "New Hampton": "new-hampton",
    "New Hampton School": "new-hampton",
    "Governors Academy": "governors",
    "Pomfret School": "pomfret",
    "Rivers School": "rivers",
    "Brunswick School": "brunswick",
    "Choate Rosemary Hall": "choate",
    "St. Pauls School": "st-pauls",
    "Andover": "andover",
    "Loomis Chaffee": "loomis",
    "Worcester Academy": "worcester",
    "BB&N": "bbn",
    "Millbrook School": "millbrook",
    "Brooks School": "brooks",
    "Milton Academy": "milton",
    "Lawrence Academy": "lawrence",
    "Frederick Gunn": "frederick-gunn",
    "Kingswood Oxford": "kingswood-oxford",
    "Deerfield Academy": "deerfield",
    "Middlesex School": "middlesex",
    "Thayer Academy": "thayer",
    "Winchendon School": "winchendon",
    "Exeter": "exeter",
    "Holderness": "holderness",
    "St. Georges School": "st-georges",
    "Kents Hill": "kents-hill",
    "Tilton School": "tilton",
    "Williston-Northampton": "williston",
    "North Yarmouth": "north-yarmouth",
    "Pingree School": "pingree",
    "St. Lukes School": "st-lukes",
    "Gunnery": "gunnery",
    "Brewster Academy": "brewster",
    "Proctor Academy": "proctor",
    "Trinity-Pawling": "trinity-pawling",
    "Hebron": "hebron",
    "Portsmouth Abbey": "portsmouth-abbey",
    "Hoosac": "hoosac",
    "Albany Academy": "albany",
    "Vermont Academy": "vermont-academy",
    "NMH": "nmh",
    "Wilbraham & Monson": "wilbraham-monson",
}

def update_standings():
    """Update nepsac_standings table with new records"""
    print("Updating standings...")

    for rank, team, wins, losses, ties, win_pct, gf, ga in standings_data:
        team_id = team_id_map.get(team)
        if not team_id:
            print(f"  WARNING: No team_id mapping for '{team}'")
            continue

        games_played = wins + losses + ties
        goal_diff = gf - ga
        points = (wins * 2) + ties  # Standard hockey points

        # Check if record exists
        check_query = f"""
        SELECT standing_id FROM `prodigy-ranking.algorithm_core.nepsac_standings`
        WHERE team_id = '{team_id}' AND season = '2025-26'
        """
        rows = list(client.query(check_query).result())

        if rows:
            # Update existing
            update_query = f"""
            UPDATE `prodigy-ranking.algorithm_core.nepsac_standings`
            SET wins = {wins},
                losses = {losses},
                ties = {ties},
                goals_for = {gf},
                goals_against = {ga},
                goal_differential = {goal_diff},
                points = {points},
                win_pct = {win_pct / 100},
                games_played = {games_played},
                last_updated = FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', CURRENT_TIMESTAMP())
            WHERE team_id = '{team_id}' AND season = '2025-26'
            """
            client.query(update_query).result()
        else:
            # Insert new
            standing_id = f"{team_id}_2025-26"
            insert_query = f"""
            INSERT INTO `prodigy-ranking.algorithm_core.nepsac_standings`
            (standing_id, team_id, season, wins, losses, ties, goals_for, goals_against,
             goal_differential, points, win_pct, games_played, last_updated)
            VALUES ('{standing_id}', '{team_id}', '2025-26', {wins}, {losses}, {ties},
                    {gf}, {ga}, {goal_diff}, {points}, {win_pct / 100}, {games_played}, FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', CURRENT_TIMESTAMP()))
            """
            client.query(insert_query).result()

        print(f"  {rank}. {team} ({wins}-{losses}-{ties})")

def update_rankings():
    """Update ranking field in nepsac_team_rankings based on win percentage"""
    print("\nUpdating power rankings based on standings...")

    for rank, team, wins, losses, ties, win_pct, gf, ga in standings_data:
        team_id = team_id_map.get(team)
        if not team_id:
            continue

        # Update the rank in team_rankings
        update_query = f"""
        UPDATE `prodigy-ranking.algorithm_core.nepsac_team_rankings`
        SET rank = {rank},
            calculated_at = FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', CURRENT_TIMESTAMP())
        WHERE team_id = '{team_id}' AND season = '2025-26'
        """
        try:
            client.query(update_query).result()
        except Exception as e:
            print(f"  Could not update ranking for {team_id}: {e}")

def verify_updates():
    """Verify the updates were successful"""
    print("\nVerifying updates...")

    query = """
    SELECT
        s.team_id,
        s.wins, s.losses, s.ties,
        s.goals_for, s.goals_against,
        r.rank
    FROM `prodigy-ranking.algorithm_core.nepsac_standings` s
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` r
        ON s.team_id = r.team_id AND s.season = r.season
    WHERE s.season = '2025-26'
    ORDER BY r.rank
    LIMIT 10
    """

    rows = list(client.query(query).result())
    print("\nTop 10 teams by ranking:")
    for row in rows:
        print(f"  #{row.rank} {row.team_id}: {row.wins}-{row.losses}-{row.ties} (GF:{row.goals_for} GA:{row.goals_against})")

if __name__ == "__main__":
    print("=" * 60)
    print("NEPSAC Standings Update - January 29, 2026")
    print("=" * 60)

    update_standings()
    update_rankings()
    verify_updates()

    print("\n" + "=" * 60)
    print("Standings update complete!")
    print("=" * 60)

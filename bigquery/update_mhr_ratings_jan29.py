"""Update NEPSAC team rankings with MHR ratings data"""
from google.cloud import bigquery

client = bigquery.Client(project='prodigy-ranking')

# MHR ratings data from January 29, 2026
# Rank, Team, Record (W-L-T), Rating, AGD, Schedule
mhr_data = [
    (1, "St Marks School", "13-3-0", 99.76, 4.50, 95.26),
    (2, "Dexter School", "17-2-2", 99.43, 3.04, 96.38),
    (3, "Avon Old Farms", "12-1-1", 99.09, 2.42, 96.66),
    (4, "Salisbury School", "15-4-1", 98.58, 1.65, 96.93),
    (5, "Hotchkiss School", "7-3-4", 98.15, 1.07, 97.08),
    (6, "Tabor Academy", "12-4-1", 98.15, 1.76, 96.38),
    (7, "Kimball Union Academy", "17-5-1", 98.11, 2.13, 95.98),
    (8, "Brunswick School", "14-5-0", 97.85, 2.57, 95.27),
    (9, "Berkshire School", "12-7-2", 97.74, 2.00, 95.74),
    (10, "Belmont Hill", "13-6-0", 97.63, 1.05, 96.57),
    (11, "St Pauls School", "11-6-1", 97.49, 1.22, 96.27),
    (12, "Canterbury School", "11-6-4", 97.46, 0.61, 96.84),
    (13, "Cushing Academy", "11-11-1", 97.44, 0.52, 96.92),
    (14, "Deerfield Academy", "7-5-4", 97.32, 0.62, 96.69),
    (15, "Frederick Gunn School", "9-9-3", 97.26, 0.33, 96.92),
    (16, "Rivers School", "7-5-1", 97.22, 0.76, 96.45),
    (17, "Holderness School", "9-4-0", 97.13, 1.69, 95.44),
    (18, "Westminster School", "7-6-3", 97.13, 0.50, 96.63),
    (19, "Winchendon School", "13-8-2", 97.07, 1.56, 95.50),
    (20, "Phillips Academy Andover", "10-7-0", 97.07, 0.52, 96.54),
    (21, "Milton Academy", "9-9-1", 97.04, 0.47, 96.56),
    (22, "Williston Northampton School", "8-8-1", 97.00, 1.23, 95.77),
    (23, "St Sebastians School", "9-5-0", 96.94, 0.92, 96.01),
    (24, "Kent School", "8-11-1", 96.91, -0.25, 97.16),
    (25, "Thayer Academy", "8-5-3", 96.86, 0.18, 96.67),
    (26, "Governors Academy", "7-8-3", 96.68, 0.16, 96.52),
    (27, "Lawrence Academy", "7-7-1", 96.65, 0.13, 96.52),
    (28, "Pomfret School", "11-6-1", 96.58, 1.33, 95.24),
    (29, "Taft School", "7-11-0", 96.50, -0.50, 97.00),
    (30, "Loomis Chaffee", "6-6-2", 96.49, -0.57, 97.06),
    (31, "Choate Rosemary Hall", "6-8-0", 96.37, -0.64, 97.01),
    (32, "Groton School", "10-8-0", 96.21, 0.50, 95.71),
    (33, "Noble & Greenough School", "7-9-0", 96.11, -0.81, 96.92),
    (34, "Trinity-Pawling School", "3-9-3", 96.05, -1.06, 97.12),
    (35, "Phillips Academy Exeter", "6-9-1", 95.57, -0.81, 96.38),
    (36, "Millbrook School", "11-10-0", 95.51, -0.04, 95.55),
    (37, "Tilton School", "4-7-1", 95.30, 0.00, 95.30),
    (38, "Middlesex School", "7-6-2", 95.29, 0.26, 95.02),
    (39, "St Georges School", "6-9-2", 95.19, -1.17, 96.36),
    (40, "New Hampton School", "8-10-0", 95.04, -0.88, 95.93),
    (41, "Austin Prep", "13-4-2", 94.77, 2.05, 92.72),
    (42, "Roxbury Latin School", "7-5-2", 94.38, -0.42, 94.80),
    (43, "Berwick Academy", "6-9-2", 94.10, -0.35, 94.45),
    (44, "Proctor Academy", "4-11-0", 93.95, -1.80, 95.75),
    (45, "Portsmouth Abbey School", "2-7-1", 93.94, -2.00, 95.94),
    (46, "Pingree School", "4-5-2", 93.83, -0.90, 94.74),
    (47, "Brooks School", "4-11-0", 93.63, -2.06, 95.70),
    (48, "Vermont Academy", "2-12-0", 93.24, -2.64, 95.88),
    (49, "Buckingham Browne & Nichols", "6-9-0", 93.05, -1.26, 94.31),
    (50, "Kents Hill School", "6-11-3", 92.96, -1.50, 94.46),
    (51, "Albany Academy", "4-15-0", 92.67, -2.84, 95.51),
    (52, "Worcester Academy", "4-9-0", 92.66, -2.46, 95.12),
    (53, "North Yarmouth Academy", "5-9-2", 92.64, -1.75, 94.39),
    (54, "Brewster Academy", "3-6-0", 92.43, -3.22, 95.65),
    (55, "Mount Saint Charles Academy", "7-8-1", 92.40, 0.00, 92.40),
    (56, "Hoosac School", "3-8-0", 92.17, -2.18, 94.35),
    (57, "Hebron Academy", "2-11-2", 92.13, -2.00, 94.13),
    (58, "Northfield Mount Hermon School", "3-17-0", 92.02, -3.50, 95.52),
]

# Team name to team_id mapping
team_id_map = {
    "St Marks School": "st-marks",
    "Dexter School": "dexter-southfield",
    "Avon Old Farms": "avon-old-farms",
    "Salisbury School": "salisbury",
    "Hotchkiss School": "hotchkiss",
    "Tabor Academy": "tabor",
    "Kimball Union Academy": "kimball-union",
    "Brunswick School": "brunswick",
    "Berkshire School": "berkshire",
    "Belmont Hill": "belmont-hill",
    "St Pauls School": "st-pauls",
    "Canterbury School": "canterbury",
    "Cushing Academy": "cushing",
    "Deerfield Academy": "deerfield",
    "Frederick Gunn School": "frederick-gunn",
    "Rivers School": "rivers",
    "Holderness School": "holderness",
    "Westminster School": "westminster",
    "Winchendon School": "winchendon",
    "Phillips Academy Andover": "andover",
    "Milton Academy": "milton",
    "Williston Northampton School": "williston",
    "St Sebastians School": "st-sebastians",
    "Kent School": "kent",
    "Thayer Academy": "thayer",
    "Governors Academy": "governors",
    "Lawrence Academy": "lawrence",
    "Pomfret School": "pomfret",
    "Taft School": "taft",
    "Loomis Chaffee": "loomis",
    "Choate Rosemary Hall": "choate",
    "Groton School": "groton",
    "Noble & Greenough School": "nobles",
    "Trinity-Pawling School": "trinity-pawling",
    "Phillips Academy Exeter": "exeter",
    "Millbrook School": "millbrook",
    "Tilton School": "tilton",
    "Middlesex School": "middlesex",
    "St Georges School": "st-georges",
    "New Hampton School": "new-hampton",
    "Austin Prep": "austin-prep",
    "Roxbury Latin School": "roxbury-latin",
    "Berwick Academy": "berwick",
    "Proctor Academy": "proctor",
    "Portsmouth Abbey School": "portsmouth-abbey",
    "Pingree School": "pingree",
    "Brooks School": "brooks",
    "Vermont Academy": "vermont-academy",
    "Buckingham Browne & Nichols": "bbn",
    "Kents Hill School": "kents-hill",
    "Albany Academy": "albany",
    "Worcester Academy": "worcester",
    "North Yarmouth Academy": "north-yarmouth",
    "Brewster Academy": "brewster",
    "Mount Saint Charles Academy": "mount-saint-charles",
    "Hoosac School": "hoosac",
    "Hebron Academy": "hebron",
    "Northfield Mount Hermon School": "nmh",
}

def add_mhr_columns():
    """Add MHR rating columns if they don't exist"""
    print("Adding MHR columns...")
    try:
        # Check if columns exist
        table = client.get_table('prodigy-ranking.algorithm_core.nepsac_team_rankings')
        existing_cols = [f.name for f in table.schema]

        new_cols = []
        if 'mhr_rating' not in existing_cols:
            new_cols.append('mhr_rating FLOAT64')
        if 'mhr_agd' not in existing_cols:
            new_cols.append('mhr_agd FLOAT64')
        if 'mhr_schedule' not in existing_cols:
            new_cols.append('mhr_schedule FLOAT64')
        if 'mhr_rank' not in existing_cols:
            new_cols.append('mhr_rank INTEGER')

        if new_cols:
            for col in new_cols:
                alter_query = f"""
                ALTER TABLE `prodigy-ranking.algorithm_core.nepsac_team_rankings`
                ADD COLUMN {col}
                """
                client.query(alter_query).result()
                print(f"  Added column: {col.split()[0]}")
        else:
            print("  All MHR columns already exist")
    except Exception as e:
        print(f"  Error adding columns: {e}")

def update_mhr_ratings():
    """Update MHR ratings for all teams"""
    print("\nUpdating MHR ratings...")

    for mhr_rank, team, record, rating, agd, schedule in mhr_data:
        team_id = team_id_map.get(team)
        if not team_id:
            print(f"  WARNING: No team_id mapping for '{team}'")
            continue

        # Check if team exists in rankings
        check_query = f"""
        SELECT ranking_id FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
        WHERE team_id = '{team_id}' AND season = '2025-26'
        """
        rows = list(client.query(check_query).result())

        if rows:
            # Update existing
            update_query = f"""
            UPDATE `prodigy-ranking.algorithm_core.nepsac_team_rankings`
            SET mhr_rating = {rating},
                mhr_agd = {agd},
                mhr_schedule = {schedule},
                mhr_rank = {mhr_rank},
                rank = {mhr_rank},
                calculated_at = FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', CURRENT_TIMESTAMP())
            WHERE team_id = '{team_id}' AND season = '2025-26'
            """
            client.query(update_query).result()
            print(f"  #{mhr_rank} {team} - Rating: {rating}, AGD: {agd}")
        else:
            # Insert new record
            ranking_id = f"{team_id}_2025-26"
            insert_query = f"""
            INSERT INTO `prodigy-ranking.algorithm_core.nepsac_team_rankings`
            (ranking_id, team_id, season, rank, mhr_rating, mhr_agd, mhr_schedule, mhr_rank, calculated_at)
            VALUES ('{ranking_id}', '{team_id}', '2025-26', {mhr_rank}, {rating}, {agd}, {schedule}, {mhr_rank},
                    FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', CURRENT_TIMESTAMP()))
            """
            client.query(insert_query).result()
            print(f"  #{mhr_rank} {team} (NEW) - Rating: {rating}")

def update_predictions():
    """Update predictions for upcoming games based on MHR rankings"""
    print("\nUpdating game predictions...")

    # Get upcoming games
    games_query = """
    SELECT game_id, home_team_id, away_team_id, game_date
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE game_date >= CURRENT_DATE()
    ORDER BY game_date
    """

    games = list(client.query(games_query).result())
    print(f"  Found {len(games)} upcoming games")

    # Build rating lookup
    ratings_query = """
    SELECT team_id, mhr_rating, mhr_rank, rank
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
    WHERE season = '2025-26'
    """
    ratings = {r.team_id: {'rating': r.mhr_rating or 95, 'rank': r.mhr_rank or r.rank or 30}
               for r in client.query(ratings_query).result()}

    updated = 0
    for game in games:
        home_data = ratings.get(game.home_team_id, {'rating': 95, 'rank': 30})
        away_data = ratings.get(game.away_team_id, {'rating': 95, 'rank': 30})

        home_rating = home_data['rating']
        away_rating = away_data['rating']

        # Calculate win probability (higher rating = higher chance, with home advantage)
        home_advantage = 1.5  # Rating points for home ice
        adjusted_home = home_rating + home_advantage

        # Logistic-style probability
        rating_diff = adjusted_home - away_rating
        home_win_prob = 1 / (1 + 10 ** (-rating_diff / 10))

        # Determine predicted winner
        if home_win_prob >= 0.5:
            winner_id = game.home_team_id
            confidence = home_win_prob
        else:
            winner_id = game.away_team_id
            confidence = 1 - home_win_prob

        # Update prediction
        update_query = f"""
        UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule`
        SET predicted_winner_id = '{winner_id}',
            prediction_confidence = {confidence:.3f}
        WHERE game_id = '{game.game_id}'
        """
        try:
            client.query(update_query).result()
            updated += 1
        except Exception as e:
            pass

    print(f"  Updated {updated} game predictions")

def verify_updates():
    """Verify the MHR updates"""
    print("\nVerifying MHR rankings...")

    query = """
    SELECT team_id, rank, mhr_rating, mhr_agd, mhr_schedule, mhr_rank
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
    WHERE season = '2025-26' AND mhr_rating IS NOT NULL
    ORDER BY mhr_rank
    LIMIT 15
    """

    rows = list(client.query(query).result())
    print("\nTop 15 teams by MHR rating:")
    for row in rows:
        print(f"  #{row.mhr_rank} {row.team_id}: {row.mhr_rating} (AGD: {row.mhr_agd}, Sched: {row.mhr_schedule})")

if __name__ == "__main__":
    print("=" * 60)
    print("MHR Ratings Update - January 29, 2026")
    print("=" * 60)

    add_mhr_columns()
    update_mhr_ratings()
    update_predictions()
    verify_updates()

    print("\n" + "=" * 60)
    print("MHR ratings update complete!")
    print("=" * 60)

"""
Factor 28: NHL Scouting Report (F28 NHLSR) - V2 with Fuzzy Matching
====================================================================
Improved matching using fuzzy string matching and multiple strategies.
"""

import pandas as pd
from google.cloud import bigquery
from rapidfuzz import fuzz, process
import re

PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"

def calculate_points(rank, total_players, max_points=1000, min_points=500):
    """Calculate points using linear interpolation."""
    if total_players == 1:
        return max_points
    points = max_points - (rank - 1) * (max_points - min_points) / (total_players - 1)
    return round(points, 1)

def normalize_name(name):
    """Normalize name for matching."""
    if pd.isna(name):
        return ""
    name = str(name).lower().strip()

    # Handle "LAST, FIRST" format
    if "," in name:
        parts = name.split(",")
        name = f"{parts[1].strip()} {parts[0].strip()}"

    # Remove special characters but keep spaces and hyphens
    name = re.sub(r"['\.\"]", "", name)

    # Normalize spaces
    name = " ".join(name.split())

    return name

def normalize_name_for_search(name):
    """Create multiple name variants for searching."""
    base = normalize_name(name)
    variants = [base]

    # Handle initials like "JP" -> "j.p." or "j p"
    words = base.split()
    if len(words) >= 2:
        # First name might be initials
        first = words[0]
        if len(first) == 2 and first.isalpha():
            # "jp" -> "j.p.", "j p", "j-p"
            expanded = f"{first[0]}.{first[1]}."
            variants.append(f"{expanded} {' '.join(words[1:])}")
            expanded2 = f"{first[0]} {first[1]}"
            variants.append(f"{expanded2} {' '.join(words[1:])}")

        # Try with/without middle names
        if len(words) > 2:
            variants.append(f"{words[0]} {words[-1]}")  # First + Last only

    # Handle hyphenated names
    if "-" in base:
        variants.append(base.replace("-", " "))
        variants.append(base.replace("-", ""))

    # Handle apostrophes in original
    if "'" in name.lower():
        variants.append(base.replace("'", ""))

    return list(set(variants))

def get_birth_year_from_date(birthdate):
    """Extract birth year from date string like '20-Dec-2007'."""
    try:
        parts = birthdate.split("-")
        return int(parts[2])
    except:
        return None

def fuzzy_match_player(name_variants, birth_year, bq_players, threshold=85):
    """
    Try to fuzzy match a player using multiple strategies.
    Returns (player_id, match_type, score) or (None, None, 0)
    """
    # Filter by birth year first (if available)
    if birth_year:
        candidates = bq_players[bq_players['birth_year'] == birth_year].copy()
    else:
        candidates = bq_players.copy()

    if len(candidates) == 0:
        candidates = bq_players.copy()  # Fall back to all players

    best_match = None
    best_score = 0
    best_type = None

    for variant in name_variants:
        if len(candidates) == 0:
            continue

        # Use rapidfuzz to find best match
        result = process.extractOne(
            variant,
            candidates['normalized_name'].tolist(),
            scorer=fuzz.WRatio,
            score_cutoff=threshold
        )

        if result and result[1] > best_score:
            best_score = result[1]
            matched_name = result[0]
            matched_row = candidates[candidates['normalized_name'] == matched_name].iloc[0]
            best_match = int(matched_row['player_id'])
            best_type = f"fuzzy_{int(best_score)}"

    return best_match, best_type, best_score

# ============================================================================
# DATA FROM PDFs - NHL Central Scouting Mid-Term Rankings 2025/2026
# ============================================================================

# North American Skaters (225 players including LV)
na_skaters = [
    (1, "MCKENNA, GAVIN", "PENN STATE", "BIG10", "20-Dec-2007", "LW"),
    (2, "VERHOEFF, KEATON", "NORTH DAKOTA", "NCHC", "19-Jun-2008", "D"),
    (3, "CARELS, CARSON", "PRINCE GEORGE", "WHL", "23-Jun-2008", "D"),
    (4, "REID, CHASE", "SAULT STE. MARIE", "OHL", "30-Dec-2007", "D"),
    (5, "MALHOTRA, CALEB", "BRANTFORD", "OHL", "02-Jun-2008", "C"),
    (6, "RUDOLPH, DAXON", "PRINCE ALBERT", "WHL", "06-Mar-2008", "D"),
    (7, "LAWRENCE, TYNAN", "BOSTON UNIVERSITY", "H-EAST", "03-Aug-2008", "C"),
    (8, "MOROZOV, ILIA", "MIAMI", "NCHC", "03-Aug-2008", "C"),
    (9, "BELCHETZ, ETHAN", "WINDSOR", "OHL", "30-Mar-2008", "LW"),
    (10, "HURLBERT, JP", "KAMLOOPS", "WHL", "11-Apr-2008", "LW"),
    (11, "HEMMING, OSCAR", "BOSTON COLLEGE", "H-EAST", "13-Aug-2008", "LW"),
    (12, "NOVOTNY, ADAM", "PETERBOROUGH", "OHL", "13-Nov-2007", "LW"),
    (13, "LIN, RYAN", "VANCOUVER", "WHL", "18-Apr-2008", "D"),
    (14, "ROGOWSKI, BROOKS", "OSHAWA", "OHL", "24-Jun-2008", "C"),
    (15, "VILLENEUVE, XAVIER", "BLAINVILLE-BOISBRIAND", "QMJHL", "29-Sep-2007", "D"),
    (16, "KLEPOV, NIKITA", "SAGINAW", "OHL", "27-Jun-2008", "RW"),
    (17, "SHILOV, EGOR", "VICTORIAVILLE", "QMJHL", "30-Apr-2008", "C"),
    (18, "DAGENAIS, MADDOX", "QUEBEC", "QMJHL", "27-Mar-2008", "C"),
    (19, "DI IORIO, ALESSANDRO", "SARNIA", "OHL", "17-Mar-2008", "C"),
    (20, "MACBEATH, BEN", "CALGARY", "WHL", "04-Mar-2008", "D"),
    (21, "VANECEK, JAKUB", "TRI-CITY", "WHL", "25-Feb-2008", "D"),
    (22, "CALI, RYDER", "NORTH BAY", "OHL", "06-Sep-2008", "C"),
    (23, "CULLEN, WYATT", "USA U-18", "NTDP - USHL", "08-Sep-2008", "LW"),
    (24, "PRESTON, MATHIS", "VANCOUVER", "WHL", "21-Jul-2008", "RW"),
    (25, "VANDENBERG, THOMAS", "OTTAWA", "OHL", "08-Sep-2008", "C"),
    (26, "RUCK, LIAM", "MEDICINE HAT", "WHL", "21-Feb-2008", "RW"),
    (27, "ROOBROECK, RYAN", "NIAGARA", "OHL", "25-Sep-2007", "LW"),
    (28, "NYCZ, LANDON", "UMASS", "H-EAST", "04-Oct-2007", "D"),
    (29, "MORRISON, CHARLIE", "QUEBEC", "QMJHL", "12-Oct-2007", "D"),
    (30, "MUTRYN, CASEY", "USA U-18", "NTDP - USHL", "05-Jul-2008", "RW"),
    (31, "RUCK, MARKUS", "MEDICINE HAT", "WHL", "21-Feb-2008", "C"),
    (32, "HARRINGTON, CHASE", "SPOKANE", "WHL", "30-Oct-2007", "LW"),
    (33, "HEXTALL, JACK", "YOUNGSTOWN", "USHL", "23-Mar-2008", "C"),
    (34, "LISKE, BREK", "EVERETT", "WHL", "09-Jan-2008", "D"),
    (35, "BLEYL, TOMMY", "MONCTON", "QMJHL", "01-Dec-2007", "D"),
    (36, "PLANTE, VICTOR", "USA U-18", "NTDP - USHL", "10-Mar-2008", "LW"),
    (37, "SCHAIRER, LUKE", "USA U-18", "NTDP - USHL", "30-Jan-2008", "D"),
    (38, "BILECKI, ALEXANDER", "KITCHENER", "OHL", "09-May-2008", "D"),
    (39, "BARABANOV, EGOR", "SAGINAW", "OHL", "16-May-2006", "C"),
    (40, "DRAVECKY, VLADIMIR", "BRANTFORD", "OHL", "19-Dec-2007", "D"),
    (41, "FITZGERALD, COLIN", "SAULT STE. MARIE", "OHL", "01-Apr-2008", "C"),
    (42, "WILLIAMS, COOPER", "SASKATOON", "WHL", "18-Feb-2008", "C"),
    (43, "OLSEN, ZACH", "SASKATOON", "WHL", "16-Mar-2008", "RW"),
    (44, "MBUYI, PIERCE", "OWEN SOUND", "OHL", "17-Apr-2008", "LW"),
    (45, "COVER, JAXON", "LONDON", "OHL", "13-Feb-2008", "RW"),
    (46, "EDWARDS, BECKHAM", "SARNIA", "OHL", "06-Jan-2008", "C"),
    (47, "ZURAWSKI, COLE", "OWEN SOUND", "OHL", "06-Feb-2008", "RW"),
    (48, "HAFELE, LANDON", "GREEN BAY", "USHL", "18-Sep-2007", "C"),
    (49, "BERZKALNS, RUDOLFS", "MUSKEGON", "USHL", "03-Mar-2008", "C"),
    (50, "WASSILYN, BRAIDY", "LONDON", "OHL", "28-May-2008", "LW"),
    (51, "ROYSTON, WESLEY", "OWEN SOUND", "OHL", "22-Nov-2007", "RW"),
    (52, "GUSTAFSON, JAKE", "PORTLAND", "WHL", "03-Apr-2008", "C"),
    (53, "RUNTSO, TIMOFEI", "VICTORIA", "WHL", "06-Jul-2007", "D"),
    (54, "STEVENS, CARTER", "GUELPH", "OHL", "11-Jan-2008", "RW"),
    (55, "KOSICK, NOAH", "SEATTLE", "WHL", "18-Aug-2008", "C"),
    (56, "ZIELINSKI, BLAKE", "DES MOINES", "USHL", "05-Mar-2008", "C"),
    (57, "BEUKER, DAYNE", "USA U-18", "NTDP - USHL", "23-Mar-2008", "C"),
    (58, "PANTELAS, GIORGOS", "BRANDON", "WHL", "24-Apr-2008", "D"),
    (59, "CROSKERY, CALLUM", "SAULT STE. MARIE", "OHL", "29-Jan-2008", "D"),
    (60, "KUEHNE, LINCOLN", "ARIZONA STATE", "NCHC", "28-Nov-2007", "D"),
    (61, "STEINER, LARS", "ROUYN-NORANDA", "QMJHL", "12-Nov-2007", "RW"),
    (62, "GALLACHER, LAYNE", "GUELPH", "OHL", "16-Feb-2008", "C"),
    (63, "SPARKS, TYUS", "SPOKANE", "WHL", "04-Jan-2008", "C"),
    (64, "LEMIRE, KAYDEN", "PRINCE GEORGE", "WHL", "27-Jan-2008", "RW"),
    (65, "KEMPS, JONAS", "CHICAGO", "USHL", "16-Jan-2008", "D"),
    (66, "DOYLE, EDDY", "HALIFAX", "QMJHL", "08-Nov-2007", "D"),
    (67, "HEGER, KYLE", "LETHBRIDGE", "WHL", "21-Sep-2007", "D"),
    (68, "KULEBIAKIN, OLEG", "HALIFAX", "QMJHL", "11-Jan-2008", "RW"),
    (69, "BERCHILD, MICHAEL", "USA U-18", "NTDP - USHL", "16-Feb-2008", "LW"),
    (70, "LEFEBVRE, LIAM", "CHICOUTIMI", "QMJHL", "15-May-2007", "C"),
    (71, "MURNIEKS, OLIVERS", "SAINT JOHN", "QMJHL", "31-Jul-2008", "C"),
    (72, "LANSARD, ZACHARY", "REGINA", "WHL", "29-Jul-2008", "RW"),
    (73, "DUGUAY, JORDAN", "PORTLAND", "WHL", "16-Feb-2008", "LW"),
    (74, "MACKENZIE, ETHAN", "EDMONTON", "WHL", "02-Sep-2006", "D"),
    (75, "HAMILTON, BECKETT", "RED DEER", "WHL", "28-Mar-2008", "C"),
    (76, "VANHANEN, MATIAS", "EVERETT", "WHL", "11-Sep-2007", "LW"),
    (77, "KURTZ, JAYDEN", "ROGERS", "HIGH-MN", "30-Dec-2007", "D"),
    (78, "STUART, LOGAN", "USA U-18", "NTDP - USHL", "23-Apr-2008", "C"),
    (79, "KLIMPKE, BRAYDEN", "SASKATOON", "WHL", "08-Oct-2007", "D"),
    (80, "FRANCISCO, AJ", "USA U-18", "NTDP - USHL", "10-Jan-2008", "D"),
    (81, "TOURNAS, NIKO", "MONCTON", "QMJHL", "17-Feb-2006", "RW"),
    (82, "AMBROSIO, LUCAS", "ERIE", "OHL", "06-Jan-2008", "D"),
    (83, "TROTTIER, PARKER", "USA U-18", "NTDP - USHL", "13-Feb-2008", "LW"),
    (84, "O'DONNELL, AIDEN", "OSHAWA", "OHL", "03-Jan-2008", "LW"),
    (85, "AMRHEIN, LANDON", "CALGARY", "WHL", "06-Apr-2008", "LW"),
    (86, "ERICKSON, JOSEPH", "BLAKE", "HIGH-MN", "21-Apr-2008", "C"),
    (87, "AMIDOVSKI, NATHAN", "BRAMPTON", "OHL", "06-Apr-2008", "LW"),
    (88, "SIVERTSON, JONAH", "PRINCE ALBERT", "WHL", "27-Aug-2008", "RW"),
    (89, "LEVAC, ADAM", "PETERBOROUGH", "OHL", "27-Jun-2008", "C"),
    (90, "CHUDZINSKI, RIAN", "MONCTON", "QMJHL", "30-Dec-2007", "RW"),
    (91, "MCLAUGHLIN, WILL", "PORTLAND", "WHL", "10-Mar-2008", "D"),
    (92, "TAILLEFER, ALEXANDRE", "QUEBEC", "QMJHL", "01-Jan-2008", "D"),
    (93, "KUHTA, JASPER", "OTTAWA", "OHL", "28-Oct-2006", "C"),
    (94, "TA'AMU, ALOFA TUNOA", "EDMONTON", "WHL", "28-May-2008", "D"),
    (95, "CHARTRAND, CAMERON", "SAINT JOHN", "QMJHL", "03-Mar-2008", "D"),
    (96, "DEAN, DYLAN", "EDMONTON", "WHL", "14-May-2008", "C"),
    (97, "ROUSSEAU, THOMAS", "SHERBROOKE", "QMJHL", "12-Feb-2008", "C"),
    (98, "LECHNER, THEODORE", "HOLY ANGELS", "HIGH-MN", "22-Aug-2008", "D"),
    (99, "BRYZGALOV, YAROSLAV", "MEDICINE HAT", "WHL", "23-Mar-2007", "LW"),
    (100, "DINGMAN, SAWYER", "SWIFT CURRENT", "WHL", "11-Sep-2008", "LW"),
    (101, "JOUDREY, CAELAN", "WENATCHEE", "WHL", "17-Jan-2008", "C"),
    (102, "OVCHAROV, NIKITA", "QUEBEC", "QMJHL", "17-Feb-2008", "LW"),
    (103, "LAYLIN, BODE", "TRI-CITY", "USHL", "17-Nov-2007", "D"),
    (104, "BROSNAN, MYLES", "DEXTER SCHOOL", "HIGH-MA", "19-Oct-2007", "D"),
    (105, "RUML, ONDREJ", "OTTAWA", "OHL", "25-Mar-2008", "D"),
    (106, "BOGAS, NICHOLAS", "USA U-18", "NTDP - USHL", "23-Jul-2008", "D"),
    (107, "RHEAUME-MULLEN, DAKODA", "MICHIGAN", "BIG10", "18-Dec-2006", "D"),
    (108, "VLASOV, ALEKSEI", "VICTORIAVILLE", "QMJHL", "02-Feb-2008", "LW"),
    (109, "VALENTINI, ADAM", "MICHIGAN", "BIG10", "11-Apr-2008", "C"),
    (110, "PEPOY, BRODY", "SAGINAW", "OHL", "16-May-2008", "RW"),
    (111, "MCFADDEN, BRIAN", "THAYER ACADEMY", "HIGH-MA", "02-Jan-2008", "D"),
    (112, "XU, JACOB", "LONDON", "OHL", "13-Mar-2008", "D"),
    (113, "DUMONT, DYLAN", "DRUMMONDVILLE", "QMJHL", "19-Aug-2008", "RW"),
    (114, "MANCHUSO, WILLIAM", "ST. MARK'S SCHOOL", "HIGH-MA", "09-Jan-2008", "C"),
    (115, "TUMINARO, COLE", "CHICAGO", "USHL", "24-Jan-2007", "D"),
    (116, "COSSETTE AYOTTE, BENJAMIN", "VAL-D'OR", "QMJHL", "03-Jan-2008", "D"),
    (117, "KOSTOV, ALEX", "FLINT", "OHL", "03-Jun-2006", "RW"),
    (118, "MARTHALER, JACKSON", "USA U-18", "NTDP - USHL", "10-Feb-2008", "D"),
    (119, "BURICK, SEAN", "PENTICTON", "WHL", "09-Jan-2008", "D"),
    (120, "ZAJIC, LUKAS", "USA U-18", "NTDP - USHL", "19-Jan-2008", "RW"),
    (121, "RIEBER, JAMES", "WATERLOO", "USHL", "25-Apr-2008", "D"),
    (122, "LITALIEN, ROMAIN", "CAPE BRETON", "QMJHL", "07-Apr-2008", "RW"),
    (123, "BOURQUE, LOUIS FELIX", "DRUMMONDVILLE", "QMJHL", "15-Jul-2008", "RW"),
    (124, "IGINLA, JOE", "VANCOUVER", "WHL", "13-Aug-2008", "RW"),
    (125, "BIDGOOD, COHEN", "LONDON", "OHL", "11-Jan-2007", "RW"),
    (126, "O'NEILL, ANDREW", "EDMONTON", "WHL", "07-Feb-2007", "C"),
    (127, "ARNETT, ELLIOT", "OWEN SOUND", "OHL", "12-Mar-2008", "D"),
    (128, "KAMAS, JIRI", "RED DEER", "WHL", "04-Mar-2008", "D"),
    (129, "VOIAGA, NIKITA", "CHARLOTTETOWN", "QMJHL", "16-Oct-2007", "D"),
    (130, "REISNECKER, BEN", "NIAGARA", "OHL", "21-Feb-2008", "D"),
    (131, "MYLOSERDNYY, MICHEL", "GATINEAU", "QMJHL", "15-Feb-2008", "D"),
    (132, "SOKOLOVSKII, MAKSIM", "LONDON", "OHL", "12-Jul-2008", "D"),
    (133, "DONIA, KAIDEN", "GROTON", "HIGH-MA", "16-Jan-2008", "D"),
    (134, "MONDOUX, ANDRE", "KINGSTON", "OHL", "16-Mar-2007", "D"),
    (135, "MURNANE, BRADY", "OSHAWA", "OHL", "23-Apr-2008", "D"),
    (136, "DAIGNEAULT, JEAN-SAMUEL", "MUSKEGON", "USHL", "15-Feb-2008", "D"),
    (137, "OLSON, BRETT", "VANCOUVER", "WHL", "24-Feb-2008", "C"),
    (138, "GILLESPIE, BRODY", "SPOKANE", "WHL", "16-Feb-2008", "C"),
    (139, "KRIZIZKE, LINCOLN", "DUBUQUE", "USHL", "08-Apr-2008", "D"),
    (140, "LEGOSTAEV, PETER", "GATINEAU", "QMJHL", "02-Oct-2007", "RW"),
    (141, "VAUGHAN, PARKER", "NORTH BAY", "OHL", "06-Mar-2008", "RW"),
    (142, "KLASSEN, COHEN", "REGINA", "WHL", "08-Sep-2008", "C"),
    (143, "KELLY, BENETT", "PRINCE ALBERT", "WHL", "04-Feb-2008", "D"),
    (144, "SINGH, RYLAN", "GUELPH", "OHL", "04-Oct-2007", "D"),
    (145, "HOULE, FLORENT", "SHERBROOKE", "QMJHL", "04-Aug-2007", "RW"),
    (146, "PITTSLEY, CALEB", "MADISON", "USHL", "16-Nov-2007", "C"),
    (147, "WALTERS, DANIEL", "HALIFAX", "QMJHL", "28-Mar-2008", "C"),
    (148, "YAKUTSENAK, DMITRI", "PRINCE GEORGE", "WHL", "12-Mar-2007", "C"),
    (149, "DEGRAFF, OWEN", "WATERLOO", "USHL", "13-Jan-2008", "RW"),
    (150, "WATHIER, SAM", "USA U-18", "NTDP - USHL", "17-May-2008", "D"),
    (151, "FROSSARD, ERIC", "GUELPH", "OHL", "12-Jan-2008", "D"),
    (152, "PANGRETITSCH, HARRIS", "SAULT STE. MARIE", "OHL", "29-Mar-2008", "D"),
    (153, "FORTIN, ALEXIS", "VAL-D'OR", "QMJHL", "04-Oct-2007", "D"),
    (154, "TOMIK, TOBIAS", "VANCOUVER", "WHL", "18-Dec-2007", "LW"),
    (155, "JARDINE, EVAN", "YOUNGSTOWN", "USHL", "23-Oct-2007", "LW"),
    (156, "FEELEY, COLIN", "OSHAWA", "OHL", "07-Mar-2008", "D"),
    (157, "LASCHON, LEO", "OSHAWA", "OHL", "19-Mar-2008", "D"),
    (158, "ROLSING, DARIAN", "WENATCHEE", "WHL", "14-Feb-2008", "D"),
    (159, "BOYCHUK, RILEY", "PRINCE ALBERT", "WHL", "31-Jan-2008", "C"),
    (160, "SALANDRA, JOSEPH", "BARRIE", "OHL", "15-Feb-2008", "RW"),
    (161, "ROZZI, DYLAN", "SAINT JOHN", "QMJHL", "08-Mar-2008", "LW"),
    (162, "KOLARIK, LEON", "PETERBOROUGH", "OHL", "23-Sep-2007", "LW"),
    (163, "YARED, WILLIAM", "SAINT JOHN", "QMJHL", "21-Jan-2008", "C"),
    (164, "VARGA, KALDER", "RED DEER", "WHL", "24-Jun-2008", "RW"),
    (165, "WILMOTT, BENJAMIN", "BARRIE", "OHL", "30-Aug-2006", "C"),
    (166, "SOUCH, BROCK", "PRINCE GEORGE", "WHL", "11-Oct-2006", "LW"),
    (167, "BROWN, REED", "PORTLAND", "WHL", "22-Feb-2008", "C"),
    (168, "SAWCHYN, LUKAS", "EDMONTON", "WHL", "27-Feb-2007", "C"),
    (169, "BAUMULLER, JOBY", "BRANDON", "WHL", "20-Jul-2007", "RW"),
    (170, "KINGWELL, SHAAN", "OTTAWA", "OHL", "07-Feb-2007", "LW"),
    (171, "LANGLOIS, TRISTAN", "ROUYN-NORANDA", "QMJHL", "14-Jul-2007", "D"),
    (172, "STANKOVEN, MATEJ", "BRAMPTON", "OHL", "28-Feb-2008", "C"),
    (173, "RICARD, EMILE", "CHICOUTIMI", "QMJHL", "18-Nov-2007", "LW"),
    (174, "KORNEYEV, KORNEY", "VICTORIAVILLE", "QMJHL", "16-Oct-2007", "LW"),
    (175, "SARKENOV, ALISHER", "PRINCE ALBERT", "WHL", "15-Dec-2007", "RW"),
    (176, "MARTINU, PAVEL", "SIOUX CITY", "USHL", "20-Dec-2007", "C"),
    (177, "LESIUK, GAVIN", "LETHBRIDGE", "WHL", "14-Jan-2008", "LW"),
    (178, "HARVEY, CADEN", "WINDSOR", "OHL", "13-Feb-2008", "C"),
    (179, "WOOD, CODY", "LONDON", "GOHL", "13-Jun-2008", "D"),
    (180, "MAN, MATYAS", "PRINCE ALBERT", "WHL", "31-May-2006", "D"),
    (181, "MAGNUSSON, CARL-OTTO", "SAINT JOHN", "QMJHL", "11-Jan-2006", "D"),
    (182, "BOSCO, DAVID", "CEDAR RAPIDS", "USHL", "08-Feb-2008", "RW"),
    (183, "SOLLER, COOPER", "SIOUX FALLS", "USHL", "11-Aug-2008", "C"),
    (184, "LEMIEUX, JEAN-CRISTOPH", "SUDBURY", "OHL", "19-Jun-2008", "LW"),
    (185, "SHYBINSKYI, ILLIA", "GUELPH", "OHL", "14-May-2007", "LW"),
    (186, "CYR, SIMON-XAVIER", "GATINEAU", "QMJHL", "11-Mar-2008", "C"),
    (187, "MCLEAN, ALEX", "KINGSTON", "OHL", "08-Aug-2008", "C"),
    (188, "STEEN, RILEY", "MEDICINE HAT", "WHL", "07-Sep-2008", "D"),
    (189, "ALLEN, DRYDEN", "FLINT", "OHL", "09-Aug-2007", "D"),
    (190, "ALLARD, CAMERON", "BRANDON", "WHL", "11-Jan-2008", "D"),
    (191, "HENDERSON, ROWAN", "SUDBURY", "OHL", "10-Dec-2007", "LW"),
    (192, "CAHILL, PHOENIX", "PRINCE GEORGE", "WHL", "07-Jul-2008", "D"),
    (193, "YOUNG, AIDEN", "PETERBOROUGH", "OHL", "18-Apr-2007", "LW"),
    (194, "KARMANOV, ALEXANDER", "NORTH BAY", "OHL", "22-Mar-2008", "D"),
    (195, "DILLARD, CAMERON", "RED DEER", "WHL", "15-May-2008", "D"),
    (196, "KWAJAH, JET", "MADISON", "USHL", "13-Mar-2008", "D"),
    (197, "BROWN, JULIAN", "OWEN SOUND", "OHL", "10-Apr-2006", "D"),
    (198, "ANISIMOV, ARSENII", "PRINCE GEORGE", "WHL", "25-Nov-2007", "D"),
    (199, "MOLGACHEV, ANDREI", "CALGARY", "WHL", "01-Mar-2008", "C"),
    (200, "STEWART, NOLAN", "VICTORIA", "WHL", "12-Jan-2008", "RW"),
    (201, "PUGLISI, CHARLIE", "WINCHENDON", "HIGH-MA", "16-Apr-2008", "C"),
    (202, "DENNIS, COOPER", "BRANTFORD", "OHL", "07-May-2007", "RW"),
    (203, "HANDSOR, JUSTIN", "BARRIE", "OHL", "24-Sep-2007", "D"),
    (204, "DAMPHOUSSE, BO", "SAINT JOHN", "QMJHL", "21-Oct-2007", "D"),
    (205, "KULTGEN, JACK", "GREEN BAY", "USHL", "11-Oct-2007", "D"),
    (206, "THEODORE, ALEX", "PHILLIPS ANDOVER ACADEMY", "HIGH-MA", "21-May-2008", "LW"),
    (207, "TORR, JACK", "FARGO", "USHL", "29-Jul-2008", "C"),
    (208, "KAMZIK, KASE", "ERIE", "OHL", "15-Apr-2008", "LW"),
    (209, "PAVAO, CRUZ", "TRI-CITY", "WHL", "24-Aug-2008", "RW"),
    (210, "KURYACHENKOV, STEPAN", "SWIFT CURRENT", "WHL", "16-Jul-2008", "C"),
    (211, "KUZMA, CAMERON", "RED DEER", "WHL", "17-Jul-2008", "C"),
    (212, "CAREY, RYDER", "NORTH BAY", "OHL", "02-Aug-2008", "C"),
    (213, "STURGIS, ETHAN", "MINNETONKA", "HIGH-MN", "03-Feb-2008", "RW"),
    (214, "PRONIN, ARSENY", "NORTH BAY", "OHL", "16-May-2007", "RW"),
    (215, "MCCANN, KADON", "MEDICINE HAT", "WHL", "25-Mar-2007", "C"),
    (216, "RUDOLPH, BRENDAN", "SWIFT CURRENT", "WHL", "08-Mar-2008", "LW"),
    (217, "WOODALL, CARSON", "WINDSOR", "OHL", "25-May-2006", "D"),
    (218, "NELSON, NICKLAS", "MONTICELLO", "HIGH-MN", "11-Aug-2008", "D"),
    (219, "LOHSE, HUDSON", "DUBUQUE", "USHL", "14-Jun-2008", "D"),
    (220, "MALONEY, NATHAN", "LETHBRIDGE", "WHL", "16-Sep-2006", "D"),
    (221, "SYKORA, NICHOLAS", "OWEN SOUND", "OHL", "24-May-2007", "LW"),
    (222, "CELSKI, NATHANIEL", "MUSKEGON", "USHL", "10-Mar-2008", "D"),
    (223, "PUCHNER, LUKE", "SHATTUCK - ST.MARY'S PREP", "HIGH-MN", "02-Jan-2008", "C"),
    (224, "HODGSON, KAM", "CULVER ACADEMY", "HIGH-IN", "02-Apr-2008", "RW"),
    (225, "SAUER, KENT", "ANDOVER", "HIGH-MN", "24-Oct-2007", "C"),
]

# North American Goalies (37 players)
na_goalies = [
    (1, "KNOWLING, BRADY", "USA U-18", "NTDP - USHL", "09-Mar-2008", "G"),
    (2, "ORSULAK, MICHAL", "PRINCE ALBERT", "WHL", "26-Aug-2007", "G"),
    (3, "TREJBAL, TOBIAS", "YOUNGSTOWN", "USHL", "09-Nov-2007", "G"),
    (4, "LARYS, JAN", "DRUMMONDVILLE", "QMJHL", "14-Feb-2008", "G"),
    (5, "TVRZNIK, TOBIAS", "WENATCHEE", "WHL", "29-Jul-2007", "G"),
    (6, "LACELLE, WILLIAM", "BLAINVILLE-BOISBRIAND", "QMJHL", "26-Dec-2007", "G"),
    (7, "BOETTIGER, HARRISON", "KELOWNA", "WHL", "11-Dec-2007", "G"),
    (8, "SKLENICKA, MAREK", "SEATTLE", "WHL", "27-Aug-2008", "G"),
    (9, "SHAIIKOV, DANAI", "GATINEAU", "QMJHL", "13-Apr-2007", "G"),
    (10, "JOVANOVSKI, ZACHARY", "GUELPH", "OHL", "07-Oct-2007", "G"),
    (11, "MINCHAK, MATTHEW", "KINGSTON", "OHL", "23-May-2007", "G"),
    (12, "CASEY, CARTER", "MEDICINE HAT", "WHL", "03-Dec-2007", "G"),
    (13, "RUZICKA, FILIP", "BRANDON", "WHL", "24-Mar-2008", "G"),
    (14, "YERMOLENKO, VLADISLAV", "NIAGARA", "OHL", "16-Dec-2007", "G"),
    (15, "WENDT, XAVIER", "TRI-CITY", "WHL", "24-Jan-2008", "G"),
    (16, "FETTEROLF, RYDER", "OTTAWA", "OHL", "05-Jan-2008", "G"),
    (17, "SHURYGIN, STEPAN", "SAGINAW", "OHL", "26-Aug-2007", "G"),
    (18, "KITCHENER, DAYTON", "RIMOUSKI", "QMJHL", "02-Oct-2007", "G"),
    (19, "HREBIK, BEN", "BARRIE", "OHL", "04-Apr-2006", "G"),
    (20, "GILLHAM-CIRKA, NICOLAS", "HALIFAX", "QMJHL", "24-Mar-2008", "G"),
    (21, "SNELL, PARKER", "EDMONTON", "WHL", "21-Apr-2008", "G"),
    (22, "STEBETAK, ONDREJ", "PORTLAND", "WHL", "19-Jul-2007", "G"),
    (23, "JASWAL, ARVIN", "BARRIE", "OHL", "29-Mar-2008", "G"),
    (24, "COROVIC, MAKSIM", "COLLINGWOOD", "OJHL", "20-May-2008", "G"),
    (25, "CARRITHERS, LUKE", "USA U-18", "NTDP - USHL", "11-Jan-2008", "G"),
    (26, "BETTS, GAVIN", "KINGSTON", "OHL", "03-Apr-2008", "G"),
    (27, "COURCHESNE, RAFAEL", "SAINT JOHN", "QMJHL", "21-Aug-2008", "G"),
    (28, "LENNON, ELLIOT", "DEERFIELD", "HIGH-MA", "05-Mar-2008", "G"),
    (29, "SCHAUBEL, JASON", "KITCHENER", "OHL", "30-Aug-2008", "G"),
    (30, "RAYMOND, ALEXANDRE", "ROUYN-NORANDA", "QMJHL", "13-Nov-2007", "G"),
    (31, "CATANZARITI, ANTHONY", "VICTORIAVILLE", "QMJHL", "23-Jan-2008", "G"),
    (32, "NEWLOVE, MICHAEL", "WINDSOR", "OHL", "14-Jan-2007", "G"),
    (33, "KEANE, WILL", "MUSKEGON", "USHL", "26-Sep-2007", "G"),
    (34, "HUMPHRIES, MATTHEW", "OSHAWA", "OHL", "28-Jul-2008", "G"),
    (35, "NELSON, JAEDEN", "OTTAWA", "OHL", "11-Apr-2007", "G"),
    (36, "JOHNSON, NEILAN", "HOTCHKISS SCHOOL", "HIGH-CT", "01-Aug-2008", "G"),
    (37, "WEINER, JACOBY", "MONCTON", "QMJHL", "19-Jun-2008", "G"),
]

# International Skaters (128 players)
intl_skaters = [
    (1, "STENBERG, IVAR", "FROLUNDA", "SWEDEN", "30-Sep-2007", "LW"),
    (2, "SMITS, ALBERTS", "JUKURIT", "FINLAND", "02-Dec-2007", "D"),
    (3, "SUVANTO, OLIVER", "TAPPARA", "FINLAND", "03-Sep-2008", "C"),
    (4, "HERMANSSON, ELTON", "MODO", "SWEDEN-2", "05-Feb-2008", "RW"),
    (5, "BJORCK, VIGGO", "DJURGARDEN", "SWEDEN", "12-Mar-2008", "C"),
    (6, "PIIPARINEN, JUHO", "TAPPARA", "FINLAND", "10-Aug-2008", "D"),
    (7, "NORDMARK, MARCUS", "DJURGARDEN JR.", "SWEDEN-JR.", "04-May-2008", "LW"),
    (8, "GUSTAFSSON, MALTE", "HV71", "SWEDEN", "11-Jun-2008", "D"),
    (9, "HAKANSSON, WILLIAM", "LULEA", "SWEDEN", "08-Oct-2007", "D"),
    (10, "IGNATAVICIUS, SIMAS", "GENEVE", "SWISS", "22-Oct-2007", "RW"),
    (11, "SHCHERBAKOV, NIKITA", "UFA JR.", "RUSSIA-JR.", "23-Oct-2007", "D"),
    (12, "COMMAND, ALEXANDER", "OREBRO JR.", "SWEDEN-JR.", "16-Jun-2008", "C"),
    (13, "GOLJER, ADAM", "TRENCIN", "SLOVAKIA", "07-Jun-2008", "D"),
    (14, "VANHATALO, VILHO", "TAPPARA JR.", "FINLAND-JR.", "18-Jan-2008", "RW"),
    (15, "PUGACHYOV, GLEB", "NIZHNY NOVGOROD JR.", "RUSSIA-JR.", "25-Mar-2008", "RW"),
    (16, "CHRENKO, TOMAS", "NITRA", "SLOVAKIA", "02-Nov-2007", "C"),
    (17, "KATOLICKY, SIMON", "TAPPARA JR.", "FINLAND-JR.", "24-Jul-2008", "LW"),
    (18, "AARAM-OLSEN, NIKLAS", "OREBRO JR.", "SWEDEN-JR.", "19-Apr-2008", "LW"),
    (19, "ALALAURI, SAMU", "PELICANS JR.", "FINLAND-JR.", "31-May-2008", "D"),
    (20, "HOLMERTZ, OSCAR", "LINKOPING JR.", "SWEDEN-JR.", "21-Mar-2008", "C"),
    (21, "GUDMUNDSSON, MANS", "FARJESTAD JR.", "SWEDEN-JR.", "09-Jun-2008", "D"),
    (22, "NOVAK, FILIP", "SPARTA JR.", "CZECHIA-JR.", "07-Mar-2008", "LW"),
    (23, "FEDOROV, VIKTOR", "TORPEDO-GORKY NN", "RUSSIA-2", "21-Feb-2008", "C"),
    (24, "ELOFSSON, AXEL", "OREBRO JR.", "SWEDEN-JR.", "03-Jun-2008", "D"),
    (25, "MATVEYEV, VSEVOLOD", "SPARTAK JR.", "RUSSIA-JR.", "28-Dec-2007", "D"),
    (26, "ARKKO, LUKA", "PELICANS JR.", "FINLAND-JR.", "14-Jan-2008", "LW"),
    (27, "ERIKSSON, SAMUEL", "FARJESTAD JR.", "SWEDEN-JR.", "20-Mar-2008", "D"),
    (28, "SHAIKHLISLAMOV, ALAN", "UFA JR.", "RUSSIA-JR.", "04-Sep-2008", "RW"),
    (29, "NEMEC, ADAM", "NITRA", "SLOVAKIA", "18-Oct-2007", "LW"),
    (30, "ANDERSSON, ADAM", "LEKSAND JR.", "SWEDEN-JR.", "02-Jul-2008", "C"),
    (31, "LAGERBERG HOEN, JONAS", "LEKSAND JR.", "SWEDEN-JR.", "24-Oct-2007", "RW"),
    (32, "PAKARINEN, NOEL", "K-ESPOO JR.", "FINLAND-JR.", "09-Jul-2008", "LW"),
    (33, "GASHILOV, LAVR", "YEKATERINBURG JR.", "RUSSIA-JR.", "23-Sep-2007", "C"),
    (34, "ISAKSSON, MAX", "VAXJO JR.", "SWEDEN-JR.", "28-Jan-2008", "C"),
    (35, "BERNAT, LUCIAN", "TAPPARA JR.", "FINLAND-JR.", "08-Jun-2008", "RW"),
    (36, "FEDOSEYEV, YAROSLAV", "CHELYABINSK JR.", "RUSSIA-JR.", "05-Nov-2007", "D"),
    (37, "SAPOZHNIKOV, ALEXANDER", "STUPINO JR.", "RUSSIA-JR.", "17-Jan-2007", "D"),
    (38, "SZONGOTH, DOMAN", "KOOKOO JR.", "FINLAND-JR.", "08-Jun-2008", "C"),
    (39, "ANDERSSON, LUDVIG", "OREBRO JR.", "SWEDEN-JR.", "24-May-2008", "RW"),
    (40, "FROLO, JAKUB", "ILVES JR.", "FINLAND-JR.", "05-Dec-2007", "C"),
    (41, "BARTHOLDSSON, NILS", "ROGLE JR.", "SWEDEN-JR.", "25-Apr-2008", "RW"),
    (42, "MATYEV, YAROSLAV", "KHABAROVSK JR.", "RUSSIA-JR.", "11-Dec-2007", "D"),
    (43, "LUNDQVIST, WILLIAM", "LEKSAND JR.", "SWEDEN-JR.", "08-Nov-2007", "D"),
    (44, "TUKIO, OSSI", "ILVES JR.", "FINLAND-JR.", "03-Nov-2007", "D"),
    (45, "KURKA, PAVEL", "KARLOVY VARY JR.", "CZECHIA-JR.", "14-Jun-2008", "D"),
    (46, "PALME, OLA", "VAXJO JR.", "SWEDEN-JR.", "09-Feb-2008", "D"),
    (47, "DOLGOPOLOV, ILYA", "DYNAMO ST. PETERSBURG JR.", "RUSSIA-JR.", "18-Oct-2007", "D"),
    (48, "LAITINEN, JIKO", "ILVES JR.", "FINLAND-JR.", "16-Apr-2008", "C"),
    (49, "SEDLACEK, DAVID", "KARLOVY VARY JR.", "CZECHIA-JR.", "06-Jan-2008", "LW"),
    (50, "IVANOV, ALEXANDER", "BARS KAZAN", "RUSSIA-2", "10-Jun-2008", "D"),
    (51, "KNIGHTS, THEODOR", "MODO JR.", "SWEDEN-JR.", "16-Apr-2008", "D"),
    (52, "KOTKOV, MATVEI", "YAROSLAVL JR.", "RUSSIA-JR.", "27-Aug-2008", "RW"),
    (53, "MOROZOV, ALEXANDER", "TOGLIATTI JR.", "RUSSIA-JR.", "14-Jul-2008", "D"),
    (54, "FLORIS, JAKUB", "LUKKO JR.", "FINLAND-JR.", "19-Feb-2008", "D"),
    (55, "MATYUK, ARTYOM", "NIZHNY NOVGOROD JR.", "RUSSIA-JR.", "02-Nov-2007", "C"),
    (56, "JOSBRANT, MANS", "LULEA JR.", "SWEDEN-JR.", "23-Apr-2008", "LW"),
    (57, "LAATIKAINEN, MAX", "K-ESPOO JR.", "FINLAND-JR.", "14-Sep-2008", "D"),
    (58, "TSYPLAKOV, GLEB", "KHANTY-MANSIYSK JR.", "RUSSIA-JR.", "14-Jul-2008", "LW"),
    (59, "LARSSON, MELWIN", "BRYNAS JR.", "SWEDEN-JR.", "16-Nov-2007", "LW"),
    (60, "BRABENEC, JAN", "BRNO JR.", "CZECHIA-JR.", "02-Oct-2007", "C"),
    (61, "RYABYKIN, ELISEI", "DYNAMO MOSCOW JR.", "RUSSIA-JR.", "08-Jul-2008", "D"),
    (62, "BRONGEL-LARSSON, AXEL", "FROLUNDA JR.", "SWEDEN-JR.", "01-Nov-2007", "D"),
    (63, "KALIMULLIN, ADEL", "IRBIS KAZAN", "RUSSIA-JR.", "12-Apr-2008", "RW"),
    (64, "KARSAY, SAMUEL", "TRENCIN JR.", "SLOVAKIA-JR.", "12-Mar-2008", "RW"),
    (65, "GASTRIN, MALCOM", "MODO JR.", "SWEDEN-JR.", "19-Aug-2008", "LW"),
    (66, "CARELL, FELIX", "MALMO", "SWEDEN", "09-May-2006", "D"),
    (67, "JAKUBEC, MICHAL", "TRENCIN JR.", "SLOVAKIA-JR.", "14-Jul-2008", "C"),
    (68, "SJOSTROM, OLIWER", "BJORKLOVEN", "SWEDEN-2", "08-Apr-2007", "D"),
    (69, "GALVAS, TOMAS", "LIBEREC", "CZECHIA", "11-Feb-2006", "D"),
    (70, "BOUVARD, FABRICE", "GCK ZURICH JR.", "SWISS-JR.", "06-Jun-2008", "C"),
    (71, "PUFR, ANTONIN", "LIBEREC JR.", "CZECHIA-JR.", "25-Jul-2008", "D"),
    (72, "TARVAINEN, JOEL", "KALPA JR.", "FINLAND-JR.", "06-Apr-2008", "D"),
    (73, "NICOLAYSEN, HENRY", "SODERTALJE JR.", "SWEDEN-JR.", "16-Feb-2008", "D"),
    (74, "TUUVA, LEO", "LUKKO", "FINLAND", "02-Aug-2006", "RW"),
    (75, "CERMAK, TOMAS", "MLADA BOLESLAV JR.", "CZECHIA-JR.", "29-Jun-2008", "D"),
    (76, "USTINKOV, DANIIL", "GCK ZURICH", "SWISS-2", "26-Aug-2006", "D"),
    (77, "VAROSYAN, RAFIK", "VLADIVOSTOK JR.", "RUSSIA-JR.", "01-Oct-2007", "LW"),
    (78, "DENISOV, PAVEL", "OMSK JR.", "RUSSIA-JR.", "31-Aug-2008", "D"),
    (79, "HEDQVIST, ISAC", "LULEA", "SWEDEN", "22-Mar-2005", "C"),
    (80, "DANIELSSON, LIAM", "OREBRO", "SWEDEN", "05-Aug-2006", "RW"),
    (81, "SIMONOV, SEMYON", "BARYS ASTANA", "RUSSIA", "17-Jun-2005", "RW"),
    (82, "SOMERVUORI, JERE", "HIFK", "FINLAND", "10-Aug-2007", "LW"),
    (83, "BUZAEV, KIRILL", "IRBIS KAZAN", "RUSSIA-JR.", "08-Sep-2008", "LW"),
    (84, "SVENSK, VERTTI", "SAIPA JR.", "FINLAND-JR.", "09-Nov-2007", "D"),
    (85, "BYKOV, ANDREI", "SPARTAK JR.", "RUSSIA-JR.", "25-Dec-2007", "C"),
    (86, "URONEN, ANTTONI", "HIFK", "FINLAND", "24-Jun-2008", "C"),
    (87, "TUZIN, TSIMAFEI", "LULEA JR.", "SWEDEN-JR.", "11-Oct-2007", "LW"),
    (88, "WAHLROOS, OLLI", "TPS JR.", "FINLAND-JR.", "15-Feb-2008", "LW"),
    (89, "ZMRHAL, DAVID", "JIHLAVA JR.", "CZECHIA-JR.", "18-May-2008", "D"),
    (90, "GROMAKOV, NIKITA", "DYNAMO ST. PETERSBURG JR.", "RUSSIA-JR.", "06-Jan-2008", "RW"),
    (91, "JUNTUNEN, OIVA", "KOOKOO JR.", "FINLAND-JR.", "07-Aug-2008", "LW"),
    (92, "SODERBERG, LUDVIG", "SODERTALJE JR.", "SWEDEN-JR.", "27-Nov-2007", "D"),
    (93, "JUUSTOVAARA, CASPER", "LULEA", "SWEDEN", "25-Oct-2007", "C"),
    (94, "KUBIESA, MATEJ", "TRINEC", "CZECHIA", "11-Sep-2006", "RW"),
    (95, "CILTHE, HJALMAR", "FROLUNDA JR.", "SWEDEN-JR.", "10-Mar-2008", "D"),
    (96, "KHABAROV, MIKHAIL", "KHANTY-MANSIYSK JR.", "RUSSIA-JR.", "28-Dec-2007", "D"),
    (97, "HOLEJSOVSKY, JOSEF", "SLAVIA JR.", "CZECHIA-JR.", "24-May-2008", "RW"),
    (98, "KALLIO, WILMER", "TPS JR.", "FINLAND-JR.", "14-Jan-2008", "RW"),
    (99, "BRATT, ZIGGE", "FROLUNDA JR.", "SWEDEN-JR.", "13-May-2008", "D"),
    (100, "PATRIKHAYEV, IVAN", "CSKA", "RUSSIA", "03-Feb-2006", "D"),
    (101, "URONEN, EELIS", "HIFK JR.", "FINLAND-JR.", "24-Jun-2008", "LW"),
    (102, "ANDERBERG, MORGAN", "VAXJO", "SWEDEN", "27-Oct-2007", "C"),
    (103, "VAANANEN, VILMERI", "JOKERIT JR.", "FINLAND-JR.", "13-Aug-2008", "D"),
    (104, "LAMAN, ROMAN", "OMSK JR.", "RUSSIA-JR.", "30-Jan-2008", "C"),
    (105, "MATTA, IVAN", "MICHALOVCE", "SLOVAKIA", "11-Jan-2008", "C"),
    (106, "NOMME, ADAM", "FROLUNDA JR.", "SWEDEN-JR.", "21-Jan-2008", "RW"),
    (107, "SYSOYEV, DANIL", "MAGNITOGORSK JR.", "RUSSIA-JR.", "09-Dec-2007", "C"),
    (108, "RASANEN, VEETI", "JOKERIT JR.", "FINLAND-JR.", "26-Aug-2006", "LW"),
    (109, "KUBIN, VOJTECH", "BRNO JR.", "CZECHIA-JR.", "11-Jan-2008", "C"),
    (110, "ROING, RASMUS", "FARJESTAD JR.", "SWEDEN-JR.", "17-Feb-2008", "C"),
    (111, "SVANCAR, VOJTECH", "SLAVIA JR.", "CZECHIA-JR.", "12-May-2008", "LW"),
    (112, "PARSSINEN, JESSE", "TPS", "FINLAND", "15-Oct-2007", "C"),
    (113, "VATJUS, MIKO", "LUKKO JR.", "FINLAND-JR.", "02-Jul-2008", "C"),
    (114, "PAUL, DOUGLAS", "LINKOPING JR.", "SWEDEN-JR.", "11-Jul-2008", "C"),
    (115, "MELNIKOV, YAN", "NIZHNY NOVGOROD JR.", "RUSSIA-JR.", "16-Sep-2007", "RW"),
    (116, "CERNAK, RODERIK", "BRATISLAVA JR.", "SLOVAKIA-JR.", "19-Mar-2008", "D"),
    (117, "SUTTER, KIMI", "GCK ZURICH JR.", "SWISS-JR.", "10-Apr-2008", "RW"),
    (118, "KIM, MIKAEL", "ROGLE JR.", "SWEDEN-JR.", "08-Aug-2008", "C"),
    (119, "KOSSILA, TINO", "JOKERIT JR.", "FINLAND-JR.", "13-Feb-2008", "RW"),
    (120, "ANTONOV, YAROSLAV", "IRBIS KAZAN", "RUSSIA-JR.", "30-Dec-2007", "RW"),
    (121, "ONDREJCAK, MICHAL", "SLOVAKIA U18 (SVK-2)", "SLOVAKIA-2", "26-May-2008", "LW"),
    (122, "ILYIN, ARSENI", "SPARTAK JR.", "RUSSIA-JR.", "24-Dec-2007", "LW"),
    (123, "SIDOROV, PAVEL", "CSKA JR.", "RUSSIA-JR.", "04-Apr-2008", "RW"),
    (124, "SZAROWSKI, ONDREJ", "VITKOVICE JR.", "CZECHIA-JR.", "02-Jan-2008", "D"),
    (125, "OBUSEK, ADAM", "TRENCIN JR.", "SLOVAKIA-JR.", "06-Feb-2008", "C"),
    (126, "KOVALENKO, ALEKSANDR", "CHELYABINSK JR.", "RUSSIA-JR.", "12-Oct-2007", "D"),
    (127, "CERNY, VOJTECH", "SPARTA JR.", "CZECHIA-JR.", "31-Jan-2008", "D"),
    (128, "FOGELNEST, MARK", "UFA JR.", "RUSSIA-JR.", "03-Jul-2008", "LW"),
]

# International Goalies (20 players)
intl_goalies = [
    (1, "BORICHEV, DMITRI", "LOKO-76 YAROSLAVL", "RUSSIA-JR.", "19-Jun-2008", "G"),
    (2, "RYBKIN, YEGOR", "NIZHNY NOVGOROD JR.", "RUSSIA-JR.", "03-Dec-2007", "G"),
    (3, "LINDBERG NILSSON, DOUGLAS", "FARJESTAD JR.", "SWEDEN-JR.", "28-Mar-2008", "G"),
    (4, "TAMM, VIGGO", "LEKSAND JR.", "SWEDEN-JR.", "04-Jun-2008", "G"),
    (5, "POLETIN, FRANTISEK", "PELICANS JR.", "FINLAND-JR.", "13-Sep-2008", "G"),
    (6, "KARBAINOV, MATVEY", "SKA-ACADEMY ST. PETERSBURG", "RUSSIA-JR.", "06-Nov-2007", "G"),
    (7, "VERMIROVSKY, DAVID", "PARDUBICE JR.", "CZECHIA-JR.", "25-Jul-2008", "G"),
    (8, "IVCHENKO, DMITRI", "OMSK JR.", "RUSSIA-JR.", "29-Jun-2008", "G"),
    (9, "CHARVAT, SEBASTIAN", "LIBEREC JR.", "CZECHIA-JR.", "31-Jan-2008", "G"),
    (10, "HRENAK, SAMUEL", "TRENCIN JR.", "SLOVAKIA-JR.", "19-Mar-2008", "G"),
    (11, "GAMMALS, WILLIAM", "TAPPARA JR.", "FINLAND-JR.", "12-Feb-2008", "G"),
    (12, "SELIVANOV, VLADIMIR", "DYNAMO MOSCOW JR.", "RUSSIA-JR.", "25-Jul-2008", "G"),
    (13, "TJARNLUND, MILO", "ROGLE JR.", "SWEDEN-JR.", "17-Mar-2008", "G"),
    (14, "POVAROV, MIKHAIL", "UFA JR.", "RUSSIA-JR.", "10-Jan-2008", "G"),
    (15, "KERKOLA, PATRIK", "KALPA", "FINLAND", "29-Mar-2007", "G"),
    (16, "PLUMINS, PATRIKS", "ZEMGALE", "LATVIA", "07-Jan-2008", "G"),
    (17, "PSOHLAVEC, MARTIN", "KARLOVY VARY JR.", "CZECHIA-JR.", "06-May-2008", "G"),
    (18, "RIIHIMAKI, AARNI", "JYP JR.", "FINLAND-JR.", "28-Jun-2008", "G"),
    (19, "AINASTO, JUUSO", "JOKERIT JR.", "FINLAND-JR.", "17-Mar-2008", "G"),
    (20, "STENGARD, GUSTAV", "VASTERAS JR.", "SWEDEN-JR.", "03-Aug-2008", "G"),
]


def create_f28_dataframe():
    """Create DataFrame with all F28 data."""
    all_data = []

    for list_name, players in [
        ("NA_SKATERS", na_skaters),
        ("NA_GOALIES", na_goalies),
        ("INTL_SKATERS", intl_skaters),
        ("INTL_GOALIES", intl_goalies)
    ]:
        total = len(players)
        for rank, name, team, league, birthdate, pos in players:
            points = calculate_points(rank, total)
            all_data.append({
                'nhl_scouting_rank': rank,
                'list_type': list_name,
                'player_name': name,
                'team': team,
                'league': league,
                'birthdate': birthdate,
                'position': pos,
                'factor_28_nhl_scouting_points': points,
                'total_in_list': total
            })

    return pd.DataFrame(all_data)


def match_players_fuzzy(df):
    """Match players to BigQuery using fuzzy matching."""
    client = bigquery.Client(project=PROJECT_ID)

    # Get all players from player_stats
    query = """
    SELECT
        id as player_id,
        name as bq_name,
        yearOfBirth as birth_year,
        position as bq_position
    FROM `prodigy-ranking.algorithm_core.player_stats`
    """

    print("Fetching player_stats from BigQuery...")
    bq_players = client.query(query).to_dataframe()
    bq_players['normalized_name'] = bq_players['bq_name'].apply(normalize_name)

    # Extract birth year from birthdate
    df['birth_year'] = df['birthdate'].apply(get_birth_year_from_date)

    matched = []
    unmatched = []

    print(f"\nMatching {len(df)} players with fuzzy matching...")

    for idx, row in df.iterrows():
        name_variants = normalize_name_for_search(row['player_name'])
        birth_year = row['birth_year']

        # Strategy 1: Exact match with birth year
        for variant in name_variants:
            exact_matches = bq_players[
                (bq_players['normalized_name'] == variant) &
                (bq_players['birth_year'] == birth_year)
            ]
            if len(exact_matches) >= 1:
                matched.append({
                    **row.to_dict(),
                    'player_id': int(exact_matches.iloc[0]['player_id']),
                    'match_type': 'exact'
                })
                break
        else:
            # Strategy 2: Fuzzy match with birth year
            player_id, match_type, score = fuzzy_match_player(
                name_variants, birth_year, bq_players, threshold=80
            )
            if player_id:
                matched.append({
                    **row.to_dict(),
                    'player_id': player_id,
                    'match_type': match_type
                })
            else:
                # Strategy 3: Fuzzy match without birth year (lower threshold)
                player_id, match_type, score = fuzzy_match_player(
                    name_variants, None, bq_players, threshold=90
                )
                if player_id:
                    matched.append({
                        **row.to_dict(),
                        'player_id': player_id,
                        'match_type': f"no_year_{match_type}"
                    })
                else:
                    unmatched.append(row.to_dict())

        if (idx + 1) % 50 == 0:
            print(f"  Processed {idx + 1}/{len(df)} players...")

    matched_df = pd.DataFrame(matched)
    unmatched_df = pd.DataFrame(unmatched)

    print(f"\nMatching Summary:")
    print(f"  Total players: {len(df)}")
    print(f"  Matched: {len(matched_df)} ({100*len(matched_df)/len(df):.1f}%)")
    print(f"  Unmatched: {len(unmatched_df)} ({100*len(unmatched_df)/len(df):.1f}%)")

    if len(matched_df) > 0:
        print(f"\n  Match types:")
        for mt, count in matched_df['match_type'].value_counts().items():
            print(f"    {mt}: {count}")

    return matched_df, unmatched_df


def upload_to_bigquery(df, table_name):
    """Upload DataFrame to BigQuery."""
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET}.{table_name}"

    upload_df = df[[
        'player_id',
        'nhl_scouting_rank',
        'list_type',
        'player_name',
        'team',
        'league',
        'birth_year',
        'position',
        'factor_28_nhl_scouting_points'
    ]].copy()

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_dataframe(upload_df, table_id, job_config=job_config)
    job.result()

    print(f"\nUploaded {len(upload_df)} rows to {table_id}")


def main():
    print("=" * 60)
    print("Factor 28: NHL Scouting Report - V2 with Fuzzy Matching")
    print("=" * 60)

    # Create DataFrame
    print("\n1. Creating DataFrame from NHL Central Scouting data...")
    df = create_f28_dataframe()
    print(f"   Total players: {len(df)}")

    # Match with fuzzy matching
    print("\n2. Matching players with fuzzy matching...")
    matched_df, unmatched_df = match_players_fuzzy(df)

    # Save results
    matched_df.to_csv("F28_nhl_scouting_matched_v2.csv", index=False)
    print(f"\n3. Saved matched players to F28_nhl_scouting_matched_v2.csv")

    if len(unmatched_df) > 0:
        unmatched_df.to_csv("F28_nhl_scouting_unmatched_v2.csv", index=False)
        print(f"   Saved unmatched players to F28_nhl_scouting_unmatched_v2.csv")

    # Upload to BigQuery
    if len(matched_df) > 0:
        print("\n4. Uploading to BigQuery...")
        upload_to_bigquery(matched_df, "PT_F28_NHLSR")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    main()

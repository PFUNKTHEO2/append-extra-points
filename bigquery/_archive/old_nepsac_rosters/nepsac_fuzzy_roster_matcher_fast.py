"""
NEPSAC Fuzzy Roster Matcher (Optimized)
=======================================
Matches all roster players to ProdigyRanking database using fuzzy matching.
Optimized for speed with better indexing and reduced comparisons.
"""

import os
import csv
import re
from datetime import datetime
from difflib import SequenceMatcher
from google.cloud import bigquery

PROJECT_ID = "prodigy-ranking"
DATASET = "algorithm_core"

# Nickname mappings
NICKNAMES = {
    'william': ['will', 'bill', 'billy', 'willy', 'liam'],
    'robert': ['rob', 'bob', 'bobby', 'robbie'],
    'richard': ['rick', 'dick', 'rich', 'richie'],
    'michael': ['mike', 'mikey', 'mick'],
    'james': ['jim', 'jimmy', 'jamie'],
    'john': ['jack', 'johnny', 'jon'],
    'thomas': ['tom', 'tommy'],
    'christopher': ['chris', 'kit'],
    'matthew': ['matt', 'matty'],
    'nicholas': ['nick', 'nicky'],
    'alexander': ['alex', 'xander'],
    'benjamin': ['ben', 'benny'],
    'samuel': ['sam', 'sammy'],
    'daniel': ['dan', 'danny'],
    'joseph': ['joe', 'joey'],
    'anthony': ['tony', 'ant'],
    'andrew': ['andy', 'drew'],
    'joshua': ['josh'],
    'david': ['dave', 'davey'],
    'edward': ['ed', 'eddie', 'ted', 'teddy'],
    'charles': ['charlie', 'chuck'],
    'timothy': ['tim', 'timmy'],
    'patrick': ['pat', 'paddy'],
    'nathaniel': ['nate', 'nathan'],
    'nathan': ['nate'],
    'jonathan': ['jon', 'jonny'],
    'zachary': ['zach', 'zack'],
    'cameron': ['cam'],
    'jacob': ['jake'],
    'maxwell': ['max'],
    'ryan': ['ry'],
    'tyler': ['ty'],
    'connor': ['con'],
    'lucas': ['luke'],
    'aidan': ['aiden'],
    'aiden': ['aidan'],
    'cole': ['coley'],
    'luca': ['luke'],
    'sebastian': ['seb'],
}

# Build reverse nickname map
NICKNAME_TO_FULL = {}
for full, nicks in NICKNAMES.items():
    for nick in nicks:
        if nick not in NICKNAME_TO_FULL:
            NICKNAME_TO_FULL[nick] = []
        NICKNAME_TO_FULL[nick].append(full)


def log(message, level="INFO"):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f"[{timestamp}] {level}: {message}")


def normalize_name(name):
    """Normalize a name for matching."""
    if not name:
        return ""
    name = name.lower().strip()
    name = re.sub(r'[^\w\s]', '', name)
    name = re.sub(r'\s+', ' ', name)
    return name


def get_first_name_variants(first_name):
    """Get all variants of a first name."""
    variants = {first_name}

    # Check if it's a nickname
    if first_name in NICKNAME_TO_FULL:
        for full in NICKNAME_TO_FULL[first_name]:
            variants.add(full)

    # Check if it has nicknames
    if first_name in NICKNAMES:
        for nick in NICKNAMES[first_name]:
            variants.add(nick)

    return variants


def similarity(a, b):
    """Calculate string similarity using SequenceMatcher."""
    return SequenceMatcher(None, a, b).ratio()


def extract_birth_year_from_dob(dob_str):
    """Extract birth year from DOB string."""
    if not dob_str:
        return None
    patterns = [
        r'(\d{4})$',
        r'^(\d{4})',
        r'/(\d{4})',
        r'-(\d{4})',
        r'/(\d{2})$',
    ]
    for pattern in patterns:
        match = re.search(pattern, dob_str)
        if match:
            year = int(match.group(1))
            if year < 100:
                year += 2000
            if 1990 <= year <= 2015:
                return year
    return None


def extract_birth_year_from_grad(grad_str):
    """Extract approximate birth year from graduation year."""
    if not grad_str:
        return None
    try:
        grad = int(grad_str)
        if 2020 <= grad <= 2035:
            return grad - 18
    except:
        pass
    return None


def load_database_players():
    """Load all players from database with their points."""
    log("Loading players from database...")
    client = bigquery.Client(project=PROJECT_ID)

    query = """
    SELECT
        pc.player_id,
        pc.player_name,
        pc.total_points,
        ps.yearOfBirth,
        ps.latestStats_team_name
    FROM `prodigy-ranking.algorithm_core.player_cumulative_points` pc
    LEFT JOIN `prodigy-ranking.algorithm_core.player_stats` ps ON pc.player_id = ps.id
    WHERE pc.total_points > 0
    """

    results = client.query(query).result()

    players = []
    for row in results:
        name = row.player_name or ''
        normalized = normalize_name(name)
        players.append({
            'player_id': row.player_id,
            'name': name,
            'name_normalized': normalized,
            'total_points': row.total_points or 0,
            'birth_year': row.yearOfBirth,
            'team': row.latestStats_team_name or ''
        })

    log(f"Loaded {len(players)} players from database")
    return players


def build_index(db_players):
    """Build index by last name for faster matching."""
    index = {}
    for p in db_players:
        name = p['name_normalized']
        if not name:
            continue
        parts = name.split()
        if parts:
            last = parts[-1]
            # Index by full last name AND first 3 chars
            if last not in index:
                index[last] = []
            index[last].append(p)

            key3 = last[:3] if len(last) >= 3 else last
            if key3 != last:
                if key3 not in index:
                    index[key3] = []
                index[key3].append(p)

    log(f"Built index with {len(index)} keys")
    return index


def find_best_match(roster_name, roster_birth_year, roster_team, index):
    """Find best matching database player."""
    if not roster_name:
        return None, 0

    parts = roster_name.split()
    if not parts:
        return None, 0

    first_name = parts[0]
    last_name = parts[-1]

    # Get first name variants
    first_variants = get_first_name_variants(first_name)

    # Build candidate set from index
    candidates = set()

    # Try full last name
    if last_name in index:
        for p in index[last_name]:
            candidates.add(p['player_id'])

    # Try first 3 chars of last name
    key3 = last_name[:3] if len(last_name) >= 3 else last_name
    if key3 in index:
        for p in index[key3]:
            candidates.add(p['player_id'])

    if not candidates:
        return None, 0

    # Get actual player objects
    candidate_players = [p for p in index.get(last_name, []) + index.get(key3, [])
                         if p['player_id'] in candidates]

    # Dedupe
    seen = set()
    unique_candidates = []
    for p in candidate_players:
        if p['player_id'] not in seen:
            seen.add(p['player_id'])
            unique_candidates.append(p)

    best_match = None
    best_score = 0

    for db_player in unique_candidates:
        db_name = db_player['name_normalized']
        if not db_name:
            continue

        db_parts = db_name.split()
        if not db_parts:
            continue

        db_first = db_parts[0]
        db_last = db_parts[-1]

        # Last name similarity
        last_sim = similarity(last_name, db_last)
        if last_sim < 0.7:
            continue

        # First name similarity (check variants)
        first_sim = 0
        for variant in first_variants:
            sim = similarity(variant, db_first)
            first_sim = max(first_sim, sim)

        if first_sim < 0.5:
            continue

        # Combined name score
        name_sim = (first_sim * 0.4 + last_sim * 0.6)

        # Base score
        score = name_sim * 0.7

        # Birth year bonus
        if roster_birth_year and db_player.get('birth_year'):
            year_diff = abs(roster_birth_year - db_player['birth_year'])
            if year_diff == 0:
                score += 0.2
            elif year_diff == 1:
                score += 0.1
            elif year_diff > 2:
                score -= 0.15

        # Team similarity bonus
        db_team = (db_player.get('team') or '').lower()
        if roster_team and db_team:
            team_sim = similarity(roster_team, db_team)
            if team_sim > 0.5:
                score += 0.1 * team_sim

        if score > best_score:
            best_score = score
            best_match = db_player

    return best_match, best_score


def main():
    print("=" * 70)
    print("NEPSAC FUZZY ROSTER MATCHER (OPTIMIZED)")
    print("=" * 70)

    # Load database players
    db_players = load_database_players()
    index = build_index(db_players)

    # Load combined rosters
    roster_file = os.path.join(os.path.dirname(__file__), "nepsac_all_rosters_combined.csv")
    log(f"Loading rosters from {roster_file}")

    roster_players = []
    with open(roster_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        roster_players = list(reader)

    log(f"Loaded {len(roster_players)} roster players")

    # Match each player
    log("Matching players...")
    matches = []
    team_stats = {}

    start_time = datetime.now()

    for i, rp in enumerate(roster_players):
        if (i + 1) % 100 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            rate = (i + 1) / elapsed if elapsed > 0 else 0
            remaining = (len(roster_players) - i - 1) / rate if rate > 0 else 0
            log(f"Progress: {i+1}/{len(roster_players)} ({rate:.1f}/sec, ~{remaining:.0f}s remaining)")

        roster_name = normalize_name(rp.get('name', ''))
        roster_birth_year = extract_birth_year_from_dob(rp.get('dob', ''))
        if not roster_birth_year:
            roster_birth_year = extract_birth_year_from_grad(rp.get('grad_year', ''))
        roster_team = rp.get('team', '').lower()

        match, score = find_best_match(roster_name, roster_birth_year, roster_team, index)

        team = rp.get('team', 'Unknown')
        if team not in team_stats:
            team_stats[team] = {'total': 0, 'matched': 0, 'points': []}
        team_stats[team]['total'] += 1

        if match and score >= 0.65:
            matches.append({
                'roster_name': rp.get('name', ''),
                'roster_team': team,
                'roster_position': rp.get('position', ''),
                'roster_grad_year': rp.get('grad_year', ''),
                'roster_dob': rp.get('dob', ''),
                'db_player_id': match['player_id'],
                'db_name': match['name'],
                'db_birth_year': match.get('birth_year'),
                'total_points': match['total_points'],
                'match_score': round(score, 3),
                'confidence': 'HIGH' if score >= 0.85 else 'MEDIUM' if score >= 0.75 else 'LOW'
            })
            team_stats[team]['matched'] += 1
            team_stats[team]['points'].append(match['total_points'])
        else:
            matches.append({
                'roster_name': rp.get('name', ''),
                'roster_team': team,
                'roster_position': rp.get('position', ''),
                'roster_grad_year': rp.get('grad_year', ''),
                'roster_dob': rp.get('dob', ''),
                'db_player_id': None,
                'db_name': None,
                'db_birth_year': None,
                'total_points': 0,
                'match_score': round(score, 3) if match else 0,
                'confidence': 'NO_MATCH'
            })

    # Save matches
    output_file = os.path.join(os.path.dirname(__file__), "nepsac_roster_matches.csv")
    log(f"Saving {len(matches)} matches to {output_file}")

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['roster_name', 'roster_team', 'roster_position', 'roster_grad_year',
                      'roster_dob', 'db_player_id', 'db_name', 'db_birth_year',
                      'total_points', 'match_score', 'confidence']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(matches)

    # Calculate team rankings
    team_rankings = []
    for team, stats in team_stats.items():
        avg_pts = sum(stats['points']) / len(stats['points']) if stats['points'] else 0
        team_rankings.append({
            'team': team,
            'roster_size': stats['total'],
            'matched': stats['matched'],
            'match_rate': stats['matched'] / stats['total'] * 100 if stats['total'] > 0 else 0,
            'avg_points': avg_pts,
            'total_points': sum(stats['points']),
            'max_points': max(stats['points']) if stats['points'] else 0,
        })

    team_rankings.sort(key=lambda x: x['avg_points'], reverse=True)

    # Save team rankings
    rankings_file = os.path.join(os.path.dirname(__file__), "nepsac_team_rankings_full.csv")
    with open(rankings_file, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['rank', 'team', 'roster_size', 'matched', 'match_rate',
                      'avg_points', 'total_points', 'max_points']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for i, t in enumerate(team_rankings, 1):
            writer.writerow({
                'rank': i,
                'team': t['team'],
                'roster_size': t['roster_size'],
                'matched': t['matched'],
                'match_rate': f"{t['match_rate']:.1f}%",
                'avg_points': round(t['avg_points'], 2),
                'total_points': round(t['total_points'], 2),
                'max_points': round(t['max_points'], 2)
            })

    # Print summary
    total_matched = sum(1 for m in matches if m['db_player_id'])
    high_conf = sum(1 for m in matches if m['confidence'] == 'HIGH')
    med_conf = sum(1 for m in matches if m['confidence'] == 'MEDIUM')
    low_conf = sum(1 for m in matches if m['confidence'] == 'LOW')

    elapsed = (datetime.now() - start_time).total_seconds()

    print("\n" + "=" * 70)
    print("MATCHING SUMMARY")
    print("=" * 70)
    print(f"Total roster players: {len(roster_players)}")
    print(f"Matched to database:  {total_matched} ({total_matched/len(roster_players)*100:.1f}%)")
    print(f"  - High confidence:  {high_conf}")
    print(f"  - Medium confidence: {med_conf}")
    print(f"  - Low confidence:   {low_conf}")
    print(f"Unmatched:            {len(roster_players) - total_matched}")
    print(f"Processing time:      {elapsed:.1f} seconds")

    print("\n" + "=" * 70)
    print("TOP 20 TEAMS BY AVERAGE PRODIGYPOINTS")
    print("=" * 70)
    print(f"{'Rank':<5} {'Team':<28} {'Roster':<8} {'Match%':<8} {'Avg Pts':<12} {'Best':<10}")
    print("-" * 70)
    for i, t in enumerate(team_rankings[:20], 1):
        print(f"{i:<5} {t['team']:<28} {t['roster_size']:<8} {t['match_rate']:.1f}%{'':<3} {t['avg_points']:<12.2f} {t['max_points']:<10.2f}")

    print("\n" + "=" * 70)
    print(f"Results saved to:")
    print(f"  - {output_file}")
    print(f"  - {rankings_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()

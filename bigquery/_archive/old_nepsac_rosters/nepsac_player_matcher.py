"""
NEPSAC Player Matcher
=====================
Matches NEPSAC players to ProdigyRanking database using fuzzy matching.
Uses name similarity + team validation to ensure accurate matches.
"""

import os
import csv
import json
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from google.cloud import bigquery
from difflib import SequenceMatcher

PROJECT_ID = "prodigy-ranking"

# Team name aliases for matching
TEAM_ALIASES = {
    "st. marks": ["st. mark's", "saint marks", "saint mark's", "st marks"],
    "st. georges": ["st. george's", "saint georges", "saint george's", "st georges"],
    "st. paul's": ["st. pauls", "saint paul's", "saint pauls", "st paul's school"],
    "noble & greenough": ["nobles", "noble and greenough", "noble greenough"],
    "bb&n": ["buckingham browne & nichols", "buckingham browne nichols"],
    "nmh": ["northfield mount hermon", "northfield-mount hermon"],
    "kua": ["kimball union", "kimball union academy"],
    "governor's": ["governors", "governor's academy"],
    "milton": ["milton academy"],
    "belmont hill": ["belmont hill school"],
    "rivers": ["rivers school"],
    "thayer": ["thayer academy"],
    "lawrence": ["lawrence academy"],
    "tabor": ["tabor academy"],
    "brooks": ["brooks school"],
    "middlesex": ["middlesex school"],
    "groton": ["groton school"],
}


def levenshtein_ratio(s1: str, s2: str) -> float:
    """Calculate similarity ratio between two strings (0-1)."""
    return SequenceMatcher(None, s1.lower(), s2.lower()).ratio()


def normalize_name(name: str) -> str:
    """Normalize a player name for matching."""
    if not name:
        return ""
    # Remove common suffixes/prefixes
    name = name.lower().strip()
    name = name.replace(".", "").replace("'", "").replace("-", " ")
    # Handle common nicknames
    replacements = {
        "william": "will", "billy": "will", "bill": "will",
        "robert": "rob", "bob": "rob", "bobby": "rob",
        "michael": "mike", "mikey": "mike",
        "james": "jim", "jimmy": "jim", "jamie": "james",
        "thomas": "tom", "tommy": "tom",
        "richard": "rich", "rick": "rich", "dick": "rich",
        "christopher": "chris",
        "nicholas": "nick", "nicky": "nick",
        "alexander": "alex",
        "benjamin": "ben",
        "matthew": "matt",
        "daniel": "dan", "danny": "dan",
        "joseph": "joe", "joey": "joe",
        "anthony": "tony",
        "edward": "ed", "eddie": "ed", "ted": "ed",
        "theodore": "theo", "teddy": "theo",
        "jonathan": "jon", "johnny": "jon",
        "patrick": "pat",
        "timothy": "tim",
        "samuel": "sam",
        "joshua": "josh",
        "zachary": "zach",
        "andrew": "drew", "andy": "drew",
        "cameron": "cam",
        "jacob": "jake",
        "maxwell": "max",
        "charles": "charlie",
    }
    parts = name.split()
    if parts and parts[0] in replacements:
        parts[0] = replacements[parts[0]]
    return " ".join(parts)


def normalize_team(team: str) -> str:
    """Normalize team name for matching."""
    team = team.lower().strip()
    # Check aliases
    for canonical, aliases in TEAM_ALIASES.items():
        if team in aliases or canonical in team:
            return canonical
        for alias in aliases:
            if alias in team or team in alias:
                return canonical
    return team


def teams_match(team1: str, team2: str) -> bool:
    """Check if two team names likely refer to the same team."""
    t1 = normalize_team(team1)
    t2 = normalize_team(team2)

    if t1 == t2:
        return True

    # Check if one contains the other
    if t1 in t2 or t2 in t1:
        return True

    # Check word overlap
    words1 = set(t1.split())
    words2 = set(t2.split())
    overlap = words1 & words2
    if len(overlap) >= 1 and any(len(w) > 3 for w in overlap):
        return True

    return False


def load_nepsac_players(filepath: str) -> List[Dict]:
    """Load players from NEPSAC CSV."""
    players = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player = {
                "nepsac_rank": int(row.get("rank", 0)),
                "first_name": row.get("first_name", "").strip(),
                "last_name": row.get("last_name", "").strip(),
                "player_name": f"{row.get('first_name', '')} {row.get('last_name', '')}".strip(),
                "team": row.get("team", "").strip(),
                "position": row.get("position", "").strip(),
                "games_played": int(row.get("gp", 0) or 0),
                "goals": int(row.get("goals", 0) or 0),
                "assists": int(row.get("assists", 0) or 0),
                "points": int(row.get("points", 0) or 0),
                "ppg": float(row.get("ppg", 0) or 0),
            }
            players.append(player)
    return players


def fetch_prodigy_players() -> List[Dict]:
    """Fetch potential matches from ProdigyRanking database."""
    client = bigquery.Client(project=PROJECT_ID)

    # Filter to US/Canada players in prep school age range
    # and preferably in prep/high school leagues
    query = """
    SELECT
        p.id as player_id,
        p.name as player_name,
        p.firstName,
        p.lastName,
        p.yearOfBirth as birth_year,
        p.position,
        p.nationality_name,
        pc.f01_views as ep_views,
        pc.total_points as prodigy_points,
        pc.current_team,
        pc.current_league
    FROM `prodigy-ranking.algorithm_core.player_stats` p
    LEFT JOIN `prodigy-ranking.algorithm_core.player_cumulative_points` pc
        ON p.id = pc.player_id
    WHERE p.yearOfBirth >= 2004 AND p.yearOfBirth <= 2011
      AND (p.nationality_name IN ('USA', 'Canada', 'United States')
           OR pc.current_league LIKE '%Prep%'
           OR pc.current_league LIKE '%High School%'
           OR pc.current_league LIKE '%USHS%'
           OR pc.current_league LIKE '%School%'
           OR pc.current_league LIKE '%Academy%')
    """

    results = client.query(query).result()
    return [dict(row) for row in results]


def build_player_index(players: List[Dict]) -> Dict[str, List[Dict]]:
    """Build an index by last name for faster lookups."""
    index = {}
    for p in players:
        lastname = (p.get('lastName') or '').lower()[:3]  # First 3 chars of lastname
        if lastname:
            if lastname not in index:
                index[lastname] = []
            index[lastname].append(p)
    return index


def find_best_match(nepsac_player: Dict, prodigy_index: Dict[str, List[Dict]],
                    all_players: List[Dict], matched_ids: set) -> Tuple[Optional[Dict], float, str]:
    """
    Find the best matching ProdigyRanking player for a NEPSAC player.

    Returns: (matched_player, confidence_score, match_reason)
    """
    nepsac_name = normalize_name(nepsac_player['player_name'])
    nepsac_first = normalize_name(nepsac_player['first_name'])
    nepsac_last = nepsac_player['last_name'].lower()
    nepsac_team = nepsac_player['team']

    candidates = []

    # Get candidates from index (by first 3 chars of last name)
    lastname_prefix = nepsac_last[:3] if len(nepsac_last) >= 3 else nepsac_last
    potential_matches = list(prodigy_index.get(lastname_prefix, []))

    for pr in potential_matches:
        # Skip already matched players
        if pr['player_id'] in matched_ids:
            continue

        pr_name = normalize_name(pr.get('player_name', ''))
        pr_first = normalize_name(pr.get('firstName', ''))
        pr_last = (pr.get('lastName') or '').lower()
        pr_team = pr.get('current_team') or ''

        # Calculate name similarity
        full_name_sim = levenshtein_ratio(nepsac_name, pr_name)
        last_name_sim = levenshtein_ratio(nepsac_last, pr_last)
        first_name_sim = levenshtein_ratio(nepsac_first, pr_first)

        # Check team match
        team_match = teams_match(nepsac_team, pr_team)

        # Scoring logic
        score = 0
        reason = []

        # Exact full name match
        if full_name_sim > 0.95:
            score += 50
            reason.append("exact_name")
        elif full_name_sim > 0.85:
            score += 40
            reason.append("close_name")
        elif full_name_sim > 0.75:
            score += 25
            reason.append("similar_name")

        # Last name match (important)
        if last_name_sim > 0.95:
            score += 25
            reason.append("exact_lastname")
        elif last_name_sim > 0.85:
            score += 15
            reason.append("close_lastname")

        # First name match
        if first_name_sim > 0.90:
            score += 15
            reason.append("exact_firstname")
        elif first_name_sim > 0.70:
            score += 8
            reason.append("similar_firstname")

        # Team validation bonus
        if team_match:
            score += 20
            reason.append("team_match")

        # Position match bonus
        nepsac_pos = nepsac_player.get('position', '').upper()
        pr_pos = (pr.get('position') or '').upper()
        if nepsac_pos and pr_pos:
            if nepsac_pos == pr_pos:
                score += 5
                reason.append("position_match")
            elif nepsac_pos in ['F', 'C', 'LW', 'RW'] and pr_pos in ['F', 'C', 'LW', 'RW']:
                score += 3  # Forward positions are interchangeable

        if score >= 40:  # Minimum threshold
            candidates.append({
                'player': pr,
                'score': score,
                'reason': '+'.join(reason),
                'name_sim': full_name_sim,
                'team_match': team_match
            })

    if not candidates:
        return None, 0, "no_match"

    # Sort by score, then by name similarity
    candidates.sort(key=lambda x: (x['score'], x['name_sim']), reverse=True)
    best = candidates[0]

    # Confidence calculation
    confidence = min(best['score'] / 100, 1.0)

    # If there are close competitors, reduce confidence
    if len(candidates) > 1 and candidates[1]['score'] > best['score'] * 0.85:
        confidence *= 0.8  # Multiple close matches reduces confidence

    return best['player'], confidence, best['reason']


def match_players(nepsac_players: List[Dict], prodigy_players: List[Dict]) -> List[Dict]:
    """Match all NEPSAC players to ProdigyRanking database."""

    matched_ids = set()
    results = []

    # Build index for faster lookups
    print("Building player index...")
    prodigy_index = build_player_index(prodigy_players)
    print(f"Index built with {len(prodigy_index)} prefixes")

    # Sort NEPSAC players by points (prioritize high-value matches)
    sorted_nepsac = sorted(nepsac_players, key=lambda x: x['points'], reverse=True)

    for i, nep in enumerate(sorted_nepsac):
        if i % 100 == 0:
            print(f"  Matching player {i+1}/{len(sorted_nepsac)}...")
        match, confidence, reason = find_best_match(nep, prodigy_index, prodigy_players, matched_ids)

        result = {**nep}  # Copy NEPSAC data

        if match and confidence >= 0.5:
            result['matched'] = True
            result['match_confidence'] = round(confidence, 2)
            result['match_reason'] = reason
            result['player_id'] = match['player_id']
            result['birth_year'] = match.get('birth_year')
            result['ep_views'] = match.get('ep_views', 0) or 0
            result['prodigy_points'] = match.get('prodigy_points', 0) or 0
            result['prodigy_team'] = match.get('current_team', '')
            result['prodigy_league'] = match.get('current_league', '')
            result['nationality'] = match.get('nationality_name', '')
            matched_ids.add(match['player_id'])
        else:
            result['matched'] = False
            result['match_confidence'] = confidence if match else 0
            result['match_reason'] = reason
            result['player_id'] = None
            result['birth_year'] = None
            result['ep_views'] = 0
            result['prodigy_points'] = 0

        results.append(result)

    return results


def generate_match_report(results: List[Dict]) -> str:
    """Generate a matching report."""
    report = []
    report.append("=" * 80)
    report.append("NEPSAC PLAYER MATCHING REPORT")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("=" * 80)
    report.append("")

    matched = [r for r in results if r['matched']]
    unmatched = [r for r in results if not r['matched']]

    high_conf = [r for r in matched if r['match_confidence'] >= 0.8]
    med_conf = [r for r in matched if 0.6 <= r['match_confidence'] < 0.8]
    low_conf = [r for r in matched if r['match_confidence'] < 0.6]

    report.append("MATCHING SUMMARY")
    report.append("-" * 50)
    report.append(f"Total NEPSAC Players:     {len(results)}")
    report.append(f"Matched to Database:      {len(matched)} ({len(matched)/len(results)*100:.1f}%)")
    report.append(f"  - High Confidence (>=80%): {len(high_conf)}")
    report.append(f"  - Medium Confidence:      {len(med_conf)}")
    report.append(f"  - Low Confidence:         {len(low_conf)}")
    report.append(f"Unmatched:                {len(unmatched)} ({len(unmatched)/len(results)*100:.1f}%)")
    report.append("")

    # Birth year distribution of matched players
    by_year = {}
    for r in matched:
        by = r.get('birth_year')
        if by:
            by_year[by] = by_year.get(by, 0) + 1

    if by_year:
        report.append("BIRTH YEAR DISTRIBUTION (Matched Players)")
        report.append("-" * 50)
        for year in sorted(by_year.keys(), reverse=True):
            count = by_year[year]
            bar = "#" * (count // 5)
            report.append(f"  {year}: {count:3} players {bar}")
        report.append("")

    # Top matched players by points
    report.append("TOP 30 MATCHED PLAYERS (by NEPSAC points)")
    report.append("-" * 80)
    top_matched = sorted(matched, key=lambda x: x['points'], reverse=True)[:30]

    for r in top_matched:
        conf_str = f"{r['match_confidence']*100:.0f}%"
        by_str = str(r.get('birth_year', '????'))
        report.append(
            f"  {r['player_name']:<25} {r['team']:<18} "
            f"BY:{by_str} | {r['points']:2}pts | Conf:{conf_str:<4} | {r['match_reason']}"
        )
    report.append("")

    # Unmatched players (top 30 by points)
    if unmatched:
        report.append("TOP UNMATCHED PLAYERS (Need Manual Review)")
        report.append("-" * 80)
        top_unmatched = sorted(unmatched, key=lambda x: x['points'], reverse=True)[:30]

        for r in top_unmatched:
            report.append(
                f"  {r['player_name']:<25} {r['team']:<20} "
                f"{r['points']:2}pts {r['ppg']:.2f}ppg"
            )
        report.append("")

    # Low confidence matches for review
    if low_conf:
        report.append("LOW CONFIDENCE MATCHES (Review Recommended)")
        report.append("-" * 80)
        for r in sorted(low_conf, key=lambda x: x['points'], reverse=True)[:20]:
            report.append(
                f"  {r['player_name']:<22} → DB:{r.get('prodigy_team', 'Unknown'):<18} "
                f"Conf:{r['match_confidence']*100:.0f}% | {r['match_reason']}"
            )

    report.append("")
    report.append("=" * 80)
    report.append("END OF MATCHING REPORT")
    report.append("=" * 80)

    return "\n".join(report)


def export_matched_csv(results: List[Dict], filename: str):
    """Export matched data to CSV."""
    filepath = os.path.join(os.path.dirname(__file__), filename)

    fieldnames = [
        'nepsac_rank', 'player_name', 'first_name', 'last_name', 'team', 'position',
        'games_played', 'goals', 'assists', 'points', 'ppg',
        'matched', 'match_confidence', 'match_reason',
        'player_id', 'birth_year', 'nationality', 'ep_views', 'prodigy_points',
        'prodigy_team', 'prodigy_league'
    ]

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()

        # Sort by NEPSAC rank
        sorted_results = sorted(results, key=lambda x: x['nepsac_rank'])
        writer.writerows(sorted_results)

    print(f"Exported to {filepath}")


def main():
    print("=" * 60)
    print("NEPSAC PLAYER MATCHER")
    print("=" * 60)

    # Load NEPSAC players
    csv_path = os.path.join(os.path.dirname(__file__), "nepsac_983_players.csv")
    print(f"\nLoading NEPSAC players from {csv_path}...")
    nepsac_players = load_nepsac_players(csv_path)
    print(f"Loaded {len(nepsac_players)} NEPSAC players")

    # Fetch ProdigyRanking players
    print("\nFetching players from ProdigyRanking database...")
    prodigy_players = fetch_prodigy_players()
    print(f"Loaded {len(prodigy_players)} players from database")

    # Match players
    print("\nMatching players (this may take a moment)...")
    results = match_players(nepsac_players, prodigy_players)

    matched_count = sum(1 for r in results if r['matched'])
    print(f"Matched {matched_count}/{len(results)} players")

    # Generate report
    print("\nGenerating match report...")
    report = generate_match_report(results)
    # Handle encoding for Windows console
    try:
        print("\n" + report)
    except UnicodeEncodeError:
        print("\n" + report.encode('ascii', 'replace').decode('ascii'))

    # Save report
    report_path = os.path.join(os.path.dirname(__file__), "nepsac_match_report.txt")
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\nReport saved to {report_path}")

    # Export CSV
    export_matched_csv(results, "nepsac_matched_players.csv")

    print("\nMatching complete!")


if __name__ == "__main__":
    main()

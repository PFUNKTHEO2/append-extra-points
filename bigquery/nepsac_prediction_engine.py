"""
NEPSAC Enhanced Prediction Engine
Ace & Scouty's Game Prediction Model

Combines multiple data sources:
- ProdigyPoints (team talent level) with AGE NORMALIZATION
- Recent form (last 5 games)
- Goals for/against differential
- Home/away advantage
- Head-to-head history

Age Normalization:
A 16-year-old performing at prep level is more impressive than a 19-year-old.
We apply age multipliers to individual player points before team aggregation.
This also compensates for EP views accumulating over time (older = more views).
"""

import csv
import json
from datetime import datetime, timedelta
from collections import defaultdict
import re

# =============================================================================
# AGE NORMALIZATION
# =============================================================================

# Current season reference (January 2026)
CURRENT_YEAR = 2026

# Age multipliers by birth year
# Younger players get a boost because:
# 1. Less time to accumulate EP views (big part of algorithm)
# 2. More impressive to perform against older competition
# 3. Higher potential trajectory
AGE_MULTIPLIERS = {
    2011: 1.45,  # 14-15 year old (exceptional if playing prep)
    2010: 1.35,  # 15-16 year old
    2009: 1.22,  # 16-17 year old
    2008: 1.10,  # 17-18 year old (typical prep junior/senior)
    2007: 1.00,  # 18-19 year old (baseline - PG year)
    2006: 0.92,  # 19-20 year old (older PG, slight penalty)
    2005: 0.85,  # 20+ year old (significant penalty)
}

def get_age_multiplier(birth_year):
    """Get age multiplier for a player's birth year"""
    if not birth_year:
        return 1.0  # No birth year = no adjustment

    try:
        year = int(birth_year)
        # Use the defined multipliers, or interpolate for edge cases
        if year in AGE_MULTIPLIERS:
            return AGE_MULTIPLIERS[year]
        elif year > 2011:
            return 1.50  # Even younger = bigger boost
        elif year < 2005:
            return 0.80  # Even older = bigger penalty
        else:
            return 1.0
    except (ValueError, TypeError):
        return 1.0

# =============================================================================
# DATA LOADING
# =============================================================================

def load_game_results(filepath='nz_boys_prep_results_only.csv'):
    """Load game-by-game results from Neutral Zone CSV"""
    games = []

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Handle data quality issues (some rows have date in wrong column)
            date = row['Date']
            opponent = row['Opponent']

            # If Date is empty but Opponent looks like a date, swap them
            if not date and opponent and re.match(r'\d{1,2}/\d{1,2}/\d{4}', opponent):
                date = opponent
                opponent = ''

            if date and opponent:
                games.append({
                    'team': normalize_team_name(row['Team']),
                    'date': parse_date(date),
                    'home_away': row['Home/Away'],
                    'opponent': normalize_team_name(opponent),
                    'outcome': row['Outcome'],
                    'team_score': int(row['Team Score']) if row['Team Score'] else 0,
                    'opp_score': int(row['Opponent Score']) if row['Opponent Score'] else 0
                })

    return games


def load_team_rankings(filepath='nepsac_team_rankings_full.csv'):
    """Load team ProdigyPoints rankings"""
    rankings = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize_team_name(row['team'])
            rankings[team] = {
                'rank': int(row['rank']),
                'avg_points': float(row['avg_points']),
                'total_points': float(row['total_points']),
                'max_points': float(row['max_points']),
                'roster_size': int(row['roster_size'])
            }

    return rankings


def load_player_roster(filepath='neutralzone_prep_boys_hockey_data_clean.csv'):
    """
    Load player roster with birth years for age adjustment

    Uses NeutralZone data as the authoritative source.

    Returns dict keyed by team with list of players:
    {
        'avon old farms': [
            {'name': 'John Smith', 'birth_year': 2008, 'points': 3500, 'position': 'F'},
            ...
        ]
    }
    """
    from collections import defaultdict
    roster = defaultdict(list)

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize_team_name(row['team'])

            # Convert rank to points-like value (lower rank = more points)
            # Rank 1 = best player, we want higher points for better players
            rank = row.get('rank', '')
            if rank and rank.strip():
                try:
                    rank_val = float(rank)
                    # Convert rank to inverted points (max ~10000 for rank 1)
                    points = max(0, 10000 - rank_val * 5)
                except (ValueError, TypeError):
                    points = 0
            else:
                points = 0

            # Only include players with points (ranked players)
            if points > 0:
                # Derive birth year from graduation year (grad_year - 18 approx)
                birth_year = None
                grad_year = row.get('grad_year', '')
                if grad_year and grad_year.strip():
                    try:
                        grad = float(grad_year)
                        birth_year = int(grad - 18)  # Approximate birth year
                    except (ValueError, TypeError):
                        pass

                roster[team].append({
                    'name': row.get('player_name', ''),
                    'birth_year': birth_year,
                    'points': points,
                    'position': row.get('position', '')
                })

    return dict(roster)


def calculate_age_adjusted_rankings(roster, original_rankings=None):
    """
    Calculate team rankings with age-adjusted player points

    A 2010-born player (15-16 yr old) with 2100 points gets boosted to ~2835
    A 2007-born player (18-19 yr old) with 2800 points stays at 2800

    This recognizes that younger players performing at same level have higher talent.
    """
    rankings = {}

    for team, players in roster.items():
        if not players:
            continue

        # Calculate age-adjusted points for each player
        adjusted_players = []
        for p in players:
            multiplier = get_age_multiplier(p['birth_year'])
            adjusted_points = p['points'] * multiplier
            adjusted_players.append({
                **p,
                'raw_points': p['points'],
                'adjusted_points': adjusted_points,
                'age_multiplier': multiplier
            })

        # Sort by adjusted points for top player
        adjusted_players.sort(key=lambda x: x['adjusted_points'], reverse=True)

        # Calculate team aggregates
        total_adjusted = sum(p['adjusted_points'] for p in adjusted_players)
        total_raw = sum(p['raw_points'] for p in adjusted_players)
        roster_size = len(adjusted_players)

        avg_adjusted = total_adjusted / roster_size if roster_size > 0 else 0
        avg_raw = total_raw / roster_size if roster_size > 0 else 0

        max_adjusted = adjusted_players[0]['adjusted_points'] if adjusted_players else 0
        max_raw = adjusted_players[0]['raw_points'] if adjusted_players else 0

        # Calculate average age multiplier (indicator of team youth)
        avg_multiplier = sum(p['age_multiplier'] for p in adjusted_players) / roster_size if roster_size > 0 else 1.0

        # Get original rank if available
        original_rank = 999
        if original_rankings and team in original_rankings:
            original_rank = original_rankings[team].get('rank', 999)

        rankings[team] = {
            'rank': original_rank,  # Will be re-ranked later
            'avg_points': avg_adjusted,
            'avg_points_raw': avg_raw,
            'total_points': total_adjusted,
            'total_points_raw': total_raw,
            'max_points': max_adjusted,
            'max_points_raw': max_raw,
            'roster_size': roster_size,
            'avg_age_multiplier': avg_multiplier,
            'top_players': adjusted_players[:6]  # Top 6 for display
        }

    # Re-rank by age-adjusted average points
    sorted_teams = sorted(rankings.items(), key=lambda x: x[1]['avg_points'], reverse=True)
    for i, (team, data) in enumerate(sorted_teams, 1):
        rankings[team]['rank'] = i
        rankings[team]['rank_change'] = data.get('rank', i) - i  # Positive = moved up with age adjustment

    return rankings


def load_standings(filepath='nepsac_standings_jan19.csv'):
    """Load current standings"""
    standings = {}

    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = normalize_team_name(row['team'])
            standings[team] = {
                'wins': int(row['wins']),
                'losses': int(row['losses']),
                'ties': int(row['ties']),
                'win_pct': float(row['win_pct']),
                'division': row['division']
            }

    return standings


def load_schedule(filepath='nepsac_full_schedule.json'):
    """Load the full game schedule"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# TEAM NAME NORMALIZATION
# =============================================================================

TEAM_ALIASES = {
    'bb&n': 'bb&n',
    'buckingham browne and nichols': 'bb&n',
    'buckingham browne & nichols': 'bb&n',
    'belmont hill': 'belmont hill',
    'berwick academy': 'berwick',
    'berwick': 'berwick',
    'brooks school': 'brooks school',
    'brooks': 'brooks school',
    'choate rosemary hall': 'choate',
    'choate': 'choate',
    'dexter': 'dexter',
    'dexter southfield': 'dexter',
    'governors academy': 'governors academy',
    'governors': 'governors academy',
    'the governors academy': 'governors academy',
    'groton': 'groton',
    'groton eberhart': 'groton',
    'hoosac': 'hoosac',
    'hoosac school': 'hoosac',
    'kent school': 'kent school',
    'kent': 'kent school',
    'kent school housatonic': 'kent school',
    'middlesex': 'middlesex',
    'middlesex school': 'middlesex',
    'milton academy': 'milton academy',
    'milton': 'milton academy',
    'noble & greenough': 'noble & greenough',
    'nobles': 'noble & greenough',
    'rivers school': 'rivers school',
    'rivers': 'rivers school',
    'roxbury latin': 'roxbury latin',
    'st. marks': 'st. marks',
    "st. mark's": 'st. marks',
    'st marks': 'st. marks',
    'st. georges': 'st. georges',
    "st. george's": 'st. georges',
    'st georges': 'st. georges',
    "st. sebastian's": "st. sebastian's",
    'st sebastians': "st. sebastian's",
    "st. paul's school": "st. paul's school",
    'st pauls': "st. paul's school",
    'thayer academy': 'thayer academy',
    'thayer': 'thayer academy',
    'andover': 'andover',
    'phillips andover': 'andover',
    'exeter': 'exeter',
    'phillips exeter': 'exeter',
    'phillips exeter academy': 'exeter',
    'avon old farms': 'avon old farms',
    'avon': 'avon old farms',
    'salisbury school': 'salisbury school',
    'salisbury': 'salisbury school',
    'hotchkiss school': 'hotchkiss school',
    'hotchkiss': 'hotchkiss school',
    'taft': 'taft',
    'taft school': 'taft',
    'loomis chaffee': 'loomis chaffee',
    'loomis': 'loomis chaffee',
    'westminster': 'westminster',
    'canterbury': 'canterbury',
    'canterbury school': 'canterbury',
    'berkshire school': 'berkshire school',
    'berkshire': 'berkshire school',
    'pomfret': 'pomfret',
    'pomfret school': 'pomfret',
    'pomfret independent': 'pomfret',
    'frederick gunn': 'frederick gunn',
    'frederick gunn school': 'frederick gunn',
    'deerfield academy': 'deerfield academy',
    'deerfield': 'deerfield academy',
    'cushing academy': 'cushing academy',
    'cushing': 'cushing academy',
    'kimball union': 'kimball union',
    'kimball union academy': 'kimball union',
    'kua': 'kimball union',
    'holderness': 'holderness',
    'holderness school': 'holderness',
    'proctor academy': 'proctor academy',
    'proctor': 'proctor academy',
    'tilton': 'tilton',
    'tilton school': 'tilton',
    'new hampton': 'new hampton',
    'new hampton school': 'new hampton',
    'brewster': 'brewster',
    'brewster academy': 'brewster',
    'vermont academy': 'vermont academy',
    'nmh': 'nmh',
    'northfield mount hermon': 'nmh',
    'northfield mt. hermon': 'nmh',
    'williston-northampton': 'williston-northampton',
    'williston northampton': 'williston-northampton',
    'williston': 'williston-northampton',
    'worcester academy': 'worcester academy',
    'worcester': 'worcester academy',
    'winchendon': 'winchendon',
    'winchendon school': 'winchendon',
    'tabor': 'tabor',
    'tabor academy': 'tabor',
    'tabor keller': 'tabor',
    'lawrence academy': 'lawrence academy',
    'lawrence': 'lawrence academy',
    'pingree': 'pingree',
    'pingree school': 'pingree',
    'portsmouth abbey': 'portsmouth abbey',
    'north yarmouth': 'north yarmouth',
    'north yarmouth academy': 'north yarmouth',
    'nya': 'north yarmouth',
    'kents hill': 'kents hill',
    'kents hill school': 'kents hill',
    'hebron': 'hebron',
    'hebron academy': 'hebron',
    'trinity-pawling': 'trinity-pawling',
    'trinity pawling': 'trinity-pawling',
    'lawrenceville school': 'lawrenceville school',
    'lawrenceville': 'lawrenceville school',
    'the hill school': 'the hill school',
    'hill school': 'the hill school',
    'albany academy': 'albany academy',
    'albany': 'albany academy',
    'austin prep': 'austin prep',
    'mount st. charles': 'mount st. charles',
    'mount st charles': 'mount st. charles',
    'msc': 'mount st. charles',
    'brunswick': 'brunswick',
    'brunswick school': 'brunswick',
    'millbrook': 'millbrook',
    'millbrook school': 'millbrook',
    'wilbraham & monson': 'wilbraham & monson',
    'wilbraham and monson': 'wilbraham & monson',
}

def normalize_team_name(name):
    """Normalize team name for matching"""
    if not name:
        return ''

    # Lowercase and strip
    normalized = name.lower().strip()

    # Replace curly apostrophes with straight
    normalized = normalized.replace('\u2019', "'").replace('\u2018', "'")

    # Look up in aliases
    return TEAM_ALIASES.get(normalized, normalized)


def parse_date(date_str):
    """Parse date string to datetime"""
    if not date_str:
        return None

    # Handle various formats
    for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%m/%d/%y']:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue

    return None


# =============================================================================
# STATS CALCULATION
# =============================================================================

def calculate_team_stats(games, as_of_date=None):
    """
    Calculate comprehensive stats for each team from game results

    Returns dict with:
    - recent_form: Last 5 games (W-L-T)
    - goals_per_game: Average goals scored
    - goals_against_per_game: Average goals allowed
    - goal_diff_per_game: Net goal differential per game
    - home_record: Record at home (W-L-T)
    - away_record: Record on road (W-L-T)
    - streak: Current streak (W3, L2, etc.)
    """

    if as_of_date is None:
        as_of_date = datetime.now()

    team_stats = defaultdict(lambda: {
        'games': [],
        'home_games': [],
        'away_games': [],
        'total_gf': 0,
        'total_ga': 0,
        'wins': 0,
        'losses': 0,
        'ties': 0
    })

    # Process all games
    for game in games:
        if game['date'] and game['date'] <= as_of_date:
            team = game['team']
            stats = team_stats[team]

            stats['games'].append(game)
            stats['total_gf'] += game['team_score']
            stats['total_ga'] += game['opp_score']

            if game['outcome'] == 'Win':
                stats['wins'] += 1
            elif game['outcome'] == 'Loss':
                stats['losses'] += 1
            else:
                stats['ties'] += 1

            if game['home_away'] == 'Home':
                stats['home_games'].append(game)
            else:
                stats['away_games'].append(game)

    # Calculate derived stats for each team
    result = {}
    for team, stats in team_stats.items():
        num_games = len(stats['games'])
        if num_games == 0:
            continue

        # Sort games by date for recent form
        sorted_games = sorted(stats['games'], key=lambda g: g['date'], reverse=True)

        # Last 5 games
        last_5 = sorted_games[:5]
        last_5_record = calculate_record(last_5)

        # Recent form score (0-1 scale, 1 = all wins)
        form_score = (last_5_record['wins'] + 0.5 * last_5_record['ties']) / len(last_5) if last_5 else 0.5

        # Current streak
        streak = calculate_streak(sorted_games)

        # Home/Away records
        home_record = calculate_record(stats['home_games'])
        away_record = calculate_record(stats['away_games'])

        result[team] = {
            'games_played': num_games,
            'wins': stats['wins'],
            'losses': stats['losses'],
            'ties': stats['ties'],
            'win_pct': (stats['wins'] + 0.5 * stats['ties']) / num_games,
            'goals_per_game': stats['total_gf'] / num_games,
            'goals_against_per_game': stats['total_ga'] / num_games,
            'goal_diff_per_game': (stats['total_gf'] - stats['total_ga']) / num_games,
            'last_5_record': f"{last_5_record['wins']}-{last_5_record['losses']}-{last_5_record['ties']}",
            'form_score': form_score,
            'streak': streak,
            'home_record': f"{home_record['wins']}-{home_record['losses']}-{home_record['ties']}",
            'away_record': f"{away_record['wins']}-{away_record['losses']}-{away_record['ties']}",
            'home_win_pct': home_record['wins'] / len(stats['home_games']) if stats['home_games'] else 0.5,
            'away_win_pct': away_record['wins'] / len(stats['away_games']) if stats['away_games'] else 0.5
        }

    return result


def calculate_record(games):
    """Calculate W-L-T record from list of games"""
    wins = sum(1 for g in games if g['outcome'] == 'Win')
    losses = sum(1 for g in games if g['outcome'] == 'Loss')
    ties = len(games) - wins - losses
    return {'wins': wins, 'losses': losses, 'ties': ties}


def calculate_streak(sorted_games):
    """Calculate current streak (e.g., 'W3', 'L2')"""
    if not sorted_games:
        return '-'

    first_outcome = sorted_games[0]['outcome']
    streak_type = first_outcome[0]  # W, L, or T
    count = 1

    for game in sorted_games[1:]:
        if game['outcome'] == first_outcome:
            count += 1
        else:
            break

    return f"{streak_type}{count}"


def calculate_head_to_head(games, team1, team2):
    """
    Calculate head-to-head record between two teams
    Returns record from team1's perspective
    """
    h2h_games = [g for g in games
                 if (g['team'] == team1 and g['opponent'] == team2)]

    if not h2h_games:
        return None

    record = calculate_record(h2h_games)
    return {
        'wins': record['wins'],
        'losses': record['losses'],
        'ties': record['ties'],
        'games': len(h2h_games)
    }


# =============================================================================
# PREDICTION MODEL
# =============================================================================

# Weight factors (must sum to 1.0)
# UPDATED 2026-01-26: Added NEHJ expert rankings alongside JSPR
# Key changes:
#   - JSPR at 20% - official league rankings with RPI (updated weekly)
#   - NEHJ Expert at 10% - Evan Marinofsky's expert rankings (captures intangibles)
#   - Performance ranking at 15% - our own ELO-style ranking from game results
#   - MHR at 18% - mathematical ELO with schedule strength
#   - Reduced reliance on roster-based factors
PREDICTION_WEIGHTS = {
    'jspr_ranking': 0.20,       # NEPSIHA JSPR - Official league power rankings
    'nehj_expert': 0.10,        # NEHJ Expert Rankings - Marinofsky's eye test (NEW)
    'mhr_rating': 0.18,         # MyHockeyRankings ELO with schedule strength
    'performance_rank': 0.15,   # Our own ELO from game results
    'recent_form': 0.12,        # Last 5 games performance
    'win_pct': 0.08,            # Overall win percentage
    'top_player': 0.07,         # Best player on roster (age-adjusted)
    'head_to_head': 0.05,       # Historical matchup
    'home_advantage': 0.03,     # Home ice advantage
    'goal_diff': 0.02,          # Goals differential
}

# Home advantage factor - reduced from 0.58 to 0.55 to better predict away upsets
# Data: Home teams won 60% of games, but we missed 9/10 away upset predictions
HOME_ADVANTAGE = 0.55


def load_expert_rankings(filepath='nepsac_expert_rankings_jan21.csv'):
    """
    Load expert power rankings with GPG/GAA data

    Expert rankings capture intangibles our algorithm misses:
    - Coaching quality
    - Team chemistry
    - Goaltending (Tabor's D'Urso, Hotchkiss's Johnson)
    - Systems play
    """
    expert = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = normalize_team_name(row['team'])
                expert[team] = {
                    'rank': int(row['expert_rank']),
                    'gpg': float(row['gpg']),
                    'gaa': float(row['gaa']),
                    'hot_streak': int(row['hot_streak']),
                    'elite_goalie': int(row['elite_goalie']),
                    'record': row['record']
                }
    except FileNotFoundError:
        pass  # Expert rankings optional

    return expert


def load_mhr_rankings(filepath='nepsac_mhr_rankings_jan21.csv'):
    """
    Load MyHockeyRankings power rankings

    MHR provides mathematical ELO-style ratings that account for:
    - Opponent quality (schedule strength)
    - Goal differential
    - Win/loss record

    This covers ALL 60 teams, unlike expert rankings (top 10 only)
    """
    mhr = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = normalize_team_name(row['team'])
                mhr[team] = {
                    'rank': int(row['mhr_rank']),
                    'rating': float(row['rating']),
                    'agd': float(row['agd']),  # Average Goal Differential
                    'schedule_strength': float(row['schedule_strength']),
                    'wins': int(row['wins']),
                    'losses': int(row['losses']),
                    'ties': int(row['ties'])
                }
    except FileNotFoundError:
        pass  # MHR rankings optional

    return mhr


def load_jspr_rankings(filepath='nepsac_jspr_rankings.csv'):
    """
    Load NEPSIHA JSPR (Jeff Seaver Power Rankings)

    Official prep school hockey power rankings from U.S. Hockey Report.
    Updated weekly during the season.

    JSPR uses:
    - RPI (Rating Percentage Index) - accounts for opponent strength
    - League points (wins/ties)
    - Schedule strength

    This is the OFFICIAL ranking system for NEPSIHA playoffs.
    """
    jspr = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = normalize_team_name(row['team'])
                jspr[team] = {
                    'rank': int(row['rank']),
                    'rpi_rank': int(row['rpi_rank']),
                    'points': int(row['points']),
                    'rpi': float(row['rpi']),
                    'updated': row['updated']
                }
    except FileNotFoundError:
        print("  Warning: JSPR rankings file not found")

    return jspr


def load_nehj_expert_rankings(filepath='nepsac_nehj_expert_rankings.csv'):
    """
    Load NEHJ (New England Hockey Journal) expert rankings by Evan Marinofsky.

    Expert rankings capture intangibles that pure stats miss:
    - Coaching quality and systems
    - Team chemistry and momentum
    - Goaltending depth
    - Schedule difficulty ahead
    - Eye test from watching games

    Updated weekly during the season.
    """
    nehj = {}

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team = normalize_team_name(row['team'])

                # Parse wins/losses/ties if available
                wins = int(row['wins']) if row.get('wins') and row['wins'].strip() else 0
                losses = int(row['losses']) if row.get('losses') and row['losses'].strip() else 0
                ties = int(row['ties']) if row.get('ties') and row['ties'].strip() else 0

                nehj[team] = {
                    'rank': int(row['rank']),
                    'record': row.get('record', ''),
                    'wins': wins,
                    'losses': losses,
                    'ties': ties,
                    'notes': row.get('notes', ''),
                    'updated': row.get('updated', '')
                }
    except FileNotFoundError:
        print("  Warning: NEHJ expert rankings file not found")

    return nehj


def calculate_performance_rankings(games, as_of_date=None):
    """
    Calculate our own ELO-style performance rankings from game results.

    This creates a pure performance-based ranking that:
    - Rewards wins against strong opponents
    - Penalizes losses to weak opponents
    - Accounts for margin of victory (capped)
    - Uses recent games more heavily

    Returns dict with rank and rating for each team.
    """
    from collections import defaultdict

    if as_of_date is None:
        as_of_date = datetime.now()

    # Initialize ratings (start at 1500 like chess ELO)
    BASE_RATING = 1500
    K_FACTOR = 32  # How much ratings change per game

    ratings = defaultdict(lambda: BASE_RATING)
    games_played = defaultdict(int)

    # Sort games by date
    sorted_games = sorted([g for g in games if g['date'] and g['date'] <= as_of_date],
                          key=lambda g: g['date'])

    # Process each game and update ratings
    for game in sorted_games:
        team = game['team']
        opponent = game['opponent']

        if not opponent:
            continue

        team_rating = ratings[team]
        opp_rating = ratings[opponent]

        # Expected score (ELO formula)
        expected = 1 / (1 + 10 ** ((opp_rating - team_rating) / 400))

        # Actual score (1 for win, 0.5 for tie, 0 for loss)
        if game['outcome'] == 'Win':
            actual = 1.0
            # Bonus for margin of victory (capped at 3 goals)
            margin = min(3, game['team_score'] - game['opp_score'])
            actual += margin * 0.05
        elif game['outcome'] == 'Loss':
            actual = 0.0
        else:
            actual = 0.5

        # Update rating
        ratings[team] += K_FACTOR * (actual - expected)
        games_played[team] += 1

    # Convert to rankings
    sorted_teams = sorted(ratings.items(), key=lambda x: x[1], reverse=True)

    performance_rankings = {}
    for i, (team, rating) in enumerate(sorted_teams, 1):
        if games_played[team] >= 3:  # Minimum 3 games to be ranked
            performance_rankings[team] = {
                'rank': i,
                'rating': round(rating, 1),
                'games_played': games_played[team]
            }

    return performance_rankings


def predict_game(away_team, home_team, rankings, team_stats, games, expert_rankings=None, mhr_rankings=None, jspr_rankings=None, performance_rankings=None, nehj_rankings=None):
    """
    Predict game outcome using multi-factor model

    Returns:
    - predicted_winner: Team name
    - confidence: 50-99%
    - factors: Dict with each factor's contribution
    """
    if expert_rankings is None:
        expert_rankings = {}
    if mhr_rankings is None:
        mhr_rankings = {}
    if jspr_rankings is None:
        jspr_rankings = {}
    if performance_rankings is None:
        performance_rankings = {}
    if nehj_rankings is None:
        nehj_rankings = {}

    # Normalize team names
    away_team = normalize_team_name(away_team)
    home_team = normalize_team_name(home_team)

    # Initialize scores
    away_score = 0
    home_score = 0
    factors = {}

    # Get data for each team
    away_ranking = rankings.get(away_team, {})
    home_ranking = rankings.get(home_team, {})
    away_stats = team_stats.get(away_team, {})
    home_stats = team_stats.get(home_team, {})
    away_mhr = mhr_rankings.get(away_team, {})
    home_mhr = mhr_rankings.get(home_team, {})
    away_jspr = jspr_rankings.get(away_team, {})
    home_jspr = jspr_rankings.get(home_team, {})
    away_perf = performance_rankings.get(away_team, {})
    home_perf = performance_rankings.get(home_team, {})
    away_nehj = nehj_rankings.get(away_team, {})
    home_nehj = nehj_rankings.get(home_team, {})

    # ==========================================================================
    # 1. JSPR Rankings (25%) - OFFICIAL NEPSIHA power rankings
    # This is the most important factor - official league rankings with RPI
    # ==========================================================================
    away_jspr_rank = away_jspr.get('rank', 40)  # Default to #40 if not ranked
    home_jspr_rank = home_jspr.get('rank', 40)
    away_rpi = away_jspr.get('rpi', 0.50)
    home_rpi = home_jspr.get('rpi', 0.50)

    # Normalize RPI to 0-1 scale (range: 0.50 to 0.65)
    rpi_min, rpi_max = 0.50, 0.65
    away_rpi_norm = (away_rpi - rpi_min) / (rpi_max - rpi_min)
    home_rpi_norm = (home_rpi - rpi_min) / (rpi_max - rpi_min)

    away_score += PREDICTION_WEIGHTS['jspr_ranking'] * max(0, min(1, away_rpi_norm))
    home_score += PREDICTION_WEIGHTS['jspr_ranking'] * max(0, min(1, home_rpi_norm))

    factors['jspr_ranking'] = {
        'away': f"#{away_jspr_rank}" if away_jspr_rank <= 16 else 'NR',
        'away_rpi': round(away_rpi, 4),
        'home': f"#{home_jspr_rank}" if home_jspr_rank <= 16 else 'NR',
        'home_rpi': round(home_rpi, 4),
        'favors': 'home' if home_rpi > away_rpi else 'away'
    }

    # ==========================================================================
    # 2. Performance Rankings (15%) - Our own ELO-style ranking from game results
    # ==========================================================================
    away_perf_rank = away_perf.get('rank', 50)
    home_perf_rank = home_perf.get('rank', 50)
    away_perf_rating = away_perf.get('rating', 1500)
    home_perf_rating = home_perf.get('rating', 1500)

    # Normalize rating to 0-1 scale (range: 1400 to 1650)
    perf_min, perf_max = 1400, 1650
    away_perf_norm = (away_perf_rating - perf_min) / (perf_max - perf_min)
    home_perf_norm = (home_perf_rating - perf_min) / (perf_max - perf_min)

    away_score += PREDICTION_WEIGHTS['performance_rank'] * max(0, min(1, away_perf_norm))
    home_score += PREDICTION_WEIGHTS['performance_rank'] * max(0, min(1, home_perf_norm))

    factors['performance_rank'] = {
        'away': f"#{away_perf_rank}",
        'away_rating': round(away_perf_rating, 1),
        'home': f"#{home_perf_rank}",
        'home_rating': round(home_perf_rating, 1),
        'favors': 'home' if home_perf_rating > away_perf_rating else 'away'
    }

    # ==========================================================================
    # 3. MHR Rating (20%) - ELO-style rating adjusted for schedule strength
    # Rating range: ~89 (bottom) to ~100 (top)
    away_mhr_rating = away_mhr.get('rating', 94.0)  # Default to middle-tier
    home_mhr_rating = home_mhr.get('rating', 94.0)

    # Normalize to 0-1 scale (89-100 range)
    mhr_min, mhr_max = 89.0, 100.0
    away_mhr_norm = (away_mhr_rating - mhr_min) / (mhr_max - mhr_min)
    home_mhr_norm = (home_mhr_rating - mhr_min) / (mhr_max - mhr_min)

    away_score += PREDICTION_WEIGHTS['mhr_rating'] * max(0, min(1, away_mhr_norm))
    home_score += PREDICTION_WEIGHTS['mhr_rating'] * max(0, min(1, home_mhr_norm))

    factors['mhr_rating'] = {
        'away': round(away_mhr_rating, 2),
        'away_rank': away_mhr.get('rank', 'NR'),
        'away_agd': away_mhr.get('agd', '-'),
        'home': round(home_mhr_rating, 2),
        'home_rank': home_mhr.get('rank', 'NR'),
        'home_agd': home_mhr.get('agd', '-'),
        'favors': 'home' if home_mhr_rating > away_mhr_rating else 'away'
    }

    # ==========================================================================
    # 4. NEHJ Expert Rankings (10%) - Marinofsky's expert eye test
    # Captures intangibles: coaching, chemistry, goaltending, momentum
    # ==========================================================================
    away_nehj_rank = away_nehj.get('rank', 25)  # Default to #25 if not ranked
    home_nehj_rank = home_nehj.get('rank', 25)

    # Convert rank to score (lower rank = higher score)
    # Rank 1 = 1.0, Rank 14 = 0.0 (bottom of ranked teams)
    nehj_min, nehj_max = 1, 14
    away_nehj_norm = max(0, (nehj_max - away_nehj_rank) / (nehj_max - nehj_min))
    home_nehj_norm = max(0, (nehj_max - home_nehj_rank) / (nehj_max - nehj_min))

    away_score += PREDICTION_WEIGHTS['nehj_expert'] * away_nehj_norm
    home_score += PREDICTION_WEIGHTS['nehj_expert'] * home_nehj_norm

    factors['nehj_expert'] = {
        'away': f"#{away_nehj_rank}" if away_nehj_rank <= 14 else 'NR',
        'home': f"#{home_nehj_rank}" if home_nehj_rank <= 14 else 'NR',
        'away_notes': away_nehj.get('notes', '')[:50] if away_nehj.get('notes') else '',
        'home_notes': home_nehj.get('notes', '')[:50] if home_nehj.get('notes') else '',
        'favors': 'home' if home_nehj_rank < away_nehj_rank else 'away'
    }

    # ==========================================================================
    # 5. Recent Form (12%)
    # ==========================================================================
    away_form = away_stats.get('form_score', 0.5)
    home_form = home_stats.get('form_score', 0.5)

    away_score += PREDICTION_WEIGHTS['recent_form'] * away_form
    home_score += PREDICTION_WEIGHTS['recent_form'] * home_form
    factors['recent_form'] = {
        'away': away_stats.get('last_5_record', '-'),
        'home': home_stats.get('last_5_record', '-'),
        'favors': 'home' if home_form > away_form else 'away'
    }

    # 3. Goal Differential (15%)
    away_gd = away_stats.get('goal_diff_per_game', 0)
    home_gd = home_stats.get('goal_diff_per_game', 0)

    # Normalize (-3 to +3 typical range)
    away_gd_norm = (away_gd + 3) / 6  # Maps -3 to 0, +3 to 1
    home_gd_norm = (home_gd + 3) / 6

    away_score += PREDICTION_WEIGHTS['goal_diff'] * max(0, min(1, away_gd_norm))
    home_score += PREDICTION_WEIGHTS['goal_diff'] * max(0, min(1, home_gd_norm))
    factors['goal_diff'] = {
        'away': round(away_gd, 2),
        'home': round(home_gd, 2),
        'favors': 'home' if home_gd > away_gd else 'away'
    }

    # 4. Home Advantage (10%)
    # Away team gets (1 - HOME_ADVANTAGE), home gets HOME_ADVANTAGE
    away_score += PREDICTION_WEIGHTS['home_advantage'] * (1 - HOME_ADVANTAGE)
    home_score += PREDICTION_WEIGHTS['home_advantage'] * HOME_ADVANTAGE
    factors['home_advantage'] = {
        'away': 'Away',
        'home': 'Home',
        'favors': 'home'
    }

    # 5. Overall Win Percentage (10%)
    away_wp = away_stats.get('win_pct', 0.5)
    home_wp = home_stats.get('win_pct', 0.5)

    away_score += PREDICTION_WEIGHTS['win_pct'] * away_wp
    home_score += PREDICTION_WEIGHTS['win_pct'] * home_wp
    factors['win_pct'] = {
        'away': f"{away_wp:.1%}",
        'home': f"{home_wp:.1%}",
        'favors': 'home' if home_wp > away_wp else 'away'
    }

    # 6. Top Player with Age Adjustment (10%)
    away_max = away_ranking.get('max_points', 3000)
    home_max = home_ranking.get('max_points', 3000)
    away_max_raw = away_ranking.get('max_points_raw', away_max)
    home_max_raw = home_ranking.get('max_points_raw', home_max)

    # Normalize (range roughly 2500-6500 for age-adjusted)
    max_min, max_max = 2500, 6500
    away_max_norm = (away_max - max_min) / (max_max - max_min)
    home_max_norm = (home_max - max_min) / (max_max - max_min)

    away_score += PREDICTION_WEIGHTS['top_player'] * max(0, min(1, away_max_norm))
    home_score += PREDICTION_WEIGHTS['top_player'] * max(0, min(1, home_max_norm))
    factors['top_player'] = {
        'away': round(away_max, 0),
        'away_raw': round(away_max_raw, 0),
        'home': round(home_max, 0),
        'home_raw': round(home_max_raw, 0),
        'favors': 'home' if home_max > away_max else 'away'
    }

    # 7. Head-to-Head (5%)
    h2h = calculate_head_to_head(games, away_team, home_team)
    if h2h and h2h['games'] > 0:
        # Away team's perspective
        h2h_score = (h2h['wins'] + 0.5 * h2h['ties']) / h2h['games']
        away_score += PREDICTION_WEIGHTS['head_to_head'] * h2h_score
        home_score += PREDICTION_WEIGHTS['head_to_head'] * (1 - h2h_score)
        factors['head_to_head'] = {
            'away': f"{h2h['wins']}-{h2h['losses']}-{h2h['ties']}",
            'home': f"{h2h['losses']}-{h2h['wins']}-{h2h['ties']}",
            'favors': 'away' if h2h['wins'] > h2h['losses'] else 'home'
        }
    else:
        # No head-to-head, split evenly
        away_score += PREDICTION_WEIGHTS['head_to_head'] * 0.5
        home_score += PREDICTION_WEIGHTS['head_to_head'] * 0.5
        factors['head_to_head'] = {
            'away': 'N/A',
            'home': 'N/A',
            'favors': 'neutral'
        }

    # Calculate winner and confidence
    total_score = away_score + home_score
    if total_score == 0:
        total_score = 1  # Avoid division by zero

    away_pct = away_score / total_score
    home_pct = home_score / total_score

    if home_pct >= away_pct:
        predicted_winner = home_team
        win_probability = home_pct
    else:
        predicted_winner = away_team
        win_probability = away_pct

    # Convert probability to confidence (50-99 scale)
    # 50% probability = 50 confidence (toss-up)
    # 75% probability = 75 confidence
    # 95% probability = 95 confidence (max practical)
    confidence = int(min(99, max(50, win_probability * 100)))

    # Confidence tier
    if confidence >= 85:
        tier = 'Very High'
    elif confidence >= 70:
        tier = 'High'
    elif confidence >= 60:
        tier = 'Medium'
    elif confidence >= 55:
        tier = 'Low'
    else:
        tier = 'Toss-up'

    return {
        'predicted_winner': predicted_winner,
        'confidence': confidence,
        'tier': tier,
        'away_score': round(away_score, 4),
        'home_score': round(home_score, 4),
        'away_pct': round(away_pct * 100, 1),
        'home_pct': round(home_pct * 100, 1),
        'factors': factors
    }


# =============================================================================
# MAIN EXECUTION
# =============================================================================

def generate_all_predictions():
    """Generate predictions for all scheduled games"""

    print("Loading data...")
    games = load_game_results()
    original_rankings = load_team_rankings()
    schedule = load_schedule()

    print(f"  Loaded {len(games)} game results")
    print(f"  Loaded {len(original_rankings)} team rankings (raw)")
    print(f"  Loaded {len(schedule['dates'])} game dates")

    # Load player roster and calculate age-adjusted rankings
    print("\nApplying age normalization...")
    roster = load_player_roster()
    print(f"  Loaded rosters for {len(roster)} teams")

    rankings = calculate_age_adjusted_rankings(roster, original_rankings)
    print(f"  Calculated age-adjusted rankings for {len(rankings)} teams")

    # Show some examples of age adjustment impact
    young_teams = [(t, r['avg_age_multiplier']) for t, r in rankings.items() if r['avg_age_multiplier'] > 1.10]
    young_teams.sort(key=lambda x: x[1], reverse=True)
    if young_teams[:3]:
        print(f"  Youngest rosters (biggest boost): {', '.join([t for t,_ in young_teams[:3]])}")

    print("\nCalculating team stats...")
    team_stats = calculate_team_stats(games)
    print(f"  Calculated stats for {len(team_stats)} teams")

    # Load MHR rankings (mathematical ELO ratings for all 60 teams)
    print("\nLoading MyHockeyRankings...")
    mhr_rankings = load_mhr_rankings()
    if mhr_rankings:
        print(f"  Loaded MHR rankings for {len(mhr_rankings)} teams")
        top_mhr = sorted(mhr_rankings.items(), key=lambda x: x[1]['rank'])[:5]
        print(f"  MHR Top 5: {', '.join([t.title() for t,_ in top_mhr])}")
    else:
        print("  No MHR rankings available")

    # Load USHR expert rankings (captures intangibles: coaching, goaltending, chemistry)
    print("\nLoading USHR expert rankings...")
    expert_rankings = load_expert_rankings()
    if expert_rankings:
        print(f"  Loaded USHR expert rankings for {len(expert_rankings)} teams")
        top_expert = sorted(expert_rankings.items(), key=lambda x: x[1]['rank'])[:5]
        print(f"  USHR Top 5: {', '.join([t.title() for t,_ in top_expert])}")
    else:
        print("  No USHR expert rankings available")

    # Load JSPR rankings (official NEPSIHA power rankings - highest weight)
    print("\nLoading JSPR rankings...")
    jspr_rankings = load_jspr_rankings()
    if jspr_rankings:
        print(f"  Loaded JSPR rankings for {len(jspr_rankings)} teams")
        top_jspr = sorted(jspr_rankings.items(), key=lambda x: x[1]['rank'])[:5]
        print(f"  JSPR Top 5: {', '.join([t.title() for t,_ in top_jspr])}")
    else:
        print("  No JSPR rankings available")

    # Calculate performance rankings from game results (our own ELO-style ranking)
    print("\nCalculating performance rankings...")
    performance_rankings = calculate_performance_rankings(games)
    if performance_rankings:
        print(f"  Calculated performance rankings for {len(performance_rankings)} teams")
        top_perf = sorted(performance_rankings.items(), key=lambda x: x[1]['rank'])[:5]
        print(f"  Performance Top 5: {', '.join([t.title() for t,_ in top_perf])}")
    else:
        print("  No performance rankings available")

    # Load NEHJ expert rankings (Evan Marinofsky's eye test)
    print("\nLoading NEHJ expert rankings...")
    nehj_rankings = load_nehj_expert_rankings()
    if nehj_rankings:
        print(f"  Loaded NEHJ expert rankings for {len(nehj_rankings)} teams")
        top_nehj = sorted(nehj_rankings.items(), key=lambda x: x[1]['rank'])[:5]
        print(f"  NEHJ Top 5: {', '.join([t.title() for t,_ in top_nehj])}")
    else:
        print("  No NEHJ expert rankings available")

    print("\nGenerating predictions...")
    predictions = {}

    for date, date_games in schedule['dates'].items():
        predictions[date] = []

        for game in date_games:
            away_team = game['awayTeam']
            home_team = game['homeTeam']

            prediction = predict_game(away_team, home_team, rankings, team_stats, games, expert_rankings, mhr_rankings, jspr_rankings, performance_rankings, nehj_rankings)

            predictions[date].append({
                'gameId': game['gameId'],
                'away': away_team,
                'home': home_team,
                'time': game['time'],
                'venue': game.get('location', ''),
                'prediction': prediction
            })

    total_games = sum(len(g) for g in predictions.values())
    print(f"  Generated {total_games} predictions")

    return predictions


def save_predictions(predictions, filepath='nepsac_predictions.json'):
    """Save predictions to JSON file"""
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(predictions, f, indent=2)
    print(f"\nSaved predictions to {filepath}")


def print_sample_predictions(predictions, num_samples=10):
    """Print sample predictions for review"""
    print("\n" + "=" * 70)
    print("SAMPLE PREDICTIONS (Ace & Scouty's Picks)")
    print("=" * 70)

    count = 0
    for date, games in sorted(predictions.items()):
        if count >= num_samples:
            break

        for game in games:
            if count >= num_samples:
                break

            pred = game['prediction']
            winner = pred['predicted_winner']
            conf = pred['confidence']
            tier = pred['tier']

            # Determine which team won
            winner_is_home = normalize_team_name(winner) == normalize_team_name(game['home'])

            print(f"\n{date} - {game['time']}")
            print(f"  {game['away']} @ {game['home']}")
            print(f"  >>> Prediction: {winner.upper()} ({conf}% - {tier})")
            print(f"  Score: Away {pred['away_pct']}% vs Home {pred['home_pct']}%")

            # Show key factors
            factors = pred['factors']
            jspr = factors.get('jspr_ranking', {'away': 'NR', 'home': 'NR', 'away_rpi': 0.5, 'home_rpi': 0.5})
            nehj = factors.get('nehj_expert', {'away': 'NR', 'home': 'NR'})
            perf = factors.get('performance_rank', {'away': 'N/A', 'home': 'N/A'})
            print(f"  JSPR: Away {jspr['away']} vs Home {jspr['home']} | NEHJ: Away {nehj['away']} vs Home {nehj['home']}")
            print(f"  Perf: Away {perf['away']} vs Home {perf['home']}")
            print(f"  Form (L5): Away {factors['recent_form']['away']} vs Home {factors['recent_form']['home']}")

            count += 1


if __name__ == '__main__':
    # Generate predictions
    predictions = generate_all_predictions()

    # Save to file
    save_predictions(predictions)

    # Print samples
    print_sample_predictions(predictions, num_samples=10)

    # Summary stats
    print("\n" + "=" * 70)
    print("PREDICTION SUMMARY")
    print("=" * 70)

    all_preds = [g['prediction'] for games in predictions.values() for g in games]

    tier_counts = defaultdict(int)
    for pred in all_preds:
        tier_counts[pred['tier']] += 1

    print(f"\nTotal predictions: {len(all_preds)}")
    print("\nBy confidence tier:")
    for tier in ['Very High', 'High', 'Medium', 'Low', 'Toss-up']:
        count = tier_counts.get(tier, 0)
        pct = count / len(all_preds) * 100 if all_preds else 0
        print(f"  {tier}: {count} ({pct:.1f}%)")

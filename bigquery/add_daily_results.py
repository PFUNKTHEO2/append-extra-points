"""
Add Daily Game Results and Box Scores
Copy/paste friendly format for quick daily updates.

Usage:
  python add_daily_results.py                    # Interactive paste mode
  python add_daily_results.py --file results.txt # From file
  python add_daily_results.py --date 2026-01-28  # Specific date (optional)

Format:
  DATE: 2026-01-28

  Salisbury 6 - Kent 2
    J. Smith 2G 1A
    M. Johnson 1G 2A
    GK: D. Brown 28sv W

  Taft 3 - Canterbury 1
    A. Lee 1G 1A
    GK: C. Davis 22sv W
"""

import os
import re
import sys
import argparse
from datetime import datetime, date
from google.cloud import bigquery
from supabase import create_client, Client

# BigQuery client
bq_client = bigquery.Client(project='prodigy-ranking')

# Supabase client
SUPABASE_URL = os.environ.get('SUPABASE_URL', 'https://xqkwvywcxmnfimkubtyo.supabase.co')
SUPABASE_KEY = os.environ.get('SUPABASE_SERVICE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhxa3d2eXdjeG1uZmlta3VidHlvIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTcxOTQzNTU2NywiZXhwIjoyMDM1MDExNTY3fQ.I2u4shTCxEt-1nJCNZKcl1DV91flxB5KrJ4NDcl_hWw')
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Team name aliases for fuzzy matching
# Maps input names to BigQuery team_id format (uses short IDs like 'salisbury', 'groton', 'bbn')
TEAM_ALIASES = {
    # Main NEPSAC teams - map to actual BigQuery team_id
    'salisbury': 'salisbury',
    'salisbury school': 'salisbury',
    'kent': 'kent',
    'kent school': 'kent',
    'taft': 'taft',
    'taft school': 'taft',
    'avon': 'avon-old-farms',
    'avon old farms': 'avon-old-farms',
    'choate': 'choate',
    'choate rosemary hall': 'choate',
    'hotchkiss': 'hotchkiss',
    'the hotchkiss school': 'hotchkiss',
    'hotchkiss school': 'hotchkiss',
    'canterbury': 'canterbury',
    'canterbury school': 'canterbury',
    'berkshire': 'berkshire',
    'berkshire school': 'berkshire',
    'loomis': 'loomis',
    'loomis chaffee': 'loomis',
    'westminster': 'westminster',
    'westminster school': 'westminster',
    'trinity-pawling': 'trinity-pawling',
    'trinity pawling': 'trinity-pawling',
    'millbrook': 'millbrook',
    'millbrook school': 'millbrook',
    'pomfret': 'pomfret',
    'pomfret school': 'pomfret',
    'gunnery': 'frederick-gunn',
    'the gunnery': 'frederick-gunn',
    'frederick gunn': 'frederick-gunn',
    'frederick gunn school': 'frederick-gunn',
    'gunn': 'frederick-gunn',
    'kingswood oxford': 'kingswood-oxford',
    'kingswood': 'kingswood-oxford',
    'williston': 'williston',
    'williston northampton': 'williston',
    'northampton': 'williston',
    'cushing': 'cushing',
    'cushing academy': 'cushing',
    'exeter': 'exeter',
    'phillips exeter': 'exeter',
    'andover': 'andover',
    'phillips andover': 'andover',
    'nobles': 'nobles',
    'noble': 'nobles',
    'noble greenough': 'nobles',
    'noble & greenough': 'nobles',
    'noble and greenough': 'nobles',
    'milton': 'milton',
    'milton academy': 'milton',
    'belmont hill': 'belmont-hill',
    'rivers': 'rivers',
    'rivers school': 'rivers',
    'st marks': 'st-marks',
    "st mark's": 'st-marks',
    'st. marks': 'st-marks',
    "st. mark's": 'st-marks',
    'middlesex': 'middlesex',
    'middlesex school': 'middlesex',
    'groton': 'groton',
    'groton school': 'groton',
    'lawrence': 'lawrence',
    'lawrence academy': 'lawrence',
    'governors': 'governors',
    "governor's": 'governors',
    'governors academy': 'governors',
    "the governor's academy": 'governors',
    'brooks': 'brooks',
    'brooks school': 'brooks',
    'st sebastians': 'st-sebastians',
    "st sebastian's": 'st-sebastians',
    "st. sebastian's": 'st-sebastians',
    "st. seb's": 'st-sebastians',
    "st seb's": 'st-sebastians',
    'bb&n': 'bbn',
    'bbn': 'bbn',
    'b.b.&n.': 'bbn',
    'buckingham browne nichols': 'bbn',
    'dexter': 'dexter',
    'dexter southfield': 'dexter',
    'thayer': 'thayer',
    'thayer academy': 'thayer',
    'tabor': 'tabor',
    'tabor academy': 'tabor',
    'st georges': 'st-georges',
    "st george's": 'st-georges',
    "st. george's": 'st-georges',
    'portsmouth abbey': 'portsmouth-abbey',
    'portsmouth': 'portsmouth-abbey',
    'roxbury latin': 'roxbury-latin',
    'roxbury': 'roxbury-latin',
    'pingree': 'pingree',
    'pingree school': 'pingree',
    'st pauls': 'st-pauls',
    "st paul's": 'st-pauls',
    "st. paul's": 'st-pauls',
    'holderness': 'holderness',
    'holderness school': 'holderness',
    'proctor': 'proctor',
    'proctor academy': 'proctor',
    'new hampton': 'new-hampton',
    'new hampton school': 'new-hampton',
    'tilton': 'tilton',
    'tilton school': 'tilton',
    'brewster': 'brewster',
    'brewster academy': 'brewster',
    'kua': 'kimball-union',
    'kimball union': 'kimball-union',
    'kimball union academy': 'kimball-union',
    'vermont academy': 'vermont-academy',
    'vermont': 'vermont-academy',
    'nmh': 'nmh',
    'northfield mount hermon': 'nmh',
    'deerfield': 'deerfield',
    'deerfield academy': 'deerfield',
    'winchendon': 'winchendon',
    'winchendon school': 'winchendon',
    'kents hill': 'kents-hill',
    'kents hill school': 'kents-hill',
    'hebron': 'hebron',
    'hebron academy': 'hebron',
    'hoosac': 'hoosac',
    'hoosac school': 'hoosac',
    'brunswick': 'brunswick',
    'brunswick school': 'brunswick',
    'st lukes': 'st-lukes',
    "st luke's": 'st-lukes',
    "st. luke's": 'st-lukes',
    'berwick': 'berwick',
    'berwick academy': 'berwick',
    'austin prep': 'austin-prep',
    'austin preparatory': 'austin-prep',
    'worcester': 'worcester',
    'worcester academy': 'worcester',
    'wilbraham': 'wilbraham-monson',
    'wilbraham monson': 'wilbraham-monson',
    'wilbraham & monson': 'wilbraham-monson',
    'albany': 'albany-academy',
    'albany academy': 'albany-academy',
    'north yarmouth': 'north-yarmouth',
    'north yarmouth academy': 'north-yarmouth',
    'nya': 'north-yarmouth',
}


def normalize_team_name(name):
    """Convert team name to team_id"""
    name_lower = name.lower().strip()

    # Check aliases first
    if name_lower in TEAM_ALIASES:
        return TEAM_ALIASES[name_lower]

    # Try to construct team_id from name
    team_id = name_lower.replace(' ', '-').replace("'", '').replace('.', '')
    return team_id


def parse_results_text(text, default_date=None):
    """Parse the copy/paste format into structured data"""
    games = []
    current_game = None
    current_date = default_date or date.today().isoformat()

    lines = text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for date line
        date_match = re.match(r'^DATE:\s*(\d{4}-\d{2}-\d{2})', line, re.IGNORECASE)
        if date_match:
            current_date = date_match.group(1)
            continue

        # Check for game score line: "Team1 # - Team2 #" or "Team1 #, Team2 #"
        score_match = re.match(r'^(.+?)\s+(\d+)\s*[-,]\s*(.+?)\s+(\d+)\s*$', line)
        if score_match:
            # Save previous game if exists
            if current_game:
                games.append(current_game)

            away_team = score_match.group(1).strip()
            away_score = int(score_match.group(2))
            home_team = score_match.group(3).strip()
            home_score = int(score_match.group(4))

            current_game = {
                'date': current_date,
                'away_team': away_team,
                'away_team_id': normalize_team_name(away_team),
                'away_score': away_score,
                'home_team': home_team,
                'home_team_id': normalize_team_name(home_team),
                'home_score': home_score,
                'performers': []
            }
            continue

        # Check for goalie line: "GK: Name #sv W/L/T" or "G: Name #sv W"
        goalie_match = re.match(r'^(?:GK|G|Goalie):\s*(.+?)\s+(\d+)\s*(?:sv|saves?)(?:\s+(W|L|T|OT|SO|WIN|LOSS|TIE|OTL))?', line, re.IGNORECASE)
        if goalie_match and current_game:
            name = goalie_match.group(1).strip()
            saves = int(goalie_match.group(2))
            result = goalie_match.group(3)

            # Determine win/loss/tie
            is_win = None
            is_loss = None
            is_tie = None
            if result:
                result = result.upper()
                if result in ['W', 'WIN']:
                    is_win = True
                elif result in ['L', 'LOSS']:
                    is_loss = True
                elif result in ['T', 'TIE']:
                    is_tie = True
                elif result in ['OT', 'OTL']:
                    is_loss = True  # OT loss

            # Check for shutout
            is_shutout = 'SO' in line.upper() or 'shutout' in line.lower()

            current_game['performers'].append({
                'name': name,
                'position': 'G',
                'goals': 0,
                'assists': 0,
                'saves': saves,
                'is_win': is_win,
                'is_loss': is_loss,
                'is_tie': is_tie,
                'is_shutout': is_shutout
            })
            continue

        # Check for skater line: "Name #G #A" or "Name #G" or "Name 1A"
        skater_match = re.match(r'^(.+?)\s+(?:(\d+)\s*G)?(?:\s*(\d+)\s*A)?(?:\s*(\d+)\s*G)?(?:\s*(\d+)\s*A)?\s*$', line, re.IGNORECASE)
        if skater_match and current_game:
            name = skater_match.group(1).strip()

            # Skip if name looks like a header or invalid
            if name.lower() in ['scorers', 'scoring', 'goals', 'assists', 'performers', 'stars']:
                continue

            # Extract goals and assists from various positions
            goals = 0
            assists = 0

            # Look for patterns like "2G", "1A", "2G 1A", etc.
            g_match = re.search(r'(\d+)\s*G', line, re.IGNORECASE)
            a_match = re.search(r'(\d+)\s*A', line, re.IGNORECASE)

            if g_match:
                goals = int(g_match.group(1))
            if a_match:
                assists = int(a_match.group(1))

            # Only add if they have stats
            if goals > 0 or assists > 0:
                # Clean up name (remove the stats part)
                name = re.sub(r'\s*\d+\s*[GA].*$', '', name, flags=re.IGNORECASE).strip()

                current_game['performers'].append({
                    'name': name,
                    'position': 'F',  # Default to forward, could be D
                    'goals': goals,
                    'assists': assists,
                    'saves': None,
                    'is_win': None,
                    'is_loss': None,
                    'is_tie': None,
                    'is_shutout': False
                })

    # Don't forget the last game
    if current_game:
        games.append(current_game)

    return games


def find_game_in_schedule(game_date, away_team_id, home_team_id):
    """Find matching game in BigQuery schedule"""
    # Simplify team IDs for matching (remove -school, -academy suffixes)
    away_simple = away_team_id.replace('-school', '').replace('-academy', '').replace('phillips-', '').replace('the-', '')
    home_simple = home_team_id.replace('-school', '').replace('-academy', '').replace('phillips-', '').replace('the-', '')

    # Also create very short versions
    away_short = away_simple.split('-')[0]  # First word only
    home_short = home_simple.split('-')[0]

    query = f"""
    SELECT game_id, away_team_id, home_team_id, predicted_winner_id, prediction_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE game_date = '{game_date}'
      AND (
        -- Exact match
        (away_team_id = '{away_team_id}' AND home_team_id = '{home_team_id}')
        -- Simplified match (without -school/-academy)
        OR (away_team_id = '{away_simple}' AND home_team_id = '{home_simple}')
        -- Partial match
        OR (away_team_id LIKE '{away_simple}%' AND home_team_id LIKE '{home_simple}%')
        OR (away_team_id LIKE '%{away_short}%' AND home_team_id LIKE '%{home_short}%')
      )
    LIMIT 1
    """

    try:
        rows = list(bq_client.query(query).result())
        if rows:
            return {
                'game_id': rows[0].game_id,
                'away_team_id': rows[0].away_team_id,
                'home_team_id': rows[0].home_team_id,
                'predicted_winner_id': rows[0].predicted_winner_id,
                'prediction_confidence': rows[0].prediction_confidence
            }
    except Exception as e:
        print(f"  [WARN] Error finding game: {e}")

    return None


def update_bigquery_score(game_id, away_score, home_score):
    """Update game score in BigQuery"""
    # Scores and updated_at are STRING type in the table
    from datetime import datetime
    now_str = datetime.now().isoformat()

    query = f"""
    UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule`
    SET status = 'final',
        away_score = '{away_score}',
        home_score = '{home_score}',
        updated_at = '{now_str}'
    WHERE game_id = '{game_id}'
    """

    bq_client.query(query).result()


def add_performers_to_bigquery(game_id, game_date, performers, team_id):
    """Add performers to BigQuery"""
    if not performers:
        return

    # Delete existing performers for this game/team first
    delete_query = f"""
    DELETE FROM `prodigy-ranking.algorithm_core.nepsac_game_performers`
    WHERE game_id = '{game_id}' AND team_id = '{team_id}'
    """

    try:
        bq_client.query(delete_query).result()
    except Exception:
        pass  # Table might not exist or no rows to delete

    # Build insert values
    values = []
    for i, p in enumerate(performers):
        performer_id = f"{game_id}_{team_id}_{i+1}"
        goals = p.get('goals', 0) or 0
        assists = p.get('assists', 0) or 0
        points = goals + assists
        saves = p.get('saves')
        is_win = p.get('is_win')
        is_shutout = p.get('is_shutout', False)

        values.append(f"""(
            '{performer_id}',
            '{game_id}',
            '{game_date}',
            NULL,
            '{p["name"].replace("'", "''")}',
            '{team_id}',
            '{p.get("position", "F")}',
            {goals},
            {assists},
            {points},
            NULL, NULL, NULL,
            {saves if saves else 'NULL'},
            NULL, NULL, NULL,
            {str(is_shutout).upper()},
            {str(is_win).upper() if is_win is not None else 'NULL'},
            {'TRUE' if p.get('is_loss') else 'NULL'},
            NULL,
            FALSE,
            NULL,
            'manual',
            NULL,
            CURRENT_TIMESTAMP(),
            CURRENT_TIMESTAMP()
        )""")

    insert_query = f"""
    INSERT INTO `prodigy-ranking.algorithm_core.nepsac_game_performers` (
        performer_id, game_id, game_date, player_id, roster_name, team_id, position,
        goals, assists, points, plus_minus, pim, shots,
        saves, goals_against, shots_faced, save_pct, is_shutout, is_win, is_loss, is_otl,
        is_star_of_game, star_rank, source, notes, created_at, updated_at
    ) VALUES {', '.join(values)}
    """

    bq_client.query(insert_query).result()


def sync_game_to_supabase(game_id, game_date, away_team_id, home_team_id,
                          away_score, home_score, predicted_winner_id, prediction_confidence):
    """Sync game result to Supabase"""

    # Determine actual winner
    if away_score > home_score:
        actual_winner_id = away_team_id
        is_tie = False
    elif home_score > away_score:
        actual_winner_id = home_team_id
        is_tie = False
    else:
        actual_winner_id = None
        is_tie = True

    # Check prediction
    if is_tie:
        prediction_correct = None
    elif predicted_winner_id == actual_winner_id:
        prediction_correct = True
    else:
        prediction_correct = False

    # Map team IDs for Supabase (they use shorter IDs)
    def shorten_team_id(tid):
        """Convert BigQuery team_id to Supabase format"""
        if not tid:
            return None
        # Remove common suffixes
        short = tid.replace('-school', '').replace('-academy', '')
        short = short.replace('phillips-', '').replace('the-', '')
        return short

    game_data = {
        "game_id": game_id,
        "season": "2025-26",
        "game_date": game_date,
        "away_team_id": shorten_team_id(away_team_id),
        "home_team_id": shorten_team_id(home_team_id),
        "status": "final",
        "away_score": away_score,
        "home_score": home_score,
        "predicted_winner_id": shorten_team_id(predicted_winner_id),
        "prediction_confidence": prediction_confidence,
        "actual_winner_id": shorten_team_id(actual_winner_id),
        "is_tie": is_tie,
        "prediction_correct": prediction_correct,
    }

    try:
        supabase.table('nepsac_games').upsert(game_data, on_conflict='game_id').execute()
        return prediction_correct, is_tie
    except Exception as e:
        print(f"  [WARN] Supabase sync error: {e}")
        return prediction_correct, is_tie


def update_supabase_summaries(game_date):
    """Update daily and overall summaries in Supabase"""
    try:
        # Daily summary
        result = supabase.table('nepsac_games').select('*').eq('game_date', game_date).execute()
        games = result.data

        if games:
            correct = sum(1 for g in games if g.get('prediction_correct') == True)
            incorrect = sum(1 for g in games if g.get('prediction_correct') == False)
            ties = sum(1 for g in games if g.get('is_tie') == True)
            total = correct + incorrect
            accuracy = round(100 * correct / total, 1) if total > 0 else None

            summary = {
                "game_date": game_date,
                "total_games": len(games),
                "games_completed": len([g for g in games if g['status'] == 'final']),
                "correct_predictions": correct,
                "incorrect_predictions": incorrect,
                "ties": ties,
                "accuracy": accuracy
            }

            supabase.table('nepsac_daily_summary').upsert(summary, on_conflict='game_date').execute()

        # Overall stats
        result = supabase.table('nepsac_games').select('*').eq('status', 'final').execute()
        all_games = result.data

        correct = sum(1 for g in all_games if g.get('prediction_correct') == True)
        incorrect = sum(1 for g in all_games if g.get('prediction_correct') == False)
        ties = sum(1 for g in all_games if g.get('is_tie') == True)
        total = correct + incorrect
        accuracy = round(100 * correct / total, 1) if total > 0 else None

        stats = {
            "season": "2025-26",
            "total_predictions": len(all_games),
            "correct_predictions": correct,
            "incorrect_predictions": incorrect,
            "ties": ties,
            "overall_accuracy": accuracy,
        }

        supabase.table('nepsac_overall_stats').upsert(stats, on_conflict='season').execute()

        return correct, incorrect, ties, accuracy

    except Exception as e:
        print(f"  [WARN] Summary update error: {e}")
        return None, None, None, None


def process_games(games):
    """Process parsed games - update BigQuery and Supabase"""
    results = {'updated': 0, 'not_found': 0, 'correct': 0, 'incorrect': 0, 'ties': 0}
    dates_processed = set()

    print(f"\nProcessing {len(games)} games...")
    print("=" * 60)

    for game in games:
        game_date = game['date']
        dates_processed.add(game_date)

        print(f"\n{game['away_team']} {game['away_score']} - {game['home_team']} {game['home_score']}")

        # Find in schedule
        schedule_game = find_game_in_schedule(
            game_date, game['away_team_id'], game['home_team_id']
        )

        if not schedule_game:
            print(f"  [NOT FOUND] Could not match in schedule")
            print(f"    Tried: {game['away_team_id']} @ {game['home_team_id']} on {game_date}")
            results['not_found'] += 1
            continue

        game_id = schedule_game['game_id']

        # Update BigQuery score
        update_bigquery_score(game_id, game['away_score'], game['home_score'])
        print(f"  [BQ] Updated score")

        # Add performers to BigQuery
        away_performers = [p for p in game['performers'] if p['name']]  # Filter empty
        if away_performers:
            # For now, assume performers listed after team1 score belong to team1
            # In practice, we might need team indicators
            add_performers_to_bigquery(
                game_id, game_date, away_performers, schedule_game['away_team_id']
            )
            print(f"  [BQ] Added {len(away_performers)} performers")

        # Sync to Supabase
        pred_correct, is_tie = sync_game_to_supabase(
            game_id, game_date,
            schedule_game['away_team_id'], schedule_game['home_team_id'],
            game['away_score'], game['home_score'],
            schedule_game['predicted_winner_id'], schedule_game['prediction_confidence']
        )

        # Track results
        results['updated'] += 1
        if is_tie:
            results['ties'] += 1
            status = "TIE"
        elif pred_correct:
            results['correct'] += 1
            status = "CORRECT"
        else:
            results['incorrect'] += 1
            status = "WRONG"

        print(f"  [SUPABASE] Synced - Prediction: {status}")

    # Update summaries for all dates
    print("\n" + "=" * 60)
    print("Updating summaries...")

    for d in dates_processed:
        correct, incorrect, ties, accuracy = update_supabase_summaries(d)
        if accuracy is not None:
            print(f"  {d}: {correct}-{incorrect}-{ties} ({accuracy}%)")

    return results


def interactive_mode(default_date=None):
    """Interactive paste mode"""
    print("=" * 60)
    print("NEPSAC DAILY RESULTS ENTRY")
    print("=" * 60)
    print("\nPaste your results below. Format:")
    print("  DATE: 2026-01-28")
    print("  ")
    print("  Salisbury 6 - Kent 2")
    print("    J. Smith 2G 1A")
    print("    M. Johnson 1G")
    print("    GK: D. Brown 28sv W")
    print("")
    print("Press Enter twice (blank line) when done, or Ctrl+C to cancel.")
    print("-" * 60)

    lines = []
    blank_count = 0

    try:
        while True:
            line = input()
            if line == "":
                blank_count += 1
                if blank_count >= 2:
                    break
                lines.append(line)
            else:
                blank_count = 0
                lines.append(line)
    except EOFError:
        pass
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        return

    text = "\n".join(lines)

    if not text.strip():
        print("No input provided.")
        return

    # Parse and process
    games = parse_results_text(text, default_date)

    if not games:
        print("Could not parse any games from input.")
        return

    results = process_games(games)

    # Print summary
    print("\n" + "=" * 60)
    print("SESSION SUMMARY")
    print("=" * 60)
    print(f"Games updated:   {results['updated']}")
    print(f"Not found:       {results['not_found']}")
    print(f"Correct:         {results['correct']}")
    print(f"Incorrect:       {results['incorrect']}")
    print(f"Ties:            {results['ties']}")

    if results['updated'] > 0:
        decided = results['correct'] + results['incorrect']
        if decided > 0:
            accuracy = round(100 * results['correct'] / decided, 1)
            print(f"\nSession accuracy: {accuracy}%")


def file_mode(filepath, default_date=None):
    """Load from file"""
    print(f"Loading from {filepath}...")

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    games = parse_results_text(text, default_date)

    if not games:
        print("Could not parse any games from file.")
        return

    results = process_games(games)

    print(f"\nProcessed {results['updated']} games, {results['not_found']} not found")


def main():
    parser = argparse.ArgumentParser(description='Add NEPSAC daily results (scores + box scores)')
    parser.add_argument('--file', '-f', help='Load results from text file')
    parser.add_argument('--date', '-d', help='Default date if not specified in input (YYYY-MM-DD)')

    args = parser.parse_args()

    if args.file:
        file_mode(args.file, args.date)
    else:
        interactive_mode(args.date)


if __name__ == '__main__':
    main()

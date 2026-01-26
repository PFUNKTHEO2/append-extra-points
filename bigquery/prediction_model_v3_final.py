#!/usr/bin/env python3
"""
NEPSAC Prediction Model v3.0 - Final

Key insight: Balance TALENT (ProdigyPoints) with PERFORMANCE (W-L record)
- Teams like Kents Hill have high talent but poor record
- Teams like Winchendon have lower talent but better record
- Model must weight both factors

Factors:
1. ProdigyPoints (talent/potential)
2. Win Percentage (actual performance)
3. Home Ice Advantage
4. Recent Form (last 5 games if available)
"""

from google.cloud import bigquery
from collections import defaultdict

client = bigquery.Client(project='prodigy-ranking')

def load_team_data():
    """Load team rankings and standings."""
    # Rankings (talent)
    rankings_query = '''
    SELECT team_id, rank, avg_prodigy_points
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
    WHERE season = '2025-26'
    '''
    rankings = {}
    for row in client.query(rankings_query).result():
        rankings[row.team_id] = {
            'rank': row.rank or 50,
            'points': row.avg_prodigy_points or 1500
        }

    # Standings (performance)
    standings_query = '''
    SELECT team_id, wins, losses, ties, win_pct
    FROM `prodigy-ranking.algorithm_core.nepsac_standings`
    WHERE season = '2025-26'
    '''
    standings = {}
    for row in client.query(standings_query).result():
        standings[row.team_id] = {
            'wins': row.wins or 0,
            'losses': row.losses or 0,
            'ties': row.ties or 0,
            'win_pct': row.win_pct or 0.5
        }

    return rankings, standings

def load_completed_games():
    """Load completed games."""
    query = '''
    SELECT
        game_id, game_date, away_team_id, home_team_id,
        CAST(away_score AS INT64) as away_score,
        CAST(home_score AS INT64) as home_score,
        predicted_winner_id, prediction_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE season = '2025-26' AND status = 'final' AND away_score IS NOT NULL
    ORDER BY game_date ASC
    '''
    return [dict(row) for row in client.query(query).result()]

def load_scheduled_games(start_date, end_date):
    """Load scheduled games."""
    query = f'''
    SELECT
        game_id, game_date, day_of_week, away_team_id, home_team_id,
        predicted_winner_id, prediction_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE season = '2025-26'
        AND game_date >= '{start_date}'
        AND game_date <= '{end_date}'
        AND status = 'scheduled'
    ORDER BY game_date ASC
    '''
    return [dict(row) for row in client.query(query).result()]

class GameHistory:
    """Track recent games for a team."""
    def __init__(self):
        self.results = []  # List of 'W', 'L', 'T'

    def add(self, result):
        self.results.append(result)

    def recent_form(self, n=5):
        """Win pct in last n games."""
        recent = self.results[-n:] if self.results else []
        if not recent:
            return None  # No data
        wins = recent.count('W')
        ties = recent.count('T')
        return (wins + 0.5 * ties) / len(recent)

def build_history(games):
    """Build game history from completed games."""
    history = defaultdict(GameHistory)
    for g in games:
        away_result = 'W' if g['away_score'] > g['home_score'] else ('L' if g['away_score'] < g['home_score'] else 'T')
        home_result = 'W' if g['home_score'] > g['away_score'] else ('L' if g['home_score'] < g['away_score'] else 'T')
        history[g['away_team_id']].add(away_result)
        history[g['home_team_id']].add(home_result)
    return history

def predict_game(away_team, home_team, rankings, standings, history=None):
    """
    Predict game outcome.

    Model weights:
    - 40% ProdigyPoints (talent)
    - 35% Win Percentage (performance)
    - 15% Home Ice Advantage
    - 10% Recent Form (if available)
    """

    # Get team data
    away_rank = rankings.get(away_team, {'rank': 50, 'points': 1500})
    home_rank = rankings.get(home_team, {'rank': 50, 'points': 1500})
    away_stand = standings.get(away_team, {'win_pct': 0.5})
    home_stand = standings.get(home_team, {'win_pct': 0.5})

    away_pts = away_rank['points'] or 1500
    home_pts = home_rank['points'] or 1500
    away_win_pct = away_stand['win_pct'] if away_stand['win_pct'] else 0.5
    home_win_pct = home_stand['win_pct'] if home_stand['win_pct'] else 0.5

    # === FACTOR 1: PRODIGY POINTS (40%) ===
    total_pts = away_pts + home_pts
    away_pts_score = away_pts / total_pts
    home_pts_score = home_pts / total_pts

    # === FACTOR 2: WIN PERCENTAGE (35%) ===
    # Normalize win_pct to be comparable
    total_win_pct = away_win_pct + home_win_pct
    if total_win_pct > 0:
        away_wp_score = away_win_pct / total_win_pct
        home_wp_score = home_win_pct / total_win_pct
    else:
        away_wp_score = 0.5
        home_wp_score = 0.5

    # === FACTOR 3: HOME ICE (15%) ===
    # Home team gets ~8% boost (based on 61% home win rate observed)
    away_home_score = 0.46
    home_home_score = 0.54

    # === FACTOR 4: RECENT FORM (10%) ===
    if history:
        away_hist = history.get(away_team)
        home_hist = history.get(home_team)
        away_form = away_hist.recent_form(5) if away_hist else None
        home_form = home_hist.recent_form(5) if home_hist else None

        if away_form is not None and home_form is not None:
            total_form = away_form + home_form
            if total_form > 0:
                away_form_score = away_form / total_form
                home_form_score = home_form / total_form
            else:
                away_form_score = 0.5
                home_form_score = 0.5
            form_weight = 0.10
        else:
            away_form_score = 0.5
            home_form_score = 0.5
            form_weight = 0.0
    else:
        away_form_score = 0.5
        home_form_score = 0.5
        form_weight = 0.0

    # Adjust weights if form not available
    pts_weight = 0.40 + (0.05 if form_weight == 0 else 0)
    wp_weight = 0.35 + (0.05 if form_weight == 0 else 0)
    home_weight = 0.15

    # === CALCULATE FINAL SCORES ===
    away_score = (
        away_pts_score * pts_weight +
        away_wp_score * wp_weight +
        away_home_score * home_weight +
        away_form_score * form_weight
    )

    home_score = (
        home_pts_score * pts_weight +
        home_wp_score * wp_weight +
        home_home_score * home_weight +
        home_form_score * form_weight
    )

    # Normalize to probabilities
    total = away_score + home_score
    away_prob = away_score / total
    home_prob = home_score / total

    # Determine winner
    if home_prob > away_prob:
        winner = home_team
        confidence = int(min(home_prob * 100, 92))
    else:
        winner = away_team
        confidence = int(min(away_prob * 100, 92))

    confidence = max(51, confidence)

    # Tier
    if confidence >= 70:
        tier = 'High'
    elif confidence >= 60:
        tier = 'Medium'
    elif confidence >= 54:
        tier = 'Low'
    else:
        tier = 'Toss-up'

    return {
        'winner': winner,
        'confidence': confidence,
        'tier': tier,
        'away_prob': round(away_prob * 100, 1),
        'home_prob': round(home_prob * 100, 1),
        'factors': {
            'pts': {'away': away_pts_score, 'home': home_pts_score},
            'win_pct': {'away': away_wp_score, 'home': home_wp_score},
            'home_ice': {'away': away_home_score, 'home': home_home_score},
            'form': {'away': away_form_score, 'home': home_form_score}
        }
    }

def backtest():
    """Backtest the model."""
    rankings, standings = load_team_data()
    games = load_completed_games()
    history = build_history(games)

    # Test on all completed games
    old_correct = 0
    new_correct = 0
    total = 0

    print("=" * 70)
    print("BACKTEST: New Model vs Old Predictions")
    print("=" * 70)

    wrong = []

    for g in games:
        if g['away_score'] == g['home_score']:
            continue

        actual = g['away_team_id'] if g['away_score'] > g['home_score'] else g['home_team_id']

        # Old prediction
        if g['predicted_winner_id'] == actual:
            old_correct += 1

        # New prediction
        pred = predict_game(g['away_team_id'], g['home_team_id'], rankings, standings, history)
        if pred['winner'] == actual:
            new_correct += 1
        else:
            wrong.append({
                'matchup': f"{g['away_team_id']} @ {g['home_team_id']}",
                'score': f"{g['away_score']}-{g['home_score']}",
                'predicted': pred['winner'],
                'confidence': pred['confidence'],
                'actual': actual
            })

        total += 1

    old_acc = old_correct / total * 100
    new_acc = new_correct / total * 100

    print(f"\nOld Model: {old_correct}/{total} ({old_acc:.1f}%)")
    print(f"New Model: {new_correct}/{total} ({new_acc:.1f}%)")
    print(f"Improvement: {new_acc - old_acc:+.1f}%")

    print(f"\n--- Wrong Predictions ({len(wrong)}) ---")
    for w in wrong:
        print(f"  {w['matchup']} ({w['score']}): Predicted {w['predicted']} ({w['confidence']}%), Actual: {w['actual']}")

def generate_predictions(start_date, end_date, apply=False):
    """Generate predictions for upcoming games."""
    rankings, standings = load_team_data()
    completed = load_completed_games()
    scheduled = load_scheduled_games(start_date, end_date)
    history = build_history(completed)

    print(f"\n{'='*80}")
    print(f"PREDICTIONS: {start_date} to {end_date}")
    print(f"{'='*80}")

    predictions = []
    changed = 0

    for g in scheduled:
        pred = predict_game(g['away_team_id'], g['home_team_id'], rankings, standings, history)

        is_changed = pred['winner'] != g['predicted_winner_id']
        if is_changed:
            changed += 1

        predictions.append({
            'game_id': g['game_id'],
            'date': str(g['game_date']),
            'away': g['away_team_id'],
            'home': g['home_team_id'],
            'old_winner': g['predicted_winner_id'],
            'old_conf': g['prediction_confidence'],
            'new_winner': pred['winner'],
            'new_conf': pred['confidence'],
            'tier': pred['tier']
        })

        mark = "** CHANGED **" if is_changed else ""
        print(f"{g['game_date']} | {g['away_team_id']:25} @ {g['home_team_id']:25} | {pred['winner']} ({pred['confidence']}%) {mark}")

    print(f"\n{changed}/{len(predictions)} predictions changed")

    if apply:
        print("\nApplying to BigQuery...")
        for p in predictions:
            query = f'''
            UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule`
            SET predicted_winner_id = '{p['new_winner']}',
                prediction_confidence = {p['new_conf']},
                prediction_method = 'model_v3.0'
            WHERE game_id = '{p['game_id']}'
            '''
            client.query(query).result()
        print("Done!")

    return predictions

if __name__ == '__main__':
    import sys

    if '--backtest' in sys.argv:
        backtest()
    elif '--predict' in sys.argv:
        idx = sys.argv.index('--predict')
        start = sys.argv[idx + 1] if len(sys.argv) > idx + 1 else '2026-01-26'
        end = sys.argv[idx + 2] if len(sys.argv) > idx + 2 else '2026-02-01'
        apply = '--apply' in sys.argv
        generate_predictions(start, end, apply)
    else:
        print("Usage:")
        print("  python prediction_model_v3_final.py --backtest")
        print("  python prediction_model_v3_final.py --predict 2026-01-26 2026-02-01 [--apply]")

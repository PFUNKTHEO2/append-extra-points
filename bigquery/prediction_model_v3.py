#!/usr/bin/env python3
"""
NEPSAC Prediction Model v3.0

Key findings from data analysis:
- Home ice advantage: 61% win rate
- ProdigyPoints correlation: 61%
- Close games (rank diff < 5): Essentially coin flips
- Larger gaps (rank diff > 10): Rankings very predictive (70%)

Strategy:
1. Use ProdigyPoints as base (weighted by rank difference)
2. Apply home ice advantage (scaled by team's home record)
3. Add recent form ONLY for teams with 5+ games
4. Include momentum for hot/cold streaks
"""

from google.cloud import bigquery
from datetime import datetime
from collections import defaultdict

client = bigquery.Client(project='prodigy-ranking')

def load_team_rankings():
    """Load current team rankings."""
    query = '''
    SELECT team_id, rank, avg_prodigy_points, team_ovr
    FROM `prodigy-ranking.algorithm_core.nepsac_team_rankings`
    WHERE season = '2025-26'
    '''
    rankings = {}
    for row in client.query(query).result():
        rankings[row.team_id] = {
            'rank': row.rank or 50,
            'points': row.avg_prodigy_points or 1500,
            'ovr': row.team_ovr or 75
        }
    return rankings

def load_completed_games():
    """Load all completed games."""
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
    """Load scheduled games for prediction."""
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

class TeamHistory:
    """Track team's game history."""

    def __init__(self):
        self.games = []
        self.home_wins = 0
        self.home_games = 0
        self.away_wins = 0
        self.away_games = 0

    def add_game(self, goals_for, goals_against, is_home):
        result = 'W' if goals_for > goals_against else ('L' if goals_for < goals_against else 'T')
        self.games.append({'gf': goals_for, 'ga': goals_against, 'result': result, 'home': is_home})

        if is_home:
            self.home_games += 1
            if result == 'W':
                self.home_wins += 1
        else:
            self.away_games += 1
            if result == 'W':
                self.away_wins += 1

    def recent_form(self, n=5):
        """Win percentage in last n games."""
        recent = self.games[-n:] if self.games else []
        if not recent:
            return 0.5
        wins = sum(1 for g in recent if g['result'] == 'W')
        ties = sum(1 for g in recent if g['result'] == 'T')
        return (wins + 0.5 * ties) / len(recent)

    def goal_diff_per_game(self):
        """Average goal differential."""
        if not self.games:
            return 0
        return sum(g['gf'] - g['ga'] for g in self.games) / len(self.games)

    def streak(self):
        """Current win/loss streak (positive = wins, negative = losses)."""
        if not self.games:
            return 0
        streak = 0
        for g in reversed(self.games):
            if g['result'] == 'W':
                if streak >= 0:
                    streak += 1
                else:
                    break
            elif g['result'] == 'L':
                if streak <= 0:
                    streak -= 1
                else:
                    break
            else:
                break
        return streak

    def home_win_rate(self):
        if self.home_games == 0:
            return 0.5
        return self.home_wins / self.home_games

def build_team_history(games):
    """Build team history from completed games."""
    history = defaultdict(TeamHistory)
    for g in games:
        history[g['away_team_id']].add_game(g['away_score'], g['home_score'], is_home=False)
        history[g['home_team_id']].add_game(g['home_score'], g['away_score'], is_home=True)
    return history

def predict_game(away_team, home_team, rankings, history):
    """
    Predict game outcome using enhanced model.

    Returns: (winner_id, confidence, breakdown)
    """

    # Get team data
    away_data = rankings.get(away_team, {'rank': 50, 'points': 1500})
    home_data = rankings.get(home_team, {'rank': 50, 'points': 1500})
    away_hist = history.get(away_team, TeamHistory())
    home_hist = history.get(home_team, TeamHistory())

    away_pts = away_data['points'] or 1500
    home_pts = home_data['points'] or 1500
    away_rank = away_data['rank'] or 50
    home_rank = home_data['rank'] or 50

    rank_diff = abs(away_rank - home_rank)

    breakdown = {}

    # === FACTOR 1: BASE PRODIGY POINTS (40-60% weight depending on rank diff) ===
    # Higher weight when rank difference is larger (more predictive)
    if rank_diff >= 15:
        pts_weight = 0.55
    elif rank_diff >= 10:
        pts_weight = 0.50
    elif rank_diff >= 5:
        pts_weight = 0.45
    else:
        pts_weight = 0.40  # Close matchups, points less predictive

    total_pts = away_pts + home_pts
    away_pts_factor = away_pts / total_pts
    home_pts_factor = home_pts / total_pts
    breakdown['prodigy_points'] = {'away': away_pts_factor, 'home': home_pts_factor, 'weight': pts_weight}

    # === FACTOR 2: HOME ICE ADVANTAGE (15-25% weight) ===
    # Base: 61% home win rate observed
    # Adjust based on team's actual home performance
    base_home_adv = 0.08  # 8% boost

    if home_hist.home_games >= 3:
        # Adjust based on actual home performance
        home_wr = home_hist.home_win_rate()
        if home_wr > 0.7:
            home_adv = 0.12  # Strong home team
        elif home_wr > 0.5:
            home_adv = 0.08  # Average
        else:
            home_adv = 0.04  # Weak at home
    else:
        home_adv = base_home_adv

    away_home_factor = 0.5 - (home_adv / 2)
    home_home_factor = 0.5 + (home_adv / 2)
    home_weight = 0.20
    breakdown['home_ice'] = {'away': away_home_factor, 'home': home_home_factor, 'weight': home_weight}

    # === FACTOR 3: RECENT FORM (10-20% weight if enough games) ===
    away_games = len(away_hist.games)
    home_games = len(home_hist.games)

    if away_games >= 5 and home_games >= 5:
        away_form = away_hist.recent_form(5)
        home_form = home_hist.recent_form(5)
        form_weight = 0.15
    elif away_games >= 3 and home_games >= 3:
        away_form = away_hist.recent_form(3)
        home_form = home_hist.recent_form(3)
        form_weight = 0.10
    else:
        away_form = 0.5
        home_form = 0.5
        form_weight = 0.05

    breakdown['recent_form'] = {'away': away_form, 'home': home_form, 'weight': form_weight}

    # === FACTOR 4: GOAL DIFFERENTIAL (5-10% weight) ===
    if away_games >= 3 and home_games >= 3:
        away_gd = away_hist.goal_diff_per_game()
        home_gd = home_hist.goal_diff_per_game()
        # Normalize: -4 to +4 -> 0 to 1
        away_gd_norm = max(0, min(1, (away_gd + 4) / 8))
        home_gd_norm = max(0, min(1, (home_gd + 4) / 8))
        gd_weight = 0.10
    else:
        away_gd_norm = 0.5
        home_gd_norm = 0.5
        gd_weight = 0.05

    breakdown['goal_diff'] = {'away': away_gd_norm, 'home': home_gd_norm, 'weight': gd_weight}

    # === FACTOR 5: MOMENTUM/STREAK (5% weight) ===
    away_streak = away_hist.streak()
    home_streak = home_hist.streak()
    # Normalize: -4 to +4 -> 0 to 1
    away_momentum = max(0, min(1, (away_streak + 4) / 8))
    home_momentum = max(0, min(1, (home_streak + 4) / 8))
    momentum_weight = 0.05
    breakdown['momentum'] = {'away': away_momentum, 'home': home_momentum, 'weight': momentum_weight}

    # === CALCULATE FINAL SCORES ===
    # Normalize weights
    total_weight = pts_weight + home_weight + form_weight + gd_weight + momentum_weight

    away_score = (
        away_pts_factor * (pts_weight / total_weight) +
        away_home_factor * (home_weight / total_weight) +
        away_form * (form_weight / total_weight) +
        away_gd_norm * (gd_weight / total_weight) +
        away_momentum * (momentum_weight / total_weight)
    )

    home_score = (
        home_pts_factor * (pts_weight / total_weight) +
        home_home_factor * (home_weight / total_weight) +
        home_form * (form_weight / total_weight) +
        home_gd_norm * (gd_weight / total_weight) +
        home_momentum * (momentum_weight / total_weight)
    )

    # Convert to probability
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

    # Floor confidence at 51 for decisive picks
    confidence = max(51, confidence)

    # Determine tier
    if confidence >= 72:
        tier = 'High'
    elif confidence >= 60:
        tier = 'Medium'
    elif confidence >= 54:
        tier = 'Low'
    else:
        tier = 'Toss-up'

    return winner, confidence, tier, breakdown

def backtest():
    """Run backtest comparing old vs new model."""
    rankings = load_team_rankings()
    games = load_completed_games()

    # Progressive backtest
    history = defaultdict(TeamHistory)

    old_correct = 0
    old_total = 0
    new_correct = 0
    new_total = 0

    results = []

    for i, g in enumerate(games):
        away = g['away_team_id']
        home = g['home_team_id']
        away_score = g['away_score']
        home_score = g['home_score']

        # Skip ties
        if away_score == home_score:
            history[away].add_game(away_score, home_score, is_home=False)
            history[home].add_game(home_score, away_score, is_home=True)
            continue

        actual_winner = away if away_score > home_score else home

        # Old model
        if g['predicted_winner_id']:
            old_total += 1
            if g['predicted_winner_id'] == actual_winner:
                old_correct += 1

        # New model (only predict after 5 games in the season)
        if i >= 5:
            new_winner, conf, tier, breakdown = predict_game(away, home, rankings, history)
            new_total += 1
            is_correct = new_winner == actual_winner
            if is_correct:
                new_correct += 1

            results.append({
                'matchup': f'{away} @ {home}',
                'score': f'{away_score}-{home_score}',
                'predicted': new_winner,
                'actual': actual_winner,
                'confidence': conf,
                'correct': is_correct
            })

        # Update history
        history[away].add_game(away_score, home_score, is_home=False)
        history[home].add_game(home_score, away_score, is_home=True)

    old_acc = old_correct / old_total * 100 if old_total else 0
    new_acc = new_correct / new_total * 100 if new_total else 0

    print("=" * 60)
    print("BACKTEST RESULTS")
    print("=" * 60)
    print(f"\nOld Model (v2.1): {old_correct}/{old_total} ({old_acc:.1f}%)")
    print(f"New Model (v3.0): {new_correct}/{new_total} ({new_acc:.1f}%)")
    print(f"Improvement: {new_acc - old_acc:+.1f}%")

    # Show wrong predictions
    print("\n--- Wrong Predictions ---")
    for r in results:
        if not r['correct']:
            print(f"  {r['matchup']} ({r['score']}): Predicted {r['predicted']} ({r['confidence']}%), Actual: {r['actual']}")

    return results

def generate_predictions(start_date, end_date, apply=False):
    """Generate predictions for upcoming games."""
    rankings = load_team_rankings()
    completed = load_completed_games()
    scheduled = load_scheduled_games(start_date, end_date)
    history = build_team_history(completed)

    print(f"\nGenerating predictions for {start_date} to {end_date}")
    print(f"Using {len(completed)} completed games for history")
    print("=" * 80)

    predictions = []

    for g in scheduled:
        away = g['away_team_id']
        home = g['home_team_id']
        winner, conf, tier, breakdown = predict_game(away, home, rankings, history)

        old_winner = g['predicted_winner_id']
        old_conf = g['prediction_confidence']

        changed = "** CHANGED **" if winner != old_winner else ""

        predictions.append({
            'game_id': g['game_id'],
            'date': str(g['game_date']),
            'day': g.get('day_of_week', ''),
            'away': away,
            'home': home,
            'old_winner': old_winner,
            'old_conf': old_conf,
            'new_winner': winner,
            'new_conf': conf,
            'tier': tier,
            'changed': bool(changed)
        })

        print(f"{g['game_date']} | {away:25} @ {home:25} | {winner} ({conf}%) {tier:8} {changed}")

    changed_count = sum(1 for p in predictions if p['changed'])
    print(f"\n{changed_count}/{len(predictions)} predictions changed")

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
        print(f"Updated {len(predictions)} games")

    return predictions

if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--backtest':
        backtest()
    elif len(sys.argv) > 1 and sys.argv[1] == '--predict':
        start = sys.argv[2] if len(sys.argv) > 2 else '2026-01-26'
        end = sys.argv[3] if len(sys.argv) > 3 else '2026-02-01'
        apply = '--apply' in sys.argv
        generate_predictions(start, end, apply=apply)
    else:
        print("Usage:")
        print("  python prediction_model_v3.py --backtest")
        print("  python prediction_model_v3.py --predict [start_date] [end_date] [--apply]")

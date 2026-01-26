#!/usr/bin/env python3
"""
Enhanced NEPSAC Prediction Model v3.0

Incorporates past performance factors:
- Team rankings (ProdigyPoints)
- Recent form (last 5 games)
- Head-to-head history
- Goal differential
- Home/away performance
- Momentum/streaks

Target: 75%+ prediction accuracy
"""

from google.cloud import bigquery
from datetime import datetime, timedelta
from collections import defaultdict
import json

client = bigquery.Client(project='prodigy-ranking')

# =============================================================================
# DATA LOADING
# =============================================================================

def load_team_rankings():
    """Load current team rankings with ProdigyPoints."""
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
    """Load all completed games with scores."""
    query = '''
    SELECT
        game_id,
        game_date,
        away_team_id,
        home_team_id,
        CAST(away_score AS INT64) as away_score,
        CAST(home_score AS INT64) as home_score,
        predicted_winner_id,
        prediction_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE season = '2025-26'
        AND status = 'final'
        AND away_score IS NOT NULL
    ORDER BY game_date ASC
    '''
    games = []
    for row in client.query(query).result():
        games.append({
            'game_id': row.game_id,
            'date': str(row.game_date),
            'away_team': row.away_team_id,
            'home_team': row.home_team_id,
            'away_score': row.away_score,
            'home_score': row.home_score,
            'predicted_winner': row.predicted_winner_id,
            'confidence': row.prediction_confidence
        })
    return games

def load_scheduled_games(start_date, end_date):
    """Load scheduled games for prediction."""
    query = f'''
    SELECT
        game_id,
        game_date,
        away_team_id,
        home_team_id,
        predicted_winner_id,
        prediction_confidence
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule`
    WHERE season = '2025-26'
        AND game_date >= '{start_date}'
        AND game_date <= '{end_date}'
        AND status = 'scheduled'
    ORDER BY game_date ASC
    '''
    games = []
    for row in client.query(query).result():
        games.append({
            'game_id': row.game_id,
            'date': str(row.game_date),
            'away_team': row.away_team_id,
            'home_team': row.home_team_id,
            'current_prediction': row.predicted_winner_id,
            'current_confidence': row.prediction_confidence
        })
    return games

# =============================================================================
# FEATURE CALCULATION
# =============================================================================

class TeamStats:
    """Track cumulative team statistics."""

    def __init__(self):
        self.games = []  # List of game results
        self.home_record = {'wins': 0, 'losses': 0, 'ties': 0, 'gf': 0, 'ga': 0}
        self.away_record = {'wins': 0, 'losses': 0, 'ties': 0, 'gf': 0, 'ga': 0}
        self.h2h = defaultdict(lambda: {'wins': 0, 'losses': 0, 'ties': 0})

    def add_game(self, date, opponent, goals_for, goals_against, is_home):
        """Record a game result."""
        if goals_for > goals_against:
            result = 'W'
        elif goals_for < goals_against:
            result = 'L'
        else:
            result = 'T'

        self.games.append({
            'date': date,
            'opponent': opponent,
            'gf': goals_for,
            'ga': goals_against,
            'result': result,
            'is_home': is_home
        })

        # Update records
        record = self.home_record if is_home else self.away_record
        record['gf'] += goals_for
        record['ga'] += goals_against
        if result == 'W':
            record['wins'] += 1
            self.h2h[opponent]['wins'] += 1
        elif result == 'L':
            record['losses'] += 1
            self.h2h[opponent]['losses'] += 1
        else:
            record['ties'] += 1
            self.h2h[opponent]['ties'] += 1

    def get_recent_form(self, n=5):
        """Get last N games performance."""
        recent = self.games[-n:] if len(self.games) >= n else self.games
        if not recent:
            return {'win_pct': 0.5, 'goal_diff': 0, 'ppg': 0, 'games': 0}

        wins = sum(1 for g in recent if g['result'] == 'W')
        ties = sum(1 for g in recent if g['result'] == 'T')
        gf = sum(g['gf'] for g in recent)
        ga = sum(g['ga'] for g in recent)

        return {
            'win_pct': (wins + 0.5 * ties) / len(recent),
            'goal_diff': (gf - ga) / len(recent),
            'ppg': gf / len(recent),
            'games': len(recent)
        }

    def get_streak(self):
        """Get current win/loss streak."""
        if not self.games:
            return 0

        streak = 0
        last_result = self.games[-1]['result']

        for game in reversed(self.games):
            if game['result'] == last_result:
                if last_result == 'W':
                    streak += 1
                elif last_result == 'L':
                    streak -= 1
                else:
                    break  # Tie breaks streak
            else:
                break

        return streak

    def get_home_advantage(self):
        """Calculate home vs away performance differential."""
        home_games = self.home_record['wins'] + self.home_record['losses'] + self.home_record['ties']
        away_games = self.away_record['wins'] + self.away_record['losses'] + self.away_record['ties']

        if home_games == 0 or away_games == 0:
            return 0.03  # Default 3% home advantage

        home_pct = (self.home_record['wins'] + 0.5 * self.home_record['ties']) / home_games
        away_pct = (self.away_record['wins'] + 0.5 * self.away_record['ties']) / away_games

        return home_pct - away_pct

    def get_h2h_record(self, opponent):
        """Get head-to-head record vs specific opponent."""
        return self.h2h.get(opponent, {'wins': 0, 'losses': 0, 'ties': 0})

    def get_goal_differential(self):
        """Get overall goal differential per game."""
        total_games = len(self.games)
        if total_games == 0:
            return 0

        total_gf = sum(g['gf'] for g in self.games)
        total_ga = sum(g['ga'] for g in self.games)
        return (total_gf - total_ga) / total_games

def build_team_stats(games):
    """Build team statistics from game history."""
    team_stats = defaultdict(TeamStats)

    for game in games:
        away = game['away_team']
        home = game['home_team']
        away_score = game['away_score']
        home_score = game['home_score']
        date = game['date']

        team_stats[away].add_game(date, home, away_score, home_score, is_home=False)
        team_stats[home].add_game(date, away, home_score, away_score, is_home=True)

    return team_stats

# =============================================================================
# ENHANCED PREDICTION MODEL
# =============================================================================

class EnhancedPredictor:
    """Enhanced prediction model with multiple factors."""

    # Base weight configuration - adjusted dynamically based on data availability
    BASE_WEIGHTS = {
        'ranking': 0.50,      # Base team ranking (ProdigyPoints) - primary factor
        'recent_form': 0.20,  # Last 5 games performance
        'goal_diff': 0.10,    # Goal differential
        'home_adv': 0.08,     # Home ice advantage
        'h2h': 0.07,          # Head-to-head history
        'momentum': 0.05,     # Win/loss streaks
    }

    # Minimum games required for factor to be meaningful
    MIN_GAMES = {
        'recent_form': 3,
        'goal_diff': 3,
        'home_adv': 2,
        'h2h': 1,
        'momentum': 2,
    }

    def __init__(self, rankings, team_stats):
        self.rankings = rankings
        self.team_stats = team_stats

        # Calculate league averages for normalization
        all_points = [r['points'] for r in rankings.values() if r['points']]
        self.avg_points = sum(all_points) / len(all_points) if all_points else 1500
        self.max_points = max(all_points) if all_points else 3000
        self.min_points = min(all_points) if all_points else 500

    def normalize_points(self, points):
        """Normalize points to 0-1 scale."""
        if self.max_points == self.min_points:
            return 0.5
        return (points - self.min_points) / (self.max_points - self.min_points)

    def predict(self, away_team, home_team, verbose=False):
        """Generate prediction for a matchup."""

        # Get team data
        away_ranking = self.rankings.get(away_team, {'rank': 50, 'points': 1500, 'ovr': 75})
        home_ranking = self.rankings.get(home_team, {'rank': 50, 'points': 1500, 'ovr': 75})
        away_stats = self.team_stats.get(away_team, TeamStats())
        home_stats = self.team_stats.get(home_team, TeamStats())

        # Count games for adaptive weighting
        away_games = len(away_stats.games)
        home_games = len(home_stats.games)
        min_games = min(away_games, home_games)

        factors = {}
        active_weights = {}

        # 1. RANKING FACTOR (always active - primary factor)
        away_rank_score = self.normalize_points(away_ranking['points'])
        home_rank_score = self.normalize_points(home_ranking['points'])
        factors['ranking'] = {
            'away': away_rank_score,
            'home': home_rank_score
        }
        active_weights['ranking'] = self.BASE_WEIGHTS['ranking']

        # 2. RECENT FORM (last 5 games) - only if enough games
        away_form = away_stats.get_recent_form(5)
        home_form = home_stats.get_recent_form(5)
        if min_games >= self.MIN_GAMES['recent_form']:
            factors['recent_form'] = {
                'away': away_form['win_pct'],
                'home': home_form['win_pct']
            }
            active_weights['recent_form'] = self.BASE_WEIGHTS['recent_form']
        else:
            factors['recent_form'] = {'away': 0.5, 'home': 0.5}
            active_weights['recent_form'] = 0

        # 3. GOAL DIFFERENTIAL (normalized)
        if min_games >= self.MIN_GAMES['goal_diff']:
            away_gd = away_stats.get_goal_differential()
            home_gd = home_stats.get_goal_differential()
            # Normalize to 0-1 (assume -5 to +5 range)
            factors['goal_diff'] = {
                'away': max(0, min(1, (away_gd + 5) / 10)),
                'home': max(0, min(1, (home_gd + 5) / 10))
            }
            active_weights['goal_diff'] = self.BASE_WEIGHTS['goal_diff']
        else:
            factors['goal_diff'] = {'away': 0.5, 'home': 0.5}
            active_weights['goal_diff'] = 0

        # 4. HOME ADVANTAGE - only if we have home/away data
        home_home_games = home_stats.home_record['wins'] + home_stats.home_record['losses'] + home_stats.home_record['ties']
        if home_home_games >= self.MIN_GAMES['home_adv']:
            home_adv = home_stats.get_home_advantage()
            base_home_adv = 0.03  # 3% base
            actual_home_adv = base_home_adv + (home_adv * 0.5)
            factors['home_adv'] = {
                'away': 0,
                'home': max(0, min(0.15, actual_home_adv))
            }
            active_weights['home_adv'] = self.BASE_WEIGHTS['home_adv']
        else:
            # Default home advantage
            factors['home_adv'] = {'away': 0, 'home': 0.03}
            active_weights['home_adv'] = self.BASE_WEIGHTS['home_adv']

        # 5. HEAD-TO-HEAD - only if they've played
        h2h = away_stats.get_h2h_record(home_team)
        h2h_games = h2h['wins'] + h2h['losses'] + h2h['ties']
        if h2h_games >= self.MIN_GAMES['h2h']:
            away_h2h = (h2h['wins'] + 0.5 * h2h['ties']) / h2h_games
            home_h2h = 1 - away_h2h
            factors['h2h'] = {'away': away_h2h, 'home': home_h2h}
            active_weights['h2h'] = self.BASE_WEIGHTS['h2h']
        else:
            factors['h2h'] = {'away': 0.5, 'home': 0.5}
            active_weights['h2h'] = 0

        # 6. MOMENTUM (streak bonus)
        if min_games >= self.MIN_GAMES['momentum']:
            away_streak = away_stats.get_streak()
            home_streak = home_stats.get_streak()
            factors['momentum'] = {
                'away': max(0, min(1, (away_streak + 5) / 10)),
                'home': max(0, min(1, (home_streak + 5) / 10))
            }
            active_weights['momentum'] = self.BASE_WEIGHTS['momentum']
        else:
            factors['momentum'] = {'away': 0.5, 'home': 0.5}
            active_weights['momentum'] = 0

        # Redistribute inactive weights to ranking
        total_active = sum(active_weights.values())
        if total_active < 1.0:
            active_weights['ranking'] += (1.0 - total_active)

        # CALCULATE WEIGHTED SCORES
        away_score = 0
        home_score = 0

        for factor_name, weight in active_weights.items():
            factor_data = factors[factor_name]
            away_score += factor_data['away'] * weight
            home_score += factor_data['home'] * weight

        # Normalize to probabilities
        total = away_score + home_score
        if total == 0:
            away_prob = 0.5
            home_prob = 0.5
        else:
            away_prob = away_score / total
            home_prob = home_score / total

        # Determine winner and confidence
        if home_prob > away_prob:
            winner = home_team
            confidence = int(min(home_prob * 100, 95))
        else:
            winner = away_team
            confidence = int(min(away_prob * 100, 95))

        # Minimum confidence of 50
        confidence = max(confidence, 50)

        # Determine tier
        if confidence >= 75:
            tier = 'Very High'
        elif confidence >= 65:
            tier = 'High'
        elif confidence >= 55:
            tier = 'Medium'
        elif confidence >= 52:
            tier = 'Low'
        else:
            tier = 'Toss-up'

        result = {
            'winner': winner,
            'confidence': confidence,
            'tier': tier,
            'away_prob': round(away_prob * 100, 1),
            'home_prob': round(home_prob * 100, 1)
        }

        if verbose:
            result['factors'] = factors
            result['away_score'] = away_score
            result['home_score'] = home_score

        return result

# =============================================================================
# BACKTESTING
# =============================================================================

def backtest_model(predictor, games, min_history=5):
    """Backtest the model against historical games."""

    correct = 0
    total = 0
    predictions = []

    # Build stats progressively
    progressive_stats = defaultdict(TeamStats)

    for i, game in enumerate(games):
        away = game['away_team']
        home = game['home_team']
        away_score = game['away_score']
        home_score = game['home_score']

        # Skip ties for accuracy calculation
        if away_score == home_score:
            # Still add to stats
            progressive_stats[away].add_game(game['date'], home, away_score, home_score, is_home=False)
            progressive_stats[home].add_game(game['date'], away, home_score, away_score, is_home=True)
            continue

        # Only predict if we have some history
        if i >= min_history:
            # Create predictor with current stats
            temp_predictor = EnhancedPredictor(predictor.rankings, progressive_stats)
            pred = temp_predictor.predict(away, home)

            actual_winner = away if away_score > home_score else home
            is_correct = pred['winner'] == actual_winner

            if is_correct:
                correct += 1
            total += 1

            predictions.append({
                'game': f"{away} @ {home}",
                'predicted': pred['winner'],
                'actual': actual_winner,
                'confidence': pred['confidence'],
                'correct': is_correct
            })

        # Add game to progressive stats
        progressive_stats[away].add_game(game['date'], home, away_score, home_score, is_home=False)
        progressive_stats[home].add_game(game['date'], away, home_score, away_score, is_home=True)

    accuracy = (correct / total * 100) if total > 0 else 0

    return {
        'correct': correct,
        'total': total,
        'accuracy': accuracy,
        'predictions': predictions
    }

def compare_models(rankings, games):
    """Compare old vs new model."""

    # Old model accuracy (from stored predictions)
    old_correct = 0
    old_total = 0

    for game in games:
        if game['away_score'] == game['home_score']:
            continue
        if game['predicted_winner']:
            actual = game['away_team'] if game['away_score'] > game['home_score'] else game['home_team']
            if game['predicted_winner'] == actual:
                old_correct += 1
            old_total += 1

    old_accuracy = (old_correct / old_total * 100) if old_total > 0 else 0

    # New model (backtest)
    team_stats = build_team_stats(games)
    predictor = EnhancedPredictor(rankings, team_stats)
    backtest = backtest_model(predictor, games)

    return {
        'old_model': {
            'correct': old_correct,
            'total': old_total,
            'accuracy': old_accuracy
        },
        'new_model': {
            'correct': backtest['correct'],
            'total': backtest['total'],
            'accuracy': backtest['accuracy']
        },
        'improvement': backtest['accuracy'] - old_accuracy
    }

# =============================================================================
# UPDATE PREDICTIONS
# =============================================================================

def update_predictions(start_date, end_date):
    """Generate new predictions for upcoming games."""

    print("Loading data...")
    rankings = load_team_rankings()
    completed_games = load_completed_games()
    scheduled_games = load_scheduled_games(start_date, end_date)

    print(f"Loaded {len(rankings)} team rankings")
    print(f"Loaded {len(completed_games)} completed games")
    print(f"Loaded {len(scheduled_games)} scheduled games")

    # Build team stats from completed games
    team_stats = build_team_stats(completed_games)

    # Create predictor
    predictor = EnhancedPredictor(rankings, team_stats)

    # Generate predictions
    predictions = []
    for game in scheduled_games:
        pred = predictor.predict(game['away_team'], game['home_team'], verbose=True)

        predictions.append({
            'game_id': game['game_id'],
            'date': game['date'],
            'away_team': game['away_team'],
            'home_team': game['home_team'],
            'old_winner': game['current_prediction'],
            'old_confidence': game['current_confidence'],
            'new_winner': pred['winner'],
            'new_confidence': pred['confidence'],
            'tier': pred['tier'],
            'factors': pred.get('factors', {})
        })

    return predictions

def apply_predictions_to_bigquery(predictions):
    """Update BigQuery with new predictions."""

    for pred in predictions:
        query = f'''
        UPDATE `prodigy-ranking.algorithm_core.nepsac_schedule`
        SET
            predicted_winner_id = '{pred['new_winner']}',
            prediction_confidence = {pred['new_confidence']},
            prediction_method = 'model_v3.0'
        WHERE game_id = '{pred['game_id']}'
        '''
        client.query(query).result()

    print(f"Updated {len(predictions)} predictions in BigQuery")

# =============================================================================
# MAIN
# =============================================================================

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced NEPSAC Prediction Model')
    parser.add_argument('--backtest', action='store_true', help='Run backtest comparison')
    parser.add_argument('--predict', action='store_true', help='Generate new predictions')
    parser.add_argument('--apply', action='store_true', help='Apply predictions to BigQuery')
    parser.add_argument('--start', default='2026-01-26', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end', default='2026-02-01', help='End date (YYYY-MM-DD)')

    args = parser.parse_args()

    if args.backtest:
        print("=" * 60)
        print("BACKTESTING MODEL COMPARISON")
        print("=" * 60)

        rankings = load_team_rankings()
        games = load_completed_games()

        comparison = compare_models(rankings, games)

        print(f"\nOld Model (v2.1):")
        print(f"  Accuracy: {comparison['old_model']['correct']}/{comparison['old_model']['total']} ({comparison['old_model']['accuracy']:.1f}%)")

        print(f"\nNew Model (v3.0):")
        print(f"  Accuracy: {comparison['new_model']['correct']}/{comparison['new_model']['total']} ({comparison['new_model']['accuracy']:.1f}%)")

        print(f"\nImprovement: {comparison['improvement']:+.1f}%")

    if args.predict or args.apply:
        print("=" * 60)
        print(f"GENERATING PREDICTIONS: {args.start} to {args.end}")
        print("=" * 60)

        predictions = update_predictions(args.start, args.end)

        print(f"\n{'Date':<12} {'Matchup':<45} {'Old':<20} {'New':<20}")
        print("-" * 100)

        changed = 0
        for p in predictions:
            old = f"{p['old_winner']} ({p['old_confidence']}%)" if p['old_winner'] else "None"
            new = f"{p['new_winner']} ({p['new_confidence']}%)"

            marker = ""
            if p['old_winner'] != p['new_winner']:
                marker = " ** CHANGED **"
                changed += 1

            matchup = f"{p['away_team']} @ {p['home_team']}"
            print(f"{p['date']:<12} {matchup:<45} {old:<20} {new:<20}{marker}")

        print(f"\n{changed} predictions changed out of {len(predictions)}")

        if args.apply:
            confirm = input("\nApply these predictions to BigQuery? (y/n): ")
            if confirm.lower() == 'y':
                apply_predictions_to_bigquery(predictions)
                print("Done!")
            else:
                print("Cancelled.")

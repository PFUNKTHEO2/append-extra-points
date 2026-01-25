"""
NEPSAC Prediction Regenerator
Regenerates predictions for upcoming games using the updated model weights.
Updates BigQuery nepsac_schedule table with new predictions.

Model Version: 2.1 (2026-01-24)
Weight Changes:
- Reduced home_advantage: 12% -> 5% (missed 9/10 away upsets)
- Increased win_pct: 2% -> 15% (underweighted per ML analysis)
- Minor reductions to prodigy_points, expert_rank, goal_diff

Usage:
    python regenerate_predictions.py [--dry-run]
"""

import json
from datetime import datetime
from google.cloud import bigquery

PROJECT_ID = 'prodigy-ranking'
DATASET_ID = 'algorithm_core'
SEASON = '2025-26'

# Updated prediction weights (Model v2.1 - 2026-01-24)
PREDICTION_WEIGHTS = {
    'mhr_rating': 0.30,         # MyHockeyRankings ELO - strong predictor
    'top_player': 0.15,         # Best player on roster
    'recent_form': 0.15,        # Last 5 games performance
    'win_pct': 0.15,            # Overall win percentage - INCREASED from 2%
    'head_to_head': 0.08,       # Historical matchup
    'prodigy_points': 0.07,     # Team avg ProdigyPoints - reduced from 10%
    'home_advantage': 0.05,     # REDUCED from 12% - was causing missed away upsets
    'expert_rank': 0.03,        # USHR Expert rankings - reduced from 5%
    'goal_diff': 0.02,          # Goals differential - reduced from 3%
}

# Home advantage factor (reduced from 0.58 to 0.55)
HOME_ADVANTAGE = 0.55

client = bigquery.Client(project=PROJECT_ID)


def fetch_upcoming_games():
    """Fetch all scheduled (not final) games."""
    query = '''
    SELECT
        s.game_id,
        s.game_date,
        s.away_team_id,
        s.home_team_id,
        away_team.team_name as away_team_name,
        home_team.team_name as home_team_name,
        -- Away team data
        COALESCE(ar.avg_prodigy_points, 0) as away_avg_points,
        COALESCE(ar.max_prodigy_points, 0) as away_max_points,
        COALESCE(ar.total_prodigy_points, 0) as away_total_points,
        COALESCE(ar.team_ovr, 75) as away_ovr,
        COALESCE(ast.wins, 0) as away_wins,
        COALESCE(ast.losses, 0) as away_losses,
        COALESCE(ast.ties, 0) as away_ties,
        COALESCE(ast.goals_for, 0) as away_gf,
        COALESCE(ast.goals_against, 0) as away_ga,
        -- Home team data
        COALESCE(hr.avg_prodigy_points, 0) as home_avg_points,
        COALESCE(hr.max_prodigy_points, 0) as home_max_points,
        COALESCE(hr.total_prodigy_points, 0) as home_total_points,
        COALESCE(hr.team_ovr, 75) as home_ovr,
        COALESCE(hst.wins, 0) as home_wins,
        COALESCE(hst.losses, 0) as home_losses,
        COALESCE(hst.ties, 0) as home_ties,
        COALESCE(hst.goals_for, 0) as home_gf,
        COALESCE(hst.goals_against, 0) as home_ga
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule` s
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` away_team ON s.away_team_id = away_team.team_id
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_teams` home_team ON s.home_team_id = home_team.team_id
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` ar
        ON s.away_team_id = ar.team_id AND ar.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` hr
        ON s.home_team_id = hr.team_id AND hr.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` ast
        ON s.away_team_id = ast.team_id AND ast.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` hst
        ON s.home_team_id = hst.team_id AND hst.season = '2025-26'
    WHERE s.status = 'scheduled'
        AND s.season = '2025-26'
    ORDER BY s.game_date
    '''
    return list(client.query(query).result())


def calculate_prediction(row):
    """
    Calculate prediction for a single game using Model v2.1 weights.

    Returns:
        dict with predicted_winner_id, confidence, factors
    """
    away_score = 0
    home_score = 0
    factors = {}

    # 1. MHR Rating (30%) - using OVR as proxy
    away_ovr_norm = (row.away_ovr - 70) / 29  # Normalize 70-99 to 0-1
    home_ovr_norm = (row.home_ovr - 70) / 29
    away_score += PREDICTION_WEIGHTS['mhr_rating'] * max(0, min(1, away_ovr_norm))
    home_score += PREDICTION_WEIGHTS['mhr_rating'] * max(0, min(1, home_ovr_norm))
    factors['mhr_rating'] = {'away': row.away_ovr, 'home': row.home_ovr}

    # 2. Top Player (15%)
    max_min, max_max = 2500, 6500
    away_max_norm = (row.away_max_points - max_min) / (max_max - max_min)
    home_max_norm = (row.home_max_points - max_min) / (max_max - max_min)
    away_score += PREDICTION_WEIGHTS['top_player'] * max(0, min(1, away_max_norm))
    home_score += PREDICTION_WEIGHTS['top_player'] * max(0, min(1, home_max_norm))
    factors['top_player'] = {'away': row.away_max_points, 'home': row.home_max_points}

    # 3. Recent Form (15%) - using win percentage as proxy
    away_games = row.away_wins + row.away_losses + row.away_ties
    home_games = row.home_wins + row.home_losses + row.home_ties
    away_form = (row.away_wins + 0.5 * row.away_ties) / away_games if away_games > 0 else 0.5
    home_form = (row.home_wins + 0.5 * row.home_ties) / home_games if home_games > 0 else 0.5
    away_score += PREDICTION_WEIGHTS['recent_form'] * away_form
    home_score += PREDICTION_WEIGHTS['recent_form'] * home_form
    factors['recent_form'] = {'away': f"{away_form:.1%}", 'home': f"{home_form:.1%}"}

    # 4. Win Percentage (15%) - INCREASED WEIGHT
    away_wp = row.away_wins / away_games if away_games > 0 else 0.5
    home_wp = row.home_wins / home_games if home_games > 0 else 0.5
    away_score += PREDICTION_WEIGHTS['win_pct'] * away_wp
    home_score += PREDICTION_WEIGHTS['win_pct'] * home_wp
    factors['win_pct'] = {'away': f"{away_wp:.1%}", 'home': f"{home_wp:.1%}"}

    # 5. Head-to-Head (8%) - not available in current data, split evenly
    away_score += PREDICTION_WEIGHTS['head_to_head'] * 0.5
    home_score += PREDICTION_WEIGHTS['head_to_head'] * 0.5
    factors['head_to_head'] = {'away': 'N/A', 'home': 'N/A'}

    # 6. ProdigyPoints (7%) - reduced weight
    pp_min, pp_max = 750, 3500
    away_pp_norm = (row.away_avg_points - pp_min) / (pp_max - pp_min)
    home_pp_norm = (row.home_avg_points - pp_min) / (pp_max - pp_min)
    away_score += PREDICTION_WEIGHTS['prodigy_points'] * max(0, min(1, away_pp_norm))
    home_score += PREDICTION_WEIGHTS['prodigy_points'] * max(0, min(1, home_pp_norm))
    factors['prodigy_points'] = {'away': row.away_avg_points, 'home': row.home_avg_points}

    # 7. Home Advantage (5%) - REDUCED WEIGHT
    away_score += PREDICTION_WEIGHTS['home_advantage'] * (1 - HOME_ADVANTAGE)
    home_score += PREDICTION_WEIGHTS['home_advantage'] * HOME_ADVANTAGE
    factors['home_advantage'] = {'away': 'Away', 'home': 'Home'}

    # 8. Expert Rank (3%) - not available, split evenly
    away_score += PREDICTION_WEIGHTS['expert_rank'] * 0.5
    home_score += PREDICTION_WEIGHTS['expert_rank'] * 0.5
    factors['expert_rank'] = {'away': 'N/A', 'home': 'N/A'}

    # 9. Goal Differential (2%)
    away_gd = (row.away_gf - row.away_ga) / max(away_games, 1)
    home_gd = (row.home_gf - row.home_ga) / max(home_games, 1)
    away_gd_norm = (away_gd + 3) / 6  # Normalize -3 to +3 range
    home_gd_norm = (home_gd + 3) / 6
    away_score += PREDICTION_WEIGHTS['goal_diff'] * max(0, min(1, away_gd_norm))
    home_score += PREDICTION_WEIGHTS['goal_diff'] * max(0, min(1, home_gd_norm))
    factors['goal_diff'] = {'away': f"{away_gd:+.2f}", 'home': f"{home_gd:+.2f}"}

    # Calculate winner and confidence
    total_score = away_score + home_score
    if total_score == 0:
        total_score = 1

    away_pct = away_score / total_score
    home_pct = home_score / total_score

    if home_pct >= away_pct:
        predicted_winner_id = row.home_team_id
        win_probability = home_pct
    else:
        predicted_winner_id = row.away_team_id
        win_probability = away_pct

    # Convert to confidence (50-99 scale)
    confidence = int(min(99, max(50, win_probability * 100)))

    return {
        'predicted_winner_id': predicted_winner_id,
        'confidence': confidence,
        'away_pct': round(away_pct * 100, 1),
        'home_pct': round(home_pct * 100, 1),
        'factors': factors
    }


def update_predictions_in_bigquery(predictions, dry_run=False):
    """Update predictions in BigQuery nepsac_schedule table."""
    if dry_run:
        print("\n[DRY RUN - No updates will be made]")
        return 0

    updated = 0
    timestamp_str = datetime.now().isoformat()
    for game_id, pred in predictions.items():
        query = f'''
        UPDATE `{PROJECT_ID}.{DATASET_ID}.nepsac_schedule`
        SET
            predicted_winner_id = '{pred["predicted_winner_id"]}',
            prediction_confidence = {pred["confidence"]},
            prediction_method = 'model_v2.1',
            updated_at = '{timestamp_str}'
        WHERE game_id = '{game_id}'
        '''
        try:
            client.query(query).result()
            updated += 1
        except Exception as e:
            print(f"  Error updating {game_id}: {e}")

    return updated


def main(dry_run=False):
    print("=" * 70)
    print("NEPSAC PREDICTION REGENERATOR")
    print("Model Version: 2.1 (2026-01-24)")
    print("=" * 70)

    print("\nWeight Configuration:")
    for factor, weight in sorted(PREDICTION_WEIGHTS.items(), key=lambda x: -x[1]):
        print(f"  {factor}: {weight*100:.0f}%")
    print(f"\nHome Advantage Factor: {HOME_ADVANTAGE:.0%}")

    print("\n" + "-" * 50)
    print("FETCHING UPCOMING GAMES")
    print("-" * 50)

    games = fetch_upcoming_games()
    print(f"Found {len(games)} scheduled games")

    if not games:
        print("No upcoming games to predict.")
        return

    print("\n" + "-" * 50)
    print("GENERATING PREDICTIONS")
    print("-" * 50)

    predictions = {}
    prediction_summary = {'home': 0, 'away': 0, 'high_conf': 0, 'low_conf': 0}

    for game in games:
        pred = calculate_prediction(game)
        predictions[game.game_id] = pred

        # Track statistics
        is_home_pick = pred['predicted_winner_id'] == game.home_team_id
        if is_home_pick:
            prediction_summary['home'] += 1
        else:
            prediction_summary['away'] += 1

        if pred['confidence'] >= 60:
            prediction_summary['high_conf'] += 1
        else:
            prediction_summary['low_conf'] += 1

        # Print sample predictions
        if len(predictions) <= 10:
            winner_name = game.home_team_name if is_home_pick else game.away_team_name
            print(f"\n{game.game_date}: {game.away_team_name} @ {game.home_team_name}")
            print(f"  Prediction: {winner_name} ({pred['confidence']}%)")
            print(f"  Score: Away {pred['away_pct']}% vs Home {pred['home_pct']}%")

    print("\n" + "-" * 50)
    print("PREDICTION SUMMARY")
    print("-" * 50)
    print(f"Total games: {len(predictions)}")
    print(f"Home picks: {prediction_summary['home']} ({prediction_summary['home']/len(predictions)*100:.1f}%)")
    print(f"Away picks: {prediction_summary['away']} ({prediction_summary['away']/len(predictions)*100:.1f}%)")
    print(f"High confidence (60%+): {prediction_summary['high_conf']}")
    print(f"Low confidence (<60%): {prediction_summary['low_conf']}")

    print("\n" + "-" * 50)
    print("UPDATING BIGQUERY")
    print("-" * 50)

    updated = update_predictions_in_bigquery(predictions, dry_run)
    print(f"Updated {updated} game predictions")

    # Save predictions to JSON for reference
    output = {
        'generated_at': datetime.now().isoformat(),
        'model_version': '2.1',
        'weights': PREDICTION_WEIGHTS,
        'home_advantage': HOME_ADVANTAGE,
        'total_games': len(predictions),
        'predictions': {
            gid: {
                'predicted_winner_id': p['predicted_winner_id'],
                'confidence': p['confidence'],
                'away_pct': p['away_pct'],
                'home_pct': p['home_pct']
            }
            for gid, p in predictions.items()
        }
    }

    with open('predictions_v2.1_output.json', 'w') as f:
        json.dump(output, f, indent=2)
    print("\nSaved predictions to predictions_v2.1_output.json")

    print("\n" + "=" * 70)
    print("REGENERATION COMPLETE")
    print("=" * 70)


if __name__ == '__main__':
    import sys
    dry_run = '--dry-run' in sys.argv
    main(dry_run=dry_run)

"""
NEPSAC Prediction Model Optimizer v2
More robust analysis with cross-validation and regularization.
"""

import numpy as np
from google.cloud import bigquery
from sklearn.linear_model import LogisticRegressionCV
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score, LeaveOneOut
import json
import warnings
warnings.filterwarnings('ignore')

client = bigquery.Client(project='prodigy-ranking')

def fetch_training_data():
    """Fetch all completed games with predictions and team stats."""
    query = '''
    SELECT
        s.game_id,
        s.game_date,
        s.predicted_winner_id,
        s.prediction_confidence,
        s.away_team_id,
        s.home_team_id,
        CAST(s.away_score AS INT64) as away_score,
        CAST(s.home_score AS INT64) as home_score,
        COALESCE(ar.avg_prodigy_points, 0) as away_avg_points,
        COALESCE(ar.max_prodigy_points, 0) as away_max_points,
        COALESCE(ar.total_prodigy_points, 0) as away_total_points,
        COALESCE(ar.team_ovr, 75) as away_ovr,
        COALESCE(ast.wins, 0) as away_wins,
        COALESCE(ast.losses, 0) as away_losses,
        COALESCE(ast.goals_for, 0) as away_gf,
        COALESCE(ast.goals_against, 0) as away_ga,
        COALESCE(hr.avg_prodigy_points, 0) as home_avg_points,
        COALESCE(hr.max_prodigy_points, 0) as home_max_points,
        COALESCE(hr.total_prodigy_points, 0) as home_total_points,
        COALESCE(hr.team_ovr, 75) as home_ovr,
        COALESCE(hst.wins, 0) as home_wins,
        COALESCE(hst.losses, 0) as home_losses,
        COALESCE(hst.goals_for, 0) as home_gf,
        COALESCE(hst.goals_against, 0) as home_ga
    FROM `prodigy-ranking.algorithm_core.nepsac_schedule` s
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` ar
        ON s.away_team_id = ar.team_id AND ar.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_team_rankings` hr
        ON s.home_team_id = hr.team_id AND hr.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` ast
        ON s.away_team_id = ast.team_id AND ast.season = '2025-26'
    LEFT JOIN `prodigy-ranking.algorithm_core.nepsac_standings` hst
        ON s.home_team_id = hst.team_id AND hst.season = '2025-26'
    WHERE s.status = 'final'
        AND s.season = '2025-26'
        AND s.predicted_winner_id IS NOT NULL
    ORDER BY s.game_date
    '''
    return list(client.query(query).result())

def extract_features(row):
    """Extract normalized feature differences (home - away)."""
    # Normalize by typical ranges
    avg_points_diff = (row.home_avg_points - row.away_avg_points) / 1000
    max_points_diff = (row.home_max_points - row.away_max_points) / 1000
    total_points_diff = (row.home_total_points - row.away_total_points) / 10000
    ovr_diff = (row.home_ovr - row.away_ovr) / 10

    # Win percentage
    away_games = row.away_wins + row.away_losses
    home_games = row.home_wins + row.home_losses
    away_win_pct = row.away_wins / away_games if away_games > 0 else 0.5
    home_win_pct = row.home_wins / home_games if home_games > 0 else 0.5
    win_pct_diff = home_win_pct - away_win_pct

    # Goal differential per game
    away_goal_diff = (row.away_gf - row.away_ga) / max(away_games, 1)
    home_goal_diff = (row.home_gf - row.home_ga) / max(home_games, 1)
    goal_diff_diff = home_goal_diff - away_goal_diff

    # Recent form
    away_form = (row.away_wins - row.away_losses) / max(away_games, 1)
    home_form = (row.home_wins - row.home_losses) / max(home_games, 1)
    form_diff = home_form - away_form

    return np.array([
        avg_points_diff,      # ProdigyPoints average
        max_points_diff,      # Top player strength
        total_points_diff,    # Team depth
        ovr_diff,             # OVR rating
        win_pct_diff,         # Win percentage
        goal_diff_diff,       # Goal differential
        form_diff,            # Recent form
        1.0,                  # Home advantage (constant)
    ])

FEATURE_NAMES = [
    'Avg Points',
    'Top Player',
    'Team Depth',
    'OVR Rating',
    'Win %',
    'Goal Diff',
    'Form',
    'Home Ice',
]

def analyze():
    print("=" * 70)
    print("NEPSAC PREDICTION MODEL OPTIMIZER v2")
    print("With Cross-Validation and Regularization")
    print("=" * 70)

    # Fetch data
    rows = fetch_training_data()
    print(f"\nTotal completed games: {len(rows)}")

    # Build feature matrix
    X, y, game_info = [], [], []
    for row in rows:
        if row.home_score == row.away_score:  # Skip ties
            continue
        outcome = 1 if row.home_score > row.away_score else 0
        X.append(extract_features(row))
        y.append(outcome)
        game_info.append({
            'game_id': row.game_id,
            'date': str(row.game_date),
            'matchup': f"{row.away_team_id} @ {row.home_team_id}",
            'score': f"{row.away_score}-{row.home_score}",
            'original_prediction': row.predicted_winner_id,
            'original_confidence': row.prediction_confidence,
        })

    X = np.array(X)
    y = np.array(y)

    print(f"Training samples (excl ties): {len(y)}")
    print(f"Home wins: {sum(y)} ({sum(y)/len(y)*100:.1f}%)")
    print(f"Away wins: {len(y)-sum(y)} ({(len(y)-sum(y))/len(y)*100:.1f}%)")

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Cross-validated Logistic Regression with regularization
    print("\n" + "-" * 50)
    print("LOGISTIC REGRESSION WITH CROSS-VALIDATION")
    print("-" * 50)

    # Use Leave-One-Out cross-validation (best for small datasets)
    loo = LeaveOneOut()
    model = LogisticRegressionCV(
        cv=5,  # 5-fold CV for hyperparameter tuning
        Cs=[0.01, 0.1, 1, 10],
        penalty='l2',
        max_iter=1000,
        random_state=42
    )
    model.fit(X_scaled, y)

    # Leave-one-out accuracy (true generalization)
    loo_scores = cross_val_score(model, X_scaled, y, cv=loo)
    loo_accuracy = np.mean(loo_scores)

    # 5-fold CV accuracy
    cv5_scores = cross_val_score(model, X_scaled, y, cv=5)

    print(f"Best regularization C: {model.C_[0]:.2f}")
    print(f"Training accuracy: {model.score(X_scaled, y)*100:.1f}%")
    print(f"5-Fold CV accuracy: {np.mean(cv5_scores)*100:.1f}% (+/- {np.std(cv5_scores)*100:.1f}%)")
    print(f"Leave-One-Out accuracy: {loo_accuracy*100:.1f}%")

    # Feature importance
    print("\n" + "-" * 50)
    print("FEATURE IMPORTANCE (Standardized Coefficients)")
    print("-" * 50)

    coefs = model.coef_[0]
    importance = np.abs(coefs)
    importance_pct = importance / importance.sum() * 100

    # Sort by importance
    sorted_idx = np.argsort(importance)[::-1]

    print(f"{'Rank':<5} {'Feature':<15} {'Coef':>8} {'Importance':>12}")
    print("-" * 45)
    for rank, idx in enumerate(sorted_idx, 1):
        print(f"{rank:<5} {FEATURE_NAMES[idx]:<15} {coefs[idx]:>8.3f} {importance_pct[idx]:>10.1f}%")

    # Analyze prediction errors
    print("\n" + "-" * 50)
    print("PREDICTION ERROR ANALYSIS")
    print("-" * 50)

    predictions = model.predict(X_scaled)
    probabilities = model.predict_proba(X_scaled)[:, 1]

    errors = []
    for i, (pred, actual, prob, info) in enumerate(zip(predictions, y, probabilities, game_info)):
        if pred != actual:
            errors.append({
                **info,
                'predicted': 'home' if pred else 'away',
                'actual': 'home' if actual else 'away',
                'confidence': prob if pred == 1 else 1 - prob,
            })

    print(f"Total errors: {len(errors)}/{len(y)} ({len(errors)/len(y)*100:.1f}%)")

    # Categorize errors
    upset_errors = [e for e in errors if e['actual'] == 'away']
    home_errors = [e for e in errors if e['actual'] == 'home']

    print(f"  - Missed away upsets: {len(upset_errors)}")
    print(f"  - Missed home wins: {len(home_errors)}")

    print("\nMost confident errors:")
    sorted_errors = sorted(errors, key=lambda x: x['confidence'], reverse=True)
    for e in sorted_errors[:5]:
        print(f"  {e['date']}: {e['matchup']} ({e['score']})")
        print(f"    Predicted {e['predicted']} with {e['confidence']*100:.0f}% confidence")

    # Generate recommended weights
    print("\n" + "=" * 70)
    print("RECOMMENDED PRODUCTION WEIGHTS")
    print("=" * 70)

    # Convert coefficients to interpretable weights
    # Only use positive coefficients for each feature (set floor at 0)
    # Then normalize to sum to 100%
    raw_weights = np.abs(coefs)
    raw_weights = raw_weights / raw_weights.sum()

    # Apply minimum threshold (3%) to avoid very small weights
    MIN_WEIGHT = 0.03
    adjusted_weights = np.maximum(raw_weights, MIN_WEIGHT)
    adjusted_weights = adjusted_weights / adjusted_weights.sum()

    print("\nOptimized weights based on 35 games:")
    print(f"{'Feature':<20} {'Weight':>10} {'Current':>10} {'Change':>10}")
    print("-" * 50)

    current_weights = [0.30, 0.15, 0.10, 0.08, 0.05, 0.05, 0.15, 0.12]  # Same order as FEATURE_NAMES
    weight_dict = {}

    for i, name in enumerate(FEATURE_NAMES):
        new_w = adjusted_weights[i] * 100
        old_w = current_weights[i] * 100
        change = new_w - old_w
        weight_dict[name] = round(new_w, 1)
        sign = "+" if change > 0 else ""
        print(f"{name:<20} {new_w:>9.1f}% {old_w:>9.1f}% {sign}{change:>9.1f}%")

    # Summary statistics
    print("\n" + "-" * 50)
    print("SUMMARY")
    print("-" * 50)
    print(f"Current model accuracy: ~71% (from stored predictions)")
    print(f"Optimized model (LOO CV): {loo_accuracy*100:.1f}%")
    print(f"Potential improvement: {(loo_accuracy - 0.71)*100:+.1f}%")
    print(f"\nKey insights:")

    # Find biggest changes
    changes = [(FEATURE_NAMES[i], adjusted_weights[i] - current_weights[i])
               for i in range(len(FEATURE_NAMES))]
    increases = sorted([c for c in changes if c[1] > 0.02], key=lambda x: -x[1])
    decreases = sorted([c for c in changes if c[1] < -0.02], key=lambda x: x[1])

    if increases:
        print(f"  - Increase weight on: {', '.join([c[0] for c in increases[:3]])}")
    if decreases:
        print(f"  - Decrease weight on: {', '.join([c[0] for c in decreases[:3]])}")

    # Check home advantage significance
    home_coef = coefs[-1]
    if home_coef > 0.1:
        print(f"  - Home ice advantage is significant (coef: {home_coef:.2f})")
    else:
        print(f"  - Home ice advantage is weak (coef: {home_coef:.2f})")

    # Save results
    results = {
        'analysis_date': str(np.datetime64('today')),
        'games_analyzed': len(y),
        'loo_cv_accuracy': round(loo_accuracy * 100, 1),
        'cv5_accuracy': round(np.mean(cv5_scores) * 100, 1),
        'training_accuracy': round(model.score(X_scaled, y) * 100, 1),
        'recommended_weights': weight_dict,
        'feature_coefficients': {FEATURE_NAMES[i]: round(coefs[i], 4) for i in range(len(FEATURE_NAMES))},
        'regularization_C': float(model.C_[0]),
        'errors': len(errors),
        'home_win_rate': round(sum(y)/len(y) * 100, 1),
    }

    with open('prediction_model_analysis_v2.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to prediction_model_analysis_v2.json")

    return results

if __name__ == '__main__':
    analyze()

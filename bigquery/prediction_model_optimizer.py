"""
NEPSAC Prediction Model Optimizer
Uses historical game results to optimize prediction weights via gradient descent.
"""

import numpy as np
from google.cloud import bigquery
from scipy.optimize import minimize
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
import json

client = bigquery.Client(project='prodigy-ranking')

# Current static weights (for comparison)
CURRENT_WEIGHTS = {
    'avg_points_diff': 0.30,      # MHR Rating
    'max_points_diff': 0.15,      # Top Player
    'recent_form_diff': 0.15,     # Recent Form (wins-losses)
    'home_advantage': 0.12,       # Home Advantage
    'total_points_diff': 0.10,    # ProdigyPoints
    'ovr_diff': 0.08,             # Head-to-Head (using OVR as proxy)
    'goal_diff_diff': 0.05,       # Goal Differential
    'win_pct_diff': 0.05,         # Win Percentage
}

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
        -- Away team stats
        COALESCE(ar.avg_prodigy_points, 0) as away_avg_points,
        COALESCE(ar.max_prodigy_points, 0) as away_max_points,
        COALESCE(ar.total_prodigy_points, 0) as away_total_points,
        COALESCE(ar.team_ovr, 75) as away_ovr,
        COALESCE(ast.wins, 0) as away_wins,
        COALESCE(ast.losses, 0) as away_losses,
        COALESCE(ast.goals_for, 0) as away_gf,
        COALESCE(ast.goals_against, 0) as away_ga,
        -- Home team stats
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
    """Extract feature differences between home and away teams.
    Positive values favor home team, negative favor away team.
    """
    # Calculate differences (home - away)
    avg_points_diff = (row.home_avg_points - row.away_avg_points) / 1000  # Normalize
    max_points_diff = (row.home_max_points - row.away_max_points) / 1000
    total_points_diff = (row.home_total_points - row.away_total_points) / 10000
    ovr_diff = (row.home_ovr - row.away_ovr) / 10

    # Win percentage
    away_games = row.away_wins + row.away_losses
    home_games = row.home_wins + row.home_losses
    away_win_pct = row.away_wins / away_games if away_games > 0 else 0.5
    home_win_pct = row.home_wins / home_games if home_games > 0 else 0.5
    win_pct_diff = home_win_pct - away_win_pct

    # Goal differential
    away_goal_diff = row.away_gf - row.away_ga
    home_goal_diff = row.home_gf - row.home_ga
    goal_diff_diff = (home_goal_diff - away_goal_diff) / 10

    # Recent form (simple wins - losses)
    away_form = row.away_wins - row.away_losses
    home_form = row.home_wins - row.home_losses
    form_diff = (home_form - away_form) / 5

    # Home advantage (constant feature)
    home_advantage = 1.0

    return np.array([
        avg_points_diff,
        max_points_diff,
        form_diff,
        home_advantage,
        total_points_diff,
        ovr_diff,
        goal_diff_diff,
        win_pct_diff,
    ])

def get_outcome(row):
    """Returns 1 if home team won, 0 if away team won, None if tie."""
    if row.home_score > row.away_score:
        return 1  # Home win
    elif row.away_score > row.home_score:
        return 0  # Away win
    else:
        return None  # Tie

def sigmoid(x):
    """Sigmoid function for probability."""
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))

def predict_with_weights(features, weights):
    """Predict probability of home team winning."""
    score = np.dot(features, weights)
    return sigmoid(score)

def log_loss(weights, X, y):
    """Calculate log loss for given weights."""
    predictions = sigmoid(np.dot(X, weights))
    predictions = np.clip(predictions, 1e-15, 1 - 1e-15)
    return -np.mean(y * np.log(predictions) + (1 - y) * np.log(1 - predictions))

def accuracy(weights, X, y):
    """Calculate prediction accuracy."""
    predictions = sigmoid(np.dot(X, weights)) > 0.5
    return np.mean(predictions == y)

def analyze_current_model():
    """Analyze current model performance and optimize weights."""
    print("=" * 60)
    print("NEPSAC PREDICTION MODEL OPTIMIZER")
    print("=" * 60)

    # Fetch data
    print("\nFetching training data...")
    rows = fetch_training_data()
    print(f"Total games with predictions: {len(rows)}")

    # Extract features and outcomes
    X = []
    y = []
    games_info = []

    for row in rows:
        outcome = get_outcome(row)
        if outcome is None:  # Skip ties
            continue

        features = extract_features(row)
        X.append(features)
        y.append(outcome)
        games_info.append({
            'game_id': row.game_id,
            'date': str(row.game_date),
            'away': row.away_team_id,
            'home': row.home_team_id,
            'score': f"{row.away_score}-{row.home_score}",
            'predicted': row.predicted_winner_id,
            'confidence': row.prediction_confidence,
        })

    X = np.array(X)
    y = np.array(y)

    print(f"Games for training (excluding ties): {len(y)}")
    print(f"Home wins: {sum(y)}, Away wins: {len(y) - sum(y)}")

    # Current weights as array
    current_weights = np.array([
        0.30,  # avg_points_diff
        0.15,  # max_points_diff
        0.15,  # form_diff
        0.12,  # home_advantage
        0.10,  # total_points_diff
        0.08,  # ovr_diff
        0.05,  # goal_diff_diff
        0.05,  # win_pct_diff
    ])

    # Evaluate current weights
    print("\n" + "-" * 40)
    print("CURRENT MODEL PERFORMANCE")
    print("-" * 40)
    current_acc = accuracy(current_weights, X, y)
    current_loss = log_loss(current_weights, X, y)
    print(f"Accuracy: {current_acc * 100:.1f}%")
    print(f"Log Loss: {current_loss:.4f}")

    # Optimize with scipy
    print("\n" + "-" * 40)
    print("OPTIMIZING WEIGHTS (Gradient Descent)")
    print("-" * 40)

    result = minimize(
        log_loss,
        current_weights,
        args=(X, y),
        method='L-BFGS-B',
        options={'maxiter': 1000}
    )

    optimized_weights = result.x

    # Normalize weights to sum to ~1 (for interpretability)
    optimized_weights_normalized = optimized_weights / np.sum(np.abs(optimized_weights))

    opt_acc = accuracy(optimized_weights, X, y)
    opt_loss = log_loss(optimized_weights, X, y)

    print(f"Optimized Accuracy: {opt_acc * 100:.1f}%")
    print(f"Optimized Log Loss: {opt_loss:.4f}")
    print(f"Improvement: {(opt_acc - current_acc) * 100:+.1f}%")

    # Also try Logistic Regression
    print("\n" + "-" * 40)
    print("LOGISTIC REGRESSION COMPARISON")
    print("-" * 40)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    lr = LogisticRegression(max_iter=1000, C=1.0)
    lr.fit(X_scaled, y)
    lr_acc = lr.score(X_scaled, y)
    print(f"Logistic Regression Accuracy: {lr_acc * 100:.1f}%")

    # Feature importance from LR
    feature_names = [
        'Avg Points Diff',
        'Max Points Diff',
        'Form Diff',
        'Home Advantage',
        'Total Points Diff',
        'OVR Diff',
        'Goal Diff Diff',
        'Win Pct Diff',
    ]

    print("\n" + "-" * 40)
    print("OPTIMIZED WEIGHTS COMPARISON")
    print("-" * 40)
    print(f"{'Feature':<20} {'Current':>10} {'Optimized':>10} {'LR Coef':>10}")
    print("-" * 50)

    for i, name in enumerate(feature_names):
        current = current_weights[i]
        optimized = optimized_weights_normalized[i]
        lr_coef = lr.coef_[0][i] / np.sum(np.abs(lr.coef_[0]))
        print(f"{name:<20} {current:>10.2f} {optimized:>10.2f} {lr_coef:>10.2f}")

    # Analyze misclassified games
    print("\n" + "-" * 40)
    print("MISCLASSIFIED GAMES ANALYSIS")
    print("-" * 40)

    predictions = sigmoid(np.dot(X, optimized_weights)) > 0.5
    misclassified = []

    for i, (pred, actual, info) in enumerate(zip(predictions, y, games_info)):
        if pred != actual:
            misclassified.append({
                **info,
                'predicted_winner': 'home' if pred else 'away',
                'actual_winner': 'home' if actual else 'away',
            })

    print(f"Misclassified games: {len(misclassified)}")
    for m in misclassified[:5]:  # Show first 5
        print(f"  {m['date']}: {m['away']} @ {m['home']} ({m['score']})")
        print(f"    Model predicted {m['predicted_winner']}, actual: {m['actual_winner']}")

    # Output recommended weights
    print("\n" + "=" * 60)
    print("RECOMMENDED WEIGHTS FOR PRODUCTION")
    print("=" * 60)

    # Use a blend of current and optimized (to avoid overfitting)
    blend_ratio = 0.6  # 60% optimized, 40% current
    blended_weights = blend_ratio * optimized_weights_normalized + (1 - blend_ratio) * (current_weights / np.sum(current_weights))
    blended_weights = blended_weights / np.sum(np.abs(blended_weights))  # Renormalize

    print("\nBlended weights (60% optimized + 40% current to avoid overfitting):")
    weight_dict = {}
    for i, name in enumerate(feature_names):
        pct = blended_weights[i] * 100
        weight_dict[name] = round(pct, 1)
        print(f"  {name}: {pct:.1f}%")

    # Save results to JSON
    results = {
        'analysis_date': str(np.datetime64('today')),
        'games_analyzed': len(y),
        'current_accuracy': round(current_acc * 100, 1),
        'optimized_accuracy': round(opt_acc * 100, 1),
        'logistic_regression_accuracy': round(lr_acc * 100, 1),
        'current_weights': {name: round(current_weights[i] * 100, 1) for i, name in enumerate(feature_names)},
        'optimized_weights': {name: round(optimized_weights_normalized[i] * 100, 1) for i, name in enumerate(feature_names)},
        'recommended_weights': weight_dict,
    }

    with open('prediction_model_analysis.json', 'w') as f:
        json.dump(results, f, indent=2)

    print("\nResults saved to prediction_model_analysis.json")

    return results

if __name__ == '__main__':
    analyze_current_model()

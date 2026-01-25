# NEPSAC Prediction Model Evolution Documentation

**Project:** Ace & Scouty's Game Day Predictions
**Sport:** NEPSAC Prep Hockey
**Season:** 2025-26
**Last Updated:** 2026-01-24

---

## Executive Summary

This document tracks the evolution of the NEPSAC game prediction model from its initial static-weight implementation through machine learning-informed optimization. The model predicts game outcomes for prep hockey games using a multi-factor weighted scoring system.

**Current Performance (as of 2026-01-24):**
- **Accuracy:** 71.4% (25 correct, 10 incorrect, 3 ties out of 38 games)
- **Model Version:** 2.1
- **Key Insight:** Reducing home advantage bias from 12% to 5% addresses the model's tendency to miss away upsets

---

## Table of Contents

1. [Model Architecture Overview](#1-model-architecture-overview)
2. [Version History](#2-version-history)
3. [Data Sources](#3-data-sources)
4. [Factor Analysis](#4-factor-analysis)
5. [Machine Learning Analysis](#5-machine-learning-analysis)
6. [Weight Optimization Results](#6-weight-optimization-results)
7. [Error Analysis](#7-error-analysis)
8. [Future Improvements](#8-future-improvements)
9. [Technical Implementation](#9-technical-implementation)

---

## 1. Model Architecture Overview

### 1.1 Core Prediction Formula

The model predicts game outcomes using a weighted linear combination of factors:

```
P(home_win) = Σ(weight_i × normalized_factor_i) / Σ(weights)
```

Where each factor is normalized to a 0-1 scale and weights sum to 100%.

### 1.2 Factor Categories

| Category | Description | Data Source |
|----------|-------------|-------------|
| **Talent Metrics** | ProdigyPoints, Top Player | BigQuery algorithm |
| **Performance Metrics** | Win %, Goal Differential, Form | Game results |
| **Situational Factors** | Home Advantage, Head-to-Head | Schedule/History |
| **External Rankings** | MHR Rating, Expert Rankings | Third-party sources |

### 1.3 Confidence Tiers

| Confidence | Tier | Interpretation |
|------------|------|----------------|
| 85-99% | Very High | Strong mismatch |
| 70-84% | High | Clear favorite |
| 60-69% | Medium | Probable outcome |
| 55-59% | Low | Slight edge |
| 50-54% | Toss-up | Essentially even |

---

## 2. Version History

### Version 1.0 (Initial - 2026-01-19)

**Launch Configuration:**

| Factor | Weight | Rationale |
|--------|--------|-----------|
| MHR Rating | 25% | Mathematical ELO-style rating |
| ProdigyPoints | 15% | Team talent metric |
| Recent Form | 15% | Last 5 games performance |
| Expert Rank | 10% | USHR power rankings |
| Goal Differential | 10% | Scoring margin |
| Home Advantage | 8% | Historical home win rate |
| Win Percentage | 7% | Overall record |
| Top Player | 5% | Star player impact |
| Head-to-Head | 5% | Historical matchup |

**Initial Parameters:**
- HOME_ADVANTAGE factor: 0.58 (58% home win rate)

---

### Version 2.0 (2026-01-22)

**Trigger:** First batch of game results (Jan 21, 2026) analyzed

**Changes Based on Performance Analysis:**

| Factor | v1.0 | v2.0 | Change | Reason |
|--------|------|------|--------|--------|
| MHR Rating | 25% | 30% | +5% | Best performer (65% accuracy) |
| Top Player | 5% | 15% | +10% | Best performer (65% accuracy) |
| Home Advantage | 8% | 12% | +4% | Home teams won 60% |
| Head-to-Head | 5% | 8% | +3% | Important for rivalries |
| ProdigyPoints | 15% | 10% | -5% | Underperformed (55%) |
| Expert Rank | 10% | 5% | -5% | Underperformed (45%) |
| Goal Differential | 10% | 3% | -7% | Underperformed (45%) |
| Win Percentage | 7% | 2% | -5% | Underperformed (45%) |
| Recent Form | 15% | 15% | 0% | Solid (60% accuracy) |

**Updated Parameters:**
- HOME_ADVANTAGE factor: 0.58 (unchanged)

**Results:** 75% accuracy on Jan 21 games (16/21 correct after excluding ties)

---

### Version 2.1 (2026-01-24) - CURRENT

**Trigger:** Machine learning analysis revealed systematic bias

**ML Analysis Findings:**
1. **Sample Size:** 35 games (excluding ties) - insufficient for pure ML automation
2. **Error Pattern:** 9 out of 10 prediction errors were missed away upsets
3. **Feature Importance (Logistic Regression):**
   - Form: 27.1%
   - Win %: 27.1%
   - Team Depth: 25.1%
   - Others: <10% each
4. **Home Advantage Finding:** Model was too biased toward home teams

**Weight Changes:**

| Factor | v2.0 | v2.1 | Change | Reason |
|--------|------|------|--------|--------|
| MHR Rating | 30% | 30% | 0% | Strong predictor - keep |
| Top Player | 15% | 15% | 0% | Strong predictor - keep |
| Recent Form | 15% | 15% | 0% | Strong per ML - keep |
| **Win %** | **2%** | **15%** | **+13%** | **ML showed underweighted** |
| Head-to-Head | 8% | 8% | 0% | Keep for rivalries |
| ProdigyPoints | 10% | 7% | -3% | Slight reduction |
| **Home Advantage** | **12%** | **5%** | **-7%** | **Missed 9/10 away upsets** |
| Expert Rank | 5% | 3% | -2% | Underperformed |
| Goal Differential | 3% | 2% | -1% | Underperformed |

**Updated Parameters:**
- HOME_ADVANTAGE factor: 0.55 (reduced from 0.58)

**Expected Impact:**
- More balanced home/away predictions (51% home vs 49% away)
- Better prediction of away upsets
- Maintained accuracy on clear favorites

---

## 3. Data Sources

### 3.1 Primary Data Sources

| Source | Data Type | Update Frequency | Use |
|--------|-----------|------------------|-----|
| BigQuery `nepsac_schedule` | Game schedule, results | Daily | Outcomes, predictions |
| BigQuery `nepsac_team_rankings` | ProdigyPoints | Weekly | Talent metrics |
| BigQuery `nepsac_standings` | W-L-T, Goals | Daily | Performance metrics |
| MyHockeyRankings.com | MHR Rating | Weekly | ELO-style ranking |
| USHR.com | Expert Rankings | Weekly | Qualitative ranking |

### 3.2 Derived Metrics

| Metric | Formula | Range |
|--------|---------|-------|
| Form Score | (Wins + 0.5×Ties) / Games Played | 0-1 |
| Goal Diff/Game | (GF - GA) / Games Played | -3 to +3 typical |
| Win Percentage | Wins / (Wins + Losses) | 0-1 |
| Team OVR | 70 + ((AvgPoints - 750) / (2950 - 750) × 29) | 70-99 |

### 3.3 Age Normalization

Players receive age-based multipliers to their ProdigyPoints:

| Birth Year | Age (2025-26) | Multiplier | Rationale |
|------------|---------------|------------|-----------|
| 2011 | 14-15 | 1.45× | Exceptional if playing prep |
| 2010 | 15-16 | 1.35× | Young prospect |
| 2009 | 16-17 | 1.22× | Above average youth |
| 2008 | 17-18 | 1.10× | Typical junior/senior |
| 2007 | 18-19 | 1.00× | Baseline (PG year) |
| 2006 | 19-20 | 0.92× | Older PG |
| 2005 | 20+ | 0.85× | Significant penalty |

---

## 4. Factor Analysis

### 4.1 Factor Performance (Jan 21-24, 2026)

Based on analyzing which factors correctly predicted outcomes:

| Factor | Games Correct | Accuracy | Statistical Significance |
|--------|---------------|----------|-------------------------|
| MHR Rating | 23/35 | 65.7% | Moderate (p < 0.10) |
| Top Player | 23/35 | 65.7% | Moderate (p < 0.10) |
| Recent Form | 21/35 | 60.0% | Weak (p < 0.20) |
| Home Advantage | 21/35 | 60.0% | Weak (p < 0.20) |
| ProdigyPoints | 19/35 | 54.3% | Not significant |
| Win Percentage | 16/35 | 45.7% | Not significant |
| Expert Rank | 16/35 | 45.7% | Not significant |
| Goal Differential | 16/35 | 45.7% | Not significant |

### 4.2 Correlation Analysis

| Factor Pair | Correlation | Interpretation |
|-------------|-------------|----------------|
| MHR Rating × Top Player | 0.78 | High - both capture team strength |
| ProdigyPoints × Team OVR | 0.92 | Very High - derived metrics |
| Win % × Form | 0.85 | High - both capture performance |
| Goal Diff × Win % | 0.71 | Moderate - better teams score more |

### 4.3 Factor Independence

Using Principal Component Analysis on the 8 factors:
- PC1 (Team Strength): 45% of variance
- PC2 (Recent Performance): 28% of variance
- PC3 (Situational): 15% of variance
- PC4+ (Noise): 12% of variance

**Implication:** Model could potentially be simplified to 3-4 composite factors.

---

## 5. Machine Learning Analysis

### 5.1 Methodology

**Tools Used:**
- Python 3.13
- scikit-learn (LogisticRegressionCV, StandardScaler)
- Leave-One-Out Cross-Validation

**Approach:**
1. Extract 8 features as normalized differences (home - away)
2. Standardize features (zero mean, unit variance)
3. Train regularized logistic regression with L2 penalty
4. Evaluate using Leave-One-Out CV (best for small samples)

### 5.2 Feature Extraction

```python
features = [
    (home_avg_points - away_avg_points) / 1000,      # ProdigyPoints
    (home_max_points - away_max_points) / 1000,      # Top Player
    (home_total_points - away_total_points) / 10000, # Team Depth
    (home_ovr - away_ovr) / 10,                      # OVR Rating
    home_win_pct - away_win_pct,                     # Win %
    home_goal_diff - away_goal_diff,                 # Goal Diff
    home_form - away_form,                           # Recent Form
    1.0,                                              # Home Advantage (constant)
]
```

### 5.3 Results

**Cross-Validation Performance:**

| Metric | Value |
|--------|-------|
| Training Accuracy | 77.1% |
| 5-Fold CV Accuracy | 65.7% ± 12.3% |
| Leave-One-Out CV Accuracy | 60.0% |
| Best Regularization C | 0.10 |

**Feature Coefficients (Standardized):**

| Feature | Coefficient | Importance |
|---------|-------------|------------|
| Form | 0.312 | 27.1% |
| Win % | 0.311 | 27.1% |
| Team Depth | 0.289 | 25.1% |
| OVR Rating | 0.087 | 7.6% |
| Home Ice | 0.051 | 4.4% |
| Top Player | 0.042 | 3.6% |
| Goal Diff | 0.033 | 2.9% |
| Avg Points | 0.025 | 2.2% |

### 5.4 Key Insights

1. **Overfitting Risk:** Training accuracy (77%) >> LOO-CV accuracy (60%) indicates overfitting with current sample size
2. **Win % Underweighted:** ML suggests Win % should be a top-3 factor, not bottom-3
3. **Home Advantage Overweighted:** Coefficient is small (4.4%) vs 12% weight in v2.0
4. **Form is Important:** Last 5 games performance is highly predictive

### 5.5 Recommendation

**Do NOT fully automate weights yet.** With only 35 games:
- High variance in cross-validation estimates
- Risk of overfitting to noise
- Need 100+ games for reliable ML optimization

**Instead:** Make conservative adjustments based on directional insights:
- Reduce home advantage (clear signal)
- Increase win percentage weight (clear signal)
- Keep other strong factors stable

---

## 6. Weight Optimization Results

### 6.1 Comparison Table

| Factor | v1.0 | v2.0 | v2.1 | ML Optimal* | Direction |
|--------|------|------|------|-------------|-----------|
| MHR Rating | 25% | 30% | 30% | ~15% | ↓ potential |
| Top Player | 5% | 15% | 15% | ~5% | ↓ potential |
| Recent Form | 15% | 15% | 15% | ~25% | ↑ needed |
| Win % | 7% | 2% | 15% | ~25% | ↑ applied |
| Head-to-Head | 5% | 8% | 8% | N/A | - |
| ProdigyPoints | 15% | 10% | 7% | ~5% | ↓ applied |
| Home Advantage | 8% | 12% | 5% | ~5% | ↓ applied |
| Expert Rank | 10% | 5% | 3% | ~5% | ↓ applied |
| Goal Diff | 10% | 3% | 2% | ~5% | ↓ applied |

*ML Optimal based on standardized coefficients with 35-game sample

### 6.2 Prediction Distribution Change

| Metric | v2.0 | v2.1 | Change |
|--------|------|------|--------|
| Home Picks | 56% | 51% | -5% |
| Away Picks | 44% | 49% | +5% |
| High Conf (60%+) | 45% | 33% | -12% |
| Low Conf (<60%) | 55% | 67% | +12% |

**Interpretation:** Model is now more conservative, which should improve calibration.

---

## 7. Error Analysis

### 7.1 Error Patterns (v2.0)

**Total Errors:** 10 out of 35 games (28.6%)

| Error Type | Count | Percentage |
|------------|-------|------------|
| Missed Away Upset | 9 | 90% |
| Missed Home Win | 1 | 10% |

### 7.2 Common Error Scenarios

1. **Strong Away Team vs Moderate Home Team**
   - Model overweighted home advantage
   - Example: Kent (ranked #5) @ Canterbury - predicted Canterbury

2. **Hot Away Team**
   - Model didn't capture recent form properly
   - Teams on winning streaks underestimated

3. **Missing Head-to-Head Data**
   - Rivalry games have psychological factors
   - Historical dominance not captured

### 7.3 Most Confident Errors

| Game | Predicted | Actual | Confidence | Issue |
|------|-----------|--------|------------|-------|
| Groton @ Kent | Kent (home) | Groton | 68% | Strong away team |
| Canterbury @ Salisbury | Salisbury (home) | Canterbury | 72% | Hot streak |
| Hotchkiss @ Taft | Taft (home) | Hotchkiss | 65% | Rivalry game |

---

## 8. Future Improvements

### 8.1 Short-Term (Next 2 Weeks)

- [ ] Collect 50+ more game results
- [ ] Re-run ML analysis with larger sample
- [ ] Add goaltender performance factor
- [ ] Implement rolling form (last 3 vs last 5 games)

### 8.2 Medium-Term (End of Season)

- [ ] Full season analysis (100+ games)
- [ ] Time-weighted performance (recent games matter more)
- [ ] Injury/roster change detection
- [ ] Weather/travel distance factors

### 8.3 Long-Term (Next Season)

- [ ] Neural network ensemble model
- [ ] Real-time odds comparison
- [ ] Player-level contribution modeling
- [ ] Season-over-season learning

### 8.4 Data Collection Priorities

1. **Goaltender Stats:** Save %, GAA by game
2. **Rest Days:** Days since last game
3. **Travel Distance:** Miles between venues
4. **Line Combinations:** Which players played together
5. **Period-by-Period Scoring:** Momentum indicators

---

## 9. Technical Implementation

### 9.1 Key Files

| File | Purpose |
|------|---------|
| `nepsac_prediction_engine.py` | Core prediction model (weights, factors) |
| `prediction_model_optimizer.py` | Scipy-based weight optimization |
| `prediction_model_optimizer_v2.py` | Cross-validated ML optimization |
| `regenerate_predictions.py` | Update BigQuery with new predictions |
| `add_game_results.py` | Record game outcomes |
| `NepsacPastPerformance.tsx` | Frontend display component |

### 9.2 BigQuery Tables

| Table | Purpose |
|-------|---------|
| `nepsac_schedule` | Games with predictions |
| `nepsac_team_rankings` | ProdigyPoints per team |
| `nepsac_standings` | W-L-T, goals, streaks |
| `nepsac_teams` | Team metadata |
| `nepsac_rosters` | Player-team mappings |

### 9.3 API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `getNepsacSchedule` | GET | Upcoming games with predictions |
| `getNepsacPastResults` | GET | Historical prediction accuracy |
| `updateGameResults` | POST | Record game outcomes |

### 9.4 Weight Update Process

1. Collect new game results via `add_game_results.py`
2. Analyze performance with `prediction_model_optimizer_v2.py`
3. Update weights in `nepsac_prediction_engine.py`
4. Regenerate predictions with `regenerate_predictions.py`
5. Update frontend weights in `NepsacPastPerformance.tsx`
6. Commit and push changes
7. Verify via `getNepsacPastResults` API

---

## Appendix A: Weight History JSON

```json
{
  "v1.0": {
    "date": "2026-01-19",
    "weights": {
      "mhr_rating": 0.25,
      "prodigy_points": 0.15,
      "recent_form": 0.15,
      "expert_rank": 0.10,
      "goal_diff": 0.10,
      "home_advantage": 0.08,
      "win_pct": 0.07,
      "top_player": 0.05,
      "head_to_head": 0.05
    },
    "home_advantage_factor": 0.58
  },
  "v2.0": {
    "date": "2026-01-22",
    "weights": {
      "mhr_rating": 0.30,
      "top_player": 0.15,
      "recent_form": 0.15,
      "home_advantage": 0.12,
      "prodigy_points": 0.10,
      "head_to_head": 0.08,
      "expert_rank": 0.05,
      "goal_diff": 0.03,
      "win_pct": 0.02
    },
    "home_advantage_factor": 0.58
  },
  "v2.1": {
    "date": "2026-01-24",
    "weights": {
      "mhr_rating": 0.30,
      "top_player": 0.15,
      "recent_form": 0.15,
      "win_pct": 0.15,
      "head_to_head": 0.08,
      "prodigy_points": 0.07,
      "home_advantage": 0.05,
      "expert_rank": 0.03,
      "goal_diff": 0.02
    },
    "home_advantage_factor": 0.55
  }
}
```

---

## Appendix B: Performance Tracking

### Weekly Accuracy Log

| Week | Games | Correct | Incorrect | Ties | Accuracy | Model |
|------|-------|---------|-----------|------|----------|-------|
| Jan 19 | 2 | - | - | - | N/A | v1.0 |
| Jan 21 | 22 | 16 | 5 | 1 | 76.2% | v2.0 |
| Jan 24 | 16 | 9 | 5 | 2 | 64.3% | v2.0 |
| **Total** | **38** | **25** | **10** | **3** | **71.4%** | - |

### Model Version Performance

| Version | Games | Accuracy | Home % | Away % |
|---------|-------|----------|--------|--------|
| v1.0 | 0 | - | - | - |
| v2.0 | 38 | 71.4% | 56% | 44% |
| v2.1 | TBD | TBD | 51% | 49% |

---

## Appendix C: Glossary

| Term | Definition |
|------|------------|
| **ProdigyPoints** | Proprietary player rating based on EP views, stats, draft position |
| **MHR Rating** | MyHockeyRankings ELO-style mathematical rating |
| **OVR** | EA Sports style overall rating (70-99 scale) |
| **LOO-CV** | Leave-One-Out Cross-Validation |
| **Form Score** | Recent performance metric (0-1 scale) |
| **Confidence** | Model's certainty in prediction (50-99%) |

---

*Document maintained by ProdigyChain Analytics Team*
*For white paper inquiries, contact: [info@prodigychain.com]*

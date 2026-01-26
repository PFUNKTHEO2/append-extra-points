"""
NEPSAC Player Import & Analytics
=================================
Import 983 NEPSAC players and run analytics for Scouty.

Expected data columns:
- player_name (required)
- team (required)
- position (F/D/G)
- birth_year or grad_year
- games_played (GP)
- goals (G)
- assists (A)
- points (PTS) or calculated from G+A
- plus_minus (+/-)
- pim (PIM)
- ppg (optional, calculated if not provided)

For Goalies:
- wins, losses, ties
- gaa (goals against average)
- save_pct (save percentage)
- shutouts
"""

import os
import csv
import json
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from google.cloud import bigquery

PROJECT_ID = "prodigy-ranking"

# Team name normalization mapping
TEAM_ALIASES = {
    "AOF": "Avon Old Farms",
    "Avon": "Avon Old Farms",
    "KUA": "Kimball Union",
    "Kimball Union Academy": "Kimball Union",
    "NMH": "Northfield Mount Hermon",
    "Northfield-Mount Hermon": "Northfield Mount Hermon",
    "Loomis": "Loomis Chaffee",
    "Williston": "Williston-Northampton",
    "Frederick Gunn": "The Gunnery",
    "Gunnery": "The Gunnery",
    "St. Marks": "St. Mark's",
    "St Marks": "St. Mark's",
    "St. Sebastian's": "St. Sebastian's",
    "St Sebastians": "St. Sebastian's",
    "BB&N": "Buckingham Browne & Nichols",
    "BBN": "Buckingham Browne & Nichols",
    "T-P": "Trinity-Pawling",
    "TP": "Trinity-Pawling",
    "Nobles": "Noble & Greenough",
    "Choate": "Choate Rosemary Hall",
    "Hotchkiss": "Hotchkiss School",
    "Kent": "Kent School",
    "Salisbury": "Salisbury School",
    "Taft": "Taft School",
    "Berkshire": "Berkshire School",
    "Deerfield": "Deerfield Academy",
    "Westminster": "Westminster School",
    "Canterbury": "Canterbury School",
    "Pomfret": "Pomfret School",
    "Brunswick": "Brunswick School",
    "Millbrook": "Millbrook School",
    "Groton": "Groton School",
    "Middlesex": "Middlesex School",
    "Milton": "Milton Academy",
    "Andover": "Phillips Academy Andover",
    "Exeter": "Phillips Exeter Academy",
    "Tabor": "Tabor Academy",
    "Thayer": "Thayer Academy",
    "Cushing": "Cushing Academy",
    "Holderness": "Holderness School",
    "Tilton": "Tilton School",
    "Proctor": "Proctor Academy",
    "New Hampton": "New Hampton School",
    "Brewster": "Brewster Academy",
    "Hebron": "Hebron Academy",
    "Kents Hill": "Kents Hill School",
    "Winchendon": "Winchendon School",
    "Dexter": "Dexter Southfield",
    "Rivers": "Rivers School",
    "Belmont Hill": "Belmont Hill School",
    "St. Paul's": "St. Paul's School",
    "St Pauls": "St. Paul's School",
    "Lawrence": "Lawrence Academy",
    "Governors": "Governor's Academy",
    "Governor's": "Governor's Academy",
    "Brooks": "Brooks School",
    "Pingree": "Pingree School",
    "Berwick": "Berwick Academy",
    "Portsmouth Abbey": "Portsmouth Abbey School",
    "Roxbury Latin": "Roxbury Latin School",
    "Worcester": "Worcester Academy",
    "Austin Prep": "Austin Preparatory School",
    "Mount St. Charles": "Mount Saint Charles Academy",
    "St. George's": "St. George's School",
    "St Georges": "St. George's School",
    "Albany": "Albany Academy",
    "Hoosac": "Hoosac School",
    "Vermont Academy": "Vermont Academy",
    "Stanstead": "Stanstead College",
    "Hill School": "The Hill School",
    "Lawrenceville": "Lawrenceville School",
}


def normalize_team_name(team: str) -> str:
    """Normalize team name to standard format."""
    if not team:
        return "Unknown"
    team = team.strip()
    return TEAM_ALIASES.get(team, team)


def calculate_ppg(goals: int, assists: int, gp: int) -> float:
    """Calculate points per game."""
    if gp == 0:
        return 0.0
    return round((goals + assists) / gp, 2)


def load_players_from_csv(filepath: str) -> pd.DataFrame:
    """Load player data from CSV file."""
    df = pd.read_csv(filepath)

    # Standardize column names
    column_mapping = {
        'Player': 'player_name',
        'Name': 'player_name',
        'player': 'player_name',
        'Team': 'team',
        'School': 'team',
        'Pos': 'position',
        'Position': 'position',
        'GP': 'games_played',
        'Games': 'games_played',
        'G': 'goals',
        'Goals': 'goals',
        'A': 'assists',
        'Assists': 'assists',
        'PTS': 'points',
        'Pts': 'points',
        'Points': 'points',
        'P': 'points',
        '+/-': 'plus_minus',
        'PM': 'plus_minus',
        'PIM': 'pim',
        'Pen': 'pim',
        'Year': 'birth_year',
        'Birth Year': 'birth_year',
        'Grad': 'grad_year',
        'Grad Year': 'grad_year',
        'Class': 'grad_year',
        # Goalie stats
        'W': 'wins',
        'L': 'losses',
        'T': 'ties',
        'GAA': 'gaa',
        'SV%': 'save_pct',
        'Save%': 'save_pct',
        'SO': 'shutouts',
        'Shutouts': 'shutouts',
    }

    df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})

    # Normalize team names
    if 'team' in df.columns:
        df['team'] = df['team'].apply(normalize_team_name)

    # Calculate points if not provided
    if 'points' not in df.columns and 'goals' in df.columns and 'assists' in df.columns:
        df['points'] = df['goals'].fillna(0) + df['assists'].fillna(0)

    # Calculate PPG
    if 'games_played' in df.columns:
        df['ppg'] = df.apply(
            lambda row: calculate_ppg(
                row.get('goals', 0) or 0,
                row.get('assists', 0) or 0,
                row.get('games_played', 1) or 1
            ), axis=1
        )
        df['gpg'] = df.apply(
            lambda row: round((row.get('goals', 0) or 0) / max(row.get('games_played', 1) or 1, 1), 2),
            axis=1
        )
        df['apg'] = df.apply(
            lambda row: round((row.get('assists', 0) or 0) / max(row.get('games_played', 1) or 1, 1), 2),
            axis=1
        )

    return df


def load_players_from_excel(filepath: str, sheet_name: str = None) -> pd.DataFrame:
    """Load player data from Excel file."""
    if sheet_name:
        df = pd.read_excel(filepath, sheet_name=sheet_name)
    else:
        df = pd.read_excel(filepath)

    # Use same processing as CSV
    return load_players_from_csv(df) if isinstance(df, str) else df


def match_to_elite_prospects(players_df: pd.DataFrame) -> pd.DataFrame:
    """Match NEPSAC players to Elite Prospects IDs."""
    try:
        client = bigquery.Client(project=PROJECT_ID)

        # Get all prep school players from ProdigyRanking
        query = """
        SELECT
            player_id,
            player_name,
            position,
            birth_year,
            current_team,
            current_league,
            nationality_name
        FROM `prodigy-ranking.algorithm_core.player_stats`
        WHERE LOWER(current_league) LIKE '%prep%'
           OR LOWER(current_league) LIKE '%nepsac%'
           OR LOWER(current_league) LIKE '%school%'
           OR LOWER(current_league) LIKE '%ushs%'
        """

        ep_players = client.query(query).to_dataframe()

        # Create matching keys
        players_df['match_key'] = players_df['player_name'].str.lower().str.strip()
        ep_players['match_key'] = ep_players['player_name'].str.lower().str.strip()

        # Merge on name
        merged = players_df.merge(
            ep_players[['player_id', 'player_name', 'match_key', 'nationality_name']],
            on='match_key',
            how='left',
            suffixes=('', '_ep')
        )

        matched = merged[merged['player_id'].notna()]
        unmatched = merged[merged['player_id'].isna()]

        print(f"Matched: {len(matched)} players")
        print(f"Unmatched: {len(unmatched)} players")

        return merged

    except Exception as e:
        print(f"Error matching to Elite Prospects: {e}")
        return players_df


def generate_analytics(df: pd.DataFrame) -> Dict:
    """Generate comprehensive analytics from player data."""
    analytics = {
        "generated_at": datetime.now().isoformat(),
        "total_players": len(df),
    }

    # Position breakdown
    if 'position' in df.columns:
        analytics["by_position"] = df['position'].value_counts().to_dict()

    # Team breakdown
    if 'team' in df.columns:
        analytics["by_team"] = df['team'].value_counts().to_dict()
        analytics["teams_count"] = df['team'].nunique()

    # Scoring leaders (Skaters)
    skaters = df[df['position'].isin(['F', 'D', 'LW', 'RW', 'C', 'W'])] if 'position' in df.columns else df

    if 'points' in df.columns:
        analytics["scoring_leaders"] = skaters.nlargest(25, 'points')[
            ['player_name', 'team', 'position', 'games_played', 'goals', 'assists', 'points', 'ppg']
        ].to_dict('records')

    if 'goals' in df.columns:
        analytics["goal_leaders"] = skaters.nlargest(15, 'goals')[
            ['player_name', 'team', 'goals', 'games_played', 'gpg']
        ].to_dict('records')

    if 'assists' in df.columns:
        analytics["assist_leaders"] = skaters.nlargest(15, 'assists')[
            ['player_name', 'team', 'assists', 'games_played', 'apg']
        ].to_dict('records')

    if 'ppg' in df.columns:
        # Min 5 games for PPG leaders
        qualified = skaters[skaters['games_played'] >= 5] if 'games_played' in skaters.columns else skaters
        analytics["ppg_leaders"] = qualified.nlargest(15, 'ppg')[
            ['player_name', 'team', 'ppg', 'points', 'games_played']
        ].to_dict('records')

    # Defensemen leaders
    defensemen = df[df['position'] == 'D'] if 'position' in df.columns else pd.DataFrame()
    if len(defensemen) > 0 and 'points' in defensemen.columns:
        analytics["top_defensemen"] = defensemen.nlargest(10, 'points')[
            ['player_name', 'team', 'goals', 'assists', 'points', 'ppg']
        ].to_dict('records')

    # Goalies
    goalies = df[df['position'] == 'G'] if 'position' in df.columns else pd.DataFrame()
    if len(goalies) > 0:
        if 'gaa' in goalies.columns:
            analytics["top_goalies_gaa"] = goalies.nsmallest(10, 'gaa')[
                ['player_name', 'team', 'wins', 'losses', 'gaa', 'save_pct']
            ].to_dict('records')
        if 'save_pct' in goalies.columns:
            analytics["top_goalies_svpct"] = goalies.nlargest(10, 'save_pct')[
                ['player_name', 'team', 'wins', 'losses', 'gaa', 'save_pct']
            ].to_dict('records')

    # By grad year / birth year
    if 'grad_year' in df.columns:
        analytics["by_grad_year"] = df['grad_year'].value_counts().sort_index().to_dict()
    if 'birth_year' in df.columns:
        analytics["by_birth_year"] = df['birth_year'].value_counts().sort_index().to_dict()

    # Team scoring
    if 'team' in df.columns and 'points' in df.columns:
        team_scoring = df.groupby('team').agg({
            'points': 'sum',
            'goals': 'sum',
            'assists': 'sum',
            'player_name': 'count'
        }).rename(columns={'player_name': 'player_count'})
        team_scoring['ppg_team'] = round(team_scoring['points'] / team_scoring['player_count'], 2)
        analytics["team_scoring"] = team_scoring.sort_values('points', ascending=False).head(20).to_dict('index')

    return analytics


def generate_scouty_report(df: pd.DataFrame, analytics: Dict) -> str:
    """Generate Scouty's comprehensive NEPSAC report."""
    report = []
    report.append("=" * 70)
    report.append("SCOUTY'S NEPSAC PLAYER ANALYTICS REPORT")
    report.append(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}")
    report.append(f"Total Players Analyzed: {analytics['total_players']}")
    report.append("=" * 70)
    report.append("")

    # Scoring Leaders
    report.append("TOP 25 SCORING LEADERS")
    report.append("-" * 70)
    report.append(f"{'Rank':<5}{'Player':<25}{'Team':<20}{'GP':<5}{'G':<5}{'A':<5}{'PTS':<6}{'PPG':<6}")
    report.append("-" * 70)

    for i, player in enumerate(analytics.get('scoring_leaders', [])[:25], 1):
        report.append(
            f"{i:<5}{player['player_name'][:24]:<25}{player['team'][:19]:<20}"
            f"{player.get('games_played', 0):<5}{player.get('goals', 0):<5}"
            f"{player.get('assists', 0):<5}{player.get('points', 0):<6}"
            f"{player.get('ppg', 0):<6.2f}"
        )

    report.append("")

    # Top Defensemen
    if analytics.get('top_defensemen'):
        report.append("TOP 10 DEFENSEMEN")
        report.append("-" * 60)
        for i, player in enumerate(analytics['top_defensemen'][:10], 1):
            report.append(
                f"{i}. {player['player_name']} ({player['team']}) - "
                f"{player.get('goals', 0)}G {player.get('assists', 0)}A {player.get('points', 0)}PTS"
            )
        report.append("")

    # PPG Leaders
    if analytics.get('ppg_leaders'):
        report.append("PPG LEADERS (min 5 GP)")
        report.append("-" * 60)
        for i, player in enumerate(analytics['ppg_leaders'][:10], 1):
            report.append(
                f"{i}. {player['player_name']} ({player['team']}) - "
                f"{player.get('ppg', 0):.2f} PPG ({player.get('points', 0)} pts in {player.get('games_played', 0)} GP)"
            )
        report.append("")

    # Top Goalies
    if analytics.get('top_goalies_gaa'):
        report.append("TOP GOALIES BY GAA")
        report.append("-" * 60)
        for i, player in enumerate(analytics['top_goalies_gaa'][:10], 1):
            report.append(
                f"{i}. {player['player_name']} ({player['team']}) - "
                f"{player.get('gaa', 0):.2f} GAA, {player.get('save_pct', 0):.3f} SV%"
            )
        report.append("")

    # Team Scoring
    if analytics.get('team_scoring'):
        report.append("TEAM SCORING TOTALS")
        report.append("-" * 60)
        for i, (team, stats) in enumerate(list(analytics['team_scoring'].items())[:15], 1):
            report.append(
                f"{i}. {team}: {stats['points']} PTS ({stats['goals']}G, {stats['assists']}A) - "
                f"{stats['player_count']} players"
            )
        report.append("")

    report.append("=" * 70)
    report.append("END OF SCOUTY REPORT")
    report.append("=" * 70)

    return "\n".join(report)


def process_nepsac_data(filepath: str, output_prefix: str = "nepsac_983"):
    """Main function to process NEPSAC player data."""
    print(f"Loading data from {filepath}...")

    # Determine file type and load
    if filepath.endswith('.csv'):
        df = load_players_from_csv(filepath)
    elif filepath.endswith(('.xlsx', '.xls')):
        df = pd.read_excel(filepath)
        # Apply same column mapping
        df = load_players_from_csv(filepath) if filepath.endswith('.csv') else df
    else:
        print(f"Unsupported file format: {filepath}")
        return

    print(f"Loaded {len(df)} players")
    print(f"Columns: {list(df.columns)}")

    # Match to Elite Prospects
    print("\nMatching to Elite Prospects database...")
    df = match_to_elite_prospects(df)

    # Generate analytics
    print("\nGenerating analytics...")
    analytics = generate_analytics(df)

    # Generate Scouty report
    print("\nGenerating Scouty report...")
    report = generate_scouty_report(df, analytics)
    print(report)

    # Export files
    print("\nExporting files...")

    # CSV export
    df.to_csv(f"{output_prefix}_players.csv", index=False)
    print(f"  - {output_prefix}_players.csv")

    # Analytics JSON
    with open(f"{output_prefix}_analytics.json", 'w') as f:
        json.dump(analytics, f, indent=2, default=str)
    print(f"  - {output_prefix}_analytics.json")

    # Scouty report
    with open(f"{output_prefix}_scouty_report.txt", 'w') as f:
        f.write(report)
    print(f"  - {output_prefix}_scouty_report.txt")

    print("\nProcessing complete!")
    return df, analytics


# Quick test with sample data
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        process_nepsac_data(filepath)
    else:
        print("NEPSAC Player Import Tool")
        print("=" * 40)
        print("\nUsage: python nepsac_player_import.py <path_to_data_file>")
        print("\nSupported formats: .csv, .xlsx, .xls")
        print("\nExpected columns:")
        print("  - Player/Name (required)")
        print("  - Team/School (required)")
        print("  - Position (F/D/G)")
        print("  - GP/Games")
        print("  - G/Goals")
        print("  - A/Assists")
        print("  - PTS/Points")
        print("  - +/-")
        print("  - PIM")
        print("\nFor goalies: W, L, T, GAA, SV%, SO")
        print("\nWaiting for data upload...")

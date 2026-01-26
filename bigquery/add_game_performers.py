#!/usr/bin/env python3
"""
Add game performers to BigQuery for NEPSAC Top Performers API.
This script allows quick entry of box score stats after games.

Usage:
  python add_game_performers.py --game-id game_0045 --date 2026-01-24

  Then follow the prompts to enter player stats.
"""

import argparse
import json
import requests
from datetime import datetime
from google.cloud import bigquery

# Cloud Function endpoint for adding performers
API_ENDPOINT = "https://us-central1-prodigy-ranking.cloudfunctions.net/addNepsacGamePerformers"

# Team ID lookup (short name -> team_id)
TEAM_LOOKUP = {
    "avon": "avon-old-farms",
    "salisbury": "salisbury-school",
    "canterbury": "canterbury-school",
    "taft": "taft-school",
    "hotchkiss": "hotchkiss-school",
    "choate": "choate-rosemary-hall",
    "loomis": "loomis-chaffee-school",
    "westminster": "westminster-school",
    "trinity-pawling": "trinity-pawling-school",
    "kent": "kent-school",
    "berkshire": "berkshire-school",
    "millbrook": "millbrook-school",
    "pomfret": "pomfret-school",
    "kua": "kimball-union-academy",
    "holderness": "holderness-school",
    "proctor": "proctor-academy",
    "tilton": "tilton-school",
    "new-hampton": "new-hampton-school",
    "brewster": "brewster-academy",
    "cushing": "cushing-academy",
    "winchendon": "winchendon-school",
    "vermont": "vermont-academy",
    "northfield": "northfield-mount-hermon",
    "deerfield": "deerfield-academy",
    "exeter": "phillips-exeter-academy",
    "andover": "phillips-andover-academy",
    "st-pauls": "st-pauls-school",
    "nobles": "noble-greenough-school",
    "milton": "milton-academy",
    "bb&n": "buckingham-browne-nichols",
    "rivers": "rivers-school",
    "thayer": "thayer-academy",
    "governor": "governors-academy",
    "lawrence": "lawrence-academy",
    "st-marks": "st-marks-school",
    "st-sebastians": "st-sebastians-school",
    "belmont-hill": "belmont-hill-school",
    "middlesex": "middlesex-school",
    "groton": "groton-school",
    "brooks": "brooks-school",
    "dexter": "dexter-southfield-school",
}


def get_team_id(name: str) -> str:
    """Convert team short name to full team_id."""
    name_lower = name.lower().strip()

    # Direct lookup
    if name_lower in TEAM_LOOKUP:
        return TEAM_LOOKUP[name_lower]

    # Check if already a full team_id
    if "-" in name_lower:
        return name_lower

    # Fuzzy match
    for key, value in TEAM_LOOKUP.items():
        if name_lower in key or key in name_lower:
            return value

    return name_lower  # Return as-is if no match


def parse_skater_line(line: str, team_id: str) -> dict:
    """
    Parse a skater stat line.
    Format: "Name, Position, G-A" or "Name, G-A" (assumes F)
    Examples:
      "Seamus McMakin, F, 2-2"
      "John Smith, D, 0-3"
      "Mike Jones, 1-1"
    """
    parts = [p.strip() for p in line.split(",")]

    if len(parts) == 3:
        name, position, stats = parts
    elif len(parts) == 2:
        name, stats = parts
        position = "F"  # Default to forward
    else:
        raise ValueError(f"Invalid format: {line}. Expected 'Name, Position, G-A' or 'Name, G-A'")

    goals, assists = stats.split("-")

    return {
        "rosterName": name,
        "teamId": team_id,
        "position": position.upper(),
        "goals": int(goals),
        "assists": int(assists)
    }


def parse_goalie_line(line: str, team_id: str) -> dict:
    """
    Parse a goalie stat line.
    Format: "Name, Saves, W/L/OTL" or "Name, Saves, SO" for shutout
    Examples:
      "John Smith, 32, W"
      "Mike Jones, 28, L"
      "Bob Wilson, 35, SO"
    """
    parts = [p.strip() for p in line.split(",")]

    if len(parts) != 3:
        raise ValueError(f"Invalid goalie format: {line}. Expected 'Name, Saves, W/L/OTL/SO'")

    name, saves, result = parts
    result = result.upper()

    performer = {
        "rosterName": name,
        "teamId": team_id,
        "position": "G",
        "saves": int(saves),
        "isShutout": result == "SO",
        "isWin": result in ["W", "SO"],
        "isLoss": result == "L",
        "isOtl": result == "OTL"
    }

    return performer


def add_via_api(game_id: str, game_date: str, performers: list, source: str = "manual"):
    """Add performers via Cloud Function API."""
    payload = {
        "gameId": game_id,
        "gameDate": game_date,
        "source": source,
        "performers": performers
    }

    print(f"\nSending {len(performers)} performers to API...")
    print(json.dumps(payload, indent=2))

    response = requests.post(API_ENDPOINT, json=payload)

    if response.status_code == 200:
        result = response.json()
        print(f"\n✅ Success: {result['message']}")
        return True
    else:
        print(f"\n❌ Error: {response.status_code}")
        print(response.text)
        return False


def add_via_bigquery(game_id: str, game_date: str, performers: list, source: str = "manual"):
    """Add performers directly to BigQuery."""
    client = bigquery.Client(project="prodigy-ranking")

    rows = []
    for idx, p in enumerate(performers):
        goals = p.get("goals", 0)
        assists = p.get("assists", 0)

        row = {
            "performer_id": f"{game_id}_{idx + 1}",
            "game_id": game_id,
            "game_date": game_date,
            "player_id": p.get("playerId"),
            "roster_name": p["rosterName"],
            "team_id": p["teamId"],
            "position": p.get("position"),
            "goals": goals,
            "assists": assists,
            "points": goals + assists,
            "plus_minus": p.get("plusMinus"),
            "pim": p.get("pim"),
            "shots": p.get("shots"),
            "saves": p.get("saves"),
            "goals_against": p.get("goalsAgainst"),
            "shots_faced": p.get("shotsFaced"),
            "save_pct": p.get("savePct"),
            "is_shutout": p.get("isShutout", False),
            "is_win": p.get("isWin"),
            "is_loss": p.get("isLoss"),
            "is_otl": p.get("isOtl"),
            "is_star_of_game": p.get("isStarOfGame", False),
            "star_rank": p.get("starRank"),
            "source": source,
            "notes": p.get("notes"),
        }
        rows.append(row)

    table_id = "prodigy-ranking.algorithm_core.nepsac_game_performers"

    # Delete existing for this game
    delete_query = f"DELETE FROM `{table_id}` WHERE game_id = '{game_id}'"
    client.query(delete_query).result()

    # Insert new rows
    errors = client.insert_rows_json(table_id, rows)

    if errors:
        print(f"❌ BigQuery errors: {errors}")
        return False
    else:
        print(f"✅ Added {len(rows)} performers to BigQuery")
        return True


def interactive_mode(game_id: str, game_date: str):
    """Interactive mode for entering stats."""
    print(f"\n📊 Adding performers for game {game_id} on {game_date}")
    print("=" * 50)

    performers = []

    # Get team 1
    team1_name = input("\nTeam 1 (short name, e.g. 'salisbury'): ").strip()
    team1_id = get_team_id(team1_name)
    print(f"  → Using team_id: {team1_id}")

    print("\nEnter skaters for Team 1 (format: 'Name, Position, G-A')")
    print("Enter blank line when done.")
    while True:
        line = input("  Skater: ").strip()
        if not line:
            break
        try:
            performer = parse_skater_line(line, team1_id)
            performers.append(performer)
            print(f"    ✓ {performer['rosterName']}: {performer['goals']}G-{performer['assists']}A")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    print("\nEnter goalie for Team 1 (format: 'Name, Saves, W/L/SO')")
    goalie_line = input("  Goalie: ").strip()
    if goalie_line:
        try:
            performer = parse_goalie_line(goalie_line, team1_id)
            performers.append(performer)
            result = "SO" if performer["isShutout"] else "W" if performer["isWin"] else "L"
            print(f"    ✓ {performer['rosterName']}: {performer['saves']} saves, {result}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    # Get team 2
    team2_name = input("\nTeam 2 (short name, e.g. 'avon'): ").strip()
    team2_id = get_team_id(team2_name)
    print(f"  → Using team_id: {team2_id}")

    print("\nEnter skaters for Team 2 (format: 'Name, Position, G-A')")
    print("Enter blank line when done.")
    while True:
        line = input("  Skater: ").strip()
        if not line:
            break
        try:
            performer = parse_skater_line(line, team2_id)
            performers.append(performer)
            print(f"    ✓ {performer['rosterName']}: {performer['goals']}G-{performer['assists']}A")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    print("\nEnter goalie for Team 2 (format: 'Name, Saves, W/L/SO')")
    goalie_line = input("  Goalie: ").strip()
    if goalie_line:
        try:
            performer = parse_goalie_line(goalie_line, team2_id)
            performers.append(performer)
            result = "SO" if performer["isShutout"] else "W" if performer["isWin"] else "L"
            print(f"    ✓ {performer['rosterName']}: {performer['saves']} saves, {result}")
        except Exception as e:
            print(f"    ✗ Error: {e}")

    # Summary
    print(f"\n📋 Summary: {len(performers)} performers")
    for p in performers:
        if p["position"] == "G":
            print(f"  - {p['rosterName']} ({p['teamId']}): {p['saves']} saves")
        else:
            print(f"  - {p['rosterName']} ({p['teamId']}): {p['goals']}G-{p['assists']}A")

    # Confirm and submit
    confirm = input("\nSubmit? (y/n): ").strip().lower()
    if confirm == "y":
        return performers
    else:
        print("Cancelled.")
        return None


def main():
    parser = argparse.ArgumentParser(description="Add NEPSAC game performers")
    parser.add_argument("--game-id", required=True, help="Game ID (e.g., game_0045)")
    parser.add_argument("--date", required=True, help="Game date (YYYY-MM-DD)")
    parser.add_argument("--source", default="manual", help="Data source (manual, elite_prospects, neutral_zone)")
    parser.add_argument("--method", default="api", choices=["api", "bigquery"], help="Submission method")
    parser.add_argument("--json", help="JSON file with performers data (skip interactive mode)")

    args = parser.parse_args()

    # Validate date
    try:
        datetime.strptime(args.date, "%Y-%m-%d")
    except ValueError:
        print("Error: Invalid date format. Use YYYY-MM-DD")
        return

    if args.json:
        # Load from JSON file
        with open(args.json, "r") as f:
            performers = json.load(f)
    else:
        # Interactive mode
        performers = interactive_mode(args.game_id, args.date)

    if performers:
        if args.method == "api":
            add_via_api(args.game_id, args.date, performers, args.source)
        else:
            add_via_bigquery(args.game_id, args.date, performers, args.source)


if __name__ == "__main__":
    main()

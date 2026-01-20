"""
Generate NEPSAC Matchup Page HTML with embedded data and Wednesday schedule
"""
import csv
import json
from collections import defaultdict

# Read standings data (for records)
standings_by_team = {}
with open('nepsac_week_jan19.json', 'r', encoding='utf-8') as f:
    week_data = json.load(f)
    for team_standing in week_data.get('standings', []):
        team_name = team_standing['team']
        standings_by_team[team_name] = {
            'wins': team_standing['wins'],
            'losses': team_standing['losses'],
            'ties': team_standing['ties'],
            'win_pct': team_standing['win_pct'],
            'division': team_standing.get('division', '')
        }

# Read logo URLs (use GitHub URLs for standalone HTML)
logos_by_team = {}
try:
    with open('nepsac_logos_github.json', 'r', encoding='utf-8') as f:
        logos_by_team = json.load(f)
    print(f"Loaded {len(logos_by_team)} logo URLs (GitHub)")
except FileNotFoundError:
    try:
        with open('nepsac_logos.json', 'r', encoding='utf-8') as f:
            logos_by_team = json.load(f)
        print(f"Loaded {len(logos_by_team)} logo URLs (relative)")
    except FileNotFoundError:
        print("No nepsac_logos.json found, using initials for all teams")

# Read player images from players table
player_images = {}
try:
    with open('hockey_players_LATEST_SYNC.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            player_id = row.get('id', '')
            image_url = row.get('image_url', '')
            if player_id and image_url:
                player_images[player_id] = image_url
    print(f"Loaded {len(player_images)} player images")
except FileNotFoundError:
    print("No hockey_players_LATEST_SYNC.csv found, using fallback avatars")

# Read roster data
players_by_team = defaultdict(list)
with open('nepsac_roster_matches.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row['roster_team']
        try:
            points = float(row['total_points']) if row['total_points'] else 0
        except:
            points = 0

        player_id = row.get('db_player_id', '')
        players_by_team[team].append({
            'name': row['roster_name'],
            'position': row['roster_position'],
            'grad_year': row['roster_grad_year'],
            'points': points,
            'db_name': row.get('db_name', ''),
            'player_id': player_id,
            'image_url': player_images.get(player_id, '')
        })

# Read team rankings
teams_data = {}
with open('nepsac_team_rankings_full.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        team = row['team']
        standing = standings_by_team.get(team, {})
        teams_data[team] = {
            'name': team,  # Include team name for logo rendering
            'rank': int(row['rank']),
            'roster_size': int(row['roster_size']),
            'matched': int(row['matched']),
            'avg_points': float(row['avg_points']),
            'total_points': float(row['total_points']),
            'max_points': float(row['max_points']),
            'wins': standing.get('wins', 0),
            'losses': standing.get('losses', 0),
            'ties': standing.get('ties', 0),
            'win_pct': standing.get('win_pct', 0),
            'division': standing.get('division', ''),
            'logo': logos_by_team.get(team, ''),
            'players': []
        }

# Add top 6 players to each team (sorted by points)
for team, players in players_by_team.items():
    if team in teams_data:
        sorted_players = sorted(players, key=lambda x: x['points'], reverse=True)[:6]
        teams_data[team]['players'] = sorted_players

# Read schedule for Wednesday games
wednesday_games = []
with open('nepsac_schedule_jan19.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['date'] == '2026-01-22':  # Wednesday Jan 22
            wednesday_games.append({
                'away': row['away'],
                'home': row['home'],
                'time': row['time'],
                'venue': row['venue'],
                'predicted_winner': row['predicted_winner'],
                'confidence': int(row['confidence']) if row['confidence'] else 50
            })
        elif row['date'] == '2026-01-21':  # Tuesday Jan 21
            wednesday_games.append({
                'away': row['away'],
                'home': row['home'],
                'time': row['time'],
                'venue': row['venue'],
                'predicted_winner': row['predicted_winner'],
                'confidence': int(row['confidence']) if row['confidence'] else 50
            })

# If no Wednesday games, use Tuesday games
if not wednesday_games:
    with open('nepsac_schedule_jan19.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['date'] == '2026-01-21':
                wednesday_games.append({
                    'away': row['away'],
                    'home': row['home'],
                    'time': row['time'],
                    'venue': row['venue'],
                    'predicted_winner': row['predicted_winner'],
                    'confidence': int(row['confidence']) if row['confidence'] else 50
                })

# Find max points for OVR conversion
all_points = [p['points'] for players in players_by_team.values() for p in players if p['points'] > 0]
max_points = max(all_points) if all_points else 5000

# Generate JSON
teams_json = json.dumps(teams_data, indent=2)
teams_list = sorted(teams_data.keys())
teams_list_json = json.dumps(teams_list)
games_json = json.dumps(wednesday_games, indent=2)

# Generate HTML
html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEPSAC Team Matchup - EA Sports Style</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        :root {{
            --bg-dark: #0a0a0f;
            --bg-panel: rgba(20, 20, 30, 0.8);
            --bg-card: rgba(25, 25, 40, 0.9);
            --accent-pink: #d946ef;
            --accent-purple: #8b5cf6;
            --accent-cyan: #06b6d4;
            --accent-green: #22c55e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --gold: #ffd700;
            --gold-dark: #b8860b;
            --silver: #c0c0c0;
            --silver-dark: #808080;
            --bronze: #cd7f32;
            --bronze-dark: #8b4513;
        }}

        body {{
            font-family: 'Rajdhani', sans-serif;
            background: var(--bg-dark);
            min-height: 100vh;
            color: var(--text-primary);
            overflow-x: hidden;
        }}

        /* Animated background */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background:
                radial-gradient(ellipse at 20% 20%, rgba(139, 92, 246, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(217, 70, 239, 0.15) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.1) 0%, transparent 50%);
            pointer-events: none;
            z-index: 0;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }}

        /* Header */
        .header {{
            text-align: center;
            padding: 30px 0;
            margin-bottom: 30px;
        }}

        .mascot-image {{
            max-width: 200px;
            height: auto;
            margin-bottom: 15px;
            filter: drop-shadow(0 0 20px rgba(217, 70, 239, 0.5));
        }}

        .header h1 {{
            font-family: 'Orbitron', sans-serif;
            font-size: 3rem;
            font-weight: 900;
            text-transform: uppercase;
            letter-spacing: 4px;
            background: linear-gradient(135deg, var(--accent-pink), var(--accent-purple), var(--accent-cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-shadow: 0 0 40px rgba(139, 92, 246, 0.5);
            animation: glow 2s ease-in-out infinite alternate;
        }}

        @keyframes glow {{
            from {{ filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.5)); }}
            to {{ filter: drop-shadow(0 0 30px rgba(217, 70, 239, 0.7)); }}
        }}

        .header .subtitle {{
            font-size: 1.5rem;
            color: var(--text-secondary);
            margin-top: 10px;
            letter-spacing: 8px;
        }}

        .header .date-badge {{
            display: inline-block;
            margin-top: 15px;
            padding: 8px 25px;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink));
            border-radius: 25px;
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            font-weight: 700;
            letter-spacing: 2px;
        }}

        /* Glass Panel */
        .glass-panel {{
            background: var(--bg-panel);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border-radius: 20px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 30px;
            margin-bottom: 30px;
            box-shadow:
                0 8px 32px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }}

        /* Game Selector */
        .game-selector {{
            margin-bottom: 30px;
        }}

        .game-selector-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 20px;
            color: var(--accent-cyan);
            text-transform: uppercase;
            letter-spacing: 3px;
        }}

        .games-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 15px;
        }}

        .game-card {{
            background: rgba(30, 30, 45, 0.8);
            border: 2px solid rgba(139, 92, 246, 0.3);
            border-radius: 12px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}

        .game-card:hover {{
            border-color: var(--accent-purple);
            transform: translateY(-3px);
            box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);
        }}

        .game-card.active {{
            border-color: var(--accent-pink);
            background: rgba(217, 70, 239, 0.15);
            box-shadow: 0 0 25px rgba(217, 70, 239, 0.4);
        }}

        .game-card-teams {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}

        .game-card-team {{
            font-weight: 600;
            font-size: 0.95rem;
            max-width: 40%;
        }}

        .game-card-vs {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.8rem;
            color: var(--accent-pink);
        }}

        .game-card-time {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-align: center;
        }}

        .game-card-prediction {{
            position: absolute;
            top: 8px;
            right: 8px;
            font-size: 0.7rem;
            padding: 2px 8px;
            border-radius: 10px;
            background: rgba(34, 197, 94, 0.2);
            color: var(--accent-green);
        }}

        /* Team Comparison Section */
        .team-comparison {{
            display: grid;
            grid-template-columns: 1fr auto 1fr;
            gap: 40px;
            align-items: center;
        }}

        .team-side {{
            text-align: center;
        }}

        .team-crest {{
            width: 140px;
            height: 140px;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Orbitron', sans-serif;
            font-size: 2.5rem;
            font-weight: 900;
        }}

        .team-crest img {{
            max-width: 140px;
            max-height: 140px;
            object-fit: contain;
        }}

        .team-crest .initials {{
            /* Initials fallback styling */
        }}

        .team-name {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 10px;
        }}

        .team-overall {{
            font-family: 'Orbitron', sans-serif;
            font-size: 4rem;
            font-weight: 900;
            background: linear-gradient(135deg, var(--gold), var(--gold-dark));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .team-overall-label {{
            font-size: 0.9rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 3px;
        }}

        .vs-badge {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            color: var(--accent-pink);
            text-shadow: 0 0 20px var(--accent-pink);
        }}

        .rank-badge {{
            display: inline-block;
            background: linear-gradient(135deg, var(--accent-purple), var(--accent-pink));
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9rem;
            font-weight: 600;
            margin-top: 10px;
        }}

        .team-record {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.3rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 10px 0;
            letter-spacing: 2px;
        }}

        .team-record .wins {{
            color: var(--accent-green);
        }}

        .team-record .losses {{
            color: #ef4444;
        }}

        .team-record .ties {{
            color: var(--text-secondary);
        }}

        .team-division {{
            font-size: 0.85rem;
            color: var(--accent-cyan);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }}

        .prediction-banner {{
            text-align: center;
            margin-top: 20px;
            padding: 20px 30px;
            background: rgba(34, 197, 94, 0.05);
            border: 1px solid rgba(34, 197, 94, 0.2);
            border-radius: 10px;
        }}

        .prediction-banner .label {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 20px;
        }}

        .prediction-slider {{
            position: relative;
            width: 100%;
            max-width: 500px;
            margin: 0 auto;
        }}

        .prediction-track {{
            position: relative;
            height: 12px;
            background: linear-gradient(90deg, var(--accent-cyan), rgba(255,255,255,0.1) 45%, rgba(255,255,255,0.1) 55%, var(--accent-pink));
            border-radius: 6px;
            margin: 15px 0;
        }}

        .prediction-marker {{
            position: absolute;
            top: 50%;
            transform: translate(-50%, -50%);
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, var(--accent-green), #16a34a);
            border-radius: 50%;
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.6), 0 0 40px rgba(34, 197, 94, 0.3);
            display: flex;
            align-items: center;
            justify-content: center;
            font-family: 'Orbitron', sans-serif;
            font-size: 0.75rem;
            font-weight: 700;
            color: white;
            transition: left 0.8s cubic-bezier(0.34, 1.56, 0.64, 1);
            z-index: 2;
        }}

        .prediction-marker::before {{
            content: '';
            position: absolute;
            width: 50px;
            height: 50px;
            border: 2px solid var(--accent-green);
            border-radius: 50%;
            animation: pulse-ring 1.5s ease-out infinite;
        }}

        @keyframes pulse-ring {{
            0% {{ transform: scale(0.8); opacity: 1; }}
            100% {{ transform: scale(1.3); opacity: 0; }}
        }}

        .prediction-teams {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-top: 10px;
        }}

        .prediction-team {{
            font-family: 'Orbitron', sans-serif;
            font-size: 0.85rem;
            font-weight: 600;
            max-width: 45%;
            text-align: center;
        }}

        .prediction-team.away {{
            color: var(--accent-cyan);
        }}

        .prediction-team.home {{
            color: var(--accent-pink);
        }}

        .prediction-team.favored {{
            color: var(--accent-green);
            text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
        }}

        .prediction-center-line {{
            position: absolute;
            left: 50%;
            top: -5px;
            bottom: -5px;
            width: 2px;
            background: rgba(255, 255, 255, 0.3);
            transform: translateX(-50%);
        }}

        /* Stats Comparison */
        .stats-section {{
            margin-top: 20px;
        }}

        .stats-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 25px;
            color: var(--accent-cyan);
            text-transform: uppercase;
            letter-spacing: 3px;
        }}

        .stat-row {{
            display: grid;
            grid-template-columns: 100px 1fr 120px 1fr 100px;
            gap: 15px;
            align-items: center;
            margin-bottom: 20px;
        }}

        .stat-value {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
        }}

        .stat-value.left {{
            text-align: right;
            color: var(--accent-cyan);
        }}

        .stat-value.right {{
            text-align: left;
            color: var(--accent-pink);
        }}

        .stat-label {{
            text-align: center;
            font-size: 0.85rem;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .stat-bar-container {{
            height: 8px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 4px;
            overflow: hidden;
            position: relative;
        }}

        .stat-bar {{
            height: 100%;
            border-radius: 4px;
            transition: width 1s ease-out;
        }}

        .stat-bar.left {{
            background: linear-gradient(90deg, transparent, var(--accent-cyan));
            float: right;
        }}

        .stat-bar.right {{
            background: linear-gradient(90deg, var(--accent-pink), transparent);
        }}

        /* Player Cards Section */
        .players-section {{
            margin-top: 30px;
        }}

        .players-title {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            text-align: center;
            margin-bottom: 25px;
            color: var(--accent-purple);
            text-transform: uppercase;
            letter-spacing: 3px;
        }}

        .players-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 40px;
        }}

        .team-players {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
        }}

        .team-players-header {{
            grid-column: 1 / -1;
            text-align: center;
            font-family: 'Orbitron', sans-serif;
            font-size: 1rem;
            color: var(--text-secondary);
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 2px;
        }}

        /* Player Card */
        .player-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 15px 10px;
            text-align: center;
            position: relative;
            overflow: hidden;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            cursor: pointer;
        }}

        .player-card:hover {{
            transform: translateY(-5px) scale(1.02);
            box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
        }}

        .player-card.gold {{
            border: 2px solid var(--gold);
            box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        }}

        .player-card.gold::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--gold-dark), var(--gold), var(--gold-dark));
        }}

        .player-card.silver {{
            border: 2px solid var(--silver);
            box-shadow: 0 0 15px rgba(192, 192, 192, 0.2);
        }}

        .player-card.silver::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--silver-dark), var(--silver), var(--silver-dark));
        }}

        .player-card.bronze {{
            border: 2px solid var(--bronze);
            box-shadow: 0 0 10px rgba(205, 127, 50, 0.2);
        }}

        .player-card.bronze::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: linear-gradient(90deg, var(--bronze-dark), var(--bronze), var(--bronze-dark));
        }}

        .player-ovr {{
            font-family: 'Orbitron', sans-serif;
            font-size: 2rem;
            font-weight: 900;
            margin-bottom: 10px;
        }}

        .player-card.gold .player-ovr {{
            color: var(--gold);
        }}

        .player-card.silver .player-ovr {{
            color: var(--silver);
        }}

        .player-card.bronze .player-ovr {{
            color: var(--bronze);
        }}

        .player-photo {{
            width: 70px;
            height: 70px;
            margin: 0 auto 10px;
            background: linear-gradient(135deg, #FF1493, #8B5CF6);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
            box-shadow: 0 0 15px rgba(255, 20, 147, 0.3);
        }}

        .player-photo img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .player-photo .initials {{
            font-family: 'Orbitron', sans-serif;
            font-size: 1.2rem;
            font-weight: 700;
            color: white;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }}

        .player-photo svg {{
            width: 40px;
            height: 40px;
            fill: rgba(255, 255, 255, 0.5);
        }}

        .player-name {{
            font-size: 0.85rem;
            font-weight: 600;
            margin-bottom: 8px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .player-position {{
            display: inline-block;
            padding: 3px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .player-position.F {{
            background: linear-gradient(135deg, #ef4444, #dc2626);
        }}

        .player-position.D {{
            background: linear-gradient(135deg, #3b82f6, #2563eb);
        }}

        .player-position.G {{
            background: linear-gradient(135deg, #22c55e, #16a34a);
        }}

        .player-points {{
            font-size: 0.7rem;
            color: var(--text-secondary);
            margin-top: 8px;
        }}

        /* Footer */
        .footer {{
            text-align: center;
            padding: 30px 0;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }}

        .footer a {{
            color: var(--accent-cyan);
            text-decoration: none;
        }}

        /* Animations */
        @keyframes slideInLeft {{
            from {{
                opacity: 0;
                transform: translateX(-50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}

        @keyframes slideInRight {{
            from {{
                opacity: 0;
                transform: translateX(50px);
            }}
            to {{
                opacity: 1;
                transform: translateX(0);
            }}
        }}

        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}

        @keyframes scaleIn {{
            from {{
                opacity: 0;
                transform: scale(0.8);
            }}
            to {{
                opacity: 1;
                transform: scale(1);
            }}
        }}

        .animate-left {{
            animation: slideInLeft 0.6s ease-out forwards;
        }}

        .animate-right {{
            animation: slideInRight 0.6s ease-out forwards;
        }}

        .animate-fade {{
            animation: fadeIn 0.8s ease-out forwards;
        }}

        .animate-scale {{
            animation: scaleIn 0.5s ease-out forwards;
        }}

        /* Card stagger animation */
        .player-card:nth-child(1) {{ animation-delay: 0.1s; }}
        .player-card:nth-child(2) {{ animation-delay: 0.2s; }}
        .player-card:nth-child(3) {{ animation-delay: 0.3s; }}
        .player-card:nth-child(4) {{ animation-delay: 0.4s; }}
        .player-card:nth-child(5) {{ animation-delay: 0.5s; }}
        .player-card:nth-child(6) {{ animation-delay: 0.6s; }}

        /* Responsive */
        @media (max-width: 1024px) {{
            .team-comparison {{
                grid-template-columns: 1fr;
                gap: 20px;
            }}

            .vs-badge {{
                order: -1;
            }}

            .players-grid {{
                grid-template-columns: 1fr;
            }}

            .team-players {{
                grid-template-columns: repeat(3, 1fr);
            }}

            .stat-row {{
                grid-template-columns: 60px 1fr 80px 1fr 60px;
                gap: 10px;
            }}

            .stat-value {{
                font-size: 0.9rem;
            }}
        }}

        @media (max-width: 640px) {{
            .header h1 {{
                font-size: 1.8rem;
                letter-spacing: 2px;
            }}

            .team-players {{
                grid-template-columns: repeat(2, 1fr);
            }}

            .games-grid {{
                grid-template-columns: 1fr;
            }}

            .stat-row {{
                grid-template-columns: 1fr;
                gap: 5px;
                text-align: center;
            }}

            .stat-value.left,
            .stat-value.right {{
                text-align: center;
            }}

            .stat-bar-container {{
                display: none;
            }}
        }}

        /* No data message */
        .no-data {{
            text-align: center;
            padding: 40px;
            color: var(--text-secondary);
        }}

        .no-data-icon {{
            font-size: 3rem;
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header class="header">
            <img src="https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac_logos_short/ace_scouty.png" alt="Ace & Scout" class="mascot-image">
            <h1>NEPSAC Team Matchup</h1>
            <div class="subtitle">⚔️ HEAD TO HEAD ⚔️</div>
            <div class="date-badge">WEDNESDAY, JANUARY 21, 2026</div>
        </header>

        <!-- Game Selector -->
        <section class="glass-panel game-selector">
            <h2 class="game-selector-title">Select Today's Game</h2>
            <div class="games-grid" id="gamesGrid">
                <!-- Games will be populated by JS -->
            </div>
        </section>

        <!-- Team Comparison -->
        <section class="glass-panel team-comparison" id="teamComparison">
            <div class="team-side animate-left" id="awayTeamSection">
                <div class="team-crest" id="awayCrest">AOF</div>
                <div class="team-name" id="awayName">Away Team</div>
                <div class="team-division" id="awayDivision">--</div>
                <div class="team-record" id="awayRecord"><span class="wins">-</span>-<span class="losses">-</span>-<span class="ties">-</span></div>
                <div class="team-overall" id="awayOvr">--</div>
                <div class="team-overall-label">OVERALL</div>
                <div class="rank-badge" id="awayRank">#-- NEPSAC</div>
            </div>

            <div class="vs-badge">VS</div>

            <div class="team-side animate-right" id="homeTeamSection">
                <div class="team-crest" id="homeCrest">KS</div>
                <div class="team-name" id="homeName">Home Team</div>
                <div class="team-division" id="homeDivision">--</div>
                <div class="team-record" id="homeRecord"><span class="wins">-</span>-<span class="losses">-</span>-<span class="ties">-</span></div>
                <div class="team-overall" id="homeOvr">--</div>
                <div class="team-overall-label">OVERALL</div>
                <div class="rank-badge" id="homeRank">#-- NEPSAC</div>
            </div>
        </section>

        <!-- Prediction Banner -->
        <section class="glass-panel" id="predictionSection" style="display: none;">
            <div class="prediction-banner">
                <div class="label">ProdigyPrediction</div>
                <div class="prediction-slider">
                    <div class="prediction-track">
                        <div class="prediction-center-line"></div>
                        <div class="prediction-marker" id="predictionMarker">70%</div>
                    </div>
                    <div class="prediction-teams">
                        <div class="prediction-team away" id="predAwayTeam">Away</div>
                        <div class="prediction-team home" id="predHomeTeam">Home</div>
                    </div>
                </div>
            </div>
        </section>

        <!-- Stats Comparison -->
        <section class="glass-panel stats-section" id="statsSection">
            <h2 class="stats-title">Head-to-Head Comparison</h2>

            <div class="stat-row">
                <div class="stat-value left" id="awayAvgPts">--</div>
                <div class="stat-bar-container">
                    <div class="stat-bar left" id="awayAvgBar" style="width: 0%"></div>
                </div>
                <div class="stat-label">AVG PTS</div>
                <div class="stat-bar-container">
                    <div class="stat-bar right" id="homeAvgBar" style="width: 0%"></div>
                </div>
                <div class="stat-value right" id="homeAvgPts">--</div>
            </div>

            <div class="stat-row">
                <div class="stat-value left" id="awayMaxPts">--</div>
                <div class="stat-bar-container">
                    <div class="stat-bar left" id="awayMaxBar" style="width: 0%"></div>
                </div>
                <div class="stat-label">TOP PLAYER</div>
                <div class="stat-bar-container">
                    <div class="stat-bar right" id="homeMaxBar" style="width: 0%"></div>
                </div>
                <div class="stat-value right" id="homeMaxPts">--</div>
            </div>

            <div class="stat-row">
                <div class="stat-value left" id="awayRoster">--</div>
                <div class="stat-bar-container">
                    <div class="stat-bar left" id="awayRosterBar" style="width: 0%"></div>
                </div>
                <div class="stat-label">ROSTER</div>
                <div class="stat-bar-container">
                    <div class="stat-bar right" id="homeRosterBar" style="width: 0%"></div>
                </div>
                <div class="stat-value right" id="homeRoster">--</div>
            </div>

            <div class="stat-row">
                <div class="stat-value left" id="awayTotalPts">--</div>
                <div class="stat-bar-container">
                    <div class="stat-bar left" id="awayTotalBar" style="width: 0%"></div>
                </div>
                <div class="stat-label">TOTAL PTS</div>
                <div class="stat-bar-container">
                    <div class="stat-bar right" id="homeTotalBar" style="width: 0%"></div>
                </div>
                <div class="stat-value right" id="homeTotalPts">--</div>
            </div>
        </section>

        <!-- Player Cards -->
        <section class="glass-panel players-section" id="playersSection">
            <h2 class="players-title">GameDay ProdigyPicks</h2>

            <div class="players-grid">
                <div class="team-players" id="awayPlayers">
                    <div class="team-players-header" id="awayPlayersHeader">Away Team</div>
                    <!-- Player cards will be inserted by JavaScript -->
                </div>

                <div class="team-players" id="homePlayers">
                    <div class="team-players-header" id="homePlayersHeader">Home Team</div>
                    <!-- Player cards will be inserted by JavaScript -->
                </div>
            </div>

        </section>

        <!-- Footer -->
        <footer class="footer">
            <p>Powered by <a href="#">Prodigy Hockey</a> | NEPSAC 2025-26 Season</p>
        </footer>
    </div>

    <script>
        // Embedded team data
        const TEAMS_DATA = {teams_json};

        const TEAMS_LIST = {teams_list_json};

        const GAMES = {games_json};

        const MAX_POINTS = {max_points};

        let selectedGameIndex = 0;

        // Convert Prodigy Points to OVR (70-99 scale)
        function convertToOVR(points) {{
            if (!points || points <= 0) return 70;
            const ovr = 70 + (points / MAX_POINTS) * 29;
            return Math.min(99, Math.max(70, Math.round(ovr)));
        }}

        // Calculate team overall from avg points
        function calculateTeamOVR(avgPoints) {{
            const minAvg = 750;
            const maxAvg = 2950;
            const normalized = (avgPoints - minAvg) / (maxAvg - minAvg);
            const ovr = 70 + normalized * 29;
            return Math.min(99, Math.max(70, Math.round(ovr)));
        }}

        // Get rating tier class
        function getRatingTier(ovr) {{
            if (ovr >= 90) return 'gold';
            if (ovr >= 80) return 'silver';
            return 'bronze';
        }}

        // Get team initials
        function getTeamInitials(teamName) {{
            const words = teamName.split(' ');
            if (words.length === 1) return teamName.substring(0, 3).toUpperCase();
            return words.map(w => w[0]).join('').substring(0, 3).toUpperCase();
        }}

        // Render team crest (logo or initials)
        function renderCrest(team, fallbackName) {{
            const name = team ? team.name : (fallbackName || '');
            if (team && team.logo) {{
                return `<img src="${{team.logo}}" alt="Logo" onerror="this.parentElement.innerHTML='${{getTeamInitials(name)}}'">`;
            }}
            return getTeamInitials(name);
        }}

        // Player silhouette SVG (fallback)
        const playerSvg = `<svg viewBox="0 0 24 24"><path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg>`;

        // Get player initials for fallback avatar
        function getPlayerInitials(name) {{
            if (!name) return '??';
            return name.split(' ')
                .map(n => n[0])
                .join('')
                .toUpperCase()
                .slice(0, 2);
        }}

        // Create player photo HTML with image or initials fallback
        function createPlayerPhoto(player) {{
            const initials = getPlayerInitials(player.name);
            if (player.image_url) {{
                return `<img src="${{player.image_url}}" alt="${{player.name}}" onerror="this.parentElement.innerHTML='<span class=\\'initials\\'>${{initials}}</span>'">`;
            }}
            return `<span class="initials">${{initials}}</span>`;
        }}

        // Create player card HTML
        function createPlayerCard(player, index) {{
            const ovr = convertToOVR(player.points);
            const tier = getRatingTier(ovr);
            const position = player.position || 'F';
            // Get first position for CSS class (handle D/F, F/D, etc.)
            const positionClass = position.split('/')[0].trim();

            return `
                <div class="player-card ${{tier}} animate-scale" style="animation-delay: ${{index * 0.1}}s">
                    <div class="player-ovr">${{ovr}}</div>
                    <div class="player-photo">${{createPlayerPhoto(player)}}</div>
                    <div class="player-name">${{player.name}}</div>
                    <div class="player-position ${{positionClass}}">${{position}}</div>
                    <div class="player-points">${{Math.round(player.points).toLocaleString()}} pts</div>
                </div>
            `;
        }}

        // Animate stat bars
        function animateStatBars(awayVal, homeVal, awayBarId, homeBarId) {{
            const total = awayVal + homeVal;
            const awayPercent = total > 0 ? (awayVal / total) * 100 : 50;
            const homePercent = total > 0 ? (homeVal / total) * 100 : 50;

            setTimeout(() => {{
                document.getElementById(awayBarId).style.width = awayPercent + '%';
                document.getElementById(homeBarId).style.width = homePercent + '%';
            }}, 100);
        }}

        // Format record for game card
        function formatRecordShort(team) {{
            if (!team) return '';
            return `(${{team.wins}}-${{team.losses}}-${{team.ties}})`;
        }}

        // Create game card HTML
        function createGameCard(game, index) {{
            const awayTeam = TEAMS_DATA[game.away];
            const homeTeam = TEAMS_DATA[game.home];

            const awayInfo = awayTeam ? `#${{awayTeam.rank}} ${{game.away}} ${{formatRecordShort(awayTeam)}}` : game.away;
            const homeInfo = homeTeam ? `#${{homeTeam.rank}} ${{game.home}} ${{formatRecordShort(homeTeam)}}` : game.home;

            return `
                <div class="game-card ${{index === selectedGameIndex ? 'active' : ''}}" onclick="selectGame(${{index}})">
                    <div class="game-card-prediction">${{game.confidence}}%</div>
                    <div class="game-card-teams">
                        <div class="game-card-team">${{awayInfo}}</div>
                        <div class="game-card-vs">@</div>
                        <div class="game-card-team">${{homeInfo}}</div>
                    </div>
                    <div class="game-card-time">${{game.time}} - ${{game.venue}}</div>
                </div>
            `;
        }}

        // Populate games grid
        function populateGames() {{
            const gamesGrid = document.getElementById('gamesGrid');
            gamesGrid.innerHTML = GAMES.map((game, i) => createGameCard(game, i)).join('');
        }}

        // Select a game
        function selectGame(index) {{
            selectedGameIndex = index;

            // Update active state
            document.querySelectorAll('.game-card').forEach((card, i) => {{
                card.classList.toggle('active', i === index);
            }});

            loadMatchup(GAMES[index]);
        }}

        // Load matchup
        function loadMatchup(game) {{
            const awayTeamName = game.away;
            const homeTeamName = game.home;

            const awayTeam = TEAMS_DATA[awayTeamName];
            const homeTeam = TEAMS_DATA[homeTeamName];

            // Show/hide sections based on data availability
            const hasAwayData = !!awayTeam;
            const hasHomeData = !!homeTeam;

            if (!hasAwayData && !hasHomeData) {{
                document.getElementById('teamComparison').innerHTML = `
                    <div class="no-data" style="grid-column: 1/-1;">
                        <div class="no-data-icon">🏒</div>
                        <p>Team data not available for this matchup</p>
                    </div>
                `;
                return;
            }}

            // Helper to format record
            function formatRecord(team) {{
                if (!team) return '<span class="wins">-</span>-<span class="losses">-</span>-<span class="ties">-</span>';
                return `<span class="wins">${{team.wins}}</span>-<span class="losses">${{team.losses}}</span>-<span class="ties">${{team.ties}}</span>`;
            }}

            // Update away team info
            document.getElementById('awayCrest').innerHTML = renderCrest(awayTeam, awayTeamName);
            document.getElementById('awayName').textContent = awayTeamName;
            document.getElementById('awayDivision').textContent = hasAwayData && awayTeam.division ? awayTeam.division : '';
            document.getElementById('awayRecord').innerHTML = formatRecord(awayTeam);
            document.getElementById('awayOvr').textContent = hasAwayData ? calculateTeamOVR(awayTeam.avg_points) : '--';
            document.getElementById('awayRank').textContent = hasAwayData ? `#${{awayTeam.rank}} NEPSAC` : 'UNRANKED';

            // Update home team info
            document.getElementById('homeCrest').innerHTML = renderCrest(homeTeam, homeTeamName);
            document.getElementById('homeName').textContent = homeTeamName;
            document.getElementById('homeDivision').textContent = hasHomeData && homeTeam.division ? homeTeam.division : '';
            document.getElementById('homeRecord').innerHTML = formatRecord(homeTeam);
            document.getElementById('homeOvr').textContent = hasHomeData ? calculateTeamOVR(homeTeam.avg_points) : '--';
            document.getElementById('homeRank').textContent = hasHomeData ? `#${{homeTeam.rank}} NEPSAC` : 'UNRANKED';

            // Update prediction slider
            document.getElementById('predictionSection').style.display = 'block';
            const predAwayEl = document.getElementById('predAwayTeam');
            const predHomeEl = document.getElementById('predHomeTeam');
            const markerEl = document.getElementById('predictionMarker');

            predAwayEl.textContent = awayTeamName;
            predHomeEl.textContent = homeTeamName;

            // Remove previous favored class
            predAwayEl.classList.remove('favored');
            predHomeEl.classList.remove('favored');

            // Determine position: 50% = center (toss-up), 0% = away favored, 100% = home favored
            const isHomeFavored = game.predicted_winner === homeTeamName;
            const confidence = game.confidence;

            // Calculate marker position
            // If home favored: position moves right (50% + offset)
            // If away favored: position moves left (50% - offset)
            // Offset based on confidence: 50% confidence = center, 100% = edge
            const offset = ((confidence - 50) / 50) * 40; // Max 40% offset from center
            let markerPos;

            if (isHomeFavored) {{
                markerPos = 50 + offset;
                predHomeEl.classList.add('favored');
            }} else {{
                markerPos = 50 - offset;
                predAwayEl.classList.add('favored');
            }}

            // Animate marker position
            setTimeout(() => {{
                markerEl.style.left = markerPos + '%';
                markerEl.textContent = confidence + '%';
            }}, 100);

            // Update stats
            const awayAvg = hasAwayData ? awayTeam.avg_points : 0;
            const homeAvg = hasHomeData ? homeTeam.avg_points : 0;
            document.getElementById('awayAvgPts').textContent = hasAwayData ? Math.round(awayAvg).toLocaleString() : '--';
            document.getElementById('homeAvgPts').textContent = hasHomeData ? Math.round(homeAvg).toLocaleString() : '--';
            animateStatBars(awayAvg, homeAvg, 'awayAvgBar', 'homeAvgBar');

            const awayMax = hasAwayData ? awayTeam.max_points : 0;
            const homeMax = hasHomeData ? homeTeam.max_points : 0;
            document.getElementById('awayMaxPts').textContent = hasAwayData ? Math.round(awayMax).toLocaleString() : '--';
            document.getElementById('homeMaxPts').textContent = hasHomeData ? Math.round(homeMax).toLocaleString() : '--';
            animateStatBars(awayMax, homeMax, 'awayMaxBar', 'homeMaxBar');

            const awayRoster = hasAwayData ? awayTeam.roster_size : 0;
            const homeRoster = hasHomeData ? homeTeam.roster_size : 0;
            document.getElementById('awayRoster').textContent = hasAwayData ? awayRoster : '--';
            document.getElementById('homeRoster').textContent = hasHomeData ? homeRoster : '--';
            animateStatBars(awayRoster, homeRoster, 'awayRosterBar', 'homeRosterBar');

            const awayTotal = hasAwayData ? awayTeam.total_points : 0;
            const homeTotal = hasHomeData ? homeTeam.total_points : 0;
            document.getElementById('awayTotalPts').textContent = hasAwayData ? Math.round(awayTotal).toLocaleString() : '--';
            document.getElementById('homeTotalPts').textContent = hasHomeData ? Math.round(homeTotal).toLocaleString() : '--';
            animateStatBars(awayTotal, homeTotal, 'awayTotalBar', 'homeTotalBar');

            // Update player cards
            const awayPlayersContainer = document.getElementById('awayPlayers');
            const homePlayersContainer = document.getElementById('homePlayers');

            // Clear existing cards and set new header
            awayPlayersContainer.innerHTML = `<div class="team-players-header">${{awayTeamName}}</div>`;
            homePlayersContainer.innerHTML = `<div class="team-players-header">${{homeTeamName}}</div>`;

            // Add player cards
            console.log('Loading players for:', awayTeamName, homeTeamName);
            console.log('Away team data:', awayTeam);
            console.log('Home team data:', homeTeam);

            if (hasAwayData && awayTeam.players && awayTeam.players.length > 0) {{
                console.log('Adding', awayTeam.players.length, 'away players');
                awayTeam.players.forEach((player, i) => {{
                    awayPlayersContainer.innerHTML += createPlayerCard(player, i);
                }});
            }} else {{
                console.log('No away player data');
                awayPlayersContainer.innerHTML += `<div class="no-data" style="grid-column: 1/-1;"><p>No player data</p></div>`;
            }}

            if (hasHomeData && homeTeam.players && homeTeam.players.length > 0) {{
                console.log('Adding', homeTeam.players.length, 'home players');
                homeTeam.players.forEach((player, i) => {{
                    homePlayersContainer.innerHTML += createPlayerCard(player, i);
                }});
            }} else {{
                console.log('No home player data');
                homePlayersContainer.innerHTML += `<div class="no-data" style="grid-column: 1/-1;"><p>No player data</p></div>`;
            }}

        }}

        // Initialize
        document.addEventListener('DOMContentLoaded', () => {{
            try {{
                console.log('Page loaded, initializing...');
                console.log('TEAMS_DATA keys:', Object.keys(TEAMS_DATA).length);
                console.log('GAMES count:', GAMES.length);
                populateGames();
                if (GAMES.length > 0) {{
                    selectGame(0);
                }}
                console.log('Initialization complete');
            }} catch (error) {{
                console.error('Initialization error:', error);
                alert('Error loading page: ' + error.message);
            }}
        }});

        // Global error handler
        window.onerror = function(msg, url, lineNo, columnNo, error) {{
            console.error('Global error:', msg, 'at line', lineNo);
            return false;
        }};
    </script>
</body>
</html>
'''

# Write the HTML file
with open('nepsac_matchup_page.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Generated nepsac_matchup_page.html")
print(f"Total teams: {len(teams_data)}")
print(f"Total games for Tuesday Jan 21: {len(wednesday_games)}")
print(f"Max points found: {max_points}")

# List the games
print("\nGames included:")
for game in wednesday_games:
    print(f"  {game['away']} @ {game['home']} - {game['time']}")

import { useState, useEffect } from 'react';
import {
  fetchNepsacSchedule,
  fetchNepsacMatchup,
  fetchNepsacGameDates,
  type NepsacGame,
  type NepsacMatchup as MatchupType,
  type NepsacGameDate,
  type NepsacPlayer,
} from '@/lib/nepsac-api';
import { GameComments } from '@/components/nepsac/GameComments';
import { NepsacPowerRankings } from '@/components/nepsac';

// Import Orbitron font
const fontLink = document.createElement('link');
fontLink.href = 'https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Rajdhani:wght@400;500;600;700&display=swap';
fontLink.rel = 'stylesheet';
document.head.appendChild(fontLink);

export default function NepsacGameDay() {
  const [gameDates, setGameDates] = useState<NepsacGameDate[]>([]);
  const [selectedDate, setSelectedDate] = useState<string>('');
  const [games, setGames] = useState<NepsacGame[]>([]);
  const [selectedGameId, setSelectedGameId] = useState<string | null>(null);
  const [matchup, setMatchup] = useState<MatchupType | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [showRankings, setShowRankings] = useState(true);

  // Load game dates on mount
  useEffect(() => {
    async function loadDates() {
      const data = await fetchNepsacGameDates();
      if (data && data.dates.length > 0) {
        setGameDates(data.dates);
        setSelectedDate(data.dates[0].date);
      }
      setIsLoading(false);
    }
    loadDates();
  }, []);

  // Load games when date changes
  useEffect(() => {
    if (!selectedDate) return;
    async function loadGames() {
      const data = await fetchNepsacSchedule(selectedDate);
      if (data) {
        setGames(data.games);
        if (data.games.length > 0) {
          setSelectedGameId(data.games[0].gameId);
        }
      }
    }
    loadGames();
  }, [selectedDate]);

  // Load matchup when game selected
  useEffect(() => {
    if (!selectedGameId) return;
    async function loadMatchup() {
      const data = await fetchNepsacMatchup(selectedGameId!);
      setMatchup(data);
    }
    loadMatchup();
  }, [selectedGameId]);

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr + 'T00:00:00');
    return date.toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });
  };

  return (
    <>
      <style>{`
        .nepsac-page {
          font-family: 'Rajdhani', sans-serif;
          background: #0a0a0f;
          min-height: 100vh;
          color: #ffffff;
          overflow-x: hidden;
        }

        .nepsac-page::before {
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
        }

        .nepsac-container {
          max-width: 1400px;
          margin: 0 auto;
          padding: 20px;
          position: relative;
          z-index: 1;
        }

        .nepsac-header {
          text-align: center;
          padding: 30px 0;
          margin-bottom: 30px;
        }

        .nepsac-header h1 {
          font-family: 'Orbitron', sans-serif;
          font-size: 3rem;
          font-weight: 900;
          text-transform: uppercase;
          letter-spacing: 4px;
          background: linear-gradient(135deg, #d946ef, #8b5cf6, #06b6d4);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
          animation: glow 2s ease-in-out infinite alternate;
        }

        @keyframes glow {
          from { filter: drop-shadow(0 0 20px rgba(139, 92, 246, 0.5)); }
          to { filter: drop-shadow(0 0 30px rgba(217, 70, 239, 0.7)); }
        }

        .nepsac-header .subtitle {
          font-size: 1.5rem;
          color: #a0a0b0;
          margin-top: 10px;
          letter-spacing: 8px;
          text-transform: uppercase;
        }

        .date-badge {
          display: inline-block;
          margin-top: 15px;
          padding: 8px 25px;
          background: linear-gradient(135deg, #8b5cf6, #d946ef);
          border-radius: 25px;
          font-family: 'Orbitron', sans-serif;
          font-size: 1rem;
          font-weight: 700;
          letter-spacing: 2px;
        }

        .glass-panel {
          background: rgba(20, 20, 30, 0.8);
          backdrop-filter: blur(20px);
          -webkit-backdrop-filter: blur(20px);
          border-radius: 20px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          padding: 30px;
          margin-bottom: 30px;
          box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.1);
        }

        .game-selector-title {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.2rem;
          text-align: center;
          margin-bottom: 20px;
          color: #06b6d4;
          text-transform: uppercase;
          letter-spacing: 3px;
        }

        .games-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 15px;
        }

        .game-card {
          background: rgba(30, 30, 45, 0.8);
          border: 2px solid rgba(139, 92, 246, 0.3);
          border-radius: 12px;
          padding: 15px;
          cursor: pointer;
          transition: all 0.3s ease;
          position: relative;
        }

        .game-card:hover {
          border-color: #8b5cf6;
          transform: translateY(-3px);
          box-shadow: 0 10px 30px rgba(139, 92, 246, 0.3);
        }

        .game-card.active {
          border-color: #d946ef;
          background: rgba(217, 70, 239, 0.15);
          box-shadow: 0 0 25px rgba(217, 70, 239, 0.4);
        }

        .game-card-teams {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }

        .game-card-team {
          font-weight: 600;
          font-size: 0.95rem;
          max-width: 40%;
        }

        .game-card-vs {
          font-family: 'Orbitron', sans-serif;
          font-size: 0.8rem;
          color: #d946ef;
        }

        .game-card-time {
          font-size: 0.85rem;
          color: #a0a0b0;
          text-align: center;
        }

        .game-card-prediction {
          position: absolute;
          top: 8px;
          right: 8px;
          font-size: 0.7rem;
          padding: 2px 8px;
          border-radius: 10px;
          background: rgba(34, 197, 94, 0.2);
          color: #22c55e;
        }

        .team-comparison {
          display: grid;
          grid-template-columns: 1fr auto 1fr;
          gap: 40px;
          align-items: center;
        }

        .team-side {
          text-align: center;
        }

        .team-crest {
          width: 140px;
          height: 140px;
          margin: 0 auto 20px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .team-crest img {
          max-width: 140px;
          max-height: 140px;
          object-fit: contain;
        }

        .team-name {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.5rem;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 2px;
          margin-bottom: 10px;
        }

        .team-overall {
          font-family: 'Orbitron', sans-serif;
          font-size: 4rem;
          font-weight: 900;
          background: linear-gradient(135deg, #ffd700, #b8860b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .team-overall-label {
          font-size: 0.9rem;
          color: #a0a0b0;
          text-transform: uppercase;
          letter-spacing: 3px;
        }

        .vs-badge {
          font-family: 'Orbitron', sans-serif;
          font-size: 2rem;
          font-weight: 900;
          color: #d946ef;
          text-shadow: 0 0 20px #d946ef;
        }

        .rank-badge {
          display: inline-block;
          background: linear-gradient(135deg, #8b5cf6, #d946ef);
          padding: 5px 15px;
          border-radius: 20px;
          font-size: 0.9rem;
          font-weight: 600;
          margin-top: 10px;
        }

        .team-record {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.3rem;
          font-weight: 700;
          margin: 10px 0;
          letter-spacing: 2px;
        }

        .team-record .wins { color: #22c55e; }
        .team-record .losses { color: #ef4444; }
        .team-record .ties { color: #a0a0b0; }

        .team-division {
          font-size: 0.85rem;
          color: #06b6d4;
          text-transform: uppercase;
          letter-spacing: 1px;
          margin-bottom: 5px;
        }

        .prediction-banner {
          text-align: center;
          margin-top: 20px;
          padding: 20px 30px;
          background: rgba(34, 197, 94, 0.05);
          border: 1px solid rgba(34, 197, 94, 0.2);
          border-radius: 10px;
        }

        .prediction-banner .label {
          font-size: 0.85rem;
          color: #a0a0b0;
          text-transform: uppercase;
          letter-spacing: 2px;
          margin-bottom: 20px;
        }

        .prediction-slider {
          position: relative;
          width: 100%;
          max-width: 500px;
          margin: 0 auto;
        }

        .prediction-track {
          position: relative;
          height: 12px;
          background: linear-gradient(90deg, #06b6d4, rgba(255,255,255,0.1) 45%, rgba(255,255,255,0.1) 55%, #d946ef);
          border-radius: 6px;
          margin: 15px 0;
        }

        .prediction-marker {
          position: absolute;
          top: 50%;
          transform: translate(-50%, -50%);
          width: 40px;
          height: 40px;
          background: linear-gradient(135deg, #22c55e, #16a34a);
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
        }

        .prediction-marker::before {
          content: '';
          position: absolute;
          width: 50px;
          height: 50px;
          border: 2px solid #22c55e;
          border-radius: 50%;
          animation: pulse-ring 1.5s ease-out infinite;
        }

        @keyframes pulse-ring {
          0% { transform: scale(0.8); opacity: 1; }
          100% { transform: scale(1.3); opacity: 0; }
        }

        .prediction-center-line {
          position: absolute;
          left: 50%;
          top: -5px;
          bottom: -5px;
          width: 2px;
          background: rgba(255, 255, 255, 0.3);
          transform: translateX(-50%);
        }

        .prediction-teams {
          display: flex;
          justify-content: space-between;
          margin-top: 10px;
        }

        .prediction-team {
          font-family: 'Orbitron', sans-serif;
          font-size: 0.85rem;
          font-weight: 600;
        }

        .prediction-team.away { color: #06b6d4; }
        .prediction-team.home { color: #d946ef; }
        .prediction-team.favored { color: #22c55e; text-shadow: 0 0 10px rgba(34, 197, 94, 0.5); }

        .stats-title {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.2rem;
          text-align: center;
          margin: 30px 0 25px;
          color: #06b6d4;
          text-transform: uppercase;
          letter-spacing: 3px;
        }

        .stat-row {
          display: grid;
          grid-template-columns: 100px 1fr 120px 1fr 100px;
          gap: 15px;
          align-items: center;
          margin-bottom: 20px;
        }

        .stat-value {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.1rem;
          font-weight: 700;
        }

        .stat-value.left { text-align: right; color: #06b6d4; }
        .stat-value.right { text-align: left; color: #d946ef; }

        .stat-label {
          text-align: center;
          font-size: 0.85rem;
          color: #a0a0b0;
          text-transform: uppercase;
          letter-spacing: 1px;
        }

        .stat-bar-container {
          height: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 4px;
          overflow: hidden;
        }

        .stat-bar {
          height: 100%;
          border-radius: 4px;
          transition: width 1s ease-out;
        }

        .stat-bar.left {
          background: linear-gradient(90deg, transparent, #06b6d4);
          float: right;
        }

        .stat-bar.right {
          background: linear-gradient(90deg, #d946ef, transparent);
        }

        .players-title {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.2rem;
          text-align: center;
          margin: 30px 0 25px;
          color: #8b5cf6;
          text-transform: uppercase;
          letter-spacing: 3px;
        }

        .players-grid {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 40px;
        }

        .team-players {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 15px;
        }

        .team-players-header {
          grid-column: 1 / -1;
          text-align: center;
          font-family: 'Orbitron', sans-serif;
          font-size: 1rem;
          color: #a0a0b0;
          margin-bottom: 10px;
          text-transform: uppercase;
          letter-spacing: 2px;
        }

        .player-card {
          background: rgba(25, 25, 40, 0.9);
          border-radius: 12px;
          padding: 15px 10px;
          text-align: center;
          position: relative;
          overflow: hidden;
          transition: transform 0.3s ease, box-shadow 0.3s ease;
          cursor: pointer;
        }

        .player-card:hover {
          transform: translateY(-5px) scale(1.02);
          box-shadow: 0 15px 40px rgba(0, 0, 0, 0.5);
        }

        .player-card.gold {
          border: 2px solid #ffd700;
          box-shadow: 0 0 20px rgba(255, 215, 0, 0.3);
        }

        .player-card.gold::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #b8860b, #ffd700, #b8860b);
        }

        .player-card.silver {
          border: 2px solid #c0c0c0;
          box-shadow: 0 0 15px rgba(192, 192, 192, 0.2);
        }

        .player-card.silver::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #808080, #c0c0c0, #808080);
        }

        .player-card.bronze {
          border: 2px solid #cd7f32;
          box-shadow: 0 0 10px rgba(205, 127, 50, 0.2);
        }

        .player-card.bronze::before {
          content: '';
          position: absolute;
          top: 0;
          left: 0;
          right: 0;
          height: 3px;
          background: linear-gradient(90deg, #8b4513, #cd7f32, #8b4513);
        }

        .player-ovr {
          font-family: 'Orbitron', sans-serif;
          font-size: 2rem;
          font-weight: 900;
          margin-bottom: 10px;
        }

        .player-card.gold .player-ovr { color: #ffd700; }
        .player-card.silver .player-ovr { color: #c0c0c0; }
        .player-card.bronze .player-ovr { color: #cd7f32; }

        .player-photo {
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
        }

        .player-photo img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .player-photo .initials {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.2rem;
          font-weight: 700;
          color: white;
        }

        .player-name {
          font-size: 0.85rem;
          font-weight: 600;
          margin-bottom: 8px;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .player-position {
          display: inline-block;
          padding: 3px 12px;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 700;
          text-transform: uppercase;
        }

        .player-position.F { background: linear-gradient(135deg, #ef4444, #dc2626); }
        .player-position.D { background: linear-gradient(135deg, #3b82f6, #2563eb); }
        .player-position.G { background: linear-gradient(135deg, #22c55e, #16a34a); }

        .player-points {
          font-size: 0.7rem;
          color: #a0a0b0;
          margin-top: 8px;
        }

        .footer {
          text-align: center;
          padding: 30px 0;
          color: #a0a0b0;
          font-size: 0.85rem;
        }

        .footer a {
          color: #06b6d4;
          text-decoration: none;
        }

        .loading {
          text-align: center;
          padding: 100px 0;
          font-family: 'Orbitron', sans-serif;
          font-size: 1.5rem;
          color: #8b5cf6;
        }

        @media (max-width: 768px) {
          .team-comparison {
            grid-template-columns: 1fr;
            gap: 20px;
          }
          .players-grid {
            grid-template-columns: 1fr;
          }
          .team-players {
            grid-template-columns: repeat(2, 1fr);
          }
          .stat-row {
            grid-template-columns: 60px 1fr 80px 1fr 60px;
            gap: 8px;
          }
        }

        /* Two-column layout with rankings sidebar */
        .nepsac-main-layout {
          display: grid;
          grid-template-columns: 1fr 320px;
          gap: 25px;
        }

        .nepsac-content-area {
          min-width: 0;
        }

        .nepsac-rankings-sidebar {
          position: sticky;
          top: 20px;
          align-self: start;
        }

        .rankings-toggle {
          display: none;
          width: 100%;
          padding: 12px 20px;
          margin-bottom: 15px;
          background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(217, 70, 239, 0.2));
          border: 1px solid rgba(139, 92, 246, 0.4);
          border-radius: 10px;
          color: #d946ef;
          font-family: 'Orbitron', sans-serif;
          font-size: 0.9rem;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 2px;
          cursor: pointer;
          transition: all 0.3s ease;
        }

        .rankings-toggle:hover {
          background: linear-gradient(135deg, rgba(139, 92, 246, 0.4), rgba(217, 70, 239, 0.3));
          border-color: #d946ef;
        }

        @media (max-width: 1200px) {
          .nepsac-main-layout {
            grid-template-columns: 1fr;
          }

          .rankings-toggle {
            display: block;
          }

          .nepsac-rankings-sidebar {
            position: static;
            display: none;
          }

          .nepsac-rankings-sidebar.show {
            display: block;
          }
        }
      `}</style>

      <div className="nepsac-page">
        <div className="nepsac-container">
          {/* Header */}
          <header className="nepsac-header">
            <h1>NEPSAC GameDay</h1>
            <div className="subtitle">Prep Hockey Matchups</div>
            {selectedDate && (
              <div className="date-badge">{formatDate(selectedDate)}</div>
            )}
          </header>

          {isLoading ? (
            <div className="loading">Loading...</div>
          ) : (
            <>
              {/* Rankings Toggle (mobile only) */}
              <button
                className="rankings-toggle"
                onClick={() => setShowRankings(!showRankings)}
              >
                {showRankings ? 'Hide' : 'Show'} Power Rankings
              </button>

              <div className="nepsac-main-layout">
                {/* Main Content Area */}
                <div className="nepsac-content-area">
                  {/* Game Selector */}
                  <div className="glass-panel">
                    <h2 className="game-selector-title">Select Matchup</h2>
                    <div className="games-grid">
                      {games.map((game) => (
                        <div
                          key={game.gameId}
                          className={`game-card ${selectedGameId === game.gameId ? 'active' : ''}`}
                          onClick={() => setSelectedGameId(game.gameId)}
                        >
                          {game.prediction.confidence && (
                            <div className="game-card-prediction">
                              {game.prediction.confidence}%{game.prediction.confidenceOdds && ` (${game.prediction.confidenceOdds})`}
                            </div>
                          )}
                          <div className="game-card-teams">
                            <span className="game-card-team">{game.awayTeam.shortName || game.awayTeam.name}</span>
                            <span className="game-card-vs">VS</span>
                            <span className="game-card-team">{game.homeTeam.shortName || game.homeTeam.name}</span>
                          </div>
                          <div className="game-card-time">{game.gameTime} • {game.venue || 'TBD'}</div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Matchup Display */}
                  {matchup && (
                    <>
                      <div className="glass-panel">
                        {/* Team Comparison */}
                        <div className="team-comparison">
                          <TeamSide team={matchup.awayTeam} />
                          <div className="vs-badge">VS</div>
                          <TeamSide team={matchup.homeTeam} />
                        </div>

                        {/* Prediction */}
                        <PredictionBanner matchup={matchup} />
                      </div>

                      {/* Stats */}
                      <div className="glass-panel">
                        <h3 className="stats-title">Head to Head</h3>
                        <StatsComparison matchup={matchup} />
                      </div>

                      {/* Players */}
                      <div className="glass-panel">
                        <h3 className="players-title">Top 6 Players</h3>
                        <div className="players-grid">
                          <div className="team-players">
                            <div className="team-players-header">{matchup.awayTeam.shortName || matchup.awayTeam.name}</div>
                            {matchup.awayTeam.topPlayers.slice(0, 6).map((player, i) => (
                              <PlayerCard key={i} player={player} maxPoints={matchup.maxPoints} />
                            ))}
                          </div>
                          <div className="team-players">
                            <div className="team-players-header">{matchup.homeTeam.shortName || matchup.homeTeam.name}</div>
                            {matchup.homeTeam.topPlayers.slice(0, 6).map((player, i) => (
                              <PlayerCard key={i} player={player} maxPoints={matchup.maxPoints} />
                            ))}
                          </div>
                        </div>
                      </div>

                      {/* Comments */}
                      {selectedGameId && <GameComments gameId={selectedGameId} />}
                    </>
                  )}
                </div>

                {/* Power Rankings Sidebar */}
                <div className={`nepsac-rankings-sidebar ${showRankings ? 'show' : ''}`}>
                  <NepsacPowerRankings limit={20} />
                </div>
              </div>

              {/* Footer */}
              <footer className="footer">
                <p>Powered by ProdigyPoints Algorithm</p>
                <p><a href="https://theprodigychain.com" target="_blank" rel="noopener noreferrer">theprodigychain.com</a></p>
              </footer>
            </>
          )}
        </div>
      </div>
    </>
  );
}

function TeamSide({ team }: { team: MatchupType['awayTeam'] }) {
  const getInitials = (name: string) => {
    return name.split(' ').map(w => w[0]).join('').slice(0, 3).toUpperCase();
  };

  return (
    <div className="team-side">
      <div className="team-crest">
        {team.logoUrl ? (
          <img src={team.logoUrl} alt={team.name} />
        ) : (
          <span style={{ fontFamily: 'Orbitron', fontSize: '2.5rem', color: '#8b5cf6' }}>
            {getInitials(team.name)}
          </span>
        )}
      </div>
      <div className="team-division">{team.division}</div>
      <div className="team-name">{team.shortName || team.name}</div>
      <div className="team-overall">{team.ovr}</div>
      <div className="team-overall-label">Overall</div>
      <div className="team-record">
        <span className="wins">{team.record.wins}W</span>
        {' - '}
        <span className="losses">{team.record.losses}L</span>
        {' - '}
        <span className="ties">{team.record.ties}T</span>
      </div>
      {team.rank && <div className="rank-badge">Rank #{team.rank}</div>}
    </div>
  );
}

function PredictionBanner({ matchup }: { matchup: MatchupType }) {
  const { game, awayTeam, homeTeam } = matchup;
  const confidence = game.prediction.confidence || 50;
  const confidenceOdds = game.prediction.confidenceOdds;
  const predictedWinner = game.prediction.winnerId;
  const awayFavored = predictedWinner === awayTeam.teamId;

  // Calculate marker position (0-100)
  const markerPosition = awayFavored ? (50 - (confidence - 50)) : (50 + (confidence - 50));

  return (
    <div className="prediction-banner">
      <div className="label">AI Prediction</div>
      <div className="prediction-slider">
        <div className="prediction-track">
          <div className="prediction-center-line" />
          <div
            className="prediction-marker"
            style={{ left: `${markerPosition}%` }}
          >
            {confidence}%
          </div>
        </div>
        <div className="prediction-teams">
          <span className={`prediction-team away ${awayFavored ? 'favored' : ''}`}>
            {awayTeam.shortName || awayTeam.name}
          </span>
          <span className={`prediction-team home ${!awayFavored ? 'favored' : ''}`}>
            {homeTeam.shortName || homeTeam.name}
          </span>
        </div>
        {confidenceOdds && (
          <div style={{ textAlign: 'center', marginTop: '8px' }}>
            <span style={{ fontFamily: 'Orbitron', fontSize: '1.1rem', color: '#a0a0b0' }}>
              {confidenceOdds}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

function StatsComparison({ matchup }: { matchup: MatchupType }) {
  const { awayTeam, homeTeam } = matchup;

  const stats = [
    { label: 'AVG POINTS', away: awayTeam.stats.avgPoints, home: homeTeam.stats.avgPoints },
    { label: 'MAX POINTS', away: awayTeam.stats.maxPoints, home: homeTeam.stats.maxPoints },
    { label: 'ROSTER SIZE', away: awayTeam.stats.rosterSize, home: homeTeam.stats.rosterSize },
    { label: 'MATCH RATE', away: awayTeam.stats.matchRate, home: homeTeam.stats.matchRate, suffix: '%' },
  ];

  return (
    <div>
      {stats.map((stat) => {
        const total = stat.away + stat.home;
        const awayPct = total > 0 ? (stat.away / total) * 100 : 50;
        const homePct = 100 - awayPct;

        return (
          <div key={stat.label} className="stat-row">
            <div className="stat-value left">
              {stat.away.toLocaleString(undefined, { maximumFractionDigits: 0 })}{stat.suffix || ''}
            </div>
            <div className="stat-bar-container">
              <div className="stat-bar left" style={{ width: `${awayPct}%` }} />
            </div>
            <div className="stat-label">{stat.label}</div>
            <div className="stat-bar-container">
              <div className="stat-bar right" style={{ width: `${homePct}%` }} />
            </div>
            <div className="stat-value right">
              {stat.home.toLocaleString(undefined, { maximumFractionDigits: 0 })}{stat.suffix || ''}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function PlayerCard({ player, maxPoints }: { player: NepsacPlayer; maxPoints: number }) {
  const ovr = player.ovr;
  const tier = ovr >= 90 ? 'gold' : ovr >= 80 ? 'silver' : 'bronze';

  const getInitials = (name: string) => {
    const parts = name.split(' ');
    if (parts.length >= 2) {
      return parts[0][0] + parts[parts.length - 1][0];
    }
    return name.slice(0, 2).toUpperCase();
  };

  return (
    <div className={`player-card ${tier}`}>
      <div className="player-ovr">{ovr}</div>
      <div className="player-photo">
        {player.imageUrl ? (
          <img src={player.imageUrl} alt={player.name} />
        ) : (
          <span className="initials">{getInitials(player.name)}</span>
        )}
      </div>
      <div className="player-name" title={player.name}>{player.name}</div>
      <div className={`player-position ${player.position}`}>{player.position}</div>
      <div className="player-points">{player.prodigyPoints.toLocaleString()} pts</div>
    </div>
  );
}

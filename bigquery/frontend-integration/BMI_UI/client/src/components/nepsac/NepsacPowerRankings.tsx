import { useState, useEffect } from 'react';
import {
  fetchNepsacPowerRankings,
  type NepsacPowerRanking,
  type NepsacPowerRankingsResponse,
} from '@/lib/nepsac-api';

interface NepsacPowerRankingsProps {
  limit?: number;
  onTeamClick?: (teamId: string) => void;
}

export function NepsacPowerRankings({ limit = 20, onTeamClick }: NepsacPowerRankingsProps) {
  const [rankings, setRankings] = useState<NepsacPowerRanking[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadRankings() {
      const data = await fetchNepsacPowerRankings('2025-26', limit);
      if (data) {
        setRankings(data.rankings);
      }
      setIsLoading(false);
    }
    loadRankings();
  }, [limit]);

  if (isLoading) {
    return (
      <div className="power-rankings-loading">
        Loading Power Rankings...
      </div>
    );
  }

  return (
    <>
      <style>{`
        .power-rankings-container {
          background: rgba(20, 20, 30, 0.8);
          backdrop-filter: blur(20px);
          border-radius: 16px;
          border: 1px solid rgba(139, 92, 246, 0.3);
          overflow: hidden;
        }

        .power-rankings-header {
          background: linear-gradient(135deg, rgba(139, 92, 246, 0.3), rgba(217, 70, 239, 0.2));
          padding: 15px 20px;
          border-bottom: 1px solid rgba(139, 92, 246, 0.3);
        }

        .power-rankings-title {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.1rem;
          font-weight: 700;
          color: #d946ef;
          text-transform: uppercase;
          letter-spacing: 2px;
          margin: 0;
          display: flex;
          align-items: center;
          gap: 10px;
        }

        .power-rankings-title::before {
          content: '👑';
        }

        .power-rankings-list {
          max-height: 600px;
          overflow-y: auto;
          scrollbar-width: thin;
          scrollbar-color: #8b5cf6 rgba(20, 20, 30, 0.5);
        }

        .power-rankings-list::-webkit-scrollbar {
          width: 6px;
        }

        .power-rankings-list::-webkit-scrollbar-track {
          background: rgba(20, 20, 30, 0.5);
        }

        .power-rankings-list::-webkit-scrollbar-thumb {
          background: #8b5cf6;
          border-radius: 3px;
        }

        .ranking-item {
          display: grid;
          grid-template-columns: 45px 40px 1fr 80px;
          gap: 10px;
          align-items: center;
          padding: 12px 15px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.05);
          transition: background 0.2s ease;
          cursor: pointer;
        }

        .ranking-item:hover {
          background: rgba(139, 92, 246, 0.15);
        }

        .ranking-item:last-child {
          border-bottom: none;
        }

        .ranking-position {
          font-family: 'Orbitron', sans-serif;
          font-size: 1rem;
          font-weight: 700;
          text-align: center;
        }

        .ranking-position.top-3 {
          color: #ffd700;
          text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
        }

        .ranking-position.top-5 {
          color: #c0c0c0;
        }

        .ranking-position.top-10 {
          color: #cd7f32;
        }

        .ranking-position.other {
          color: #a0a0b0;
        }

        .ranking-logo {
          width: 36px;
          height: 36px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 6px;
          overflow: hidden;
          background: rgba(255, 255, 255, 0.05);
        }

        .ranking-logo img {
          max-width: 100%;
          max-height: 100%;
          object-fit: contain;
        }

        .ranking-logo .initials {
          font-family: 'Orbitron', sans-serif;
          font-size: 0.7rem;
          font-weight: 700;
          color: #8b5cf6;
        }

        .ranking-team-info {
          overflow: hidden;
        }

        .ranking-team-name {
          font-family: 'Rajdhani', sans-serif;
          font-size: 0.95rem;
          font-weight: 600;
          color: #ffffff;
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .ranking-team-record {
          font-size: 0.75rem;
          color: #a0a0b0;
          display: flex;
          align-items: center;
          gap: 8px;
          margin-top: 2px;
        }

        .ranking-team-record .wins {
          color: #22c55e;
        }

        .ranking-team-record .losses {
          color: #ef4444;
        }

        .ranking-team-record .ties {
          color: #a0a0b0;
        }

        .ranking-ovr {
          font-family: 'Orbitron', sans-serif;
          font-size: 1.2rem;
          font-weight: 900;
          text-align: right;
        }

        .ranking-ovr.elite {
          background: linear-gradient(135deg, #ffd700, #b8860b);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .ranking-ovr.great {
          color: #22c55e;
        }

        .ranking-ovr.good {
          color: #06b6d4;
        }

        .ranking-ovr.average {
          color: #a0a0b0;
        }

        .ranking-division {
          font-size: 0.65rem;
          color: #06b6d4;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .power-rankings-loading {
          padding: 40px;
          text-align: center;
          font-family: 'Orbitron', sans-serif;
          color: #8b5cf6;
        }

        .power-rankings-footer {
          padding: 10px 15px;
          background: rgba(0, 0, 0, 0.2);
          text-align: center;
          font-size: 0.7rem;
          color: #a0a0b0;
        }

        .power-rankings-methodology {
          font-size: 0.65rem;
          color: #666;
          padding: 8px 15px;
          background: rgba(0, 0, 0, 0.15);
          border-top: 1px solid rgba(255, 255, 255, 0.05);
        }
      `}</style>

      <div className="power-rankings-container">
        <div className="power-rankings-header">
          <h3 className="power-rankings-title">Prodigy Power Rankings</h3>
        </div>

        <div className="power-rankings-list">
          {rankings.map((team) => {
            const positionClass = team.rank <= 3 ? 'top-3' : team.rank <= 5 ? 'top-5' : team.rank <= 10 ? 'top-10' : 'other';
            const ovrClass = team.ovr >= 90 ? 'elite' : team.ovr >= 80 ? 'great' : team.ovr >= 75 ? 'good' : 'average';

            return (
              <div
                key={team.teamId}
                className="ranking-item"
                onClick={() => onTeamClick?.(team.teamId)}
              >
                <div className={`ranking-position ${positionClass}`}>
                  #{team.rank}
                </div>
                <div className="ranking-logo">
                  {team.logoUrl ? (
                    <img src={team.logoUrl} alt={team.name} />
                  ) : (
                    <span className="initials">
                      {team.shortName?.slice(0, 2).toUpperCase() || team.name.split(' ').map(w => w[0]).join('').slice(0, 2)}
                    </span>
                  )}
                </div>
                <div className="ranking-team-info">
                  <div className="ranking-team-name">{team.shortName || team.name}</div>
                  <div className="ranking-team-record">
                    <span className="ranking-division">{team.division}</span>
                    <span>
                      <span className="wins">{team.record.wins}W</span>-
                      <span className="losses">{team.record.losses}L</span>-
                      <span className="ties">{team.record.ties}T</span>
                    </span>
                  </div>
                </div>
                <div className={`ranking-ovr ${ovrClass}`}>
                  {team.ovr}
                </div>
              </div>
            );
          })}
        </div>

        <div className="power-rankings-methodology">
          Performance (70%) + Roster (30%) | JSPR, NEHJ, ELO, MHR, Win%, Form
        </div>

        <div className="power-rankings-footer">
          Updated daily during season
        </div>
      </div>
    </>
  );
}

export default NepsacPowerRankings;

import { useState } from 'react';
import { getTeamCardUrl, hasTeamCardImages, getImageSlug } from '@/lib/team-logos';

interface TeamCardProps {
  teamId: string;
  teamName?: string;
  isHome: boolean;
  className?: string;
  showBothSides?: boolean;
}

/**
 * Displays team trading card images from the nepsac-cards folder
 * These are the stylized card images, not team logos
 */
export default function TeamCard({
  teamId,
  teamName,
  isHome,
  className = '',
  showBothSides = false,
}: TeamCardProps) {
  const [imageError, setImageError] = useState(false);

  const leftUrl = getTeamCardUrl(teamId, isHome, 'left');
  const rightUrl = getTeamCardUrl(teamId, isHome, 'right');
  const hasCards = hasTeamCardImages(teamId);

  // Fallback placeholder for teams without cards
  const placeholderUrl = '/images/nepsac/placeholder-card.webp';

  if (!hasCards || imageError) {
    return (
      <div className={`team-card-placeholder ${className}`}>
        <div className="w-full h-full bg-gradient-to-br from-purple-900/50 to-slate-900/50 rounded-lg flex items-center justify-center border border-purple-500/30">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400 uppercase tracking-wider">
              {teamName || getImageSlug(teamId).replace(/-/g, ' ')}
            </div>
            <div className="text-sm text-white/50 mt-2">
              {isHome ? 'HOME' : 'AWAY'}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (showBothSides) {
    return (
      <div className={`team-card-container flex gap-2 ${className}`}>
        <img
          src={leftUrl || placeholderUrl}
          alt={`${teamName || teamId} card left`}
          className="team-card-image rounded-lg shadow-lg"
          onError={() => setImageError(true)}
        />
        <img
          src={rightUrl || placeholderUrl}
          alt={`${teamName || teamId} card right`}
          className="team-card-image rounded-lg shadow-lg"
          onError={() => setImageError(true)}
        />
      </div>
    );
  }

  // Single card (left side by default)
  return (
    <div className={`team-card-container ${className}`}>
      <img
        src={leftUrl || placeholderUrl}
        alt={`${teamName || teamId} card`}
        className="team-card-image rounded-lg shadow-lg w-full h-auto"
        onError={() => setImageError(true)}
      />
    </div>
  );
}

/**
 * Displays a matchup with both teams' trading cards side by side
 */
interface TeamCardMatchupProps {
  awayTeamId: string;
  homeTeamId: string;
  awayTeamName?: string;
  homeTeamName?: string;
  className?: string;
}

export function TeamCardMatchup({
  awayTeamId,
  homeTeamId,
  awayTeamName,
  homeTeamName,
  className = '',
}: TeamCardMatchupProps) {
  return (
    <div className={`team-card-matchup flex items-center justify-center gap-4 ${className}`}>
      <TeamCard
        teamId={awayTeamId}
        teamName={awayTeamName}
        isHome={false}
        className="w-48"
      />
      <div className="vs-badge font-bold text-2xl text-fuchsia-400">VS</div>
      <TeamCard
        teamId={homeTeamId}
        teamName={homeTeamName}
        isHome={true}
        className="w-48"
      />
    </div>
  );
}

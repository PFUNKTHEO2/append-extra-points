import { motion } from 'framer-motion';
import { User } from 'lucide-react';
import type { NepsacPlayer } from '@/lib/nepsac-api';
import { getOvrColor, getOvrGradient, getPositionColor } from '@/lib/nepsac-api';
import { cn } from '@/lib/utils';

interface NepsacPlayerCardProps {
  player: NepsacPlayer;
  rank?: number;
  size?: 'sm' | 'md' | 'lg';
  showDetails?: boolean;
  delay?: number;
}

export default function NepsacPlayerCard({
  player,
  rank,
  size = 'md',
  showDetails = true,
  delay = 0,
}: NepsacPlayerCardProps) {
  const sizeClasses = {
    sm: {
      container: 'w-20 h-28',
      ovr: 'text-lg',
      ovrBadge: 'w-8 h-8',
      name: 'text-[10px]',
      icon: 'w-8 h-8',
      position: 'text-[8px] px-1',
    },
    md: {
      container: 'w-28 h-36',
      ovr: 'text-2xl',
      ovrBadge: 'w-10 h-10',
      name: 'text-xs',
      icon: 'w-12 h-12',
      position: 'text-[10px] px-1.5',
    },
    lg: {
      container: 'w-36 h-48',
      ovr: 'text-3xl',
      ovrBadge: 'w-14 h-14',
      name: 'text-sm',
      icon: 'w-16 h-16',
      position: 'text-xs px-2',
    },
  };

  const s = sizeClasses[size];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ delay: delay * 0.1, duration: 0.3, ease: 'easeOut' }}
      whileHover={{ scale: 1.05, y: -4 }}
      className={cn(
        s.container,
        'relative rounded-lg overflow-hidden cursor-pointer',
        'bg-gradient-to-b border',
        getOvrGradient(player.ovr),
        'backdrop-blur-sm'
      )}
    >
      {/* Rank Badge (optional) */}
      {rank && (
        <div className="absolute top-1 left-1 z-20">
          <span className="text-[10px] font-bold text-white/60">#{rank}</span>
        </div>
      )}

      {/* OVR Badge - Top Right */}
      <div className="absolute top-1 right-1 z-20">
        <div
          className={cn(
            s.ovrBadge,
            'rounded-md flex items-center justify-center',
            'bg-black/60 backdrop-blur-sm border border-white/20'
          )}
        >
          <span className={cn(s.ovr, 'font-bold', getOvrColor(player.ovr))}>
            {player.ovr}
          </span>
        </div>
      </div>

      {/* Player Image / Placeholder */}
      <div className="flex-1 flex items-center justify-center pt-10 pb-2">
        {player.imageUrl ? (
          <img
            src={player.imageUrl}
            alt={player.name}
            className={cn(s.icon, 'rounded-full object-cover border-2 border-white/20')}
          />
        ) : (
          <div
            className={cn(
              s.icon,
              'rounded-full bg-white/10 flex items-center justify-center',
              'border-2 border-white/20'
            )}
          >
            <User className="w-1/2 h-1/2 text-white/40" />
          </div>
        )}
      </div>

      {/* Player Info - Bottom */}
      <div className="absolute bottom-0 left-0 right-0 bg-black/60 backdrop-blur-sm p-1.5">
        {/* Name */}
        <p
          className={cn(
            s.name,
            'font-semibold text-white text-center truncate leading-tight'
          )}
          title={player.name}
        >
          {player.name}
        </p>

        {/* Position & Grad Year */}
        {showDetails && (
          <div className="flex items-center justify-center gap-1 mt-0.5">
            <span
              className={cn(
                s.position,
                'py-0.5 rounded font-semibold border',
                getPositionColor(player.position)
              )}
            >
              {player.position}
            </span>
            {player.gradYear && (
              <span className={cn(s.position, 'text-white/50')}>
                '{String(player.gradYear).slice(-2)}
              </span>
            )}
          </div>
        )}

        {/* Season Stats (GP-G-A) or ProdigyPoints fallback */}
        {showDetails && size !== 'sm' && (
          <p className="text-[9px] text-white/40 text-center mt-0.5">
            {player.stats?.gp ? (
              <span className="text-white/60">
                {player.stats.gp}GP {player.stats.goals ?? 0}G {player.stats.assists ?? 0}A
              </span>
            ) : (
              <span>{player.prodigyPoints.toLocaleString()} pts</span>
            )}
          </p>
        )}
      </div>

      {/* Glow effect for high OVR */}
      {player.ovr >= 90 && (
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-t from-yellow-500/10 to-transparent" />
          <div className="absolute -inset-1 bg-yellow-500/5 blur-xl" />
        </div>
      )}
    </motion.div>
  );
}

// Grid of player cards for a team
interface NepsacPlayerGridProps {
  players: NepsacPlayer[];
  maxPlayers?: number;
  size?: 'sm' | 'md' | 'lg';
}

export function NepsacPlayerGrid({
  players,
  maxPlayers = 6,
  size = 'md',
}: NepsacPlayerGridProps) {
  const displayPlayers = players.slice(0, maxPlayers);

  return (
    <div className="flex flex-wrap justify-center gap-2">
      {displayPlayers.map((player, index) => (
        <NepsacPlayerCard
          key={player.playerId || index}
          player={player}
          rank={index + 1}
          size={size}
          delay={index}
        />
      ))}
    </div>
  );
}

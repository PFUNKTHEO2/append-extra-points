import { motion } from 'framer-motion';
import { Swords, Clock, MapPin, Calendar, TrendingUp, Zap } from 'lucide-react';
import type { NepsacMatchup as MatchupType, NepsacMatchupTeam } from '@/lib/nepsac-api';
import { getConfidenceColor, formatGameDate } from '@/lib/nepsac-api';
import { cn } from '@/lib/utils';
import NepsacTeamCard from './NepsacTeamCard';
import { NepsacPlayerGrid } from './NepsacPlayerCard';

interface NepsacMatchupProps {
  matchup: MatchupType;
}

export default function NepsacMatchup({ matchup }: NepsacMatchupProps) {
  const { game, awayTeam, homeTeam } = matchup;
  const predictedWinner =
    game.prediction.winnerId === awayTeam.teamId ? 'away' : 'home';
  const confidence = game.prediction.confidence || 50;
  const confidenceOdds = game.prediction.confidenceOdds;

  return (
    <div className="space-y-8">
      {/* Header - Game Info */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-3xl md:text-4xl font-black text-white uppercase tracking-wider">
          NEPSAC GameDay
        </h1>
        <div className="flex items-center justify-center gap-4 text-sm text-white/60">
          <span className="flex items-center gap-1">
            <Calendar className="w-4 h-4" />
            {formatGameDate(game.date)}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-4 h-4" />
            {game.time}
          </span>
          {game.venue && (
            <span className="flex items-center gap-1">
              <MapPin className="w-4 h-4" />
              {game.venue}
            </span>
          )}
        </div>
      </motion.div>

      {/* Team vs Team Header */}
      <div className="grid grid-cols-[1fr,auto,1fr] gap-4 md:gap-8 items-center">
        {/* Away Team */}
        <NepsacTeamCard
          team={awayTeam}
          side="right"
          size="lg"
          showStats
          isWinner={game.status === 'final' && game.score ? game.score.away > game.score.home : false}
          delay={1}
        />

        {/* VS Badge */}
        <motion.div
          initial={{ scale: 0, rotate: -180 }}
          animate={{ scale: 1, rotate: 0 }}
          transition={{ delay: 0.3, type: 'spring', stiffness: 200 }}
          className="flex flex-col items-center"
        >
          <div className="w-16 h-16 md:w-20 md:h-20 rounded-full bg-gradient-to-br from-fuchsia-500 to-purple-600 flex items-center justify-center shadow-lg shadow-fuchsia-500/30">
            <Swords className="w-8 h-8 md:w-10 md:h-10 text-white" />
          </div>
          <span className="text-2xl font-black text-white mt-2">VS</span>
        </motion.div>

        {/* Home Team */}
        <NepsacTeamCard
          team={homeTeam}
          side="left"
          size="lg"
          showStats
          isWinner={game.status === 'final' && game.score ? game.score.home > game.score.away : false}
          delay={2}
        />
      </div>

      {/* Prediction Bar */}
      <PredictionBar
        awayTeam={awayTeam}
        homeTeam={homeTeam}
        predictedWinner={predictedWinner}
        confidence={confidence}
        confidenceOdds={confidenceOdds}
      />

      {/* Head-to-Head Stats */}
      <div className="space-y-4">
        <h2 className="text-xl font-bold text-white text-center uppercase tracking-wide flex items-center justify-center gap-2">
          <Zap className="w-5 h-5 text-fuchsia-400" />
          Head to Head
          <Zap className="w-5 h-5 text-fuchsia-400" />
        </h2>
        <ComparisonBars awayTeam={awayTeam} homeTeam={homeTeam} />
      </div>

      {/* Top Players */}
      <div className="space-y-6">
        <h2 className="text-xl font-bold text-white text-center uppercase tracking-wide">
          Top 6 Players
        </h2>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Away Team Players */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white/70 text-center uppercase">
              {awayTeam.shortName || awayTeam.name}
            </h3>
            <NepsacPlayerGrid players={awayTeam.topPlayers} maxPlayers={6} size="md" />
          </div>

          {/* Home Team Players */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold text-white/70 text-center uppercase">
              {homeTeam.shortName || homeTeam.name}
            </h3>
            <NepsacPlayerGrid players={homeTeam.topPlayers} maxPlayers={6} size="md" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Prediction slider/bar component
function PredictionBar({
  awayTeam,
  homeTeam,
  predictedWinner,
  confidence,
  confidenceOdds,
}: {
  awayTeam: NepsacMatchupTeam;
  homeTeam: NepsacMatchupTeam;
  predictedWinner: 'away' | 'home';
  confidence: number;
  confidenceOdds: string | null | undefined;
}) {
  // Calculate slider position (0-100)
  // 50 = even, <50 = away favorite, >50 = home favorite
  const sliderPosition = predictedWinner === 'away' ? 50 - (confidence - 50) : 50 + (confidence - 50);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.5 }}
      className="space-y-3"
    >
      <div className="flex justify-between items-center text-sm">
        <span className="text-white/70">{awayTeam.shortName || awayTeam.name}</span>
        <span className="flex items-center gap-1 text-white/50">
          <TrendingUp className="w-4 h-4 text-fuchsia-400" />
          Prediction
        </span>
        <span className="text-white/70">{homeTeam.shortName || homeTeam.name}</span>
      </div>

      {/* Prediction Bar */}
      <div className="relative h-8 bg-white/5 rounded-full overflow-hidden">
        {/* Away Side (gradient) */}
        <div
          className="absolute inset-y-0 left-0 bg-gradient-to-r from-cyan-500/40 to-transparent"
          style={{ width: `${100 - sliderPosition}%` }}
        />

        {/* Home Side (gradient) */}
        <div
          className="absolute inset-y-0 right-0 bg-gradient-to-l from-fuchsia-500/40 to-transparent"
          style={{ width: `${sliderPosition}%` }}
        />

        {/* Center Line */}
        <div className="absolute left-1/2 top-0 bottom-0 w-px bg-white/20" />

        {/* Confidence Marker */}
        <motion.div
          initial={{ left: '50%' }}
          animate={{ left: `${sliderPosition}%` }}
          transition={{ delay: 0.7, type: 'spring', stiffness: 100 }}
          className="absolute top-0 bottom-0 w-1"
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white shadow-lg" />
          <div className="h-full w-1 bg-white mx-auto" />
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-white shadow-lg" />
        </motion.div>
      </div>

      {/* Confidence Display */}
      <div className="text-center">
        <span className={cn('text-lg font-bold', getConfidenceColor(confidence))}>
          {confidence}%
        </span>
        {confidenceOdds && (
          <span className="text-lg font-bold text-white/80 ml-2">
            ({confidenceOdds})
          </span>
        )}
        <span className="text-sm text-white/50 ml-2">
          for {predictedWinner === 'away' ? awayTeam.shortName : homeTeam.shortName}
        </span>
      </div>
    </motion.div>
  );
}

// Head-to-head comparison bars
function ComparisonBars({
  awayTeam,
  homeTeam,
}: {
  awayTeam: NepsacMatchupTeam;
  homeTeam: NepsacMatchupTeam;
}) {
  const comparisons = [
    {
      label: 'AVG POINTS',
      away: awayTeam.stats.avgPoints,
      home: homeTeam.stats.avgPoints,
      format: (v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 0 }),
    },
    {
      label: 'TOP PLAYER',
      away: awayTeam.stats.maxPoints,
      home: homeTeam.stats.maxPoints,
      format: (v: number) => v.toLocaleString(undefined, { maximumFractionDigits: 0 }),
    },
    {
      label: 'TOTAL POINTS',
      away: awayTeam.stats.totalPoints,
      home: homeTeam.stats.totalPoints,
      format: (v: number) => (v / 1000).toFixed(1) + 'K',
    },
    {
      label: 'ROSTER SIZE',
      away: awayTeam.stats.rosterSize,
      home: homeTeam.stats.rosterSize,
      format: (v: number) => v.toString(),
    },
    {
      label: 'MATCH RATE',
      away: awayTeam.stats.matchRate,
      home: homeTeam.stats.matchRate,
      format: (v: number) => v.toFixed(0) + '%',
    },
  ];

  return (
    <div className="space-y-3">
      {comparisons.map((stat, index) => (
        <ComparisonBar key={stat.label} stat={stat} delay={index * 0.1} />
      ))}
    </div>
  );
}

function ComparisonBar({
  stat,
  delay,
}: {
  stat: {
    label: string;
    away: number;
    home: number;
    format: (v: number) => string;
  };
  delay: number;
}) {
  const total = stat.away + stat.home;
  const awayPct = total > 0 ? (stat.away / total) * 100 : 50;
  const homePct = 100 - awayPct;
  const awayWins = stat.away > stat.home;
  const homeWins = stat.home > stat.away;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.6 + delay }}
      className="space-y-1"
    >
      {/* Values */}
      <div className="flex justify-between items-center text-sm">
        <span className={cn('font-mono', awayWins ? 'text-cyan-400 font-bold' : 'text-white/70')}>
          {stat.format(stat.away)}
        </span>
        <span className="text-xs text-white/40 uppercase tracking-wider">
          {stat.label}
        </span>
        <span className={cn('font-mono', homeWins ? 'text-fuchsia-400 font-bold' : 'text-white/70')}>
          {stat.format(stat.home)}
        </span>
      </div>

      {/* Bar */}
      <div className="h-2 bg-white/5 rounded-full overflow-hidden flex">
        <motion.div
          initial={{ width: '50%' }}
          animate={{ width: `${awayPct}%` }}
          transition={{ delay: 0.8 + delay, duration: 0.5 }}
          className={cn(
            'h-full rounded-l-full',
            awayWins
              ? 'bg-gradient-to-r from-cyan-500 to-cyan-400'
              : 'bg-gradient-to-r from-cyan-500/50 to-cyan-400/30'
          )}
        />
        <motion.div
          initial={{ width: '50%' }}
          animate={{ width: `${homePct}%` }}
          transition={{ delay: 0.8 + delay, duration: 0.5 }}
          className={cn(
            'h-full rounded-r-full',
            homeWins
              ? 'bg-gradient-to-l from-fuchsia-500 to-fuchsia-400'
              : 'bg-gradient-to-l from-fuchsia-500/50 to-fuchsia-400/30'
          )}
        />
      </div>
    </motion.div>
  );
}

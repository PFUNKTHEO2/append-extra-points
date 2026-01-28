import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Trophy, Target, X, Minus, Calendar, TrendingUp, CheckCircle, XCircle, MinusCircle } from 'lucide-react';
import { fetchNepsacPastResults, type NepsacPastResultsResponse, type NepsacPastResultGame, type NepsacPastResultDate } from '@/lib/nepsac-api';
import { cn } from '@/lib/utils';

interface NepsacPastPerformanceProps {
  season?: string;
}

export default function NepsacPastPerformance({ season = '2025-26' }: NepsacPastPerformanceProps) {
  const [data, setData] = useState<NepsacPastResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      setLoading(true);
      setError(null);
      const result = await fetchNepsacPastResults(season, 200);
      if (result) {
        setData(result);
      } else {
        setError('Failed to load past results');
      }
      setLoading(false);
    }
    loadData();
  }, [season]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <div className="w-12 h-12 border-4 border-fuchsia-500/30 border-t-fuchsia-500 rounded-full animate-spin" />
        <p className="mt-4 text-white/60 font-medium">Loading prediction results...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="text-center py-20">
        <XCircle className="w-16 h-16 text-red-500/50 mx-auto mb-4" />
        <p className="text-white/60">{error || 'No data available'}</p>
      </div>
    );
  }

  if (data.dates.length === 0) {
    return (
      <div className="text-center py-20">
        <Trophy className="w-16 h-16 text-fuchsia-500/50 mx-auto mb-4" />
        <p className="text-white/60">No completed games with predictions yet.</p>
        <p className="text-white/40 text-sm mt-2">Check back after games are played!</p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="text-center space-y-2"
      >
        <h1 className="text-3xl md:text-4xl font-black text-white uppercase tracking-wider">
          Past Performance
        </h1>
        <p className="text-white/60">NEPSAC Prediction Tracker</p>
      </motion.div>

      {/* Stats Summary */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        <StatCard
          value={`${data.summary.accuracy}%`}
          label="Accuracy"
          icon={<Target className="w-5 h-5" />}
          highlight
        />
        <StatCard
          value={data.summary.correct}
          label="Correct"
          icon={<CheckCircle className="w-5 h-5 text-emerald-400" />}
        />
        <StatCard
          value={data.summary.incorrect}
          label="Missed"
          icon={<XCircle className="w-5 h-5 text-red-400" />}
        />
        <StatCard
          value={data.summary.totalGames}
          label="Total Games"
          icon={<Trophy className="w-5 h-5 text-amber-400" />}
        />
      </motion.div>

      {/* Game Results by Date */}
      <div className="space-y-6">
        {data.dates.map((dateData, dateIndex) => (
          <DateSection key={dateData.date} dateData={dateData} delay={dateIndex * 0.1} />
        ))}
      </div>

      {/* Model Info */}
      <ModelWeights />
    </div>
  );
}

// Stat Card Component
function StatCard({
  value,
  label,
  icon,
  highlight = false,
}: {
  value: string | number;
  label: string;
  icon: React.ReactNode;
  highlight?: boolean;
}) {
  return (
    <div
      className={cn(
        'bg-white/5 backdrop-blur-sm rounded-xl p-4 border transition-transform hover:-translate-y-1',
        highlight
          ? 'border-emerald-500/50 shadow-lg shadow-emerald-500/10'
          : 'border-white/10'
      )}
    >
      <div className="flex items-center justify-center gap-2 mb-2">
        {icon}
      </div>
      <div
        className={cn(
          'text-3xl md:text-4xl font-black text-center',
          highlight
            ? 'bg-gradient-to-r from-emerald-400 to-amber-400 bg-clip-text text-transparent'
            : 'text-white'
        )}
      >
        {value}
      </div>
      <div className="text-xs text-white/50 uppercase tracking-wider text-center mt-1">
        {label}
      </div>
    </div>
  );
}

// Date Section Component
function DateSection({ dateData, delay }: { dateData: NepsacPastResultDate; delay: number }) {
  const total = dateData.correct + dateData.incorrect + dateData.ties;
  const accuracy = total > 0 ? Math.round((dateData.correct / (total - dateData.ties)) * 100) : 0;
  const record = dateData.ties > 0
    ? `${dateData.correct}-${dateData.incorrect}-${dateData.ties}`
    : `${dateData.correct}-${dateData.incorrect}`;

  // Format date
  const formattedDate = new Date(dateData.date + 'T00:00:00').toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    year: 'numeric',
  });

  // Sort games: correct first, then incorrect, then ties
  const sortedGames = [...dateData.games].sort((a, b) => {
    const order = { correct: 0, incorrect: 1, tie: 2 };
    return order[a.result] - order[b.result];
  });

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.2 + delay }}
      className="bg-white/5 backdrop-blur-sm rounded-2xl border border-white/10 overflow-hidden"
    >
      {/* Date Header */}
      <div className="flex items-center justify-between p-4 border-b border-white/10 bg-white/5">
        <div className="flex items-center gap-2">
          <Calendar className="w-5 h-5 text-cyan-400" />
          <span className="font-bold text-white">{formattedDate}</span>
        </div>
        <div className="px-4 py-1.5 rounded-full bg-gradient-to-r from-fuchsia-500 to-purple-600 text-white text-sm font-bold">
          {record} ({accuracy}%)
        </div>
      </div>

      {/* Games Grid */}
      <div className="divide-y divide-white/5">
        {sortedGames.map((game, index) => (
          <GameResultRow key={game.gameId} game={game} delay={index * 0.05} />
        ))}
      </div>
    </motion.div>
  );
}

// Game Result Row Component
function GameResultRow({ game, delay }: { game: NepsacPastResultGame; delay: number }) {
  const getResultStyles = () => {
    switch (game.result) {
      case 'correct':
        return 'bg-emerald-500/5 border-l-emerald-500';
      case 'incorrect':
        return 'bg-red-500/5 border-l-red-500';
      case 'tie':
        return 'bg-amber-500/5 border-l-amber-500';
    }
  };

  const getResultIcon = () => {
    switch (game.result) {
      case 'correct':
        return <CheckCircle className="w-5 h-5 text-emerald-400" />;
      case 'incorrect':
        return <XCircle className="w-5 h-5 text-red-400" />;
      case 'tie':
        return <MinusCircle className="w-5 h-5 text-amber-400" />;
    }
  };

  const getConfidenceClass = (confidence: number) => {
    if (confidence >= 65) return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50';
    if (confidence >= 55) return 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50';
    return 'bg-white/10 text-white/60 border-white/20';
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ delay: 0.3 + delay }}
      className={cn(
        'grid grid-cols-[1fr,auto,1fr,auto] items-center gap-2 md:gap-4 p-3 md:p-4 border-l-4',
        getResultStyles()
      )}
    >
      {/* Away Team */}
      <div className="text-right">
        <span
          className={cn(
            'font-semibold text-sm md:text-base',
            game.awayTeam.isWinner && 'text-emerald-400',
            game.awayTeam.wasPredicted && 'underline decoration-fuchsia-500 underline-offset-4'
          )}
        >
          {game.awayTeam.shortName || game.awayTeam.name}
        </span>
      </div>

      {/* Score */}
      <div className="flex items-center gap-2 md:gap-3 font-mono font-bold text-lg md:text-xl">
        <span className={cn(game.awayTeam.isWinner && 'text-emerald-400')}>
          {game.awayTeam.score}
        </span>
        <span className="text-white/30">-</span>
        <span className={cn(game.homeTeam.isWinner && 'text-emerald-400')}>
          {game.homeTeam.score}
        </span>
      </div>

      {/* Home Team */}
      <div className="text-left">
        <span
          className={cn(
            'font-semibold text-sm md:text-base',
            game.homeTeam.isWinner && 'text-emerald-400',
            game.homeTeam.wasPredicted && 'underline decoration-fuchsia-500 underline-offset-4'
          )}
        >
          {game.homeTeam.shortName || game.homeTeam.name}
        </span>
      </div>

      {/* Prediction Badge */}
      <div className="flex items-center gap-2">
        <span
          className={cn(
            'px-2 py-0.5 rounded-full text-xs font-bold border',
            getConfidenceClass(game.prediction.confidence)
          )}
        >
          {game.prediction.confidence}%{game.prediction.confidenceOdds && ` (${game.prediction.confidenceOdds})`}
        </span>
        {getResultIcon()}
      </div>
    </motion.div>
  );
}

// Model Weights Component - Updated 2026-01-24 based on ML analysis
function ModelWeights() {
  const weights = [
    { label: 'MHR Rating', value: 30 },
    { label: 'Top Player', value: 15 },
    { label: 'Recent Form', value: 15 },
    { label: 'Win Pct', value: 15 },       // Increased from 2% - ML showed strong predictor
    { label: 'Head-to-Head', value: 8 },
    { label: 'ProdigyPoints', value: 7 },  // Reduced from 10%
    { label: 'Home Advantage', value: 5 }, // Reduced from 12% - missed away upsets
    { label: 'Expert Rank', value: 3 },    // Reduced from 5%
    { label: 'Goal Diff', value: 2 },      // Reduced from 3%
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.5 }}
      className="bg-white/5 backdrop-blur-sm rounded-xl border border-fuchsia-500/30 p-6"
    >
      <h3 className="text-lg font-bold text-fuchsia-400 mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5" />
        Model v2.1 Weights
      </h3>
      <div className="space-y-3">
        {weights.map((w) => (
          <div key={w.label} className="flex items-center gap-3">
            <span className="w-32 text-sm text-white/60">{w.label}</span>
            <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-fuchsia-500 to-purple-500 rounded-full"
                style={{ width: `${(w.value / 30) * 100}%` }}
              />
            </div>
            <span className="w-10 text-right text-sm font-mono text-cyan-400">{w.value}%</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

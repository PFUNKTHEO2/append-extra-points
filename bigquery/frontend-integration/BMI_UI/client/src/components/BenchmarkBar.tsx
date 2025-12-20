import { BenchmarkStatus } from "@/lib/bmi";
import { motion } from "framer-motion";

interface BenchmarkBarProps {
  label: string;
  value: number;
  range: [number, number];
  nhlValue: number;
  unit: string;
  status: BenchmarkStatus;
}

export default function BenchmarkBar({
  label,
  value,
  range,
  nhlValue,
  unit,
  status,
}: BenchmarkBarProps) {
  const [min, max] = range;

  // Calculate visual range with padding for out-of-range values
  const padding = (max - min) * 0.3;
  const visualMin = min - padding;
  const visualMax = max + padding;
  const visualRange = visualMax - visualMin;

  // Calculate positions as percentages
  const getPosition = (val: number) => {
    const pos = ((val - visualMin) / visualRange) * 100;
    return Math.max(0, Math.min(100, pos));
  };

  const rangeStartPos = getPosition(min);
  const rangeEndPos = getPosition(max);
  const rangeWidth = rangeEndPos - rangeStartPos;
  const valuePos = getPosition(value);
  const nhlPos = getPosition(nhlValue);

  const statusColors = {
    below: { bg: 'bg-amber-500', text: 'text-amber-400' },
    within: { bg: 'bg-green-500', text: 'text-green-400' },
    above: { bg: 'bg-red-500', text: 'text-red-400' },
  };

  return (
    <div className="space-y-2">
      {/* Range Labels */}
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>{min}{unit}</span>
        <span className="text-[#d946ef]">NHL: {nhlValue}{unit}</span>
        <span>{max}{unit}</span>
      </div>

      {/* Bar Container */}
      <div className="relative h-6 bg-white/5 rounded-full overflow-hidden">
        {/* Optimal Range Zone */}
        <div
          className="absolute h-full bg-green-500/30 border-x border-green-500/50"
          style={{
            left: `${rangeStartPos}%`,
            width: `${rangeWidth}%`,
          }}
        />

        {/* NHL Marker */}
        <div
          className="absolute h-full w-0.5 bg-[#d946ef] z-10"
          style={{ left: `${nhlPos}%` }}
        >
          <div className="absolute -top-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-[#d946ef] rounded-full" />
        </div>

        {/* Current Value Marker */}
        <motion.div
          className={`absolute h-full w-1 ${statusColors[status].bg} z-20`}
          initial={{ left: '50%' }}
          animate={{ left: `${valuePos}%` }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
        >
          <div className={`absolute -top-1 left-1/2 -translate-x-1/2 w-3 h-3 ${statusColors[status].bg} rounded-full shadow-lg`} />
        </motion.div>
      </div>

      {/* Status Label */}
      <div className="flex justify-center">
        <span className={`text-xs font-medium ${statusColors[status].text}`}>
          {status === 'within' ? 'Within optimal range' : status === 'below' ? 'Below optimal range' : 'Above optimal range'}
        </span>
      </div>
    </div>
  );
}

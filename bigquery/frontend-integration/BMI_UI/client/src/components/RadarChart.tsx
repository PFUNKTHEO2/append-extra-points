import { motion } from "framer-motion";

interface RadarChartProps {
  stats: {
    speed: number;
    power: number;
    skill: number;
  };
}

export default function RadarChart({ stats }: RadarChartProps) {
  // Normalize stats to 0-100 range for the chart
  // The chart is a triangle/hexagon for 3 axes
  // Axes: Top (Speed), Bottom Right (Power), Bottom Left (Skill)
  
  const size = 200;
  const center = size / 2;
  const radius = size * 0.4; // 40% of size

  // Calculate points for the 3 axes
  // 0 degrees is top (Speed)
  // 120 degrees is bottom right (Power)
  // 240 degrees is bottom left (Skill)
  
  const getPoint = (value: number, angle: number) => {
    const r = (value / 100) * radius;
    const x = center + r * Math.sin(angle * (Math.PI / 180));
    const y = center - r * Math.cos(angle * (Math.PI / 180));
    return `${x},${y}`;
  };

  const speedPoint = getPoint(stats.speed, 0);
  const powerPoint = getPoint(stats.power, 120);
  const skillPoint = getPoint(stats.skill, 240);

  const polyPoints = `${speedPoint} ${powerPoint} ${skillPoint}`;

  // Background grid (concentric triangles)
  const levels = [100, 75, 50, 25];

  return (
    <div className="relative w-[200px] h-[200px] flex items-center justify-center">
      <svg width={size} height={size} className="overflow-visible">
        {/* Background Grid */}
        {levels.map((level, i) => {
          const p1 = getPoint(level, 0);
          const p2 = getPoint(level, 120);
          const p3 = getPoint(level, 240);
          return (
            <polygon
              key={level}
              points={`${p1} ${p2} ${p3}`}
              fill="none"
              stroke="rgba(255, 255, 255, 0.1)"
              strokeWidth="1"
            />
          );
        })}

        {/* Axes Lines */}
        <line x1={center} y1={center} x2={getPoint(100, 0).split(',')[0]} y2={getPoint(100, 0).split(',')[1]} stroke="rgba(255, 255, 255, 0.1)" />
        <line x1={center} y1={center} x2={getPoint(100, 120).split(',')[0]} y2={getPoint(100, 120).split(',')[1]} stroke="rgba(255, 255, 255, 0.1)" />
        <line x1={center} y1={center} x2={getPoint(100, 240).split(',')[0]} y2={getPoint(100, 240).split(',')[1]} stroke="rgba(255, 255, 255, 0.1)" />

        {/* The Data Polygon */}
        <motion.polygon
          points={polyPoints}
          fill="rgba(217, 70, 239, 0.3)" // Neon Pink fill
          stroke="#d946ef" // Neon Pink stroke
          strokeWidth="2"
          initial={{ opacity: 0 }}
          animate={{ points: polyPoints, opacity: 1 }}
          transition={{ type: "spring", stiffness: 100, damping: 20 }}
          style={{ filter: "drop-shadow(0 0 8px #d946ef)" }}
        />

        {/* Data Points (Dots) */}
        {[
          { val: stats.speed, angle: 0 },
          { val: stats.power, angle: 120 },
          { val: stats.skill, angle: 240 }
        ].map((item, i) => {
          const [cx, cy] = getPoint(item.val, item.angle).split(',');
          return (
            <motion.circle
              key={i}
              cx={cx}
              cy={cy}
              r="4"
              fill="#fff"
              animate={{ cx, cy }}
              transition={{ type: "spring", stiffness: 100, damping: 20 }}
            />
          );
        })}
      </svg>

      {/* Labels */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-2 text-xs font-bold text-primary uppercase tracking-wider">Speed</div>
      <div className="absolute bottom-4 right-0 translate-x-2 text-xs font-bold text-primary uppercase tracking-wider">Power</div>
      <div className="absolute bottom-4 left-0 -translate-x-2 text-xs font-bold text-primary uppercase tracking-wider">Skill</div>
      
      {/* Values */}
      <div className="absolute top-4 left-1/2 -translate-x-1/2 text-[10px] text-white font-mono">{Math.round(stats.speed)}</div>
      <div className="absolute bottom-8 right-4 text-[10px] text-white font-mono">{Math.round(stats.power)}</div>
      <div className="absolute bottom-8 left-4 text-[10px] text-white font-mono">{Math.round(stats.skill)}</div>
    </div>
  );
}

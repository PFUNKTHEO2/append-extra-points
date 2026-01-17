import { BodyStats, AgeCategory, Position, NHLBenchmark, PhysicalRange, UnitSystem, metricToImperial } from "@/lib/bmi";
import { motion } from "framer-motion";

interface PlayerGraphicProps {
  stats: BodyStats;
  position: Position;
  ageCategory: AgeCategory;
  nhlBenchmark: NHLBenchmark;
  optimalRange: PhysicalRange;
  unitSystem: UnitSystem;
}

interface BodyModelProps {
  label: string;
  sublabel?: string;
  height: number;
  weight: number;
  bmi: number;
  accentColor: string;
  // Scale relative to reference (1.0 = reference height)
  heightScale: number;
  widthScale: number;
  delay?: number;
  unitSystem: UnitSystem;
}

function BodyModel({ label, sublabel, height, weight, bmi, accentColor, heightScale, widthScale, delay = 0, unitSystem }: BodyModelProps) {
  // Select image based on BMI
  const getPlayerImage = (bmi: number) => {
    if (bmi < 22) return '/images/mesh-aligned-lean-transparent.png';
    if (bmi > 28) return '/images/mesh-aligned-heavy-transparent.png';
    return '/images/mesh-aligned-athletic-transparent.png';
  };

  const image = getPlayerImage(bmi);

  // Container height that fits the tallest possible figure
  const containerHeight = 340;
  // The tallest figure (scale 1.0) uses this base height
  const maxFigureHeight = 320;
  // Actual height for this figure based on its scale
  const actualHeight = maxFigureHeight * heightScale;

  // Convert to imperial if needed
  const imperial = metricToImperial(height, weight);
  const displayHeight = unitSystem === 'imperial' ? `${imperial.feet}'${imperial.inches}"` : height;
  const displayWeight = unitSystem === 'imperial' ? imperial.lbs : weight;
  const heightUnit = unitSystem === 'imperial' ? '' : 'cm';
  const weightUnit = unitSystem === 'imperial' ? 'lbs' : 'kg';

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      className="flex flex-col items-center"
      style={{ width: '160px' }}
    >
      {/* Label */}
      <div className="text-center mb-2">
        <h3
          className="text-sm font-heading font-bold uppercase tracking-wide"
          style={{ color: accentColor }}
        >
          {label}
        </h3>
        {sublabel && (
          <p className="text-[10px] text-muted-foreground">{sublabel}</p>
        )}
      </div>

      {/* Body Model Container - Fixed height, bottom-aligned */}
      <div
        className="relative flex items-end justify-center"
        style={{ height: `${containerHeight}px` }}
      >
        <motion.img
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: delay + 0.2 }}
          src={image}
          alt={`${label} Body Model`}
          style={{
            height: `${actualHeight}px`,
            transform: `scaleX(${widthScale})`,
            transformOrigin: 'bottom center',
            filter: `drop-shadow(0 0 15px ${accentColor})`,
          }}
        />
      </div>

      {/* Stats */}
      <div
        className="bg-black/60 backdrop-blur-md p-2 rounded-lg border mt-3 w-full"
        style={{ borderColor: `${accentColor}50` }}
      >
        <div className="grid grid-cols-3 gap-1 text-center">
          <div>
            <div className="text-base font-bold text-white">{displayHeight}</div>
            <div className="text-[9px] text-muted-foreground uppercase">{heightUnit}</div>
          </div>
          <div>
            <div className="text-base font-bold text-white">{displayWeight}</div>
            <div className="text-[9px] text-muted-foreground uppercase">{weightUnit}</div>
          </div>
          <div>
            <div className="text-base font-bold" style={{ color: accentColor }}>{bmi}</div>
            <div className="text-[9px] text-muted-foreground uppercase">BMI</div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}

export default function PlayerGraphic({ stats, position, ageCategory, nhlBenchmark, optimalRange, unitSystem }: PlayerGraphicProps) {
  // Calculate optimal range midpoints
  const optimalBMI = Math.round(((optimalRange.bmi[0] + optimalRange.bmi[1]) / 2) * 10) / 10;
  const optimalHeight = Math.round((optimalRange.height[0] + optimalRange.height[1]) / 2);
  const optimalWeight = Math.round((optimalRange.weight[0] + optimalRange.weight[1]) / 2);

  const positionLabel = position.charAt(0).toUpperCase() + position.slice(1);

  // Find the tallest height to use as reference (scale = 1.0)
  const maxHeight = Math.max(stats.height, optimalHeight, nhlBenchmark.height);

  // Calculate relative scales for each figure
  // Height scale: proportional to actual height difference
  const playerHeightScale = stats.height / maxHeight;
  const optimalHeightScale = optimalHeight / maxHeight;
  const nhlHeightScale = nhlBenchmark.height / maxHeight;

  // Width scale: based on BMI with visible differences
  // Reference BMI of 22 = 100% width
  // Minimum 60% (very underweight but not skeletal)
  // Maximum 150% (very overweight)
  const calculateWidthScale = (bmi: number): number => {
    if (bmi < 14) return 0.60; // Floor at 60%
    if (bmi < 16) return 0.60 + (bmi - 14) * 0.05; // 60% to 70%
    if (bmi < 18.5) return 0.70 + (bmi - 16) * 0.06; // 70% to 85%
    if (bmi < 22) return 0.85 + (bmi - 18.5) * 0.043; // 85% to 100%
    if (bmi < 25) return 1.0 + (bmi - 22) * 0.05; // 100% to 115%
    if (bmi < 30) return 1.15 + (bmi - 25) * 0.04; // 115% to 135%
    return Math.min(1.50, 1.35 + (bmi - 30) * 0.02); // 135% to max 150%
  };

  const playerWidthScale = calculateWidthScale(stats.bmi);
  const optimalWidthScale = calculateWidthScale(optimalBMI);
  const nhlWidthScale = calculateWidthScale(nhlBenchmark.bmi);

  return (
    <div className="relative w-full h-full flex flex-col overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 bg-[url('/images/frost-texture.jpg')] opacity-20 mix-blend-overlay pointer-events-none"></div>
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.05)_1px,transparent_1px)] bg-[size:50px_50px] pointer-events-none"></div>

      {/* Main Content - Three Body Models Side by Side, Tightly Grouped */}
      <div className="relative z-10 flex-1 flex items-center justify-center p-4">
        <div className="flex items-end justify-center gap-2">
          {/* Player Model */}
          <BodyModel
            label="You"
            height={stats.height}
            weight={stats.weight}
            bmi={stats.bmi}
            accentColor="#d946ef"
            heightScale={playerHeightScale}
            widthScale={playerWidthScale}
            delay={0}
            unitSystem={unitSystem}
          />

          {/* Optimal Range Model */}
          <BodyModel
            label={`Average ${ageCategory}`}
            sublabel={`${positionLabel} benchmark`}
            height={optimalHeight}
            weight={optimalWeight}
            bmi={optimalBMI}
            accentColor="#22c55e"
            heightScale={optimalHeightScale}
            widthScale={optimalWidthScale}
            delay={0.1}
            unitSystem={unitSystem}
          />

          {/* NHL Model */}
          <BodyModel
            label={`NHL ${positionLabel}`}
            sublabel="League average"
            height={nhlBenchmark.height}
            weight={nhlBenchmark.weight}
            bmi={nhlBenchmark.bmi}
            accentColor="#8b5cf6"
            heightScale={nhlHeightScale}
            widthScale={nhlWidthScale}
            delay={0.2}
            unitSystem={unitSystem}
          />
        </div>
      </div>

      {/* Comparison Summary Bar */}
      <motion.div
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="relative z-10 bg-black/60 backdrop-blur-md border-t border-white/10 p-4"
      >
        <div className="flex justify-center gap-8">
          {/* vs Optimal */}
          <div className="text-center">
            <div className="text-xs text-muted-foreground uppercase mb-1">vs Average {ageCategory}</div>
            <div className="flex gap-4">
              <div>
                <span className={`text-sm font-bold ${stats.height - optimalHeight >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.height - optimalHeight >= 0 ? '+' : ''}{stats.height - optimalHeight} cm
                </span>
              </div>
              <div>
                <span className={`text-sm font-bold ${stats.weight - optimalWeight >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.weight - optimalWeight >= 0 ? '+' : ''}{stats.weight - optimalWeight} kg
                </span>
              </div>
              <div>
                <span className={`text-sm font-bold ${Math.abs(stats.bmi - optimalBMI) <= 1 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.bmi - optimalBMI >= 0 ? '+' : ''}{(stats.bmi - optimalBMI).toFixed(1)} BMI
                </span>
              </div>
            </div>
          </div>

          <div className="w-px bg-white/20" />

          {/* vs NHL */}
          <div className="text-center">
            <div className="text-xs text-muted-foreground uppercase mb-1">vs NHL {positionLabel}</div>
            <div className="flex gap-4">
              <div>
                <span className={`text-sm font-bold ${stats.height - nhlBenchmark.height >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.height - nhlBenchmark.height >= 0 ? '+' : ''}{stats.height - nhlBenchmark.height} cm
                </span>
              </div>
              <div>
                <span className={`text-sm font-bold ${stats.weight - nhlBenchmark.weight >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.weight - nhlBenchmark.weight >= 0 ? '+' : ''}{stats.weight - nhlBenchmark.weight} kg
                </span>
              </div>
              <div>
                <span className={`text-sm font-bold ${Math.abs(stats.bmi - nhlBenchmark.bmi) <= 1 ? 'text-green-400' : 'text-amber-400'}`}>
                  {stats.bmi - nhlBenchmark.bmi >= 0 ? '+' : ''}{(stats.bmi - nhlBenchmark.bmi).toFixed(1)} BMI
                </span>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
}

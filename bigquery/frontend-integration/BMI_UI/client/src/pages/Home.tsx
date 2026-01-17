import PlayerGraphic from "@/components/PlayerGraphic";
import BenchmarkBar from "@/components/BenchmarkBar";

import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import {
  BodyStats,
  calculateBMI,
  getBMICategory,
  imperialToMetric,
  metricToImperial,
  AgeCategory,
  Position,
  AGE_CATEGORIES,
  POSITIONS,
  PHYSICAL_STANDARDS,
  NHL_BENCHMARKS,
  getBenchmarkStatus,
  getNHLComparison,
  PhysicalRange
} from "@/lib/bmi";
import { fetchPhysicalBenchmarks, benchmarkToPhysicalRange, PhysicalBenchmarksResponse } from "@/lib/api";
import { motion } from "framer-motion";
import { useEffect, useState, useMemo } from "react";

export default function Home() {
  const [unitSystem, setUnitSystem] = useState<'metric' | 'imperial'>('metric');

  // Age & Position State
  const [ageCategory, setAgeCategory] = useState<AgeCategory>('U16');
  const [position, setPosition] = useState<Position>('forward');

  // Metric State
  const [heightCm, setHeightCm] = useState(175);
  const [weightKg, setWeightKg] = useState(70);

  // Imperial State
  const [feet, setFeet] = useState(5);
  const [inches, setInches] = useState(9);
  const [lbs, setLbs] = useState(154);

  const [stats, setStats] = useState<BodyStats>({
    height: 175,
    weight: 70,
    bmi: 22.9,
    category: 'Normal Weight'
  });

  // API data for real player benchmarks
  const [apiBenchmarks, setApiBenchmarks] = useState<PhysicalBenchmarksResponse | null>(null);
  const [isLoadingBenchmarks, setIsLoadingBenchmarks] = useState(true);

  // Fetch real player benchmarks from API on mount
  useEffect(() => {
    fetchPhysicalBenchmarks()
      .then((data) => {
        if (data) {
          setApiBenchmarks(data);
          console.log('Loaded real player benchmarks from API');
        }
      })
      .finally(() => setIsLoadingBenchmarks(false));
  }, []);

  // Get current standards based on age/position
  // Uses real API data when available, falls back to hardcoded values
  const currentStandards = useMemo((): PhysicalRange => {
    // Try to get real data from API first
    if (apiBenchmarks?.by_age_category?.[ageCategory]?.[position]) {
      const apiData = apiBenchmarks.by_age_category[ageCategory][position];
      return benchmarkToPhysicalRange(apiData);
    }
    // Fallback to hardcoded values
    return PHYSICAL_STANDARDS[position][ageCategory];
  }, [position, ageCategory, apiBenchmarks]);

  // Get sample size for current selection (for display)
  const sampleSize = useMemo(() => {
    if (apiBenchmarks?.by_age_category?.[ageCategory]?.[position]) {
      return apiBenchmarks.by_age_category[ageCategory][position].sample_size;
    }
    return null;
  }, [position, ageCategory, apiBenchmarks]);

  // Check if using real data
  const usingRealData = useMemo(() => {
    return apiBenchmarks?.by_age_category?.[ageCategory]?.[position] !== undefined;
  }, [position, ageCategory, apiBenchmarks]);

  const nhlBenchmark = useMemo(() => {
    return NHL_BENCHMARKS[position];
  }, [position]);

  const nhlComparison = useMemo(() => {
    return getNHLComparison(stats, position);
  }, [stats, position]);

  // Benchmark statuses
  const benchmarkStatuses = useMemo(() => ({
    height: getBenchmarkStatus(stats.height, currentStandards.height),
    weight: getBenchmarkStatus(stats.weight, currentStandards.weight),
    bmi: getBenchmarkStatus(stats.bmi, currentStandards.bmi),
  }), [stats, currentStandards]);

  // Update stats when inputs change
  useEffect(() => {
    let h = heightCm;
    let w = weightKg;

    if (unitSystem === 'imperial') {
      const metric = imperialToMetric(feet, inches, lbs);
      h = metric.heightCm;
      w = metric.weightKg;
    }

    const bmi = calculateBMI(h, w);
    setStats({
      height: Math.round(h),
      weight: Math.round(w),
      bmi,
      category: getBMICategory(bmi)
    });
  }, [heightCm, weightKg, feet, inches, lbs, unitSystem]);

  // Sync systems when switching
  const toggleUnitSystem = () => {
    if (unitSystem === 'metric') {
      const imp = metricToImperial(heightCm, weightKg);
      setFeet(imp.feet);
      setInches(imp.inches);
      setLbs(imp.lbs);
      setUnitSystem('imperial');
    } else {
      const met = imperialToMetric(feet, inches, lbs);
      setHeightCm(Math.round(met.heightCm));
      setWeightKg(Math.round(met.weightKg));
      setUnitSystem('metric');
    }
  };

  return (
    <div className="min-h-screen flex flex-col lg:flex-row overflow-hidden bg-background text-foreground font-body">

      {/* Left Panel - Controls (HUD Style) */}
      <motion.div
        initial={{ x: -100, opacity: 0 }}
        animate={{ x: 0, opacity: 1 }}
        className="w-full lg:w-1/3 p-6 z-20 flex flex-col relative bg-black/40 backdrop-blur-xl border-r border-white/10 overflow-y-auto"
      >
        <div className="space-y-5">
          {/* Age Category Selector */}
          <Card className="p-4 glass-panel rounded-xl">
            <Label className="text-sm font-heading uppercase text-primary mb-3 block">Age Category</Label>
            <div className="flex flex-wrap gap-2">
              {AGE_CATEGORIES.map((cat) => (
                <button
                  key={cat.value}
                  onClick={() => setAgeCategory(cat.value)}
                  className={`px-3 py-2 rounded-lg text-sm font-bold transition-all ${
                    ageCategory === cat.value
                      ? 'bg-gradient-to-r from-[#d946ef] to-[#8b5cf6] text-white'
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  {cat.label}
                  <span className="text-xs ml-1 opacity-60">({cat.birthYear})</span>
                </button>
              ))}
            </div>
          </Card>

          {/* Position Selector */}
          <Card className="p-4 glass-panel rounded-xl">
            <Label className="text-sm font-heading uppercase text-primary mb-3 block">Position</Label>
            <div className="flex gap-2">
              {POSITIONS.map((pos) => (
                <button
                  key={pos.value}
                  onClick={() => setPosition(pos.value)}
                  className={`flex-1 px-4 py-3 rounded-lg text-sm font-bold transition-all ${
                    position === pos.value
                      ? 'bg-gradient-to-r from-[#d946ef] to-[#8b5cf6] text-white'
                      : 'bg-white/10 text-white/70 hover:bg-white/20'
                  }`}
                >
                  {pos.label}
                </button>
              ))}
            </div>
          </Card>

          {/* Unit Toggle */}
          <div className="flex items-center justify-between bg-white/5 p-3 rounded-lg border border-white/10">
            <Label className="text-sm font-bold uppercase">Units</Label>
            <div className="flex items-center gap-2">
              <span className={`text-sm ${unitSystem === 'metric' ? "text-primary font-bold" : "text-muted-foreground"}`}>METRIC</span>
              <Switch checked={unitSystem === 'imperial'} onCheckedChange={toggleUnitSystem} />
              <span className={`text-sm ${unitSystem === 'imperial' ? "text-primary font-bold" : "text-muted-foreground"}`}>IMPERIAL</span>
            </div>
          </div>

          {/* Height Controls */}
          <Card className="p-4 glass-panel space-y-4 rounded-xl">
            <div className="flex justify-between items-end">
              <Label className="text-lg font-heading uppercase text-primary">Height</Label>
              <div className="text-xl font-bold">
                {unitSystem === 'metric' ? `${heightCm} cm` : `${feet}' ${inches}"`}
              </div>
            </div>

            {unitSystem === 'metric' ? (
              <Slider
                value={[heightCm]}
                min={140}
                max={210}
                step={1}
                onValueChange={(v) => setHeightCm(v[0])}
                className="py-2"
              />
            ) : (
              <Slider
                value={[(feet * 12) + inches]}
                min={55} // 4'7"
                max={84} // 7'0"
                step={1}
                onValueChange={(v) => {
                  const totalInches = v[0];
                  setFeet(Math.floor(totalInches / 12));
                  setInches(totalInches % 12);
                }}
                className="py-2"
              />
            )}

            {/* Height Benchmark Bar */}
            <BenchmarkBar
              label="Height"
              value={stats.height}
              range={currentStandards.height}
              nhlValue={nhlBenchmark.height}
              unit="cm"
              status={benchmarkStatuses.height}
            />
          </Card>

          {/* Weight Controls */}
          <Card className="p-4 glass-panel space-y-4 rounded-xl">
            <div className="flex justify-between items-end">
              <Label className="text-lg font-heading uppercase text-primary">Weight</Label>
              <div className="text-xl font-bold">
                {unitSystem === 'metric' ? `${weightKg} kg` : `${lbs} lbs`}
              </div>
            </div>

            {unitSystem === 'metric' ? (
              <Slider
                value={[weightKg]}
                min={35}
                max={120}
                step={1}
                onValueChange={(v) => setWeightKg(v[0])}
                className="py-2"
              />
            ) : (
              <Slider
                value={[lbs]}
                min={77}
                max={265}
                step={1}
                onValueChange={(v) => setLbs(v[0])}
                className="py-2"
              />
            )}

            {/* Weight Benchmark Bar */}
            <BenchmarkBar
              label="Weight"
              value={stats.weight}
              range={currentStandards.weight}
              nhlValue={nhlBenchmark.weight}
              unit="kg"
              status={benchmarkStatuses.weight}
            />
          </Card>

          {/* BMI Display with Benchmark */}
          <Card className="p-4 glass-panel space-y-4 rounded-xl">
            <div className="flex justify-between items-end">
              <Label className="text-lg font-heading uppercase text-primary">BMI</Label>
              <div className="text-xl font-bold">{stats.bmi}</div>
            </div>

            <BenchmarkBar
              label="BMI"
              value={stats.bmi}
              range={currentStandards.bmi}
              nhlValue={nhlBenchmark.bmi}
              unit=""
              status={benchmarkStatuses.bmi}
            />
          </Card>

          {/* NHL Comparison Summary */}
          <Card className="p-4 glass-panel rounded-xl bg-gradient-to-br from-[#d946ef]/10 to-[#8b5cf6]/10 border border-[#d946ef]/30">
            <Label className="text-sm font-heading uppercase text-[#d946ef] mb-3 block">vs NHL {position.charAt(0).toUpperCase() + position.slice(1)}</Label>
            <div className="grid grid-cols-3 gap-3 text-center">
              <div>
                <div className="text-xs text-muted-foreground uppercase">Height</div>
                <div className={`text-lg font-bold ${nhlComparison.heightDiff >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {nhlComparison.heightDiff >= 0 ? '+' : ''}{nhlComparison.heightDiff} cm
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase">Weight</div>
                <div className={`text-lg font-bold ${nhlComparison.weightDiff >= 0 ? 'text-green-400' : 'text-amber-400'}`}>
                  {nhlComparison.weightDiff >= 0 ? '+' : ''}{nhlComparison.weightDiff} kg
                </div>
              </div>
              <div>
                <div className="text-xs text-muted-foreground uppercase">BMI</div>
                <div className={`text-lg font-bold ${Math.abs(nhlComparison.bmiDiff) <= 2 ? 'text-green-400' : 'text-amber-400'}`}>
                  {nhlComparison.bmiDiff >= 0 ? '+' : ''}{nhlComparison.bmiDiff}
                </div>
              </div>
            </div>
          </Card>
        </div>
      </motion.div>

      {/* Right Panel - Visualization */}
      <div className="flex-1 relative bg-gradient-to-b from-black/20 to-black/60">
        <PlayerGraphic
          stats={stats}
          position={position}
          ageCategory={ageCategory}
          nhlBenchmark={nhlBenchmark}
          optimalRange={currentStandards}
          unitSystem={unitSystem}
        />

        {/* Age/Position Badge */}
        <div className="absolute top-6 left-6 flex flex-col gap-2">
          <div className="bg-black/60 backdrop-blur-md px-4 py-2 rounded-lg border border-white/10">
            <span className="text-[#d946ef] font-bold">{ageCategory}</span>
            <span className="text-white/50 mx-2">|</span>
            <span className="text-white font-medium capitalize">{position}</span>
          </div>
          {/* Data Source Indicator */}
          <div className={`backdrop-blur-md px-3 py-1.5 rounded-lg border text-xs ${
            usingRealData
              ? 'bg-blue-500/20 border-blue-500/40 text-blue-300'
              : 'bg-white/10 border-white/20 text-white/60'
          }`}>
            {isLoadingBenchmarks ? (
              <span>Loading benchmarks...</span>
            ) : usingRealData ? (
              <span>Real data: {sampleSize?.toLocaleString()} players</span>
            ) : (
              <span>Using estimated benchmarks</span>
            )}
          </div>
        </div>

        {/* Benchmark Status Badge */}
        <div className="absolute top-6 right-6">
          <div className={`backdrop-blur-md px-4 py-2 rounded-lg border ${
            benchmarkStatuses.bmi === 'within'
              ? 'bg-green-500/20 border-green-500/50 text-green-400'
              : benchmarkStatuses.bmi === 'below'
              ? 'bg-amber-500/20 border-amber-500/50 text-amber-400'
              : 'bg-red-500/20 border-red-500/50 text-red-400'
          }`}>
            <span className="font-bold uppercase text-sm">
              {benchmarkStatuses.bmi === 'within' ? 'Average Range' : benchmarkStatuses.bmi === 'below' ? 'Below Range' : 'Above Range'}
            </span>
          </div>
        </div>
      </div>

    </div>
  );
}

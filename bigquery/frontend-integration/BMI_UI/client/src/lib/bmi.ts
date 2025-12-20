export type UnitSystem = 'metric' | 'imperial';

export interface BodyStats {
  height: number; // in cm
  weight: number; // in kg
  bmi: number;
  category: string;
}

export const calculateBMI = (height: number, weight: number): number => {
  // height in cm, weight in kg
  if (height <= 0 || weight <= 0) return 0;
  const heightInMeters = height / 100;
  return parseFloat((weight / (heightInMeters * heightInMeters)).toFixed(1));
};

export const getBMICategory = (bmi: number): string => {
  if (bmi < 18.5) return 'Underweight';
  if (bmi < 25) return 'Normal Weight';
  if (bmi < 30) return 'Overweight';
  return 'Obese';
};

export const imperialToMetric = (feet: number, inches: number, lbs: number) => {
  const heightCm = (feet * 30.48) + (inches * 2.54);
  const weightKg = lbs * 0.453592;
  return { heightCm, weightKg };
};

export const metricToImperial = (cm: number, kg: number) => {
  const totalInches = cm / 2.54;
  const feet = Math.floor(totalInches / 12);
  const inches = Math.round(totalInches % 12);
  const lbs = Math.round(kg * 2.20462);
  return { feet, inches, lbs };
};

// Age Categories
export type AgeCategory = 'U14' | 'U15' | 'U16' | 'U17' | 'U18' | 'U19' | 'U20';
export type Position = 'forward' | 'defender' | 'goalie';

export interface PhysicalRange {
  height: [number, number]; // [min, max] in cm
  weight: [number, number]; // [min, max] in kg
  bmi: [number, number];    // [min, max]
}

export interface NHLBenchmark {
  height: number;
  weight: number;
  bmi: number;
}

export const AGE_CATEGORIES: { value: AgeCategory; label: string; birthYear: string }[] = [
  { value: 'U14', label: 'U14', birthYear: '2012' },
  { value: 'U15', label: 'U15', birthYear: '2011' },
  { value: 'U16', label: 'U16', birthYear: '2010' },
  { value: 'U17', label: 'U17', birthYear: '2009' },
  { value: 'U18', label: 'U18', birthYear: '2008' },
  { value: 'U19', label: 'U19', birthYear: '2007' },
  { value: 'U20', label: 'U20', birthYear: '2006' },
];

export const POSITIONS: { value: Position; label: string }[] = [
  { value: 'forward', label: 'Forward' },
  { value: 'defender', label: 'Defender' },
  { value: 'goalie', label: 'Goalie' },
];

// Physical Standards by Position and Age Category
export const PHYSICAL_STANDARDS: Record<Position, Record<AgeCategory, PhysicalRange>> = {
  forward: {
    U14: { height: [149, 168], weight: [42, 58], bmi: [14.9, 24.5] },
    U15: { height: [159, 175], weight: [51, 68], bmi: [16.7, 25.2] },
    U16: { height: [165, 183], weight: [59, 78], bmi: [17.6, 27.3] },
    U17: { height: [170, 186], weight: [65, 83], bmi: [18.8, 27.5] },
    U18: { height: [172, 188], weight: [69, 88], bmi: [19.2, 28.0] },
    U19: { height: [175, 191], weight: [72, 92], bmi: [19.6, 28.8] },
    U20: { height: [175, 193], weight: [74, 95], bmi: [19.8, 29.5] },
  },
  defender: {
    U14: { height: [153, 173], weight: [46, 63], bmi: [15.2, 25.2] },
    U15: { height: [163, 181], weight: [55, 73], bmi: [16.9, 26.0] },
    U16: { height: [168, 188], weight: [63, 83], bmi: [17.8, 28.0] },
    U17: { height: [173, 191], weight: [69, 88], bmi: [19.0, 28.2] },
    U18: { height: [175, 193], weight: [73, 93], bmi: [19.5, 28.8] },
    U19: { height: [178, 196], weight: [76, 98], bmi: [19.7, 29.5] },
    U20: { height: [178, 198], weight: [78, 102], bmi: [19.9, 30.5] },
  },
  goalie: {
    U14: { height: [155, 175], weight: [47, 65], bmi: [15.2, 25.4] },
    U15: { height: [165, 183], weight: [56, 75], bmi: [16.8, 26.0] },
    U16: { height: [170, 190], weight: [64, 85], bmi: [17.7, 27.8] },
    U17: { height: [175, 193], weight: [70, 90], bmi: [18.8, 28.0] },
    U18: { height: [178, 196], weight: [75, 95], bmi: [19.5, 28.5] },
    U19: { height: [180, 198], weight: [78, 100], bmi: [19.9, 29.2] },
    U20: { height: [180, 201], weight: [80, 105], bmi: [20.0, 30.0] },
  },
};

// NHL Benchmarks by Position
export const NHL_BENCHMARKS: Record<Position, NHLBenchmark> = {
  forward: { height: 185, weight: 90, bmi: 26.3 },
  defender: { height: 188, weight: 92, bmi: 26.0 },
  goalie: { height: 190, weight: 91, bmi: 25.2 },
};

// Get benchmark status for a metric
export type BenchmarkStatus = 'below' | 'within' | 'above';

export const getBenchmarkStatus = (
  value: number,
  range: [number, number]
): BenchmarkStatus => {
  if (value < range[0]) return 'below';
  if (value > range[1]) return 'above';
  return 'within';
};

// Get percentage position within range (can be < 0 or > 100)
export const getRangePosition = (
  value: number,
  range: [number, number]
): number => {
  const [min, max] = range;
  return ((value - min) / (max - min)) * 100;
};

// Compare to NHL benchmark
export const getNHLComparison = (
  stats: BodyStats,
  position: Position
): { heightDiff: number; weightDiff: number; bmiDiff: number } => {
  const nhl = NHL_BENCHMARKS[position];
  return {
    heightDiff: stats.height - nhl.height,
    weightDiff: stats.weight - nhl.weight,
    bmiDiff: parseFloat((stats.bmi - nhl.bmi).toFixed(1)),
  };
};

// API configuration and hooks for fetching real player data

const API_BASE = 'https://us-central1-prodigy-ranking.cloudfunctions.net';

export interface PhysicalBenchmarkData {
  sample_size: number;
  height: {
    avg: number;
    range: [number, number];
    min: number;
    max: number;
  };
  weight: {
    avg: number;
    range: [number, number];
    min: number;
    max: number;
  };
  bmi: {
    avg: number;
    range: [number, number];
  };
}

export interface PhysicalBenchmarksResponse {
  by_birth_year: Record<string, Record<string, PhysicalBenchmarkData>>;
  by_age_category: Record<string, Record<string, PhysicalBenchmarkData>>;
  age_category_mapping: Record<string, string>;
  total_benchmarks: number;
  generated_at: string;
}

/**
 * Fetch physical benchmarks from the API
 * Returns real player averages by age category and position
 */
export async function fetchPhysicalBenchmarks(): Promise<PhysicalBenchmarksResponse | null> {
  try {
    const response = await fetch(`${API_BASE}/getPhysicalBenchmarks`);
    if (!response.ok) {
      console.error('Failed to fetch physical benchmarks:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching physical benchmarks:', error);
    return null;
  }
}

/**
 * Convert API benchmark data to the format expected by the BMI tool
 * Returns PhysicalRange format: { height: [min, max], weight: [min, max], bmi: [min, max] }
 */
export function benchmarkToPhysicalRange(benchmark: PhysicalBenchmarkData) {
  return {
    height: benchmark.height.range as [number, number],
    weight: benchmark.weight.range as [number, number],
    bmi: benchmark.bmi.range as [number, number],
  };
}

/**
 * Get the average values for display (midpoint of ranges becomes actual average)
 */
export function getBenchmarkAverages(benchmark: PhysicalBenchmarkData) {
  return {
    height: benchmark.height.avg,
    weight: benchmark.weight.avg,
    bmi: benchmark.bmi.avg,
  };
}

// NEPSAC API Hooks for GameDay feature
// React hooks for fetching NEPSAC data with loading/error states

import { useState, useEffect, useCallback } from 'react';
import {
  fetchPowerGrid,
  fetchNepsacPowerRankings,
  fetchNepsacSchedule,
  fetchNepsacPastResults,
  fetchNepsacTeams,
  PowerGridResponse,
  NepsacPowerRankingsResponse,
  NepsacScheduleResponse,
  NepsacPastResultsResponse,
  NepsacTeamsResponse,
} from '../lib/nepsac-api';

// ============================================================================
// Generic Hook State
// ============================================================================

interface UseApiState<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
}

// ============================================================================
// PowerGrid Hook
// ============================================================================

/**
 * Hook for fetching PowerGrid tournament probabilities
 *
 * Returns MUTUALLY EXCLUSIVE probabilities:
 * - Elite 8: Top 8 teams overall
 * - Large School: Large schools who MISSED Elite 8
 * - Small School: Small schools who MISSED Elite 8
 *
 * Example usage:
 * ```tsx
 * const { data, loading, error } = usePowerGrid('2025-26');
 * if (data) {
 *   // Dexter: elite8Bid=99%, largeSchoolBid=1% (mutually exclusive!)
 *   data.teams.forEach(team => {
 *     console.log(team.name, team.elite8Bid, team.largeSchoolBid);
 *   });
 * }
 * ```
 */
export function usePowerGrid(season: string = '2025-26'): UseApiState<PowerGridResponse> {
  const [data, setData] = useState<PowerGridResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchPowerGrid(season);
      if (result) {
        setData(result);
      } else {
        setError(new Error('Failed to fetch PowerGrid data'));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [season]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// Power Rankings Hook
// ============================================================================

/**
 * Hook for fetching Power Rankings
 */
export function usePowerRankings(
  season: string = '2025-26',
  limit: number = 20
): UseApiState<NepsacPowerRankingsResponse> {
  const [data, setData] = useState<NepsacPowerRankingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNepsacPowerRankings(season, limit);
      if (result) {
        setData(result);
      } else {
        setError(new Error('Failed to fetch Power Rankings'));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [season, limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// Schedule Hook
// ============================================================================

/**
 * Hook for fetching NEPSAC schedule for a specific date
 */
export function useNepsacSchedule(
  date: string,
  season: string = '2025-26'
): UseApiState<NepsacScheduleResponse> {
  const [data, setData] = useState<NepsacScheduleResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNepsacSchedule(date, season);
      if (result) {
        setData(result);
      } else {
        setError(new Error('Failed to fetch schedule'));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [date, season]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// Past Results Hook
// ============================================================================

/**
 * Hook for fetching past results with prediction accuracy
 */
export function usePastResults(
  season: string = '2025-26',
  limit: number = 200
): UseApiState<NepsacPastResultsResponse> {
  const [data, setData] = useState<NepsacPastResultsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNepsacPastResults(season, limit);
      if (result) {
        setData(result);
      } else {
        setError(new Error('Failed to fetch past results'));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [season, limit]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

// ============================================================================
// Teams Hook
// ============================================================================

/**
 * Hook for fetching all NEPSAC teams
 */
export function useNepsacTeams(
  season: string = '2025-26',
  division?: string
): UseApiState<NepsacTeamsResponse> {
  const [data, setData] = useState<NepsacTeamsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await fetchNepsacTeams(season, division);
      if (result) {
        setData(result);
      } else {
        setError(new Error('Failed to fetch teams'));
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'));
    } finally {
      setLoading(false);
    }
  }, [season, division]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}

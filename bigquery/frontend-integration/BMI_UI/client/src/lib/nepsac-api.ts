// NEPSAC API functions for GameDay feature
// Connects to Cloud Functions for NEPSAC prep hockey data

const API_BASE = 'https://us-central1-prodigy-ranking.cloudfunctions.net';

// ============================================================================
// Types
// ============================================================================

export interface NepsacTeam {
  teamId: string;
  name: string;
  shortName: string;
  logoUrl: string | null;
  division: string;
  rank: number | null;
  ovr: number;
  record: {
    wins: number;
    losses: number;
    ties: number;
  };
}

export interface NepsacPlayerStats {
  gp: number | null;
  goals: number | null;
  assists: number | null;
  points: number | null;
  gaa: number | null;      // Goalies only
  savePct: number | null;  // Goalies only
}

export interface NepsacPlayer {
  playerId: number | null;
  name: string;
  position: 'F' | 'D' | 'G';
  gradYear: number | null;
  jerseyNumber: string | null;
  imageUrl: string | null;
  prodigyPoints: number;
  ovr: number;
  stats?: NepsacPlayerStats;  // Season stats from Elite Prospects
}

export interface NepsacGame {
  gameId: string;
  gameDate: string;
  gameTime: string;
  dayOfWeek: string;
  venue: string | null;
  city: string | null;
  status: 'scheduled' | 'in_progress' | 'final' | 'postponed' | 'cancelled';
  score: { away: number; home: number } | null;
  awayTeam: NepsacTeam;
  homeTeam: NepsacTeam;
  prediction: {
    winnerId: string | null;
    confidence: number | null;
    confidenceOdds: string | null;  // American odds format (-300 or +150)
  };
}

export interface NepsacTeamStats {
  avgPoints: number;
  totalPoints: number;
  maxPoints: number;
  rosterSize: number;
  matchedPlayers: number;
  matchRate: number;
}

export interface NepsacMatchupTeam extends NepsacTeam {
  stats: NepsacTeamStats;
  goalsFor: number;
  goalsAgainst: number;
  streak: string | null;
  topPlayers: NepsacPlayer[];
}

export interface NepsacMatchup {
  game: {
    gameId: string;
    date: string;
    time: string;
    dayOfWeek: string;
    venue: string | null;
    city: string | null;
    status: string;
    score: { away: number; home: number } | null;
    prediction: {
      winnerId: string | null;
      confidence: number | null;
      confidenceOdds: string | null;  // American odds format (-300 or +150)
    };
  };
  awayTeam: NepsacMatchupTeam;
  homeTeam: NepsacMatchupTeam;
  maxPoints: number;
}

export interface NepsacScheduleResponse {
  date: string;
  season: string;
  gameCount: number;
  games: NepsacGame[];
}

export interface NepsacGameDate {
  date: string;
  gameCount: number;
  firstGame: string;
  lastGame: string;
}

export interface NepsacGameDatesResponse {
  season: string;
  dateCount: number;
  dates: NepsacGameDate[];
}

// Past Results Types
export interface NepsacPastResultTeam {
  teamId: string;
  name: string;
  shortName: string;
  score: number;
  isWinner: boolean;
  wasPredicted: boolean;
}

export interface NepsacPastResultGame {
  gameId: string;
  gameTime: string;
  awayTeam: NepsacPastResultTeam;
  homeTeam: NepsacPastResultTeam;
  prediction: {
    winnerId: string;
    confidence: number;
    confidenceOdds: string | null;  // American odds format (-300 or +150)
  };
  result: 'correct' | 'incorrect' | 'tie';
  isTie: boolean;
}

export interface NepsacPastResultDate {
  date: string;
  dayOfWeek: string;
  games: NepsacPastResultGame[];
  correct: number;
  incorrect: number;
  ties: number;
}

export interface NepsacPastResultsSummary {
  totalGames: number;
  correct: number;
  incorrect: number;
  ties: number;
  accuracy: number;
  record: string;
}

export interface NepsacPastResultsResponse {
  season: string;
  summary: NepsacPastResultsSummary;
  dateCount: number;
  dates: NepsacPastResultDate[];
}

export interface NepsacTeamWithStats extends NepsacTeam {
  venue: string | null;
  city: string | null;
  state: string | null;
  streak: string | null;
  stats: NepsacTeamStats & { topPlayer: string | null };
}

export interface NepsacTeamsResponse {
  season: string;
  teamCount: number;
  teams: NepsacTeamWithStats[];
}

// PowerGrid Types (Tournament Probabilities)
export interface PowerGridTeam {
  powerRank: number;
  classRank: number;
  teamId: string;
  name: string;
  shortName: string;
  logoUrl: string | null;
  classification: 'Large' | 'Small';
  divisionName: string;
  enrollment: number;
  ovr: number;
  record: {
    wins: number;
    losses: number;
    ties: number;
    gamesPlayed: number;
    winPct: number;
  };
  // MUTUALLY EXCLUSIVE probabilities
  // High elite8Bid = Low division bid (teams can only be in ONE tournament)
  elite8Bid: number;        // % chance for Elite 8
  elite8BidOdds?: string;   // American odds format
  elite8Champ: number;      // % chance to WIN Elite 8
  elite8ChampOdds?: string;
  largeSchoolBid: number;   // % chance for Large tournament (if MISS Elite 8)
  largeSchoolBidOdds?: string;
  largeSchoolChamp: number;
  largeSchoolChampOdds?: string;
  smallSchoolBid: number;   // % chance for Small tournament (if MISS Elite 8)
  smallSchoolBidOdds?: string;
  smallSchoolChamp: number;
  smallSchoolChampOdds?: string;
}

export interface PowerGridResponse {
  season: string;
  generated: string;
  teams: PowerGridTeam[];
  currentElite8: PowerGridTeam[];
  largeSchoolContenders: PowerGridTeam[];
  smallSchoolContenders: PowerGridTeam[];
  bubbleTeams: PowerGridTeam[];
  summary: {
    totalTeams: number;
    largeSchools: number;
    smallSchools: number;
    currentElite8Composition: {
      large: number;
      small: number;
    };
  };
}

// Power Rankings Types
export interface NepsacPowerRanking {
  rank: number;
  teamId: string;
  name: string;
  shortName: string;
  division: string;
  logoUrl: string | null;
  ovr: number;
  record: {
    wins: number;
    losses: number;
    ties: number;
    gamesPlayed: number;
    winPct: number;
  };
  stats: {
    avgPoints: number;
    totalPoints: number;
    maxPoints: number;
    rosterSize: number;
    matchedPlayers: number;
    matchRate: number;
    topPlayer: string | null;
  };
  performance: {
    goalsFor: number;
    goalsAgainst: number;
    goalDiff: number;
    streak: string;
  };
}

export interface NepsacPowerRankingsResponse {
  rankings: NepsacPowerRanking[];
  season: string;
  count: number;
  updated: string;
}

// ============================================================================
// API Functions
// ============================================================================

/**
 * Fetch games for a specific date
 */
export async function fetchNepsacSchedule(
  date: string,
  season: string = '2025-26'
): Promise<NepsacScheduleResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/getNepsacSchedule?date=${date}&season=${season}`
    );
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC schedule:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC schedule:', error);
    return null;
  }
}

/**
 * Fetch full matchup data for a specific game
 */
export async function fetchNepsacMatchup(
  gameId: string
): Promise<NepsacMatchup | null> {
  try {
    const response = await fetch(`${API_BASE}/getNepsacMatchup?gameId=${gameId}`);
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC matchup:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC matchup:', error);
    return null;
  }
}

/**
 * Fetch all game dates for the season
 */
export async function fetchNepsacGameDates(
  season: string = '2025-26'
): Promise<NepsacGameDatesResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/getNepsacGameDates?season=${season}`
    );
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC game dates:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC game dates:', error);
    return null;
  }
}

/**
 * Fetch past results with prediction accuracy
 */
export async function fetchNepsacPastResults(
  season: string = '2025-26',
  limit: number = 200
): Promise<NepsacPastResultsResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/getNepsacPastResults?season=${season}&limit=${limit}`
    );
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC past results:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC past results:', error);
    return null;
  }
}

/**
 * Fetch all NEPSAC teams
 */
export async function fetchNepsacTeams(
  season: string = '2025-26',
  division?: string
): Promise<NepsacTeamsResponse | null> {
  try {
    let url = `${API_BASE}/getNepsacTeams?season=${season}`;
    if (division) {
      url += `&division=${encodeURIComponent(division)}`;
    }
    const response = await fetch(url);
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC teams:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC teams:', error);
    return null;
  }
}

/**
 * Fetch Prodigy Power Rankings
 * Returns top teams ranked by performance-first methodology:
 * - Primary (70%): JSPR, NEHJ Expert, Performance ELO, MHR, Win%, Form
 * - Secondary (30%): Roster strength (Avg Points, Top Player, Depth)
 */
export async function fetchNepsacPowerRankings(
  season: string = '2025-26',
  limit: number = 20
): Promise<NepsacPowerRankingsResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/getNepsacPowerRankings?season=${season}&limit=${limit}`
    );
    if (!response.ok) {
      console.error('Failed to fetch NEPSAC power rankings:', response.status);
      return null;
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching NEPSAC power rankings:', error);
    return null;
  }
}

/**
 * Fetch PowerGrid - Tournament Probabilities
 *
 * Returns teams with MUTUALLY EXCLUSIVE tournament probabilities:
 * - Elite 8: Top 8 teams overall make this tournament
 * - Large School: Large schools who MISSED Elite 8
 * - Small School: Small schools who MISSED Elite 8
 *
 * A team can only be in ONE tournament!
 * Example: Dexter #1 has 99% Elite 8, 1% Large School (not both high)
 *
 * Data source: BigQuery algorithm_core.nepsac_team_rankings
 */
export async function fetchPowerGrid(
  season: string = '2025-26'
): Promise<PowerGridResponse | null> {
  try {
    const response = await fetch(
      `${API_BASE}/getNepsacPowerGrid?season=${season}`
    );
    if (!response.ok) {
      console.error('Failed to fetch PowerGrid:', response.status);
      return null;
    }

    const data = await response.json();

    // Transform API response - use FLAT fields directly (not nested probabilities)
    // API returns: team.elite8Bid, team.largeSchoolBid, etc. at root level
    const transformTeam = (team: any): PowerGridTeam => ({
      powerRank: team.powerRank,
      classRank: team.classRank,
      teamId: team.teamId,
      name: team.name,
      shortName: team.shortName,
      logoUrl: team.logoUrl,
      classification: team.classification,
      divisionName: team.divisionName,
      enrollment: team.enrollment,
      ovr: team.ovr,
      record: team.record,
      // Use flat fields directly (NOT team.probabilities.*)
      elite8Bid: team.elite8Bid ?? 0,
      elite8BidOdds: team.elite8BidOdds,
      elite8Champ: team.elite8Champ ?? 0,
      elite8ChampOdds: team.elite8ChampOdds,
      largeSchoolBid: team.largeSchoolBid ?? 0,
      largeSchoolBidOdds: team.largeSchoolBidOdds,
      largeSchoolChamp: team.largeSchoolChamp ?? 0,
      largeSchoolChampOdds: team.largeSchoolChampOdds,
      smallSchoolBid: team.smallSchoolBid ?? 0,
      smallSchoolBidOdds: team.smallSchoolBidOdds,
      smallSchoolChamp: team.smallSchoolChamp ?? 0,
      smallSchoolChampOdds: team.smallSchoolChampOdds,
    });

    return {
      season: data.season,
      generated: data.generated,
      teams: data.teams.map(transformTeam),
      currentElite8: data.currentElite8?.map(transformTeam) ?? [],
      largeSchoolContenders: data.largeSchoolContenders?.map(transformTeam) ?? [],
      smallSchoolContenders: data.smallSchoolContenders?.map(transformTeam) ?? [],
      bubbleTeams: data.bubbleTeams?.map(transformTeam) ?? [],
      summary: data.summary,
    };
  } catch (error) {
    console.error('Error fetching PowerGrid:', error);
    return null;
  }
}

/**
 * Get team's primary tournament path based on probabilities
 * Returns the tournament they're most likely to compete in
 */
export function getMainTournament(team: PowerGridTeam): {
  name: string;
  bid: number;
  champ: number;
} {
  if (team.elite8Bid >= 50) {
    return { name: 'Elite 8', bid: team.elite8Bid, champ: team.elite8Champ };
  } else if (team.classification === 'Large') {
    return { name: 'Large School', bid: team.largeSchoolBid, champ: team.largeSchoolChamp };
  } else {
    return { name: 'Small School', bid: team.smallSchoolBid, champ: team.smallSchoolChamp };
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get OVR rating color based on value (EA Sports style)
 */
export function getOvrColor(ovr: number): string {
  if (ovr >= 90) return 'text-yellow-400'; // Gold - Elite
  if (ovr >= 80) return 'text-emerald-400'; // Green - Great
  if (ovr >= 75) return 'text-blue-400'; // Blue - Good
  return 'text-slate-400'; // Gray - Average
}

/**
 * Get OVR rating background gradient based on value
 */
export function getOvrGradient(ovr: number): string {
  if (ovr >= 90) return 'from-yellow-500/20 to-amber-600/20 border-yellow-500/50';
  if (ovr >= 80) return 'from-emerald-500/20 to-green-600/20 border-emerald-500/50';
  if (ovr >= 75) return 'from-blue-500/20 to-cyan-600/20 border-blue-500/50';
  return 'from-slate-500/20 to-gray-600/20 border-slate-500/50';
}

/**
 * Get position display name
 */
export function getPositionLabel(position: string): string {
  const labels: Record<string, string> = {
    F: 'Forward',
    D: 'Defense',
    G: 'Goalie',
  };
  return labels[position] || position;
}

/**
 * Get position badge color
 */
export function getPositionColor(position: string): string {
  const colors: Record<string, string> = {
    F: 'bg-red-500/20 text-red-400 border-red-500/50',
    D: 'bg-blue-500/20 text-blue-400 border-blue-500/50',
    G: 'bg-purple-500/20 text-purple-400 border-purple-500/50',
  };
  return colors[position] || 'bg-slate-500/20 text-slate-400';
}

/**
 * Format record as string (W-L-T)
 */
export function formatRecord(record: { wins: number; losses: number; ties: number }): string {
  return `${record.wins}-${record.losses}-${record.ties}`;
}

/**
 * Calculate win percentage from record
 */
export function calculateWinPct(record: { wins: number; losses: number; ties: number }): number {
  const games = record.wins + record.losses + record.ties;
  if (games === 0) return 0;
  return ((record.wins + record.ties * 0.5) / games) * 100;
}

/**
 * Get prediction confidence color
 */
export function getConfidenceColor(confidence: number): string {
  if (confidence >= 70) return 'text-emerald-400';
  if (confidence >= 60) return 'text-yellow-400';
  return 'text-orange-400';
}

/**
 * Format date for display
 */
export function formatGameDate(dateString: string): string {
  const date = new Date(dateString + 'T00:00:00');
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

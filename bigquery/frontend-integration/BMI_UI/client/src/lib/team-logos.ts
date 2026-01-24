// Team card image mapping for NEPSAC GameDay
// Maps team_id from API to image slug used in card filenames

export const TEAM_ID_TO_IMAGE_SLUG: Record<string, string> = {
  "albany-academy": "albany-academy",
  "andover": "andover",
  "austin-prep": "austin-prep",
  "avon-old-farms": "avon-old-farms",
  "bbn": "buckingham-browne-and-nichols",
  "belmont-hill": "belmont-hill-school",
  "berkshire": "berkshire-school",
  "berwick": "berwick-academy",
  "brewster": "brewster-academy",
  "brooks": "brooks-school",
  "brunswick": "brunswick-school",
  "canterbury": "canterbury-school",
  "choate": "choate-rosemary-hall",
  "cushing": "cushing-academy",
  "deerfield": "deerfield-academy",
  "dexter": "dexter-southfield",
  "exeter": "phillips-exeter-academy",
  "frederick-gunn": "frederick-gunn-school",
  "governors": "the-governors-academy",
  "groton": "groton-school",
  "hebron": "hebron-academy",
  "holderness": "holderness-school",
  "hoosac": "hoosac-school",
  "hotchkiss": "hotchkiss-school",
  "kent": "kent-school",
  "kents-hill": "kents-hill-school",
  "kimball-union": "kimball-union-academy",
  "kingswood-oxford": "kingswood-oxford",
  "lawrence": "lawrence-academy",
  "loomis": "loomis-chaffee",
  "middlesex": "middlesex-school",
  "millbrook": "millbrook-school",
  "milton": "milton-academy",
  "new-hampton": "new-hampton-school",
  "nmh": "northfield-mount-hermon",
  "nobles": "noble-and-greenough",
  "north-yarmouth": "north-yarmouth-academy",
  "pingree": "pingree-school",
  "pomfret": "pomfret-school",
  "portsmouth-abbey": "portsmouth-abbey",
  "proctor": "proctor-academy",
  "rivers": "rivers-school",
  "roxbury-latin": "roxbury-latin",
  "salisbury": "salisbury-school",
  "st-georges": "st-georges-school",
  "st-lukes": "st-lukes-school",
  "st-marks": "st-marks-school",
  "st-pauls": "st-pauls-school",
  "st-sebastians": "st-sebastians-school",
  "tabor": "tabor-academy",
  "taft": "taft-school",
  "thayer": "thayer-academy",
  "tilton": "tilton-school",
  "trinity-pawling": "trinity-pawling-school",
  "vermont-academy": "vermont-academy",
  "westminster": "westminster-school",
  "wilbraham-monson": "wilbraham-and-monson-academy",
  "williston": "williston-northampton",
  "winchendon": "winchendon-school",
  "worcester": "worcester-academy",
  "shattuck-st-marys": "shattuck-st-marys",
};

const BASE_URL = "https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards";

// Teams that don't have card images yet (use placeholder)
const TEAMS_WITHOUT_CARDS: string[] = [];

/**
 * Get the card image URL for a team
 * @param teamId - The team_id from the API (e.g., "berkshire", "brooks")
 * @param isHome - Whether team is home (true) or away (false)
 * @param side - "left" or "right" side of card
 * @returns URL string or null if team has no card images
 */
export function getTeamCardUrl(
  teamId: string,
  isHome: boolean,
  side: "left" | "right"
): string | null {
  const imageSlug = TEAM_ID_TO_IMAGE_SLUG[teamId] || teamId;

  // Return null for teams without cards (use placeholder in component)
  if (TEAMS_WITHOUT_CARDS.includes(imageSlug)) {
    return null;
  }

  const homeAway = isHome ? "home" : "away";
  return `${BASE_URL}/${imageSlug}_${homeAway}_${side}.webp`;
}

/**
 * Get both card URLs for a team (left and right)
 */
export function getTeamCardUrls(teamId: string, isHome: boolean) {
  return {
    left: getTeamCardUrl(teamId, isHome, "left"),
    right: getTeamCardUrl(teamId, isHome, "right"),
  };
}

/**
 * Check if a team has card images available
 */
export function hasTeamCardImages(teamId: string): boolean {
  const imageSlug = TEAM_ID_TO_IMAGE_SLUG[teamId] || teamId;
  return !TEAMS_WITHOUT_CARDS.includes(imageSlug);
}

/**
 * Get image slug from team ID
 */
export function getImageSlug(teamId: string): string {
  return TEAM_ID_TO_IMAGE_SLUG[teamId] || teamId;
}

/**
 * Convert display team name to team ID slug
 * Handles special cases like "Shattuck St. Mary's" -> "shattuck-st-marys"
 */
export function teamNameToId(teamName: string): string {
  // Special case mappings for non-standard names
  const specialCases: Record<string, string> = {
    "shattuck st. mary's": "shattuck-st-marys",
    "shattuck st mary's": "shattuck-st-marys",
    "shattuck st. marys": "shattuck-st-marys",
    "shattuck st marys": "shattuck-st-marys",
    "shattuck": "shattuck-st-marys",
    "bb&n": "bbn",
    "buckingham browne & nichols": "bbn",
    "nmh": "nmh",
    "northfield mount hermon": "nmh",
  };

  const normalized = teamName.toLowerCase().trim();

  // Check special cases first
  if (specialCases[normalized]) {
    return specialCases[normalized];
  }

  // Default: convert to slug format
  return normalized
    .replace(/['']/g, "")
    .replace(/&/g, "and")
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "");
}

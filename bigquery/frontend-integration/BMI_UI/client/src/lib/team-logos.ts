// Complete team card mapping for NEPSAC GameDay
// Maps API team_id to card image filename slug

export const TEAM_ID_TO_IMAGE_SLUG: Record<string, string> = {
  // Direct matches (API ID = image slug)
  "albany-academy": "albany-academy",
  "andover": "andover",
  "austin-prep": "austin-prep",
  "avon-old-farms": "avon-old-farms",
  "kingswood-oxford": "kingswood-oxford",
  "loomis-chaffee": "loomis-chaffee",
  "portsmouth-abbey": "portsmouth-abbey",
  "roxbury-latin": "roxbury-latin",
  "vermont-academy": "vermont-academy",
  "williston-northampton": "williston-northampton",

  // API ID -> Image slug (need mapping)
  "bb-n": "buckingham-browne-and-nichols",
  "belmont-hill": "belmont-hill-school",
  "berkshire": "berkshire-school",
  "berwick": "berwick-academy",
  "brewster": "brewster-academy",
  "brooks-school": "brooks-school",
  "brunswick": "brunswick-school",
  "canterbury": "canterbury-school",
  "choate": "choate-rosemary-hall",
  "cushing": "cushing-academy",
  "deerfield": "deerfield-academy",
  "dexter": "dexter-southfield",
  "exeter": "phillips-exeter-academy",
  "frederick-gunn": "frederick-gunn-school",
  "governors-academy": "the-governors-academy",
  "groton": "groton-school",
  "hebron": "hebron-academy",
  "holderness": "holderness-school",
  "hoosac": "hoosac-school",
  "hotchkiss-school": "hotchkiss-school",
  "kent-school": "kent-school",
  "kents-hill": "kents-hill-school",
  "kimball-union": "kimball-union-academy",
  "lawrence-academy": "lawrence-academy",
  "middlesex": "middlesex-school",
  "millbrook": "millbrook-school",
  "milton-academy": "milton-academy",
  "new-hampton": "new-hampton-school",
  "nmh": "northfield-mount-hermon",
  "noble-greenough": "noble-and-greenough",
  "north-yarmouth": "north-yarmouth-academy",
  "pingree": "pingree-school",
  "pomfret": "pomfret-school",
  "proctor-academy": "proctor-academy",
  "rivers-school": "rivers-school",
  "salisbury-school": "salisbury-school",
  "shattuck-st-mary-s": "shattuck-st-marys",
  "st-georges": "st-georges-school",
  "st-lukes": "st-lukes-school",
  "st-marks": "st-marks-school",
  "st-paul-s-school": "st-pauls-school",
  "st-sebastian-s": "st-sebastians-school",
  "tabor": "tabor-academy",
  "taft": "taft-school",
  "thayer-academy": "thayer-academy",
  "tilton": "tilton-school",
  "trinity-pawling": "trinity-pawling-school",
  "westminster": "westminster-school",
  "wilbraham-monson": "wilbraham-and-monson-academy",
  "winchendon": "winchendon-school",
  "worcester-academy": "worcester-academy",
};

/**
 * Get the image slug for a team ID (for display purposes)
 * @param teamId - The team_id from the API
 * @returns The image slug or the teamId if not found
 */
export function getImageSlug(teamId: string): string {
  if (!teamId) return '';
  return TEAM_ID_TO_IMAGE_SLUG[teamId.toLowerCase()] || teamId;
}

const BASE_URL = "https://raw.githubusercontent.com/PFUNKTHEO2/append-extra-points/main/bigquery/nepsac-cards";

/**
 * Get the card image URL for a team
 * @param teamId - The team_id from the API
 * @param isHome - Whether team is home (true) or away (false)
 * @param side - "left" or "right" side of card
 */
export function getTeamCardUrl(
  teamId: string,
  isHome: boolean,
  side: "left" | "right" = "left"
): string | null {
  if (!teamId) return null;

  const imageSlug = TEAM_ID_TO_IMAGE_SLUG[teamId];

  // If no mapping exists, team doesn't have cards
  if (!imageSlug) {
    console.warn(`No card mapping for team: ${teamId}`);
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
  return !!TEAM_ID_TO_IMAGE_SLUG[teamId];
}

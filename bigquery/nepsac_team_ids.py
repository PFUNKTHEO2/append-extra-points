"""
NEPSAC Team ID Normalization Utility
====================================
Provides canonical team ID mappings to ensure consistency across all tables.

Usage:
    from nepsac_team_ids import normalize_team_id, validate_all_tables

    # Normalize a team ID before inserting/updating
    canonical_id = normalize_team_id("loomis-chaffee")  # Returns "loomis"

    # Validate all tables for consistency
    validate_all_tables()
"""

from google.cloud import bigquery
from typing import Dict, List, Optional, Tuple

# ============================================================================
# CANONICAL TEAM ID MAPPING
# ============================================================================
# Maps common variations to the canonical team_id used in nepsac_teams table.
# Add new mappings here when you encounter new variations.

TEAM_ID_ALIASES: Dict[str, str] = {
    # Loomis variations
    "loomis-chaffee": "loomis",
    "loomis-chaffee-school": "loomis",

    # Schools with "school" suffix
    "hotchkiss-school": "hotchkiss",
    "kent-school": "kent",
    "salisbury-school": "salisbury",
    "proctor-academy": "proctor",
    "milton-academy": "milton",
    "lawrence-academy": "lawrence",
    "berkshire-school": "berkshire",

    # Lawrenceville (different school, but mapped to lawrence for now)
    "lawrenceville-school": "lawrence",
    "lawrenceville": "lawrence",

    # Northampton variations
    "williston-northampton": "williston",
    "williston-northampton-school": "williston",

    # Wilbraham Monson
    "wilbraham-monson": "wma",
    "wilbraham-monson-academy": "wma",

    # St. schools variations
    "st-pauls": "st-paul-s-school",
    "st-pauls-school": "st-paul-s-school",
    "saint-pauls": "st-paul-s-school",
    "st-sebastians": "st-sebastian-s",
    "st-sebastians-school": "st-sebastian-s",
    "saint-sebastians": "st-sebastian-s",
    "st-marks": "st-marks",
    "st-marks-school": "st-marks",
    "st-georges": "st-georges",
    "st-georges-school": "st-georges",

    # BBN variations
    "buckingham-browne-nichols": "bb-n",
    "bbn": "bb-n",

    # KUA variations
    "kua": "kimball-union",
    "kimball-union-academy": "kimball-union",

    # NMH variations
    "northfield-mount-hermon": "nmh",
    "northfield": "nmh",

    # Other common variations
    "brooks": "brooks-school",
    "rivers": "rivers-school",
    "nobles": "noble-greenough",
    "governors": "governors-academy",
    "thayer": "thayer-academy",
    "worcester": "worcester-academy",
    "dexter-southfield": "dexter",

    # Full name variations
    "avon-old-farms-school": "avon-old-farms",
    "belmont-hill": "belmont-hill",
    "phillips-andover": "andover",
    "phillips-exeter": "exeter",
}

# Canonical team IDs (from nepsac_teams table)
CANONICAL_TEAM_IDS = {
    "albany-academy", "austin-prep", "avon-old-farms", "belmont-hill", "berkshire",
    "berwick", "brewster", "brooks-school", "brunswick", "bb-n", "canterbury",
    "choate", "cushing", "deerfield", "dexter", "frederick-gunn", "governors-academy",
    "groton", "hebron", "holderness", "hoosac", "hotchkiss", "kent", "kents-hill",
    "kimball-union", "lawrence", "loomis", "middlesex", "millbrook", "milton",
    "new-hampton", "noble-greenough", "nmh", "andover", "exeter", "pingree",
    "pomfret", "portsmouth-abbey", "proctor", "rivers-school", "roxbury-latin",
    "salisbury", "st-georges", "st-marks", "st-paul-s-school", "st-sebastian-s",
    "tabor", "taft", "thayer-academy", "tilton", "trinity-pawling", "vermont-academy",
    "westminster", "wma", "williston", "winchendon", "worcester-academy"
}


def normalize_team_id(team_id: str) -> str:
    """
    Normalize a team ID to its canonical form.

    Args:
        team_id: The team ID to normalize (e.g., "loomis-chaffee", "Loomis Chaffee")

    Returns:
        The canonical team ID (e.g., "loomis")
    """
    if not team_id:
        return team_id

    # Convert to lowercase and replace spaces with hyphens
    normalized = team_id.lower().strip().replace(" ", "-").replace("'", "")

    # Check if it's already canonical
    if normalized in CANONICAL_TEAM_IDS:
        return normalized

    # Check aliases
    if normalized in TEAM_ID_ALIASES:
        return TEAM_ID_ALIASES[normalized]

    # Try removing common suffixes
    for suffix in ["-school", "-academy"]:
        if normalized.endswith(suffix):
            base = normalized[:-len(suffix)]
            if base in CANONICAL_TEAM_IDS:
                return base
            if base in TEAM_ID_ALIASES:
                return TEAM_ID_ALIASES[base]

    # Return as-is if no mapping found (might be a new team)
    return normalized


def get_mismatched_team_ids(table_name: str, team_id_column: str = "team_id") -> List[Tuple[str, str]]:
    """
    Find team IDs in a table that don't match canonical IDs.

    Returns:
        List of (current_id, suggested_canonical_id) tuples
    """
    client = bigquery.Client()

    query = f"""
    SELECT DISTINCT {team_id_column}
    FROM `prodigy-ranking.algorithm_core.{table_name}`
    WHERE {team_id_column} IS NOT NULL
    """

    mismatches = []
    for row in client.query(query).result():
        current_id = getattr(row, team_id_column)
        canonical_id = normalize_team_id(current_id)

        if current_id != canonical_id:
            mismatches.append((current_id, canonical_id))

    return mismatches


def fix_team_ids_in_table(table_name: str, team_id_column: str = "team_id",
                          dry_run: bool = True) -> int:
    """
    Fix all mismatched team IDs in a table.

    Args:
        table_name: Name of the table (without project/dataset prefix)
        team_id_column: Name of the team ID column
        dry_run: If True, only report what would be fixed

    Returns:
        Number of rows that would be/were updated
    """
    client = bigquery.Client()
    mismatches = get_mismatched_team_ids(table_name, team_id_column)

    if not mismatches:
        print(f"[OK] {table_name}: All team IDs are canonical")
        return 0

    total_updated = 0

    for current_id, canonical_id in mismatches:
        if canonical_id not in CANONICAL_TEAM_IDS:
            print(f"[WARN] {table_name}: {current_id} -> {canonical_id} (NOT in canonical list, skipping)")
            continue

        if dry_run:
            # Count how many rows would be affected
            count_query = f"""
            SELECT COUNT(*) as cnt
            FROM `prodigy-ranking.algorithm_core.{table_name}`
            WHERE {team_id_column} = '{current_id}'
            """
            result = list(client.query(count_query).result())[0]
            print(f"  {table_name}: Would update {result.cnt} rows: {current_id} -> {canonical_id}")
            total_updated += result.cnt
        else:
            # Actually update
            update_query = f"""
            UPDATE `prodigy-ranking.algorithm_core.{table_name}`
            SET {team_id_column} = '{canonical_id}'
            WHERE {team_id_column} = '{current_id}'
            """
            job = client.query(update_query)
            job.result()
            print(f"  {table_name}: Updated {job.num_dml_affected_rows} rows: {current_id} -> {canonical_id}")
            total_updated += job.num_dml_affected_rows

    return total_updated


def validate_all_tables(fix: bool = False) -> Dict[str, int]:
    """
    Validate team IDs across all NEPSAC tables.

    Args:
        fix: If True, fix mismatches. If False, just report.

    Returns:
        Dict of table_name -> number of mismatched/fixed rows
    """
    tables = [
        ("nepsac_rosters", "team_id"),
        ("nepsac_schedule", "away_team_id"),
        ("nepsac_schedule", "home_team_id"),
        ("nepsac_standings", "team_id"),
        ("nepsac_team_rankings", "team_id"),
        ("nepsac_game_performers", "team_id"),
    ]

    print("=" * 60)
    print("NEPSAC Team ID Validation")
    print("=" * 60)

    if fix:
        print("Mode: FIX (will update database)")
    else:
        print("Mode: DRY RUN (report only)")
    print()

    results = {}

    for table_name, column in tables:
        try:
            count = fix_team_ids_in_table(table_name, column, dry_run=not fix)
            key = f"{table_name}.{column}"
            results[key] = count
        except Exception as e:
            print(f"[ERROR] {table_name}.{column}: Error - {e}")
            results[f"{table_name}.{column}"] = -1

    print()
    print("=" * 60)
    total = sum(v for v in results.values() if v > 0)
    if fix:
        print(f"Total rows fixed: {total}")
    else:
        print(f"Total rows to fix: {total}")
    print("=" * 60)

    return results


def add_alias(variation: str, canonical_id: str):
    """
    Add a new alias mapping. Call this when you encounter a new variation.

    Note: This only updates the in-memory mapping. To persist, add to TEAM_ID_ALIASES dict.
    """
    if canonical_id not in CANONICAL_TEAM_IDS:
        print(f"Warning: {canonical_id} is not a canonical team ID")
    TEAM_ID_ALIASES[variation.lower()] = canonical_id
    print(f"Added alias: {variation} -> {canonical_id}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--fix":
        validate_all_tables(fix=True)
    else:
        print("Usage: python nepsac_team_ids.py [--fix]")
        print()
        print("Without --fix: Reports mismatches (dry run)")
        print("With --fix: Actually fixes mismatches in database")
        print()
        validate_all_tables(fix=False)

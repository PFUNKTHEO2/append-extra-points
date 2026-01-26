#!/usr/bin/env python3
"""
Cleanup old redundant NEPSAC roster files.

The definitive source of truth is now:
- CSV: neutralzone_prep_boys_hockey_data_clean.csv
- Script: import_neutralzone_rosters.py
- Tables: nepsac_rosters, nepsac_player_stats

This script moves old/redundant files to _archive/old_nepsac_rosters/
"""

import os
import shutil
from pathlib import Path

# Files to archive (no longer needed)
OLD_CSV_FILES = [
    'nepsac_983_players.csv',
    'nepsac_all_rosters_combined.csv',
    'nepsac_full_rosters.csv',
    'nepsac_matched_players.csv',
    'nepsac_players_raw.csv',
    'nepsac_players_sample.csv',
    'nepsac_roster_matches.csv',
    'nepsac_scraped_rosters.csv',
]

OLD_PYTHON_SCRIPTS = [
    'fix_nepsac_roster_duplicates.py',
    'fix_roster_duplicates_v2.py',
    'restore_nepsac_rosters.py',
    'nepsac_player_import.py',
    'nepsac_player_matcher.py',
    'nepsac_fuzzy_roster_matcher.py',
    'nepsac_fuzzy_roster_matcher_fast.py',
    'scrape_nepsac_rosters.py',
    'fix_team_assignments.py',  # One-time fix, no longer needed
]

# Files to KEEP (current authoritative sources)
KEEP_FILES = [
    'neutralzone_prep_boys_hockey_data_clean.csv',  # Authoritative CSV
    'import_neutralzone_rosters.py',  # Authoritative import script
]

def main():
    base_dir = Path(__file__).parent
    archive_dir = base_dir / '_archive' / 'old_nepsac_rosters'

    print("=" * 60)
    print("NEPSAC ROSTER CLEANUP")
    print("=" * 60)
    print(f"\nArchive directory: {archive_dir}")

    # Create archive directory
    archive_dir.mkdir(parents=True, exist_ok=True)

    # Archive old CSV files
    print("\n=== OLD CSV FILES ===")
    for filename in OLD_CSV_FILES:
        filepath = base_dir / filename
        if filepath.exists():
            dest = archive_dir / filename
            print(f"  Moving: {filename}")
            shutil.move(str(filepath), str(dest))
        else:
            print(f"  Not found: {filename}")

    # Archive old Python scripts
    print("\n=== OLD PYTHON SCRIPTS ===")
    for filename in OLD_PYTHON_SCRIPTS:
        filepath = base_dir / filename
        if filepath.exists():
            dest = archive_dir / filename
            print(f"  Moving: {filename}")
            shutil.move(str(filepath), str(dest))
        else:
            print(f"  Not found: {filename}")

    # Verify kept files exist
    print("\n=== AUTHORITATIVE FILES (KEPT) ===")
    for filename in KEEP_FILES:
        filepath = base_dir / filename
        if filepath.exists():
            print(f"  ✓ {filename}")
        else:
            print(f"  ✗ MISSING: {filename}")

    print("\n" + "=" * 60)
    print("CLEANUP COMPLETE")
    print("=" * 60)
    print(f"\nOld files moved to: {archive_dir}")
    print("\nAuthoritative sources:")
    print("  - CSV: neutralzone_prep_boys_hockey_data_clean.csv")
    print("  - Script: import_neutralzone_rosters.py")
    print("  - Tables: nepsac_rosters, nepsac_player_stats")

if __name__ == '__main__':
    import sys
    if '--apply' not in sys.argv:
        print("DRY RUN - showing what would be archived")
        print("Run with --apply to execute\n")

        base_dir = Path(__file__).parent

        print("=== FILES TO ARCHIVE ===")
        for filename in OLD_CSV_FILES + OLD_PYTHON_SCRIPTS:
            filepath = base_dir / filename
            status = "EXISTS" if filepath.exists() else "not found"
            print(f"  {filename}: {status}")

        print("\n=== FILES TO KEEP ===")
        for filename in KEEP_FILES:
            filepath = base_dir / filename
            status = "EXISTS" if filepath.exists() else "MISSING!"
            print(f"  {filename}: {status}")
    else:
        main()

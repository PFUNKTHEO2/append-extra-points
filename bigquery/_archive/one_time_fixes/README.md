# One-Time Fix Scripts (Archived)

**Deprecated Date:** 2026-01-26

These scripts were used for one-time fixes and migrations. They have been archived after their changes were successfully applied.

## Files

| File | Purpose | Status |
|------|---------|--------|
| `FIXES_FOR_DRAFT_AND_LEAGUE_POINTS.sql` | Fixed draft points > 300 and OHL league points | Applied |
| `rebuild_with_height_weight.py` | One-time rebuild adding F26/F27 | Applied |
| `run_rebuild_with_f26_f27.py` | Runner for F26/F27 rebuild | Applied |
| `verify_f10_and_rebuild.py` | Verification and rebuild for F10 | Applied |
| `verify_f14_rebuild.py` | Verification and rebuild for F14 | Applied |
| `fix_f09_and_rebuild.py` | One-time fix for F09 factor | Applied |

## Note

These scripts should NOT be run again as they were designed for specific one-time migrations. If similar issues arise, create new scripts rather than reusing these.

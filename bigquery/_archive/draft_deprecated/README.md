# Deprecated Draft Scripts

**Deprecated Date:** 2026-01-26

These scripts were deprecated after consolidating the draft points pipeline.

## Current Active Pipeline

The draft points pipeline now uses two scripts:

1. **`working_draft_script.py`** - Uploads raw draft data from CSV to `hockey-data-analysis.hockey.all_drafts`
2. **`refresh_DL_F17_draft_points.py`** - Transforms `all_drafts` into `prodigy-ranking.algorithm_core.DL_F17_draft_points` with calculated points

## Deprecated Files

| File | Reason |
|------|--------|
| `clean_draft_data.py` | One-time data cleaning script |
| `encode_draft.py` | Small encoding helper, no longer needed |
| `final_draft_upsert.py` | Superseded by `working_draft_script.py` |
| `fixed_draft_script.py` | One-time null fix, superseded |
| `upsert_draft_data.py` | Superseded by `working_draft_script.py` |
| `upsert_draft_data_v1.py` | Old version of upsert script |
| `uspert_draft_data.py` | Typo version of `upsert_draft_data.py` |

## Data Flow

```
CSV Files (canadian_drafts_master_consolidated.csv, ushl_master_consolidated.csv)
    │
    ▼ [working_draft_script.py]
    │
hockey-data-analysis.hockey.all_drafts (raw draft picks)
    │
    ▼ [refresh_DL_F17_draft_points.py]
    │
prodigy-ranking.algorithm_core.DL_F17_draft_points (calculated points)
    │
    ▼ [rebuild_cumulative_with_ratings.sql]
    │
prodigy-ranking.algorithm_core.player_cumulative_points (F17 factor)
```

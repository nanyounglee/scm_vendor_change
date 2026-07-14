
## v1 - 2026-07-14 17:42:32
- Deployed index.html with in-index workflow status management.
- Added monthly completed product/vendor-change list.
- Removed local report download/export controls from the deployed UI.

## v2 - 2026-07-14 17:44:23
- Restored MD/PDF report save buttons while keeping index workflow status management.

## v3 - 2026-07-14
- Fixed getRpts() so bank-synced reports stay visible even after local-only edits (previously any local report fully hid the shared snapshot).
- Added `bank/` shared snapshot: `reports.json`, per-report markdown, and `sync_bank.py` to merge exported reports and regenerate the embedded snapshot in index.html.
- Added a "보고서 동기화" badge/modal in the header explaining how to sync local reports into the shared bank so review/confirmed/completed reports are viewable from any device, grouped by month.

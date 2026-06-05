# Phase goal-i_will_be_super_rich-iter-8 — UI Surface Map

**Phase:** goal-i_will_be_super_rich-iter-8
**Date:** 2026-06-05
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `TopBar` — local timezone label | New component | Historical picker must show the user which timezone their entry is interpreted in (J-20) | Switch to Historical mode, verify a muted monospaced timezone label (e.g. `Asia/Hong_Kong` or `America/New_York`) appears immediately beside the time inputs without entering a date |
| `/` | `TopBar` — quick-pick buttons (disabled state) | New component | US-session presets must be disabled until a date is entered to prevent malformed windows (J-20) | Switch to Historical mode with no date entered; verify all three buttons ("Open 9:30 ET", "Close 16:00 ET", "Full RTH 9:30–16:00 ET") are visible but appear at 40% opacity with a not-allowed cursor on hover |
| `/` | `TopBar` — quick-pick buttons (enabled state with local annotations) | New component | US-session presets must show local-equivalent time for the chosen date so the user sees both ET and their own time (J-20) | Enter a date (e.g. 2026-06-02) in Historical mode; verify all three quick-pick buttons now appear active and each shows a local-time annotation (e.g. "Open 9:30 ET (09:30 PM local)") beside the ET label |
| `/` | `TopBar` — "Open 9:30 ET" quick-pick click | Changed behavior | One-click fill of the US market open window in one action (J-20) | Enter a date, click "Open 9:30 ET", verify the start and end time inputs are filled with the local-equivalent of 9:30 ET on that date and start < end |
| `/` | `TopBar` — "Close 16:00 ET" quick-pick click | Changed behavior | One-click fill of the US market close window in one action (J-20) | Enter a date, click "Close 16:00 ET", verify the start and end time inputs are filled with the local-equivalent of 16:00 ET on that date and start < end |
| `/` | `TopBar` — "Full RTH 9:30–16:00 ET" quick-pick click | Changed behavior | One-click fill of the full regular-trading-hours window (J-20) | Enter a date, click "Full RTH 9:30–16:00 ET", verify the start time input shows the local-equivalent of 9:30 ET and the end time input shows the local-equivalent of 16:00 ET for that date |
| `/` | `TopBar` — Historical Watch POST body | Changed behavior | The picker previously sent naive datetime strings treated as UTC by the backend; now sends tz-aware UTC instants so the fetched window matches the user's local selection (J-20 load-bearing fix) | In Historical mode, enter a date and local start/end times (e.g. 21:30–23:00 in Hong Kong), click Watch, inspect the network request body — verify `start` and `end` are ISO strings with a `Z` suffix (e.g. `2026-06-02T13:30:00.000Z`), not naive strings like `2026-06-02T21:30` |
| `/` | `TopBar` — quick-pick clears on manual field edit | Changed behavior | Manual edits after a quick-pick must take control so the submitted window matches the manually typed values (J-20 correctness) | Click "Open 9:30 ET" to fill the window, then manually change the start time input to a different value; click Watch and inspect the POST body — verify `start` reflects the manually typed value (resolved to UTC), not the earlier quick-pick instant |
| `/` | `TopBar` — Historical date/time picker (existing controls) | Changed behavior | The resolver was wired in; the inputs now feed the tz-aware UTC resolution path instead of the old naive string construction | Enter a date and manual start/end times (not via quick-pick), click Watch; verify the POST body `start` and `end` are tz-aware (`Z` suffix) and equal to the entered local time resolved to UTC (e.g. local 15:00 in UTC+8 → `07:00:00.000Z`) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_window_resolution.py` — New test module with 6 tests asserting that `_parse_window_dt` and the historical watch path correctly resolve offset-bearing ISO instants to their exact UTC equivalents (summer EDT and winter EST), that the `Z` suffix works, and that the legacy naive→UTC fallback is unchanged. This is a source-of-truth verification; no API behavior changed and there is no user-visible effect.

---

## Summary

- **Frontend surfaces changed:** 1 (TopBar on `/`)
- **New pages/routes:** 0
- **Modified components:** 2 (`apps/frontend/components/TopBar.tsx`, `apps/frontend/lib/datetime.ts`)
- **Navigation changes:** no
- **Backend-only changes:** 1 (test file only)

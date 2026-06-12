# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-18 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-18
**Date:** 2026-06-12
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| All pages (global nav) | `NavBar` — Studies link | Changed behavior | Studies page now exists; pre-registered disabled entry is activated | Click the "Studies" nav item; confirm it navigates to `/studies` and the link gains the active (emerald) highlight |
| All pages (global nav) | `NavBar` — Studies link (was disabled) | Changed behavior | The old `<span aria-disabled>` with cursor-not-allowed styling is replaced by a `<Link>` | Confirm the link is not a greyed-out label and has no "Coming with replay studies" tooltip |
| `/studies` | `StudiesPage` — page header | New page | Entire `/studies` route is new | Load `/studies`; confirm the "Replay studies" title and measurement-framing paragraph are visible and the page does not show a blank/error state |
| `/studies` | `StudyCreateForm` — source picker (reference) | New component | User can pick the committed PG SIP reference window (no credentials) | Select the "Reference window" radio card; confirm the sim scenario dropdown and symbol/date fields are hidden; click "Run study" and confirm a study row appears in the job list |
| `/studies` | `StudyCreateForm` — source picker (sim) | New component | User can pick a seeded sim scenario | Select "Seeded sim scenario"; confirm the sim select dropdown appears with SIM-REVERSAL, SIM-BUYER, SIM-SHIFT, SIM-SELLER; choose SIM-REVERSAL and click "Run study"; confirm a study row appears |
| `/studies` | `StudyCreateForm` — source picker (historical) | New component | User can specify a real symbol + past window | Select "Symbol + past window"; confirm a symbol search field, a dd-MM-yyyy date input, start/end time inputs, and the three preset buttons (Open 9:30 ET, Close 16:00 ET, Full RTH) appear; confirm preset buttons are disabled until a valid date is entered |
| `/studies` | `StudyCreateForm` — level input + hindsight warning | New component | Level setups require a user-supplied level with a hindsight disclaimer | Select "level_break" in the Setup dropdown; confirm a "Level price" number input and an amber hindsight warning box appear; switch back to "absorption_reversal" and confirm both disappear |
| `/studies` | `StudyCreateForm` — Run study button | New component | Submit triggers create + start on the backend | Leave level price blank when "level_break" is selected; confirm the "Run study" button stays disabled; fill in a level price and confirm it becomes enabled |
| `/studies` | `StudyCreateForm` — inline 422 error | New component | Backend validation errors surface inline | Submit a historical study without valid credentials; confirm a rose error box appears below the form with the backend's error message (not a page-level crash) |
| `/studies` | `StudyList` — loading state | New component | Page has a loading state before first fetch completes | Hard-reload `/studies`; confirm a pulsing dot and "Loading studies…" text appear briefly before the list or empty state renders |
| `/studies` | `StudyList` — empty state | New component | No studies exist on first visit | Visit `/studies` with no studies created; confirm the text "No studies yet — create one above…" is shown (not a blank area) |
| `/studies` | `StudyList` — study row with status badge | New component | Each study row shows live status | Create a reference-window study; confirm the job row appears with a "Queued" then "Running" badge before settling on "Done" (amber while running, neutral slate when done) |
| `/studies` | `StudyList` — Cancel button | New component | Running/queued studies can be cancelled | Start a long sim study; while status is Running or Queued click the "Cancel" button; confirm the status badge changes to "Cancelled" and the Cancel button disappears from the row |
| `/studies` | `StudyList` — cancelled row shows PARTIAL results | New component | Cancelled studies surface partial results honestly | After cancelling a running study, click its row; confirm the results panel shows a "PARTIAL" warning above any occurrence data (not an empty or success state) |
| `/studies` | `StudyList` — failed row | New component | A study that fails must show an explicit error | Attempt a historical study without credentials; confirm the row's status badge reads "Failed" (rose); click the row and confirm the results panel shows a rose error box with the failure reason |
| `/studies` | `StudyList` — events-processed counter | New component | Progress is visible while a study is running | Create a reference-window study; while status is Running confirm a monospace event counter (e.g. "3200 events processed") appears on the running row |
| `/studies` | `StudyList` — hindsight-level chip on row | New component | Level-setup studies are flagged in the list | Create a level_break study with a level price; confirm an amber "Hindsight level" chip appears on the row in the job list |
| `/studies` | `StudyResultsView` — side-by-side distributions | New component | Results render setup vs null baseline | After a study completes, click its row; confirm two distribution panels appear side-by-side (or stacked on narrow): "Your setup" (darker border) and "Random-time baseline" (lighter border) |
| `/studies` | `StudyResultsView` — horizon rows (+1R / −1R / neither / truncated) | New component | Per-horizon ternary outcomes with truncated counted separately | In the results view, confirm each horizon row (10s, 30s, 60s, 120s) shows four distinct chips — +1R (emerald), −1R (rose), neither (slate), and Truncated (amber) — and that Truncated is never merged with the others |
| `/studies` | `StudyResultsView` — occurrences table | New component | Each setup occurrence is individually listed | For a completed reference-window study, confirm an "Occurrences" table appears with columns "Arm time (logical s)", "Verdict reached", and "R basis" in monospace font |
| `/studies` | `StudyResultsView` — honesty stamps | New component | Feed, config fingerprint, and baseline seed are always visible on results | On a completed study's results panel, confirm three monospace chips appear in the header: a Feed chip (e.g. "sip"), a Config fingerprint chip (with hover tooltip showing the full hash), and a Baseline seed chip (e.g. "1729") |
| `/studies` | `StudyResultsView` — hindsight label and caption | New component | Level-setup results carry a hindsight disclosure | Open a completed level_break study; confirm an amber "Level chosen with hindsight" label appears in the results header and an amber caption block explaining the exclusion appears below the framing line |
| `/studies` | `StudyResultsView` — insufficient-sample marker | New component | Small-n populations carry an honest marker | If a study produces fewer occurrences than the configured minimum sample size, confirm an amber "Insufficient sample (n = X < Y)" chip appears inside the relevant distribution block |
| `/studies` | `StudyResultsView` — Re-run identical button | New component | User can reproduce exact results | Click "Re-run identical" on a completed study; confirm a new study row appears in the job list with the same source, setup, direction, and seed; after it completes, confirm the occurrence counts match the original |
| `/studies` | `StudyResultsView` — queued/running absence sentence | New component | Non-terminal studies show their own per-status copy | Select a queued study from the list; confirm the results panel shows a queued-specific absence sentence (not a running-specific one or a generic "no results yet") |
| `/studies` | `StudyResultsView` — measurement-framing line | New component | Anti-edge disclaimer is always adjacent to figures | On any completed study results, confirm the "Journaled measurements … Descriptive only — not trading advice." framing text appears above the distribution blocks and again at the foot of the panel |
| `/studies` | `StudyResultsView` — empty selection state | New component | Right column has an explicit empty state before a study is selected | Load `/studies`; confirm the right column shows a grey panel with "∅" and "Create a study, or select one from the list, to read its results." (not a blank white or crash area) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/studies.py` (new) — study runner module and `StudyJobManager`; all capabilities are consumed via the four `/research/studies` endpoints which the frontend wires directly.
- `apps/backend/app/research/store.py` — `StudyRecord` dataclass and study repository methods (first writes to `studies` / `study_occurrences` tables, v7 schema unchanged); directly backing the persisted results served verbatim to the UI.
- `apps/backend/app/config.py` — six new study config keys (`study_null_arm_count`, `study_arm_sustain_seconds`, `study_arm_cooldown_seconds`, `study_occurrence_r_spread_multiple`, `study_occurrence_r_floor`, `study_null_baseline_seed`) plus `study_list_max`; no UI control over these values but they shape the numbers rendered in the results view.
- `apps/backend/app/main.py` — shutdown drain for in-flight study jobs; not observable as a UI surface change.
- `apps/backend/app/research/taxonomy.py` — additive studies display-copy keys (`GET /research/taxonomy → studies`); consumed by the frontend for all labels, but the taxonomy endpoint itself has no UI surface.
- `apps/backend/tests/test_studies.py`, `test_studies_reference.py`, `test_studies_api.py` — 42 new backend test cases; no UI surface.
- `apps/frontend/lib/api.ts`, `apps/frontend/lib/types.ts` — study API functions (`fetchStudies`, `fetchStudy`, `createStudy`, `cancelStudy`) and TypeScript types; no directly visible UI surface but they wire the page to the backend.

---

## Summary

- **Frontend surfaces changed:** 26
- **New pages/routes:** 1 (`/studies`)
- **Modified components:** 1 (`NavBar.tsx` — Studies entry enabled)
- **New components:** 3 (`StudyCreateForm`, `StudyList`, `StudyResultsView`)
- **Navigation changes:** yes (Studies link activated globally)
- **Backend-only changes:** 7

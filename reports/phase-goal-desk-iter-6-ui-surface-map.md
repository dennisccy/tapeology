# Phase goal-desk-iter-6 — UI Surface Map

**Phase:** goal-desk-iter-6
**Date:** 2026-07-26
**Written by:** ui-impact-analyst

---

## Changed-File Classification

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/frontend/app/desk/page.tsx` | frontend-direct | direct | `DeskHistoryRow`/`DeskHistoryTable` made clickable, new `DeskPopulatedScreen` component holds the "Latest" control + viewing banner + error note, `DeskRow`/`DeskSkipRow` gained drill-in `Link`s. |
| `apps/frontend/app/structure/page.tsx` | frontend-direct | direct | New `useSearchParams`-driven prefill effect (marked `J-05-PREFILL-START/END`) + `Suspense`-wrapped default export; additive only when params absent. |
| `apps/frontend/lib/api.ts` | frontend-direct | direct | New `fetchDeskScreenByDate()` client helper — the code path `/desk/page.tsx` calls to fetch a history row's snapshot; no new backend route (proxies the already-shipped `GET /research/desk/screen?date=`). |
| `apps/backend/tests/test_desk_ui_guards.py` | backend-internal (test) | none | Source-introspection guard tests (read `.tsx` files as text, assert on substrings) proving `/desk` never calls a structure-compute endpoint and the `/structure` prefill reuses `handleLoad`. Guards a UI contract but is not itself a UI surface — nothing here renders or is user-reachable. |
| `runs/goal-session-desk/journey-scripts/J-04.json` | config (test infra) | none | Fixes a golden replay script's step 5/6 from a mutating click (`desk-run-screen-button`) to read-only `expect` assertions. Affects only the QA replay harness's behavior against a backend, not anything a real user sees. |

No new backend route was added this iteration — `GET /research/desk/screen?date=` already existed
(shipped iter-3); this iteration is the endpoint's first frontend consumer.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/desk` | `DeskHistoryTable` / `DeskHistoryRow` (`data-testid="desk-history-row"`) | Changed behavior | History rows are now clickable — selecting one fetches and displays that exact date's own recorded screen instead of the latest one | Click the history row for `2026-06-22` and verify the Briefing table's AAPL row shows `band_class A`, and the values match `GET /research/desk/screen?date=2026-06-22` field-for-field, with no new POST issued (check network tab) |
| `/desk` | "Latest" control (`data-testid="desk-history-latest-button"`) + viewing banner (`data-testid="desk-viewing-indicator"`) | New component | Lets the operator return to the newest screen after viewing history, and makes clear which screen is currently on screen | From the `2026-06-22` history view, click the "Latest" button and verify the page reverts to the original latest snapshot's rows/skipped counts and the "Viewing the recorded screen for..." banner disappears |
| `/desk` | Briefing table ranked row drill-in (`data-testid="desk-row-drill-in"` inside `desk-screen-row`) | Added navigation | Every ranked row is now a link into `/structure` for that symbol/date, closing the previously-deferred drill-in gap | Click anywhere on the AAPL ranked row while the `2026-06-22` screen is displayed; verify the browser navigates to `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`, the Symbol/As-of fields show exactly those values, and the AAPL tradable-map band (298.02–300.1001) is already rendered without clicking Load |
| `/desk` | Skipped Members table row drill-in (`data-testid="desk-skip-row-drill-in"` inside `desk-skip-row`) | Added navigation | Skipped symbols also drill into `/structure`, per the iter-6 assumption that both row kinds link | Click a skipped-member row's symbol; verify navigation to `/structure?symbol=<SYM>&asof=<date>` and that `/structure` renders its own honest empty/no-bars state for that symbol without an error or crash |
| `/desk` | History fetch error note (`data-testid="desk-history-fetch-error"`) | New error state | A history click for a date with no matching screen, or a momentarily unreachable backend, must not blank or crash the page | Click a history row for a date with no recorded screen (or simulate a network failure) and verify the amber note appears while the previously-displayed Briefing/Skipped/Provenance sections remain unchanged |
| `/structure` | Symbol/As-of fields + auto-Load (`J-05-PREFILL-START/END` effect via `useSearchParams`) | Changed behavior (additive) | Arriving from a `/desk` drill-in link should not require a second manual Load click | Navigate directly to `/structure?symbol=AAPL&asof=2026-06-22T23:59:59Z`; verify the Symbol field shows "AAPL", the As-of field shows the exact timestamp, and the tradable-map chart is already drawn on first paint (no Load click) |
| `/structure` | No-params baseline (Load form default state) | Unchanged (regression check) | Must remain byte-identical when no query params are present, per the anti-goal "frozen foundations" rule | Open `/structure` with no query string; verify the Symbol and As-of fields are both empty, no chart/data is loaded, and the page matches the pre-iteration baseline screenshot pixel-for-pixel |
| `/structure` | Partial-params edge case | Changed behavior (additive edge case) | Only one of `symbol`/`asof` present must not trigger a partial auto-load | Open `/structure?symbol=AAPL` (omit `asof`); verify the Symbol field stays empty and no load is triggered, identical to opening `/structure` with no params at all |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/tests/test_desk_ui_guards.py` — new source-introspection guard tests (TC-5/TC-6)
  that scan the `.tsx` source of `/desk` and `/structure` as plain text; asserts `/desk` never
  references a structure-compute endpoint/function and the new `/structure` prefill code calls only
  the existing `handleLoad` — no UI surface affected, this only guards a contract at test time.
- `runs/goal-session-desk/journey-scripts/J-04.json` — replaces a mutating click step with two
  read-only `expect` assertions in the golden replay script for the QA/regression harness — no UI
  surface affected; this changes what the automated replay tool does, not what a user sees or can
  do.

---

## Summary

- **Frontend surfaces changed:** 2 (`/desk`, `/structure`)
- **New pages/routes:** 0
- **Modified components:** 6 (`DeskHistoryTable`/`DeskHistoryRow`, `DeskRow`, `DeskSkipRow`,
  `DeskPopulatedScreen` (new), `StructurePage`/`StructurePageContent` split, `api.ts`'s
  `fetchDeskScreenByDate` helper)
- **Navigation changes:** no (top nav unchanged: Cockpit / Structure / Desk)
- **Backend-only changes:** 2 (guard test file, journey-script replay fix) — neither adds or
  changes a backend route

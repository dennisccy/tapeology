# Phase goal-desk-iter-4 — UI Surface Map

**Phase:** goal-desk-iter-4
**Date:** 2026-07-25
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/`, `/structure`, `/desk` (all pages) | `NavBar` (`data-testid="nav-link"`) | Added navigation | `app/meta.py`'s `UI_ROUTES` gained a third entry (`/desk`, "Desk"); `NavBar.tsx` renders whatever `GET /meta/ui-routes` returns and was not itself edited | Load any page (e.g. `/`); confirm the top nav shows exactly three links in order "Cockpit", "Structure", "Desk", and that clicking "Desk" navigates to `/desk` with that link highlighted emerald/active (`aria-current="page"`). |
| `/desk` | `DeskPage` (new route, `data-testid="desk-title"`) | New page | J-04 ships the era's first new page | Navigate directly to `/desk`; confirm the page renders a header reading "Desk" and does not 404 or render blank. |
| `/desk` | Empty-state panel (`data-testid="desk-screen-not-computed"`) | New feature | Honest empty state before any screen has ever been computed (`latest === null`) | Against a backend with zero recorded screens, load `/desk`; confirm the exact text "Desk screen not computed yet." appears with an enabled "Run Screen" button (`data-testid="desk-run-screen-button"`, `disabled` attribute absent) and an enabled "Top-up" button (`data-testid="desk-topup-button"`). |
| `/desk` | Provenance panel (`data-testid="desk-provenance"`) | New feature | Every screen must carry its full traceability (universe snapshot, `as_of`, fingerprint, freshness) | With a computed screen loaded, confirm the Provenance panel shows five labeled values — "Universe snapshot", "Screen date", "As of", "Config fingerprint", "Window last requested" — each populated with a real (non-empty, non-placeholder) string. |
| `/desk` | Briefing table (`data-testid="desk-screen-rows-table"`, rows `data-testid="desk-screen-row"`) | New table | Ranked screen rows are the page's core deliverable | With a screen containing ranked rows, confirm each row shows symbol, side, a "Class X" chip captioned "nearest same-class band" (or "Unclassified" when `band_class` is null), a distance value ending in "bps", and a numeric score, in the same order the snapshot's own `rows` array serves them (no client-side re-sort). |
| `/desk` | Coverage badges (`data-testid="desk-coverage-badge"`) | New component | Per-timeframe bar coverage must render honestly per row, never assuming uniform coverage (iter-2 lesson) | Find a row for a symbol with partial timeframe coverage (e.g. `1h`/`1d` present, `4h`/`1w` absent); confirm exactly one badge renders per timeframe key that row's own `coverage` object carries — `data-has-bars="true"` badges colored emerald, `data-has-bars="false"` badges colored muted slate — never a fixed 4-badge set assumed for every row. |
| `/desk` | Skipped Members section (`data-testid="desk-skipped-section"`) | New feature | Screened-but-unranked members must be shown, grouped by an honest reason | With a screen that skipped members for both reasons, confirm a "Skipped — no bars (N)" heading (`data-testid="desk-skipped-no-bars-heading"`) and a "Skipped — no basis session (N)" heading (`data-testid="desk-skipped-no-basis-heading"`) each render with the correct count, and confirm a heading is omitted entirely (not shown as "(0)") when its group has zero members. |
| `/desk` | Screen History panel (`data-testid="desk-history-table"`) | New table | Read-only list of past screen runs (click-through is J-05, deferred) | Confirm the history table lists one row per past screen (`data-testid="desk-history-row"`) showing date, rows count, skipped count, and a provenance-summary string; confirm clicking a row triggers no navigation and no new network request. |
| `/desk` | "Run Screen" button + live progress (`desk-run-screen-button`, `desk-screen-compute-running`) | New form/action | First-ever UI trigger for the screen-compute manager (previously CLI/API-only) | Click "Run Screen"; confirm exactly one `POST /research/desk/screen/compute` fires, the button becomes disabled and relabels to "Computing…", a progress line (`data-testid="desk-screen-compute-progress"`) shows "N / M members" with a pulsing dot, and a "Cancel" button (`data-testid="desk-screen-compute-cancel"`) appears. |
| `/desk` | "Run Screen" single-flight guard | New safeguard | A second trigger must never start a second concurrent job | While a screen compute is running, confirm the "Run Screen" button stays disabled and unclickable in the same tab; separately, issue a second `POST /research/desk/screen/compute` directly (e.g. via devtools or a second tab) and confirm the response's `started` field is `false` with the same job `id` as the first trigger. |
| `/desk` | "Run Screen" Cancel control (`desk-screen-compute-cancel`) | New feature | Operator must be able to abort a running screen | While a screen compute is running, click "Cancel"; confirm the button relabels to "Cancelling — finishing the current member…", then once the job resolves confirm the text "Screen compute cancelled — nothing was recorded this run." (`data-testid="desk-screen-compute-cancelled"`) appears and the Screen History list gained no new row. |
| `/desk` | "Run Screen" no-universe error (`desk-screen-compute-trigger-error`) | New error state | Closes audit B4 — refuse rather than silently persist an empty snapshot | Against a backend with zero registered universe snapshots, click "Run Screen"; confirm an inline red error paragraph (`data-testid="desk-screen-compute-trigger-error"`) appears naming the missing universe, the button returns to its normal enabled "Run Screen" label (not stuck on "Computing…"), and the Screen History list gained no new row. |
| `/desk` | "Top-up" button + live progress (`desk-topup-button`, `desk-topup-compute-running`) | New form/action | First-ever UI trigger for the J-02 bar top-up compute manager (previously CLI/API-only) | Click "Top-up"; confirm exactly one `POST /research/desk/topup/compute` fires, the button becomes disabled and relabels to "Topping up…", a progress line (`data-testid="desk-topup-compute-progress"`) shows "N / M pairs" with a pulsing dot, and once at least one pair resolves a "last: SYMBOL timeframe — outcome" line (`data-testid="desk-topup-compute-current"`) appears. |
| `/desk` | "Top-up" Cancel control (`desk-topup-compute-cancel`) | New feature | Operator must be able to abort a running top-up | While a top-up is running, click "Cancel"; confirm the button relabels to "Cancelling — finishing the current pair…", then once the job resolves confirm the text "Top-up cancelled — pairs already recorded before the cancel stay stored." (`data-testid="desk-topup-compute-cancelled"`) appears. |
| `/desk` | All-skipped screen rendering (`desk-rows-empty`) | New edge-case handling | An all-skipped screen must render the empty-ranked-rows message, never the not-computed panel | Load a screen snapshot where `rows` is `[]` but `skipped` is non-empty; confirm the Briefing panel shows "No members ranked in this screen." (`data-testid="desk-rows-empty"`) alongside a populated Skipped Members section, and confirm the "Desk screen not computed yet." panel does NOT render (that panel is gated on `latest === null` only). |
| `/desk` | Mount network behavior | New safeguard | Page load must never trigger a compute as a side effect | Open the browser network tab and load `/desk` fresh; confirm exactly three GET requests fire (`/research/desk/screen`, `/research/desk/screen/compute`, `/research/desk/topup/compute`) and zero POST requests fire before any button is clicked. |
| `/desk` | Backend-unreachable poll fallback (`desk-screen-unavailable`, poll-tick fold) | New error handling | A failed poll tick must never fabricate a snapshot | While a screen or top-up compute is running, stop the backend process mid-poll; confirm the progress panel keeps showing the last known "N / M" value rather than clearing, crashing, or displaying a fabricated status. |

<!-- Change Type options used above: New page | New table | New component | New form/action | New feature | New error state | New safeguard | New edge-case handling | Added navigation -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/research/desk_screen_compute.py`'s new `reused: bool` / `screen_id: str | null`
  fields — additive fields on the SAME job snapshot `/desk`'s "Run Screen" progress panel already
  polls (`GET /research/desk/screen/compute`); present in the API response and the frontend's
  `DeskScreenComputeSnapshot` type, but not read or displayed by any element on `/desk` this
  iteration — no UI surface renders either value (see "Not Visible Yet" in the companion report).
- `apps/backend/app/research/desk_universe.py`'s `UniverseStore.record` corrupt-file `.exists()`
  guard — protects universe-snapshot recording from silently overwriting a damaged file at a
  colliding checksum path — no UI surface affected; universe registration has no UI entry point in
  this or any prior iteration (CLI/API-only).
- `apps/backend/tests/test_meta_routes.py`, `test_desk_screen_compute.py`,
  `test_desk_universe.py` — widened/added test coverage for the changes above (route-count
  assertions, `reused`/`screen_id` behavior, the no-universe refusal, the corrupt-file guard) — no
  UI surface affected; these are test files, not application code.
- `runs/goal-session-desk/journey-scripts/J-07.json` — step 8's replay timeout raised from the
  file's default `15000`ms to an explicit `20000`ms — test-infrastructure (golden-replay script)
  only, not application code — no UI surface affected.

---

## Summary

- **Frontend surfaces changed:** 2 (the new `/desk` page; the `NavBar`'s rendered output across
  every existing page — note `NavBar.tsx`'s own source is byte-unchanged, only the backend route
  list it fetches grew by one entry)
- **New pages/routes:** 1 (`/desk`)
- **Modified components:** 0 (no existing component's source file was edited — `NavBar.tsx`,
  `components/Panel.tsx`, `app/structure/page.tsx`, `PriceChart.tsx`, `StructureChart.tsx`, and
  `app/page.tsx` are all confirmed byte-unchanged)
- **Navigation changes:** yes — third top-nav entry, "Desk"
- **Backend-only changes:** 4 (see above)

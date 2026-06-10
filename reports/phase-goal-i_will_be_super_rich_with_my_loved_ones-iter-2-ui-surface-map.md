# Phase goal-i_will_be_super_rich_with_my_loved_ones-iter-2 — UI Surface Map

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-2
**Date:** 2026-06-10
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/` | `ThesisStrip` (idle bar) | New component | Thesis declaration capability added | After starting a watch on any ticker and reaching the settled cockpit, confirm a single-line bar appears between the price chart and the panel grid, containing the text "Declare a thesis on this ticker…" and a "Declare thesis" button — confirm no other cockpit panel shifts position |
| `/` | `ThesisStrip` — declare form | New component | Taxonomy-driven thesis declaration form | Click "Declare thesis", wait for the form to load, then confirm a Setup dropdown, a Direction dropdown, an Invalidation price input, and a "Declare" + "Cancel" button are all visible; confirm no "Level" field is shown when "Absorption Reversal" is selected |
| `/` | `ThesisStrip` — level field | New component | Conditional field for level-requiring setups | Open the declare form, change the Setup dropdown to "Level Break" (or "Failed Move Fade"), and confirm a "Level" price input field appears; change back to "Absorption Reversal" and confirm the Level field disappears immediately |
| `/` | `ThesisStrip` — taxonomy loading state | New component | Explicit loading state prevents fabricated form | Click "Declare thesis" and observe the strip shows "Loading the setup catalog…" while the taxonomy request is in flight (only visible at slow network; verify by throttling DevTools network to Slow 3G and clicking Declare) |
| `/` | `ThesisStrip` — inline validation error | New component | Backend rejection messages surfaced verbatim | On the open form, select "Absorption Reversal / Long", enter an invalidation price that is higher than the current last price, submit, and confirm a rose error message appears below the form and the form values (setup, direction, invalidation) are preserved unchanged |
| `/` | `ThesisStrip` — 409 duplicate error | New component | Prevents a second thesis while one is active | After a thesis is successfully declared (active strip visible), click the browser back/forward to confirm the strip remains active; then via the REST API declare a second thesis directly (POST /research/thesis) and confirm the strip surface continues to show the first thesis — or test by sending the POST directly and confirming a 409 with a plain message |
| `/` | `ThesisStrip` — active thesis display | New component | Active thesis judgment rendered from WS frame | Declare a valid thesis and confirm the strip switches to show: the setup name in sentence case, the direction in emerald (long) or rose (short), the invalidation price in monospace font, a bulleted statement list each with a dot and a "met" / "not yet" / "violated" label, a slate "Pending" badge, and a footer line including "source" and "feed" labels |
| `/` | `ThesisStrip` — statement status dots | New component | Live statement status recomputed per WS event | While an active thesis is displayed, observe that statement status dots and labels update live as the tape changes — specifically confirm that at least one statement transitions between statuses (met/not yet/violated) without a page reload, using a simulated ticker that produces predictable state transitions |
| `/` | `ThesisStrip` — monitor_status failed notice | New component | Honest surfacing of backend monitor errors | Cannot be triggered via normal UI; test by manually triggering a monitor fault (e.g. breaking the DB path), then confirm the amber text "Monitor unavailable — statement statuses may be stale." appears in the active thesis footer, and the live tape feed (state, confidence, chart) continues updating normally |
| `/` | `ThesisStrip` — idle guard (no thesis) | New component | Strip must not appear before settled snapshot | Start a watch and observe the connecting / waiting states — confirm the thesis strip does not appear during "Connecting…" or "Waiting for first event" phases; it should appear only once the cockpit panel grid is visible |
| `/` | `page.tsx` — ThesisStrip mount point | Updated layout | New strip inserted between PriceChart and Cockpit | Navigate to `/`, start a sim watch on SIM-BIDABS, wait for the cockpit to settle, and confirm the order of elements top-to-bottom is: TopBar, PriceChart, ThesisStrip (idle), Cockpit panel grid — with no visible gap or reflow |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/config.py` — added `TAPEOLOGY_JOURNAL_DB` env var, `journal_busy_timeout_ms`, `journal_schema_version`, and `config_fingerprint()` SHA-256 hash — no UI surface; affects where the journal DB is written on disk
- `apps/backend/app/research/__init__.py` — new Python package marker — no UI surface
- `apps/backend/app/research/taxonomy.py` — single source of all setup/direction/statement-template data; surfaced only via `GET /research/taxonomy` which is consumed by the ThesisStrip declare form
- `apps/backend/app/research/store.py` — SQLite journal store (WAL, writer queue, versioned schema, append-only verdict_events) — no direct UI surface; backs the thesis persistence that the strip reads via the WS frame
- `apps/backend/app/research/monitor.py` — research monitor observer; attached per-watch via the observer seam — no UI surface of its own; its output feeds the WS `thesis` key
- `apps/backend/app/watch_manager.py` — added exception-isolated `on_engine_created` hook — no UI surface; wires the monitor to each new engine
- `apps/backend/tests/test_research_store.py` — new test file — no UI surface
- `apps/backend/tests/test_research_monitor.py` — new test file — no UI surface
- `apps/backend/tests/test_research_api.py` — new test file — no UI surface
- `apps/backend/tests/test_observer_equivalence.py` — extended test file — no UI surface
- `.gitignore` — added `*.db-wal` and `*.db-shm` WAL sidecar patterns — no UI surface

---

## Summary

- **Frontend surfaces changed:** 1 route (`/`)
- **New pages/routes:** 0
- **Modified components:** 2 (`ThesisStrip` new, `page.tsx` mount point updated)
- **Navigation changes:** no (Journal/Studies nav deferred to later iterations)
- **Backend-only changes:** 11

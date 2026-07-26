# Phase goal-desk-iter-6 — UX Regression Review

**Date:** 2026-07-26

**Verdict:** UX-REGRESSION-PASS

---

## New Capability Discoverability

| Capability | Navigation path from home | Clicks | Visual feedback | Assessment |
|---|---|---|---|---|
| Browse a past recorded screen in place (`/desk` history click-through) | Persistent top `NavBar` (`Cockpit · Structure · Desk`, driven by `GET /meta/ui-routes`, unchanged this iteration) → `Desk` → click a row in the already-visible "Screen History" table | 1 click to `/desk`, then 1 click on a row the operator can already see and already understood as data (it was a read-only table since iter-4) | `bg-slate-800/60` solid highlight + `data-selected="true"` on the clicked row, plus a new banner ("Viewing the recorded screen for `<date>` — not the latest.") above the Provenance panel — confirmed live via screenshot `UT-03-result.png` and DOM assertion in `phase-goal-desk-iter-6-ui-test-results.md` (UT-03) | Discoverable. The capability upgrades a table the operator was already looking at; no new nav entry needed, and the state change is unambiguous (banner + persistent highlight, not just a hover cue). |
| Return to the newest screen ("Latest" control) | Appears inline in the viewing banner, next to the text, only when a non-latest screen is on screen | 1 click, and it is co-located with the exact state it undoes | Banner disappears, row highlight clears (`data-selected="false"` on both rows per UT-04) | Discoverable — contextual, appears exactly when relevant, gone when not needed (no permanent clutter). |
| Drill in from a ranked or skipped briefing row to `/structure` | Same `/desk` page, click anywhere on a row in the Briefing table or the Skipped Members table | 1 click from a page already reached in 1 click (≤2 total from home) | Whole-row "stretched link" (`<Link className="absolute inset-0">` inside a `position: relative` `<tr>`), `hover:bg-slate-900/40` background + browser's native pointer cursor on hover (confirmed live, UT-12: `getComputedStyle().cursor === "pointer"` on hover) | Discoverable within the rubric's click-depth definition. One soft note: the row gives no *persistent* affordance (icon, underline, "→") that it is a link before the operator hovers — see Visual Consistency below. Not flagged as a hard gap because (a) it matches this app's existing "hover-only" convention elsewhere, (b) the phase's own Visual Requirements explicitly called for "no new chrome," and (c) discoverability was itself a tested acceptance criterion (UT-12, PASS). |
| `/structure` auto-load via `?symbol=&asof=` | Not a capability an operator navigates to directly — it activates automatically when arriving via one of the drill-in links above | 0 extra clicks (the point of the feature) | Symbol/As-of fields pre-filled, tradable-map chart already drawn on first paint (UT-05, UT-06 screenshots) | Fully discoverable by construction — no separate discovery path is needed or expected. |

No new page or nav entry was added, and none was needed — `docs/phases/goal-desk-iter-6.md`'s own "Navigation changes: none" claim holds; `NavBar.tsx` and `app/meta.py`'s `UI_ROUTES` are byte-unchanged this iteration (confirmed via the dev handoff's `git diff --stat`, empty).

## Regression Risk

| Shared component | Prior feature(s) it serves | This iteration's change | Risk level | Evidence it still works |
|---|---|---|---|---|
| `apps/frontend/app/structure/page.tsx` | The era's single deep-dive instrument page — built by `goal-structure_ui` (iters 0–4), heavily reshaped by `goal-tradable_wall` (iters 0–10, the ≤10-band declutter), `goal-fast_wall` (iters 0–5, the operator-run Compute button), `goal-clean_slate` (iter-2, the two-page Cockpit+Structure merge), and `goal-yahoo_fetch` (iter-5, the "Fetch from Yahoo Finance" button + provenance badge). This is the ONE file this era's anti-goal rail names as frozen-but-sanctioned-for-one-edit. | Added a `useSearchParams`-driven prefill effect (delimited `J-05-PREFILL-START/END`) that calls the *existing* `handleLoad`, plus a `Suspense`-wrapper-only refactor (renamed the default export to `StructurePageContent`, added a thin new `StructurePage` default export). No edit inside the renamed component beyond the new prefill block. | High blast radius by nature of the file, but low residual risk given the change is additive-only and the byte-unchanged-when-absent behavior was itself a first-class acceptance criterion (TC-4/TC-8 in the plan). | J-07 (this project's explicit `/structure` regression sentinel: AAPL as-of 2026-06-22 Load → pinned wall renders) passed (`UT-J-07`, both the merged LLM+replay results and the standalone deterministic-replay report). TC-4 (no-params baseline) verified live: `UT-02` — both inputs `value=""`, Load disabled, idle state, no console errors. The partial-param edge case (only one of `symbol`/`asof`) verified twice: `UT-08`/`UT-09` — both fields empty, idle, after a ≥2s wait (rules out a race where the effect fires on a stale partial value). Manual Load flow re-verified end-to-end: `UT-10` — typed AAPL + the same as-of, clicked Load, same band set rendered as the auto-loaded case. |
| `apps/frontend/app/desk/page.tsx` | J-04 (`goal-desk-iter-4`): the Provenance panel, Briefing table, Skipped Members table, Run Screen / Top-up controls. | History rows made clickable, `DeskPopulatedScreen` extracted, ranked/skip rows wrapped in drill-in `Link`s. | Low residual risk. | `UT-J-04` (regression journey for the `/desk` briefing page) passed in both the merged results and the standalone replay report. `UT-11` explicitly re-confirms Run Screen and Top-up buttons still render, enabled, unchanged labels, and were NOT clicked (avoiding the iter-4 audit's write-side-effect lesson). |
| `apps/frontend/lib/api.ts` | Every page that imports it (`/desk`, `/structure`, `/`). | Purely additive: one new function (`fetchDeskScreenByDate`) plus one new type import. No existing function signature or shape changed, per the dev handoff. | Low. | No existing caller's behavior could change from an added, unreferenced-elsewhere function; full backend suite (1341 collected / 0 failed / 8 skipped) and `next build` both green. |
| `runs/goal-session-desk/journey-scripts/J-04.json` | The J-04 golden replay script itself (test infrastructure, not a UI surface). | Step 5/6 changed from a mutating click (`desk-run-screen-button` + `wait_for`) to two read-only `expect` assertions. | Not a UI regression — this is a fix to a latent replay-harness hazard (the golden was silently able to write a real screen snapshot into any backend it replayed against). Confirmed positive: replaying it now leaves the screen-store file count unchanged (per the dev handoff, TC-7). | N/A (infra fix, not user-facing). |

No other prior-phase user-visible surface (`/` Cockpit, its chart/tape components, `PriceChart.tsx`, `StructureChart.tsx`, `bars.py`) was touched this iteration — confirmed empty in the dev handoff's `git diff --stat` for those paths, and the plan's own "No changes expected to" list matches what was actually built.

## UI vs Backend Parity

- **Gap closed, not opened.** `GET /research/desk/screen?date=` was shipped at iter-3 (three iterations ago) but had zero frontend callers until this iteration — a standing backend-ahead-of-UI gap. This iteration's `/desk` history click-through is that endpoint's first UI consumer, closing the gap.
- **No new backend value was introduced this iteration** (confirmed in both the dev handoff and the ui-surface-map: "No new backend route was added this iteration"), so there is no new capability left stranded behind an unwired UI path.
- **J-06 (MCP contract v3, 17 tools)** remains explicitly out of scope, scheduled next iteration. This is acceptable under the backend-only-phase rule: MCP tools are a programmatic/agent-access surface, not a human-facing UI capability, and the phase spec itself defers it by design, not by oversight.
- **Three carried hardening items** (CLI screen-write-path guard, per-series price-less-row filter, chart-guard-test re-tightening) are internal engineering/test-hardening tasks with no user-facing surface — correctly not claimed as UI-visible anywhere in `user-visible-changes.md`.
- `user-visible-changes.md`'s own "Not Visible Yet" section states "None" for this iteration and the reasoning holds: this was a pure wiring iteration over already-registered data.

## Flags

### Hidden Capabilities
- None found.

### Undiscoverable Capabilities
- None found under the skill's click-depth rubric (all new capabilities are reachable in ≤2 clicks from home, with reactive visual feedback for each).

### Potential Regressions
- None confirmed. Both components with meaningful blast radius (`/structure/page.tsx`, shared across five prior eras' worth of work; `/desk/page.tsx`, shared with J-04) have dedicated passing regression evidence (J-07, J-04, and the TC-4/TC-8/TC-9/TC-10-equivalent UT-02/08/09/10/11 checks) rather than being asserted safe by inference alone.

### Visual Consistency
- Both edited pages continue the house dark/dense/terminal-grade style (slate panels, monospace numeric cells, emerald active-nav/positive accents, amber for degraded/error states) with no new colors or chrome introduced, consistent with the plan's own Visual Requirements and confirmed in the `UT-01`/`UT-03`/`UT-05` screenshots.
- Soft note (not a flag): the new drill-in rows signal clickability only via `hover:bg-slate-900/40` + cursor change, with no persistent icon or underline. This matches the pre-existing convention this codebase already uses for other clickable table rows in `/desk`, and discoverability of this exact affordance was itself a tested, passing acceptance check (`UT-12`). Worth keeping in mind if a future iteration adds a row-click affordance elsewhere and wants to reconsider the convention project-wide, but it is not a deviation introduced by this iteration and does not warrant a WARN on its own.
- The new "viewing: not latest" banner and the row-selected highlight (`bg-slate-800/60`, `data-selected`) give a persistent, unambiguous signal of which snapshot is on screen — directly satisfying the plan's own Visual Requirements item 3 ("the currently-displayed-snapshot vs latest-snapshot distinction must be visually clear").

## Recommendation

No action required. All new capabilities from this iteration are discoverable within the existing navigation (no new nav entry needed or added), regression risk on the two shared/frozen files this iteration touched (`/structure/page.tsx`, `/desk/page.tsx`) is covered by passing dedicated sentinel journeys (J-07, J-04) plus explicit before/after-state checks, and the one standing UI-vs-backend parity gap this era carried (the unconsumed `?date=` endpoint) is now closed with no new gap opened in its place.

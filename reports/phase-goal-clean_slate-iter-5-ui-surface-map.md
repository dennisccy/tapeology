# Phase goal-clean_slate-iter-5 — UI Surface Map

**Phase:** goal-clean_slate-iter-5
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/structure` | "Case Studies" panel + table (`aria-label="Case studies"`, `data-testid="case-studies-table"`) | Restored/un-hidden feature | `SHOW_CASE_STUDIES` flipped `false`→`true` (`apps/frontend/app/structure/page.tsx:335`); the section was fully built in era 5B/5C but render-gated off | Load `/structure` with symbol `AAPL` and as-of `2026-06-22T21:00:00Z` (the pinned recorded window with scanned band-touch events) and click "Load"; confirm a "Case Studies" panel renders below the Levels & Zones section with a table whose header row reads symbol / session / band / reaction / forward returns, populated with at least one row |
| `/structure` | Case Studies row → drill-in (`data-testid="case-studies-row"` click → `data-testid="case-drillin"`) | Restored interaction | Same flag flip; the row-click handler, `selectedSetupId` state, and drill-in fetch already existed in era 5B/5C — only reachability changed | Click any row in the populated `case-studies-table`; confirm a "Case Studies — drill-in" panel appears showing that row's band and reaction (via `data-testid="case-drillin-reaction"`), and either a populated `data-testid="case-drillin-tape-timeline"` list or the literal text "No recorded tape for this event." |
| `/structure` | Case Studies filters (`data-testid="case-studies-filter-symbol"` input, `data-testid="case-studies-filter-reaction"` select) | Restored interaction | Same flag flip | Type "AAPL" into the Symbol filter, then separately pick "chopped" from the Reaction dropdown (options: All / rejected / broke / chopped); confirm the table's visible rows narrow to only matching entries, or — if nothing matches — the panel shows the exact text "No events match these filters." |
| `/structure` | Case Studies honest empty/error sub-states (`data-testid="case-studies-loading"`, `-unavailable`, `-empty`) | Restored (now reachable) | Same flag flip — these sub-states were built alongside the table but were unreachable while the whole section was hidden | Load `/structure` for a symbol/as-of combination with zero scanned band-touch events; confirm the panel shows the exact text "No band-touch events scanned yet." rather than a blank area or an empty-bodied table |
| `/structure` | Framing paragraph (`data-testid="structure-framing"`) | Changed copy | Reinstated the sentence commit `e60f6a7` had dropped, three days before this clean-up project began | Read the paragraph directly under the `/structure` page header; confirm it contains the exact substring "Case Studies lists every band-touch event with its reaction, forward returns, and — once recorded — its tape timeline;" immediately before "Edge Report compares v1, structure_tape, and structure_tape_map" |

<!-- Change Type options used: Restored/un-hidden feature | Restored interaction | Changed copy -->

---

## Backend-Only Changes (No UI Impact)

- No backend source file changed this iteration — `git diff --stat HEAD` shows exactly one product
  file (`apps/frontend/app/structure/page.tsx`). The full backend pytest suite (1167 passed / 7
  skipped / 0 failed), the named guard/chart-guard test files re-run in isolation (47 passed), the
  MCP `list_tools()` count/name check, the deleted-route 404 sweep, and the 11-module import-grep
  sweep are all re-verification of already-shipped backend behavior from prior iterations — no new
  backend surface, so no UI impact.
- `runs/goal-session-clean_slate/iter-5/kept-route-after.txt` — new evidence artifact: a
  byte-comparison capture of the 28 kept routes vs. iter-4's capture (0 new diffs). Process/evidence
  output, not a product surface.
- `runs/goal-session-clean_slate/iter-5/diff-vs-inventory-crosscheck.md` — new evidence artifact:
  the session-wide cumulative diff-vs-inventory cross-check. Process/evidence output, not a product
  surface.
- `runs/goal-session-clean_slate/telemetry.jsonl`, `runs/goal-session-clean_slate/trace/trace.jsonl`
  — pipeline telemetry/trace logs updated by this iteration's dispatch. No UI impact.
- `docs/handoffs/goal-clean_slate-iter-5-dev.md`, `docs/handoffs/goal-clean_slate-iter-5-frontend.md`,
  `docs/phases/goal-clean_slate-iter-5.md`,
  `reports/phase-goal-clean_slate-iter-5-implementation-summary.md`,
  `reports/qa/goal-clean_slate-iter-5-test-plan.md`,
  `reports/reviews/goal-clean_slate-iter-5-review.md` — pipeline process documentation for this
  iteration. No UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 (`/structure`'s Case Studies section, plus its own
  framing-paragraph sentence)
- **New pages/routes:** 0
- **Modified components:** 1 file (`apps/frontend/app/structure/page.tsx`); 0 new components — the
  existing Case Studies `Panel`/table/filter/drill-in components (built in era 5B/5C) are
  re-enabled, not rebuilt
- **Navigation changes:** no (nav stays exactly Cockpit + Structure, 2 rows)
- **Backend-only changes:** 0 product backend changes; re-verification/evidence artifacts only (see
  above)

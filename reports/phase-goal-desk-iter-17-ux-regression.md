# Phase goal-desk-iter-17 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

**Capability:** the `band` column on `/desk`'s ranked-rows table, disclosing `reference_close`
beside the row's already-recorded `price_low`–`price_high` range, plus a matching new segment in
the row's composite hover tooltip.

- **Navigation path:** from any page, click the top-level **Desk** nav tab (1 click) → the ranked
  table renders immediately with the `band` column as the last of 10 header cells, no scroll or
  extra interaction required. Confirmed live via `document.querySelectorAll('th')` returning
  `["symbol","side","class","distance","score","coverage","tick evidence","basis","history","band"]`
  (`reports/phase-goal-desk-iter-17-ui-test-results.md` UT-01/UT-02) and by the `TC-06-desk-page.png`
  / demo `step-02.png`/`step-08.png` screenshots, which show the full 10-column table at normal
  viewport width with no horizontal scroll needed.
- **qa's UI Evolution Audit** (`reports/qa/goal-desk-iter-17-qa.md`, lines 123-148) — cited, not
  re-derived: Reachability PASS, Visibility PASS, Control PASS (spec declares zero new user
  actions, none built), No-generic-page-dumping PASS. Overall **UI-PASS**. No `coherence.md` exists
  yet for iter-17 (only the decomposer step has run in `runs/goal-session-desk/iter-17/`), so there
  is no coherence-auditor finding to cross-check against qa's audit this iteration — no
  contradiction to flag.
- **Label clarity:** the header reads `band`; the cell repeats `band <low>–<high> · close <val>`.
  This is redundant-looking in isolation, but it is the *same* established convention this era
  already uses for the `basis` and `history` columns (header `basis` / cell `basis 2026-07-23 · 5 d
  before as-of`; header `history` / cell `history 500 sessions · from 2024-07-25` — both visible in
  `UT-05-result.png`). Consistent with precedent, not a new inconsistency.
- **Visual consistency:** the new cell reuses `LABEL_CELL`/`HEADER_CELL_LEFT` and the `fmt()`
  rounded-display helper verbatim (per the frontend handoff, `docs/handoffs/goal-desk-iter-17-frontend.md:39-42`)
  — no new component, color, spacing token, or effect. Screenshots (`step-08.png`, `UT-05-result.png`)
  show the same dark, dense, terminal-grade styling as every adjacent column and as the `/structure`
  and `/` (Cockpit) pages in the same nav bar.
- **Feedback:** none required — read-only disclosure, no control, no state change on interaction
  (matches the spec's own "New user actions: none").

**One caveat, honestly disclosed by the product itself, not a UX defect:** every screen snapshot in
the live/ambient store predates this iteration, so an operator opening `/desk` today sees the
`"close not recorded in this snapshot"` fallback on all 63 visible rows (`UT-03`, `UT-10`) rather
than a populated example. This is not a hidden or undiscoverable capability, though: `/desk` already
carries a **"Run Screen"** button (`apps/frontend/app/desk/page.tsx:1040`, `ScreenComputeControl`,
pre-existing from J-03/J-04) that computes a new screen snapshot against the pinned universe — the
very next real screen run an operator triggers will populate `reference_close` on every row and the
band column will show populated values with zero further UI work. The populated rendering itself
was independently proven correct in a real browser by `UT-05` (`reports/phase-goal-desk-iter-17-ui-test-results.md:31`),
which stood up a scoped rig, computed a new screen, verified the browser's `location.origin` matched
the rig before treating the page as evidence (iter-16 lesson), and captured one screenshot showing
`BRK-B` in-band (`band 488.50–490.85 · close 490.85`, at the high edge) and `LIN` out-of-band
(`band 506.33–509.61 · close 506.32`, below the low edge) — visually confirmed by directly reading
`reports/qa/goal-desk-iter-17-evidence/UT-05-result.png`.

**Note (non-blocking, evidentiary rather than UX):** the demo-narrator artifact
(`reports/phase-goal-desk-iter-17-demo-results.md`) recorded against the *ambient* store at
`:3301`, not the scoped rig, so its gallery (`reports/demo/goal-desk-iter-17/step-01.png` through
`step-08.png`, directly viewed) shows only the legacy-fallback state repeated across every
screenshot — it never narrates an in-band or out-of-band populated row, and its verdict is
`RECORDED_WITH_NOTES` (four soft-note timeouts) rather than the plain `RECORDED` goal.md's TC-12
literally asks for. This does not change the discoverability verdict above (the capability itself
is reachable, correctly rendered, and independently browser-QA'd via UT-05 against a real,
origin-verified page); it is a showcase-artifact completeness gap best owned by the
phase-closure-auditor's artifact-consistency gate, flagged here only for visibility.

## Regression Risk

| Shared component | Prior feature(s) served | Current change | Risk | Evidence |
|---|---|---|---|---|
| `DeskRowsTable` header row | J-04 (ranked table itself), J-08 (basis column), J-11 (history column) | Appended one `<th>band</th>` after `history` | Low | `UT-02` confirms exact 10-cell header order, `basis`/`history` positions unmoved |
| `DeskRow` ranked-row cell | J-04, J-08, J-09/J-10 (coverage/tick-evidence badges), J-11 | Appended one `<td data-testid="desk-row-band">` after the `history` cell | Low | `UT-06` re-verified `side`/`class`/`distance`/`score`/`basis`/`history` text and all 4 coverage badges for `BRK-B`/`LIN` byte-identical to pre-change expectations |
| `deskRowDrillInTitle` composite tooltip | J-08 (`basisLine`), J-11 (`historyLine`) | Appended `bandLine` after the existing segments | Low | `UT-04` confirms the composite `title` string's exact order (`distance · score · basis · history · close/band · coverage timestamps`); the F2 lesson (no per-cell `title` under the stretched drill-in anchor) was applied proactively, so the anchor's pointer-reachability is unchanged |
| Row drill-in navigation (`tr` click → `/structure`) | J-05 | Untouched | Low | `UT-07` confirms clicking `BRK-B` still navigates to `/structure?symbol=BRK-B&asof=...` |
| Screen History row click (in-place swap) | J-12 | Untouched | Low | `UT-07` confirms clicking a Screen History row still swaps in place (no navigation), highlights the row, and re-renders the same 10-column table |
| Skip table | J-02/J-09/J-10 (skip reasons, coverage) | Untouched — intentionally has no `band` column | Low | `UT-08` confirms the skip table still renders exactly 4 columns (`symbol, reason, coverage, tick evidence`), no `band` bleed |
| Regression journeys J-01, J-02, J-03, J-05, J-06, J-07, J-08, J-09, J-10 | all prior desk journeys | N/A — replayed end-to-end | Low | All PASS in `reports/phase-goal-desk-iter-17-ui-test-results.md`; suite grew 1426→1435 passed, 0 regressed, skip count unchanged |

No high- or medium-risk shared component was found. Every prior-iteration behavior that touches the
same table/tooltip components this iteration modified has a direct, passing regression check in this
iteration's own evidence (not merely inferred from "should still work").

## UI vs Backend Parity

| Backend capability | UI surface | Status |
|---|---|---|
| `reference_close` field on every ranked row (`compute_screen`, `desk_screen.py`) | `band` column cell + tooltip `bandLine` on `/desk` | Fully surfaced, same iteration |
| Legacy-row absence contract (key entirely absent, never `null`) | Honest `"close not recorded in this snapshot"` fallback | Fully surfaced, same iteration |
| MCP `desk_screen` tool / `get_endpoint` proxy of the new field | N/A (MCP/agent-facing, not a browser surface — correctly documented as such) | No gap — not a UI capability |

Per `reports/phase-goal-desk-iter-17-user-visible-changes.md`'s own "Not Visible Yet" section: "Nothing
is backend-only in this iteration." Confirmed independently — the new field has no code path that
serves it without also rendering it (`grep` of `page.tsx` shows `reference_close` consumed only by
the `band` cell and `bandLine`; no other backend-only sibling field was added this iteration per the
"Out of scope" list, which explicitly forbids new Data-Contract rows/endpoints/Config fields).

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None. The one populated-example gap on the live ambient store is a data-staleness caveat, honestly
disclosed by three separate artifacts (dev handoff, frontend handoff, user-visible-changes.md), not
a missing UI wire-up — and the existing "Run Screen" control already provides the path to populate
it without any further UI work.

### Potential Regressions
None found. See Regression Risk table above — every shared component carries a passing,
evidence-backed regression check from this iteration's own QA run, not an assumption.

### Visual Consistency
- The new `band` column and tooltip segment reuse existing cell classes (`LABEL_CELL`,
  `HEADER_CELL_LEFT`) and the existing `fmt()` rounding helper verbatim — zero new tokens, zero
  arbitrary values.
- Rendered style (dark background, monospace-leaning numeric alignment, teal coverage badges,
  terminal-grade density) matches the rest of `/desk` and the sibling `Cockpit`/`Structure` pages
  visible in the same nav bar across all reviewed screenshots (`TC-06-desk-page.png`,
  `UT-05-result.png`, `step-08.png`).
- No deviation from the DESIGN SYSTEM found.

## Recommendation

No action required to ship this iteration. Two non-blocking follow-ups worth carrying forward (not
blockers for this verdict):
1. Consider re-recording the demo-narrator's `[NEW]` J-13 walkthrough against the same scoped rig
   `UT-05` used, so the showcase gallery actually narrates an in-band and an out-of-band populated
   row rather than eight screenshots of the same legacy-fallback state — this is an artifact
   completeness matter for the phase-closure-auditor/demo lane, not a product defect.
2. When the next real "Run Screen" click lands a post-iteration snapshot on the ambient store, spot
   check the live `/desk` page once to see the populated `band` column in ordinary use (purely
   confirmatory — UT-05 already proves the rendering logic correct in a real, origin-verified
   browser).

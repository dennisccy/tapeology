# Phase goal-desk-iter-15 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

- **History-depth disclosure (`history_sessions`/`history_start` per ranked `/desk` row).**
  Navigation path: `/` (Cockpit) → click **Desk** in the 3-link nav (Cockpit / Structure / Desk) →
  ranked table is visible immediately on page load, no further click/scroll/toggle required. That
  is **1 click from home**, well inside the 2-click bar.
  - The new `history` `<th>` sits immediately after the existing `basis` column in the same
    `<thead>` row (`apps/frontend/app/desk/page.tsx:368`), confirmed live by QA's UT-01
    (`<thead>` reads `symbol, side, class, distance, score, coverage, tick evidence, basis,
    history`).
  - Label clarity: the header text is the plain lowercase word `history`, styled identically to
    its `coverage`/`tick evidence`/`basis` neighbors (same `HEADER_CELL_LEFT` class); the cell
    text is a self-explanatory `history <N> sessions · from <YYYY-MM-DD>` — QA's UT-09 confirms no
    advisory/judgement language ("enough", "reliable", "confidence", etc.) appears anywhere in the
    new copy, and the label matches exactly what the spec and goal.md call it ("history"). No
    label-confusion flag.
  - Visual feedback: none needed — this is inert disclosure (no button, no loading/success/error
    state to signal), consistent with the spec's explicit "no new user actions."
  - Design-system conformance: the column reuses the existing `LABEL_CELL`/`HEADER_CELL_LEFT`
    classes verbatim (confirmed via source grep, `apps/frontend/app/desk/page.tsx:335-368`) — zero
    new tokens, zero new visual chrome, consistent with the dense, dark, terminal-grade style
    every prior `/desk` column (band/basis/coverage/tick-evidence) already uses. The tooltip
    addition reuses the single existing `deskRowDrillInTitle` builder rather than introducing a
    second tooltip mechanism, per the spec's own instruction.
  - Legacy-row honesty: pre-iteration screen snapshots render `"history not recorded in this
    snapshot"` rather than blank or the literal string `null` — verified live by QA's UT-04
    (all 63 rows of the `screen-2026-07-29-ce0d82b8e9bf` legacy snapshot render the identical
    fallback string; the "Latest" button correctly restores real values).
  - Short/long split legible together: QA's UT-02 confirms a `history_sessions <= 60` row (HONA,
    27 sessions) and a `>= 400` row (BRK-B, 500 sessions) are both visible in one screenshot
    without scrolling — the DoD's TC-8 acceptance is met, not just plausible.

No hidden or undiscoverable capability found. QA's own UI Evolution Audit block
(`reports/qa/goal-desk-iter-15-qa.md`) independently reaches the same conclusion — Reachability
PASS (1 click from main nav), Visibility PASS, Control PASS (disclosure-only, no control expected),
Generic-page-dumping PASS (lands on `/desk`, the designated surface) — cited here, not re-derived.

Note: `runs/goal-session-desk/iter-15/coherence.md` does not exist yet at review time (only
`decomposer.done` is present in `.steps/`; the coherence-auditor step for this iteration runs
later in the pipeline than this review). No audit-contradiction check was possible against it —
this review relies on qa's live-browser UI Evolution Audit block instead, per this agent's Step 1
instructions on which artifact to cite when both are unavailable.

## Regression Risk

| Shared component touched | Prior feature(s) it serves | Risk assessed | Evidence |
|---|---|---|---|
| `desk_screen.py`'s ascending `merged_bars` walk (renamed `_resolve_reference_close` → `_resolve_reference_close_and_history`, now returns a 3-tuple) | J-08 basis-disclosure (`basis_as_of`/`basis_age_days`), and indirectly every ranked row J-04/J-05 render | Low | Single call site confirmed via `grep -n "_resolve_reference_close" apps/backend/app/research/desk_screen.py` — only `compute_screen`'s one call at line 370 unpacks the new tuple; no other module references the old name. Backend suite 1418 passed/0 failed including 49 `test_desk_screen.py` cases. QA's UT-J-08 regression replay (basis-disclosure journey) passed end-to-end. |
| `deskRowDrillInTitle` composite tooltip builder | J-08 (basis line), J-05 (drill-in click-through to `/structure`) | Low | Addition is a new `historyLine` appended to the existing string (`page.tsx:243-247`); QA's UT-03 confirms the tooltip's existing distance/score/basis order is unchanged with `history` appended last, and confirms the click still navigates to `/structure?symbol=...&asof=...` with zero click-geometry change. UT-J-05 regression replay (ledger drill-in) passed. |
| `/desk` ranked table (`DeskRowsTable`/`DeskRow`) | J-04 (`/desk` page itself), J-08 (basis column) | Low | Purely additive `<th>`/`<td>` pair; QA's UT-06 confirms distance/score/coverage/tick-evidence/basis values are byte-identical before and after a full reload, and the table shows exactly one new column beyond J-08/J-10's documented shape. |
| Shared page layout (Top-up Runs / Index Reconciliation sections, below the ranked table) | J-09 (top-up runs), J-10 (index reconciliation) | Low | Spec explicitly scoped this as content-untouched, only a possible vertical shift from a wider table. QA's UT-08 confirms both sections render unchanged content, and UT-07 confirms Run Screen / Screen History click-throughs still work post-change. |

All eight required-still-passing journeys (J-03, J-04, J-05, J-06, J-07, J-08, J-09, J-10) were
independently replayed and passed, both via deterministic golden replay
(`reports/phase-goal-desk-iter-15-regression-replay-results.md`, 7/7) and the merged
browser-qa/replay results (`reports/phase-goal-desk-iter-15-ui-test-results.md`, 17/18 passed, 1
skipped — UT-10 backend-unavailable, an error-path smoke test unrelated to this iteration's
change, explicitly marked SKIP not FAIL). No regression found in any prior-phase journey.

## UI vs Backend Parity

| Backend capability | UI exposure |
|---|---|
| `history_sessions` (int >= 0) on ranked screen rows | `/desk` ranked table `history` column (`history <N> sessions · from <date>`) + composite tooltip full-precision line |
| `history_start` (ISO date-time or absent) on ranked screen rows | Same column (date-only, sliced) + same tooltip (full ISO timestamp) |
| Legacy-row key-absence (no backfill) | Honest fallback text `"history not recorded in this snapshot"`, never blank/`null` |
| Skip-row exclusion (`no_bars`/`no_basis` never carry the fields) | Skip tables (`DeskSkipTable`) structurally never had a history column and still don't — confirmed by QA's UT-05 |

`ui-impact-analyst`'s own parity read (`reports/phase-goal-desk-iter-15-user-visible-changes.md`,
"Not Visible Yet" section) states "None... there is no backend capability here without a
corresponding UI surface" — independently confirmed above. No backend-only gap exists this
iteration; `GET /research/desk/screen` is the sole serving endpoint (unchanged), and the new fields
ride through automatically per the byte-identical GET-proxy contract (also covered by MCP
`desk_screen` — no new tool, count stays 17).

## Flags

### Hidden Capabilities
None.

### Undiscoverable Capabilities
None.

### Potential Regressions
None. All eight required-still-passing journeys replayed green; the two shared components this
iteration touches (`_resolve_reference_close_and_history`'s walk, `deskRowDrillInTitle`) were
extended additively with a single call site each, confirmed by source grep and by targeted
regression replays (UT-J-08, UT-J-05) plus the general UT-06/UT-07/UT-08 before/after checks.

### Visual Consistency
- New `history` column and its tooltip line reuse existing design tokens (`LABEL_CELL`,
  `HEADER_CELL_LEFT`) verbatim — no arbitrary values introduced, no new chrome/glow/animation.
  Consistent with the established dense, dark, terminal-grade `/desk` style used by every prior
  column (band/basis/coverage/tick-evidence) and by the J-09/J-10 sections below it.

## Recommendation

No action required. The reviewer's one MINOR note (an optional MCP `desk_screen` proxy
pass-through test inside `test_desk_screen.py`, already covered by `test_mcp_server.py`'s
generic byte-identical-JSON tests) is a test-organization nit with no UX or product-surface
consequence — not a discoverability or regression gap.

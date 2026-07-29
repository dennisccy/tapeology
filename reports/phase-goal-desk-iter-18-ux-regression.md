# Phase goal-desk-iter-18 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-PASS

## New Capability Discoverability

**Capability:** the `opposite` column on `/desk`'s ranked-rows table (nearest wall on the side of
price the row's own displayed band did NOT select) plus a `bands_by_class` line appended to the
row's existing composite hover tooltip.

- **Navigation path:** top-level **Desk** nav tab (1 click from home) → the ranked table renders
  immediately with `opposite` as the 11th/last header cell. Confirmed via
  `document.querySelectorAll('th')` returning exactly `symbol, side, class, distance, score,
  coverage, tick evidence, basis, history, band, opposite`
  (`reports/phase-goal-desk-iter-18-ui-test-results.md` UT-01).
- **qa's UI Evolution Audit** (`reports/qa/goal-desk-iter-18-qa.md`, Step 5) — cited, not
  re-derived: Reachability PASS (1 click), Visibility PASS, Control PASS (spec declares zero new
  user actions, none built), No-generic-page-dumping PASS. Overall **UI-PASS**. No
  `runs/goal-session-desk/iter-18/coherence.md` exists yet (only `decomposer.done` has landed in
  `.steps/` as of this review), so there is no coherence-auditor finding to cross-check against
  qa's audit this iteration — no contradiction to flag.
- **Visibility, live-verified on real data (not merely inferred):** `reports/qa/goal-desk-iter-18-
  evidence/UT-03-result.png` (fixture-scoped rig, real Yahoo-fetched symbols) shows six rows'
  `opposite` cells simultaneously legible, including `CMCSA`/`CRM` at 0.00 bps (near) and `AAPL` at
  1208.73 bps (far) — the exact near/far pairing goal.md's own rationale names. `UT-06-result.png`
  independently confirms the `class: null` opposite band renders the literal word `unclassified`,
  never blank or `"null"`. `UT-02-result.png` (ambient `:3301`, live production data) confirms
  every one of 63 currently-recorded rows shows the honest `"opposite wall not recorded in this
  snapshot"` fallback — I independently viewed both screenshots and they match the reported text
  exactly. All three of the plan's required states (populated-near, populated-far/null-class,
  legacy-absent) are independently browser-QA'd on real pages, not source-code reads.
- **One discoverability caveat (informational, not a regression):** `UT-09` reports the `opposite`
  header is reached "after the same horizontal scroll every column past `coverage` already
  required (pre-existing behavior)." This is worth naming explicitly for the record: this
  iteration is the third consecutive one (after J-11's `history` and J-13's `band`) to append a
  column to the same `DeskRowsTable` rather than reflowing, so the table keeps growing wider and an
  increasing share of the disclosure surface sits past the fold. Per this agent's mandate,
  horizontal scroll (not a click) does not violate the 2-click reachability bar, and UT-09 rates it
  PASS with live evidence; I am not downgrading the verdict for it, but flag it as a trend worth a
  future iteration's attention if a 12th column is ever proposed.
- **Label clarity:** header reads `opposite`; cell reads `opposite <side> <class> <low>–<high> ·
  <n> bps`, matching the `basis`/`history`/`band` column convention exactly (header = one word,
  cell = self-labeled sentence). Consistent with established precedent, not a new inconsistency.
- **Feedback:** none required — read-only disclosure, matches the spec's own "New user actions:
  none," confirmed by qa's Control check.
- **Demo-narrator artifact does not actually narrate the capability (showcase-artifact gap, not a
  product defect — flagged for visibility per the iter-17 precedent of deferring this class of
  finding to the phase-closure-auditor).** I directly viewed all 6 captured frames in
  `reports/demo/goal-desk-iter-18/`: steps 02, 03, 04, and 05 — titled "Scroll the ranked table to
  see the new 'opposite' column," "Examine the top-ranked row (BRK-B)," "Hover over a row to see
  the new tooltip line," and "Scroll through the table to see multiple rows" — all four actually
  show the **`/structure` page** (an IBM symbol-autocomplete dropdown open over a candlestick
  chart), not `/desk` at all. Only steps 01 and 07 show `/desk`, and in both of those the visible
  table is cropped at the `band` column — the `opposite` column is off-screen (consistent with the
  horizontal-scroll finding above) and never appears in any of the 6 frames. The gallery never
  shows a populated row, a near/far pair, or the `bands_by_class` tooltip line — none of what
  `Demo Verdict: RECORDED` + DEFINITION OF DONE required. The verdict itself is
  `RECORDED_WITH_NOTES` (four soft-note timeouts on steps 3-6), not the plain `RECORDED` TC-16 asks
  for, and it ran against the ambient `:3301` store, not a fixture-scoped rig with a freshly
  computed screen. This is a strictly worse outcome than iter-17's analogous gap (which at least
  stayed on `/desk` and showed the correct, if legacy-fallback, page throughout) — it looks like a
  broken click target in the demo script that silently navigated away rather than a timeout that
  was honestly logged. The actual capability is independently and rigorously proven reachable/
  correct by browser-qa's UT-01 through UT-10 (real browser, origin-verified, scoped-rig evidence),
  so this does not change the discoverability verdict — but the DoD's own demo-narrator requirement
  is not, in substance, met by this artifact, and downstream lanes (phase-closure-auditor,
  release-manager) should not treat `reports/demo/goal-desk-iter-18/` as evidence that a human
  operator can see the opposite-wall disclosure end to end.

## Regression Risk

| Shared component | Prior feature(s) served | Current change | Risk | Evidence |
|---|---|---|---|---|
| `DeskRowsTable` header row | J-04 (ranked table), J-08 (basis), J-11 (history), J-13 (band) | Appended one `<th>opposite</th>` after `band` | Low | UT-01 confirms exact 11-cell header order, all prior headers unmoved |
| `DeskRow` ranked-row cell | J-04, J-08, J-09/J-10 (coverage/tick-evidence), J-11, J-13 | Appended one `<td data-testid="desk-row-opposite">` after the `band` cell | Low | UT-07 re-verified `BRK-B`/`CRM`'s side/class/distance/score/basis/history/band cell text byte-identical to pre-change values |
| `deskRowDrillInTitle` composite tooltip | J-08 (`basisLine`), J-11 (`historyLine`), J-13 (`bandLine`) | Appended `bandsByClassLine` after the existing segments | Low | UT-04 confirms the composite `title` string's exact segment order and position; per-cell `title` on the new `opposite` `<td>` is `null` (F2 lesson honored, no new pointer-unreachable tooltip introduced) |
| Row drill-in navigation (`tr` click → `/structure`) | J-05 | Untouched | Low | UT-08 confirms `BRK-B` still navigates to `/structure?symbol=BRK-B&asof=...` |
| Screen History row click (in-place swap) | J-12 | Untouched | Low | UT-08 confirms clicking a Screen History row still swaps in place, sets `data-selected` on exactly one row, re-renders the same (now 11-column) table |
| Skip table | J-02/J-09/J-10 | Untouched — intentionally no `opposite` column | Low | UT-07 confirms skip table header stays exactly `symbol, reason, coverage, tick evidence` (4 columns), no bleed |
| MCP `desk_screen`/`get_endpoint` proxy, 17-tool contract | J-06 | Zero MCP code change; two fields ride the existing proxy | Low | UT-J-06 confirms 17 tools, byte-identical `desk_screen`/`desk_universe`/`get_endpoint` output vs. direct `curl`, `test_mcp_server.py` 38/38 passed |
| Regression journeys J-01–J-13 | all prior desk journeys | N/A — replayed end-to-end | Low | All 23/23 PASS in `reports/phase-goal-desk-iter-18-ui-test-results.md`; backend suite grew 1435→1448 passed, 0 regressed, skip count unchanged (8→8) |

No high- or medium-risk shared component was found. Every prior-iteration behavior that touches the
same table/tooltip components this iteration modified has a direct, passing regression check backed
by this iteration's own live evidence, not an assumption. The reviewer report
(`reports/reviews/goal-desk-iter-18-review.md`) independently confirms zero diff on
`tradability.py`/`levels.py`/`bars.py`/`bar_index.py`/`StructureChart.tsx`/`desk_coverage.py`/
`config.py`.

## UI vs Backend Parity

| Backend capability | UI surface | Status |
|---|---|---|
| `opposite_band` field (`side`, `band_class`, `price_low`, `price_high`, `distance_bps`) on every ranked row | `opposite` column cell on `/desk` | Fully surfaced, same iteration |
| `opposite_band.band_score` | Not rendered anywhere | **Intentional gap, not a UX defect** — the frontend handoff documents this explicitly: goal.md's own worked example for the cell (`opposite resistance A 490.88–494.22 · 0.6 bps`) omits `band_score`, matching the convention that no other cell in this table surfaces the *selected* band's own score outside the dedicated `score` column. Typed on `row.opposite_band.band_score` for a future consumer; correctly out of this iteration's scope, not a hidden capability. |
| `bands_by_class` (A/B/C/unclassified counts) | Composite hover tooltip line only, no table cell | Fully surfaced per spec — plan.md explicitly scoped this to the tooltip only, not a new column |
| Legacy-row absence contract (keys entirely absent, never `null`) | Honest `"opposite wall not recorded in this snapshot"` / `"bands by class not recorded in this snapshot"` fallbacks | Fully surfaced, same iteration, verified on all 63 live rows (UT-02) |
| MCP `desk_screen` tool / `get_endpoint` proxy of both new fields | N/A (MCP/agent-facing, not a browser surface) | No gap — correctly documented as such in `user-visible-changes.md` |

Per `reports/phase-goal-desk-iter-18-user-visible-changes.md`'s "Not Visible Yet" section, the only
named gap is the `band_score` non-rendering above, which is a deliberate, spec-matching scope
decision, not an oversight. No backend capability from this iteration is silently unexposed.

## Flags

### Hidden Capabilities
None. Both new fields (`opposite_band`, `bands_by_class`) are rendered on the one already-registered
`/desk` canonical home, in the same iteration that added them to the Data Contract.

### Undiscoverable Capabilities
None that block product use. The `opposite` column requires the same horizontal scroll every column
past `coverage` already required (pre-existing table-growth pattern, not new to this iteration) —
noted as a trend above, not a defect.

### Potential Regressions
None found. See Regression Risk table — every shared component carries a passing, evidence-backed
regression check from this iteration's own QA run.

### Visual Consistency
- The new `opposite` column and tooltip line reuse existing cell classes (`LABEL_CELL`) and the
  existing `fmt()` rounding helper verbatim (per both handoffs) — zero new tokens, zero arbitrary
  values, zero new visual effect.
- Rendered style (dark background, monospace-leaning numeric alignment, teal coverage badges,
  terminal-grade density) matches the rest of `/desk` and the sibling `Cockpit`/`Structure` pages in
  the same nav bar, confirmed by direct visual inspection of `UT-02-result.png`, `UT-03-result.png`,
  and the demo gallery's `/desk` frames (steps 01/07).
- No deviation from the DESIGN SYSTEM found.
- **Demo-narrator gallery artifact defect** (see New Capability Discoverability above): 4 of 6
  captured frames show the wrong page (`/structure` instead of `/desk`) with no soft note logged for
  the navigation itself (soft notes only cover the subsequent failed clicks). This is an evidentiary/
  showcase-artifact quality issue, not a product visual-consistency issue — flagged for the
  phase-closure-auditor's artifact-consistency gate, consistent with how the iter-17 UX regression
  review handled an analogous (milder) gap.

## Recommendation

No action required to ship this iteration's product code — the actual `/desk` capability is
discoverable, correctly rendered in all three required states, and regression-free per rigorous,
origin-verified live-browser evidence (UT-01 through UT-10, UT-J-06). Two non-blocking follow-ups
worth carrying forward:

1. **Re-record (or root-cause) the `[NEW]`-flagged J-14 demo-narrator walkthrough.** The current
   gallery (`reports/demo/goal-desk-iter-18/`) shows the wrong page for 4 of its 6 steps and never
   shows the `opposite` column or a populated row anywhere — it does not, in substance, satisfy
   TC-16/DEFINITION OF DONE's "narrated over POPULATED ranked rows" requirement, nor does it close
   iter-17's carried J-13 `evidence_makeup` gap as goal.md's own text hoped it might. Since a scoped
   rig with real populated data already exists in this iteration's own browser-qa evidence
   (`UT-03`/`UT-05`/`UT-06`), a re-record against that same style of rig (mirroring the J-13
   precedent's script-pinning approach noted in `reports/phase-goal-desk-iter-18-ui-test-results.llm.md`)
   would close this cleanly.
2. If a future iteration proposes a 12th `/desk` ranked-table column, consider whether continuing to
   append columns (vs. reflowing, prioritizing, or paginating the disclosure surface) is still the
   right shape — purely observational, not a blocker for this iteration.

# goal-clean_slate-iter-5 Execution Plan

Session: `clean_slate` ("The Clean Slate" demolition interlude, era 5D). This is the interlude's
**last Must-have journey, J-05** — "the kept product stands: regression sentinel." J-01–J-04 are all
already `passing` (last verified iter-4, `journey-history.json`); nothing about their own code is
re-implemented here, only re-verified. Depth: `full` (decomposer's own choice, per goal.md's picking-
depth triggers — veto-class chart verification + backend/frontend cross-cutting + audit/coherence
diff-vs-inventory closure).

## What to Build
- Restore Case Studies visibility on `/structure`: flip `SHOW_CASE_STUDIES` `false`→`true`
  (`apps/frontend/app/structure/page.tsx:335`) — the ONE literal capability change this iteration.
  State/handlers/data-fetch have been live since era 5B/5C; only the render gate flips.
- Reinstate the one sentence commit `e60f6a7` dropped from the `data-testid="structure-framing"`
  paragraph (~line 2032-2039): insert "Case Studies lists every band-touch event with its reaction,
  forward returns, and — once recorded — its tape timeline; " immediately before the existing "Edge
  Report compares v1, structure_tape, and structure_tape_map..." sentence. No other text changes.
- Clean frontend rebuild (`rm -rf apps/frontend/.next`, rebuild, restart both processes) before any
  browser verification — T-9 discipline; a stale build bakes the wrong API base / ghost pages (this
  exact gotcha has bitten a prior phase on this project — see Notes).
- Full-suite regression sentinel (zero backend source edits): fresh `pytest` run expecting `0 failed`
  under the current pin `08e471b10130e1e2`; the 8 named guard/chart-guard suites re-run in isolation,
  byte-unmodified vs iter-4; MCP `list_tools()` count/name check; 15-route 404 sweep (I-1); T-12
  import-grep sweep for the 11 deleted modules; nav-row check (`app/meta.py` UI_ROUTES == 2).
- Final I-9 byte-comparison recapture (`kept-route-after.txt`) against iter-4's capture — expect 0 NEW
  diffs (the 2 already-sanctioned J-04 diffs, `pnl_ledger` + `backtests.list`, persist as-is).
- Session-wide diff-vs-inventory cross-check: the cumulative diff from iter-0's baseline through this
  iteration, checked against I-1…I-9 + I-8's test dispositions + J-04's landed pin/baseline updates —
  confirm nothing else was touched; independently re-confirm the 14th, derived-pin site
  (`test_profile_equivalence.py::test_candidate_resolved_fingerprint_is_distinct_from_default`) by
  name (iter-4 found this pin site was missing from goal.md's I-9 enumeration).
- Full browser walk for J-05: sim cockpit settle with both charts (candles, timeframe switch, S/R band
  overlay, live tape moving bars), `/structure` Load of AAPL as-of `2026-06-22T21:00:00Z` (wall band
  renders), Case Studies drill-in (now un-hidden), Edge Report honest current state — screenshot
  evidence for every step (T-13: no screenshot ⇒ `unknown`, never `passing`).

## Agents Required
- backend-data: yes -- zero backend SOURCE changes (no new Config fields, no route/module edits;
  J-01–J-04's own code is re-verified, not re-implemented). Work is entirely verification/evidence:
  fresh full pytest run, isolated guard-suite re-runs, I-9 byte-comparison recapture, MCP tool-count
  check, 404 sweep, T-12 grep sweep, cumulative diff-vs-inventory cross-check.
- frontend-ux: yes -- exactly one product file touched (`apps/frontend/app/structure/page.tsx`): the
  `SHOW_CASE_STUDIES` flip + the one reinstated sentence. Clean `.next` rebuild + restart. Then the
  full browser walk (both charts, Structure Load, Case Studies drill-in, Edge Report state) for
  evidence.

Frontend Present: yes

## Files to Create/Modify
- `apps/frontend/app/structure/page.tsx` -- flip `SHOW_CASE_STUDIES` (line 335, `false`→`true`);
  insert the one dropped sentence into the `structure-framing` paragraph. **The only product file
  touched this iteration.** `StructureChart.tsx` untouched; `PriceChart.tsx` gets zero further edits
  (its thesis-overlay removal already landed in J-02) — both are veto-class if modified (T-8).
- `runs/goal-session-clean_slate/iter-5/kept-route-after.txt` -- new (final I-9 byte-comparison
  capture vs iter-4's).
- `runs/goal-session-clean_slate/iter-5/` -- diff-vs-inventory cross-check artifact (new, evidence for
  TC-15).
- `docs/handoffs/goal-clean_slate-iter-5-dev.md` -- new dev handoff.
- `journey-scripts/J-05.json` -- may be extended/replaced by the ui-test-designer/browser-qa lane
  (NOT the developer) to cover the full walk (timeframe switch + live bars, Case Studies drill-in,
  Edge Report state) instead of today's scoped subset (sim-settle + wall-band load only) — a
  testing-artifact task per the spec's own NOTES, not product scope.
- No backend source file is expected to change. No other frontend file changes.

## UI Evolution
- New user-facing capability: the Case Studies panel on `/structure` becomes visible and clickable
  again — selecting a listed band-touch event opens its drill-in (tape timeline once recorded, honest
  "not recorded" otherwise). The only literal capability change; everything else this iteration is
  re-verification of the already-shipped two-page product.
- New information displayed: the restored Case Studies list/drill-in (event reaction, forward returns,
  tape timeline) — a pre-existing data view (`setups.py` / `GET /research/setups`, already in the Data
  Contract), simply un-hidden. No new field or value.
- New user actions: none new — the row-click-to-drill-in control and its state/handlers already
  existed (era-5B/5C); only the rendering gate changes from off to on.
- UI surface changes: `/structure`'s "Case Studies" `<section>` (previously withheld) renders again at
  its pre-existing position, between Levels & Zones/raw-toggle and the Edge Report section; the
  framing paragraph regains its dropped sentence. No new page, no new section beyond pre-suppression.
- Navigation changes: none. Nav stays exactly Cockpit + Structure (2 rows).

## Visual Requirements
- Component patterns: reuse the EXISTING Case Studies `Panel`/table/`LoadingPanel`/`EmptyState`
  components already built in `page.tsx` (~lines 646-760, ~2334-2410) — no new component, no restyle.
  This is a gate flip, not new UI construction.
- Layout: unchanged — Case Studies reoccupies its pre-existing position in `/structure`'s existing
  section order (Levels & Zones → Case Studies → Edge Report).
- Key visual effects: none new — match the existing dark-only, dense, terminal-grade styling already
  applied to every other `/structure` panel; do not restyle Case Studies while un-hiding it.
- States to handle (already built — re-verify each still renders correctly once un-hidden):
  `case-studies-loading`, `case-studies-unavailable` (error), `case-studies-empty` (true-empty
  registry), `case-studies-no-match` (filtered to nothing), populated table + drill-in (recorded and
  honest "not recorded" sub-states).

## Key Test Scenarios
- TC-1: fresh full backend `pytest` suite under pin `08e471b10130e1e2` reports `0 failed`, exit `0`.
  Baseline: iter-4 closed at 1167 passed / 7 skipped / 0 failed / 0 errors; this iteration adds no
  backend test file, so expect the same count on a clean rerun (literal "0 failed", no modulo).
- TC-2: `test_no_execution_path.py`, `test_no_credential_in_artifacts.py`, both `test_backtests.py`/
  `test_setups.py` guard blocks, and the 3 chart-guard suites each pass in isolation AND are
  byte-unmodified vs iter-4 (outside the already-landed J-04 pin-assertion lines).
- TC-3: levels/bands/setups recomputed on iter-4's fixture input return byte-identical VALUES; only
  the embedded `config_fingerprint` stamp reads the current pin.
- TC-4–TC-8 (browser): nav shows exactly Cockpit+Structure; `SIM-BUYER` watch settles "Buyer Control"
  with PriceChart candles; timeframe switch re-renders at a new bar width; live ticks move the
  rightmost bar with any band overlay staying anchored; Stop shows "No ticker watched".
- TC-9: `/structure` Load of AAPL as-of `2026-06-22T21:00:00Z` renders candles + the ~300–302.4 wall
  band overlay (golden's `300.11` substring check).
- TC-10: with `SHOW_CASE_STUDIES=true`, clicking a Case Studies row opens a drill-in (tape timeline or
  honest "not recorded") — screenshot required (T-13).
- TC-11: Edge Report panel shows either populated cells or the exact text "Edge report not computed
  yet." + a visible Compute button — never blank.
- TC-12: all 15 I-1 deleted routes return exactly HTTP 404 (not 200, not a redirect).
- TC-13: MCP `list_tools()` returns exactly the 15 I-6 tool names.
- TC-14: repo-wide grep (`apps/` only) for imports of the 11 deleted modules returns zero hits.
- TC-15: this iteration's git diff touches only `apps/frontend/app/structure/page.tsx` (product) plus
  refreshed golden/test-plan artifacts under `runs/`/`reports/` — zero other `apps/` file changed.
- TC-16: `SHOW_CASE_STUDIES` reads `true`; the framing paragraph includes the reinstated sentence
  verbatim, immediately before "Edge Report compares...".
- TC-17: `docs/goal-archive/`, `runs/goal-session-clean_slate/iter-0` through `iter-4`, and
  pre-iteration-5 `reports/pnl/pnl-history.md` rows show zero bytes changed.

## Notes / Risks
- The `SHOW_CASE_STUDIES` restore-vs-rescope question is already decided and logged (assumptions.md
  `## iter-5 — goal-decomposer`) — not open for re-litigation this iteration.
- Two spec-hygiene items flagged in iter-4's audit (I-9 "13 pin sites" is actually 14; TC-3's
  "48→40" arithmetic was actually "49→41") are historical/closed per this spec's own NOTES — both
  already correctly executed and re-verified across four evaluator passes. Do not treat as open work.
- Known operational gotchas on this exact project (from prior iterations): (1) a stale `apps/frontend/
  .next` build bakes the wrong API base / ghost pages — the mandatory clean rebuild above exists
  specifically to avoid this; (2) Chrome MCP's default port-9222 attach has previously broken
  mid-session on this project — if it recurs, the known fix is self-launching an isolated headless
  Chrome (`--headless=new --remote-debugging-port=9222 --no-sandbox --user-data-dir=<fresh>`) and
  letting the browser tool attach to that endpoint.
- If this iteration's evidence is clean (J-05 passing, J-01–J-04 still passing, zero regression, zero
  anti-goal violation, session-wide diff-vs-inventory cross-check clean), all 5 Must-have journeys of
  this interlude become `passing`. Whether that constitutes `GOAL_ACHIEVED` is the evaluator's
  determination alone (deterministic gates + two-key confirm) — not presumed by this plan.
- No scope drift detected: this phase spec is goal.md's own J-05 journey verbatim: it introduces no
  feature, route, endpoint, or Config field beyond the one UI-gate flip goal.md itself calls for, and
  every Anti-goal / frozen-foundation rail is respected in-scope.

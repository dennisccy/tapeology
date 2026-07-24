# goal-clean_slate-iter-2 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

J-02's demolition goal is fully achieved and independently verified in code, tests, and browser
evidence: the WS `thesis`/`hint` merge and its four dead `ResearchRegistry` stubs are gone, the nav
route list is byte-exactly two rows, the three pages + eleven components + fourteen `api.ts`
functions + ~30 `types.ts` families are deleted with zero orphaned live references, and both charts +
the provenance badge render exactly as shipped (the veto-class `StructureChart.tsx` diff is empty;
`PriceChart.tsx`'s only edit is the thesis-geometry overlay removal with the marker seam preserved).
The full backend suite is 1162 passed / 1 failed (the pre-authorized MCP case) / 7 skipped, the
fingerprint still prints `4d665603569b9dbf`, and no historical record was touched. The only items to
document are (a) one honest T-14 inventory-gap correction the dev made outside the spec's literal
"only `test_meta_routes.py` is edited" wording — deleting a test whose subject (the `/performance`
page) this journey itself deletes, and (b) a minor inaccuracy in the dev handoff's TC-11 claim that
the reviewer already flagged. Neither compromises the goal; both are correctly handled.

---

## 2. Findings

### Backend Findings

**B1 — GAP (documented): a second backend test file was edited, outside the spec's literal TC-17/DoD wording.**
The spec DoD says "`test_meta_routes.py` updated … no other backend test file is added or removed"
and TC-17 says "only `test_meta_routes.py`'s existing assertions are edited … collected-test count
unchanged from iter-1." The dev also edited `apps/backend/tests/test_profile_equivalence.py`:322-324
(diff confirmed) — deleting `test_performance_page_offers_no_profile_selection_control` and updating
one docstring line. I verified this was necessary, not scope creep: that test does
`(.../frontend/app/performance/page.tsx).read_text()`, and `/performance/page.tsx` is deleted by this
very journey (git status shows it `D`), so the test would raise `FileNotFoundError` — a *second*
unauthorized failure the DoD forbids. The spec author simply failed to catalog this test in the I-8
inventory. The fix is minimal and honest (one function + one docstring line; the file's other ~14
tests are byte-untouched and pass, and its fingerprint pin is intact at
`test_profile_equivalence.py:121` = `4d665603569b9dbf`). Consequence: collected count is 1170, not
iter-1's 1173 (−3 = 2 spec-sanctioned `test_meta_routes.py` deletions + this 1). Note the spec is
internally contradictory here — it *mandates* the 2 `test_meta_routes.py` deletions, which by itself
breaks TC-17's "count unchanged." No fix applied: deleting the test was the correct, minimal, honest
call; re-adding a test would be wrong, and adapting it to `assert not exists` would duplicate TC-3's
404 coverage. Documented as a spec-inventory imperfection, correctly handled.

**B2 — OBSERVATION: historical docstring still names the deleted registry methods.**
`apps/backend/app/research/routes.py:226` mentions
`_monitors`/`monitor_for`/`projection_for`/`_surviving_projection`/`hint_projection_for` — but this
is prose in the class docstring explaining *why they were removed*, not a live call (grep for live
references returns only this line). Correct and intentional. No action.

### Frontend Findings

**F1 — OBSERVATION: dev handoff's TC-11 "zero hits" claim is inaccurate (reviewer already flagged, MINOR).**
The literal TC-11 grep returns one tracked-source hit: `apps/frontend/app/structure/page.tsx:1305`,
a code comment (`// … NOT a reuse of `StudyResultsView`'s `results-cancelled` copy`). The dev
handoff claims "zero hits" and its Known Issues #2 characterizes the comment as only the bare word
"Study" when the compound identifier `StudyResultsView` is literally on that line. This is
comment-only, in an out-of-scope UNTOUCHED file (`git diff` on `structure/page.tsx` is empty), and
the phase spec's own NOTES section explicitly pre-cleared this exact line as "prose inside a code
COMMENT … Not a T-12 blocker." The substantive orphan cleanup is complete (git-tracked grep over all
other files is clean; `fetchTaxonomy` survives in both `lib/api.ts:403` and `FeedBasisBadge.tsx`). No
fix applied: `structure/page.tsx` is a high-stakes KEPT page this journey has no mandate to touch, and
the spec pre-cleared the line. Documented only.

**F2 — OBSERVATION (carried forward): PriceChart timeframe "selected" highlight.**
The frontend handoff notes the Tape 10s/30s/60s button highlight did not visibly update in one manual
screenshot even though the view state changed (caption + candle width updated correctly). I confirmed
the `PriceChart.tsx` diff touches ONLY the thesis-geometry overlay — `segmentClass`/view-selection
logic is byte-unchanged — so this is pre-existing, not a regression introduced here, and T-8 forbids
further edits to this file this era. Carried forward for whoever next opens `PriceChart.tsx`.

**F3 — OBSERVATION: stray untracked build-output dir inside the repo.**
`apps/frontend/home/dennis-chan/.cache/iad/iad.goal-fast_wall-iter-4…/` contains compiled JS that
matches the orphan grep. It is untracked (`git ls-files` empty) and dates from a prior session
(fast_wall era), not this iteration — not part of the deliverable. Worth a housekeeping cleanup
someday; out of scope here.

### Test Findings

**T1 — (verified, no defect): full suite has exactly one failure, the pre-authorized MCP case.**
I re-ran `.venv/bin/python -m pytest tests/ -q` myself: `1 failed, 1162 passed, 7 skipped in
119.61s`, and the single FAILED is
`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest` — J-03's to close, with
`test_mcp_server.py`'s `git diff` empty. Chart guard suites + `test_meta_routes.py` +
`test_profile_equivalence.py` + `test_copy_discipline.py` re-run green (exit 0). Assertions are tight
(TC-2 payload is an exact `==` on the 2-row dict; the wall-band table is exact values). No test passes
by accident.

---

## 3. Domain Assessment

This is a subtractive interlude iteration; the "domain logic" under audit is the *discipline of
deletion*, and it is clean. Every claim in the two handoffs was traced to code, not trusted:

- **WS transport (I-5):** `app/main.py` now sends `serialize_stream(engine.snapshot())` verbatim;
  both `_thesis_projection`/`_hint_projection` helpers are gone and have no dangling callers; `import
  app.main` succeeds; the captured live frame (`tc09-ws-frame-no-thesis-hint.json`) has 17 engine
  keys and no `thesis`/`hint`. `get_registry_or_none` is correctly retained (still called at
  `main.py:154,176`) — deleting its two former helper callers did not orphan it.
- **Single source of truth / no-recompute:** the nav shrinks purely from `app/meta.py`'s `UI_ROUTES`
  trim via `GET /meta/ui-routes` (byte-exact 2-row payload verified via TestClient); `NavBar.tsx`/
  `TopBar.tsx` diffs are empty. `/structure` renders the pinned example (resistance 300.11–302.2,
  Class A, score 171, 849 members, round number) read verbatim — the same wall as before.
- **Frozen foundations / no research-value change:** `config.py` diff empty, `config_fingerprint()`
  = `4d665603569b9dbf`, all 13 pin sites present; the I-9 kept-route re-capture matches iter-1 except
  the sanctioned `meta.ui-routes` shrink (the backtests/pnl_ledger delta is a launch-cwd artifact —
  the read-path modules have empty diffs, consistent with the dev's root-cause).
- **Deletion complete, never cosmetic:** 14 files deleted; `api.ts`/`types.ts` are pure deletions
  (no net-new exports); `page.tsx`/`Cockpit.tsx` remove state, handlers, props, and JSX (not just
  render calls); the `onHintDeclare` orphan-prop trap the plan warned about is handled.
- **Chart rails:** `StructureChart.tsx` diff empty (veto-class held); `PriceChart.tsx`'s sole edit is
  the thesis-geometry removal with the `extraMarkers`/`extraPriceLines` seam preserved via the
  stable `NO_PRICE_LINES` constant; the three chart guard suites are byte-unmodified and pass.
- **Never touch a historical record:** journal.db and `docs/goal-archive/`/`*-delivered.md` untouched;
  only append-only `telemetry.jsonl`/`trace.jsonl` housekeeping changed.

Browser evidence is genuine and shows the acceptance state (not just page loads): honest styled 404
on the deleted routes, exactly two nav links, `SIM-BUYER` at Buyer Control (conf 0.937) with no
thesis strip / hint dock / sound toggle and the "feed Simulated" provenance badge, and the structure
wall band intact.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found. The single GAP (B1) was already the correct, minimal,
honestly-surfaced handling of a spec-inventory miss; the OBSERVATIONS (F1–F3, B2) are either
out-of-scope files the iteration must not touch or pre-existing/pre-cleared items — fixing any of them
would be scope creep.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (deliverable verified correct as-is) |

---

## 5. Recommended Next Step

**Proceed to J-03 (MCP tool removal).** J-02 is complete and the two-page product is exactly as
goal.md's Vision names it. The next journey in the J-01→J-05 dependency order is J-03, which closes
the one pre-authorized red test (`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`)
by deleting the `journal`/`analytics`/`studies` MCP tools that still proxy to now-404 routes.

Carry-forward reminders for later journeys (unchanged from iter-1, re-confirmed still open):
- `SHOW_CASE_STUDIES = false` (`apps/frontend/app/structure/page.tsx:335`) remains unresolved — a
  J-05 planning decision (restore the flag vs. operator rescopes the "Case Study drill-in" clause).
- The stale `StudyResultsView` mention in `structure/page.tsx:1305` (F1) can be scrubbed for literal
  TC-11 cleanliness whenever that file is next legitimately opened — not before.
- Housekeeping: the untracked `apps/frontend/home/…fast_wall-iter-4…` build-output dir (F3) can be
  removed from the working tree.

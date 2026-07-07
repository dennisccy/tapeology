# goal-structure_ui-iter-1 Audit Report

**Date:** 2026-07-07
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The `/structure` page (J-01) achieves its goal: a data-driven nav entry, a byte-accurate populated
state (chart + A/B/C zones read verbatim from `GET /research/levels`), and honest empty/degraded
states — with zero client-side recompute and a strictly additive one-line backend edit. **One of the
five DoD-required acceptance states was genuinely broken** (the levels-but-no-zones state rendered a
silent blank chart box — the exact "silent failure" the phase's *critical* honest-UI-states anti-goal
forbids); the browser-QA and UX-regression lanes both correctly returned FAIL on it. **I fixed it
surgically and verified the fix end-to-end in the live app** (before/after screenshots below). A
documented, out-of-scope latent gap remains in the pre-existing `PriceChart.tsx` (same z-index
pattern), and the coherence-auditor lane is still downstream — hence PASS_WITH_GAPS rather than PASS.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (no change needed): backend edit is correctly additive and single-source.**
`apps/backend/app/meta.py:30` adds exactly `{"path": "/structure", "label": "Structure", "nav": True}`
to the `UI_ROUTES` tuple (`meta.py:24-31`); the endpoint serves it verbatim (`meta.py:35-37`).
`git diff --stat` confirms the ONLY `apps/backend` edits are `meta.py` (+1) and `test_meta_routes.py`
— zero touch to `config.py`, `research/levels.py`, `research/bars.py`, `research/backtests.py`,
`research/strategies.py`, or the engine. `config_fingerprint` stays `4d665603569b9dbf` (the entry
lives outside the hashed `Config` dataclass; asserted green in `test_profile_equivalence.py` /
`test_levels.py`). The `test_meta_routes.py` assertions are tight (exact 6-entry dict equality at
`:24-33`, exact top-bar list + `len==6` at `:65-77`, dedicated `/structure` precedent test at
`:55-62`). No defect. Full suite verified in QA: 1146 passed, 1 skipped. My fix is frontend-only, so
these backend results stand unaffected.

### Frontend Findings

**F1 — CRITICAL (fixed): the levels-but-no-zones honest state rendered a silent blank chart box.**
File: `apps/frontend/components/StructureChart.tsx:99`. When `levels` is non-empty but the chosen
representative bar series has zero candles at/before the queried `as_of` (`bars.length === 0`), the
`!hasBars` fallback overlay (`StructureChart.tsx:98-102`) was painted *under* the `lightweight-charts`
internal canvases: those canvases carry explicit `z-index:1`/`z-index:2` while the overlay had
`z-index:auto`, so per CSS stacking the opaque `#020617` canvas always occluded the hint. Separately,
with zero candles `fitContent()` is skipped (`StructureChart.tsx:84`) so the price axis has no range
and the `createPriceLine` level lines have no visible position either. Net user-visible effect: an
unexplained blank chart panel with no error and no disclosure — the precise "silent failure" the
phase's *critical* "Honest UI states only" anti-goal exists to prevent, and a break of DoD item (e).
I confirmed this with my own eyes in the committed evidence: `UT-10-no-zones.png` shows the blank box
with caption "Candles: 1h series (0 of 9 recorded bars…)". Root cause independently triple-confirmed
(browser-qa pixel-scan + `getComputedStyle`; ux-regression `getComputedStyle` + code read; my own
CSS-stacking analysis). Both framework lanes returned FAIL on it (`ui-test-results.md` UT-10 FAIL;
`ux-regression.md` UX-REGRESSION-FAIL), yet `status.json` recorded `qa_verdict: PASS` — the audit is
where this was resolved.

*Fix applied* (`StructureChart.tsx:99-100`): raised the overlay to `z-10` (above the canvas's
`z-index:1/2`), so the honest hint now paints on top; and made the (now-visible) copy accurate for its
real trigger — from "No recorded candle series available to draw for this symbol" to **"No candles to
draw at this as-of time."** (a series *is* recorded; there are simply no candles ≤ the `as_of`
instant, which the caption already states accurately). This is the exact fix the ux-regression
reviewer recommended; it converts the silent blank box into an explicit, distinct honest state and
touches only the `!hasBars` branch. *Verified live* — see §4.

**F2 — GAP (not fixed; out of scope; pre-existing): `PriceChart.tsx` shares the identical z-index
occlusion pattern.** File: `apps/frontend/components/PriceChart.tsx:361-370`. The Cockpit's chart
(serving the required-still-passing J-04 journey) wraps its `"Loading price history…"` /
`"No price history for this window yet"` `EmptyHint` in the same `pointer-events-none absolute inset-0`
overlay with no z-index, over the same `lightweight-charts` canvases — so its empty/loading hint is
very likely occluded during the connecting/empty window (untested here; the populated SIM-BUYER flow
UT-14 passed). This is **not a regression introduced by this phase**: `PriceChart.tsx` is byte-unchanged
this iteration (confirmed — it is not in `changed_files`), and touching it would edit a frozen-foundation
J-04 surface outside this iteration's scope (the spec forbids edits to existing surfaces' behavior).
Documented as a known limitation for a future iteration to fix consistently (ideally by mirroring the
`StructureChart` z-index fix, or extracting one shared chart-empty-state wrapper). Left unfixed per
surgical-change discipline.

### Test Findings

**T1 — OBSERVATION: the QA report's PASS was stale and masked the real browser-lane FAIL.**
`reports/qa/goal-structure_ui-iter-1-qa.md` (written 01:54) records **Verdict: PASS** while marking
7 of 11 functional cases (TC-04–TC-08, TC-10 — every browser acceptance state) **DEFERRED** with
"backend service is not currently accessible." The browser-qa lane then ran later (evidence PNGs
timestamped 02:13–02:39) and returned **FAIL** on UT-10, and ux-regression returned FAIL — the honest
signal that let me catch and fix the defect. But `status.json` carries `qa_verdict: PASS`, so a naive
reader of `qa.md` + `status.json` alone would wrongly conclude "all green." The substance is sound (the
browser/ux lanes did their job); the record is misleading. No code defect. Note: the project has no
frontend unit-test runner (confirmed — `package.json` exposes only `dev`/`build`/`start`), so the F1
fix is verified by live browser evidence rather than an automated test — the correct evidence floor
for a visual/CSS defect in this stack.

**T2 — OBSERVATION: coherence-auditor DoD item is downstream and not yet citable.** DoD requires "the
coherence-auditor returns a clean verdict." In goal mode that lane runs after this phase pipeline (at
the goal-evaluator stage); it has not produced an artifact yet, so I cannot cite its verdict. I
verified its invariants directly instead and they hold — see §3.

---

## 3. Domain Assessment

The core value is sound and honest. The page renders the era-4 structure computation **verbatim** with
no second source of truth (trap T10 respected):

- **Populated state is byte-accurate.** I re-drove it live at `PG @ 2026-06-09T21:00:00Z`: 6 zone cards
  with badges `[C,C,C,C,C,B]` and a real candle chart — matching the plan's predicted 5×C+1×B and the
  committed `UT-06-populated-chart.png` / `UT-07` byte-for-byte cross-check. The A/B/C badge reads
  `zone.class` (`page.tsx:148-152`), the score reads `zone.score` (`page.tsx:155-157`), and member
  rows read `lvl.price/timeframe/type` (`page.tsx:178-180`) — all verbatim, `String()`-stringified
  with no reformatting (e.g. `140`, not `140.00`).
- **No client-side recompute.** The only client array ops are *selection/filtering* of already-served
  rows: filter bar series by `symbol` (`page.tsx:230`), `pickRepresentativeSeries` (`page.tsx:232`,
  documented display choice mirroring the backend tie-break), and an `as_of` display filter
  (`page.tsx:241-244`). No grading, aggregation, PnL, or champion resolution — consistent with the
  "recomputes nothing" anti-goal. Types (`types.ts:1001-1028`) mirror the endpoint shapes; `class` is
  the `"A"|"B"|"C"` union read straight from the payload.
- **Honest states are now all genuinely honest.** no-bar-series (UT-08), no-levels (UT-09), degraded /
  malformed-`as_of` 422 folded verbatim (UT-11), backend-unreachable + nav degraded (UT-12) all pass;
  the fourth — levels-but-no-zones (UT-10) — is honest *after* the F1 fix. `fetchLevels`
  (`api.ts:861-883`) folds the 422 into the shared `ok:false` degraded state surfacing the backend
  `detail` verbatim — no fabricated chart on any failure path.
- **Nav is truly data-driven.** `UI_ROUTES` is the single owner; UT-04 proved no hardcoded
  `href="/structure"` outside `NavBar.tsx`'s generic `route.path`.
- **J-04 regression sentinel holds.** UT-13 (four prior pages unchanged) + UT-14 (SIM-BUYER cockpit →
  `buyer_control`) pass; backend suite green; `config_fingerprint` unchanged; champion pointer
  untouched. `PriceChart.tsx` is byte-identical (F2 is latent/pre-existing, not a regression).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Critical | `apps/frontend/components/StructureChart.tsx:99-100` | Added `z-10` to the `!hasBars` overlay so the honest empty-chart hint paints above the `lightweight-charts` canvases (`z-index:1/2`) instead of being occluded; corrected the now-visible copy to "No candles to draw at this as-of time." Converts the levels-but-no-zones state from a silent blank box into an explicit honest state (DoD item e; critical honest-UI anti-goal). |

**Post-fix verification (live, end-to-end):**

1. Started backend `:8301` + frontend `:3301` (fresh `next dev`, no concurrent build), seeded the
   committed PG fixture into `.data/bars/`. API confirmed the exact UT-10 golden state:
   `GET /research/levels?symbol=PG&as_of=2026-06-02T12:00:00Z` → `no_bar_series_for_symbol:false`,
   3 levels `[138.86, 140.28, 141.82]`, `confluence_zones:[]`.
2. Drove the page (PG / `2026-06-02T12:00:00Z` / Load). **After** screenshot
   `reports/qa/goal-structure_ui-iter-1-evidence/AUDIT-UT10-after-fix.png` shows the hint
   **"No candles to draw at this as-of time."** rendered in the chart panel (contrast the **before**,
   `UT-10-no-zones.png`, a blank box). DOM check confirmed `overlayZIndex:"10"`, canvases at `["1","2",…]`,
   and the zones panel still showing its own distinct "No qualifying confluence zone…" message.
   (`elementFromPoint` returns the canvas — expected, since the overlay is intentionally
   `pointer-events-none`; that governs hit-testing, not paint order. The rendered screenshot is the
   ground truth and shows the hint clearly.)
3. Regression re-check: reloaded the populated state (PG / `2026-06-09T21:00:00Z`) → 6 zone cards
   `[C,C,C,C,C,B]`, chart canvas present, and the empty-hint block correctly **absent**
   (`emptyHintPresentInPopulated:false`) — proving the change touches only the `!hasBars` branch.
4. Cleaned up: removed the seeded fixture (`PG` reverts to `no_bar_series_for_symbol:true` — no test
   data left behind), stopped both services (ports free), left the unrelated `trendora` project
   untouched. `.data/bars` is gitignored; `git status` confirms my only source change is the untracked
   `StructureChart.tsx`.

No new finding is introduced by the fix (the change adds no escape hatch, silences no error, and the
new copy is accurate in every trigger case). No dev-handoff claim was invalidated — the fix repairs a
claim ("the chart still renders") that was latently false; the handoffs do not quote the changed
internal hint string.

---

## 5. Recommended Next Step

**Proceed** — the J-01 goal is achieved and the one blocking defect is fixed and verified. Before the
iteration is certified, the downstream **coherence-auditor** and **phase-closure** lanes should run;
based on direct inspection I expect coherence to pass (no second computation/endpoint, verbatim reads,
client-side filtering only). Two carry-forward items for a later iteration (neither blocks J-01):
(1) **F2** — mirror this z-index fix into `PriceChart.tsx` (or a shared chart-empty-state wrapper) so
the Cockpit chart's loading/empty hint is not similarly occluded; (2) reconcile the stale `qa.md`
PASS / `status.json` `qa_verdict` with the authoritative browser-lane result so future readers are not
misled. The natural next feature iteration is **J-02** (strategy registry + champion cards) as a new
section of this same `/structure` page, per the blueprint's J-01→J-02→J-03 order.

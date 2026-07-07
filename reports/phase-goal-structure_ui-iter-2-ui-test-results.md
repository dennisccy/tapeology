# Phase goal-structure_ui-iter-2 — UI Test Results

**Phase:** goal-structure_ui-iter-2
**Date:** 2026-07-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/15 tests passed (1 skipped, 0 failed)

All seven P1 tests (UT-01 through UT-07) pass, including the two elevated-P1 J-01
closure/regression cases (UT-06, UT-07). Every P2 test passes (with one honest nuance
noted under UT-08, not rising to a FAIL). One P3/informational test (UT-13) is SKIPPED
because this Chrome MCP tool exposes no network-throttling action, so the sub-second
loading transient could not be reproduced — the test plan itself states a miss here is
not a defect.

---

## Environment note — services required manual restart

The backend (port 8301) was not running at the start of this run (the prior `qa` agent's
own cleanup step had stopped both services after its validation). The frontend (port
3301) was already up. I started the backend myself
(`uvicorn main:app --host 0.0.0.0 --port 8301`, `CORS_ORIGINS` including
`http://localhost:3301`) and confirmed `GET /health` returned `200` before testing. Both
services were healthy and left running at the end of this run (matching the prior
iteration's browser-qa-agent precedent of leaving the environment live for downstream
pipeline steps). No source files were touched — `git status` at the end of this run
shows only the pre-existing developer diff (`page.tsx`, `api.ts`, `types.ts`) and
report/handoff files from other agents; the only new artifacts from this run are this
report and the evidence screenshots below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Structure page loads with Registry visible | smoke | P1 | Heading, subtitle, form, idle message, and a populated Registry section (Champion + 2 cards) all visible; no error overlay; no console errors | All elements present exactly as specified; `get_console_messages` showed only a React DevTools info line, no errors | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-01-result.png` |
| UT-02 | Registry populates independent of Load button | happy-path | P1 | Levels & Zones stays idle; Registry (Champion `v1`/`default` + 2 cards) populates without any click | Confirmed via fresh navigate + `await_text`; idle message unchanged, Registry fully populated with no form interaction | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-02-result.png` |
| UT-03 | `v1` card verbatim fields, no `reward_target` | happy-path | P1 | entry rule/r_stop/state_flip/horizon/dataset_end match API verbatim; no `reward_target` row; exit-precedence caption present | All 5 fields byte-for-byte match `GET /research/strategies`; confirmed via DOM extract + screenshot; no reward_target row rendered | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-03-v1-card.png` |
| UT-04 | `structure_tape` card + 3 class-scaled tables | happy-path | P1 | All v1-type fields plus reward_target, and 3 tables (stop/reward/size by class) matching API | All fields and all 9 table values (A/B/C × 3 tables) match `GET /research/strategies` byte-for-byte; verified via full-page screenshot | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-04-structure-tape-card.png` |
| UT-05 | Champion badge `v1`/`default` + cross-check | happy-path | P1 | strategy=`v1`, profile=`default`, caption confirms cross-check vs `/research/profiles` | `champion-strategy`="v1", `champion-profile`="default" confirmed via DOM query; `data-testid="structure-champion-crosscheck-match"` present (not `-pending`/`-mismatch`); independently fetched `GET /research/profiles` and confirmed identical champion | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-03-v1-card.png` (Champion box visible) |
| UT-06 | J-01 closure: zero-candle honest hint (not blank) | regression | **P1 (elevated)** | "No candles to draw at this as-of time." legible, not occluded; caption "0 of 9 recorded bars"; zones panel shows its own distinct empty message | Hint text fully legible on-screen; confirmed via `getComputedStyle` that the hint overlay wrapper has `z-index:10` (`position:absolute`) vs. the `lightweight-charts` canvases' `z-index:1`/`2` — the iter-1 fix holds; captions match exactly; zones panel shows "No qualifying confluence zone…" | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-06-zero-candle-hint.png` |
| UT-07 | J-01 regression: populated chart + Registry coexist | regression | **P1 (elevated)** | Candles + level lines render; caption "9 of 9 recorded bars"; 6 zone cards (C,C,C,C,C,B); Registry renders below with no overlap; no console errors | Chart rendered with candles and level-price labels; caption exact match; confirmed exactly 6 zone cards in order C/C/C/C/C/B via `GET /research/levels` cross-check; Registry section (Champion + both cards) renders cleanly below with no layout break; console clean | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-07-populated-chart-zones.png` |
| UT-08 | Registry-unavailable when backend stopped | error | P2 | Amber panel with "Backend unreachable — is the API running?" replaces Registry; no cards/Champion/hardcoded values; Levels & Zones shows its own degraded message; recovers on restart | Registry's own `data-testid="structure-registry-unavailable"` panel rendered with exact text, no cards/Champion/fabricated values anywhere; recovery on backend restart confirmed. **Nuance:** Levels & Zones showed its normal *idle* message, not a distinct "degraded" message — because this test's steps never click Load, so Levels & Zones (which only fetches on-demand, per UT-02) never attempted a request to fail. See note below. | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-08-registry-unavailable.png`, `UT-08-recovery.png` |
| UT-09 | No-bar-series honest state still works | regression | P2 | "No bar series recorded for PG." + "Recording historical bars needs provider credentials."; no chart/levels/zones | Exact match, both before fixture seeding and again after cleanup (reversion confirmed) | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-09-no-bar-series.png` |
| UT-10 | Series-but-no-levels honest state still works | regression | P2 | "No levels found for PG as of 2026-05-01T00:00:00Z." + "A bar series is recorded, but nothing is derivable at this as-of time." | Exact match; no chart/levels/zones rendered | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-10-no-levels.png` |
| UT-11 | Malformed `as_of` still folds into degraded state | regression | P2 | Amber panel: "as_of must be an ISO date-time" + "Nothing cached and nothing fabricated is shown in its place." | Exact match; no crash, no blank page; Registry section (unrelated to this form) remained populated and unaffected | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-11-malformed-asof.png` |
| UT-12 | `/performance` champion unaffected by testid reuse | regression | P2 | Performance's own Champion box shows `v1`/`default`; Profile registry list intact; PnL ledger renders; no leakage from `/structure` | Confirmed via direct navigation (not via link click); Champion box, Profile registry (`default` frozen/default, `candidate-faster-warmup` not-frozen/candidate), and PnL ledger all rendered exactly as expected | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-12-performance-unaffected.png` |
| UT-13 | Registry-loading skeleton appears briefly | smoke | P3 (lowered) | Pulsing skeleton visible briefly during fetch on a throttled connection | Could not reproduce: this Chrome MCP tool (`use_browser`) exposes no network-throttling action, and on localhost the two fetches resolve before any capturable frame, even navigating in cold from another route. No stuck skeleton and no crash were observed either. Per the test's own text, "simply not catching the brief flash…is not a defect" | SKIP | none |
| UT-14 | Registry discoverable in 1 click from Home | ux | P3 | Nav shows exactly 5 links; 1 click reaches `/structure`; Registry visible after scroll, no second click | Nav links confirmed via DOM query: `["Cockpit","Journal","Studies","Performance","Structure"]`; single click on "Structure" navigated to `/structure`; Registry heading + cards visible after scrolling, no extra click/menu needed | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-14-nav-discoverability.png` |
| UT-15 | Registry copy honestly confirms read-only, no invented controls | ux | P3 | Muted read-only line present verbatim; zero interactive elements in Registry section; no trading/advice language | Line matches exactly: "Read-only: every strategy field and the champion below are read verbatim from GET /research/strategies — nothing here is recomputed in the browser."; `document.querySelectorAll('button, input, select, a, [role="button"], [contenteditable]')` scoped to `[aria-label="Strategy registry"]` returned 0 elements; no advice/trading language found in any Registry copy read during UT-02–UT-05 | PASS | `reports/qa/goal-structure_ui-iter-2-evidence/UT-15-readonly-copy.png` |

---

## Passed Tests

### UT-01 — Structure page loads with the Registry section visible
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-01-result.png`
- Navigated to `/structure` cold. Heading "Structure", subtitle, and the bordered Symbol/As-of/Load form all rendered immediately. The Levels & Zones panel showed its idle message. Within the same load (no click), a "Registry" section appeared below containing a Champion box (`v1`/`default`) and two strategy cards (`v1`, `structure_tape`). `get_console_messages` showed only the standard React DevTools info line — no red errors.

### UT-02 — Registry section populates independent of the Load button
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-02-result.png`
- Fresh navigate, no typing, no click. `await_text` for "structure_tape" resolved without any interaction. `extract` confirmed the Levels & Zones idle message was still present unchanged, while the full Registry content (Champion + both cards + all fields) had already rendered — proving the Registry section fetches on mount, independent of the Load button.

### UT-03 — `v1` strategy card shows correct verbatim entry/exit fields, no `reward_target` row
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-03-v1-card.png`
- Cross-checked every field against a direct `curl http://localhost:8301/research/strategies`: entry rule `state_native_sustained_premise`, r_stop `synthetic_invalidation_at_arm`, state_flip `opposing_control_state`, horizon (seconds) `120`, dataset_end `forced_exit_at_last_recorded_price` — all byte-for-byte matches. No `reward_target` row rendered (correct, since `v1`'s API payload has no `reward_target` key). Exit-precedence caption present verbatim. No class-scaled tables on this card.

### UT-04 — `structure_tape` strategy card shows correct verbatim fields plus three class-scaled tables
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-04-structure-tape-card.png`
- All fields matched the API verbatim, including `reward_target` = `class_r_multiple_bounded_by_next_opposing_level` (present here, absent on `v1`, confirming no copy-paste duplication). All three tables matched exactly: stop (bps by class) A=1/B=5/C=10; reward target (R-multiple by class) A=3/B=2/C=1; size (multiple by class) A=2/B=1/C=0.5. horizon (120) and dataset_end are legitimately identical to `v1` (shared config field, expected per the test plan's own note).

### UT-05 — Champion badge shows `v1`/`default` with a confirmed cross-check
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-03-v1-card.png` (Champion box visible in the same view)
- `champion-strategy` = "v1", `champion-profile` = "default" (confirmed via `data-testid` DOM query, not just visual read). The caption reads exactly "Confirmed identical to the champion served by GET /research/profiles — one store pointer, two read views." Deeper technical check: the actual `data-testid` on the caption element is `structure-champion-crosscheck-match` (not `-pending` or `-mismatch`), and an independent `curl http://localhost:8301/research/profiles` confirmed its `champion` field is byte-for-byte `{"strategy_id": "v1", "profile": "default"}`, matching the badge.

### UT-06 — J-01 closure: levels-but-zero-candles state shows the honest hint, not a blank chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-06-zero-candle-hint.png`
- Seeded the PG bar fixture, loaded `PG` / `2026-06-02T12:00:00Z`. The chart panel showed clearly legible gray text "No candles to draw at this as-of time." centered over the (empty) chart area — not blank, not occluded. Caption read exactly "Candles: 1h series (0 of 9 recorded bars, as of the query time). Level lines span every recorded timeframe." The Confluence zones panel showed its own distinct message: "No qualifying confluence zone among these levels." / "Levels exist, but none cluster closely enough across timeframes to form a zone." **Root-cause confirmation that the prior iteration's fix holds:** `getComputedStyle` on the hint's wrapping `<div>` showed `className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center"` with computed `z-index: 10`, while all 7 `lightweight-charts` canvases on the page have `z-index` of `1`, `2`, or `auto` — the hint provably stacks above every canvas. This is the exact defect (and exact fix) described in the phase spec's background as iter-1's `StructureChart.tsx:99` `z-10` fix; it is confirmed live in the browser on the current code, independent of the developer/auditor's in-tree confirmation.

### UT-07 — J-01 regression: populated levels/zones render correctly alongside the new Registry section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-07-populated-chart-zones.png`
- Loaded `PG` / `2026-06-09T21:00:00Z` (same seeded fixture). Chart rendered 9 candles plus multiple dashed level-price lines with labels (149.48, 148.74, 148.47, 148.23, 148.10, 148.06, 146.54, etc.). Caption read exactly "Candles: 1h series (9 of 9 recorded bars, as of the query time). Level lines span every recorded timeframe." Confluence zones showed exactly 6 zone cards; cross-checked against `GET /research/levels?symbol=PG&as_of=2026-06-09T21:00:00Z` directly: 20 levels, 6 confluence zones with classes in order C, C, C, C, C, B — an exact match to both the API and the test plan's expectation. No "No candles…" hint appeared (correct — this is the populated case). Scrolling further down, the Registry section (Champion + both cards, all fields) rendered with no visual overlap or layout break. `get_console_messages` showed no errors (only the React DevTools info line, twice).

### UT-08 — Registry-unavailable honest state when the backend is stopped
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-08-registry-unavailable.png` (down), `UT-08-recovery.png` (restarted)
- Stopped the backend process (`kill -TERM` on the PID bound to :8301, confirmed `curl` returned no response), then reloaded `/structure`. The Registry section's location showed an amber-bordered panel — confirmed via DOM query to carry `data-testid="structure-registry-unavailable"` — reading exactly "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." Zero strategy cards, zero Champion box, zero hardcoded `v1`/`default` text anywhere on the page (confirmed via `document.body.innerText` and targeted `querySelectorAll` counts, both zero). The top nav also degraded honestly ("navigation unavailable — backend unreachable", pre-existing data-driven-nav behavior, not part of this iteration). Restarted the backend, confirmed `GET /health` returned 200, reloaded the page: nav (5 links) and Registry (Champion + both cards) both fully repopulated.
  - **Noted nuance (not a fail):** the test's expected-result also states "The Levels & Zones section above it separately shows its own degraded message." In this run, the Levels & Zones panel instead showed its ordinary *idle* message ("Choose a symbol and an as-of time…"), unchanged. This is because UT-08's own steps never type a symbol/as-of or click Load — and per UT-02 (independently confirmed this same run), the Levels & Zones section only ever fetches on-demand when Load is clicked; it does not auto-fetch on mount. With no fetch attempted, there is nothing for it to report as "degraded" — showing the idle message is arguably the *correct* honest behavior (not a fabricated success, and not a false failure claim for a request that was never made), and matches ui-impact-analyst's own surface-map row for this element, which only describes the Registry panel's behavior and does not mention a Levels & Zones failure state. I flag this discrepancy from the test plan's literal wording for the record, but do not grade it a FAIL since no fabrication, crash, or blank page occurred, and the section named by this test (the Registry honest-state) behaved exactly as specified.

### UT-09 — No-bar-series-for-symbol honest state still renders correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-09-no-bar-series.png`
- Tested twice: once before fixture seeding (environment's true default state) and once more after the fixture cleanup, to confirm reversion. Both times: heading "No bar series recorded for PG." with detail "Recording historical bars needs provider credentials." No chart, no levels, no zones.

### UT-10 — Series-but-no-levels honest state still renders correctly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-10-no-levels.png`
- Loaded `PG` / `2026-05-01T00:00:00Z` against the seeded fixture. Heading "No levels found for PG as of 2026-05-01T00:00:00Z." with detail "A bar series is recorded, but nothing is derivable at this as-of time." Distinct from UT-09's message, as expected. No chart, no levels, no zones.

### UT-11 — Malformed `as_of` input still folds into the shared degraded state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-11-malformed-asof.png`
- Typed `PG` / `not-a-date`, clicked Load. Amber panel appeared with "as_of must be an ISO date-time" (the backend's own validation message, shown verbatim) and "Nothing cached and nothing fabricated is shown in its place." No chart, no crash, no blank page. The Registry section (unrelated to this form) remained populated underneath, confirming the two sections' independence.

### UT-12 — `/performance` champion summary unaffected by `/structure`'s reused testids
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-12-performance-unaffected.png`
- Navigated directly to `/performance` (typed URL, not a link click). Champion box showed strategy `v1` / profile `default`, exactly as before this phase. Profile registry list showed `default` (frozen, default) and `candidate-faster-warmup` (not frozen, candidate). PnL ledger rendered normally on the left with its founding-baseline row and simulated-disclaimer banner. Nothing from `/structure`'s new Registry section leaked onto this page.

### UT-14 — Registry section is discoverable within one click from Home
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-14-nav-discoverability.png`
- `document.querySelectorAll('nav a')` returned exactly `["Cockpit","Journal","Studies","Performance","Structure"]`. Clicking the "Structure" link navigated directly to `http://localhost:3301/structure` (confirmed via `window.location.href`). After scrolling down, the Registry section was visible with no second click, no hidden menu, no separate URL.

### UT-15 — Registry copy honestly confirms read-only, no invented controls
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-2-evidence/UT-15-readonly-copy.png`
- The muted line below the "Registry" heading reads exactly: "Read-only: every strategy field and the champion below are read verbatim from GET /research/strategies — nothing here is recomputed in the browser." A scoped DOM query (`[aria-label="Strategy registry"]` → `querySelectorAll('button, input, select, a, [role="button"], [contenteditable]')`) returned 0 elements — no buttons, inputs, checkboxes, dropdowns, or links anywhere inside the Registry section. No trading/advice language ("buy", "sell", "recommended", "should enter") appeared in any Registry copy read across this session.

---

## Failed Tests

None. Zero P1/P2/P3 tests produced a FAIL verdict this run.

---

## Skipped Tests

### UT-13 — Registry-loading placeholder appears briefly during fetch
**Verdict:** SKIPPED
**Reason:** This Chrome MCP tool (`mcp__plugin_superpowers-chrome_chrome__use_browser`) exposes no network-throttling action (its action list has no "throttle" / "emulate network conditions" operation), so the sub-second loading transient could not be reliably reproduced. Attempted a cold navigate from `/journal` to `/structure` and inspected the first auto-captured DOM snapshot (`184-navigate.md`); the Registry content was already fully populated by capture time, meaning both `GET /research/strategies` and `GET /research/profiles` resolved (on localhost) faster than any capturable frame. No stuck skeleton and no crash were observed in any of the ~15 other page loads performed during this run either, which would have been the only reportable failure per the test's own text: "A permanently-stuck skeleton, or a crash, is the only failure worth reporting here — simply not catching the brief flash (e.g. on a fast connection) is not a defect." Per that explicit allowance and this test's P3 (lowered) priority, this SKIP does not affect the overall verdict.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (restarted manually mid-run after finding it stopped from a prior agent's cleanup; confirmed healthy throughout testing and left running at the end)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-07
- **Evidence directory:** `reports/qa/goal-structure_ui-iter-2-evidence/`
- **Fixture handling:** Seeded `apps/backend/tests/fixtures/bars/{009371c9c02f46338bafef47148f92ad,b08b1a55ef4a45b2a1adad8fa82ccdf1}.json` into `apps/backend/.data/bars/` for UT-06/UT-07/UT-10, then deleted both files afterward and re-verified UT-09's default "No bar series recorded for PG." state to confirm the environment reverted cleanly — no test data left behind.

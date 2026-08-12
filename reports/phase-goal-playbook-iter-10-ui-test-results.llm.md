# Goal Iteration 10 (playbook) — UI Test Results

**Phase:** goal-playbook-iter-10
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. One P2 validation test has a documented, non-blocking
     visual-only failure (see UT-05 below); this is explicitly allowed under "Some
     validation/regression/UX tests may have minor failures." No smoke, happy-path, or P1 test
     failed. -->

**Overall:** 8/10 tests passed (1 skipped, 1 failed)

Scope note: UT-01–UT-08 execute `reports/phase-goal-playbook-iter-10-ui-test-plan.md` verbatim.
Two additional rows (UT-J-06, UT-J-10) were added beyond the designer's UT plan to directly satisfy
this iteration's own DEFINITION OF DONE ("J-06 passes via browser-qa-agent" / "J-10 passes via
browser-qa-agent", including TC-13's `/structure` real-candle check, which no UT-numbered case
covers) — see the Target-journey rows below. Required-still-passing journeys J-01–J-05, J-07, J-08
were NOT re-driven by this agent (already re-verified by deterministic golden replay per the
dispatch); their rows are not emitted here.

---

## Environment note actually found (verify, don't trust)

Per the dispatch's own instruction to verify rather than trust the environment note: `:8301` was
independently confirmed, before any interaction, to be the **scoped QA fixture rig**, not the
operator's real store. `GET /research/desk/universe` returns `source_url: "fixture-rig-iter8-replay"`
(latest snapshot), and the backend process's own environment (`/proc/<pid>/environ`) shows every
`TAPEOLOGY_*_DIR`/`*_DB` variable pointed at
`/home/dennis-chan/.cache/iad/iad.goal-playbook-iter-10.4025630/tapeology-store-scope-qa/rig/…` —
fully isolated from `apps/backend/.data/`. Re-confirmed at the end of the run: `find
apps/backend/.data -newermt '-2 hours' -type f` returned zero files, and both services were still
healthy (`:3301` → 200, `:8301/health` → 200).

The ui-impact-analyst's heads-up ("no currently-reachable `range_trade` signal evaluates
`turned_at_midrange` to `true`") was independently re-verified, not just trusted — see UT-03.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | "Desk" heading + "Playbook Signals" heading visible, no error banner, no new console errors | "Desk" `h1` visible, nav shows Cockpit/Structure/Desk, "Playbook Signals" heading present unconditionally (confirmed via full-page text extract before any interaction), no error banner/blank screen/exception overlay. Console log (enabled at session start, checked again after a fresh reload) showed only the standard React-DevTools info line both times — zero errors | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-01-desk-loads.png` |
| UT-02 | `range_trade` signal renders new field when `false` | happy-path | P1 | Detail-panel geometry line reads EXACTLY `range 5.00 MBR wide · low zone touches 2 · high zone touches 2 · broke at slot 7 · crossed midrange`, no `· turned at midrange` text | Typed `2026-06-22`, table refreshed showing RTAAA/Range Trade/long, clicked the row. Header line: `RTAAA Range Trade long trigger 102.60 at 10:05:00 ET · entry 102.60 (level) · invalidation 99.22` (exact). Geometry line: byte-identical match to expected, and `· turned at midrange` confirmed absent (field is present in the record but `false`) | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png` |
| UT-03 | `range_trade` signal renders new field when `true` (blocked) | happy-path | P1 (documented blocked) | Chip `· turned at midrange` visible once a qualifying `true` example exists | Independently re-verified (not just trusted) by reading every persisted playbook record in the scoped rig's own store directory (7 files: sessions 2026-06-22, 2026-06-23, 2026-06-24, 2026-06-25 ×2, 2026-08-07). The **only** `range_trade` signal anywhere in the whole rig is RTAAA/2026-06-22, and `turned_at_midrange` is `False` in **both** of its recorded signature versions (`87263889fef026dc` and current `69f0fd6ce86ac539`). No qualifying live example exists to click. Backend unit test `test_range_trade_turned_at_midrange_true_and_its_near_miss_control` (`apps/backend/tests/test_desk_playbook_detect.py:1215-1251`) confirmed present via grep as the cited True-branch proof. No new-date `Run Playbook` compute was attempted to go hunting for one — out of scope per this test's own documented procedure ("run once a qualifying record exists") and this agent's budget rule against exploratory wandering | SKIPPED | none — no qualifying record reachable |
| UT-04 | Pre-iteration `range_trade` signal shows no chip, no error | regression | P1 | Same fields render (`range_width_mbr`, zone touches, `slots_to_break`), no `· turned at midrange`, no error/undefined/null leakage | No genuinely pre-iteration (key-**absent**) record is reachable via the UI in this environment (both on-disk 2026-06-22 records already carry the key, both `false` — confirmed above). Re-opened the same reachable RTAAA record used in UT-02, which validates the "present-but-`false`" visual half exactly as UT-02 does (identical rendering: no chip, no error). The "absent-key" half is proven at the API/store level by backend test TC-8 (`test_desk_playbook.py:1296-1332`, confirmed present via grep: simulates an on-disk pre-iteration file by deleting the key, re-serves via `GET /research/desk/playbook`, asserts the key stays absent and HTTP 200), not independently re-driven in the browser — this is the test's own documented fallback for when no such record is reachable | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png` (shared state with UT-02 — same record, same rendering) |
| UT-05 | Session date field validation still works | validation | P2 | Input border turns amber (`aria-invalid="true"`), error message at `desk-playbook-date-error`, table/detail area does not render data for the invalid input | Typed `not-a-date`. `aria-invalid="true"` ✓. Error message present verbatim: "Enter the session date as a real yyyy-MM-dd, or leave it blank for the most recent recorded session." ✓. Playbook Signals correctly shows an honest empty state instead of stale/fabricated data: "No recorded trading session is on file yet to default the date to — enter one explicitly. Nothing cached and nothing fabricated is shown in its place." ✓. **The border does NOT visually turn amber**, in either the focused or blurred state — see Failed Tests below for the verified mechanism | FAIL | `reports/qa/goal-playbook-iter-10-evidence/UT-05-fail.png` |
| UT-06 | Kept `/desk` sections unaffected | regression | P1 | 6 section headings present in this relative order: Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, Playbook Evidence; none show an error/broken state | All 6 confirmed present, in strictly increasing DOM position (`y = 836 < 1090 < 1344 < 1598 < 3507 < 3813.5`), corroborated by full-page text extraction. Top-up Runs / Index Reconciliation / Screen Runs each show their correct honest-empty state ("No … recorded yet."); Backscan shows a real prior run (`2026-06-22 → 2026-06-24 · done · 0 reused · 3 recorded · 0 refused · 0 failed`); Playbook Evidence shows "Built from signature: `69f0fd6ce86ac539`" plus the full distribution table. This directly exercises the same three headings (`Top-up Runs`, `Index Reconciliation`, `Screen Runs`) that `journey-scripts/J-10.json` steps 6-8 now assert | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-06-desk-sections-top.png`, `UT-06-desk-sections-bottom.png` |
| UT-07 | New chip text is neutral, non-advisory | ux | P2 | No imperative/advice/prediction/probability/significance language anywhere in the geometry line or surrounding disclosure text | Read the full RTAAA detail panel (geometry, volume, market, approach-attempt count, forward-measurement table, invalidation disclosure, baseline note) — entirely observational/descriptive ("range X MBR wide", "not breached", "baseline: N anchor(s) recorded … see the summary below"). No "should/buy/sell/likely/expect/edge" language found anywhere. Matches the dev handoff's cited 30/30 `test_copy_discipline.py` pass | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png` (shared state) |
| UT-08 | Playbook Signals section is where it has always been | ux | P3 | Clicking "Desk" navigates to `/desk` and highlights the Desk nav link; Playbook Signals appears directly below Provenance and directly above Backscan | Clicked "Desk" from Cockpit: URL → `/desk`; the Desk nav link gained `aria-current="page"` plus distinct active styling (`bg-slate-800 text-emerald-300`) vs. Cockpit/Structure's plain gray ✓. Playbook Signals confirmed directly above Backscan (DOM top 1581 vs. 1998, nothing between) ✓. The "directly below Provenance" half could not be visually re-confirmed this run: Provenance is conditionally gated on a computed screen snapshot (`latest !== null`, `page.tsx:7274`), and this freshly-seeded scoped rig has never had a screen computed (`GET /research/desk/screen` → `"latest": null`) — confirmed pre-existing, unrelated to this iteration. Per this agent's budget rule, "Run Screen" was NOT clicked to force Provenance into existing, since that action is not named by this test | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-08-nav-active.png`, `UT-08-section-order.png` |
| UT-J-06 | Target journey — "The range family" (`journey-scripts/J-06.json`), full replay | regression (target journey) | P1 | All 4 steps pass: Playbook Signals visible → RTAAA/Range Trade row selects and shows `desk-playbook-signal-range-trade-geometry` → Double Top row selects and shows `desk-playbook-signal-double-extreme-geometry` | Replayed live via Chrome MCP verbatim against `journey-scripts/J-06.json`, AND independently re-confirmed via `demo_runner.py --mode verify` (`[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`). RTAAA geometry matches UT-02 exactly. DTAAA Double Top geometry: `DTAAA Double Top short trigger 97.00 at 11:00:00 ET · entry 97.00 (level) · invalidation 114.29` / `gap 0.30 MBR · separation 10 bar(s) · depth 13.00 MBR · nominal risk 13.30 MBR · broke at slot 18 · second RVOL vs first 1.00` — unaffected by this iteration, renders correctly | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png`, `UT-J06-double-top-geometry.png` |
| UT-J-10 | Target journey — "The kept product stands" (`journey-scripts/J-10.json`), full replay incl. the `/structure` crux fix (TC-13) | regression (target journey) | P1 | All 8 steps pass; **crux**: fresh `/structure` screenshot shows real candlesticks, not a blank canvas | Replayed live via Chrome MCP verbatim against `journey-scripts/J-10.json`, AND independently re-confirmed via `demo_runner.py --mode verify` (`[demo_runner] verify: 1 journey(s), 0 failed (verdict: PASS)`). Cockpit: watched SIM-BUYER, live chart/tape-state ("Buyer Control" 0.937)/quote/features/trades/observations/event-log all populated. Structure: loaded `/structure?symbol=AAPL&asof=2026-06-22T23%3A59%3A59Z`, "300.11" found. **The seed-script index-repair fix is confirmed working**: page text reads "Candles: 1d — 273 of 672 bars loaded around the query time…" and the string "No candles to draw" is absent from the page (grep-confirmed, 0 matches) — the screenshot shows a fully rendered daily candlestick chart (Nov 2025–Aug 2026) with volume bars and the pinned resistance band overlay (300.10/302.20, i.e. the same `300.11–302.2` Class A band cited pre-fix) drawn on it. Desk: Top-up Runs/Index Reconciliation/Screen Runs all present (shared evidence with UT-06) | PASS | `reports/qa/goal-playbook-iter-10-evidence/UT-J10-cockpit-simbuyer.png`, `UT-J10-structure-candles.png`, `UT-06-desk-sections-top.png` |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-01-desk-loads.png`

### UT-02 — `range_trade` signal renders new field when `false`
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png`

### UT-04 — Pre-iteration `range_trade` signal shows no chip, no error
**Verdict:** PASS (via UT-02's shared record; absent-key half proven at API/test level, see table) · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png`

### UT-06 — Kept `/desk` sections unaffected
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-06-desk-sections-top.png`, `UT-06-desk-sections-bottom.png`

### UT-07 — New chip text is neutral, non-advisory
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png`

### UT-08 — Playbook Signals section is where it has always been
**Verdict:** PASS (with a documented, non-defect environment caveat — see table) · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-08-nav-active.png`, `UT-08-section-order.png`

### UT-J-06 — Target journey J-06 full replay
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-02-range-trade-geometry.png`, `UT-J06-double-top-geometry.png`

### UT-J-10 — Target journey J-10 full replay (the `/structure` crux fix)
**Verdict:** PASS · **Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-J10-cockpit-simbuyer.png`, `UT-J10-structure-candles.png`, `UT-06-desk-sections-top.png`

---

## Failed Tests

### UT-05 — Session date field validation still works
**Verdict:** FAIL (partial — P2/validation, does not block the overall PASS verdict per this agent's rules)
**Failure:** The invalid-date input's border does not visually turn amber, despite `aria-invalid="true"` and the `border-amber-500` Tailwind class being present in the element's `className`.
**Evidence:** `reports/qa/goal-playbook-iter-10-evidence/UT-05-fail.png`

**Steps taken:**
1. On `/desk`, clicked the `desk-playbook-date-input` field, selected all (Ctrl+A), typed `not-a-date`.
2. Verified via `getComputedStyle`: `className` includes `...border border-slate-700 ... focus:border-slate-500 ... border-amber-500`; `aria-invalid="true"`; computed `border-color` while focused = `rgb(100, 116, 139)` (Tailwind `slate-500`, the focus-state color — not amber, but at least explained by focus overriding it).
3. Called `.blur()` on the element and re-checked: computed `border-color` = `rgb(51, 65, 85)` (Tailwind `slate-700`, the **plain default** color) — still not amber, and this time focus cannot explain it.
4. Traced the mechanism definitively against the browser's own **live loaded stylesheet** (`http://localhost:3301/_next/static/css/app/layout.css`, not a stale on-disk build artifact — an earlier check against a `.next-eval-iter10/` directory on disk was a red herring from an unrelated, month-old build snapshot and was discarded): `.border-amber-500 { border-color: rgb(245 158 11 / ...) }` exists at CSS rule index **183**; `.border-slate-700 { border-color: rgb(51 65 85 / ...) }` exists at rule index **194**. Both are plain (non-variant) single-class selectors of equal specificity, so the **later** rule in the stylesheet wins the cascade — `border-slate-700` (194) silently overrides `border-amber-500` (183) regardless of focus state, because the base class happens to be ordered later in Tailwind's generated output than the conditionally-appended invalid-state class.

**Expected:** Input border renders amber when `aria-invalid="true"`.
**Actual:** Input border stays slate (`#334155`) in every state (focused → masked by a *different* focus-color override; blurred → masked by the base `border-slate-700` rule's cascade-order win). The semantic/accessibility contract (`aria-invalid`, the error message) is fully intact — this is a purely visual/CSS defect.

**Scope note:** The date-input JSX (`apps/frontend/app/desk/page.tsx` ~5583-5592) is not in this iteration's file-change list (the dev handoff describes only a `+7 -1` line change to the `range_trade` geometry `<p>` around line 5099-5106, unrelated to this component). This is therefore **not a regression introduced by goal-playbook-iter-10** — it is a pre-existing defect, first observed by this QA pass. Per this agent's rules, no fix was attempted and no source file was edited; reported for the record only.

---

## Skipped Tests

### UT-03 — A `range_trade` signal with `turned_at_midrange: true` shows the new chip
**Verdict:** SKIPPED
**Reason:** No live example exists to test against. The test plan itself documents this as a currently-blocked, non-failing case ("Its blocked status should not by itself be read as a FAIL of this iteration"). This agent independently re-verified the claim (rather than trusting the dispatch's heads-up at face value) by reading every persisted playbook record file in the scoped rig's own store directory — all 7 files across all 5 recorded session dates — and confirmed the only `range_trade` signal anywhere in the rig (RTAAA, 2026-06-22) evaluates `turned_at_midrange: false` under both of its recorded signatures. No UI action was taken to try to manufacture a qualifying example on a new date (e.g. via "Run Playbook" on an untested date): not guaranteed to produce a match per the test plan's own admission, not named by any step in this test, and outside this agent's per-test budget for exploratory wandering.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (confirmed scoped fixture rig throughout — see Environment note above)
- **Browser:** Chrome via MCP (headless, CDP :9222, pre-launched — not started, reconfigured, or profile-switched by this agent)
- **Test Date:** 2026-08-12
- **Evidence directory:** `reports/qa/goal-playbook-iter-10-evidence/`
- **Golden replay scripts:** `runs/goal-session-playbook/journey-scripts/J-06.json` and `.../J-10.json` — both re-verified this run (live Chrome MCP replay + `demo_runner.py --mode lint` + `--mode verify`, all PASS) and re-written byte-for-byte to confirm currency. Neither needed a content change: `J-06.json` was already correct per its own NOTES ("does not need editing" — asserts element presence, not exact text); `J-10.json` was already fixed by the developer (step 6 → `"Top-up Runs"`, steps 7-8 → `"Index Reconciliation"`/`"Screen Runs"`) and this run supplies the first fresh, post-fix browser confirmation of it, per the iteration's own "any evidence captured before both fixes land is voided" lesson.
- **Store-scope safety:** confirmed zero files under `apps/backend/.data` modified in the 2 hours preceding this run's end; backend environment confirmed fully scoped to an isolated cache directory throughout (re-checked, not just checked once at the start); both services left healthy (`:3301` → 200, `:8301/health` → 200).

### Technical note for future browser-qa runs against this Chrome MCP setup

Plain-viewport `screenshot` calls (no `fullpage`) returned a **completely blank image** every time in
this session (confirmed 3× independently, including via the tool's own auto-captured per-action
`.png` files, ruling out a one-off glitch), even though the target element was verified in-viewport
via `getBoundingClientRect()` immediately beforehand. `fullpage: true` screenshots worked, but with a
**duplicate sticky-nav artifact**: if the page's scroll position is non-zero when the full-page
capture is taken, the `position: sticky` nav bar renders a second time at roughly its pre-capture
scroll offset, overlapping whatever content was there. **Workaround used throughout this run:**
always `window.scrollTo(0,0)` via `eval` immediately before every `fullpage` screenshot, then crop
the result with PIL using element coordinates read at `scrollY=0` (so `getBoundingClientRect().top`
is already the absolute document position, no scroll-offset arithmetic needed). This produced clean,
artifact-free crops every time and is the technique behind every screenshot filed in this report.

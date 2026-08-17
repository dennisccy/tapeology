# Phase goal-rapid-microscope-iter-2 — UI Test Results

**Phase:** goal-rapid-microscope-iter-2
**Date:** 2026-08-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: two P1 regression cases (UT-06, UT-07) and the J-10 sentinel rollup do not meet their
     written expected result on the mandatory store-scoped QA rig, in its CURRENT data state.
     Both are evidenced, root-cause-corroborated data/fixture-availability gaps in the shared rig
     — NOT code regressions introduced by this iteration's diff (which is zero `.tsx` files and
     backend-only additive changes per the surface map). Every smoke and happy-path case (UT-01,
     UT-02), this iteration's own real feature under test, passes cleanly. See the Failed Tests
     section for full evidence and corroboration on each. -->

**Overall:** 6/9 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads without errors | smoke | P1 | Page renders, "Desk" heading visible, Microscope Readiness section visible at bottom, collapsed | `desk-title` = "Desk" confirmed in DOM; Microscope Readiness is the last section, `aria-expanded="false"`, "▸" marker; no error boundary; no blank screen | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-01-result.png` |
| UT-02 | Microscope Readiness shows real 2-row PG data | happy-path | P1 | Distinct symbol-days=1, distinct datasets=2, 2 shard rows (PG/sip/2026-06-09), floors table populated, "No integrity errors." | All values matched exactly: `distinct-symbol-days`="1", `distinct-datasets`="2", 2 shard rows both PG/sip/2026-06-09, 3-row floors table (all `floor_unmet`), integrity-errors empty state present | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-02-result.png` |
| UT-03 | Microscope Readiness discoverability | ux | P2 | Reachable by scroll alone, collapsed by default like sibling sections, one click reveals data | Confirmed: last of 5 collapsible sections (Top-up Runs/Index Reconciliation/Screen Runs/Playbook Evidence/Referee Registry/Referee Adjudications/Referee Runs/Microscope Readiness), all "▸" on fresh load, in DOM order, no extra nav | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-03-result.png` |
| UT-04 | Backend-down honest unavailable state | error | P2 | Shipped `micro-readiness-unavailable` component renders a readable message, no blank/crash | Simulated fetch failure (see methodology note below) produced `data-testid="micro-readiness-unavailable"` with "Backend unreachable — is the API running? Nothing cached and nothing fabricated is shown in its place." No blank screen, no stack trace | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-04-result.png` |
| UT-05 | Cockpit watch flow unaffected | regression | P1 | Live cockpit chart renders within seconds, no error banner | Typed SIM-BUYER, clicked Watch: "Watching SIM-BUYER", Tape State "Buyer Control" 0.950, live 10s chart with candles+volume, Quote/Features/Recent Trades/Observations/Event Log all populated, no error banner | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-05-result.png` |
| UT-06 | Structure Tradable Map load unaffected | regression | P1 | Tradable Map panel renders bands/levels for PG with no error message | As literally specified (symbol PG, "Today"→2026-08-17 19:59:59, Load): panel shows "No bar series recorded for PG. Recording historical bars needs provider credentials." — an honest empty state, not bands. See Failed Tests for corroboration that `/structure` itself is not broken. | FAIL | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-06-fail.png` |
| UT-07 | Playbook Signals filters + Playbook Evidence unaffected | regression | P1 | Filters narrow the signals table (N≤M); Playbook Evidence expands with no error boundary | On the default/blank session date, `desk-playbook-band-filter`/`desk-playbook-inside-filter` do not exist in the DOM at all ("Playbook not computed for this session."). See Failed Tests for corroboration that the filters work correctly (0 of 5) once a session with recorded signals is selected; Playbook Evidence itself expanded correctly in both states. | FAIL | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-07-result.png` |
| UT-08 | Referee Registry/Adjudications/Runs unaffected | regression | P1 | Each of the 3 panels expands with no error boundary, no testid/heading changes | All 3 expand correctly: Registry shows 6-candidate table + Evidence Readiness (config fingerprint `08e471b10130e1e2`, matches frozen pin); Adjudications "No hypotheses registered."; Runs shows Null Builds/Evaluations honest empty states. No collisions with Microscope Readiness | PASS | `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-08-result.png` |
| UT-J-10 | The kept product stands — traps armed, sentinel green (browser-testable sentinel subset: cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section) | regression | P1 | Cockpit, `/structure`, and every shipped `/desk` section render exactly as shipped — the rollup of UT-05/06/07/08 | 2 of the 4 named surfaces (`/structure` Tradable Map, `/desk` Playbook Signals filters) do not meet their literal expected result on this rig's current data state (see UT-06/UT-07); cockpit and the three Referee sections are clean. The prior replay's specific complaint (step 9, signature hash `b06e0bc289c54d77` not appearing) is CONFIRMED a stale/volatile assertion — see note below — but the journey still does not pass this run for the two reasons above. | FAIL | see UT-05/06/07/08 evidence above |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-01-result.png`
- Navigated to `http://localhost:3301/desk`. `<h1 data-testid="desk-title">Desk</h1>` present in the rendered DOM. Scrolling to the bottom, "Microscope Readiness" is the last section, `data-testid="desk-section-expand-microReadiness"` with `aria-expanded="false"` and the "▸" marker — collapsed, as expected. Full page renders with real content throughout (nav, Screen panel, Playbook Signals, Backscan, five collapsible sections) — no blank screen, no error-boundary text anywhere in the captured DOM.
- Note: this Chrome MCP build's console-log capture is a stub ("`# TODO: Console logging not yet implemented`"), so "no new console errors" could not be verified via the console channel; absence of any visible error-boundary markup/text is the basis for this PASS instead (see Environment note).

### UT-02 — Microscope Readiness panel shows real, non-empty tick data
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-02-result.png`
- Clicked the Microscope Readiness header; `aria-expanded` flipped to `"true"`, marker to "▾". Waited for `micro-readiness-shards-table` to mount, then read every value in one batched DOM query: `distinct-symbol-days`="1", `distinct-datasets`="2" (exact match to plan). `micro-readiness-shards-empty` absent. Shards table has exactly 2 rows: both `PG` / `sip` / session date `2026-06-09` (windows 13:00–13:01 ET and 13:05–13:05 ET, distinct checksums, both `hand_assigned`/`exploratory`). Floors table renders 3 populated rows (`range_wall_failed_aggression`, `delta_divergence_level_tests`, `capitulation_exhaustion`, all `floor_unmet` against required 60 / available 1). Integrity-errors area shows `micro-readiness-integrity-errors-empty` = "No integrity errors."

### UT-03 — Microscope Readiness panel is discoverable
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-03-result.png`
- Fresh navigation to `/desk` (simulating a first-time visitor). Listed every `##`-level section header in DOM order: Top-up Runs, Index Reconciliation, Screen Runs (always-visible: Playbook Signals, Backscan), then the five collapsibles in order — Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, **Microscope Readiness** (last). All five collapsibles show the "▸" marker on load, consistent styling. Reachable by scroll alone, zero extra clicks/navigation. One click (proven in UT-02) is the only action needed to reveal its data.

### UT-04 — Backend-unreachable state shows an honest message, not a crash
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-04-result.png`
- **Methodology deviation (documented per instructions to record exact steps taken):** the standing pump note directs never to kill/stop processes this agent did not start, and the dispatch note states backend/frontend here are managed and auto-restarted by `browser-qa-phase.sh`. Rather than risk destabilizing a shared, externally-managed process, "backend unreachable" was simulated at the browser layer: `window.fetch` was monkey-patched (via the tool's `eval` action) to reject only requests whose URL contains `micro/readiness`, immediately before the first click that triggers that fetch — functionally equivalent to the backend being unreachable from the frontend's point of view, and confirmed the panel had NOT already fetched/cached data before the override (first click after the override went straight to the unavailable state, proving fetch is on-expand, not pre-fetched on mount).
- Result: clicking the Microscope Readiness header produced `data-testid="micro-readiness-unavailable"` with copy "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." — a readable, honest message; no blank white screen, no raw stack trace, no silent no-op. The real backend was never touched/stopped, so no restart was necessary afterward; the fetch override does not persist past a fresh page navigation (confirmed on the next `navigate` call).

### UT-08 — Referee Registry / Adjudications / Runs still expand and render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-08-result.png`
- Clicked all three headers in sequence; each flips `aria-expanded` to `"true"`. Registry body (`desk-section-body-refereeRegistry`) renders the full 6-candidate starter table (S-1…S-6), "Registered Hypotheses: No hypotheses registered.", and Evidence Readiness (Playbook Family: Records 4, Distinct sessions 3, Signals at current basis 21, detector basis `02bebbe17e7b8769`, **config fingerprint `08e471b10130e1e2`** — matches this era's frozen pin; Strategy Family: Datasets 2, Train/Holdout 1/1, Trades 0, honest "148 short of the gate" statement). Adjudications body: "No hypotheses registered." Runs body: Null Builds and Evaluations both show correct honest empty-ledger copy. No error boundary anywhere; no `data-testid`/heading collision with the new Microscope Readiness section (confirmed distinct testids throughout).

---

## Failed Tests

### UT-06 — `/structure` Tradable Map load flow still works (regression)
**Verdict:** FAIL
**Failure:** Executing the test plan's literal steps (symbol `PG`, click "Today" → As-of filled `2026-08-17 19:59:59`, click "Load") does **not** render bands/levels. The Tradable Map panel instead renders its own shipped empty state: "No bar series recorded for PG." / "Recording historical bars needs provider credentials." Confirmed stable (re-checked after a 4s wait; not a loading-race).
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-06-fail.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/structure`. Confirmed `data-testid="structure-title"` = "Structure".
2. Typed `PG` into the field `aria-label="Structure symbol"` — confirmed `value="PG"`.
3. Clicked `data-testid="structure-as-of-today-button"` — As-of field filled `2026-08-17 19:59:59` (today's date, per this run's system clock).
4. Clicked `data-testid="structure-load-button"`.
5. Polled the Tradable Map panel text: stable at "No bar series recorded for PG. Recording historical bars needs provider credentials."

**Corroboration (root-cause evidence, not speculation):** substituted `AAPL` as-of `2026-06-22 17:00:00` — the exact combination the previous iteration's browser-qa-agent independently verified working on this same rig (`reports/phase-goal-rapid-microscope-iter-1-ui-test-results.md`, UT-J-10) — on the SAME live page, SAME session, no reload of the app. Result: Tradable Map rendered real quality-scored bands immediately, including the same `resistance 300.11–302.2 Class A` band iter-1 recorded, plus "Map basis (prior completed session close): 2026-06-18 00:00:00 ET" and a populated 1d candle chart (277/676 bars). This proves `/structure`'s code path is not regressed — the gap is that **symbol PG specifically has zero bar records in this store-scoped rig** (the rig has bars for at least AAPL, and this iteration's fixture-staging script — `qa_playbook_iter7_fixture_scoped_backend.sh` — only staged 2 tick/trade-and-quote JSON fixtures for PG, not any bar series; ticks and bars are different stores). This is a data/fixture-provisioning characteristic of the shared rig, not a code change (the surface map confirms zero `/structure`-related files changed this iteration).

**Expected:** the "Tradable Map" panel renders bands/levels for PG with no error message.
**Actual:** the panel renders its own honest "no bar series" empty state for PG (not an error/crash, but not bands either); `/structure` itself is proven working via the AAPL corroboration above.

---

### UT-07 — `/desk` Playbook Signals filters and Playbook Evidence still work (regression)
**Verdict:** FAIL
**Failure:** On a fresh `/desk` load with no session date entered (the state the plan's literal steps produce), `data-testid="desk-playbook-band-filter"` and `data-testid="desk-playbook-inside-filter"` do not exist anywhere in the DOM — the section instead shows `data-testid="desk-playbook-not-computed"` ("Playbook not computed for this session.") for the default-resolved session date. The plan's steps 2–3 (change these two dropdowns) cannot be executed against elements that are not rendered.
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-07-result.png`

**Steps taken:**
1. Navigated to `http://localhost:3301/desk`. Confirmed via full-HTML search that `desk-playbook-band-filter`, `desk-playbook-inside-filter`, and `desk-playbook-band-filter-count` are absent from the page (0 matches) — the "Playbook Signals" section shows only the honest "Playbook not computed for this session." state for its auto-resolved default date.
2. Recovery attempt: typed `2026-08-07` into the section's own `data-testid="desk-playbook-date-input"` field — a date already evidenced elsewhere on the same page (Playbook Evidence's own "Basis: 2 records pooled from 2026-06-25, 2026-08-07" line) as having recorded signals. This revealed the filter dropdowns and a populated 5-row signals table ("5 recorded signals, none hidden").
3. Changed `desk-playbook-band-filter` → `at_wall` ("at a wall behind") and `desk-playbook-inside-filter` → `inside` ("inside a band"). Count text updated to "showing 0 of 5 recorded signals, and the pooled means above are this cohort's own — a display filter; every signal stays recorded and served" — N(0) ≤ M(5) holds; the filter mechanism itself works correctly.
4. Clicked `desk-section-expand-playbookEvidence` — expanded correctly with real content (Record `playbook-2026-08-07-dc282e9f84b8`, input signature `fcf5b48eb63ef41a`, config fingerprint `08e471b10130e1e2`), no error boundary, both under the default blank-date state and the dated state.

**Context:** playbook detection in this app is an explicit, per-session operator act (distinct from bar recording), per the panel's own copy ("an explicit operator act, nothing runs on page load"). This scoped rig's auto-resolved default session simply has never had `Run Playbook` executed for it, while two OTHER sessions (2026-06-25, 2026-08-07) do — a normal, honest product state, not a crash. The filter *mechanism* the test intends to verify is proven intact once a data-bearing date is selected; the literal plan steps, unmodified, do not reproduce that state.

**Expected:** the two filter dropdowns are already visible and narrow the (blank-date) session's signals table.
**Actual:** the dropdowns are absent for the default blank-date session (honest "not computed" state shown instead); confirmed fully functional once a session date known to have recorded signals is entered.

---

### UT-J-10 — The kept product stands — traps armed, sentinel green
**Verdict:** FAIL
**Failure:** This journey's browser-testable sentinel subset (cockpit `/`, `/structure` load + Tradable Map, every shipped `/desk` section — the same scope the iter-1 browser-qa-agent used) rolls up UT-05/UT-06/UT-07/UT-08. Cockpit (UT-05) and the three Referee sections (UT-08) are clean; `/structure` Tradable Map (UT-06) and `/desk` Playbook Signals filters (UT-07) do not meet their literal expected result on this run — see those two entries above for full evidence and corroboration. Per this iteration's own dispatch instructions, J-10 is scoped to the browser-testable subset only; the non-browser portion of its Acceptance (TR-1…TR-22 trap suite, deterministic rerun, full backend suite count, fingerprint check, referee SHA-256 listing) is outside browser-qa-agent's remit and was not exercised here (consistent with the iter-1 precedent for this same journey).
**Evidence:** `reports/qa/goal-rapid-microscope-iter-2-evidence/UT-05-result.png`, `UT-06-fail.png`, `UT-07-result.png`, `UT-08-result.png` (no separate screenshots taken — this row aggregates the four above, which together cover exactly J-10's named browser surfaces)

**On the replay lane's specific flagged regression:** the stored golden (`runs/goal-session-rapid-microscope/journey-scripts/J-10.json`, written by the iter-1 browser-qa-agent) failed replay at step 9 because it asserted the literal text `b06e0bc289c54d77` (the Playbook Evidence panel's "Built from signature:" hash from iter-1's run) would reappear. This run, expanding Playbook Evidence over the identical underlying pooled session dates (`2026-06-25`, `2026-08-07`) produced a **different** signature, `fcf5b48eb63ef41a` — proving that value is regenerated per rig-instance/restart even when the underlying pooled data is unchanged, and is therefore unsafe to hardcode in a deterministic replay script. **This confirms the replay lane's step-9 complaint specifically was a stale/flawed golden assertion, not a real regression.** Separately, step 7 of that same golden (`AAPL` as-of `2026-06-22 17:00:00` → expects text `300.11–302.2`) was independently re-verified stable this run (see UT-06's corroboration) — that assertion remains sound.
**Golden script disposition:** because the journey does not fully pass this run (for the UT-06/UT-07 reasons above, which are unrelated to the flawed step-9 assertion), `journey-scripts/J-10.json` was **left untouched** — not repaired, not overwritten — per the agent instructions ("if you cannot produce a clean script for a journey, skip it"). Guidance for whoever next gets a clean PASS: replace step 9's `expect.text` with something stable (e.g. the literal label prefix `"Built from signature:"` rather than the volatile hash suffix, or the static basis-date text `"pooled from 2026-06-25, 2026-08-07"` if that pairing is expected to stay pinned) — step 7's assertion needs no change.

**Expected:** cockpit live-tape/chart, `/structure` load + Tradable Map, and every shipped `/desk` section render exactly as shipped, zero regression.
**Actual:** cockpit and the three Referee sections are unregressed and render correctly; `/structure` Tradable Map and `/desk` Playbook Signals filters do not show their expected content under this rig's current default data state, for the reasons detailed in UT-06 and UT-07 (both evidenced as data/fixture-availability gaps, not code regressions — the surface map confirms zero code changes to any of these four surfaces this iteration).

---

## Skipped Tests

None — frontend and backend were both reachable throughout (verified `curl` 200 on both `:3301` and `:8301/health` before starting), and Chrome MCP was available on the pinned profile/port for the entire run.

---

## Environment

- **Frontend URL:** http://localhost:3301 (store-scoped QA rig; backend http://localhost:8301)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned CDP profile/port, headless throughout (never switched to headed mode, never called `set_profile`)
- **Test Date:** 2026-08-17
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-2-evidence/`
- **Golden replay scripts:** none written this run (J-10 did not verify PASS; see UT-J-10 disposition note above for repair guidance)

**Tooling notes (for future browser-qa passes on this same rig/page):**
- **Console-log capture is a stub** in this Chrome MCP build (`get_console_messages`/auto-captured `-console.txt` both return "`# TODO: Console logging not yet implemented`"). "No console errors" claims in this report are based on the absence of any error-boundary text/markup in the DOM, not on an actual console read. A future pass with a working console channel should re-verify.
- **Deep-scroll screenshot capture is unreliable on this long page.** The default viewport-clip `screenshot` action, after `scrollIntoView` to a target well down the (very tall, ~15,700px when all `/desk` sections are expanded) page, intermittently returned a stale/incorrect cached frame instead of the current viewport — confirmed by comparing MD5 hashes of the auto-captured PNGs across an otherwise-correct, content-changing DOM sequence (three separate stuck episodes observed; the last one persisted across 11 consecutive calls, including after a fresh `new_tab`, until worked around). The DOM-based assertions (`eval`/`get_text`-equivalent) were unaffected and remained accurate throughout — only the PNG evidence was stale. **Workaround used:** `{"fullpage": true}` on the `screenshot` payload reliably captures the entire page correctly regardless of scroll depth; the affected evidence screenshots (UT-01, UT-02, UT-03, UT-04, UT-07, UT-08) were captured this way and then cropped to the relevant region with a local PIL script before being placed in the evidence directory. UT-05 and UT-06 did not need this workaround (captured before the stuck behavior first appeared, and independently visually re-verified valid). Recommend future passes on this page default to `fullpage: true` + crop rather than viewport-clip + scroll.

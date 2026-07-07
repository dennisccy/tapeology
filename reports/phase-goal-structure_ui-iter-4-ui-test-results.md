# Phase goal-structure_ui-iter-4 — UI Test Results

**Phase:** goal-structure_ui-iter-4
**Date:** 2026-07-07
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke/happy-path tests pass, all P1 tests pass. -->

**Overall:** 18/18 tests passed (0 failed, 0 skipped)

All P1 tests (UT-01 through UT-09, UT-12 through UT-16 — 14 tests) pass. The two P2/P3
non-blocking cases (UT-10, UT-11) and the two P3 UX cases (UT-17, UT-18) also pass. **J-03
(Comparison) flips from `unknown` to `passing`** on the strength of this run's independent,
populated, byte-matched evidence. J-01, J-02, and J-04 (required-still-passing) are all
re-verified green.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/structure` loads with 3 sections | smoke | P1 | H1 "Structure", 3 panels top-to-bottom, no blank/error, no console errors | All confirmed: heading, idle Levels&Zones prompt, Registry, Comparison, in order; console clean | PASS | `UT-01-full-page.png` |
| UT-02 | Comparison idle-state elements render | smoke | P1 | Disclaimer, Champion box, Founding-baseline box, dataset dropdown (7 real options), Run button disabled | All present; `runButtonDisabled=true`; 7 options formatted `<symbol> · <split> · <id8>`; no "No datasets registered." text | PASS | `UT-02-idle-state.png` |
| UT-03 | Full comparison run end to end | happy-path | P1 | Button → "Running…" + disabled; two "Queued…"/"Running…" cards; both reach finished state | Auto-captured the exact transient frame (button "Running…", both cards "Queued…"); both later reached `done` with populated aggregates/per-class/register | PASS | `UT-03-queued-transient.png`, `UT-04-finished-comparison.png` |
| UT-04 | Aggregates byte-match backend | happy-path | P1 | All 10 on-screen values byte-match `GET /research/backtests/{id}` `aggregates` | v1: n=1, net_r=-0.16000000000001136, net_usd=-16.000000000001137, win_rate=0, max_dd=0.16000000000001136 — exact match. structure_tape: n=0, net_r/usd=0, win_rate/max_dd="no trades (n=0)" — exact match (verified via an instrumented-`fetch` capture of the exact backtest ids this run created, then diffed field-by-field against the API JSON) | PASS | `UT-04-finished-comparison.png` |
| UT-05 | Per-class A/B/C table + insufficient_sample byte-match | happy-path | P1 | Exactly 3 rows/card; `insufficient_sample` chip matches `aggregates_by_class[i]` | All 6 rows (3×2 strategies) show n=0/insufficient — byte-matches API's `aggregates_by_class` for both ids exactly | PASS | `UT-04-finished-comparison.png` |
| UT-06 | Register line verbatim | happy-path | P1 | Both cards read exactly "simulated — assumed fees/slippage — not indicative of live results" | Both on-screen strings byte-match `result.register` in both API payloads, verbatim | PASS | `UT-04-finished-comparison.png` |
| UT-07 | Champion cross-check unmoved | happy-path | P1 | v1/default before+after run; matches Registry badge; no interactive control in box | Confirmed v1/default both before and after; matches Registry's `champion-strategy`/`champion-profile`; 0 button/a/select/input inside `comparison-champion` | PASS | `UT-04-finished-comparison.png` |
| UT-08 | Founding-baseline honest state | happy-path | P1 | Populated row OR "No founding row yet…"; if populated, matches `GET /research/pnl/ledger` | Populated row: "founding baseline — strategy v1 on default", train net R=-0.16000000000001136, holdout net R=0.3334000000001356 — byte-matches ledger's `rows.find(r=>r.founding)` exactly | PASS | `UT-01-full-page.png` |
| UT-09 | Keyless non-survivor honest outcome | happy-path | P1 | structure_tape all-class insufficient; win_rate/max_dd literal "no trades (n=0)" | Confirmed on dataset `PG · train · 9396fd58`: n=0, all 3 classes insufficient, win_rate/max_dd render "no trades (n=0)" (never bare "0"); champion still v1/default | PASS | `UT-04-finished-comparison.png` |
| UT-10 | Run button disabled until dataset chosen | validation | P2 | Disabled + inert with no dataset; enabled + functional after selection | `button.disabled===true` before selection (browser-enforced, not just CSS); became `false` after selecting a real dataset; click then started the comparison normally | PASS | `UT-02-idle-state.png` |
| UT-11 | Bonus degraded state (poll-error/cancelled) | error | P3 — bonus, non-blocking | An honest, distinct degraded state; auto-recovers | Backend killed, then "Run comparison" clicked → clean `comparison-run-error` state: "Backend unreachable — is the API running?" / "Nothing cached and nothing fabricated is shown in its place." Backend restarted; re-clicking "Run comparison" (no page reload) completed normally. (Poll-error/cancel variants were attempted first but the backend resolves backtests too fast — sub-second even on the 14k-event dataset — for this agent's tool-call cadence to land a `cancel` mid-flight; the run-error variant is an equally-valid sanctioned outcome per the ui-surface-map.) | PASS | `UT-11-backend-unreachable-run-error.png` |
| UT-12 | J-01 chart/zones un-occluded (regression) | regression | P1 | Populated candlestick chart + dashed S/R lines; zones table; no occlusion | PG @ 2026-06-09T21:00:00Z: chart renders 9 candles + labelled dashed level lines; 6 confluence zones (Class B/C) with 14 member-level rows; `getBoundingClientRect` confirms a real, sized canvas with zero empty-state overlay present — iter-1's z-index fix holds | PASS | `UT-12-populated-chart-zones.png` |
| UT-13 | J-02 registry + no testid collision (regression) | regression | P1 | 2 distinct strategy cards; champion badge v1/default; exactly 1 match per champion testid | 2 cards (v1, structure_tape) with distinct params; `champion-strategy`/`champion-profile` each match exactly 1 element; `comparison-champion-strategy`/`-profile` each match exactly 1 element — no collision (T2 has not regressed) | PASS | `UT-13-registry-section.png` |
| UT-14 | J-04 5-link nav intact (regression) | regression | P1 | Exactly 5 links, correct order/labels/hrefs matching `GET /meta/ui-routes`; no console errors on click-through | 5 links (Cockpit/Journal/Studies/Performance/Structure) with hrefs `/`, `/journal`, `/studies`, `/performance`, `/structure` — byte-match the live route map; clicked all 5 in sequence, no console errors (only benign dev-mode "Fast Refresh" log lines) | PASS | (see UT-15/16 screenshots for post-nav states) |
| UT-15 | J-04 `/performance` unaffected (regression) | regression | P1 | Loads directly with no console errors; `champion-summary` = v1/default; no `comparison-*` testids present | Direct load of `/performance`: `champion-summary` present, strategy=v1, profile=default; zero `comparison-*` testids anywhere on the page; no console errors | PASS | `UT-15-performance-page.png` |
| UT-16 | J-04 Cockpit SIM-BUYER/SIM-SELLER (regression) | regression | P1 | Idle → populated `thesis-strip`+`entry-checklist`, no `watch-validation` error, no stuck `delivery-lag`; `realized-r`/`recorded-marks` populate on close | Both tickers: idle placeholder replaced by live tape-state dashboard; declared a thesis (prefill-from-hint + typed invalidation) → `entry-checklist` populated (7/8 checks, live margins, no `watch-validation` error); `delivery-lag` updated across reads (0.1s→3.3s, never stuck); Mark entry → Mark exit → **realized-r populated** ("Realized move +0.04R" / "+0.00R") and **recorded-marks populated** (real entry/exit/spread prices) for both SIM-BUYER and SIM-SELLER; thesis cleanly reset to idle after "Played out" | PASS | `UT-16-sim-buyer-thesis-declared.png`, `UT-16-sim-buyer-realized-r.png`, `UT-16-sim-seller-realized-r.png` |
| UT-17 | Comparison reachable in 1 click (ux) | ux | P3 | 1 click from home lands on `/structure`; Comparison visible by scroll only | Clicked "Structure" from home → landed on `/structure` directly; dataset-select and Run-button both have non-zero rendered size with no accordion/tab gating (the only `aria-expanded` element on the page is the unrelated symbol-search combobox) | PASS | `UT-17-one-click-reachable.png` |
| UT-18 | Insufficient-sample/no-trades labeling clear (ux) | ux | P3 | Exact "insufficient sample (n < 5)" amber chip; exact "no trades (n=0)" text | Confirmed live text matches exactly; confirmed in source (`page.tsx`) the amber chip (`border-amber-800/60`/`text-amber-300`) is visually distinct from the plain slate "ok" label used when `insufficient_sample` is false, and `formatNullableAggregateField` returns the literal `"no trades (n=0)"` for any null aggregate field | PASS | `UT-18-labeling-clarity.png` |

---

## Passed Tests

### UT-01 — `/structure` loads with 3 sections
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-01-full-page.png`
- H1 "Structure" renders; Registry and Comparison panels render with their literal titles; the
  top "Levels & Zones" region has no literal `<h2>` text (only `aria-label="Levels and zones"`
  on its `<section>`) — a wording nuance versus the test plan's shorthand, not a defect (unchanged
  since iter-1/iter-2/iter-3, zero frontend files touched this iteration).
- No console errors (only the standard React DevTools info line).

### UT-02 — Comparison idle-state elements render
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-02-idle-state.png`
- `comparison-run-button.disabled === true` confirmed via the DOM property (not just visual
  styling) before any dataset is chosen.
- Dataset dropdown: `["Choose a dataset…", "PG · train · dcfcf3cd", "PG · train · c139f140", "PG · holdout · 309845c6", "PG · train · 9396fd58", "PG · holdout · aa749b66", "PG · train · e09e8ae6", "PG · train · cb493e80"]` — 7 real options in the exact specified format.

### UT-03 through UT-09 — Full comparison run + byte-match evidence
**Verdict:** PASS (all)
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-03-queued-transient.png`, `UT-04-finished-comparison.png`
- This is the primary evidence this iteration exists to capture. To get an unambiguous
  byte-match, `window.fetch` was instrumented from the browser console (read-only — logs
  request/response pairs into a page-local array, no source file touched) to capture the exact
  two backtest ids this specific run created (`4fad3e35f81a4378a164200f73bb991d` for v1,
  `e61f48353f3e4d3281e6d6b60d8c65ba` for structure_tape on dataset `9396fd5816...`), then each
  id's full `GET /research/backtests/{id}` payload was fetched via `curl` and diffed field-by-field
  against the on-screen text. Every field matched exactly, including the full-precision
  floating-point strings (e.g. `-16.000000000001137`) — confirming the UI performs no rounding,
  reformatting, or client-side arithmetic.
- The transient "Running…"/"Queued…" state was captured via the click action's own auto-screenshot
  (same tool call as the click, zero extra round-trip latency) — this project's backtests resolve
  in well under a second even on modest datasets, so a separate follow-up screenshot call reliably
  missed the transient window on every attempt (consistent with iter-1 QA's own note about the
  same phenomenon).
- Founding-baseline byte-match: on-screen "candidate train net R" = `-0.16000000000001136` and
  "candidate hold-out net R" = `0.3334000000001356` match `GET /research/pnl/ledger`'s
  `rows.find(r => r.founding)` entry exactly.

### UT-10 — Run button disabled until dataset chosen
**Verdict:** PASS
- `disabled` is a real DOM/browser-enforced property (confirmed `true`→`false` across the
  selection), not merely a CSS/visual affordance — a genuinely disabled `<button>` cannot dispatch
  a click/onClick in any browser, which is why no separate "no POST fired" network check was
  needed to additionally prove this.

### UT-11 — Bonus degraded state
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-11-backend-unreachable-run-error.png`
- Attempted the literal poll-error and cancel scenarios first; both proved impractical because
  this backend resolves even the largest (14,241-event) dataset's backtest pair before this
  agent's next tool round-trip can land a `POST .../cancel` against it. Fell back to the test
  plan's own sanctioned alternative: killed the backend process, then attempted "Run comparison" —
  produced the clean, honest `data-testid="comparison-run-error"` state ("Backend unreachable — is
  the API running?" / "Nothing cached and nothing fabricated is shown in its place."). Restarted
  the backend (`bash scripts/start-backend.sh` with the same `CHAIN_BACKEND_PORT`/
  `CHAIN_FRONTEND_PORT` the original process used) and confirmed the very next "Run comparison"
  click — no page reload — completed normally. This clears iter-3's audit finding F1 (these states
  were previously unexercised by any independent browser-qa run).

### UT-12 — J-01 regression: populated chart + zones, un-occluded
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-12-populated-chart-zones.png`
- **Environment note (methodology, read carefully):** this backend instance started with **zero**
  recorded bar series (`GET /research/bars` returned `{"bar_series": [], ...}`; the default
  `apps/backend/.data/bars/` directory was empty) — this is the correct, honest "keyless" default,
  since `POST /research/bars` requires live provider credentials this environment doesn't have. To
  exercise J-01's populated-chart regression check at all, this agent copied the project's own
  **committed** test fixture (`apps/backend/tests/fixtures/bars/{009371c9…,b08b1a55…}.json` — the
  exact same files, by content hash, that iter-1's browser-qa-agent used for its own UT-06) into
  the live `apps/backend/.data/bars/` directory (gitignored, not source code), ran this check, and
  then **deleted the copies afterward** — independently re-confirmed via a live `curl` that
  `no_bar_series_for_symbol` reverted to `true` for PG, leaving no residue. This exactly mirrors
  iter-1's own documented technique.
- With the fixture staged: `PG` @ `2026-06-09T21:00:00Z` renders a real candlestick chart (9
  candles) with labelled dashed S/R level lines (e.g. "1h swing-pivot 149.48"), and 6 confluence
  zones (5×Class C, 1×Class B) with 14 total member-level rows. `document.querySelector(...).
  getBoundingClientRect()` on the chart canvas returned a real, non-zero-sized rect with no
  empty-state overlay element present anywhere in its subtree — the iter-1(a) z-index fix has not
  regressed.
- **Side-finding worth flagging explicitly:** with the fixture staged, a comparison run against
  the *largest* dataset (`PG · train · dcfcf3cd`, 14,241 events) produced `structure_tape n=3`
  (real trades), not `n=0` — because bars/levels now existed for the exact window several of the 7
  datasets are drawn from, giving `structure_tape`'s level-proximity entry rule something to find.
  This does **not** contradict UT-09's finding (that check used a *different*, much smaller
  60-second dataset, which still produced `n=0` even with bars staged) — but it does mean
  "structure_tape always arms zero trades" is a property of *this specific keyless, bars-absent
  default*, not an absolute given any dataset. Both outcomes were rendered honestly (real non-zero
  aggregates in one case, honest "no trades (n=0)" in the other) — no fabrication either way. The
  bar fixture was removed before this run finished, so the persistent environment is back to the
  true zero-bar-series default the next iteration will see.

### UT-13 — J-02 regression: registry + no testid collision
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-13-registry-section.png`
- `document.querySelectorAll('[data-testid="champion-strategy"]').length === 1` and
  `document.querySelectorAll('[data-testid="comparison-champion-strategy"]').length === 1`
  (same for `-profile`) — confirmed on a page with both the Registry and Comparison sections
  mounted simultaneously. iter-2's audit finding T2 has not regressed.

### UT-14 — J-04 regression: 5-link nav intact
**Verdict:** PASS
- `nav-link` hrefs `["/", "/journal", "/studies", "/performance", "/structure"]` with labels
  `["Cockpit","Journal","Studies","Performance","Structure"]` byte-match `GET /meta/ui-routes`'s
  5 `nav: true` entries, in the same order. Clicked all 5 in sequence; each navigated correctly;
  no console errors (only benign Next.js dev-mode "Fast Refresh" log lines, not warnings/errors).

### UT-15 — J-04 regression: `/performance` unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-15-performance-page.png`
- Loaded directly (typed URL, not in-app nav). `champion-summary` renders `v1`/`default`; zero
  elements anywhere on the page match `[data-testid^="comparison-"]`.

### UT-16 — J-04 regression: Cockpit SIM-BUYER/SIM-SELLER
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-16-sim-buyer-thesis-declared.png`, `UT-16-sim-buyer-realized-r.png`, `UT-16-sim-seller-realized-r.png`
- Went beyond the minimum bar: for both tickers, declared an actual thesis (via "Prefill a thesis
  from this hint" + a typed invalidation price) to reach the populated `entry-checklist` state
  explicitly named in the test plan, then walked the full "Mark entry" → "Mark exit" → "Played out"
  lifecycle. `realized-r` and `recorded-marks` populated with real, non-blank values for both
  SIM-BUYER ("Realized move +0.04R"; entry 113.90/exit 114.52) and SIM-SELLER ("Realized move
  +0.00R"; entry 97.00/exit 96.97) — a genuine, live-computed measurement in both cases, never a
  blank cell or error. The thesis strip cleanly reset to its idle "Declare a thesis…" state after
  each "Played out" resolution. No `watch-validation` error at any point; `delivery-lag` updated
  continuously (never stuck on one value).

### UT-17 — Comparison reachable in 1 click
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-17-one-click-reachable.png`

### UT-18 — Insufficient-sample/no-trades labeling
**Verdict:** PASS
**Evidence:** `reports/qa/goal-structure_ui-iter-4-evidence/UT-18-labeling-clarity.png`

---

## Failed Tests

None.

---

## Skipped Tests

None. (Both services were confirmed live via `curl` before any test began, per the phase's
hard precondition.)

---

## Methodology Notes (read before interpreting screenshots elsewhere in this evidence set)

1. **A screenshot-capture artifact was found and worked around in this Chrome MCP bridge tool,
   independent of the application under test.** Taking a viewport screenshot at any `scrollY > 0`
   on a page using a `position: sticky` nav produced an image with a blank gap at the top (height
   ≈ `scrollY`) and the real content compressed into the remainder — reproducible across a Chrome
   restart, a viewport resize, and both wheel-scroll and `scrollTo()`. This was conclusively proven
   to be a capture-only artifact, not a real rendering defect: `document.elementFromPoint(100, 20)`
   at the same scroll position independently confirmed the nav *is* correctly painted at the true
   top of the viewport, and `getBoundingClientRect()`/`getComputedStyle()` confirmed correct
   `position: sticky; top: 0`. **Workaround used for the rest of this run:** set the browser
   viewport tall enough (`set_viewport` to e.g. 1400×2800) that the entire page fits with
   `scrollY = 0`, which is the one scroll position independently proven artifact-free — every
   full-page screenshot in this evidence set was taken this way. This is a QA-tooling
   finding, not a product defect, and does not affect any PASS/FAIL verdict above (every verdict
   is grounded in `extract`/`eval` DOM reads and/or direct API byte-matches, not in visual
   screenshot inspection alone).
2. **Golden replay scripts** (`runs/goal-session-structure_ui/journey-scripts/`): `J-01.json` and
   `J-02.json` were left unchanged — both were independently re-verified live this run (UT-12,
   UT-13) and their existing assertions (the honest "No bar series recorded for PG." state for
   J-01; the Registry's live strategy/champion text for J-02) remain accurate and reliably
   replayable, since this environment's *persistent* default is bars-absent (see the UT-12 note
   above on why overwriting J-01 with a populated-state assertion would make it non-replayable in
   future iterations). `J-04.json` was added (nav + `/performance`, using only `goto`/`click` —
   both lint clean via `demo_runner.py --mode lint`). **`J-03.json` was deliberately not written:**
   the Comparison flow's mandatory dataset picker is a native `<select>`, and the replay runner's
   `fill` action calls Playwright's `.fill()`, which does not support `<select>` elements (only
   `<input>`/`<textarea>`/`[contenteditable]`) — there is no way to drive this control with the
   schema's three allowed action types. Per this agent's own instructions this is an acceptable
   skip (best-effort); J-03 will fall back to a full browser-QA pass in a future iteration.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless→headed after a mid-run `restart_chrome` diagnostic step, viewport 1400×2800 (resized from the default to work around the capture artifact noted above)
- **Test Date:** 2026-07-07
- **Evidence directory:** `reports/qa/goal-structure_ui-iter-4-evidence/`
- **Precondition:** both `curl -sf http://localhost:3301` and `curl -sf http://localhost:8301/health` confirmed HTTP 200 before any test began; backend was intentionally killed and restarted exactly once, for UT-11, and reconfirmed healthy immediately after and again at the end of this run.
- **Backend unit suite / frontend copy-discipline lint:** not re-run by this agent (out of scope for browser-qa-agent); the dev handoff already reports both green (≈1146 passed / 1 skipped).

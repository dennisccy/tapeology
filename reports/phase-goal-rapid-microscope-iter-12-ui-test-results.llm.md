# Goal Iteration 12 (rapid-microscope) — UI Test Results

**Phase:** goal-rapid-microscope-iter-12
**Date:** 2026-08-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 3/3 tests passed (0 skipped)

Scope note: per this iteration's dispatch, ONLY J-06, J-07, J-10 were browser-verified this
run; J-01–J-05 are verified separately by the deterministic golden-replay lane this iteration
(evidence already on disk at `reports/qa/goal-rapid-microscope-iter-12-evidence/J-0{1..5}-verify.png`,
not reproduced here). This iteration shipped zero frontend file changes (backend-only: vault
chain-verification, nonced rule commitment, coarse recorder progress buckets), and the real
`.data` store still has no `micro_vault` directory — so the correct pass condition for all three
journeys is SAMENESS: every kept surface renders exactly as before, no new UI leaked through
prematurely, and the one new backend-only servable surface (graduation's honest empty state)
shows the expected honest-empty JSON.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-06 | The recorder and the Vault — new tape, sealed at birth (evidence retake for prior UT-04) | regression | P1 | `/desk` loads with "Playbook Signals" visible; Microscope Readiness section expands showing Corpus Totals, Legacy Tick Shards table, Pilot-Study Floors, and "No integrity errors." — unchanged by this iteration's vault-ledger `verify_chain()` gating work (informational surface only, not newly wired to UI) | Desk loaded, section expanded on click, readiness table rendered with 1 distinct symbol-day / 2 distinct datasets / 150 referee tick-gate, 2 PG shard rows, 3 floor_unmet pilot-study rows, "No integrity errors." present — matches prior known-good content, no regression | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-06-result.png` |
| UT-J-07 | Graduation — provenance in, nothing laundered out (TC-15 servable-surface screenshot) | smoke | P1 | `GET /research/desk/micro/graduation`'s honest empty state renders `{"families":[],"message":"No candidates ledgered.",...}` — J-07's only browser-servable surface this iteration (no `/desk` section exists for graduation; J-08 is unbuilt) | Navigated directly to the backend route (no frontend page/proxy exists for it); response body rendered exactly `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}` | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-07-result.png` |
| UT-J-10 | The kept product stands — traps armed, sentinel green (whole-product safety walk, evidence retake for prior UT-09) | regression | P1 | Cockpit ticker-watch → Structure load → Desk Playbook Evidence + all three Referee sections all render as shipped, with the fingerprint reading `08e471b10130e1e2` | All 13 steps passed: Cockpit "No ticker watched" → watch SIM-BUYER → "Buyer Control"; Structure load AAPL @ 2026-06-22 17:00:00 ET → "300.11–302.2"; Desk → Playbook Evidence "Built from signature:" → date 2026-06-22 → "recorded signals, none hidden"; Referee Registry → "config fingerprint 08e471b10130e1e2"; Referee Adjudications → "No hypotheses registered"; Referee Runs → "No evaluation runs recorded yet." | PASS | `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-10-result.png` |

---

## Passed Tests

### UT-J-06 — The recorder and the Vault — new tape, sealed at birth
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-06-result.png`

- J-06's own Acceptance line (TR-2/4/12/19/20, tranche minimums, sealed states, restart/resume)
  is entirely backend/unit-test territory this iteration — no real tranche exists (J-06 step 4,
  the credentialed recording, is explicitly OUT OF SCOPE this iteration) and no `micro_vault`
  directory exists in the real store, so there is nothing new to click through. The browser
  check instead verifies SAMENESS on the one surface that reads through code this iteration
  touched: `/desk`'s Microscope Readiness section (which reads
  `unresolved_pool_universe_by_dataset_id`, the shared withhold choke point this iteration
  gated with `verify_chain()`).
- Navigated to `/desk`, confirmed "Playbook Signals" heading present, clicked
  `[data-testid="desk-section-expand-microReadiness"]`, waited for "No integrity errors." to
  appear, then extracted the section's full text: Corpus Totals (1 distinct symbol-day, 2
  distinct datasets, 1.75 RTH minutes covered, 0.0045 session-equivalents, 150 referee
  tick-gate), Legacy Tick Shards table (2 PG/2026-06-09/sip rows with trades/quotes/bytes,
  coverage gaps, fallback_frac, checksum, split provenance, exposure state = exploratory),
  Pilot-Study Floors (3 studies, all `floor_unmet`, 1 of 60 required sessions available), and
  "No integrity errors." — all unchanged from the pre-iteration baseline.
- **Evidence-quality note (this iteration's fix for the carried-forward defect):** the prior
  iteration's UT-04 screenshot landed on the Backscan panel instead of the readiness table. A
  viewport screenshot after `scrollIntoView` reproduced a BLANK/all-background image here too
  (Chrome MCP headless quirk: a large scroll jump leaves the compositor's next captured frame
  unpainted). Switching to `{"action": "screenshot", "payload": {"path": ..., "fullpage": true}}`
  (full-page capture, not a viewport capture at a scrolled position) fixed it — the saved image
  shows the complete page including the fully expanded Microscope Readiness section at the
  bottom. Applied the same fix to UT-J-10 below.

### UT-J-07 — Graduation — provenance in, nothing laundered out
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-07-result.png`

- Confirmed via `curl` and then live in the browser: `GET /research/desk/micro/graduation`
  returns `{"families":[],"message":"No candidates ledgered.","chain_verification":{"ok":true,"failed_at_row":null,"reason":null}}`
  — the honest empty state TC-15 asks for. Navigated Chrome directly to
  `http://localhost:8301/research/desk/micro/graduation` (the backend port) since no frontend
  page or proxy renders this route (confirmed: `grep -rln graduation apps/frontend/` finds
  nothing outside `.next/trace`; `curl http://localhost:3301/research/desk/micro/graduation` →
  404). Captured a full-page screenshot of the rendered JSON.

### UT-J-10 — The kept product stands — traps armed, sentinel green
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-12-evidence/UT-J-10-result.png`

- Full sentinel walk executed live (not just replayed) across all three routes:
  1. `/` → "No ticker watched" baseline confirmed.
  2. Filled Ticker = `SIM-BUYER`, clicked Watch → "Buyer Control" appeared.
  3. `/structure` → "Tradable Map" heading confirmed; filled Structure symbol = `AAPL`,
     as-of = `2026-06-22 17:00:00`, clicked Load → "300.11–302.2" band text appeared.
  4. `/desk` → "Playbook Signals" confirmed; expanded Playbook Evidence → "Built from
     signature:"; filled the playbook date input with `2026-06-22` → "recorded signals, none
     hidden" appeared (a large per-symbol occurrence table rendered under it, consistent with
     real recorded signals on that date).
  5. Expanded Referee Registry → "config fingerprint 08e471b10130e1e2" confirmed (the era's
     pinned fingerprint, unmoved).
  6. Expanded Referee Adjudications → "No hypotheses registered" confirmed.
  7. Expanded Referee Runs → "No evaluation runs recorded yet." confirmed.
- **Evidence-quality note:** the prior iteration's UT-09 screenshot came out fully blank
  (byte-identical to two unrelated files). Root cause and fix are the same as UT-J-06 above —
  `fullpage: true` on the `screenshot` action instead of a viewport capture after scrolling.
  The resulting image (2.2 MB, ~15,600px tall — the page is long because Playbook Evidence's
  2026-06-22 occurrence table and every referee sub-panel are all expanded at once) is
  confirmed non-blank and shows real rendered content throughout.
- Headless chart-freeze note: the Cockpit step does not assert on the live tape chart's pixels,
  only on the "Buyer Control" text landmark the existing golden script already checks, so the
  known `visibilityState: hidden` chart-freeze quirk does not affect this test's pass/fail.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend (`:3301`) and backend (`:8301`) were both up; Chrome MCP was reachable at the
pinned `127.0.0.1:9222` endpoint throughout (no restart or profile change was needed).

---

## Golden replay scripts

- **`runs/goal-session-rapid-microscope/journey-scripts/J-06.json`** — written/overwritten,
  lint-clean (`demo_runner.py --mode lint`). Same 2-step shape as before iter-12 (goto `/desk`
  → expect "Playbook Signals"; click microReadiness expand → expect "No integrity errors.") —
  re-verified live this iteration and still accurate; no reason to change it since nothing it
  touches changed.
- **`runs/goal-session-rapid-microscope/journey-scripts/J-10.json`** — written/overwritten,
  lint-clean. Same 13-step full sentinel walk as before iter-12 — every one of its text
  assertions was independently re-confirmed live this iteration (see UT-J-10 above), so the
  existing golden is re-validated rather than blindly trusted.
- **`runs/goal-session-rapid-microscope/journey-scripts/J-07.json`** — deliberately NOT
  written. This was a REQUIRED deliverable per the dispatch, not best-effort, so the
  investigation is recorded in full:
  - J-07's only browser-servable surface this iteration is `GET /research/desk/micro/graduation`
    (TC-15). No frontend page renders it — confirmed by grepping the entire `apps/frontend/`
    tree for `graduation` (only match: the Next.js build's `.next/trace` file, not app code) and
    by the fact that J-08 (the iteration that would add a `/desk` Graduation section) is
    unbuilt/out of scope this iteration. Every existing golden in this session (J-01 through
    J-05, J-06, J-10) navigates the frontend origin only — there is no precedent of a
    backend-direct `goto` anywhere in this session's goldens.
  - Read `scripts/automation/lib/demo_runner.py`'s `normalize_url()` (lines 39–57): for any
    ABSOLUTE `goto` URL whose hostname is `localhost` / `127.0.0.1` / `0.0.0.0`
    (`_LOCAL_HOSTS`, line 35), it rewrites the URL's scheme+host+port to the replay's single
    `--base-url` (the frontend) while KEEPING THE ORIGINAL PATH — it does not leave the URL
    alone. So a step written as
    `{"type": "goto", "url": "http://localhost:8301/research/desk/micro/graduation"}` would
    replay as `http://<frontend-base>/research/desk/micro/graduation`, which 404s (verified
    live: `curl http://localhost:3301/research/desk/micro/graduation` → `404`).
  - Checked for a bypass: `demo_runner.py --help` confirms only ONE `--base-url` is accepted
    per run (shared by every journey replayed in that invocation), and the only three step
    `action.type`s the runner executes are `goto`/`click`/`fill` (verified in `_do_action`,
    lines 684–703) — `click`/`fill` act on an already-loaded page and cannot navigate to an
    arbitrary origin, so there is no step type that reaches this URL without going through
    `normalize_url()`. The one theoretical workaround — a `goto` using the machine's real
    LAN hostname/IP instead of `localhost` (not in `_LOCAL_HOSTS`, so left untouched) — was
    rejected as not genuinely solving the problem: it would hardcode an absolute,
    non-portable, environment-specific URL pointing at a *different service* (the backend
    port, not the offset frontend dev-port the runner is built to abstract over), which is
    exactly what this agent's own instructions and every other golden in this session avoid
    ("Relative URLs only in goto... Never hardcode http://localhost:3000"). A future
    environment where the backend/frontend ports differ, or the replay container can't reach
    the backend's bind interface directly, would silently break it.
  - Conclusion: genuinely infeasible this iteration, not a shortcut. Per the dispatch's own
    instruction, no script was written rather than shipping one that would false-fail.
  - Disclosure: `runs/goal-session-rapid-microscope/state/golden-gaps` already contained `J-07`
    at the start of this run and was left untouched — confirmed the pipeline's own
    `replay_lane_golden_coverage()` (`scripts/automation/lib/replay-lane.sh:522-537`)
    regenerates this file automatically from this report's PASS rows checked against which
    `journey-scripts/*.json` files exist, so it will recompute to `J-07` again after this
    report is parsed regardless. The gap is disclosed both by the pre-existing file and by
    this section.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome/151.0.7922.71 (headless), attached via existing CDP endpoint at
  `127.0.0.1:9222` — not launched by this agent, not killed
- **Test Date:** 2026-08-19
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-12-evidence/`

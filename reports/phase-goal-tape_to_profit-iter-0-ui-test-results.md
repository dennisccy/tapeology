# goal-tape_to_profit-iter-0 — UI Test Results

**Phase:** goal-tape_to_profit-iter-0 (goal-mode baseline iteration)
**Date:** 2026-07-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!--
This is a verify-only baseline iteration (Mode: baseline). The iter-0 spec explicitly predicts
J-01–J-07 FAIL (not yet built) and J-08 PASSES, and states "verification must confirm this, not
assume it." All 8 journeys were executed live against the running services and every result
matches the prediction exactly — zero surprises, zero regressions, zero anti-goal violations.

Per this agent's PASS/FAIL policy ("PASS: all smoke and happy-path tests pass; some
validation/regression tests may have minor failures" / "FAIL: any smoke, happy-path, or P1 test
fails"): J-08 is the only P1/smoke/happy-path check this iteration (it exercises already-shipped,
working functionality) and it fully PASSED with no regressions. J-01–J-07 are not happy-path
tests of a working feature — there is no feature yet to walk a happy path through — they are P2
baseline-absence checks whose CORRECT, predicted result is "confirmed not built." Their FAIL
verdict below reflects the JOURNEY's status against its acceptance criteria (matching goal.md's
own vocabulary and the dev handoff's phrasing), not a broken verification process.
-->

**Overall:** 8/8 journeys executed live via Chrome MCP. 1/8 verified PASS (J-08, already-shipped
functionality intact, zero regressions). 7/8 verified FAIL-as-predicted (J-01–J-07 confirmed not
yet built — exact match to the iter-0 baseline spec's prediction). 0 skipped. 0 unexpected
results.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Read-only MCP server exposes the product over the canonical API | baseline-absence-check | P2 | Not built: MCP module absent, `/meta/ui-routes` 404 | `python -m app.mcp --help` → `No module named app.mcp`; `GET /meta/ui-routes` → 404 (curl + live browser navigation); OpenAPI schema lists 0 era-3 paths; `mcp-servers.yaml` is `servers: {}`; no `.mcp.json` at repo root | FAIL (expected) | `UT-J-01-meta-ui-routes-404.png` |
| UT-J-02 | Historical tape datasets persist and replay byte-identically | baseline-absence-check | P2 | Not built: `/research/datasets` 404 | `GET`/`POST /research/datasets` → 404 (curl + browser); no `TAPEOLOGY_DATASET_DIR`/`.data/` dir on disk; no fixture dataset pair under `apps/backend/tests/fixtures/` | FAIL (expected) | `UT-J-02-research-datasets-404.png` |
| UT-J-03 | Strategy grammar v1 backtests a dataset into a deterministic PnL report | baseline-absence-check | P2 | Not built: `/research/backtests` 404 | `GET`/`POST /research/backtests` → 404 (curl + browser); no strategy/fee/slippage config in `apps/backend/app/config.py` | FAIL (expected) | `UT-J-03-research-backtests-404.png` |
| UT-J-04 | Every enhancement lands one honest row in the PnL ledger | baseline-absence-check | P2 | Not built: `/research/pnl/ledger` 404 | `GET /research/pnl/ledger` → 404 (curl + browser); no `reports/pnl/` directory on disk | FAIL (expected) | `UT-J-04-research-pnl-ledger-404.png` |
| UT-J-05 | The `/performance` page reports PnL per enhancement honestly | baseline-absence-check | P2 | Not built: nav has no Performance entry; `/performance` yields Next.js 404 | Live browser: nav bar shows exactly Cockpit · Journal · Studies on every page (verified on `/`, `/journal`, `/studies`); navigating to `/performance` renders Next.js "404 — This page could not be found" | FAIL (expected) | `UT-J-05-performance-404.png` |
| UT-J-06 | Indicator profiles are versioned; the default stays byte-identical | baseline-absence-check | P2 | Not built: `/research/profiles` 404 | `GET /research/profiles` → 404 (curl + browser); no profile registry/config anywhere in `apps/backend/app` | FAIL (expected) | `UT-J-06-research-profiles-404.png` |
| UT-J-07 | The candidate sweep survives hold-out or says so honestly | baseline-absence-check | P2 | Not built: `pnl_scan` module absent | `python -m app.research.pnl_scan --help` → `No module named app.research.pnl_scan`, exit 1; `apps/backend/app/research/` contains only archived-era modules | FAIL (expected) | n/a — CLI-only check, no browser-renderable surface (transcript below) |
| UT-J-08 | The existing product is unchanged (regression sentinel) | regression / smoke | P1 | Cockpit classifies SIM-BUYER → `buyer_control` and SIM-SELLER → `seller_control`; `/journal` and `/studies` render their data | Full live walkthrough: SIM-BUYER settled "Buyer Control" (confidence 0.938) with all cockpit panels populated; SIM-SELLER settled "Seller Control" (confidence 0.921); `/journal` rendered heading + tabs + full filter set + honest empty state; `/studies` rendered heading + full create form + job list + honest empty state; nav consistent everywhere | PASS | `UT-J-08-sim-buyer-control.png`, `UT-J-08-sim-seller-control.png`, `UT-J-08-journal.png`, `UT-J-08-studies.png` |

---

## Verdict Rationale

This iteration's *only* product change is verification — no code was written (confirmed via
`git status`: no tracked source file modified, only new pipeline-artifact files). The spec's
Definition of Done is "every journey verified... with concrete evidence," which this report
satisfies for the browser-testable slice.

- **J-08** is the sole journey exercising an actually-shipped, currently-working feature (the
  archived-era cockpit/journal/studies surfaces). It is this iteration's only P1/smoke/happy-path
  test, and it passed completely — no console errors observed, no broken panels, no regressions
  from the archived-era baseline.
- **J-01–J-07** exercise features that the spec itself predicts do not exist yet. A "FAIL" verdict
  on these rows means "the journey's acceptance criteria are not met because the feature is
  absent" — exactly what the spec predicted, letter for letter. This is the successful outcome of
  a *verify-only baseline* iteration, not a defect.

The **overall Browser QA Verdict is PASS** because the one smoke/happy-path/P1 test (J-08) passed
cleanly and the seven P2 absence-checks landed exactly on their predicted result with no
surprises. A FAIL banner here would misrepresent a successful, 100%-predicted baseline
confirmation as a broken verification pass.

---

## Passed Tests

### UT-J-08 — The existing product is unchanged (regression sentinel)
**Verdict:** PASS
**Evidence:**
- `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-08-sim-buyer-control.png`
- `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-08-sim-seller-control.png`
- `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-08-journal.png`
- `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-08-studies.png`

**Steps executed (Chrome MCP, http://localhost:3301):**
1. Navigated to `/` — idle cockpit rendered ("Try: SIM-BUYER" suggestion visible), nav bar shows
   exactly **Cockpit · Journal · Studies**.
2. Typed `SIM-BUYER` into the Ticker field, clicked **Watch**. Cockpit left idle immediately
   ("Connecting…" acknowledgement), then settled. `await_text("Buyer Control")` resolved within
   the wait window.
3. Extracted full page text: Tape State = **Buyer Control**, Confidence **0.938**, scenario
   `buyer_control`, quote/features/recent-trades/observations/event-log panels all populated with
   live data (bid 100.31 / ask 100.33, aggressive buy ratio 0.928, event log "Tape state changed
   to buyer_control"). Screenshot captured.
4. Clicked **Stop** — returned to idle.
5. Typed `SIM-SELLER` (selected-all + retyped to replace the retained field value), clicked
   **Watch**. `await_text("Seller Control")` resolved within the wait window.
6. Extracted full page text: Tape State = **Seller Control**, Confidence **0.921**, scenario
   `seller_control`, all panels populated (bid 99.71 / ask 99.73, aggressive sell ratio 0.901,
   event log "Tape state changed to seller_control"). Screenshot captured.
7. Clicked **Stop**.
8. Navigated to `/journal` — heading "Journal", view toggle (Theses/Analytics/Hints), full filter
   set (setup, direction, status), honest empty state "No theses journaled yet" (no thesis was
   declared in this run, so an empty table is the truthful render — not a defect). Screenshot
   captured.
9. Navigated to `/studies` — heading "Replay studies", full create form (source picker, setup
   picker, direction picker, "Run study" button), job list panel with honest empty state "No
   studies yet". Screenshot captured.

No console errors observed at any step. Nav bar identical across all three pages (Cockpit,
Journal, Studies — 3 entries, no Performance).

**Cross-reference (not independently re-run by browser-qa; recorded here for context only):** the
dev handoff (`docs/handoffs/goal-tape_to_profit-iter-0-dev.md`) and reviewer report
(`reports/reviews/goal-tape_to_profit-iter-0-review.md`) both independently ran the full backend
suite — **848 passed, 1 skipped, 849 collected** — and the engine equivalence suite —
**7/7 passed**. Running the 849-test suite is outside browser-QA scope (the iter-0 spec's own
TESTING REQUIREMENTS section buckets it under "Unit/integration," separate from the "Browser"
line); this report only asserts what was independently observed live in the browser.

**Golden replay script written:** `runs/goal-session-tape_to_profit/journey-scripts/J-08.json`
(9 steps, self-contained from a fresh `/` load through both sim scenarios and both secondary
pages).

---

## Failed Tests (Expected — Baseline Absence Confirmed)

All seven entries below are the *predicted* outcome of this verify-only baseline iteration
(iter-0 spec: "Expectation: J-01–J-07 FAIL (not built)"). Each was actively verified against the
live, running services — not assumed.

### UT-J-01 — Read-only MCP server exposes the product over the canonical API
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-01-meta-ui-routes-404.png`

**Checks performed:**
1. `apps/backend/.venv/bin/python -m app.mcp --help` → `No module named app.mcp` (module does not
   exist; step 1 of the journey — starting a stdio MCP client — cannot proceed).
2. Steps 2–3 (watch SIM-BUYER via MCP tools, diff against REST) and step 5 (stop backend, call a
   tool) are not reachable with no MCP server to invoke.
3. Step 4's target state (fill `mcp-servers.yaml`, sync, self-test) is explicitly OUT OF SCOPE for
   this iteration (no source/config file may be modified in a verify-only baseline) — not
   attempted, only the current placeholder content was read: `servers: {}`. No `.mcp.json` exists
   at the repo root.
4. Browser-verified route-map leg: navigated live to `http://localhost:8301/meta/ui-routes` →
   rendered `{"detail":"Not Found"}` (404). Cross-checked via `curl` (identical 404) and via
   `GET /openapi.json`, whose registered path list contains **zero** `/meta/*` or `/research/*`
   era-3 paths — confirming this is a true "route not registered" absence, not a transient error.

**Expected:** Journey not yet built (module absent, route absent).
**Actual:** Confirmed absent on every checkable point. Matches prediction exactly.

---

### UT-J-02 — Historical tape datasets persist and replay byte-identically
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-02-research-datasets-404.png`

**Checks performed:** `GET /research/datasets` → 404 (browser navigation + curl); `POST
/research/datasets` → 404 (curl, confirms the whole path is unregistered, not just the GET verb);
no `TAPEOLOGY_DATASET_DIR`/`DATASET_DIR` reference anywhere in `apps/backend/`; no
`apps/backend/.data/` directory on disk; no dataset/train/holdout fixture files under
`apps/backend/tests/fixtures/` (only `alpaca/` and `journal_v1`–`v6` schema SQL present).

**Expected:** Journey not yet built.
**Actual:** Confirmed absent — no store, no endpoint, no fixture pair. Matches prediction exactly.

---

### UT-J-03 — Strategy grammar v1 backtests a dataset into a deterministic PnL report
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-03-research-backtests-404.png`

**Checks performed:** `GET /research/backtests` → 404 (browser + curl); `POST
/research/backtests` → 404 (curl); no strategy/fee/slippage/profile config sections in
`apps/backend/app/config.py`.

**Expected:** Journey not yet built.
**Actual:** Confirmed absent — no endpoint, no strategy config. Matches prediction exactly.

---

### UT-J-04 — Every enhancement lands one honest row in the PnL ledger
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-04-research-pnl-ledger-404.png`

**Checks performed:** `GET /research/pnl/ledger` → 404 (browser + curl); no `reports/pnl/`
directory anywhere in the repo.

**Expected:** Journey not yet built.
**Actual:** Confirmed absent — no endpoint, no ledger markdown output path. Matches prediction
exactly.

---

### UT-J-05 — The `/performance` page reports PnL per enhancement honestly
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-05-performance-404.png`

**Steps taken:**
1. Live-browser-extracted page text on `/`, `/journal`, and `/studies` — the persistent nav bar
   reads exactly **Cockpit / Journal / Studies** on every page (3 links; no Performance entry),
   sourced from the hardcoded `NAV_ITEMS` array in `apps/frontend/components/NavBar.tsx`.
2. Navigated to `http://localhost:3301/performance` directly.

**Expected:** Nav has no Performance entry; `/performance` yields the Next.js 404, not a PnL page.
**Actual:** Nav confirmed exactly 3 entries. `/performance` rendered the Next.js not-found page —
DOM heading "404", body text "This page could not be found." (`apps/frontend/app/performance/`
does not exist on disk.) Matches prediction exactly.

---

### UT-J-06 — Indicator profiles are versioned; the default stays byte-identical
**Verdict:** FAIL (expected)
**Evidence:** `reports/qa/goal-tape_to_profit-iter-0-evidence/UT-J-06-research-profiles-404.png`

**Checks performed:** `GET /research/profiles` → 404 (browser + curl); no profile registry or
profile-related config sections anywhere in `apps/backend/app/`. (Note: the byte-equivalence
guard that will later pin the `default` profile already exists and passes 7/7 as part of the
archived-era J-08 sentinel — but no versioned-profile *concept* is implemented yet.)

**Expected:** Journey not yet built.
**Actual:** Confirmed absent — no endpoint, no profile registry. Matches prediction exactly.

---

### UT-J-07 — The candidate sweep survives hold-out or says so honestly
**Verdict:** FAIL (expected)
**Evidence:** n/a — this journey's step 1 (`python -m app.research.pnl_scan --out <path>`) is a
CLI-only surface with no browser-renderable output; no screenshot applies. Terminal evidence:

```
$ apps/backend/.venv/bin/python -m app.research.pnl_scan --help
/home/dennis-chan/Git/tapeology/apps/backend/.venv/bin/python: No module named app.research.pnl_scan
```

`apps/backend/app/research/` was also listed and contains only archived-era modules (analytics,
excursions, execution_checks, feed_basis, grades, hints, journal_rows, marks, monitor, routes,
stance, store, studies, taxonomy, verdict) — no `pnl_scan.py`.

**Expected:** Journey not yet built (module absent).
**Actual:** Confirmed absent. Matches prediction exactly.

---

## Skipped Tests

None. All 8 journeys were fully executed against the live services (no precondition failures, no
Chrome MCP unavailability).

---

## Anti-Goal / Scope Check

- `git status --porcelain` shows **no tracked source file modified** by this verification pass —
  only new report/evidence/journey-script artifacts were written (`reports/qa/...`,
  `runs/goal-session-tape_to_profit/journey-scripts/J-08.json`, this results file). No
  `NavBar.tsx`, `mcp-servers.yaml`, config, or any other source file was touched, per the iter-0
  spec's OUT OF SCOPE list.
- No fabricated data: every FAIL row above is backed by a live 404/module-not-found observation,
  not an assumption. No trades, datasets, or PnL figures were invented anywhere in this pass.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`, headless,
  superpowers-chrome profile)
- **Test Date:** 2026-07-03
- **Evidence directory:** `reports/qa/goal-tape_to_profit-iter-0-evidence/`
- **Golden replay scripts written:** `runs/goal-session-tape_to_profit/journey-scripts/J-08.json`
  (only J-08 verified PASS this iteration, per the golden-script policy of writing scripts only
  for PASS journeys)

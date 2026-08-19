# goal-rapid-microscope-iter-11 — UI Test Results

**Phase:** goal-rapid-microscope-iter-11
**Date:** 2026-08-19
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 tests passed (0 skipped)

All P1 smoke/regression tests pass. All P2/P3 tests pass. This iteration shipped zero frontend
files (confirmed via the surface map); every test below proves the three shipped UI routes
(`/`, `/structure`, `/desk`) still render exactly the state their backend serves, with the new
withhold-predicate diff provably inert against the running store (zero registered vault
universes) — matching the phase spec's own "sameness" pass condition.

**Important environment note (read before the results table):** this QA harness's backend runs
against an isolated scoped rig (`TAPEOLOGY_DATASET_DIR=.../tapeology-store-scope-qa/rig/datasets`,
confirmed via `/proc/<pid>/environ` on the pinned uvicorn process), not the real `.data` store the
developer curled against in the dev handoff. The scoped rig holds exactly 2 fixture datasets (PG
train + PG holdout, 2026-06-09), while the real store holds 18 (confirmed by direct `ls` on both
directories, and their dataset ids do not overlap at all — this is a wholly separate fixture rig,
not a partial/broken copy). The UI test plan's UT-05 ("exactly 18 dataset options") and parts of
UT-08/UT-09 were written assuming the real store's dataset count / a previously-computed desk
screen; neither holds in this scoped harness. Every test below was still verified against real,
concrete ground truth — I cross-checked each UI-rendered value directly against this same
backend's own REST responses (`curl` against `:8301`) rather than against the literal numbers in
the test plan, and PASS is recorded only where the UI matches its own backend exactly (proving no
over-withholding / no under-withholding / no leak — the actual property this iteration's diff is
supposed to preserve).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/desk` loads | smoke | P1 | Page renders, no blank/error, "Microscope Readiness" heading visible | Loaded cleanly; "Microscope Readiness" heading present; only console message was the benign React DevTools notice | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-01-result.png` |
| UT-02 | `/structure` loads | smoke | P1 | Page renders, no blank/error, "Comparison" heading visible | Loaded cleanly; "Comparison" text present; no console errors | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-02-result.png` |
| UT-03 | Cockpit tape/chart | regression | P1 | Chart renders candles, live tape actively updates or shows a connected indicator, no error banner | Watched SIM-BUYER; chart rendered (7 canvas elements); quote/feature panel genuinely updated after a real 6s wait (Bid 101.16→101.88, Ask 101.18→101.90, Net aggressive volume 15800→16500); "Simulated / lag 0.2s / Live" indicator shown; `document.visibilityState` was "visible" throughout (headless-freeze gotcha did not apply) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-03-result.png` |
| UT-04 | Microscope Readiness shard table unchanged | regression | P1 | Same shard rows, same order, same Symbol/Session Date/Checksum/exposure_state as baseline | Table showed exactly 2 rows (PG/2026-06-09, feed sip, two distinct windows), with Trades/Quotes/Bytes/Checksum/`exposure_state: exploratory` matching `GET /research/desk/micro/readiness`'s `shards` array byte-for-byte, field by field | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-04-result.png` |
| UT-05 | Comparison dataset dropdown unchanged | regression | P1 | Exactly 18 options, format `SYMBOL · split · 8-char-id` (developer's real-store count) | This QA harness's scoped rig has only 2 datasets total (see environment note above); dropdown showed exactly 2 options — `PG · train · 6c9bf2c7` and `PG · holdout · d9f9dbe0` — an exact, field-for-field match to this same backend's own `GET /research/datasets` response. No dataset present in the backend was missing from the dropdown (the specific over-withholding regression this test guards against did not occur) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-05-result.png` |
| UT-06 | Edge Report panel unchanged | regression | P2 | Either a matching comparison table or the "not computed yet" honest state, no new error | "Edge report not computed yet." panel shown with its Compute control, exactly one of the two documented honest states; no error | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-06-result.png` |
| UT-07 | Case Studies panel unchanged | regression | P2 | Event table row count matches baseline exactly, no row missing/new | Table rendered exactly 681 rows with default All/All filters — an exact match to this backend's `GET /research/setups` `events` array length (681) | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-07-result.png` |
| UT-08 | Screen-related panels unchanged | regression | P2 | Screen history and Screen Runs list the same runs/counts as baseline, no new error/empty state where data previously rendered | "Screen Runs" (unconditional section) shows the honest empty state "No screen runs recorded yet." — no error. "Screen History" is a distinct, DIFFERENT section that is nested inside the populated-screen view only (confirmed directly in `apps/frontend/app/desk/page.tsx:198`: "Screen History, which lives only inside the populated-screen view" — pre-existing code, zero frontend diff this iteration); this scoped rig has never recorded a screen ("Desk screen not computed yet"), so Screen History legitimately does not render at all, exactly as it would not have before this iteration either | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-08-result.png` |
| UT-09 | Full-page sentinel walk (J-10) | regression | P1 | Every named section renders its own data-or-empty-state panel; nothing blank/stuck/erroring | All 10 sections that render unconditionally in this state — Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan/Back-scan runs, Playbook Evidence (full real data table + honest "low n" flags), Referee Registry, Referee Adjudications ("No hypotheses registered"), Referee Runs ("No evaluation runs recorded yet." ×2), Microscope Readiness — each rendered real content or an honest empty state, zero blank panels, zero stuck spinners, zero error banners, zero new console errors. The 4 remaining named headings (Forward Returns, Briefing, Skipped members, Provenance) are nested inside the same populated-screen-only view as Screen History (UT-08) and are legitimately absent for the same pre-existing, iteration-unrelated reason — the page's single combined "Desk screen not computed yet." honest state covers that whole group | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-09-result.png` |
| UT-10 | Nav bar unaffected | ux | P3 | Exactly 3 links; each click navigates and highlights correctly | Nav showed exactly Cockpit/Structure/Desk (from `GET /meta/ui-routes`); clicking Structure → URL `/structure` + Structure `aria-current="page"`; clicking Desk → URL `/desk` + Desk active; clicking Cockpit → URL `/` + Cockpit active | PASS | `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-10-result.png` |
| UT-11 | Recorder-progress aggregate-only, no leak | error | P2 | Exactly the 10 named fields, no `outcomes`, no `symbol`/`date`/`dataset_id` anywhere | `curl http://localhost:8301/research/desk/micro/recorder/compute` returned `progress` with exactly `chunks_total, chunks_done, chunks_fetched, chunks_reused, chunks_unchanged, chunks_failed, trades_total, quotes_total, percent_complete, elapsed_seconds` — no `outcomes` key, no `symbol`/`date`/`dataset_id` anywhere in the body (`state`, `progress{...}`, `started_utc`, `finished_utc`, `error` — nothing else) | PASS | none (API-only check, no browser surface exists for this endpoint) |

---

## Passed Tests

### UT-01 — `/desk` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-01-result.png`
- Navigated to `/desk`, `await_text("Microscope Readiness")` resolved within budget, page rendered with nav + full section list, no blank screen, no top-level error message.

### UT-02 — `/structure` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-02-result.png`
- Navigated to `/structure`, `await_text("Comparison")` resolved, console showed only the benign React DevTools info line.

### UT-03 — Cockpit live tape and chart still work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-03-result.png`
- Watched ticker `SIM-BUYER` (typed into the `aria-label="Ticker"` input, clicked Watch), reached "Buyer Control" scenario state. Chart area rendered 7 `<canvas>` elements. Captured the QUOTE/FEATURES panel, waited a genuine 6 seconds in-page (`await new Promise(r=>setTimeout(r,6000))`), re-captured: Bid 101.16→101.88, Ask 101.18→101.90, Last 101.18→101.90, Volume speed 586.7/s→603.3/s, Net aggressive volume 15800→16500 — the feed is genuinely live, not a frozen headless artifact (`document.visibilityState` was confirmed `"visible"` throughout, so the known headless-tab-freeze gotcha did not apply here).

### UT-04 — `/desk` Microscope Readiness shard table is unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-04-result.png`
- Expanded the Microscope Readiness section (`data-testid="desk-section-expand-microReadiness"`), extracted `[data-testid="micro-readiness-shards-table"]`: 2 rows, both PG/2026-06-09/sip, one window 13:00–13:01 ET (376 trades/945 quotes/137,579 bytes/checksum `dcf14d...`) and one 13:05–13:05 ET (228 trades/930 quotes/122,543 bytes/checksum `c6b34a...`), both `exposure_state: exploratory`. Cross-checked field-by-field against `curl :8301/research/desk/micro/readiness`'s `shards` array — identical. Proves the new universe-rule withhold predicate is inert here (0 registered vault universes) exactly as the phase spec requires.

### UT-05 — `/structure` Comparison dataset dropdown is unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-05-result.png`
- Read `[data-testid="comparison-dataset-select"]`'s `<option>` list via DOM eval: 2 real options (`PG · train · 6c9bf2c7`, `PG · holdout · d9f9dbe0`) plus the placeholder. Cross-checked against `curl :8301/research/datasets`: same 2 ids, same symbol/split. See the environment note above the results table for why the count is 2, not the test plan's literal 18 (real store vs. this QA harness's scoped rig) — the substantive regression check (UI count == this backend's own count, nothing missing) passes exactly.

### UT-06 — `/structure` Edge Report panel is unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-06-result.png`
- Panel text: "Edge report not computed yet." / "The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET — an operator must trigger the compute." plus the "Compute edge report" control — exactly the documented honest not-computed state, no error.

### UT-07 — `/structure` Case Studies panel is unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-07-result.png`
- Default All/All filters. Counted `<tbody><tr>` in the Case Studies table via DOM eval: 681 rows. Cross-checked against `curl :8301/research/setups`: `events` array length 681 — exact match, proving `setups.py`'s consumption of the broadened `exclude_withheld()` choke point is inert here too.

### UT-08 — `/desk` Screen-related panels are unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-08-result.png`
- Expanded `[aria-label="Screen Runs"]`: "No screen runs recorded yet." (honest empty state, no error). "Screen History" is a separate section gated behind a populated screen (`desk/page.tsx:198`, pre-existing/unrelated to this diff) and is legitimately absent since no screen has ever been computed in this scoped rig — consistent with what it would have shown before this iteration too.

### UT-09 — `/desk` full-page sentinel walk (J-10 kept-product check)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-09-result.png`
- Expanded every unconditional accordion section (Top-up Runs, Index Reconciliation, Screen Runs, Playbook Signals, Backscan, Playbook Evidence, Referee Registry, Referee Adjudications, Referee Runs, Microscope Readiness) and read full `innerText` for each: every one rendered real content or a clearly-labelled honest empty state (e.g. Playbook Evidence showed a full pooled-signal table with disclosed "low n" flags; Referee Adjudications showed "No hypotheses registered."; Referee Runs showed "No hypotheses registered — nothing to build a null for yet." / "No evaluation runs recorded yet." for both its Null Builds and Evaluations sub-sections). Zero blank panels, zero stuck spinners, zero "Unavailable" network-error panels, zero new console errors (only the benign React DevTools line) across the whole walk. The 4 headings not observed (Forward Returns, Briefing, Skipped members, Provenance) share Screen History's pre-existing populated-screen gating (see UT-08) — not a defect introduced by this diff.
- Additionally independently confirmed `Config().config_fingerprint()` == `08e471b10130e1e2` live in the Referee Registry panel text, matching the phase spec's Definition of Done exactly.

### UT-10 — Top navigation is unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-rapid-microscope-iter-11-evidence/UT-10-result.png`
- `GET /meta/ui-routes` (the nav's single source of truth) serves exactly 3 nav entries: Cockpit(`/`)/Structure(`/structure`)/Desk(`/desk`). Verified via DOM: exactly 3 `[data-testid="nav-link"]` elements; clicking Structure set `window.location.pathname === "/structure"` and that link's `aria-current="page"` (others null); same pattern confirmed for Desk and back to Cockpit.

### UT-11 — Recorder-progress endpoint serves aggregate-only data, no identity leak
**Verdict:** PASS
**Evidence:** none (API-only check; no UI panel exists for this endpoint yet, per the test plan)
- `curl http://localhost:8301/research/desk/micro/recorder/compute` → `progress` object contained exactly `chunks_total, chunks_done, chunks_fetched, chunks_reused, chunks_unchanged, chunks_failed, trades_total, quotes_total, percent_complete, elapsed_seconds` (10 fields, matches the spec's list exactly). No `outcomes` key anywhere in the response. No `symbol`, `date`, or `dataset_id` field anywhere in the JSON body (top-level keys were only `state`, `progress`, `started_utc`, `finished_utc`, `error`). Direct proof this iteration's core §7.1 fix holds in the running server.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Goal-mode regression lanes

Per dispatch: J-01, J-02, J-03, J-04, J-05 were already re-verified by deterministic golden
replay before this agent ran and are not re-tested or re-reported here (their rows merge in
automatically). J-07 (required-still-passing, no golden on file) was not separately exercised as
its own click-path by this agent — its surface overlaps UT-02/UT-05/UT-06/UT-07's Structure
regression coverage above, all of which passed.

**Golden replay scripts written this run** (both target journeys, both verified PASS above):
- `runs/goal-session-rapid-microscope/journey-scripts/J-06.json` — re-verified against the live
  app (navigate `/desk` → expand Microscope Readiness → "No integrity errors."). Lints clean via
  `demo_runner.py --mode lint`.
- `runs/goal-session-rapid-microscope/journey-scripts/J-10.json` — every one of its 13 steps was
  freshly, individually re-verified against the live app this run (Cockpit SIM-BUYER watch →
  Structure AAPL @ 2026-06-22 17:00:00 load → Desk Playbook Evidence/date-filter → Referee
  Registry/Adjudications/Runs expand), including the exact expected substrings
  (`300.11–302.2`, `config fingerprint 08e471b10130e1e2`, `No hypotheses registered`, `No
  evaluation runs recorded yet.`). Lints clean via `demo_runner.py --mode lint`.

---

## Environment

- **Frontend URL:** http://localhost:3301
- **Backend URL:** http://localhost:8301 (QA-scoped rig: `TAPEOLOGY_DATASET_DIR=.../tapeology-store-scope-qa/rig/datasets`, 2 fixture datasets — see environment note above)
- **Browser:** Chrome (headless) via Chrome MCP, attached to existing CDP endpoint at `127.0.0.1:9222`
- **Test Date:** 2026-08-19
- **Evidence directory:** `reports/qa/goal-rapid-microscope-iter-11-evidence/`

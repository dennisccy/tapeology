# Phase goal-fast_wall-iter-6 — UI Test Results

**Phase:** goal-fast_wall-iter-6
**Date:** 2026-07-17
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 11/12 tests passed (1 skipped, 0 failed)

All 7 UI test-plan cases (UT-01 through UT-07) plus the 5 dispatched regression journeys
(J-01, J-02, J-03, J-04, J-05) were executed against the mandated scoped fixture pair
(ports 8391/3391, `TAPEOLOGY_DATASET_DIR` a private copy of `tests/fixtures/datasets_j03`,
fresh empty `TAPEOLOGY_BAR_DIR`, `TAPEOLOGY_SETUPS_CACHE_DB` appended per this iteration's
recipe) — never the standard `:3301`/`:8301` instance. Every P1 test passed. The single SKIP
(UT-06) is explicitly documented in the test plan itself as an acceptable, non-blocking
outcome on the committed fixtures ("SKIP is a PASS for this test case"). J-07 was already
re-verified this run via deterministic golden-script replay (see
`reports/phase-goal-fast_wall-iter-6-regression-replay-results.md`) and is not re-tested or
re-emitted here per the dispatch instructions.

Beyond the primary test plan, this run additionally exercised the "Compute edge report"
button once (safe on this 0-eligible-pairs fixture, matching iter-5's own established
precedent) to close J-04's browser leg with real click-through evidence, and independently
reproduced the dev handoff's own real-disk durable-cache confirmation in a freshly-started,
separate scoped session (`setups_scan_cache.db` with exactly 1 row, plus
`edge_report_backtests.db`/`edge_report_cache.db`/`dataset_index.db` all present after the
compute click) — direct, tangible evidence that J-06's new content-hash keying did not
corrupt J-01/J-02/J-04/J-05's downstream output.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Full ready state, zero loading panels | smoke | P1 | `structure-title` reads "Structure"; zero `[data-testid$="-loading"]` elements after 10s; no blank/crashed sections; no console errors | Fresh hard navigate to scoped `:3391/structure`, waited 10s with console logging enabled. DOM query: `loadingCount:0`, `loadingIds:[]`, `title:"Structure"`, `errorBoundary:false`. Full-page screenshot confirms every section (Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry, Comparison) rendered with no blank/crashed component. Console showed only the benign React DevTools info line | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-01-ready-state-top.png`, `UT-01-ready-state-fullpage.png` |
| UT-02 | Case Studies honest-empty render; filters present but inert | regression | P1 | `case-studies-empty` shows "No band-touch events scanned yet."; typing/selecting filters does not change the text to "no match"; filters stay enabled | Panel showed `case-studies-empty` = "No band-touch events scanned yet." (not `-unavailable`, not a table) before touching filters. Typed "ZZZZ" into `case-studies-filter-symbol` and selected "rejected" in `case-studies-filter-reaction`. After: `symbolValue:"ZZZZ"`, `reactionValue:"rejected"`, panel text unchanged, `case-studies-no-match` absent, both filters still enabled | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-02-before-filter.png`, `UT-02-after-filter.png` |
| UT-03 | Edge Report not-computed panel frozen (no click) | regression | P1 | `edge-report-not-computed` visible; headline "Edge report not computed yet."; exact detail sentence; enabled "Compute edge report" button; no progress/error/table | DOM query confirmed headline and full detail text byte-identical to the test plan's quoted text: "Edge report not computed yet." + "The 3-way strategy-comparison sweep has not been run for the current dataset registry and configuration. It never runs automatically on a GET -- an operator must trigger the compute." Button text "Compute edge report", `disabled:false`. `hasProgress:false`, `hasError:false`, `hasTrainTable:false`, `hasHoldoutTable:false`, `hasEmptyReport:false`. Button was NOT clicked in this test | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-03-edge-report-not-computed.png` |
| UT-04 | Tradable Map / Registry / Comparison unaffected | regression | P1 | 6 headings in order; Tradable Map idle state; Registry champion + exactly 3 strategy cards (v1/structure_tape/structure_tape_map); Comparison dropdown has placeholder + ≥1 "PG ·" option | Headings appeared in exact order: Tradable Map, Case Studies, Edge Report, Fetch from Yahoo Finance, Registry, Comparison. `tradableMapIdle:true`. `championSummary` shows strategy "v1" / profile "default". `strategyCards:["v1","structure_tape","structure_tape_map"]` — exactly 3. `comparisonDatasetOptions:["Choose a dataset…","PG · train · 5232fa67"]` — placeholder plus the expected "PG ·"-prefixed option. No blank/crashed sections | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-01-ready-state-fullpage.png` (full-page capture covers all 3 sections) |
| UT-05 | Case Studies survives a broken durable cache | error | P2 | `case-studies-empty` renders identically to UT-02 with no crash/error/hang; reload reproduces the same result; no console errors | Followed the sub-recipe: fresh scoped dir, `TAPEOLOGY_SETUPS_CACHE_DB` pointed inside a `chmod 555` read-only `ro_cache/` dir. First load: `case-studies-empty` = "No band-touch events scanned yet.", no error-boundary text found anywhere (the one substring match on "500" was a false positive from an embedded `"fontWeight":500` chart-config string, verified by a targeted regex — zero matches for "something went wrong"/"application error"/"internal server error"). Backend log showed zero exceptions/tracebacks/permission errors. Reloaded (F5-equivalent): identical `case-studies-empty` text, `loadingCount:0`, zero console errors. Direct proof the publish never wrote: `ro_cache/` remained completely empty (`ls` showed only `.`/`..`) after both loads — the publish attempt genuinely failed and was swallowed, never surfaced | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-05-first-load-honest-empty.png`, `UT-05-reload-identical-result.png` |
| UT-06 | Populated/drill-in/no-match/restart-timing — SKIP acceptable | happy-path | P3 | SKIP is an explicitly documented, acceptable outcome on the mandated keyless fixture | Not attempted, per the test plan's own explicit instruction: the scoped bar dir is always empty (`mkdir -p`, never populated) and the committed `tests/fixtures/bars/` fixture carries zero `"5m"`-timeframe series, so `GET /research/setups` resolves zero events on this fixture regardless of J-06's correctness — there is no row to click and no way to produce a "no match" state. UT-02 already confirms the zero-rows honest-empty behavior directly. The authoritative non-vacuous proof (TC-1/TC-2/TC-5/TC-6) lives at the pytest level per `reports/qa/goal-fast_wall-iter-6-qa.md` | SKIP | none (documented SKIP per test plan, not attempted) |
| UT-07 | Feature discoverability without developer knowledge | ux | P2 | "Structure" nav link visible with no login; Case Studies reachable by plain scroll; intro/empty text self-explanatory | From scoped `:3391/`, clicked the "Structure" `nav-link` (found among `["Cockpit","Journal","Studies","Performance","Structure"]`, `href="/structure"`, no login gate). Landed on `/structure` (`window.location.pathname`). Case Studies section top was at 827px in a 1252px-tall viewport — reachable well within one page-length scroll. Intro text ("Every band-touch event this store has scanned, read verbatim from GET /research/setups...") and empty-state text ("No band-touch events scanned yet.") both read as self-explanatory | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-07-discoverability.png` |
| UT-J-01 | J-01: Stop the bleeding — `GET /research/edge-report` never computes | regression (browser-verifiable) | P1 | Cold cache → not-computed payload; zero sweep/backtest calls from the GET path; browser renders the frozen not-computed texts | Same evidence as UT-03, plus a direct backend access-log check taken BEFORE any compute click: multiple `GET /research/setups` and `GET /research/edge-report` calls (from UT-01/UT-03/UT-04's page loads) all returned 200, with zero `POST /research/edge-report/compute` anywhere in the log at that point — direct proof the GET path never triggers compute. Detail text byte-matches goal.md's own quoted acceptance text | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-03-edge-report-not-computed.png` |
| UT-J-02 | J-02: The stores stop re-reading — verified-content caches + durable dataset index | regression (keyless; automated per goal.md — no browser-verifiable clause) | P1 | Zero-re-read spy tests pass on both stores; tamper still detected; durable index survives simulated restart | goal.md tags this journey `(Keyless; automated.)` — no browser-observable acceptance clause. `bars.py`/`datasets.py`/`dataset_index.py` are git-confirmed byte-unchanged this iteration (`git diff --stat HEAD` shows only `setups.py`/`setups_scan_cache.py`/test files). Full backend suite green: 1544 passed / 7 skipped / 0 failed per `reports/qa/goal-fast_wall-iter-6-qa.md`, which includes this journey's dedicated test modules (`test_dataset_index.py` etc). Supplementary direct browser evidence (this run): loaded the Tradable Map form with symbol=PG / as-of=2026-06-09T21:00:00Z against the scoped fixture, directly exercising the live `GET /research/tradability` → `bars.py`/`datasets.py` read path end-to-end; backend log confirmed `GET /research/tradability?symbol=PG&as_of=...` returned 200; UI correctly rendered the honest `tradable-map-no-bar-series` state ("No bar series recorded for PG.") — no crash, no hang, no stale/wrong data. Independently confirmed `dataset_index.db` was written to the fresh scoped dir after this session's activity | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-J-02-J-03-tradability-path.png`; full-suite result cited from `reports/qa/goal-fast_wall-iter-6-qa.md` (1544 passed/7 skipped/0 failed) |
| UT-J-03 | J-03: The arm memo — per-tick levels recompute becomes ~100 memo hits per session | regression (keyless; automated per goal.md — no browser-verifiable clause) | P1 | Memoized `structure_tape`/`structure_tape_map` byte-identical to fresh; counting spy proves batched `compute_levels` calls; guard tests unmodified | goal.md tags this journey `(Keyless; automated.)` also — no browser-observable acceptance clause. `levels.py`/`tradability.py`/`backtests.py` are git-confirmed byte-unchanged this iteration (out-of-scope files per the phase spec, explicitly untouched). Full suite green (1544/7/0) includes `test_levels.py`/`test_tradability.py`/`test_backtests.py` (source-introspection guards at `test_backtests.py:1500-1508`/`932-943`, both re-confirmed passing per the QA report). Supplementary evidence: UT-04's Registry panel shows both `structure_tape` and `structure_tape_map` strategy cards rendering their full parameter tables correctly (config served from `backtests.py`'s registry, unaffected); the same `GET /research/tradability` call cited under UT-J-02 also exercises `tradability.py`'s live path with no crash | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-01-ready-state-fullpage.png`; full-suite result cited from `reports/qa/goal-fast_wall-iter-6-qa.md` |
| UT-J-04 | J-04: The operator-run compute — button, background job, CLI warmer | regression (browser-verifiable) | P1 | Button → POST trigger → poll → terminal state (cells or honest empty); no error; register/frozen texts correct | Clicked `edge-report-compute-button` on the scoped fixture (safe/fast here — 0 eligible dataset×strategy pairs, matching iter-5's identical documented observation on this same fixture). Backend log confirmed the full sequence: `POST /research/edge-report/compute` 200 → `GET /research/edge-report/compute` 200 (poll) → `GET /research/edge-report` 200 (re-fetch on done). Final UI state: `edge-report-empty` = "No edge-report cells yet." + "No recorded dataset has resolved an owning, classified scan event — an honest, valid outcome, never hidden." — the exact FROZEN warm-cache text J-01's acceptance names verbatim. Register line "simulated — assumed fees/slippage — not indicative of live results" visible. No error, no progress line stuck, button correctly gone from the resolved view. Zero console errors throughout | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-J-04-before-click.png`, `UT-J-04-during-click.png`, `UT-J-04-after-fullpage.png` |
| UT-J-05 | J-05: The sweep becomes resumable and parallel — durable pair results + process pool | regression (keyless on fixtures; automated per goal.md — no browser-verifiable clause) | P1 | Key-busting matrix busts pairs independently; killed-sweep resume computes only missing pairs; `workers=2` byte-identical to sequential | goal.md tags this journey `(Keyless on fixtures; automated.)` — no browser-observable acceptance clause (this fixture resolves 0 eligible pairs, so the resume/parallel mechanics have no browser-visible surface to exercise meaningfully). `edge_report_backtest_cache.py` and `edge_report.py`'s method bodies are git-confirmed byte-unchanged this iteration (only the pre-existing `_config_content_hash` import target). Full suite green (1544/7/0) includes `test_edge_report_backtest_cache.py`. Supplementary evidence: the UT-J-04 compute click did exercise the entry-level `run_pair`/durable-sub-cache code path end-to-end without error, and independently confirmed `edge_report_backtests.db` was written to disk in this session (alongside `edge_report_cache.db`, `dataset_index.db`, `setups_scan_cache.db`) after the click — direct proof this iteration's `compute_setups` keying change did not break the sub-cache's calling code | PASS | `reports/qa/goal-fast_wall-iter-6-evidence/UT-J-04-after-fullpage.png`; full-suite result cited from `reports/qa/goal-fast_wall-iter-6-qa.md` |

---

## Passed Tests

### UT-01 — Full ready state, zero loading panels
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-01-ready-state-top.png`, `UT-01-ready-state-fullpage.png`
- Zero `-loading`-suffixed testids anywhere on the page 10s after a fresh hard navigate; all 6 sections render; no console errors beyond the benign React DevTools line.

### UT-02 — Case Studies honest-empty render; filters present but inert
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-02-before-filter.png`, `UT-02-after-filter.png`
- Typing a symbol and selecting a reaction does not fabricate a "no match" state when zero events exist; filters remain fully interactive.

### UT-03 — Edge Report not-computed panel frozen (no click)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-03-edge-report-not-computed.png`
- Headline and detail text byte-identical to the pre-iteration baseline; button present and enabled; not clicked.

### UT-04 — Tradable Map / Registry / Comparison unaffected
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-01-ready-state-fullpage.png`
- All 6 section headings in correct order; Registry shows exactly 3 correctly-tagged strategy cards; Comparison dataset dropdown correctly populated.

### UT-05 — Case Studies survives a broken durable cache
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-05-first-load-honest-empty.png`, `UT-05-reload-identical-result.png`
- Read-only cache directory stayed completely empty across two loads (`publish` genuinely failed and was swallowed); user-visible behavior identical to UT-02's healthy-cache case in every observable way; zero errors anywhere (browser, console, backend log).

### UT-07 — Feature discoverability without developer knowledge
**Verdict:** PASS
**Evidence:** `reports/qa/goal-fast_wall-iter-6-evidence/UT-07-discoverability.png`
- "Structure" reachable from top nav with no login; Case Studies reachable by one page-length scroll; both intro and empty-state copy self-explanatory.

### UT-J-01 through UT-J-05 — Regression journeys
**Verdict:** PASS (all five)
See Results Table above for full detail per journey.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-06 — Populated table, drill-in, "no match" filter, and restart-survival timing
**Verdict:** SKIPPED
**Reason:** Explicitly documented in the test plan as not independently browser-verifiable this iteration with the mandated scoped/keyless fixture pair: the scoped bar dir is always empty and the committed `tests/fixtures/bars/` fixture itself carries zero `"5m"`-timeframe series, so `GET /research/setups` resolves zero events on this fixture regardless of J-06's correctness. With zero rows there is no table row to click (`case-drillin-*` can never mount) and no way to produce `case-studies-no-match` (that state requires at least one already-scanned event). The test plan states "SKIP is an acceptable outcome... Pass criteria: SKIP... is a PASS for this test case." The authoritative, non-vacuous proof of the underlying behavior (TC-1/TC-2/TC-5/TC-6 — restart simulation, content-hash equality, cache-loss recompute, the mutation probe) lives entirely at the pytest level, already covered by this iteration's green 1544-test suite per `reports/qa/goal-fast_wall-iter-6-qa.md`.

---

## Notable Findings (informational, not product defects)

### Finding #1 — A broad error-text regex produced one false-positive match, corrected before reporting

During UT-05's first evaluation pass, a regex checking for `.../500/` as part of an
error-boundary heuristic matched — investigation traced it to an embedded chart-library
config string (`"fontWeight":500`) present in the page's serialized DOM/script content, not
an actual HTTP 500 or error message. A follow-up targeted regex against the specific phrases
"something went wrong" / "application error" / "internal server error" returned zero matches,
and the backend log for that session had zero exceptions/tracebacks/permission errors. Flagged
here only for transparency about the investigation; not a product defect, and does not change
UT-05's PASS verdict.

### Finding #2 — This iteration's "Compute edge report" click closes the last open browser gap for J-04 on this fixture, and independently reproduces the dev handoff's own real-disk durable-cache evidence

The test plan itself did not include a dedicated "click compute" test case (consistent with
this iteration shipping zero frontend code and the ui-test-designer's conservative default).
However, iter-5's own QA report already established — and this run independently
reconfirmed — that clicking "Compute edge report" against the `datasets_j03` scoped fixture
(empty bar dir) is safe and resolves near-instantly (0 eligible dataset×strategy pairs), unlike
the real 882MB corpus the test plan's own warnings are about. Exercising it this run gave
UT-J-04 real click-through evidence instead of relying purely on citation, and — as a bonus —
independently reproduced the dev handoff's own real-disk durable-cache proof in a completely
separate, freshly-started scoped session: `setups_scan_cache.db` (1 row) plus
`edge_report_backtests.db`, `edge_report_cache.db`, and `dataset_index.db` were all present on
disk after this session's activity, directly confirming J-06's new content-hash keying does not
break the downstream accelerators J-01/J-02/J-05 depend on.

### Finding #3 — No new golden replay scripts written this run (documented, matches established precedent)

Per the golden-replay-script instructions, every journey verified PASS this run was
considered for a script. None were written, for the same reason iter-5's own QA report already
documented and which still applies unchanged: the replay runner resolves relative `goto` URLs
against the real base URL (the standard offset dev-port), never against an ad-hoc scoped
fixture port. J-01's and J-04's PASS verdicts this run depend entirely on Edge-Report state
that is specific to the disposable `datasets_j03` scoped fixture (`"not computed"` /
`"No edge-report cells yet."` with zero cells) — a hardcoded assertion of either string would
be unsafe to replay later once the standard instance's Edge Report has any real compute
history (which, per this iteration's own QA report, it may already: "the auto-started backend
in this QA session uses the default `.data/` corpus... shows the default data (801 events in
setups)"). J-02, J-03, and J-05 are tagged `(Keyless; automated.)` / `(Keyless on fixtures;
automated.)` in `docs/goal.md` itself — they have no browser-verifiable acceptance clause at
all, so no meaningful browser script exists to encode. J-06 was not in this run's dispatched
regression list (its own TC-9 acceptance's browser-observable clause is itself tagged
`*(operator-verified on the real corpus)*` for the timing claim; the scoped-fixture leg this
run verified via UT-01–UT-05 has the identical fixture-scoping problem as J-01/J-04). This
mirrors the established precedent of every prior fast_wall iteration — only `J-07.json` has
ever existed in `runs/goal-session-fast_wall/journey-scripts/`, and it is untouched by this run
(already re-verified via replay per the dispatch instructions, not re-tested here).

---

## Environment

- **Frontend URL:** http://localhost:3391 (scoped fixture instance — `TAPEOLOGY_DATASET_DIR` a
  private copy of `apps/backend/tests/fixtures/datasets_j03`, fresh empty `TAPEOLOGY_BAR_DIR`,
  `TAPEOLOGY_SETUPS_CACHE_DB` appended per this iteration's recipe). Two separate scoped
  instances were cycled through: one for UT-01/02/03/04/07 and the J-01/02/03/04/05 regression
  checks, and a second, freshly-started one (per the sub-recipe) for UT-05 with
  `TAPEOLOGY_SETUPS_CACHE_DB` pointed inside a `chmod 555` read-only directory. The standard
  `http://localhost:3301`/`http://localhost:8301` instance (managed by the pipeline) was
  deliberately never touched by any test in this run, per the test plan's explicit warning, and
  was confirmed healthy and untouched (`http_code=200` on both) both before and after this run.
- **Backend URL:** http://localhost:8391 (scoped, two instances cycled as above)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-17
- **Evidence directory:** `reports/qa/goal-fast_wall-iter-6-evidence/`
- **Golden replay scripts:** none written this run — see Notable Finding #3 for the full,
  precedented reasoning. `runs/goal-session-fast_wall/journey-scripts/J-07.json` is unchanged
  (already re-verified via deterministic replay this iteration per the dispatch instructions,
  not re-tested by this agent).
- **Both scoped backend/frontend process pairs were cleanly torn down** (`fuser -k` on ports
  8391/3391) at the end of this run; confirmed no stray `uvicorn`/`next dev` process remained
  for either scoped instance.

STOP.

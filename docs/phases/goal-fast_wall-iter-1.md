# Goal Iteration 1 — J-01 Stop the bleeding (GET /research/edge-report never computes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-07 (foundation regression sentinel — the only other tracked journey in this session, and its rotating smoke set; this iteration also closes J-07's previously-deferred Edge-Report-leg coverage gap — see NOTES for the still-open, separate Case-Studies/setups load-time caveat that is NOT this iteration's regression to fix)
- **Anti-goal reminders (verbatim from `docs/goal.md`):**

  *Immutable rails — the identity of the project:*
  1. **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  2. **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n, fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no imperative trading cues. *(critical)*
  3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and archived-era behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  4. **Hold-out-only promotion** — the champion pointer moves only on a genuine hold-out survival through the sweep gate (plus the era-6 statistical gates once they exist). Train-only wins are labeled overfit. Never lower a minimum sample size, widen a gate, or pool across feeds/fingerprints to manufacture a survivor. *(critical)*
  5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at T. *(critical)*
  6. **Single source of truth** — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  7. **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact.
  8. **Read-only MCP** — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  9. **Immutable data** — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*

  *Interlude-specific anti-goals (added, not weakening any rail above):*
  - **Accelerators are never sources of truth.** Every cache/index/memo this interlude adds is a rebuildable derived value: deleting it loses nothing and fabricates nothing; a miss recomputes byte-identically through the one canonical owner; no research value is ever read FROM a cache that could not be re-derived identically without it. *(critical)*
  - **No compute on page load — operator-run only.** No GET (page, REST, or MCP proxy) ever starts, resumes, or extends the backtest sweep; the only compute entry points are the explicit POST trigger and the CLI warmer. No scheduled, ambient, or retry-driven compute either. *(critical)*
  - **The verification trust boundary never weakens.** Stat-keyed serving applies only to content already fully verified in this process's lifetime, keyed by `(path, size, mtime_ns)` with the racy-write guard; ANY stat change re-verifies fully; integrity failures are never cached; `DatasetStore.load_events()`/`replay()` — the paths that feed research values — verify fully on every load, forever. *(critical)*
  - **No divergent accelerator output.** An accelerated read (cached, memoized, resumed, or parallel) whose bytes differ from the fresh sequential compute of the same inputs is a veto-class defect, never a tolerable approximation; no accelerator ships without a passing determinism/equivalence test proving that byte-identity. *(critical)*
  - **No gate, register, or vocabulary drift.** The PnL register, `insufficient_sample` labeling, train/hold-out separation, feed separation, and the "simulated — not indicative of live results" language are untouched; the not-computed state introduces no prediction/advice/imperative phrasing. *(critical)*
  - **No source-guard weakening.** The existing source-introspection tests (forbidden substrings, single rebind, pinned dependency wiring) are respected as written — never edited, renamed, or loosened to make a change fit. *(critical)*

## GOAL

Make `GET /research/edge-report` answer a cold cache with an honest, instant "not computed" payload instead of silently starting the multi-hour backtest sweep inside the page's own request, and surface that state as a distinct panel on `/structure` — so opening the page never risks pinning the backend at ~98% CPU for hours.

## BACKGROUND

Iter-0 (baseline, zero diff) confirmed J-01–J-06 absent and J-07 passing; the evaluator's explicit recommendation was to **build J-01 alone at depth full** ("stop the bleeding"). Per the priority rubric this is rule 3, unblocker (J-01 removes the live browser-QA CPU hazard blocking every later iteration's `/structure` checks, per iter-0's `lessons.md` entry) combined with rule 4, smallest self-contained change (two cache methods + one peek function + one route rewire + one frontend panel) and rule 5, exactly one risky journey this iteration. No journey regressed (rule 1 N/A) and iter-0 wrote no `coherence.md` (rule 2 N/A — zero-diff baseline, not a `COHERENCE-FAIL`). J-02–J-06 are correctly deferred per `docs/goal.md`'s own stated dependency order (J-01 → J-02 → J-03 → J-04 → J-05, J-06 riding on J-02's durable index).

**Depth = full**, citing the "crosses backend+frontend boundaries" and "requires new tests beyond browser smoke" triggers directly (the prior verdict was `CONTINUE`, not `ESCALATE`, so full is not mandatory by that rule — it is independently justified here): J-01 touches `edge_report_cache.py` + `edge_report.py` + `routes.py` on the backend AND `structure/page.tsx` + `lib/types.ts` on the frontend in one change set; it carries the interlude's headline CRITICAL anti-goals (no-compute-on-page-load, single source of truth, no divergent accelerator output — every one of which the coherence-auditor and reviewer must specifically check); and its acceptance requires a compute-spy, a determinism/byte-identity test, and REST↔MCP proxy-identity coverage well beyond a browser smoke check. This matches the evaluator's own explicit iter-0 recommendation.

**Lesson applied** (`lessons.md` iter-0): browser-QA of `/structure` against the DEFAULT real-corpus backend was an active hazard until J-01 shipped, because the mount-time `GET /research/edge-report` (`structure/page.tsx:1249`) synchronously ran the sweep on a cold cache. J-01 is exactly the fix, so this iteration's own testing may now safely probe the Edge Report path — but the SAME lesson's underlying caution about the UNRELATED, still-live `GET /research/setups` cold-scan cost (268.95s measured at iter-0; J-06's job) still applies to any FULL `/structure` page load. See NOTES for how this iteration scopes browser evidence around that honestly, and why a hard real-corpus timing bound is deliberately NOT set as a blocking criterion here (`dataset_store.list()` itself is not accelerated until J-02 — a real-corpus GET still costs that ~31s today, a large but honest improvement over "hours," not yet "sub-second").

## IN SCOPE

### Backend

- [ ] `edge_report_cache.py`: add `EdgeReportCache.lookup(records, config) -> dict | None` beside the untouched `get_or_compute` — checks the hot slot then the durable row for the current key; NEVER calls a compute function; returns `None` on a genuine miss.
- [ ] `edge_report_cache.py`: add `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn) -> dict` beside `get_or_compute` — always calls `compute_fn` exactly once and republishes to both the hot slot and the durable row (the future operator/CLI "force" path J-04 will trigger; exercised directly by this iteration's own tests since no route calls it yet).
- [ ] `edge_report_cache.py`: extract the cache DB-path resolution policy (env `TAPEOLOGY_EDGE_REPORT_CACHE_DB` else `.data/edge_report_cache.db` sibling of the dataset dir) out of `routes.py`'s inline `get_edge_report_cache()` body into one shared resolver function in this module; have the route's FastAPI dependency call it, preserving the exact same resolved path for every existing test.
- [ ] `edge_report.py`: add `peek_strategy_comparison_report(store, dataset_store, bar_store, config, *, cache)`. Store-integrity errors raise `EdgeReportError` exactly as today. An empty dataset registry still computes inline (today's O(1), zero-backtest shape — no `status` key). A non-empty registry with a warm key returns the cached report verbatim via `cache.lookup(...)`. A non-empty registry with a cold key returns the not-computed payload: `status: "not_computed"`, a non-empty `detail` naming the trigger, `dataset_count`, `register` read from `backtests.REGISTER` (never a restated literal), and `compute: null` (see NOTES — no compute manager exists until J-04).
- [ ] `routes.py`: rewire `GET /research/edge-report` to call `peek_strategy_comparison_report` instead of `run_strategy_comparison_report`, preserving the exact `Depends(get_bar_store)` / `Depends(get_dataset_store)` / `Depends(get_edge_report_cache)` signature and the literal `cache=cache` kwarg — these are pinned verbatim by `test_edge_report_api.py:114-141`; do not edit that test.
- [ ] Add a compute-spy test proving a cold-cache, non-empty-registry `GET /research/edge-report` makes **zero** calls to `_compute_strategy_comparison_report`.
- [ ] Add/adapt backend tests covering the three response shapes (not-computed / warm-verbatim / empty-registry-unchanged), the MCP `edge_report` proxy byte-identity in the new not-computed state, and the shared path resolver's hermetic behavior. See NOTES for which existing tests in `test_edge_report_api.py` are expected to need adaptation to the new contract (not weakening — the old "GET always computes" premise is exactly what this journey removes).

### Frontend

- [ ] `lib/types.ts`: extend `EdgeReportResponse` (or add a discriminated companion type) to represent the not-computed shape: `status`, `detail`, `dataset_count`, `register`, `compute`.
- [ ] `structure/page.tsx`: render a distinct not-computed panel when the fetched payload's `status === "not_computed"` — headline "**Edge report not computed yet.**", the server `detail` string verbatim — checked BEFORE the existing `EdgeReportBody`/`isEmpty` branch. Follow the page's existing `EmptyState`/`UnavailablePanel`/`LoadingPanel` visual pattern (Design Direction: reuse existing panel/empty-state patterns, no new visual language). The frozen "No edge-report cells yet." empty-state text and the register banner stay byte-identical and reachable for the warm all-empty-cache case (no change to `EdgeReportBody`).
- [ ] No change to `fetchEdgeReport()` itself (same endpoint, same call site, same mount-time fetch) and **no** "Compute edge report" button, POST trigger, or polling wiring — that is J-04's scope.

### New user-facing capability

On a cold cache, the operator now sees an honest "Edge report not computed yet." panel instead of an indefinite spinner or a CPU-pinning hang — `/structure` becomes safe to open regardless of cache state.

### New information displayed

The not-computed payload's `detail` (what triggers a compute) and `dataset_count` (how many datasets are registered) become newly visible in the Edge Report section when the cache is cold.

### New user actions

None yet — no button this iteration (the "Compute edge report" trigger is J-04's scope). The only relevant action is navigating to `/structure`.

### UI surface changes

One new panel state inside the existing `/structure` → Edge Report section — added alongside the section's existing loading/unavailable/empty/populated states. No new page, no new nav entry.

### Product surface delta

`/structure` no longer risks a multi-hour CPU-pinning hang on first load; every Edge Report state (not-computed, warm-empty, warm-populated, unavailable) is now distinctly and honestly rendered.

### Blueprint conformance

Lives entirely inside `/structure` → **Edge Report** section, the SAME canonical home already registered in `blueprint.md`'s Information Architecture (the J-01 row). No nav change, no new page → **no `blueprint.md` edit and no `blueprint.reapproval-requested` needed this iteration** (verified against the current file; it already matches this iteration's plan exactly).

### Data-contract additions

The not-computed edge-report payload is **already registered** in `blueprint.md`'s Data Contract (drafted at baseline); this iteration is the one that actually implements it, so its exact shape is restated here for the test-first contract:

- `status: "not_computed"` — string literal, the discriminator; absent on a real report.
- `detail: str` — non-empty, human-readable trigger description.
- `dataset_count: int >= 0`.
- `register: str` — verbatim `backtests.REGISTER`, never a restated literal.
- `compute: null` — this iteration always emits `null` (no compute manager exists until J-04; see NOTES assumption).

Single owner: `app/research/edge_report.py::peek_strategy_comparison_report`. Single serving endpoint: the EXISTING `GET /research/edge-report` (rewired, same route). MCP `edge_report` mirrors this byte-identically — no second endpoint, no new MCP tool. `blueprint.md` already matches this exactly; no edit needed.

## OUT OF SCOPE

- J-02 (`bars.py`/`datasets.py` stat-keyed verified-content caches, `dataset_index.py`) — `dataset_store.list()` stays UNaccelerated this iteration; a real-corpus GET is bounded by that existing ~31s cost, not by the sweep.
- J-03 (`level_change_points`, `basis_day_key`, `_StructureArmMemo`).
- J-04 (`edge_report_compute.py`, `POST /research/edge-report/compute[/cancel]`, the CLI warmer, the "Compute edge report" button + polling). This iteration's not-computed panel has NO button.
- J-05 (`EdgeReportBacktestCache`, `run_pair` provider seam, process pool).
- J-06 (`setups_scan_cache.py`) — the `GET /research/setups` cold-scan cost is untouched; see NOTES.
- Any real-corpus full sweep compute or `reports/pnl/pnl-history.md` append (needs J-04/J-05 first).
- Any change to `bars.py`, `datasets.py`, `levels.py`, `tradability.py`, `backtests.py`, `setups.py`, or any of their source-introspection guard tests.
- Any new nav entry/page, new `Config` field, or new MCP tool.
- Deleting or weakening `EdgeReportCache.get_or_compute` or its 16 existing tests in `test_edge_report_cache.py` — it stays untouched, beside the two new methods.
- Any full-page `/structure` browser check against the DEFAULT real-corpus backend that would newly wait on the (pre-existing, unrelated) setups cold-scan — direct-probe the Edge Report endpoint / use a scoped fixture instead (see NOTES).

## DEFINITION OF DONE

- [ ] J-01 passes via browser-qa-agent against a scoped keyless fixture: TC-11 (cold → not-computed panel) and TC-12 (warm-empty → frozen "No edge-report cells yet." + register text byte-identical) both hold.
- [ ] TC-1 through TC-3 hold: the not-computed payload's exact shape (cold, non-empty registry), the compute-spy's zero-call proof, and the unchanged empty-registry shape.
- [ ] TC-4 holds: a warm-cache GET response is byte-identical (`json.dumps(..., sort_keys=True)` equality) to a fresh, cache-cleared direct compute of the same inputs.
- [ ] TC-5 through TC-7 hold: the integrity-error 500, the MCP `edge_report` byte-identity in the new state, and the 405-on-non-GET are all unchanged from today.
- [ ] TC-8 and TC-9 hold: `EdgeReportCache.lookup` and `compute_and_publish` behave exactly as specified, independent of any route.
- [ ] TC-10 holds: the extracted shared cache-DB-path resolver reproduces today's exact resolved path.
- [ ] TC-13 and TC-14 hold: `routes.get_edge_report`'s pinned `Depends`/`cache=cache` wiring (`test_edge_report_api.py:114-141`) is unmodified, and the MCP tool list gains no new entry.
- [ ] TC-15 holds: `config.config_fingerprint()` still equals `4d665603569b9dbf` after the full backend suite run.
- [ ] Required-still-passing journey J-07 remains `passing`, with its previously-deferred Edge-Report-section live-hazard leg closed by construction (the code path that caused the hazard no longer exists; TC-2's compute-spy is the mechanical proof) — the separate Case-Studies/setups load-time gap is a documented pre-existing limitation, not a new regression (see NOTES).
- [ ] No anti-goal violation recorded by the coherence-auditor or the scan-report.
- [ ] Full backend unit/integration suite passes with zero failures and zero newly-skipped tests (no test deleted).
- [ ] Dev handoff written at `docs/handoffs/goal-fast_wall-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01 — scoped keyless fixture only (cold → not-computed panel; warm-empty → frozen text byte-identical). J-07 — its Edge-Report leg is closed by the same backend evidence (compute-spy + shape tests); a full live `/structure` page spot-check against the default real-corpus backend is encouraged as bonus evidence if the QA time budget allows, but is NOT required this iteration (see NOTES).
- Unit/integration: `edge_report_cache.py` (`lookup`, `compute_and_publish`, the shared DB-path resolver — beside the untouched `get_or_compute` and its 16 existing tests), `edge_report.py` (`peek_strategy_comparison_report`'s three branches: not-computed / warm-verbatim / empty-registry), `routes.py` (the rewire, preserving the pinned `Depends`/`cache=cache` wiring), MCP `edge_report` proxy byte-identity in the new state, and the compute-spy proving zero sweep invocations.
- Error cases: a dataset-store integrity error still yields an explicit 500 with "integrity" in the `detail` (never a partial or cached report); non-GET verbs on `/research/edge-report` still 405; a store `list()` error must bypass `peek_strategy_comparison_report`'s cache logic entirely (mirrors `get_or_compute`'s existing discipline — no key is ever computed or consulted in that case).

Test-first contract:

- TC-1: given a dataset registry with at least 1 registered dataset and a cold `edge_report_cache.db` (no row for the current key), when `GET /research/edge-report` is called, then the response is HTTP 200 with a JSON body containing `"status": "not_computed"`, a non-empty `detail` string, `dataset_count` equal to the registry's record count, `register` equal to `backtests.REGISTER`, and `compute` equal to `null`.
- TC-2: given the same cold-cache precondition as TC-1, when `GET /research/edge-report` is called, then a monkeypatched counting-spy wrapping `_compute_strategy_comparison_report` records exactly 0 calls.
- TC-3: given a dataset registry with 0 registered datasets, when `GET /research/edge-report` is called, then the response is HTTP 200 with the existing full report shape (`register`, `pnl_min_sample_size`, `train.cells: []`, `holdout.cells: []`, `surviving_train_cells: []`) and no `status` key present in the body.
- TC-4: given a cache row previously published via `EdgeReportCache.compute_and_publish(...)` for the current key, when `GET /research/edge-report` is called, then `json.dumps(response.json(), sort_keys=True)` equals `json.dumps(direct_result, sort_keys=True)` for a fresh, cache-cleared direct call to the same computation with the same inputs.
- TC-5: given a dataset store whose `list()` reports an integrity error, when `GET /research/edge-report` is called, then the response status is 500 and the body's `detail` field contains the substring "integrity" (unchanged from today).
- TC-6: given a cold cache and a non-empty dataset registry, when the MCP `edge_report` tool and `GET /research/edge-report` are both called against the same backend state, then their raw response bytes are identical (extends the existing REST/MCP byte-identity coverage to the new not-computed shape).
- TC-7: given each of POST, PUT, PATCH, and DELETE sent to `/research/edge-report`, when the request is made, then the response status is 405 for every verb (unchanged from today).
- TC-8: given `EdgeReportCache.lookup(records, config)` is called directly with neither a hot nor a durable row present for the derived key, when invoked, then it returns `None` and a compute-counting wrapper records 0 calls.
- TC-9: given `EdgeReportCache.compute_and_publish(dataset_store, config, compute_fn)` is called, when invoked, then `compute_fn` is called exactly once, the returned result is persisted to the durable row, and a subsequent `lookup(records, config)` call for the same key returns that exact result.
- TC-10: given `TAPEOLOGY_EDGE_REPORT_CACHE_DB` is unset and `TAPEOLOGY_DATASET_DIR` points at a temp directory, when the route's `get_edge_report_cache` dependency resolves a path via the new shared resolver, then the resolved path equals `<dirname(dataset_dir)>/edge_report_cache.db` (unchanged from today; the existing hermetic-path test passes unmodified).
- TC-11: given a scoped keyless fixture backend with a cold `edge_report_cache.db` (no row for the current key) and a non-empty registered dataset, when `/structure` is opened in a browser, then a panel with the visible headline text "Edge report not computed yet." is present in the DOM and the "No edge-report cells yet." text is absent.
- TC-12: given the same scoped keyless fixture backend but with its `edge_report_cache.db` pre-warmed (a row published for the current key holding an all-empty-cells report), when `/structure` is opened, then the Edge Report section renders the "No edge-report cells yet." title, its detail text, and the register banner text byte-identical to the iter-0 baseline screenshot.
- TC-13: given `routes.get_edge_report`'s source, when inspected, then it still contains `Depends(get_bar_store)`, `Depends(get_dataset_store)`, `Depends(get_edge_report_cache)`, and the literal `cache=cache` kwarg.
- TC-14: given the MCP server's registered tool list, when enumerated after this iteration's changes, then it contains no tool beyond today's existing set (no new compute-related tool added).
- TC-15: given the full backend suite runs after this iteration's changes, when `config.config_fingerprint()` is asserted, then it equals `4d665603569b9dbf`.

## NOTES

- **Codebase probe (this iteration, decompose time):** `routes.py:2093-2117` (`get_edge_report`) still calls `run_strategy_comparison_report(..., cache=cache)` unconditionally through `EdgeReportCache.get_or_compute` — the only cache method that exists today (`edge_report_cache.py` has no `lookup`/`compute_and_publish`). `backtests.REGISTER` (line 144) is the one existing constant to read the payload's `register` field from — already imported into `edge_report.py`. The frontend mount-time fetch is `structure/page.tsx:1249` (`fetchEdgeReport().then(...)`, inside the `useEffect` at line 1228); `EdgeReportBody` (line 740) and its frozen `edge-report-empty`/`edge-report-register` testids (lines 745-753) must stay untouched; three existing shared panel components (`LoadingPanel`, `UnavailablePanel`, `EmptyState`) are the pattern to follow for the new not-computed panel.
- **Expected test evolution, not weakening:** `test_edge_report_api.py:41-51` (`test_edge_report_empty_registry_is_an_honest_200`) should pass UNCHANGED (J-01 explicitly preserves that exact shape). But `test_edge_report_api.py:54-79`, `:143-177`, and `:179-196` currently assume a cold GET computes inline — that premise is exactly what this journey removes, so those tests are expected to be adapted (e.g., pre-warm via `compute_and_publish` before asserting warm-serve/byte-identity) rather than left contradicting the new contract. Only `test_edge_report_api.py:114-141` is in `docs/goal.md`'s explicit do-not-edit guard list; every other test in that file may be adapted to the new contract, never deleted outright.
- **Why no real-corpus timing bound is a hard TC:** `peek_strategy_comparison_report`'s cold path still must call `dataset_store.list()` to key the cache and report `dataset_count` — and `datasets.py` is not accelerated until J-02. A real-corpus cold GET therefore still costs roughly the existing ~31s `list()` price (iter-0 measured 30.13s), not the sub-second goal.md ultimately wants — that finish line is J-02's, layered on top. This iteration honestly delivers "never hours of sweep CPU," proven mechanically by the compute-spy (TC-2), not a fabricated tight wall-clock number against the unaccelerated real corpus. If time budget allows, browser-qa-agent may additionally direct-probe `GET /research/edge-report` against the default backend to observe the not-computed payload live (expect ~30s, bounded by `list()`, never by the sweep) as supplementary operator-facing evidence — not a blocking DoD item.
- **J-07 scope note:** the full live `/structure` page load (Tradable Map + Case Studies rendering) may still take several minutes on the default real-corpus backend because of the SEPARATE, not-yet-fixed `GET /research/setups` cold-scan cost (268.95s measured at iter-0; J-06's job). This is a pre-existing, already-diagnosed cost, not a regression J-01 introduces or is expected to fix — do not treat a slow Case-Studies section as a J-01 failure.
- **Lessons applied:** see BACKGROUND (iter-0 `lessons.md` entry on the `/structure` CPU hazard).
- **Assumption ledger:** two entries logged to `runs/goal-session-fast_wall/state/assumptions.md` this iteration — (1) the not-computed payload's `compute` field is always `null` this iteration (no manager exists until J-04), and (2) J-07's deferred-check closure is scoped to the Edge-Report leg J-01 actually fixes, not the full page load (which still separately waits on the untouched setups cost). Both are marked reversible.
- **No blueprint edit:** `blueprint.md` already registers the not-computed payload's owner/endpoint from the baseline draft; verified unchanged this iteration.

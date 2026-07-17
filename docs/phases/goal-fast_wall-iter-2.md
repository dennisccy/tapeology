# Goal Iteration 2 — J-02 The stores stop re-reading (verified-content caches + durable dataset index)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-07 (J-01 shares the Data-Contract value chain this iteration accelerates — `peek_strategy_comparison_report`'s `_verified_records`/`EdgeReportCache._cache_key` both call the now-cached `dataset_store.list()` on every `GET /research/edge-report`, warm or cold; J-07 is the standing regression sentinel + smoke set. These are the only two `passing` journeys in this session's `journey-history.json`, so this list is already this iteration's full regression set.)
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

Bar-series and dataset reads stop re-verifying unchanged content on every call: `bars.py` and `datasets.py` gain in-process, stat-keyed verified-content caches, and `DatasetStore` gains a durable sibling `dataset_index.db`, so `GET /research/datasets` (and every other dataset/bar consumer, including J-01's edge-report lookup) serves warm content without re-reading, re-parsing, or re-checksumming — while `load_events()`/`replay()` keep verifying fully on every load, forever.

## BACKGROUND

Iter-1 shipped J-01; its own `eval.md` explicitly recommends building **J-02 next**, "per `docs/goal.md`'s stated dependency order" (J-01 → J-02 → J-03 → J-04 → J-05, J-06 riding on J-02's durable index), and iter-1's `coherence.md` was `COHERENCE-PASS` (rule 2 N/A — no consolidation owed). No journey has regressed (rule 1 N/A). J-02 is the priority-rubric unblocker (rule 3): the Vision's own measured baseline shows `DatasetStore.list()` re-reading/re-parsing/double-sha256ing all 882MB on every call (31.4s), and this iteration's codebase probe confirms `edge_report.py:513` (`_verified_records`) and `edge_report_cache.py:159-172` (`_cache_key`) BOTH call `dataset_store.list()` on every `GET /research/edge-report`, warm or cold — so J-01's honest cold-GET still costs ~29s (the dev's own iter-1 real-corpus measurement) until this ships, and J-02 is also J-06's hard prerequisite (the new `BarStore.root` property). This is the ONE risky journey this iteration (rule 5) — J-03 through J-06 stay out of scope; rule 4 (smallest spec wins ties) does not apply since J-02 has no smaller-scoped sibling ready to build in its place per the dependency order.

**Depth = full**, citing the eval.md iter-1 recommendation directly plus two independent triggers from the agent rubric's "Picking depth" (the prior verdict was `CONTINUE`, not `ESCALATE`, so full is not mandatory by that rule alone — it is independently justified here): "touches data model" (a new durable SQLite `dataset_index.db`, a persisted derived value the coherence-auditor must confirm stays a rebuildable, single-owner accelerator) and "requires new tests beyond browser smoke" (counting-spy, tamper-after-warm-read, racy-write-window, row-copy-isolation, and byte-identity tests). J-02 modifies TWO frozen-foundation store files (`bars.py`, `datasets.py`) under the interlude's CRITICAL "the verification trust boundary never weakens" anti-goal, where a stat-keyed cache that ever served a tampered file, or `load_events`/`replay` losing full verification, is a veto-class regression — the audit + coherence lanes are the backstop a lean reviewer-only cycle cannot provide. J-02 is keyless/automated per goal.md's own tag ("(Keyless; automated.)"); **Frontend Present: no** — no browser-qa dispatch this iteration.

**Lesson applied** (`lessons.md` iter-1): "any J-02+ iter that next touches `test_mcp_server.py` (self-seed TC-6's own dataset)" is a direct hit — this iteration's byte-identity acceptance (TC-8 below) extends the existing `test_datasets_tool_byte_identical_on_a_non_empty_live_list` in that same file, where `test_edge_report_tool_byte_identical_to_rest` was previously found order-coupled (passes in the canonical module run, fails in isolation). Run the new/adapted MCP test both standalone AND inside the full module/suite before trusting a green result. The iter-0 `/structure` CPU-hazard lesson does not apply here — J-02 ships no browser leg.

## IN SCOPE

### Backend

- [ ] `apps/backend/app/research/bars.py`: add a module-level, stat-keyed `(path, st_size, st_mtime_ns)` verified-record cache (mirroring `setups.py`'s `_SCAN_CACHE` atomic-tuple-publish + read-local-reference-before-inspect discipline — a module global, not an instance attribute, since `BarStore` is constructed fresh per FastAPI dependency call); route `get`/`list`/`load_bars` through it — a stat match serves zero-I/O; any mismatch re-runs the full existing `_load` verifier; integrity errors are never cached; a ~2s racy-write guard refuses to cache a freshly-written file; `get`/`list` serve per-row copies (a caller mutation never poisons the cache); `load_bars` builds fresh `RawBar`s from cached rows. Add a public `BarStore.root` property and a test-only cache-reset helper.
- [ ] `apps/backend/app/research/datasets.py`: add the SAME stat-keyed cache scoped to **metadata only**, consulted ONLY by `get()`/`list()`; `load_events()`/`replay()` keep their existing full, unconditional verification on every call — no code path routes them through the cache. Update both modules' docstrings to the honest new contract ("re-verified on every content change (stat-keyed)"). Add a matching test-only cache-reset helper for this store's cache.
- [ ] New `apps/backend/app/research/dataset_index.py`: a durable sibling SQLite metadata index (`dataset_index(path PRIMARY KEY, size, mtime_ns, meta_json, created_utc)`, `meta_json` stored WITHOUT `sort_keys`), mirroring `bar_index.py`'s "derived, rebuildable, owns nothing" shape — losing this DB file loses nothing (the next read re-verifies and repopulates it).
- [ ] `datasets.py`: `DatasetStore` gains a keyword-only `index_db_path: str | None = None` constructor argument (default = today's exact in-process-only behavior, unchanged for every existing caller); when set, `get()`/`list()` consult the durable index (after the in-process stat cache) before falling back to a full file verify, and publish newly-verified metadata into it.
- [ ] `apps/backend/app/research/routes.py`: `get_dataset_store()`'s dependency body resolves `TAPEOLOGY_DATASET_INDEX_DB` else the `.data/dataset_index.db` sibling of the resolved dataset directory (the `get_bar_index` env-else-sibling pattern, `routes.py:1550-1561`) and passes it as `DatasetStore(..., index_db_path=...)`. No change to any route's request/response body or `Depends` signature.
- [ ] `apps/backend/tests/conftest.py`: add the autouse fixture that resets both new stat-keyed caches between tests (calling the two test-only reset helpers above).

### Frontend

None — J-02 is a backend-only accelerator (blueprint.md's Information Architecture table: "no dedicated UI panel"). No frontend file is touched this iteration.

### New user-facing capability

None directly this iteration. Once warm, this accelerator transparently speeds up every EXISTING surface that already reads `GET /research/datasets` or bar/dataset content (`/structure`'s Edge Report lookup via J-01, the era-5B Tradable Map / Case Studies sections, `/studies`) — with zero client code changes, since those pages already call the same unchanged endpoints.

### New information displayed

None — no new field is added to any response; existing responses are served faster, not differently. Response bytes are contractually unchanged (byte-identity tests enforce this — see TC-8).

### New user actions

None.

### UI surface changes

None — no page, panel, or component is added or modified.

### Product surface delta

No visible product surface changes this iteration. The operator-observable delta is latency only: `GET /research/datasets` on the real corpus should measurably drop from the measured ~31.4s cold baseline toward sub-second once warm (TC-15) — this specific timing claim is `(operator-verified on the real corpus)` per goal.md's own tag, not part of the keyless automated gate.

### Blueprint conformance

No new surfaces — J-02 is a cross-cutting backend accelerator with no dedicated UI panel, exactly as `blueprint.md`'s Information Architecture table already registers it: "J-02 Verified-content store caches + durable dataset index | no dedicated UI panel — accelerates `GET /research/datasets` and all bar/dataset reads behind Structure + Studies | Structure / Studies (cross-cutting)." No nav change; no `blueprint.reapproval-requested` needed.

### Data-contract additions

None. The two accelerators this iteration ships — the in-process `bars.py`/`datasets.py` stat-keyed verified-content caches, and the durable `dataset_index.db` (`app/research/dataset_index.py`) — are already pre-registered VERBATIM in `runs/goal-session-fast_wall/state/blueprint.md`'s "Rebuildable accelerators" list (drafted at baseline from the interlude's own Product Shape section). This iteration introduces no NEW displayed value, no second computation path, and no second serving endpoint for any existing Data Contract row: `GET /research/datasets` stays the ONE endpoint, `datasets.py`/`bars.py` stay the ONE owners. Verified against the current `blueprint.md` field-for-field; no edit made this iteration (nothing to add).

## OUT OF SCOPE

- J-01 (`peek_strategy_comparison_report`, the not-computed panel, `edge_report_cache.py`'s `lookup`/`compute_and_publish`) — already shipped iter-1; this iteration removes its `dataset_store.list()` call's re-read cost as a transparent side effect, with **zero** code change to `edge_report.py`, `edge_report_cache.py`, or `structure/page.tsx`.
- J-03 (`level_change_points`, `basis_day_key`, `_StructureArmMemo`) — next journey per the dependency order.
- J-04 (`edge_report_compute.py`, the compute routes, the CLI warmer, the "Compute edge report" button).
- J-05 (`EdgeReportBacktestCache`, the `run_pair` provider seam, the process pool).
- J-06 (`setups_scan_cache.py`, `compute_setups`'s cache-key change from `id(config)` to a content hash) — explicitly depends on this iteration's new `BarStore.root` property but is its own journey, not started here.
- Any change to `DatasetStore.load_events()`'s or `.replay()`'s verification LOGIC itself — both continue to fully re-verify on every call, exactly as today; this iteration adds no bypass, no shortcut, and no new parameter to either method.
- Any change to `bar_index.py` (era-5's existing store-first bar-recording lookup index) — untouched, unrelated cache.
- Any change to `setups.py`'s `_SCAN_CACHE` or `compute_setups`'s cache key — that is J-06's scope.
- Any real-corpus recording, credential work, or new dataset/bar-series registration.
- Any UI change to `/structure` or `/studies` — no dedicated panel this iteration.
- Any new `Config` field or new runtime dependency (stdlib `sqlite3` only, the `bar_index.py` precedent).
- Deleting or weakening any existing test in `test_bars.py`, `test_datasets.py`, or `test_bar_index.py`.

## DEFINITION OF DONE

- [ ] J-02 passes via automated backend verification (no browser-qa dispatch — `Frontend Present: no`): TC-1 through TC-12 all hold.
- [ ] TC-1 through TC-3 hold: `bars.py`'s stat-keyed cache serves zero-read warm hits (per-id and per-list), and still detects tampering (`BarSeriesIntegrityError`) after a warm read once a file's stat changes.
- [ ] TC-4 holds: `datasets.py`'s metadata-only cache reports a tampered file in `list()`'s `errors` return, never as cached-valid metadata.
- [ ] TC-5 holds: the ~2s racy-write guard refuses to cache a freshly-written file on either store.
- [ ] TC-6 holds: `BarStore.get`/`list` serve per-call row copies — a caller mutation never leaks into a later cached read.
- [ ] TC-7 holds: `DatasetStore.load_events`/`replay` fully re-verify on every call even when the metadata cache is warm (the trust boundary never weakens — the critical anti-goal's mechanical proof).
- [ ] TC-8 holds: `GET /research/datasets` cache-hit responses are byte-identical to cleared-cache responses, both REST and the MCP `datasets` proxy (run standalone and in the full suite per the applied lesson).
- [ ] TC-9 and TC-10 hold: a fresh `DatasetStore` (simulated restart) serves `list()` metadata from the durable `dataset_index.db` with zero content re-reads, byte-identical to a from-scratch verified list; deleting the index DB costs exactly one re-verify pass per file and repopulates it.
- [ ] TC-11 holds: `BarStore.root` is a public, read-only property.
- [ ] TC-12 holds: the new autouse conftest reset fixture prevents cross-test cache leakage on both stores.
- [ ] TC-13 holds: the full backend unit/integration suite passes with zero failures and zero newly-skipped/deleted tests, and `config.config_fingerprint()` still equals `4d665603569b9dbf`.
- [ ] TC-14 holds (Required-still-passing J-01): the edge-report integrity-error 500 path is unaffected by the new caches.
- [ ] Required-still-passing journeys J-01, J-07 remain green (deterministic replay of stored golden scripts; LLM fallback for either journey if no golden is on file).
- [ ] No anti-goal violation introduced — specifically the critical "verification trust boundary never weakens" and "no divergent accelerator output" anti-goals (TC-3/4/6/7/8/9/10 are the mechanical proof); the coherence-auditor confirms `dataset_index.db` and the two in-process caches stay rebuildable accelerators with a single owner each, matching `blueprint.md`'s pre-registered rows exactly.
- [ ] TC-15 recorded as supplementary operator-verified evidence if the real corpus is available in the dev/QA environment — encouraged, NOT a blocking DoD item (mirrors iter-1's own non-blocking treatment of its real-corpus timing claim).
- [ ] Dev handoff written at `docs/handoffs/goal-fast_wall-iter-2-dev.md`.

## TESTING REQUIREMENTS

- Browser: none. J-02 ships no UI surface (goal.md tags it "(Keyless; automated.)"; `blueprint.md`'s IA table registers no dedicated panel for it). Required-still-passing J-01 (`/structure` not-computed panel) and J-07 (regression sentinel screenshots) are covered by deterministic replay of their stored golden scripts from iter-1's UI test run, at the full pipeline's browser-qa step — no new browser-qa dispatch needed since neither journey's UI surface changes this iteration.
- Unit/integration: `bars.py`'s new stat-keyed cache (`get`/`list`/`load_bars`, the racy-write guard, the tamper-after-warm-read path, row-copy isolation, `BarStore.root`); `datasets.py`'s same cache scoped to `get()`/`list()` only, with `load_events()`/`replay()` proven to bypass it entirely; the new `dataset_index.py` (insert/lookup-on-restart/rebuild-on-deletion, mirroring `test_bar_index.py`'s structure); `routes.py`'s `get_dataset_store` dependency resolving `TAPEOLOGY_DATASET_INDEX_DB`; the new autouse conftest cache-reset fixture; the MCP `datasets` proxy byte-identity in the warm-cache state (`test_mcp_server.py`, run both standalone and inside the full suite per the applied lesson).
- Error cases: a tampered bar/dataset file (content changed post-warm-read) must raise/report the existing `BarSeriesIntegrityError`/`DatasetIntegrityError` — never served stale, never silently dropped; a file written and re-read inside the ~2s racy window must never be served from cache; deleting `dataset_index.db` must never raise or lose a dataset (exactly one full re-verify pass per file, no data loss).

Test-first contract:

- TC-1: given `BarStore.get(bar_series_id)` has already verified and served file X once (its stat unchanged since), when `get(bar_series_id)` is called again for the same id, then a file-read counting spy records 0 additional reads of file X and the returned dict is unchanged.
- TC-2: given `BarStore.list()` has already verified and served N healthy bar-series files once (their stats unchanged since), when `list()` is called again with the directory's files unchanged, then the spy records 0 reads across all N files.
- TC-3: given `BarStore.get(bar_series_id)` has already served a warm-cached read of file X, when file X's on-disk bytes are corrupted (so its stat changes and its checksum no longer matches) and `get(bar_series_id)` is called again, then it raises `BarSeriesIntegrityError` — never serving the stale-good or the tampered value from cache.
- TC-4: given `DatasetStore.list()` has already served a warm-cached metadata read for dataset Y, when dataset Y's on-disk bytes are corrupted (stat changes, checksum mismatch) and `list()` is called again, then dataset Y appears in the returned `errors` list and NOT in the healthy `records` list.
- TC-5: given a bar-series (or dataset) file is written to disk and read once via `get`/`list` within the ~2s racy-write window, when a second `get`/`list` call for the same id happens still inside that window with the file's bytes unchanged, then the spy records a real read on the second call too (the racy-write guard refuses to cache a freshly-written file).
- TC-6: given `BarStore.get(bar_series_id)` returns a dict and the caller mutates its `bars` list in place, when `get(bar_series_id)` is called again immediately after (a warm-cache hit), then the newly returned dict's `bars` content equals the original, unmutated value.
- TC-7: given `DatasetStore.get()`/`list()` have already warm-cached dataset Z's metadata, when `DatasetStore.load_events(Z)` or `DatasetStore.replay(Z, config)` is called, then a file-read counting spy proves dataset Z's full content is re-read and both checksums recomputed on that call.
- TC-8: given a populated dataset registry and a warm `datasets.py` metadata cache, when `GET /research/datasets` is called once warm and once immediately after the test-only reset helper forces a fresh full-verify pass, then the two raw HTTP response bodies are byte-identical, and the MCP `datasets` tool's proxied response byte-equals the warm REST response.
- TC-9: given a `DatasetStore` process has verified and registered N datasets with `dataset_index.db` fully populated, when a BRAND NEW `DatasetStore` instance (fresh in-process cache, same `dataset_dir` and `index_db_path`, simulating a backend restart) calls `.list()`, then a counting spy records 0 reads of the underlying `.json` dataset files, and the returned records are byte-identical (`json.dumps(sort_keys=True)` equality) to a from-scratch, index-free `.list()` call.
- TC-10: given a populated `dataset_index.db` is deleted from disk while all `.data/datasets/*.json` files remain intact, when a fresh `DatasetStore` (same `index_db_path`) calls `.list()`, then the call succeeds with no exception, each of the N dataset files is fully re-verified exactly once (spy records N reads), and `dataset_index.db` exists again afterward with N rows.
- TC-11: given a `BarStore` constructed with root path R, when `.root` is accessed, then it returns R's resolved path (a public, read-only property; no prior public accessor existed for this).
- TC-12: given two independent tests each construct a `BarStore`/`DatasetStore` under different `tmp_path` roots and register distinct content, when the new autouse conftest fixture runs between them, then the second test's first `get`/`list` call for its own fresh content is a real cache miss (spy records a nonzero read) — no state leaks from the first test's module-level cache.
- TC-13: given the full backend unit/integration suite runs after this iteration's changes, when it completes, then 0 tests fail, 0 pre-existing tests are newly skipped or deleted, and `config.config_fingerprint()` still equals `4d665603569b9dbf`.
- TC-14: given a dataset store whose `list()` reports an integrity error (an unrelated corrupt file present in the registry), when `GET /research/edge-report` (J-01's unchanged route) is called, then the response is still HTTP 500 with "integrity" present in `detail` — proving the new metadata cache never masks an integrity error inside `peek_strategy_comparison_report`'s `_verified_records` call.
- TC-15 *(operator-verified on the real corpus, non-blocking)*: given the real operator corpus (18 datasets, 882MB) with a warm `datasets.py` cache and a populated `dataset_index.db`, when `GET /research/datasets` is timed, then it completes in under 1 second — down from the measured 31.4s cold baseline.

## NOTES

- **Codebase probe (this iteration, decompose time):** confirmed `dataset_index.py`, the `TAPEOLOGY_DATASET_INDEX_DB` env var, and `BarStore.root` do not exist anywhere in the repo yet (fresh build; matches `blueprint.md`'s baseline probe comment). `edge_report.py:513` (`_verified_records`) and `edge_report_cache.py:159-172` (`_cache_key`) both call `dataset_store.list()` on EVERY `GET /research/edge-report`, warm or cold — confirming this iteration closes the gap iter-1's own NOTES flagged ("that finish line is J-02's, layered on top"). `routes.py:1550-1561` (`get_bar_index`) is the exact env-else-sibling dependency shape to mirror for the new `dataset_index.db` resolver; `bar_index.py` (the full file) is the "derived, rebuildable, owns nothing" shape precedent for the new module; `setups.py:369-409` (`_SCAN_CACHE`) is the module-level atomic-tuple-publish + read-local-reference-before-inspect precedent the two new in-process stat-keyed caches must follow — a module global, not `EdgeReportCache._hot`'s instance-scoped shape, since `BarStore`/`DatasetStore` are constructed fresh per FastAPI dependency call and have no natural long-lived instance to hang a cache off.
- **Lessons applied:** see BACKGROUND (`lessons.md` iter-1's `test_mcp_server.py` order-coupling entry — TC-8 extends `test_datasets_tool_byte_identical_on_a_non_empty_live_list` in that file).
- **No assumption-ledger entry logged this iteration:** `docs/goal.md`'s J-02 steps are fully prescriptive (exact schema, exact env var name, exact property name, exact acceptance clauses). The one open implementation detail — precisely when the durable index gets written to (opportunistically on every full-verify miss vs. only via a separate explicit publish step) — is ordinary developer-level scoping, not a goal-interpretation ambiguity: either shape satisfies every stated acceptance clause (TC-9, TC-10) identically, so nothing here rises to the assumption-ledger bar.
- **No blueprint edit:** `blueprint.md`'s existing "Rebuildable accelerators" rows already register both new caches and `dataset_index.db` verbatim (drafted at baseline from the interlude's own Product Shape section); verified field-for-field against this iteration's plan — unchanged.
- **Real-corpus timing (TC-15):** encouraged supplementary evidence, explicitly non-blocking per goal.md's own "(operator-verified on the real corpus)" tag — mirrors iter-1's identical treatment of its own real-corpus timing claim. Do not fail the iteration solely because the real 882MB corpus is unavailable in a given execution environment; the keyless TC-1 through TC-14 suite is the blocking gate.

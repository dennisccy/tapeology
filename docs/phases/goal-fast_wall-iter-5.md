# Goal Iteration 5 — Close J-04's browser gap, then J-05 The sweep becomes resumable and parallel

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04, J-05
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07 (the full `passing` set in `journey-history.json` — mirroring iter-2/3/4's identical reasoning). J-01 and J-07 share THIS iteration's own re-verification pass: both are re-confirmed in the SAME scoped browser session this iteration uses to capture J-04's still-missing screenshot (TC-1/TC-2). J-02's `dataset_store.list()`/verified-content caches are read on every sweep this iteration triggers (unaffected, zero diff expected). J-03's `_StructureArmMemo` is exercised again, at greater volume, by every backtest the new process-pool workers run (unaffected — only a NEW caller pattern reads it, never a modification).
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

Close J-04's last gap with zero new product code (a browser screenshot of the already-shipped "Compute
edge report" click-through), and make the sweep itself genuinely resumable (a killed-and-retriggered run
skips already-finished dataset×strategy pairs) and parallel (a CLI process pool) — so the first-ever
completed real edge report costs minutes, not "never."

## BACKGROUND

`eval.md`'s iter-4 Next-Step Recommendation is explicit and two-part: "FIRST re-run browser-qa for J-04
(TC-15/TC-16)... A single passing screenshot flips J-04 `partial → passing` with **no new code**...
THEN build J-05..., next per the dependency order." iter-4's `coherence.md` was `COHERENCE-PASS` (rule 2
N/A — no consolidation owed). No journey has regressed (rule 1 N/A) — J-04 is `partial`, not
`regressed`: its backend/API/CLI acceptance is fully proven (121 targeted tests, audit-run CLI,
curl-exercised lifecycle); only the REQUIRED browser leg has no screenshot, an environmental Chrome MCP
failure reproduced first-hand by four independent agents last iteration, not a product defect. Per the
priority rubric, J-04's remaining gap is the clearest possible "smallest spec wins ties" pick (rule 4)
— it costs ZERO new product code, so re-attempting it either resolves the gap outright or, at worst,
reproduces the same environmental blocker with no wasted dev effort. J-05 is the rubric's unblocker
(rule 3): it is the ONLY piece standing between this interlude and Success Criteria #4 ("The first full
real edge report completes... resumable... and parallel"), and it gives the already-built-but-INERT
`sub_cache=`/`workers=` hooks (J-04, forward-declared under a logged assumption) their real effect.
Bundling J-04's re-verification with J-05's build does NOT violate rule 5 ("never bundle two risky
journeys"): J-04 carries zero code risk this iteration (pure re-verification of already-shipped,
already-reviewed code), so J-05 remains the ONLY risky change set in this diff — exactly the shape
eval.md's own recommendation proposes. J-06 (`setups_scan_cache.py`) is deliberately NOT co-picked —
independent of J-05, and rule 5 still counsels against a third concurrent change set.

**Depth = full**, citing eval.md's own recommendation directly ("Full depth is warranted: J-05 modifies
the SAME `_split_cells`/`run_strategy_comparison_report` J-04 just touched, over frozen foundations, and
needs the audit/coherence/byte-identity backstop") plus the "Picking depth" rubric's own triggers (prior
verdict was `CONTINUE`, not `ESCALATE`, so full is not mandatory by that rule alone — independently
justified here): J-05 adds a NEW durable data model (`EdgeReportBacktestCache`, an eight-part composite
key), introduces this codebase's FIRST `ProcessPoolExecutor`/multiprocessing usage anywhere in
`apps/backend/app`, and modifies shared sweep plumbing that THREE currently-passing journeys (J-01,
J-03, J-04) all read through. It "requires new tests beyond browser smoke": a key-busting matrix (eight
independently-tested components), a kill-and-resume run-count spy, a non-vacuous parallel/sequential
byte-identity equivalence test, and a cache-loss recompute test. The audit + coherence + closure lanes
are the warranted backstop a lean reviewer-only cycle cannot provide for a change of this shape.

**Lessons applied:**
- iter-0's / iter-4's lesson (browser-QA of any Edge-Report-triggering flow must run against a SCOPED
  backend/frontend pair — ports 8391/3391, fresh temp dirs, `TAPEOLOGY_DATASET_DIR` pointed at a small
  committed fixture such as `apps/backend/tests/fixtures/datasets_j03`, NEVER the default 882MB
  `.data/datasets` corpus) applies unchanged this iteration (see `reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s
  one-time setup for the exact commands). This iteration's scoped env must ALSO set
  `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` alongside the existing `TAPEOLOGY_EDGE_REPORT_CACHE_DB`, so J-05's new
  durable cache never touches `.data/` either.
- iter-4's lesson (a golden-replay "possible regression" FAIL must be checked against its OWN evidence
  screenshot before being trusted — a "Backend unreachable" render is an infra false-negative, not a
  regression) applies directly if this iteration's replay lane reports anything against J-01/J-02/J-03/
  J-07: open the screenshot first.
- iter-4's lesson (Chrome MCP "did not become ready on port 9222" was reproduced by four independent
  agents last iteration) means a SECOND consecutive failure this iteration is plausible and must NOT be
  treated as a new, unexplained blocker. Retry the identical scoped recipe in a fresh session; if it
  STILL fails, J-04 stays `partial` (never regresses to `failing` for an infra reason, per iter-4's own
  precedent) and the blocker is escalated to the operator exactly as eval.md iter-4 already flagged —
  this is NOT human-owned in the STALLED sense (rule 6 does not apply; a future healthy session resolves
  it with zero new code).
- iter-3's lesson ("the equivalence test passes" is not by itself sufficient evidence of "No divergent
  accelerator output" — demand a non-vacuous proof, e.g. a mutation/behavior probe) applies directly to
  J-05's TC-5 (the key-busting matrix must show each component INDEPENDENTLY busts a pair — a cache that
  silently ignored one key component would fail exactly that component's row) and TC-8 (the
  `workers=2` equivalence must be shown non-vacuous — a spy confirms multiple worker processes actually
  ran, not a silent sequential fallback).

## IN SCOPE

### Verification (zero code change)

- [ ] Re-run browser-qa against a FRESH scoped backend/frontend pair (the established ports 8391/3391
      recipe: fresh temp journal/dataset/bar dirs, `TAPEOLOGY_DATASET_DIR` at a small committed fixture,
      cold edge-report cache) in a healthy Chrome MCP session: click "Compute edge report," capture a
      screenshot showing the progress counts mid-run, and a screenshot of the terminal render (TC-1).
- [ ] In the SAME scoped session, capture J-01's not-computed-panel render (before the click) and J-07's
      broader `/structure` sections (Tradable Map, Case Studies, Registry, Comparison) rendering exactly
      as shipped (TC-2).
- [ ] Capture the failed-state render, with a `state: "failed"` snapshot arranged via a direct backend
      call before navigation (mirrors iter-4 QA's own precedent) (TC-3).

### Backend

- [ ] New `EdgeReportBacktestCache` (a new sibling module — e.g. `edge_report_backtest_cache.py` — or
      co-located inside `edge_report_cache.py`; developer's choice, either satisfies goal.md's "beside
      `EdgeReportCache`, same durable discipline"): one durable SQLite row per (dataset × strategy) pair.
      Key = sha256 of the canonical JSON of `{dataset_id, dataset_checksum, strategy_id, profile,
      config_fingerprint, config_content_hash, strategy_registry, bar_store_signature}` — reuse
      `edge_report_cache.py`'s `_canonical`/`_config_content_hash` verbatim (never re-derive them a
      second time); `bar_store_signature` reuses `setups._store_signature(bar_store)` verbatim (export it
      if needed — never re-derive the tuple shape), computed ONCE per sweep rather than once per pair.
      Values are the runner's own per-pair `result` block stored WITHOUT `sort_keys` (the
      `EdgeReportCache._insert` byte-identity discipline, applied to a per-pair row). Path resolution
      mirrors `resolve_cache_db_path`: env `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` else a
      `.data/edge_report_backtests.db` sibling of the dataset dir. `lookup(key)`/`publish(key, result)`
      methods, WAL + busy_timeout (the `JournalStore._read_conn` precedent).
- [ ] `apps/backend/app/research/edge_report.py`: `_split_cells` (currently `edge_report.py:405-481`)
      gains a `run_pair(dataset_meta, strategy_id)` provider seam defaulting to `None` — when `None`, the
      loop's behavior is byte-identical to today's inline `_run_backtest` call; the pooling/ordering/
      aggregation code below the call site stays untouched. `_ProgressReporter` (`edge_report.py:371-402`)
      distinguishes a sub-cache hit from a fresh compute so `backtests_from_cache` (already part of the
      emitted patch shape since J-04, currently always 0 — dead) genuinely increments on a hit.
      `run_strategy_comparison_report`/`_compute_strategy_comparison_report` build the caching `run_pair`
      provider whenever `sub_cache` is supplied (the SAME provider/cache instance serves BOTH the train
      and hold-out `_split_cells` calls). `sub_cache=`/`workers=` stop being INERT — the J-04 assumption
      they were forward-declared under is now resolved for `sub_cache=` everywhere it is supplied, and
      for `workers=` specifically inside the CLI's own orchestration (see below and NOTES).
- [ ] The parallel provider (CLI-only this iteration — see NOTES for the button-path scope decision): a
      `ProcessPoolExecutor` with the `spawn` context; task = one dataset (all three strategies),
      largest-first (LPT) scheduling by event count; `workers` resolved from `--workers N` (CLI flag,
      default read from env `TAPEOLOGY_EDGE_SWEEP_WORKERS` else the existing `_DEFAULT_WORKERS = 4`
      constant; documented ceiling ~6). Each worker builds its own stores from explicit paths, uses a
      throwaway temp journal DB for job bookkeeping (the report never references backtest ids), and
      publishes each completed pair to the durable sub-cache the moment it finishes; the orchestrating
      process then reassembles via the SAME untouched `_split_cells`/`run_pair` sub-cache-hit path —
      reassembly is byte-identical to a sequential run BY CONSTRUCTION (the aggregation code never
      changed). Cancellation stops submitting new tasks and lets in-flight tasks persist their pairs.
- [ ] `apps/backend/app/research/edge_report_compute.py`: the CLI's `main()` constructs a real
      `EdgeReportBacktestCache` (via the new resolver) and passes `sub_cache=<cache>` alongside the
      already-passed `workers=args.workers` into `run_strategy_comparison_report`.
      `EdgeReportComputeManager.trigger()` (`edge_report_compute.py:116-181`) gains a new keyword-only
      `sub_cache: EdgeReportBacktestCache | None = None` parameter (default `None` preserves every
      existing caller/test byte-for-byte) and threads it into its own `run_strategy_comparison_report`
      call inside `_work()` — making a browser-triggered compute resumable too. `trigger()` NEVER passes
      `workers` above `1`/`None` (process-pool parallelism stays CLI-only this iteration; see NOTES —
      this is a logged assumption).
- [ ] `apps/backend/app/research/routes.py`: a new `get_edge_report_backtest_cache()` dependency resolver
      (the `get_edge_report_cache` precedent, same file), threaded into `trigger_edge_report_compute` so
      the manager's `trigger()` call receives a real `sub_cache` — no second store/cache construction
      path.
- [ ] New/updated tests: a new test module for `EdgeReportBacktestCache` (key-busting matrix, WAL
      durability, cache-loss recompute); `test_edge_report.py` additions (`run_pair` default-equivalence,
      kill-and-resume spy, new-dataset-costs-exactly-three); `test_edge_report_compute.py` additions (CLI
      `workers=2` byte-identity + multi-process spy, manager `sub_cache` wiring/resumability, the
      "manager never passes `workers>1`" guard); the existing `test_backtests.py:1500-1508`/`:932-943`
      and `test_setups.py:995-1017`/`:758-771` source-introspection guards, plus
      `test_advertised_tool_set_is_exactly_capability_6` (`test_mcp_server.py`), re-run byte-unmodified.

### Frontend (if applicable)

- [ ] None planned. `Frontend Present: yes` is set solely to force the UI Impact / UI Test Design /
      Browser QA / UX Regression lanes to run this iteration against the EXISTING, already-shipped
      `/structure` button/panel (`structure/page.tsx`, unchanged since iter-4) — the goal is capturing
      J-04's still-missing screenshot, not shipping new frontend code. A cold click's visible behavior is
      unaffected by J-05's sub-cache wiring: a cold sub-cache looks identical to no sub-cache on a fresh
      scoped session's FIRST run (nothing is cached yet either way).

### New user-facing capability

None new. J-05 accelerates the EXISTING "Compute edge report" button invisibly — a re-triggered compute
now survives a kill without redoing already-finished pairs, and the CLI warmer's `--workers N` genuinely
parallelizes instead of silently accepting-and-ignoring the flag. J-04's capability (already shipped)
becomes fully VERIFIED rather than partially verified.

### New information displayed

None new. The compute snapshot's `progress.backtests_from_cache` field — already rendered inside the
panel since iter-4 — starts reporting genuine nonzero counts on a resumed run instead of always reading
0.

### New user actions

None new — the existing "Compute edge report" button is byte-unchanged.

### UI surface changes

None — `/structure`'s Edge Report section is byte-unchanged this iteration.

### Product surface delta

Invisible on a fresh click (a cold scoped session looks identical to before). Visible only to an
operator who kills and re-triggers a compute (the resumed run finishes faster) or runs the CLI warmer
with `--workers N > 1` (now genuinely parallel instead of a silently-ignored flag).

### Blueprint conformance

No new surface. `/structure` → Edge Report section stays J-04's already-registered home (unchanged this
iteration). `EdgeReportBacktestCache`/`edge_report_backtests.db` was ALREADY pre-registered in
`blueprint.md`'s "Rebuildable accelerators" list at baseline — this iteration builds it; I refined that
bullet's detail (exact key composition) directly in `runs/goal-session-fast_wall/state/blueprint.md`
this iteration (additive documentation only; no nav-skeleton change, so no `blueprint.reapproval-requested`
file was written).

### Data-contract additions

None new. `EdgeReportBacktestCache` is explicitly a rebuildable accelerator (blueprint.md's own
"explicitly NOT canonical values" framing) — no UI/REST/MCP surface reads it directly; only
`run_strategy_comparison_report`'s own internals do. The compute-job snapshot's
`progress.backtests_from_cache: int` field is UNCHANGED shape (registered since iter-4) — this iteration
only makes its runtime VALUE genuinely meaningful; same single owner (`edge_report_compute.py`), same
single endpoint (`GET /research/edge-report/compute`), no second derivation, no second endpoint.

## OUT OF SCOPE

- J-06 (`setups_scan_cache.py`) — independent of J-05; a separate future iteration.
- Wiring `workers > 1` (genuine multi-process parallelism) into `EdgeReportComputeManager.trigger()`/the
  button path — a logged assumption (see NOTES and `assumptions.md`); process-pool execution is CLI-only
  this iteration. Reversible with no signature-breaking change later.
- Running the CLI warmer to completion against the FULL real corpus and appending the completed
  three-way comparison to `reports/pnl/pnl-history.md` (goal.md J-04 step 5 / Success Criteria #4's
  pnl-history close) — remains explicitly *(operator-verified on the real corpus)*, attempted only as
  bonus, non-blocking evidence if time/CPU budget allows; never required for this iteration's Definition
  of Done, matching iter-4's own established framing exactly. J-05 makes this leg CHEAPER when it does
  eventually run, but does not itself run it.
- Any change to `levels.py` or `tradability.py` (J-03's memo internals) — untouched; consumed at greater
  volume by the new process-pool workers, never modified.
- Any change to `bars.py`, `datasets.py`, or `dataset_index.py` (J-02's owned files) — unaffected, zero
  diff expected.
- Any change to `app/mcp/__init__.py` or any new MCP tool — the compute/sweep surface stays REST +
  CLI-only, per the critical "No MCP write surface" anti-goal.
- Any change to `EdgeReportCache`'s existing `get_or_compute`/`lookup`/`compute_and_publish` method
  BODIES — untouched; `EdgeReportBacktestCache` is a NEW, separate class/cache, never a modification of
  the existing whole-report cache.
- Any new `/structure` UI element for J-05 itself — the existing button/panel is byte-unchanged; its
  underlying compute becomes resumable invisibly.
- Any new `Config` field or runtime dependency beyond stdlib `sqlite3`/`concurrent.futures`/
  `multiprocessing` — `config_fingerprint` stays `4d665603569b9dbf`.
- Deleting or weakening any existing test in `test_edge_report.py`, `test_edge_report_compute.py`,
  `test_edge_report_api.py`, `test_backtests.py`, `test_setups.py`, or `test_mcp_server.py`.

## DEFINITION OF DONE

- [ ] J-04 flips to `passing` via a browser-qa screenshot capturing the full click → progress →
      terminal-state cycle, against a SCOPED fixture backend, with zero new product code (TC-1).
- [ ] J-01's not-computed panel and J-07's broader `/structure` regression sentinel re-verified in the
      SAME scoped browser pass (TC-2).
- [ ] J-04's failed-state render re-verified (TC-3).
- [ ] `EdgeReportBacktestCache` durably persists one row per (dataset × strategy) pair; a fully-cached
      sweep's report is byte-identical to an uncached compute of the same inputs (TC-4).
- [ ] Each of the key's eight components independently busts a pair — a non-vacuous proof (TC-5).
- [ ] A killed-and-resumed sweep computes only the missing pairs; `backtests_from_cache` is genuinely
      nonzero and matches the count of pairs served from cache (TC-6).
- [ ] Recording one additional dataset costs exactly three fresh backtests, zero for every pre-existing
      dataset (TC-7).
- [ ] A `workers=2` parallel CLI report is byte-identical to a sequential one, and the equivalence is
      proven non-vacuous by a multi-process spy (TC-8).
- [ ] Deleting the sub-cache DB is harmless — full recompute, byte-identical output (TC-9).
- [ ] The CLI warmer's published sub-cache rows are genuinely reusable by a subsequent bare function call
      (TC-10).
- [ ] `EdgeReportComputeManager.trigger()` threads a real `sub_cache`, proven resumable (TC-11), while
      never invoking `workers > 1` itself (TC-12) — the documented, reversible scope call.
- [ ] The hooked path stays byte-identical whether or not a `sub_cache` is supplied (TC-13).
- [ ] No anti-goal violation introduced — specifically "No divergent accelerator output," "Accelerators
      are never sources of truth," "No compute on page load," "No source-guard weakening," "No MCP write
      surface," and "Frozen foundations" (TC-14).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-07 remain green (replay + LLM fallback,
      mechanically verified).
- [ ] Unit tests pass; no regressions; full suite green; `config_fingerprint` still `4d665603569b9dbf`.
- [ ] Dev handoff written at `docs/handoffs/goal-fast_wall-iter-5-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-04's live compute cycle and the failed-state render (TC-1, TC-3), both against a SCOPED
  backend/frontend pair (never the default `.data/datasets` real corpus). Required-still-passing J-01
  and J-07 re-verified in the SAME browser pass (TC-2).
- Unit/integration: `EdgeReportBacktestCache`'s key composition, durability, and cache-loss recompute;
  `_split_cells`'s `run_pair` seam default-equivalence; the key-busting matrix (all eight components);
  the kill-and-resume run-count spy; the new-dataset-costs-exactly-three test; the CLI's `--workers 2`
  parallel-vs-sequential byte-identity + multi-process spy; the manager's `sub_cache` wiring and its
  "never passes `workers>1`" guard; the existing source-introspection and MCP tool-count guards re-run
  unmodified.
- Error cases: a sub-cache publish failure never blocks the sweep from completing and publishing the
  whole-report cache (the report itself is always correct even if a sub-cache row fails to persist); a
  corrupted/unreadable sub-cache DB is treated as a full miss (recompute), never a crash; a worker
  process that raises propagates as a genuine sweep failure (`state: "failed"`, `error` surfaced
  verbatim), never a silently-dropped pair.

Test-first contract:

- TC-1 (browser): given `/structure` is loaded against a SCOPED backend/frontend pair pointed at a small
  committed fixture dataset dir (never the default `.data/datasets`) with a cold edge-report cache, when
  the operator clicks "Compute edge report," then the panel's progress counts update at least once while
  `state === "running"` and, within 90 seconds of the click, the panel is replaced by either the existing
  `EdgeReportBody` render or the honest all-empty-cells state, with zero full-page reload.
- TC-2 (browser): given the SAME scoped session immediately after TC-1's completed compute, when the
  operator reloads `/structure`, then the Edge Report section renders the now-warm report directly (no
  not-computed panel, no button), and the Tradable Map / Case Studies sections and the Registry/
  Comparison banners render exactly as they did before this iteration.
- TC-3 (browser): given a compute snapshot already at `state: "failed"` with a known `error` string
  (arranged via a direct backend call before navigation), when `/structure` is loaded (or its poll tick
  fires), then the not-computed panel visibly renders that exact `error` string verbatim.
- TC-4: given the committed fixture dataset registry and a fresh, empty `EdgeReportBacktestCache` DB,
  when `run_strategy_comparison_report(..., sub_cache=<cache>)` runs to completion, then every eligible
  (dataset, strategy) pair is a durable row in the sub-cache DB, and the returned report is
  byte-identical (`json.dumps(..., sort_keys=True)`) to the SAME inputs computed with `sub_cache=None`.
- TC-5 (key-busting matrix, non-vacuous): given a warm sub-cache row for one (dataset, strategy) pair,
  when each of the eight key components in turn (`dataset_id`, `dataset_checksum`, `strategy_id`,
  `profile`, `config_fingerprint`, `config_content_hash`, `strategy_registry`, `bar_store_signature`) is
  independently changed and the SAME pair is re-requested, then a call-counting spy on `_run_backtest`
  records a NEW call for that pair for EVERY one of the eight mutations — proving each component
  independently busts the key (a cache silently ignoring one component would fail exactly that row).
- TC-6 (kill-and-resume): given a sweep that is aborted (via `should_abort`) partway through, having
  already durably published N pairs to the sub-cache, when the SAME sweep is re-triggered with the SAME
  `sub_cache`, then a call-counting spy on `_run_backtest` records fresh calls for ONLY the remaining,
  not-yet-cached pairs, and the progress snapshot's `backtests_from_cache` field equals N.
- TC-7 (new dataset costs three): given a fully-warm sub-cache for the existing fixture registry, when
  ONE additional dataset is registered and the sweep is re-triggered, then a call-counting spy records
  EXACTLY three new `_run_backtest` calls (one per registered strategy) for the new dataset, and zero
  calls for any pre-existing dataset.
- TC-8 (parallel equivalence, non-vacuous): given a fixture dataset registry with at least two datasets
  (e.g. `apps/backend/tests/fixtures/datasets`), when the sweep runs once sequentially (`workers=None`)
  and once via the CLI warmer with `--workers 2`, each against a FRESH empty sub-cache, then (a) the two
  resulting reports are byte-identical (`json.dumps(..., sort_keys=True)` equality), AND (b) a spy
  confirms at least two distinct worker process ids were used across the datasets' task assignments —
  proving the equivalence is not vacuously satisfied by a silent sequential fallback.
- TC-9 (sub-cache loss is harmless): given a fully-warm sub-cache DB, when the DB file is deleted and the
  sweep is re-triggered, then it completes a full recompute (every pair re-run, confirmed by the spy) and
  the resulting report is byte-identical to the original warm-cache report.
- TC-10 (CLI wiring reusability): given the committed fixture dataset registry and a cold sub-cache, when
  the CLI warmer (`python -m app.research.edge_report_compute`) runs, then it publishes durable rows to
  the resolved `TAPEOLOGY_EDGE_SWEEP_CACHE_DB` (or its sibling default path) that a subsequent bare
  `run_strategy_comparison_report(..., sub_cache=<the same cache path>)` call reads as 100% cache hits
  with zero fresh `_run_backtest` calls.
- TC-11 (manager resumability wiring): given `EdgeReportComputeManager.trigger()` is called once
  (completing normally, publishing to a durable sub-cache the route now injects) and, after a
  test-arranged partial abort of a second run over an overlapping dataset set, called again with the SAME
  `sub_cache`, when the second run completes, then its snapshot's `progress.backtests_from_cache` is
  greater than 0 — proving `trigger()` genuinely threads a real `sub_cache` through, not the `None`
  default.
- TC-12 (no-parallelism-in-the-manager guard): given `EdgeReportComputeManager.trigger()`'s call site,
  when the suite runs after this iteration's diff, then a test asserts `trigger()` never supplies a
  `workers` value greater than `1` to `run_strategy_comparison_report` (e.g. by capturing the kwargs of a
  monkeypatched `run_strategy_comparison_report` during a `trigger()` call) — process-pool parallelism
  stays CLI-only.
- TC-13 (byte-identity of the hooked path): given the SAME dataset registry/config, when
  `run_strategy_comparison_report` is called once via today's pre-J-05 shape (`sub_cache=None`) and once
  with a genuinely warm `sub_cache` supplied, then the two reports are byte-identical (`json.dumps(...,
  sort_keys=True)` equality).
- TC-14 (frozen foundations / no source-guard weakening): given the full backend suite after this
  iteration's diff, when it runs, then `test_backtests.py:1500-1508`/`:932-943` and
  `test_setups.py:995-1017`/`:758-771` (the source-introspection guards) and
  `test_advertised_tool_set_is_exactly_capability_6` (`test_mcp_server.py`, MCP tool count 18) all pass
  with byte-unmodified source, `config.config_fingerprint()` is still `4d665603569b9dbf`, and
  `levels.py`/`tradability.py`/`backtests.py`/`bars.py`/`datasets.py`/`dataset_index.py`/
  `app/mcp/__init__.py` are git-confirmed byte-unchanged vs the pre-iteration working tree.

## NOTES

- **Codebase probe (this iteration, decompose time):** confirmed `EdgeReportBacktestCache`/
  `edge_report_backtests.db` does not exist anywhere yet. `_split_cells` (`edge_report.py:405-481`) calls
  `_run_backtest` directly inline, no `run_pair` seam. `_ProgressReporter.pair_done()`
  (`edge_report.py:397-402`) already emits a `backtests_from_cache` field in its patch but NEVER
  increments it (dead, always 0 since J-04). `run_strategy_comparison_report`'s `sub_cache=`/`workers=`
  keyword params (`edge_report.py:544-545`) exist since J-04 but are accepted-only —
  `EdgeReportComputeManager.trigger()` (`edge_report_compute.py:116-181`) does not pass either into its
  own `run_strategy_comparison_report` call, and the CLI's `main()` (`edge_report_compute.py:244-299`)
  passes `workers=args.workers` but never `sub_cache=`. No `ProcessPoolExecutor`/`multiprocessing` usage
  exists anywhere in `apps/backend/app` yet (only an unrelated `ThreadPoolExecutor` in
  `providers/adapters/alpaca.py`). `setups._store_signature` (`setups.py:372-383`) is the confirmed
  existing bar-store-signature precedent this iteration reuses, never re-derives. The full backend suite
  ran clean (all-dots, zero failures, exit 0) at decompose time, confirming the iter-4 baseline (1489
  passed / 7 skipped per eval.md) is intact going into this iteration.
- **Assumption logged this iteration:** one new entry in `runs/goal-session-fast_wall/state/
  assumptions.md` (`## iter-5 — goal-decomposer`) — the CLI-only-vs-manager-too scope call for genuine
  `workers > 1` process-pool parallelism (goal.md's "CLI/background job" phrasing is read conservatively
  to exclude the manager's own background thread, keeping multiprocessing out of the always-on backend
  process this iteration); `sub_cache=` resumability, by contrast, IS wired into both entry points since
  it introduces no new concurrency primitive and directly serves the already-displayed
  `backtests_from_cache` UI field. Reversible with no signature-breaking change later.
- **Implementation hint (non-binding):** one clean way to give `_split_cells` its `run_pair` seam without
  widening the 2-arg `run_pair(dataset_meta, strategy_id)` shape goal.md names: build the caching
  provider as a closure over the SAME `reporter`/`cache` the enclosing `_compute_strategy_comparison_report`
  call already has in scope, so a cache hit can notify the reporter (incrementing `backtests_from_cache`)
  from inside the closure itself, rather than widening `run_pair`'s return shape or its argument list.
  Compute `bar_store_signature` once, outside the pair loop, and close over it — never re-derive it once
  per pair (the exact wasteful-recomputation pattern this whole interlude exists to remove).
- **Scope discipline:** this diff should touch `edge_report.py`, `edge_report_compute.py`, `routes.py`,
  one new cache module, and their test files — no `levels.py`, `tradability.py` (J-03's owned files), no
  `bars.py`/`datasets.py`/`dataset_index.py` (J-02's owned files), no `edge_report_cache.py` method-body
  change (only imports reused), no `app/mcp/__init__.py`, and no frontend file. Any wider diff is a
  signal scope has leaked into J-06 territory or beyond.
- **If Chrome MCP again fails to start:** do not block the rest of this iteration. J-05's TC-4 through
  TC-14 are fully keyless/automated and must still be delivered and evaluated on their own evidence; J-04
  stays `partial` (not `failing`, not `regressed`) exactly as it did in iter-4, and the environmental
  blocker is escalated to the operator again, per eval.md iter-4's own flag.

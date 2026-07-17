# Goal Iteration 4 — J-04 The operator-run compute (button, background job, CLI warmer)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 4
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-07 (these are the ONLY four `passing` journeys in this session's `journey-history.json` — the full regression set, mirroring iter-2's and iter-3's identical reasoning. J-01 shares THIS iteration's own surface: the SAME `/structure` Edge Report section and the SAME not-computed-payload `compute` field, which flips from always-`null` to a real snapshot — a shape-compatible extension per the iter-1 assumption ledger, never a shape change; the frozen "Edge report not computed yet." headline/detail/register/`dataset_count` rendering must stay byte-unchanged when no compute has ever run. J-02's `dataset_store.list()`/verified-content caches are read on every compute trigger — a new, repeated caller pattern — but are themselves untouched. J-03's `_StructureArmMemo` gets its FIRST real-scale exercise the moment a genuine sweep runs — previously inert per iter-3's own BACKGROUND ("the memo is inert to every CURRENT UI surface... J-04's compute trigger... is the only thing that will actually exercise structure_tape/structure_tape_map at scale"). J-07 is the regression sentinel, and this is the first live `/structure` browser interaction since J-01 closed the cold-GET hazard — the FIRST real click-through this session.)
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

The operator can trigger the first-ever completed edge-report compute directly from `/structure` — a
single-flight, cancellable, progress-reporting background job (a "Compute edge report" button plus a
CLI warmer) that never starts on any GET — and watch it reach a real report or an honest failure
without leaving the page.

## BACKGROUND

Iter-3's `eval.md` explicitly recommends building **J-04 next** ("per goal.md's dependency order
(J-01 → J-02 → J-03 → J-04 → J-05), now unblocked by J-03's memo"); iter-3's `coherence.md` was
`COHERENCE-PASS` (rule 2 N/A — no consolidation owed). No journey has regressed (rule 1 N/A). J-04 is
the priority-rubric unblocker (rule 3): it is the ONLY piece standing between this interlude and its
own stated purpose — "the first-ever completed real edge report" (Success Criteria #4) — and every
piece it depends on is now in place (J-01's cache split, J-02's verified-content caches, J-03's arm
memo that makes a real sweep tractable instead of ≥400× too slow). J-05 (`EdgeReportBacktestCache`,
the `run_pair` provider seam, the process pool) and J-06 (`setups_scan_cache.py`) are deliberately NOT
co-picked: rule 5 (never bundle two risky journeys) forbids it, and J-05 in particular modifies the
SAME `_split_cells` function this iteration also touches — sequencing them separately keeps any
browser-QA/audit failure attributable to one change set. J-04 is therefore the ONE risky journey this
iteration; rule 4 (smallest spec wins ties) does not apply since J-04 has no smaller-scoped sibling
ready per the dependency order, and rule 6 (don't pick a human-blocked journey) does not apply — J-04's
mandatory acceptance is entirely keyless/fixture-based (goal.md tags it "(Keyless via fixtures;
browser-verifiable.)"); only its BONUS real-corpus leg is operator-gated (see OUT OF SCOPE).

**Depth = full**, citing the eval.md iter-3 recommendation directly plus the "Picking depth" rubric's
own triggers (prior verdict was `CONTINUE`, not `ESCALATE`, so full is not mandatory by that rule alone
— it is independently justified here): J-04 is `Frontend Present: yes` and genuinely "crosses
backend+frontend boundaries" — a new backend module (`edge_report_compute.py`), three new REST routes,
a CLI warmer, AND a real, browser-clickable "Compute edge report" button with live progress. It carries
the interlude's headline CRITICAL anti-goal — "No compute on page load — operator-run only" — facing
its first genuine trigger SURFACE (until now there was nothing to trigger); it also carries the
critical "No MCP write surface" anti-goal at its highest-risk point, since the new REST surface sits
directly beside the MCP-proxied `edge_report` tool. It "requires new tests beyond browser smoke":
single-flight, cancel, force, failed-state, and a new hooks-equivalence test. The audit + coherence +
ux-regression + closure + browser-qa lanes are the warranted backstop a lean reviewer-only cycle cannot
provide for a new operator-facing compute surface over frozen foundations.

**Lessons applied:**
- iter-0's lesson (browser-QA of `/structure` against the DEFAULT real-corpus backend is an active CPU-
  pin hazard) now applies to a NEW surface: until this iteration, the hazard was a page GET; from this
  iteration on, it is also a REAL button click that starts a genuine sweep. Browser-QA of the "Compute
  edge report" flow MUST use the SAME scoped backend/frontend recipe iter-1's dev already established
  and documented (`docs/handoffs/goal-fast_wall-iter-1-dev.md`: fresh temp journal/dataset/bar dirs,
  backend port 8391 / frontend port 3391, `TAPEOLOGY_DATASET_DIR` pointed at a small committed fixture
  such as `apps/backend/tests/fixtures/datasets_j03` (1 dataset) or `apps/backend/tests/fixtures/datasets`
  (2 datasets)) — NEVER the default `.data/datasets` (882MB, 18 datasets, the exact corpus the Vision
  measured as "could not finish in 9.3 minutes"). Clicking the button against the default corpus this
  iteration would reproduce the very hazard the interlude exists to remove, just moved one click deeper.
- iter-3's lesson ("the equivalence test passes" is not by itself sufficient evidence of "No divergent
  accelerator output" — demand a non-vacuous proof, e.g. a mutation/behavior probe) applies directly to
  this iteration's new keyword-only hooks on `run_strategy_comparison_report`: TC-14 below requires
  showing the hooked path is byte-identical to the default path when UNUSED, and that a `should_abort`
  that DOES fire changes the observable outcome (no publish) — proving the hook is genuinely wired, not
  a decorative no-op that would pass even if silently ignored.

## IN SCOPE

### Backend

- [ ] New module `apps/backend/app/research/edge_report_compute.py`: `EdgeReportComputeManager` —
      **single-flight** (exactly ONE job slot at a time, a deliberately simpler shape than
      `StudyJobManager`/`BacktestJobManager`'s per-id dict, since there is only ever one "the edge
      report compute"), cooperative cancel via a `threading.Event` observed between dataset×strategy
      pairs, and an atomically-published progress snapshot (read-local-reference-before-inspect — the
      `EdgeReportCache._hot` / `setups.py` `_SCAN_CACHE` precedent) shaped exactly per the refined
      `blueprint.md` Data Contract row: `{id, state, force, started_utc, finished_utc, error,
      progress: {phase, backtests_total, backtests_done, backtests_from_cache, current}}`. A trigger
      while `state == "running"` returns the existing snapshot with `started: false` — never a second
      job. A cancelled or failed run publishes NOTHING to the edge-report cache (publish only after the
      compute function returns normally — see NOTES for one clean way to guarantee this by construction).
      Module `__all__` exports the manager class, mirroring `backtests.py`'s own `"BacktestJobManager"`
      convention.
- [ ] `apps/backend/app/research/edge_report.py`: add five additive keyword-only parameters to
      `run_strategy_comparison_report` — `force=False, progress=None, should_abort=None, sub_cache=None,
      workers=None` — every default reproducing today's EXACT byte-identical behavior. `force=False`
      (the default) keeps dispatching through `cache.get_or_compute` exactly as today; `force=True`
      dispatches through the ALREADY-SHIPPED `cache.compute_and_publish` (J-01) instead. `progress=`/
      `should_abort=` thread down to `_split_cells`/`_run_backtest`'s existing per-dataset×strategy loop
      as an optional reporting/cooperative-cancellation seam — no change to the loop's own
      ordering/pooling/aggregation code. `sub_cache=`/`workers=` are accepted this iteration but
      currently INERT (see NOTES — this is a logged assumption; J-05 gives them real effect). Rewire
      `peek_strategy_comparison_report`'s `compute` field to read the registry's compute-manager
      snapshot (replacing the always-`None` J-01 placeholder) — same key, same shape, no change for
      existing readers of a `null` value.
- [ ] `apps/backend/app/research/routes.py`: add a `registry.edge_report_compute` property (the
      `study_jobs`/`backtest_jobs` precedent, `ResearchRegistry.__init__` around line 246-250) and three
      new routes as subpaths of the existing `/research/edge-report` section: `POST
      /research/edge-report/compute` (body `{"force": bool = false}`, returns `{started: bool, compute:
      <snapshot>}`), `GET /research/edge-report/compute` (returns the snapshot or `null`), `POST
      /research/edge-report/compute/cancel` (409 when idle) — resolved through the SAME existing
      dependency seams (`get_registry`, `get_dataset_store`, `get_bar_store`, `get_edge_report_cache`),
      no second store/cache construction path. The EXISTING `get_edge_report` route body and its pinned
      `Depends(get_bar_store)`/`Depends(get_dataset_store)`/`Depends(get_edge_report_cache)`/
      `cache=cache` wiring (`test_edge_report_route_wired_through_the_existing_get_bar_store_seam`,
      `test_edge_report_route_wired_through_the_new_cache_dependency`) and the existing
      `test_non_get_verbs_are_405_no_write_surface_exists` guard stay byte-unmodified — the new routes
      are subpaths, so non-GET verbs on `/research/edge-report` itself are structurally unaffected.
- [ ] CLI warmer, `edge_report_compute.py`'s own `main()`/`if __name__ == "__main__"`: `python -m
      app.research.edge_report_compute --workers N [--force] [--out report.json]` (`--workers` default
      4, matching goal.md's usage string — see NOTES for the accepted-but-inert scoping this iteration),
      resolving the SAME env/config seams the backend reads (journal, dataset dir, bar dir, both cache
      DBs) — mirrors `edge_report.py`'s own `main()` CLI precedent (`edge_report.py:573`). Prints one
      progress line per completed backtest, exits `0` with a summary, and (per the inert-`workers`
      scoping) runs strictly sequentially regardless of the flag's value. The existing era-3 J-09
      `edge_report.main()` CLI stays byte-untouched.
- [ ] No change anywhere to `apps/backend/app/mcp/__init__.py` — `TOOL_NAMES`/`EXPECTED_TOOLS`
      (pinned by `test_advertised_tool_set_is_exactly_capability_6`, 18 registered tool names today)
      stay byte-unmodified; the compute surface is REST-only, per the critical "No MCP write surface"
      anti-goal.
- [ ] New/updated tests: `apps/backend/tests/test_edge_report_compute.py` (new — the manager's
      single-flight/cancel/force/progress/failed-state unit tests, plus the CLI tests, mirroring
      `edge_report.py`'s own `test_cli_main_writes_a_report_and_exits_zero_on_the_fixture_pair` pattern);
      `apps/backend/tests/test_edge_report_api.py` (the three new routes' request/response tests);
      `apps/backend/tests/test_edge_report.py` (the additive-hooks byte-identity/equivalence tests on
      `run_strategy_comparison_report`); `apps/backend/tests/test_mcp_server.py` re-run unmodified
      (TC-10).

### Frontend

- [ ] `apps/frontend/app/structure/page.tsx`: `NotComputedPanel` (line ~287) gains a "Compute edge
      report" button; on click, POST the trigger, then a new poll effect (mirrors the EXISTING
      `needsPolling`/`setInterval(..., 700)` backtest-poll pattern at lines 1301-1327 — reusing the
      PATTERN, not the endpoint) renders `backtests_done / backtests_total` (+ `backtests_from_cache`)
      verbatim while `state === "running"`. On the snapshot reaching `state === "done"`, re-fetch `GET
      /research/edge-report` and fall through to the EXISTING `EdgeReportBody` render (zero new
      report-rendering code — the SAME "zero client recomputation" discipline every prior `/structure`
      section already follows). On `state === "failed"`, render the snapshot's `error` verbatim inside
      the panel. The payload's already-typed `compute` field (currently always `null`) seeds the panel's
      initial state on mount, so a page load during an in-flight or already-terminal job resumes the
      correct view without a spurious extra click.
- [ ] `apps/frontend/lib/api.ts`: add `triggerEdgeReportCompute(force?: boolean)`,
      `fetchEdgeReportCompute()`, `cancelEdgeReportCompute()` — mirror `createBacktest`/`fetchBacktest`/
      `cancelStudy`'s exact `{ok, data/…, error}` shape and 422/unreachable folding byte-for-byte.
- [ ] `apps/frontend/lib/types.ts`: add the compute-job snapshot type (see Data-contract additions
      below) and widen `EdgeReportNotComputed.compute` from its current `null`-only literal type to
      `EdgeReportComputeSnapshot | null`.

### New user-facing capability

The operator can start the first-ever completed real edge-report compute directly from `/structure`
— no out-of-band script, no page-load side effect — watch it progress, and see the finished report (or
an honest failure) render in place.

### New information displayed

The compute job's live progress counts (`backtests_done` / `backtests_total` / `backtests_from_cache`),
its `state`, and — on failure — its `error` string, all rendered inside the existing `NotComputedPanel`.
On `done`, the panel is replaced by the pre-existing `EdgeReportBody` render (not new information — the
SAME report shape J-01 already types, now actually reachable without an out-of-band pre-warm).

### New user actions

A "Compute edge report" button inside the not-computed panel (POST trigger); continuous polling while a
job is in flight requires no further user action.

### UI surface changes

`/structure`'s EXISTING Edge Report section's `NotComputedPanel` gains the button + a progress line.
No new page, no new panel, no nav entry — matches the anti-goal "No new nav entries or pages."

### Product surface delta

Where today a cold `/structure` visit shows a static "Edge report not computed yet." message with no
path forward inside the browser (an operator would need an out-of-band script or REPL call, and none
existed until this iteration), it now offers an explicit in-page action that completes the report
without ever touching a GET — closing the interlude's central promise (Success Criteria #4).

### Blueprint conformance

`/structure` → **Edge Report** section — the EXACT home `blueprint.md`'s Feature/journey homes table
already registers for J-04 ("`/structure` → Edge Report section ('Compute edge report' button +
progress line) | Structure"). No nav change; no `blueprint.reapproval-requested` needed.

### Data-contract additions

The compute-job snapshot's full field/type shape (`id: str`, `state: "running"|"done"|"cancelled"|
"failed"`, `force: bool`, `started_utc: str (ISO-8601)|null`, `finished_utc: str (ISO-8601)|null`,
`error: str|null`, `progress: {phase: str, backtests_total: int, backtests_done: int,
backtests_from_cache: int, current: {dataset_id: str, strategy_id: str}|null}`) — owned by
`app/research/edge_report_compute.py` (`EdgeReportComputeManager`), served by `GET
/research/edge-report/compute` (poll), started by `POST /research/edge-report/compute`, cancelled by
`POST /research/edge-report/compute/cancel`. This is a REFINEMENT of the row `blueprint.md` already
pre-registered at baseline (from goal.md's own Product Shape Data Contract) — same single owner, same
single endpoint, no second computation or serving path; I widened the row's field list to the exact
shape this iteration ships and applied the edit directly to `runs/goal-session-fast_wall/state/
blueprint.md` this iteration (additive-only; no nav-skeleton change, so no reapproval file needed). The
SAME snapshot is embedded verbatim as the `compute` field of the ALREADY-registered not-computed
edge-report payload — never a second derivation.

## OUT OF SCOPE

- J-05 (`EdgeReportBacktestCache`, `_split_cells`'s `run_pair` provider seam, the `ProcessPoolExecutor`
  pool) — depends on this iteration's manager/hook plumbing; next iteration per the dependency order.
- J-06 (`setups_scan_cache.py`) — unrelated to J-04's plumbing; a separate future iteration.
- Any parallel EXECUTION behind `workers=`/`sub_cache=`/`--workers` — this iteration accepts the
  parameters (matching goal.md's J-04 step 1 signature + step 3 CLI usage string, logged as an
  assumption) but every compute this iteration triggers runs strictly sequentially regardless of the
  value; genuine parallelism is J-05's deliverable.
- Any change to `EdgeReportCache`'s existing `get_or_compute`/`lookup`/`compute_and_publish` method
  BODIES — all three stay byte-unchanged (already shipped at J-01); only new callers wire through them.
- Any change to `levels.py`, `tradability.py`, or `backtests.py`'s J-03 `_StructureArmMemo` — untouched;
  J-04's compute is simply the FIRST caller to exercise it at real scale.
- Any change to `bars.py`, `datasets.py`, or `dataset_index.py` (J-02's owned files) — unaffected, zero
  diff expected.
- Any new `Config` field or new runtime dependency — the compute manager and CLI use only stdlib
  (`threading`, `argparse`, etc.), the identical interlude-wide constraint; `config_fingerprint` stays
  `4d665603569b9dbf`.
- Running the CLI warmer to completion against the FULL real corpus and appending the completed
  three-way comparison to `reports/pnl/pnl-history.md` (goal.md J-04 step 5 / Success Criteria #4's
  pnl-history close) — this is explicitly an *(operator-verified on the real corpus)* leg; the goal's
  own "Test discipline" constraint states "the real-corpus timings and the full real compute are
  operator-run verifications, never CI gates." Attempted only as bonus, non-blocking evidence if
  time/CPU budget allows during dev/audit; never required for this iteration's Definition of Done, and
  never simulated or partially faked if attempted.
- Any UI surface outside `/structure`'s Edge Report section.
- Deleting or weakening any existing test in `test_edge_report.py`, `test_edge_report_api.py`,
  `test_mcp_server.py`, or `test_backtests.py`.

## DEFINITION OF DONE

- [ ] J-04 passes via browser-qa-agent (button → progress → cells or the honest empty state, on a
      SCOPED fixture backend — TC-15).
- [ ] Single-flight proven: a second trigger during a run returns the SAME job, `started: false` (TC-2).
- [ ] Cancel resolves `cancelled`; the edge-report cache holds no partial report (TC-3); cancel while
      idle is `409` (TC-4).
- [ ] `force: true` recomputes over a warm key and republishes (TC-5); a non-force trigger over the same
      warm key does NOT recompute (TC-6).
- [ ] After `done`, `GET /research/edge-report` serves the report, byte-identical to the pre-existing
      uncached compute of the same inputs (TC-7).
- [ ] The not-computed payload's `compute` field carries the live/last snapshot, byte-identical in shape
      to what `GET /research/edge-report/compute` itself serves (TC-8).
- [ ] Non-GET verbs on `/research/edge-report` stay 405 (TC-9); no new MCP tool exists (TC-10).
- [ ] The CLI warmer completes on fixtures and prints progress (TC-11); a repeat invocation without
      `--force` exits well under the pinned ceiling on the warm key (TC-12).
- [ ] A failed compute surfaces `error` verbatim and publishes no partial report (TC-13).
- [ ] The five new keyword-only hooks keep `run_strategy_comparison_report`'s unused-default path
      byte-identical to today, and the hooks are proven genuinely wired, not decorative (TC-14).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-07 remain green (replay + LLM fallback,
      mechanically verified).
- [ ] No anti-goal violation introduced — specifically "No compute on page load — operator-run only",
      "No MCP write surface", and "No divergent accelerator output".
- [ ] Unit tests pass; no regressions; full suite green; `config_fingerprint` still `4d665603569b9dbf`.
- [ ] Dev handoff written at `docs/handoffs/goal-fast_wall-iter-4-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-04's live compute cycle (TC-15) and the failed-state render (TC-16), both against a SCOPED
  backend/frontend pair (never the default `.data/datasets` real corpus — see BACKGROUND's applied
  lesson). Required-still-passing J-01 (the not-computed panel's frozen headline/detail/register render
  when no compute has run) and J-07 (the broader `/structure` regression sentinel: Tradable Map, Case
  Studies, Registry, Comparison sections all still render exactly as shipped) are re-verified in the
  SAME browser pass, since they share this iteration's touched page.
- Unit/integration: `EdgeReportComputeManager`'s single-flight/cancel/force/progress/failed-state
  lifecycle; `run_strategy_comparison_report`'s five new keyword-only hooks (default-path equivalence,
  non-vacuous `should_abort` proof); the three new routes' request/response shapes and error codes; the
  CLI warmer's fixture run + warm-key repeat-invocation speedup; the MCP tool-list guard re-run
  unmodified; the existing `test_non_get_verbs_are_405_no_write_surface_exists` and
  `test_edge_report_route_wired_through_the_new_cache_dependency` guards re-run unmodified.
- Error cases: cancelling an idle manager is `409`, never a silent no-op; a compute that raises
  mid-sweep resolves `failed` with the exception's message surfaced verbatim, never swallowed or
  generic; a store-integrity failure during a triggered compute still raises the SAME explicit
  `EdgeReportError` `peek`'s own not-computed path already respects (no new integrity-bypass path).

Test-first contract:

- TC-1: given no compute job has ever run and a cold edge-report cache with a non-empty dataset
  registry, when `POST /research/edge-report/compute` is sent with an empty body, then the response's
  `started` field is `true`, and once the job reaches a terminal state, `GET /research/edge-report/compute`
  returns `state: "done"`, a populated `finished_utc`, and `error: null`.
- TC-2: given a compute job deterministically held in flight (test harness blocks it mid-sweep), when a
  second `POST /research/edge-report/compute` is sent before the first finishes, then the response's
  `started` field is `false` and the returned job `id` equals the in-flight job's `id` — no second job
  is created.
- TC-3: given a compute job held in flight, when `POST /research/edge-report/compute/cancel` is sent,
  then the job's snapshot reaches `state: "cancelled"`, and a subsequent `GET /research/edge-report`
  still returns the not-computed payload — the edge-report cache's hot slot and durable row are
  unchanged from before the run (no partial report was ever published).
- TC-4: given `state` is idle (no job has ever run, or the last job already reached a terminal state),
  when `POST /research/edge-report/compute/cancel` is sent, then the response status is `409`.
- TC-5: given the edge-report cache already holds a warm key from a genuinely completed prior compute,
  when `POST /research/edge-report/compute` is sent with `{"force": true}`, then a call-counting spy on
  the underlying compute path records a fresh call, and the cache's stored row's `created_utc` (or an
  equivalent stored freshness marker) moves forward from its pre-force value.
- TC-6: given the SAME warm key and no `force` flag (or `{"force": false}`), when `POST
  /research/edge-report/compute` is sent, then the call-counting spy from TC-5 records zero additional
  calls, and the job's snapshot reaches `state: "done"` serving the already-cached result.
- TC-7: given a compute job that reaches `state: "done"`, when `GET /research/edge-report` is called
  afterward, then it returns the real report (no `status` key present), byte-identical
  (`json.dumps(..., sort_keys=True)`) to the SAME inputs computed via the pre-existing uncached
  `_compute_strategy_comparison_report(store, dataset_store, bar_store, config)` call.
- TC-8: given no compute job has ever run, when `GET /research/edge-report` is called on a cold key,
  then the returned payload's `compute` field is `null` (the unchanged J-01 behavior); given a compute
  job has since been triggered, when the SAME endpoint is polled again, then `compute` embeds the
  manager's current/last snapshot, byte-identical in shape to what `GET /research/edge-report/compute`
  itself returns at that instant.
- TC-9: given the route surface after this iteration's diff, when a non-GET verb (`POST`/`PUT`/`PATCH`/
  `DELETE`) is sent to `/research/edge-report` itself (not the `/compute` subpath), then the response is
  `405` and `test_non_get_verbs_are_405_no_write_surface_exists` passes with byte-unmodified source.
- TC-10: given `apps/backend/app/mcp/__init__.py`'s registered tool set before this iteration, when the
  suite runs after this iteration's diff, then `test_advertised_tool_set_is_exactly_capability_6`
  (`TOOL_NAMES == EXPECTED_TOOLS`) passes with byte-unmodified source — no new MCP tool exists.
- TC-11: given the committed fixture dataset registry (`apps/backend/tests/fixtures/datasets_j03` or
  `apps/backend/tests/fixtures/datasets`), when the CLI warmer (`python -m app.research.edge_report_compute`
  with no flags) runs, then it exits `0`, prints at least one progress line per completed backtest, and
  the durable edge-report cache row it publishes is byte-identical to what `GET /research/edge-report`
  subsequently serves.
- TC-12: given the CLI warmer already ran once against the fixture (TC-11's warm state), when it is
  invoked a SECOND time without `--force`, then it exits in under 5 seconds of wall-clock time, a
  call-counting spy confirms zero backtests re-run, and its printed summary reflects the already-warm
  result (see NOTES for the chosen ceiling's rationale).
- TC-13: given a compute run that fails partway (a test-injected exception inside the compute path),
  when the snapshot is polled after the failure, then `state: "failed"`, `error` carries the
  exception's message verbatim, and the edge-report cache holds no newly-published row from that run.
- TC-14: given the SAME dataset registry/config, when `run_strategy_comparison_report` is called once
  via the pre-existing default path (`cache=<cache>`, every new kwarg left at its default) and once via
  the SAME call with `progress=`/`should_abort=` hooks actively supplied but never triggered to abort,
  then the two reports are byte-identical (`json.dumps(..., sort_keys=True)` equality); AND, when the
  SAME call is made a third time with a `should_abort` that DOES fire mid-run, then the result differs
  observably (the run resolves `cancelled`/publishes nothing, per TC-3) — proving the hooks are
  genuinely wired, not a decorative no-op that would also pass if silently ignored.
- TC-15 (browser): given `/structure` is loaded against a SCOPED backend/frontend pair pointed at a
  small committed fixture dataset dir (never the default `.data/datasets`) with a cold edge-report
  cache, when the operator clicks "Compute edge report", then the panel's progress counts update at
  least once while `state === "running"` and, within 90 seconds of the click, the panel is replaced by
  either the existing `EdgeReportBody` render or the honest all-empty-cells state, with zero full-page
  reload.
- TC-16 (browser): given a compute snapshot already at `state: "failed"` with a known `error` string
  (arranged on the scoped backend before navigation, mirroring iter-1 QA's own "arrange the target
  state via a direct backend call, then navigate and verify the render" precedent), when `/structure` is
  loaded (or its poll tick fires), then the not-computed panel visibly renders that exact `error` string
  verbatim.

## NOTES

- **Codebase probe (this iteration, decompose time):** confirmed `edge_report_compute.py` does not
  exist anywhere in `apps/backend/app` yet (fresh build; matches `journey-history.json`'s
  `J-04 | failing`). `EdgeReportCache.lookup`/`compute_and_publish` (J-01) already exist beside the
  untouched `get_or_compute` (`edge_report_cache.py:262-350`). `run_strategy_comparison_report`
  (`edge_report.py:450-484`) currently has only `cache=None` as its sole keyword parameter — no
  `force`/`progress`/`should_abort`/`sub_cache`/`workers`. `peek_strategy_comparison_report`
  (`edge_report.py:487-525`) unconditionally emits `"compute": None` at line 524. `routes.py` has no
  `/research/edge-report/compute*` routes yet; `ResearchRegistry.__init__` (`routes.py:237-250`) wires
  only `_study_jobs`/`_backtest_jobs` — the exact precedent this iteration's manager follows, adapted to
  single-flight (see IN SCOPE). `apps/frontend/app/structure/page.tsx`'s `NotComputedPanel` (line 287)
  and its poll-while-active pattern (lines 1301-1327, `needsPolling`/`BACKTEST_TERMINAL_STATUSES`) are
  the exact precedent the new button/poll logic should mirror. `app/mcp/__init__.py` has exactly 18
  registered tool names (`tape_state`, `tape_features`, `tape_history`, `journal`, `analytics`,
  `studies`, `datasets`, `bars`, `levels`, `tradability`, `setups`, `backtests`, `strategies`,
  `edge_report`, `pnl_ledger`, `taxonomy`, `ui_route_map`, `get_endpoint`), pinned by
  `test_advertised_tool_set_is_exactly_capability_6`.
- **Implementation hint (non-binding):** one clean way to keep "publish only after the compute function
  returns NORMALLY" true by construction — matching how `EdgeReportError` already propagates unchanged
  through `get_or_compute`/`compute_and_publish` today, per that module's own docstring — is to have
  `should_abort()` raise a dedicated cancellation signal between pairs inside `_split_cells`'s loop
  (rather than returning a sentinel value the caller must remember to check), which then propagates
  straight through the cache methods' existing "propagate unchanged" contract; the manager's own worker
  thread catches that specific signal at its outer boundary to set `state: "cancelled"` rather than
  `"failed"`. The developer may choose a different mechanism as long as TC-3/TC-13's "no partial report
  published" observable holds.
- **Lessons applied:** see BACKGROUND (iter-0's scoped-browser-QA lesson, extended to the new button
  surface; iter-3's non-vacuous-equivalence lesson, applied to TC-14).
- **Assumptions logged this iteration:** two new entries in
  `runs/goal-session-fast_wall/state/assumptions.md` (`## iter-4 — goal-decomposer` ×2) — (1) the
  division of the five keyword-only hooks / `--workers` CLI flag between this iteration (signature +
  flag, inert `sub_cache=`/`workers=`) and J-05 (real parallel effect); (2) the concrete wall-clock
  ceilings TC-12 (5s) and TC-15 (90s) pin, chosen generously against the tiny fixture's real expected
  sub-second-to-low-single-digit-second cost.
- **Blueprint edit this iteration:** refined (not added) the pre-registered "Compute-job snapshot" row
  in `runs/goal-session-fast_wall/state/blueprint.md` to its full field/type shape now that this
  iteration actually builds it — additive detail only, same single owner (`edge_report_compute.py`) and
  single endpoint (`GET /research/edge-report/compute`) pre-registered at baseline; no nav-skeleton
  change, so no `blueprint.reapproval-requested` file was written.
- **Scope discipline:** this diff should touch `edge_report_compute.py` (new), `edge_report.py`,
  `routes.py`, `structure/page.tsx`, `lib/api.ts`, `lib/types.ts`, and their test files — no
  `levels.py`, `tradability.py`, `backtests.py` (J-03's owned files, byte-unchanged), no `bars.py`/
  `datasets.py`/`dataset_index.py` (J-02's owned files, byte-unchanged), no `edge_report_cache.py`
  method-body change (only new callers), and no `app/mcp/__init__.py` change. Any wider diff is a signal
  scope has leaked into J-05/J-06 territory.

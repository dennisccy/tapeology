# Goal Iteration 6 — Restarts stop hurting: the durable setups scan cache (J-06, closing the interlude)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** fast_wall
- **Iteration:** 6
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-07 (the FULL `passing` set in `journey-history.json` — a full regression pass, matching iter-5's own "closing iteration" framing). `compute_setups` is called internally by `edge_report.py`'s `run_strategy_comparison_report` (`edge_report.py:582`, `:932`) to resolve each dataset's owning touch event, so J-01/J-04/J-05's edge-report cells are DOWNSTREAM of this iteration's own keying change — a mistake here would silently corrupt their output, exactly the "No divergent accelerator output" critical anti-goal. J-02's verified-content store caches and J-03's `_StructureArmMemo` are read by the SAME scan/backtest call graph (unaffected, zero diff expected, but exercised at full volume by the regression suite). J-07 is the standing foundation sentinel. All six share `/structure`, the SAME page this iteration's own browser check re-loads.
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

Give `compute_setups`'s multi-minute full-panel touch-event scan a durable, restart-surviving cache — keyed by the scan's actual inputs (the config's CONTENT, not its object identity) alongside the existing store signature, rather than today's in-process-only slot keyed by the fragile `id(config)` — so a backend restart, or simply a freshly-constructed but content-equal `Config` object, never re-pays the scan; this closes J-06, the seventh and final Must-have journey of "The Fast Wall" interlude.

## BACKGROUND

J-01 through J-05 and J-07 are all `passing` as of iter-5; J-06 is the ONLY journey still `failing`
(`journey-history.json`), explicitly carried forward unbuilt since iter-3 ("Build J-06... — the LAST
of this interlude's seven journeys," iter-5's own Next-Step Recommendation, echoing iter-3's and
iter-4's identical deferral). Per the priority rubric this is not really a choice: rule 1
(regressions first) is N/A — nothing is `regressed`; rule 2 (consolidation) is N/A — iter-5's
`coherence.md` was `COHERENCE-PASS`; rule 3 (unblockers) collapses to a single candidate since J-06
is the only `failing` journey left; rule 4 (smallest spec wins ties) has no tie to break. J-06 is
therefore this iteration's sole target, satisfying "target 1-3 journeys" trivially and rule 5
("never bundle two risky journeys") by construction — there is only one.

**Depth = full**, citing iter-5's own Next-Step Recommendation directly ("Depth full: J-06 modifies
the frozen-foundation `setups.py` under the critical 'Frozen foundations' + 'No source-guard
weakening' anti-goals... adds a new durable accelerator needing byte-identity + zero-rescan-spy +
tamper tests, and is `Frontend Present: yes`... As the final journey, a clean J-06 makes
GOAL_ACHIEVED reachable, so the audit + coherence + ux-regression + closure lanes are the warranted
backstop for the closing iteration") plus the "Picking depth" rubric's own triggers, independently
verified here: the prior verdict was `CONTINUE`, not `ESCALATE`, so full is not mandatory by that
rule alone — but this iteration modifies a frozen-foundation file (`setups.py`) protected by two
source-introspection guard tests that MUST survive byte-unmodified
(`tests/test_setups.py:758-771`/`:995-1017`, confirmed still at those exact lines), is
`Frontend Present: yes` (`docs/goal.md` itself tags "J-01, J-04, J-06 are browser-verifiable"),
requires tests well beyond browser smoke (a durable-cache determinism/tamper/mutation-probe suite —
see TESTING REQUIREMENTS), and is the closing iteration of a six-iteration interlude.

**Lessons applied (from `lessons.md`):**
- **iter-3's lesson names J-06 explicitly**: "any future accelerator iter under 'No divergent
  accelerator output' — specifically J-05... and J-06 (durable setups scan cache); demand the
  determinism/equivalence test be shown non-vacuous... not merely present-and-green." TC-6 below is
  built for exactly this: it pre-seeds the durable row with a DELIBERATELY WRONG payload under the
  live key and asserts `compute_setups` returns that wrong payload verbatim — proving the
  durable-hit code path is genuinely read, not dead code a naive byte-identity assertion could pass
  vacuously.
- **iter-0's lesson** (browser-QA of `/structure` must run against a SCOPED/keyless dataset+bar dir,
  never the default 882MB `.data/datasets` corpus) applies verbatim to TC-9: reuse the EXACT
  established ports-8391/3391 recipe (`reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s
  one-time setup), adding `TAPEOLOGY_SETUPS_CACHE_DB` to the scoped env list (the iter-5 precedent
  of appending one new env var per new durable cache alongside `TAPEOLOGY_EDGE_SWEEP_CACHE_DB`).
- **iter-5's lesson** (a visual sub-leg can be structurally un-showable on the mandated keyless
  fixtures, and that is a documented limitation, not a missing-evidence gap) applies directly here
  too: the established scoped recipe creates `$SCOPED_DIR/bars` EMPTY (`mkdir -p`, never populated —
  confirmed by reading `reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s setup script), and the
  committed `tests/fixtures/bars/` fixture itself carries zero `"5m"`-timeframe series either (grep-
  confirmed), so Case Studies will honestly render "No band-touch events scanned yet."
  (`case-studies-empty`) on the scoped browser check REGARDLESS of J-06's correctness. TC-9 proves NO
  REGRESSION (no loading panel remains, matching goal.md's own acceptance wording verbatim), never a
  populated-table cache-hit demonstration — that proof is the keyless pytest suite's job (TC-1
  through TC-6).
- **iter-4's lesson** (a golden-replay "possible regression" FAIL must be checked against its own
  evidence screenshot before being trusted — a "Backend unreachable" render is an infra
  false-negative, not a regression; Chrome MCP has been flaky more than once this session) is
  standing operating guidance for this iteration's full regression pass.

If J-06 lands cleanly this iteration, all 7 Must-have journeys will be `passing` — whether that
constitutes `GOAL_ACHIEVED` is the evaluator's call next iteration (per this agent's own rules, the
decomposer never marks journeys passing/failing), not predetermined here.

## IN SCOPE

### Backend

- [ ] New `apps/backend/app/research/setups_scan_cache.py`: a durable SQLite cache class (e.g.
      `SetupsScanCache`) with `lookup(key: str) -> dict | None` / `publish(key: str, result: dict) ->
      None` — mirrors `edge_report_backtest_cache.py`'s "durable-only, no in-process hot slot of its
      own" shape (a fresh short-lived connection per call — the `JournalStore._read_conn` precedent —
      WAL + `busy_timeout`, `sqlite3.Error` on any method swallowed to a miss/no-op, never a crash)
      SINCE `setups.py` already owns its own in-process hot slot (`_SCAN_CACHE`) and does not need a
      second one inside this module. Result JSON stored WITHOUT `sort_keys` (the
      `EdgeReportCache._insert` byte-identity discipline). Path resolution — a module-level resolver
      function, the `resolve_cache_db_path`/`resolve_backtest_cache_db_path` precedent — env
      `TAPEOLOGY_SETUPS_CACHE_DB` if set, else a file located beside `BarStore.root`'s PARENT
      directory (`Path(store.root).parent / "setups_scan_cache.db"` — the `get_bar_index`
      env-else-sibling-of-`bar_dir_resolved()` shape, e.g. `.data/bars` → `.data/setups_scan_cache.db`).
      No `reindex()`/bulk-rebuild method — `lookup`/`publish` alone satisfy every caller (the
      `edge_report_backtest_cache.py` "stays exactly as large as its job needs to be" precedent; do
      not add an abstraction nothing calls).
- [ ] `apps/backend/app/research/setups.py`: `compute_setups`'s key changes from
      `(id(config), _store_signature(store))` to `(config_content_hash, _store_signature(store))`,
      where `config_content_hash` is `edge_report_cache._config_content_hash(config)` IMPORTED and
      reused verbatim (never re-derived a second time — goal.md's own instruction). This must be the
      conservative whole-config content hash, NOT `config.config_fingerprint()` alone: the
      fingerprint's own documented exclusion set drops exactly the `setups_*`/`tradability_*`/`sr_*`
      field families `compute_setups`/`compute_tradability` read directly (see
      `edge_report_cache.py`'s module docstring, "why it is FOUR parts" section, for the identical
      reasoning already proven necessary for the sibling report cache) — using the fingerprint alone
      would silently under-invalidate on a real `setups_reaction_threshold_bps`-style change (see
      TC-3). `compute_setups` becomes a three-tier lookup: hot slot (UNCHANGED atomic
      `(key, result)` single-rebind discipline) → the new durable `SetupsScanCache` (self-resolved
      from the `store: BarStore` parameter already in scope) → `_run_full_panel_scan`. A durable hit
      republishes to the hot slot in one atomic rebind (the `EdgeReportCache.lookup` three-tier
      precedent — read-local-reference-before-inspect preserved); a full miss publishes to BOTH
      layers (durable write before the hot-slot rebind, the `EdgeReportCache.get_or_compute` publish
      order). `compute_setups`'s OWN signature (`store: BarStore, config: Config`) and its 4 existing
      call sites (`routes.py:1945`, `:1967`; `edge_report.py:582`, `:932`) stay byte-unchanged — no
      FastAPI dependency injection is introduced for the new cache (unlike `BarIndex`/`DatasetIndex`/
      `EdgeReportCache`, this is a bare module function with no owning class/route to inject through;
      see NOTES). Both scan functions' source stays free of the "dataset" substring
      (`test_compute_setups_itself_never_touches_the_dataset_store`,
      `tests/test_setups.py:758-771`) and the hot-slot publish stays exactly ONE
      `_SCAN_CACHE = (key, result)` rebind
      (`test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`,
      `tests/test_setups.py:995-1017`) — both pass byte-unmodified.
- [ ] Refresh `setups.py`'s B3 module-docstring/block-comment wording (currently states the memo is
      "PROCESS-LOCAL and in-memory only — never SQLite/disk-persisted") to describe the new two-tier
      (hot slot + durable) reality — goal.md's own step-2 instruction ("refresh the stale
      block-comment wording"). Documentation-only; no behavior implied by this bullet beyond the code
      changes above.
- [ ] New test module `apps/backend/tests/test_setups_scan_cache.py` (the
      `test_edge_report_backtest_cache.py`/`test_dataset_index.py` naming precedent): durability
      (write then read back across a fresh instance at the same path), publish-failure swallowing,
      `sqlite3.Error` handling on a corrupted DB file. Additions to `tests/test_setups.py` for the
      `compute_setups`-level TCs below (restart simulation, content-hash equality, `setups_*`-family
      busting, store-signature busting, cache-loss recompute, the mutation probe) — the two existing
      guard tests and the module-level `_SCAN_CACHE` behavioral/concurrency tests already in the file
      stay untouched.

### Frontend

- [ ] None planned. `Frontend Present: yes` is set solely to force the UI Impact / UI Test Design /
      Browser QA / UX Regression lanes to run this iteration against the EXISTING `/structure` page
      (`structure/page.tsx`, unchanged since iter-4) — confirming Case Studies (and every other
      section) still reaches its ready/honest-empty state after `compute_setups`'s caching change,
      with zero new frontend code (mirrors iter-5's identical framing for J-04's re-verification
      pass).

### New user-facing capability

None new directly. The EXISTING Case Studies list / `/studies` page's underlying scan becomes
faster on a warm durable cache and after a backend restart; no new button, no new panel, no new
filter.

### New information displayed

None new. `compute_setups`'s served shape (`{"events": [...]}`) is byte-unchanged.

### New user actions

None new — no new control anywhere on `/structure` or `/studies`.

### UI surface changes

None — `/structure`'s sections and `/studies` are byte-unchanged this iteration.

### Product surface delta

Invisible on the mandated scoped/keyless browser check (an empty bar dir scans near-instantly
either way). Visible only to an operator on the real corpus: a backend restart followed by
`/structure`/`/studies` no longer re-pays the multi-minute full-panel scan.

### Blueprint conformance

No new surface. `/structure` → Case Studies section and `/studies` stay J-06's already-registered
homes (blueprint.md's Information Architecture table has carried this row since baseline, unchanged
this iteration). `setups_scan_cache.db` was ALREADY pre-registered in blueprint.md's "Rebuildable
accelerators" list at baseline as a one-line placeholder — this iteration builds it; I refined that
bullet's detail (exact key composition + path resolution) directly in
`runs/goal-session-fast_wall/state/blueprint.md` this iteration (additive documentation only; no
nav-skeleton change, so no `blueprint.reapproval-requested` file was written) — mirroring iter-5's
identical treatment of the `edge_report_backtests.db` bullet.

### Data-contract additions

None new. `setups_scan_cache.db` is explicitly a rebuildable accelerator (blueprint.md's own
"explicitly NOT canonical values" framing) — no UI/REST/MCP surface reads it directly; only
`compute_setups`'s own internals do. `compute_setups`'s served shape is UNCHANGED — same single
owner (`setups.py`), same two endpoints (`GET /research/setups`, `GET /research/setups/{id}`), no
second derivation, no second endpoint.

## OUT OF SCOPE

- Any change to `levels.py`, `tradability.py`, `backtests.py` (J-03's owned files) — untouched;
  `compute_tradability` is called from `_run_full_panel_scan` exactly as before.
- Any change to `bars.py`, `datasets.py`, `dataset_index.py` (J-02's owned files) — unaffected, zero
  diff expected.
- Any change to `edge_report.py`, `edge_report_compute.py`, `edge_report_cache.py`'s method BODIES,
  or `edge_report_backtest_cache.py` (J-01/J-04/J-05's owned files) — only an IMPORT of
  `_config_content_hash` from `edge_report_cache.py` is allowed (reuse, never re-derive); no body
  change to any of these files.
- Any new `/structure`/`/studies` UI element, any new nav entry, any new page.
- Any new `Config` field or runtime dependency beyond stdlib `sqlite3` — `config_fingerprint` stays
  `4d665603569b9dbf`.
- Deleting or weakening `tests/test_setups.py:758-771`/`:995-1017` (the two source-introspection
  guards), the module's existing concurrency tests, or any other existing test anywhere in the suite.
- Any MCP tool change — the `setups` MCP tool proxy stays byte-identical (tool count 18).
- A `reindex()`/bulk-rebuild method on `SetupsScanCache` — not needed; `lookup`/`publish` alone serve
  every caller.
- Running the CLI warmer / full real-corpus sweep to completion, or appending to
  `reports/pnl/pnl-history.md` — that is J-04/J-05's already-closed scope (era-5B J-08 step 3), not
  reopened here.
- Verifying goal.md's literal "within 10 seconds of navigation" real-corpus figure — that clause is
  explicitly tagged `*(operator-verified on the real corpus)*` in goal.md, mirroring the identical
  treatment iter-4/iter-5 already gave every other real-corpus timing claim (non-blocking, gathered
  as bonus evidence only if time/CPU budget allows; never required for this iteration's Definition of
  Done).

## DEFINITION OF DONE

- [ ] A hot-slot-cleared (simulated restart) `compute_setups` call serves the durable cache with zero
      rescans, byte-identical to a fresh scan (TC-1).
- [ ] An equal-content-but-distinct `Config` object is a cache HIT — the `id(config)` fragility is
      gone (TC-2).
- [ ] A `setups_*`-family config field change busts the cache (a fresh scan runs) — proving the content hash,
      not the fingerprint-excluded `config_fingerprint()`, drives the key (TC-3).
- [ ] Recording a new bar series busts the key (TC-4).
- [ ] Deleting the scan-cache DB file is harmless — one recompute, byte-identical result (TC-5).
- [ ] A non-vacuous mutation-probe test proves the durable-hit code path is genuinely exercised, not
      dead code (TC-6).
- [ ] The two source-introspection guard tests and the MCP tool-count guard pass byte-unmodified;
      `config_fingerprint()` stays `4d665603569b9dbf` (TC-7).
- [ ] A durable-cache publish failure never blocks `compute_setups`/`GET /research/setups` from
      serving the freshly-scanned events list (TC-8).
- [ ] Browser: `/structure` on the scoped fixture pair reaches every section's ready/honest-empty
      state, with no `-loading`-suffixed testid remaining, and zero visual regression vs iter-5
      (TC-9).
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05, J-07 remain green (deterministic
      replay + LLM fallback, mechanically verified).
- [ ] No anti-goal violation introduced — specifically "No divergent accelerator output",
      "Accelerators are never sources of truth", "Frozen foundations", and "No source-guard
      weakening".
- [ ] Unit tests pass; no regressions; full suite green; `config_fingerprint` still
      `4d665603569b9dbf`.
- [ ] Dev handoff written at `docs/handoffs/goal-fast_wall-iter-6-dev.md`.

## TESTING REQUIREMENTS

- Browser: `/structure`'s full-page regression check — no loading panel remains anywhere, Case
  Studies' honest-empty render, zero visual diff vs iter-5 (TC-9) — against the SCOPED fixture pair
  only, never the default `.data/` corpus.
- Unit/integration: `SetupsScanCache`'s durability, key-composition round-trip, and
  publish-failure-swallowing; `compute_setups`'s three-tier lookup (hot slot → durable → real scan)
  under a restart simulation, content-hash equality across distinct-identity equal-content `Config`
  objects, `setups_*`-family cache-busting, store-signature busting, cache-loss recompute, and the
  non-vacuous mutation probe; the two existing source-introspection guards and the MCP tool-count
  guard re-run byte-unmodified.
- Error cases: a corrupted/unwritable durable cache DB never raises out of
  `compute_setups`/`GET /research/setups` (swallowed, falls through to a fresh scan); a
  `SetupsScanCache` constructed against a DB file replaced with unparseable content is treated as a
  full miss, never a crash (the `EdgeReportBacktestCache` precedent).

Test-first contract:

- TC-1: given `compute_setups` has already computed and durably cached a scan for a `(config, store)`
  pair (both the in-process hot slot and the durable `SetupsScanCache` populated), when the in-process
  hot slot is cleared (simulating a process restart) and `compute_setups(store, config)` is called
  again with the unchanged store/config, then a call-counting spy wrapping `_run_full_panel_scan`
  records ZERO new calls, and the returned dict is byte-identical
  (`json.dumps(..., sort_keys=True)` equality) to the original scan's result.
- TC-2: given a warm cache entry published while resolving one `Config(...)` instance, when
  `compute_setups` is called with a SECOND, freshly-constructed `Config(...)` instance carrying
  IDENTICAL field values (a different `id()`), then a call-counting spy on `_run_full_panel_scan`
  records ZERO new calls — a genuine cache HIT proving the key is derived from config CONTENT, not
  `id(config)`.
- TC-3: given a warm cache for one `Config` instance, when ONE `setups_*`-family field (e.g.
  `setups_reaction_threshold_bps`) is changed on an otherwise-identical `Config` and `compute_setups`
  is re-called with the SAME store, then a call-counting spy on `_run_full_panel_scan` records exactly
  ONE new call — proving the cache key is the config CONTENT hash (which covers every field), never
  `config.config_fingerprint()` alone (which excludes exactly the `setups_*`/`tradability_*`/`sr_*`
  families `compute_setups`/`compute_tradability` read).
- TC-4: given a warm cache for a store with one registered "5m" series, when a NEW "5m" bar series is
  recorded into the SAME store (changing `_store_signature`) and `compute_setups` is re-called with
  the unchanged `config`, then a call-counting spy on `_run_full_panel_scan` records exactly ONE new
  call.
- TC-5: given a durable cache DB file containing at least one published row, when the DB file is
  deleted from disk, the in-process hot slot is cleared, and `compute_setups` is called again for the
  SAME `(config, store)` key, then it recomputes via `_run_full_panel_scan` exactly once (spy) and the
  returned result is byte-identical to the pre-deletion cached result.
- TC-6 (mutation probe, non-vacuous — iter-3's lesson applied to J-06): given the in-process hot slot
  cleared and a durable row pre-seeded (via `SetupsScanCache.publish`, or an equivalent direct write)
  under the EXACT current `(config, store)` key with a DELIBERATELY WRONG `events` payload (e.g. an
  empty list where the real scan would find events, or a fabricated event id), when
  `compute_setups(store, config)` is called, then it returns the deliberately-wrong stored payload
  VERBATIM (not a freshly-rescanned correct one) — proving the durable-hit code path is genuinely
  exercised, not dead code silently falling through to a fresh scan.
- TC-7: given the full backend suite after this iteration's diff, when it runs, then
  `tests/test_setups.py:758-771` (`test_compute_setups_itself_never_touches_the_dataset_store`) and
  `tests/test_setups.py:995-1017`
  (`test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes`) pass with
  `compute_setups`'s and `_run_full_panel_scan`'s source unchanged in the guarded sense (no "dataset"
  substring; exactly one `_SCAN_CACHE = (` rebind), `test_advertised_tool_set_is_exactly_capability_6`
  (`tests/test_mcp_server.py`) still reports exactly 18 tools, and `Config().config_fingerprint()` is
  still `4d665603569b9dbf`.
- TC-8: given a `SetupsScanCache` constructed against a DB path that cannot be written (e.g. its
  parent directory made read-only, or the file replaced with unparseable content), when
  `compute_setups` runs a fresh scan and attempts to publish it to the durable cache, then
  `compute_setups` still returns the freshly-scanned result (identical to what `_run_full_panel_scan`
  alone would produce — the publish failure is swallowed, never raised), and a direct call to
  `GET /research/setups` against that same broken path still returns HTTP 200 with that same events
  list.
- TC-9 (browser): given the established scoped backend/frontend pair (ports 8391/3391,
  `TAPEOLOGY_DATASET_DIR` pointed at a copy of `tests/fixtures/datasets_j03`, `TAPEOLOGY_BAR_DIR`
  pointed at a fresh empty directory, `TAPEOLOGY_SETUPS_CACHE_DB` added to the same scoped temp dir —
  the exact recipe `reports/phase-goal-fast_wall-iter-4-ui-test-plan.md`'s one-time setup already
  documents, with the one new env var appended), when `/structure` is navigated to fresh, then no
  element with a `-loading`-suffixed testid remains anywhere on the page within 10 seconds of
  navigation, the Case Studies panel renders its honest `case-studies-empty` "No band-touch events
  scanned yet." state (the scoped bar dir has zero registered series, so an honest-empty render — not
  a populated table — is the correct, expected outcome), and the Tradable Map / Edge Report /
  Registry / Comparison sections render exactly as they did in iter-5 (no visual regression).

## NOTES

- **Codebase probe (this iteration, decompose time):** confirmed `setups_scan_cache.py` does not
  exist anywhere yet (only `bar_index.py`/`dataset_index.py`/`edge_report_cache.py`/
  `edge_report_backtest_cache.py` exist as durable-cache precedents). `compute_setups(store, config)`
  is called from exactly 4 sites — `routes.py:1945` (`list_setups`), `routes.py:1967` (`get_setup`),
  `edge_report.py:582`, `edge_report.py:932` — all 2-arg, none passing a cache. `BarStore.root`
  (`bars.py:177-184`) already exists as a public read-only property, added at J-02 TC-11 specifically
  so "a future sibling-path consumer... can derive its own path without reaching into a private
  attribute" — this iteration is that consumer. `edge_report_cache._config_content_hash` and
  `_canonical` are private-by-convention (no underscore-stripping `__all__` export) but already
  imported cross-module by `edge_report_backtest_cache.py` (`from .edge_report_cache import
  _canonical, _config_content_hash`) — the identical import this iteration repeats into `setups.py`.
  The two guard tests are confirmed at the exact lines goal.md cites
  (`test_compute_setups_itself_never_touches_the_dataset_store` at `tests/test_setups.py:758`,
  `test_scan_cache_publish_is_a_single_atomic_rebind_never_two_separate_writes` at `:995`). The
  frontend's Case Studies panel (`structure/page.tsx:1874-1922`) uses testid `case-studies-loading`
  while `setupsResult === null`, `case-studies-empty` for a true-empty registry ("No band-touch events
  scanned yet."), and `case-studies-table` for a populated one — confirmed by direct read. The
  established scoped browser recipe's `$SCOPED_DIR/bars` is created via bare `mkdir -p` (never
  populated from any fixture), and the committed `tests/fixtures/bars/` fixture itself carries zero
  `"5m"`-timeframe series (grep-confirmed) — so `case-studies-empty` is the correct, expected TC-9
  outcome regardless of this iteration's correctness (see BACKGROUND's lessons-applied section). Full
  backend suite re-run at decompose time: all-dots, exit 0, matching iter-5's reported 1517 passed / 7
  skipped / 0 failed baseline; `git status` confirms the working tree is exactly iter-5's delivered
  state (only non-product runtime/report files touched since).
- **Implementation guidance (non-binding) — why no FastAPI dependency injection here:**
  `compute_setups`'s signature is explicitly documented as frozen ("compute_setups's own signature is
  UNCHANGED, so every caller... needs zero changes — only ITS body differs," `setups.py`'s own B3
  module comment, written at era-5B iter-5 and unchanged since). Unlike `BarIndex`/`DatasetIndex`/
  `EdgeReportCache`/`EdgeReportBacktestCache` — each constructed once via a FastAPI `Depends(...)` and
  passed into its owning route/caller — `compute_setups` is a bare module function called from FOUR
  places across two files with no shared owning object to inject through. The cleanest path
  (developer's call on exact code shape) is to resolve/construct the `SetupsScanCache` INSIDE
  `setups.py` itself, lazily, keyed off the `store: BarStore` parameter already passed to every call
  site — mirroring how `_SCAN_CACHE` itself is already a module-level construct requiring no
  injection. Do not widen `compute_setups`'s signature to accept a cache parameter; that would touch
  all 4 call sites for no reason goal.md asks for.
- **Scope discipline:** this diff should touch `setups.py`, one new cache module
  (`setups_scan_cache.py`), and their test files (`test_setups.py` additions,
  `test_setups_scan_cache.py`) — no `levels.py`/`tradability.py`/`backtests.py` (J-03's owned files),
  no `bars.py`/`datasets.py`/`dataset_index.py` (J-02's owned files), no `edge_report*.py` method-body
  change (only an import reused), no `app/mcp/__init__.py`, no `routes.py` (no new dependency needed —
  see implementation guidance above), and no frontend file. Any wider diff is a signal scope has
  leaked.
- **If Chrome MCP fails to start:** do not block the rest of this iteration. TC-1 through TC-8 are
  fully keyless/automated and must still be delivered and evaluated on their own evidence — the real
  proof of J-06's correctness lives there, not in the browser leg (see BACKGROUND's iter-5 lesson).
  Retry the scoped recipe once in a fresh session; if it still fails, escalate the environmental
  blocker to the operator exactly as iter-4's eval.md already flagged, rather than treating it as a
  new, unexplained blocker.

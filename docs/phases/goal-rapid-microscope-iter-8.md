# Goal Iteration 8 — The tape recorder: chunked, throttled, resumable, and proven hermetically

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** rapid-microscope
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — `tick_recorder.py` cross-cuts store discipline (`datasets.py`), the existing vendor chunk generator (`alpaca.py`'s `iter_historical_chunks`), the shared compute-manager/CLI/route pattern (new `micro_routes.py` wiring), and the core event dataclasses (`providers/base.py`) whose hash-safety this iteration also fixes — interactions no single journey's tests cover; this exact surface (identity/checksum functions meeting new preservation-field data) is where 4 of this session's 5 critical anti-goal violations were caught in the last 4 iterations, and the evaluator's own iter-7 next-step recommendation asks explicitly for the full pipeline with the independent auditor, "not shortened for time."
- **Frontend Present:** yes
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-02, J-03, J-04, J-05, J-10
- **Anti-goal reminders:**
  - Frozen foundations — the `v1` strategy, the `default` profile, the tape engine's five states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside them, never a mutation of them. *(critical)*
  - Immutable data — registered datasets and bar series are append-only, checksummed, never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration. *(critical)*
  - Persistence stays scoped — no ambient recording of live streams; recording/fetching is an explicit, logged act. *(critical)*
  - Deterministic and seeded — every random draw uses a recorded named seed via per-row streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any research artifact. *(critical)*
  - Single source of truth — each shared value is computed once, owned by one canonical endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails violations. *(critical)*
  - Read-only MCP — MCP tools remain byte-identical proxies of GET endpoints; nothing on the MCP surface can change state. *(critical)*
  - No fold geometry change after fold 1 without a recorded voiding event that clears every survivor state of that corpus-era. *(critical)*
  - The 12 pre-existing tick symbol-days are permanently exploratory — never sealed, never `historical_oos`, never relabeled. *(critical)*
  - The ~150-symbol-day research-readiness gate is never lowered or silently satisfied; any claim whose predeclared floor is unmet fails closed with the floor arithmetic served. *(critical)*
  - Host-guard caps are law. [...] Never disable, widen, or bypass these caps to make a run faster or a pause go away; widening the mask follows the verification ladder in `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Build J-06 step 2 — a real, resumable, throttled tick recorder (`tick_recorder.py`) proven hermetically against fixtures, closing step 1's deferred vendor-rule stamping and landing trap TR-19 — plus three small correctness fixes (fold-ledger write ordering, event hash-safety, corrupt-file honesty) that must be in place before any real tape is ever recorded.

## BACKGROUND

Iteration 7 finished J-05 and landed J-06 step 1 (storage capability only, not the recorder itself). The evaluator's binding depth recommendation for this iteration is `full`, and its next-step recommendation names this exact work: "Build the tape recorder next — step 2 of J-06 ... under the full pipeline with the independent checker kept in the loop ... Do not shorten it for time." That checker has caught a critical, in-run-fixed anti-goal violation in 4 of the last 4 full iterations, always at this same surface — an identity/checksum function meeting newly-populated data — so full depth is independently justified here, not just recommended.

Two carried facts shape this spec. First, `Frontend Present: yes` is declared even though this iteration is backend/CLI-only, because `browser-qa-phase.sh` gates the ENTIRE browser lane — including the required-still-passing regression set this spec names below — on that literal string; declaring `no` here would silently skip J-01/J-02/J-03/J-04/J-05/J-10's re-verification exactly as it did in iterations 4 and 5 (both ESCALATE). Second, J-06 is realistically only 1 of 5 steps in; this iteration targets step 2 only (steps 3–5 — `vault.py`, the credentialed operator-attended tranche, and the readiness refresh — are out of reach here and are not claimed).

Two prior lessons apply directly. Iter-7's identity lesson ("a field addition can be perfectly additive for READERS and still destroy an identity guarantee for WRITERS ... does this new key change what the identity function sees?") fires again: the `conditions: list[str] | None` field iter-7 added to `TradeEvent`/`QuoteEvent` makes `hash(event)` raise the instant it is non-`None` — untested until now because no prior iteration ever populated it with real values, which THIS iteration's recorder is the first thing to actually do. Iter-2's exception-isolation lesson ("any streamed research artifact needs its own explicit completeness/failure channel") governs the recorder's per-chunk `failed` outcome design, mirroring `desk_deep_backfill.py`'s already-shipped `reused`/`fetched`/`unchanged`/`failed` vocabulary rather than inventing a second one.

## IN SCOPE

### Backend

- [ ] Implement `apps/backend/app/research/tick_recorder.py`: a chunk planner (mirrors `plan_deep_windows` — computes the recording plan for a resolved universe/date-range with zero store or vendor calls), a per-chunk walker that pulls from the EXISTING `AlpacaAdapter.iter_historical_chunks` generator (zero changes to `alpaca.py` — it already yields Card-5.1-populated chunks since iter-7) and classifies each chunk `reused` / `fetched` / `unchanged` / `failed` exactly as `desk_deep_backfill.py`'s `_run_one_chunk` does (no second vocabulary), writing through the unchanged `DatasetStore.record`/`record_from_source` under the existing store discipline (duplicate key raises and is caught/classified, never propagated as a crash; corrupt files surfaced, never overwritten).
- [ ] A new, recorder-owned tick-throttle constant (a module constant embedded in `micro_parameters()`, never a new `Config` field — `historical_chunk_seconds`/`historical_chunk_max_concurrency` stay untouched; they govern the cockpit's own on-demand historical replay, a different caller) that paces consecutive chunk pulls; per-chunk checkpoint persistence so a restarted run resumes from the last committed chunk instead of the beginning.
- [ ] A single-flight compute manager + CLI entry point + REST routes mirroring `DeskDeepBackfillComputeManager`/`micro_routes.py`'s established shape exactly: `POST /research/desk/micro/recorder/compute` (trigger; a concurrent second trigger returns the in-flight run's snapshot unchanged, never a second job), `GET /research/desk/micro/recorder/compute` (poll), `POST /research/desk/micro/recorder/compute/cancel` (cooperative — finishes the in-flight chunk, rejects with 409 when idle), `GET /research/desk/micro/recorder/runs` (run history) — these are the EXACT endpoints already registered in `blueprint.md`'s Data Contract for `tick_recorder.py`, so this closes that row rather than opening a new one. One shared writer; terminal-state-only ledger writes.
- [ ] Pair the recorder with the EXISTING `desk_deep_backfill.py` machinery (`plan_deep_windows`/`run_deep_backfill`, unchanged) so each recorded symbol-day's bars are backfilled too, per goal.md J-06 step 2's explicit pairing instruction and `docs/rapid-validation-spec.md`'s Card-5.2 recipe — no second bar-fetch implementation.
- [ ] Define the dated vendor-rule cutover (the `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` constant `micro_features.py`'s docstring already reserves for this module) and the per-chunk stamping that applies it (Alpaca CTA/UTP quote sizes are `"shares"` from 2025-11-03, `"round_lots"` before), validated against the single existing `micro_features.QUOTE_SIZE_UNITS` tuple — closes J-06 step 1's deferred §2.6 clause, per iter-7's own assumption-ledger entry naming this module as where it lands.
- [ ] Implement the TR-19 trap (Card-5.1 preservation prerequisite) per `docs/rapid-validation-spec.md` §7.1 r2/§9: the recorder structurally verifies the preservation-field capability is present (a typed check) before permitting any recording, with a counter-test proving the refusal fires when simulated absent.
- [ ] Extend `test_real_data_gate.py`'s Alpaca-confinement guard to `tick_recorder.py` (passes the vendor string `"alpaca"` through the existing seam; never imports the SDK directly), mirroring `desk_deep_backfill.py`'s own compliance.
- [ ] Fix `walkforward.py`'s `run_tick_family_fold_request`: reorder so `require_sufficient_sessions_for_folds` runs BEFORE `register_fold_spec` — a below-floor request must write NOTHING to the fold ledger (today it freezes `DIAGNOSTIC_GEOMETRY` and today's manifest hash for a request that never actually ran); a sufficient corpus still registers exactly as today. Extend the existing TR-15 tests to assert the ledger is unchanged after a refused request.
- [ ] Fix `TradeEvent`/`QuoteEvent` (`providers/base.py:25-46`) so an instance carrying a real (non-`None`) `conditions` list stays safely hashable — a frozen dataclass with a `list` field raises `TypeError: unhashable type: 'list'` the moment the field is populated, which no code path has exercised until this iteration's recorder does. Project `conditions` out of the generated identity (custom `__hash__`/`eq`, or an internal tuple projection) with zero change to any other field's role, engine byte-output, or the golden trace.
- [ ] Fix `_tick_dataset_session_dates` (`walkforward.py:995`) to surface `DatasetStore.list()`'s `_errors` return value instead of silently discarding it — reuse `micro_readiness.py`'s existing `integrity_errors` reporting shape (no second error-reporting convention) so a damaged tick recording is reported, never quietly excluded from the known-session-dates count.

### Frontend

None — zero `.tsx`/frontend files this iteration. `Frontend Present: yes` above is declared solely so the browser-qa lane runs the required-still-passing regression set (see BACKGROUND); the Validation Vault `/desk` section that will eventually expose the recorder's compute button lands with J-08.

### New user-facing capability

None via the UI this iteration. Operator-only: a new CLI command (mirroring the shipped `--diagnostic`/`--family tick_legacy` shape) to run/resume/cancel a tick-recording job — hermetic and fixture-driven this iteration; real-credentialed use against actual Alpaca history is J-06 step 4, a separate future operator-attended act.

### New information displayed

None — nothing renders this iteration; J-08 wires the display.

### New user actions

None via the UI (see above — CLI-only this iteration).

### UI surface changes

None.

### Product surface delta

None visible on `/`, `/structure`, or `/desk`. The product's underlying CAPABILITY grows (a working, tested recorder exists) without any visible surface change until J-08 renders it.

### Blueprint conformance

`/desk` → Validation Vault (J-06's canonical home per `blueprint.md`'s Information Architecture) — no nav change, no new page. This iteration builds the ALREADY-registered `tick_recorder.py` owner module against its ALREADY-registered endpoint family; no blueprint edit is needed (nothing new to register).

### Data-contract additions

None. This iteration implements the row `blueprint.md` already carries verbatim from `docs/goal.md`'s Product Shape — `tick_recorder.py` → `POST/GET/POST-cancel /research/desk/micro/recorder/compute`, `GET /research/desk/micro/recorder/runs` — no new value, no second computing module, no second endpoint. (See the assumption-ledger iter-8 entry for why the route ships now, alongside the CLI, rather than CLI-only.)

## OUT OF SCOPE

- `vault.py` (J-06 step 3) — universe registration, published-split-vs-HMAC-seal assignment, exposure ledger, TR-2/TR-4/TR-12/TR-20 (all vault-owned per the current iteration-state blockers). A future iteration.
- The credentialed real-Alpaca tranche fetch, Tier-B resolution, and §7.6 minimums (J-06 step 4) — an explicit, later, operator-attended act. This iteration's tests are 100% hermetic/keyless against committed fixtures; no network call, no real API cost, no real corpus growth.
- Readiness refresh with real new shards (J-06 step 5) — depends on step 4 landing first.
- J-07 Graduation, J-08 `/desk` UI + MCP v6, J-09 pilot studies — untouched, per the natural dependency order.
- `alpaca.py` changes — none needed; the recorder is a pure new consumer of the already-Card-5.1-populated `iter_historical_chunks`.
- Any MCP tool addition or count change — the 22-tool contract stays exactly 22 this iteration; the v6 bump to 26 is J-08 scope, and the recorder itself is never named for an MCP tool in the Product Shape's 4-tool delta (readiness/scout/walkforward/vault only).
- The "request complete" honest-wording fix (iter-7 next-step item 4) — still unreachable at today's 11-session corpus (the floor refusal fires first, with or without this iteration's reorder fix); deferred until the corpus actually grows past the floor.
- The two standing owner rulings (the depletion timing stamp one quote early; whether J-01's readiness photo must show the real 12-day corpus) — human-owned; not re-planned here (carried forward unchanged in iteration-state.md).
- Framework-maintenance harness fixes (`merge_ui_test_results.py`'s bold-`**FAIL**` parsing; the screenshot-citation drift) — outside goal-mode's scope; flagged in NOTES for a separate maintenance session, not built here.

## DEFINITION OF DONE

- [ ] J-06 step 2 evidence: the hermetic test suite is green and reproduces, byte-for-byte, the `reused`/`fetched`/`failed` outcome classification, restart-without-duplicate-registration, and the TR-19 refusal — J-06 has no browser-reveal surface until J-08, so this is a CLI/test-evidence checkbox, not a browser-qa one; J-06 remains `partial` overall (steps 3–5 still absent) and this spec does not claim otherwise.
- [ ] Required-still-passing journeys J-01, J-02, J-03, J-04, J-05 remain green — RE-VERIFIED, not carried, given this iteration touches `datasets.py`/`providers/base.py` (surfaces every one of them reads) — and J-10's kept-product sentinel is green with real browser screenshots captured (deterministic replay + LLM fallback, mechanically covered at this depth because `Frontend Present: yes` is declared).
- [ ] No anti-goal violation introduced (or, if the independent auditor catches one mid-run, it is fixed and re-proven inside this same iteration, per this era's established practice).
- [ ] Unit tests pass; full backend suite count ≥ the iter-7 re-verified 3,045 pass / 8 skip, 0 new failures.
- [ ] `Config().config_fingerprint()` still prints `08e471b10130e1e2`; zero new `Config` fields; all six `referee_*.py` files hash identical to the iteration-0 listing.
- [ ] Engine equivalence (`test_observer_equivalence.py`) and the golden feature trace (`test_dense_replay_gate.py`) pass byte-unmodified.
- [ ] MCP surface stays the 22-tool contract, unchanged.
- [ ] Dev handoff written at `docs/handoffs/goal-rapid-microscope-iter-8-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-10 kept-product sentinel (cockpit `/` live tape + chart, `/structure` load + Tradable Map, every shipped `/desk` section including the three Referee sections) via the store-scoped rig, clean-rebuilt per T-9; required-still-passing replay/LLM-fallback coverage for J-01, J-02, J-03, J-04, J-05. J-06 itself has nothing to screenshot this iteration.
- Unit/integration: chunk planning purity (no store/vendor calls during planning); the four-outcome classification against a fixture-backed fake `iter_historical_chunks`; checkpoint/resume without duplicate `DatasetStore` registration; the single-flight manager's already-running and idle-cancel semantics; the CLI and routes calling the identical walker (no second implementation); TR-19; the Card-5.1 round-trip with genuinely non-`None` preservation values (extends `test_the_frozen_split_guard_still_refuses_one_tape_re_fetched_with_preservation_fields`); the dated vendor-rule stamping on both sides of 2025-11-03; the `providers/base.py` hash-safety fix; the `walkforward.py` fold-spec-ordering fix; the `_tick_dataset_session_dates` errors-channel fix; `test_real_data_gate.py`'s extended Alpaca-confinement guard; the full suite, engine-equivalence, golden-trace, fingerprint, and referee-hash re-runs.
- Error cases: a vendor-simulated failure on one chunk; a restart mid-plan; a recording attempt with the preservation-field capability simulated absent (TR-19); a `quote_size_unit` value outside `micro_features.QUOTE_SIZE_UNITS`; a corrupt/unreadable tick dataset file among otherwise-healthy recordings; a cancel call on an idle manager.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract
addition above maps to at least one concrete scenario line, numbered
sequentially, of exactly this shape:

- TC-1: given a fixture universe of 2 symbol-days with a fake `iter_historical_chunks` stand-in yielding 3 chunks per symbol-day (6 total), when the recorder's chunk planner computes the plan, then it returns exactly 6 entries in `(symbol, date, start)` order with zero `DatasetStore` calls and zero fixture-adapter calls made during planning.
- TC-2: given the fake adapter succeeds on every chunk, when the recorder CLI runs the full 6-chunk plan once, then `DatasetStore.list()` afterward shows exactly 2 new dataset records (one per symbol-day) with verifying checksums, and the recorder run ledger records the run `completed` with 6 chunk outcomes all `fetched`.
- TC-3: given a symbol-day already fully recorded from TC-2, when the recorder CLI is re-invoked for the identical universe/date range, then every chunk for that symbol-day reports outcome `reused`, zero `DatasetStore.record` calls are attempted for that key, and `DatasetStore.list()`'s record count is unchanged.
- TC-4: given the fake adapter raises on chunk 4 of 6 and succeeds on the rest, when the recorder walks the full plan, then chunk 4's outcome is `failed` with its error detail preserved verbatim, chunks 1-3 and 5-6 still complete (the walk never aborts), and no partial dataset record exists for chunk 4's symbol-day.
- TC-5: given the interrupted run from TC-4, when the recorder CLI is re-invoked with identical arguments, then only the previously-failed chunk is re-fetched (the completed chunks report `reused`), and the symbol-day's dataset record is registered exactly once afterward — proving resume without duplicate registration.
- TC-6: given the recorder's compute manager already has a run in flight, when a second trigger call is made concurrently, then it returns the SAME in-flight run's snapshot unchanged — no second job starts, no duplicate `DatasetStore` write is attempted.
- TC-7: given no recorder run is in flight, when cancel is called, then the route returns HTTP 409; given a run IS in flight, when cancel is called, then the walk stops after the current chunk finishes and is recorded, and the run ledger shows a shorter-than-planned, cancelled-class outcome list.
- TC-8: given the Card-5.1 preservation-field capability is simulated absent, when the recorder is asked to record any chunk, then it raises a typed refusal naming the missing prerequisite and zero dataset records are written — TR-19 passes.
- TC-9: given a fixture chunk carrying real non-`None` `conditions`/`exchange`/`tape`/`trade_id` values, when it is written through `DatasetStore.record` and read back, then every preservation field round-trips verbatim and the dataset's content-checksum/split-freeze identity is unaffected by which preservation values are present.
- TC-10: given two fixture chunks dated 2025-10-15 and 2025-11-10, when the dated-rule stamping is applied, then the pre-cutover row stores `quote_size_unit: "round_lots"` and the post-cutover row stores `quote_size_unit: "shares"`, both drawn from the single existing `micro_features.QUOTE_SIZE_UNITS` tuple.
- TC-11: given a caller supplies a `quote_size_unit` value outside `("shares", "round_lots", "unverified")`, when `DatasetStore.record` is called with it, then the existing iter-7 rejection fires unchanged.
- TC-12: given an event carrying a real (non-`None`) `conditions` list, when any code path calls `hash()` on that `TradeEvent`/`QuoteEvent` instance, then it returns without raising `TypeError`, and a legacy event (`conditions=None`) still hashes to the same value it did before this change.
- TC-13: given the real tick corpus (11 sessions, below the 105-session floor), when `run_tick_family_fold_request` is invoked, then the floor refusal `11 < 105` raises BEFORE `register_fold_spec` runs, and the walk-forward ledger holds zero new rows for `TICK_LEGACY_CORPUS_ID` after the call.
- TC-14: given a tick dataset directory containing one corrupt/unreadable file among otherwise-healthy recordings, when `_tick_dataset_session_dates` is called, then its caller surfaces the corrupt file via `micro_readiness.py`'s existing `integrity_errors` shape and still returns the healthy recordings' session dates correctly.
- TC-15: given `tick_recorder.py`'s test suite runs, when `test_real_data_gate.py`'s Alpaca-confinement guard executes, then the module contains no direct import of the `alpaca` SDK package and the guard passes.
- TC-16: given this iteration's full diff, when the full backend suite, `test_observer_equivalence.py`, `test_dense_replay_gate.py`, `Config().config_fingerprint()`, and the six `referee_*.py` SHA-256 listing are re-run, then the suite count is ≥ 3,045 pass / 8 skip with 0 new failures, both frozen tests pass byte-unmodified, the fingerprint prints `08e471b10130e1e2`, and every `referee_*.py` hash matches the iteration-0 listing.
- TC-17: given the store-scoped browser rig is rebuilt clean (`rm -rf apps/frontend/.next`, restart) per T-9, when the J-10 sentinel walks cockpit `/`, `/structure`, and every shipped `/desk` section, then every step captures a real screenshot (element-capture below the fold), with none recorded `unknown`.
- TC-18: given this iteration's diff, when J-01's readiness endpoint, J-02's snapshot listing, J-03's joinable-corpus read, J-04's scout-ledger chain verify, and J-05's tick-family CLI are each re-run against the real store, then every served value matches the iter-7 evaluator's own recorded baseline byte-for-byte (12 symbol-days/18 datasets/3.0089 session-equivalents; 18 snapshots/3,815,933 rows; `joinable_corpus.total` 2; scout chain `{'ok': True}`; the `11 < 105` refusal) — proving re-verification, not a carried assumption.
- TC-19: given this iteration's diff, when `test_mcp_server.py`'s `EXPECTED_TOOLS` assertion runs, then it still lists exactly 22 tool names, unchanged from iteration 7 — the v6/26-tool bump has not started.

## NOTES

- Assumption logged: `runs/goal-session-rapid-microscope/state/assumptions.md` gains one new `## iter-8 — goal-decomposer` entry explaining why the recorder's REST routes ship this iteration alongside the CLI (rather than CLI-only, the precedent iter-7 set for the walkforward tick-family request) — grounded in goal.md's own Product Shape table naming this exact endpoint family, and in `desk_deep_backfill.py` (the goal's own named precedent) shipping manager+CLI+route together.
- Escalation flag (not for this loop): the evaluator's iter-7 next-step asks a framework-maintenance session (outside goal mode) to fix `merge_ui_test_results.py`'s bold-`**FAIL**` misparse and investigate the screenshot-citation drift two lanes hit in iteration 6. Neither is planned here; surfacing so it isn't lost.
- Two owner rulings remain open and are not this iteration's job to resolve: the depletion `available_at` timing stamp one quote early (`micro_observer.py:636`/`:657`), and whether J-01's readiness photo must show the real 12-symbol-day corpus when the store-scoped rig can only ever seed 2 PG fixtures.
- If the independent auditor finds a new critical issue at this same surface (a fourth consecutive occurrence), fix and re-prove it in-run as this era has done every time so far — do not let it ride to iteration 9.

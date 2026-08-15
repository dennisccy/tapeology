# Goal Iteration 5 — J-04: matched nulls (ToD + context), the `min_attainable_p` floor fix, and the context-resolver import-guard correction

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** referee
- **Iteration:** 5
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: this iteration's own diff spans ≥3 modules
  (new `referee_null.py`, `referee_stats.py`, a project-wide import-topology guard in
  `test_referee_guards.py`) and mints three permanent, signature-bearing ids
  (`referee-null-tod-v1`, `referee-null-context-v1`, `referee-test-perm-v1`) plus a brand-new
  append-only store + compute-manager family that J-05 hypothesis records will reference
  immutably forever — a blast radius no single journey's own tests can cover today, because the
  journeys that will exercise it (J-05–J-08) do not exist yet.
- **Frontend Present:** yes (no frontend code changes this iteration — every target/rider item
  is backend/statistics; browser-qa still runs J-10's regression sentinel every iteration,
  matching iteration 4's own precedent)
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-02, J-03, J-10
- **Anti-goal reminders:** (verbatim from `docs/goal.md`; the subset this iteration's build
  surface actually touches — see `docs/goal.md` § Anti-goals for the full list)
  - 3. **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every
    KEPT surface's behaviour stay byte-identical. New work is additive and versioned beside
    them, never a mutation of them. *(critical)*
  - 5. **No lookahead** — every value computed as-of T uses only events/bars fully completed at
    T. *(critical)*
  - 6. **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - 7. **Deterministic and seeded** — every random draw uses a recorded named seed via per-row
    streams; identical requests reproduce byte-identical results; no wall-clock, no unseeded
    randomness in any research artifact. *(critical)*
  - 9. **Immutable data** — registered datasets and bar series are append-only, checksummed,
    never re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - 10. **Persistence stays scoped** — no ambient recording of live streams; recording/fetching
    is an explicit, logged act. *(critical)*
  - **CI-inversion is never a p-value.** Ordinary bootstrap quantities are uncertainty
    intervals; every p that feeds BH comes from a spec-named null-calibrated randomization
    procedure; the oracle suite guards the distinction. *(critical)*
  - **The Referee never feeds back.** No referee output gates, filters, ranks, or tunes any
    detector, context, screen, or strategy computation (import-ban + source-scan guard-tested);
    the frozen research vocabulary stays frozen. *(critical)*
  - **Host-guard caps are law.** This host (GEEKOM A7 Max mini-PC) hard-reset five times between
    2026-07-20 and 2026-07-28 under unconfined goal-mode load — instant power/VRM transient
    trips with nothing in the journal; resets #3–#5 struck while tapeology's goal mode ran
    UNGUARDED beside trendora's. When `project-extensions/host-guard/host-guard.env` declares
    ceilings (CPU mask `4-7,12-15` — the complement of trendora's — plus BLAS thread caps and
    memory/task bounds), every heavy path respects them: headless engine runs self-wrap under
    the mask, and interactive pump sessions are auto-confined in place by the engine
    (`host-guard-adopt.sh`; `scripts/automation/host-guard-exec.sh claude` is the optional
    from-birth wrapper) — the engine pauses `AWAITING_HOST_GUARD` (resumable) only when
    confinement cannot be established. Never disable, widen, or bypass these caps to make a run
    faster or a pause go away; widening the mask follows the verification ladder in
    `trendora/project-extensions/host-guard/README.md`. *(critical)*

## GOAL

Give every eligible Playbook occurrence its seeded time-of-day-matched and context-matched
comparison anchors — recorded append-only under three permanent, signature-bearing ids every
later hypothesis record will reference forever — so a future "beats chance" verdict can mean
"beats chance at a comparable time under identical measurement," not a strawman; and close,
before anything consumes them, three small already-diagnosed defects riding along from prior
iterations.

## BACKGROUND

**Priority rubric.** Rule 1 (regressed journeys first): nothing regressed at iteration 4. Rule 2
(consolidation before features): iteration 4's `coherence.md` was `COHERENCE-PASS`, not FAIL —
no mandated consolidation. Rule 3 (unblockers next): J-04 is the direct, named dependency J-05
(hypothesis records reference its null-spec ids), J-06 (estimand evaluators consume its null
records), and J-07 (the shortlist's readiness numbers) all need — it is the sole remaining link
in the `J-01 → J-02 → J-03 → J-04 → J-05 → …` chain the era's own dependency order names. Rule 4
(smallest spec wins ties): no tie — J-04 is the evaluator's own sole-named next step ("Build
J-04 'Matched nulls' next, alone, at full depth"). Rule 5 (never bundle two risky journeys): only
J-04 is a **target** journey; the three riders below touch the same already-diagnosed file
(`referee_stats.py`) or are pure test-quality tightening, deliberately additive/isolated, and do
not re-target J-01/J-02/J-03. Rule 6 (don't pick a human-blocked journey): n/a — J-04 is
buildable today, keyless, fixture-based; the one open human item (trendora's `:8255` restart) is
outside this project and does not gate it. Rule 7 (no evidence-only iterations): real code and
real proof land this iteration.

**Depth is full, trigger 1 — and it is also the evaluator's own binding recommendation.** The
dispatch's own depth recommendation for this iteration is `full`; independently, trigger 1 holds
on its own merits (see the metadata block above). Checking the other triggers for completeness:
trigger 2 (data-model migration) does not apply — every Data-Contract row this iteration fills in
was already registered at baseline from `docs/goal.md`'s own Product Shape table, and this
iteration only adds field-level shape to an already-registered, not-yet-consumed row; trigger 3
does not apply — the prior verdict (iteration 4) was `CONTINUE`, not `ESCALATE`; trigger 4
(hardening cadence) is not due (0 of 6 consecutive lean iterations dispatched — moot here since
trigger 1 already justifies full on its own).

**What J-04 builds, and why its ids are permanent.** Spec §4 (`docs/referee-statistical-spec.md`)
defines two matched-null families — `referee-null-tod-v1` (same-session, same-ToD-bucket,
remaining-time-matched anchors) and `referee-null-context-v1` (adds the registered backing-bucket
predicate via the recorded band map) — plus requires minting `referee-test-perm-v1`, the primary
test's own named signature. All three ids are parameter-blob hashes that J-05 hypothesis records
will pin immutably; changing what any of them means later is a named spec revision that re-keys
results, never a silent edit (T-1). Getting their contract right now, while nothing consumes
them, is exactly iteration 3/4's own "free to fix before anything reads it" reasoning, applied to
a new area.

**Three small riders, per iteration 4's own next-step recommendation ("ride along... rather than
making an iteration of them").**
1. **The `min_attainable_p` owner ruling (resolved this iteration — see NOTES for the ledger
   entry).** `permutation_test`'s exact-enumeration branch serves `min_attainable_p =
   1/(draws_used+1)`, a value the already-fixed method can never actually produce — the observed
   grouping is always one guaranteed member of the enumerated space and therefore always
   self-extreme, so the TRUE floor is `2/(draws_used+1)` (iteration 4's own 2,500-case sweep
   proved this: zero violations, 448 landing exactly on it). Ruled for the field's own literal
   name ("minimum ATTAINABLE") — fixed as a one-line conditional plus two direct assertions,
   confirmed via `_ATTESTATION_EXPECTED`'s own pinned fields
   (`{permutation_p, permutation_enumeration, ci_low, ci_high}`) that this touches ZERO
   attestation-checked value, so no `STATS_CORE_VERSION` bump or re-pin is needed or wanted.
2. **Non-finite rejection at the door.** J-04's anchor-measurement adapter is the FIRST code
   this era to actually produce observation values that could be non-finite — the natural,
   spec-consistent (T-5: "unmeasurable = counted exclusion, never zero") place to add it, paired
   with a fail-loud guard at the stats core's own entry (defense in depth against the exact
   *shape* of silent failure iteration 3 found: a NaN comparison is always `False` in Python, so
   an unguarded `_is_extreme` would silently under-count rather than error).
3. **TC-8's fast-path tolerance.** `test_iter4_tc8_n2_equals_1_fast_path_...` currently accepts
   anything inside a 6-standard-error band — wide enough to hide a real regression. Tightened
   this iteration, with a mutation counter-test proving the tighter band actually discriminates.

**A fourth, newly-found item: an existing import-topology guard is over-strict relative to the
canonical spec, and J-04's own Step 2 cannot be implemented without correcting it.**
`docs/goal.md`'s own Read-side law states, precisely and asymmetrically: "the Referee imports the
rail (`desk_forward._measure_from`, `_draw_anchor_indices`, the averaging helpers) **and the
context resolver (`BandMapResolver`)** — ... import-ban guards prove `desk_playbook_detect`/
`desk_playbook_context` never import referee modules **and referee modules never import the
detect module**." That second clause names only the DETECT module, not the context module — by
design, since spec §4.2 requires reading the recorded band map through `BandMapResolver` (the
context layer's OWN machinery) rather than re-deriving band membership a second time (which would
violate anti-goal 6, single source of truth, directly). But the CURRENTLY SHIPPED guard,
`test_no_referee_module_imports_the_detect_or_context_modules` (`test_referee_guards.py`), bans
BOTH `desk_playbook_detect` AND `desk_playbook_context` for every `referee_*.py` module — it has
been vacuously passing because no referee module needed the context resolver until now. This
iteration corrects it (see IN SCOPE) rather than either blocking on it or, worse, re-deriving
band-membership logic locally to dodge it. This is a genuine "extend the guard to match what the
canonical spec always said," not a weakening — the reverse direction and the detect-module ban
are untouched.

**Lessons applied.** iter-1 (`lessons.md`): no golden replay script exists or can exist for this
backend-only journey — verification is pytest + CLI, not replay. iter-2: never use pattern-based
process kills (`pkill -f uvicorn`) — this host still has trendora's port-8255 backend down from
exactly that mistake at iteration 2; use exact-PID kills only. iter-4: a floor/boundary test is
only as good as the regime its generator samples — every new floor-adjacent test below (TC-10,
TC-15) generates in the sensitive regime and asserts HOW OFTEN the boundary is actually reached,
not just that it is never crossed.

## IN SCOPE

### Backend

- [ ] Build `app/research/referee_null.py` implementing spec §4.1 (`referee-null-tod-v1`): for
  each eligible occurrence (primary-horizon-complete, drawn from the J-02 observation contract
  via the J-01 readiness fold), draw `K = REFEREE_NULL_ANCHORS_PER_OCCURRENCE` (4) seeded anchors
  — same symbol, same measurement series, same ToD bucket, remaining-time-matched eligibility for
  fixed horizons (ToD-bucket-only eligibility for `to_close` primaries), excluding the
  occurrence's own trigger/anchor bar, without replacement — via the **imported**
  `desk_forward._draw_anchor_indices` (zero diff to `desk_forward.py`, per the Read-side law: this
  is a direct cross-module import, NOT a local reimplementation — do not confuse this with
  `referee_stats.py`'s own `_draw_indices_without_replacement`, which is a deliberately
  import-decoupled "matched idiom" that exists ONLY because `referee_stats.py` carries its own
  stricter import ban; see NOTES). Measure every anchor through the imported
  `desk_forward._measure_from` at `entry_kind="close"` with the occurrence's own side sign.
  Disclose `k_drawn = min(K, eligible)` and `eligible_count`; a zero-eligible occurrence is
  excluded and counted, never silently dropped; disclose the mean anchor-window-overlap fraction
  (§4.1's same-session power-cost disclosure).
- [ ] Build the `referee-null-context-v1` variant (spec §4.2): as above, plus every anchor bar's
  close must additionally satisfy the registered backing-bucket predicate via the **imported**
  `desk_playbook_context.BandMapResolver` over the recorded band map for `(symbol, basis_day)`;
  `room_r` at the anchor borrows the paired occurrence's own risk distance
  (`risk_source="paired_signal"`, the shipped convention); serve per-cell anchor eligibility
  rates; a cell whose anchors cannot be found is an exclusion disclosure, never a substitution.
- [ ] Correct the import-topology guard (`test_referee_guards.py`) to match
  `docs/goal.md`'s own asymmetric Read-side law (see BACKGROUND): split
  `test_no_referee_module_imports_the_detect_or_context_modules` into (a) an UNCHANGED,
  still-blanket ban on `desk_playbook_detect` for every `referee_*.py` module (zero exceptions),
  and (b) a narrower, explicitly-commented allowance that `referee_null.py` importing
  `desk_playbook_context` is SANCTIONED (cite the exact `docs/goal.md` sentence in the code
  comment), while every OTHER referee module (`referee_evidence.py`, `referee_stats.py`,
  `referee_routes.py`) stays banned from `desk_playbook_context` too — only the module that
  actually needs `BandMapResolver` gets the exception, nothing wider. The REVERSE-direction guard
  (`test_the_detect_and_context_modules_import_no_referee_module`) is UNTOUCHED — `desk_playbook_
  detect.py`/`desk_playbook_context.py` still never import any `referee_*` module, in either
  direction, no exception. Add a can-fail counter-test for the new narrower rule (mirroring this
  file's own established "guard can fail on a seeded violation" pattern). `referee_stats.py`'s
  OWN separate, stricter ban (TC-23 in the existing suite) is untouched — it still bans
  `desk_playbook_context` too, since it stays estimand-agnostic.
- [ ] Mint the three named, signature-bearing spec ids per spec §1/§4.1/§4.3 —
  `referee-null-tod-v1`, `referee-null-context-v1`, `referee-test-perm-v1` — each hashing its OWN
  full parameter blob (the established `_canonical`/`sha256[:16]` pattern
  `referee_evidence.py`'s `current_playbook_detector_basis()` already uses), read at call time,
  embedded verbatim in every null record, changing if any parameter inside that id's own blob
  changes (counter-tested per id). `referee-test-perm-v1`'s blob is exactly spec §1's stated
  contents (weights formula identity, sidedness handling, enumeration rule, p convention) — do
  not invent additional inputs. File placement (co-located in `referee_null.py`, or a small
  shared helper) is an implementation choice; the behavior contract above is fixed.
- [ ] Build the append-only null store: env-var-or-sibling default `TAPEOLOGY_DESK_REFEREE_
  NULL_DIR` (module constant, NOT a `Config` field, matching the era's named `_NULL_DIR` family),
  keyed `(observation_id, null_spec_signature)`; duplicate key raises; a corrupt file is
  surfaced, never overwritten; no update/delete/supersede path (source-scan guard-tested,
  matching the existing store-discipline guard pattern).
- [ ] Build the run ledger (its own `_LOG_DIR`-family sibling default) + a compute-manager trio
  for null builds, reusing the shipped `desk_playbook_compute.py` pattern: single-flight per
  null-spec, snapshot-pollable progress, cancel, CLI-runnable, one shared
  `run_null_build_and_record` writer, terminal-state-only ledger writes.
- [ ] `GET /research/desk/referee/nulls` (optionally `?id=`) serves recorded null records with
  honest absence — never computes at GET time (T-8); `POST /research/desk/referee/nulls/compute`
  starts a build, `GET /research/desk/referee/nulls/compute` polls progress, a cancel endpoint
  stops an in-flight build; `GET /research/desk/referee/nulls/runs` serves the ledger — matching
  the route shape already registered in `state/blueprint.md`.
- [ ] In `referee_stats.py`'s `permutation_test`: fix `min_attainable_p` to
  `2.0 / (draws_used + 1)` when `use_enumeration` is true (the observed grouping is always one
  guaranteed member of the enumerated space, therefore always self-extreme — the same guarantee
  the iteration 3/4 floor fix already proved) and leave it `1.0 / (draws_used + 1)` in the seeded
  (Monte Carlo) branch, unchanged. The ONLY line touched is the `min_attainable_p` computation in
  the shared return-dict construction — no other line in `permutation_test`, `_t_statistic`, or
  the seeded branch's own draw logic changes. Do NOT bump `STATS_CORE_VERSION` or re-pin
  `_ATTESTATION_EXPECTED`/re-run `run_oracle_attestation()`'s capture (see NOTES: this field is
  not one of the four attestation-pinned fields).
- [ ] In `referee_stats.py`: add a finite-value validation covering `_t_statistic`'s own inputs
  (protecting `permutation_test`, `sign_flip_result`, and `equal_weight_t`, which all call it
  first) AND `bootstrap_ci_occurrence`/`bootstrap_ci_cluster`'s own inputs — a `ValueError` raised
  immediately on any non-finite (`NaN`/`inf`) value, so a bad value fails LOUDLY at the stats
  core's own door instead of silently propagating through `math.fsum` and corrupting `_is_extreme`
  comparisons (a NaN comparison is always `False` in Python — the same silent, oracle-invisible
  failure shape as the iteration-3 bug). One shared small helper checked at each of the module's
  relevant public entry points is the simplest correct shape; exact call-site organization is an
  implementation choice. A single check at input time suffices — sums/differences/quotients of
  already-finite numbers stay finite by construction, so no per-draw re-validation is needed.
- [ ] In `referee_null.py`'s anchor-measurement adapter: reject a non-finite `_measure_from`
  result at the door — exclude that single anchor (not the whole occurrence), add it to a served
  exclusion-count field, and continue with the occurrence's other eligible anchors — following
  T-5's "unmeasurable = counted exclusion, never zero" pattern exactly (the adapter-layer
  behavior is deliberately different from the stats-core's fail-loud behavior above — see NOTES).
- [ ] Tighten `test_iter4_tc8_n2_equals_1_fast_path_matches_a_from_scratch_general_algorithm_
  reference` (`test_referee_stats.py`): reduce the tolerance from `6.0` to `≤3.5` standard errors
  AND/OR raise `b` enough to shrink the absolute SE at the tighter multiplier; the test must still
  pass deterministically on its existing pinned seed. Add a companion mutation check: a
  deliberately-reintroduced incorrect `n2 == 1` fast-path formula FAILS under the tightened band —
  proving the tightened band actually discriminates a real regression, not merely that its number
  is smaller.
- [ ] Zero new `Config` fields; zero diff to `desk_forward.py` (import-only additions, no logic
  edits), `desk_playbook_context.py` (import-only), `desk_playbook.py`, `levels.py`,
  `tradability.py`, `setups.py`, `edge_report*.py`, `backtests.py`, `pnl_scan.py`,
  `app/config.py`, `app/main.py`, and `docs/referee-statistical-spec.md` (this iteration
  implements the spec's already-stated definitions — it reinterprets nothing the spec defines).

### Frontend

- (none — J-04 is `(Keyless; automated.)`; the `/desk` Referee Runs section that will one day
  read this machinery is J-09's job, per the blueprint's own Information Architecture row)

### New user-facing capability

None directly — this iteration is backend/library work. A CLI + POST/GET compute-control surface
exists for operator/automation use, matching the shipped compute-manager pattern, but is not yet
wired to any page; that wiring is J-09's job.

### New information displayed

None (no UI change this iteration).

### New user actions

None (no UI change this iteration).

### UI surface changes

None.

### Product surface delta

None visible to a user browsing the app this iteration. The backend gains the matched-null
machinery and its three permanent spec ids that J-05 onward builds directly on.

### Blueprint conformance

Matches the already-registered `state/blueprint.md` Information Architecture row: "J-04 matched
nulls — compute controls + ledger | `/desk` → **Referee Runs** | Desk." No nav change. The
Referee Runs section itself renders in J-09; this iteration only builds what J-09 will read.

### Data-contract additions

The two rows this iteration fills in were ALREADY registered in `state/blueprint.md` at
baseline, verbatim from `docs/goal.md`'s Product Shape table ("Matched-null records" →
`referee_null.py` → `GET /research/desk/referee/nulls`; "Null compute progress + runs" → same
module → the compute/runs routes). This iteration adds the field-level shape (appended as a note
to `state/blueprint.md`, matching the iteration-4 precedent for `stale_basis_dates`); owner and
endpoint are UNCHANGED from the already-registered row:

- **Null record:** `null_record_id: str` (pure function of `(observation_id,
  null_spec_signature)`), `null_spec_id: "referee-null-tod-v1"|"referee-null-context-v1"`,
  `null_spec_signature: str` (sha256[:16] of that id's full parameter blob), `observation_id:
  str`, `symbol: str`, `session_date: "YYYY-MM-DD"`, `side: "long"|"short"`, `tod_bucket:
  "open"|"mid"|"close"`, `k_requested: int`, `k_drawn: int`, `eligible_count: int`, `excluded:
  bool`, `anchors: list[{anchor_ts: str (ISO-8601 UTC), measure_key: str, value: float,
  window_overlap_fraction: float, backing_bucket_match: bool|None}]`, `mean_window_overlap:
  float|None`, `non_finite_excluded_count: int`, `backing_bucket_eligibility_rate: float|None`
  (context variant only), `context_algorithm_version: str|None`, `provenance:
  {config_fingerprint: str, computed_at: str (ISO-8601 UTC)}`.
- **Run-ledger record:** `run_id: str`, `null_spec_id: str`, `state:
  "running"|"completed"|"failed"|"cancelled"`, `started_at: str`, `finished_at: str|None`,
  `progress: {done: int, total: int}`, `error: str|None`.

No other Data-Contract row is touched. `permutation_test`'s `min_attainable_p` fix is NOT a
Data-contract addition — it is an existing internal field of a library function with no route of
its own (blueprint IA: "J-03 stats core ... n/a — consumed by J-04–J-09").

## OUT OF SCOPE

- J-05 (registry), J-06 (adjudication engines), J-07 (starter family + registration UI), J-08
  (promotion interlock), J-09 (the `/desk` Referee sections + MCP v5) — all wait on this
  iteration per the natural dependency order.
- Any change to `desk_forward.py`'s, `desk_playbook_context.py`'s, `desk_playbook.py`'s,
  `levels.py`'s, or `tradability.py`'s own LOGIC — J-04 imports only (import-ban guard-tested).
- Any change to `referee_stats.py`'s already-fixed exact-enumeration `p`/`t` computation, the
  seeded branch's own draw logic, or any of its constants — per the binding "Do not redo" list;
  the only `referee_stats.py` changes this iteration are the `min_attainable_p` conditional and
  the new finite-value guard.
- Bumping `STATS_CORE_VERSION` or re-pinning the oracle attestation — the `min_attainable_p` fix
  touches none of `_ATTESTATION_EXPECTED`'s four pinned fields.
- Extending `test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` or re-deriving
  `test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` — both stay untouched, matching
  the precedent J-01–J-03 already set (deferred to J-09, when referee numerics first reach a
  page; the refresh chain is untouched by referee work entirely).
- Any MCP tool addition — the connector stays at 20 tools; the 22-tool contract is J-09's job.
- Any real-corpus null-building compute run — J-04's Acceptance is fixture-based/hermetic; a real
  run against the 3,222-signal corpus is a future explicit operator act once J-05/J-06/J-07 need
  it.
- Resolving the carried "Lead 2" ambiguity (`_strategy_observation()`'s `epoch_anchor =
  dataset.get("epoch_anchor") or 0.0`) — still open, still needed before J-06, not before J-04
  (J-04 never calls `_strategy_observation()`); leave it exactly as iteration 4 left it.
- Any strategy-family matched-null work — spec §3.7 keeps the strategy family's null unmatched
  (uniform-random) this era; that is J-08's territory, not J-04's.
- Any new `Config` field — every new constant is a module constant read by a
  `<module>_parameters()`-style function, per the era's Path-A-only discipline.
- Widening the context-resolver import allowance beyond `referee_null.py` — `referee_evidence.py`
  and `referee_stats.py` gain no new import permissions this iteration.

## DEFINITION OF DONE

- [ ] J-04 passes: both null variants (`referee-null-tod-v1`, `referee-null-context-v1`)
  implemented per spec §4.1/§4.2, with every Acceptance clause (shortfall, zero-eligible
  exclusion, remaining-time boundary, convention-identity, lookahead-clean, idempotent re-run,
  old-stores-untouched) independently verified, not just reported
- [ ] Required-still-passing journeys J-01, J-02, J-03 remain green (re-run their own test files
  directly; `referee_stats.py` changed this iteration, so J-03 gets a full direct re-check, never
  deferred-budget)
- [ ] J-10 kept-product half re-verified in a real browser after a clean rebuild (T-9): full
  suite green, engine equivalence, fingerprint pin `08e471b10130e1e2` unchanged, MCP tool count
  still 20, the annualization guard green
- [ ] No anti-goal violation introduced (no lookahead in anchor eligibility, no unseeded draw,
  zero diff to any frozen module's logic, referee output feeds back into nothing, the corrected
  import guard still bans everything it should)
- [ ] `permutation_test`'s `min_attainable_p` is a true floor (`2/(draws_used+1)` in exact mode,
  `1/(draws_used+1)` in seeded mode) — proven by a sweep, not merely recomputed differently
- [ ] The non-finite guard rejects NaN/inf at both the stats-core door and the null adapter's own
  measurement step, each with a passing unit test
- [ ] TC-8's fast-path equivalence test is materially tighter (≤ 3.5 SE or the raised-`b`
  equivalent) and TC-15's mutation counter-test fails against the reintroduced incorrect formula
- [ ] Unit tests pass; no regressions; full suite count ≥ the iteration-4 count (2,513 collected
  / 2,505 passed / 8 skipped), never shrinks
- [ ] Dev handoff written at `docs/handoffs/goal-referee-iter-5-dev.md`, with its click-through
  doc fully filled in — no "fill in"/placeholder/TODO text (iteration 4's closure failed on
  exactly this; see NOTES)

## TESTING REQUIREMENTS

- Browser: J-04 itself carries no browser acceptance and no golden replay is possible for it
  (iter-1 lesson: `demo_runner.py` resolves every replay step against the single frontend origin,
  so a backend-only endpoint cannot be replayed). J-10's regression sentinel still requires the
  full kept-product browser walk (cockpit sim tape + chart, `/structure` pinned-AAPL Load, every
  shipped `/desk` section) with fresh screenshots after the T-9 clean rebuild, matching every
  prior iteration's practice.
- Unit/integration: new `test_referee_null.py` for both null variants' fixture goldens;
  `test_referee_stats.py` extensions for `min_attainable_p`, the finite-value guard, and the
  tightened TC-8; a store-discipline test (duplicate key raises, no update/delete path —
  source-scan guard); a compute-manager test (single-flight rejects a concurrent second build for
  the same null-spec; cancel reaches a terminal state); a CLI smoke test; `test_referee_guards.py`
  extensions for the corrected import-topology rule (both directions, both the allowed and the
  still-banned cases, each with its own can-fail counter-test).
- Error cases: a non-finite anchor measurement; a duplicate null-record key; a concurrent second
  compute request while one is in flight; a cancel request; an unknown/malformed null-spec id; a
  seeded fixture simulating a referee module importing `desk_playbook_detect` (must still fail
  the guard).

TC-1: given a fixture occurrence with exactly `K=4` ToD-bucket-eligible, remaining-time-eligible
anchor bars in its own session, when `referee-null-tod-v1` builds its null set, then the stored
record's `k_drawn == 4`, `eligible_count == 4`, `excluded == False`, and the 4 anchor indices
match a hand-computed Fisher–Yates draw from the pinned seed.

TC-2: given a fixture occurrence with only 2 eligible anchor bars, when the null set is built,
then `k_drawn == 2`, `eligible_count == 2`, and the shortfall (`k_requested - k_drawn == 2`) is a
served field, not silently absent.

TC-3: given a fixture occurrence with 0 eligible anchor bars, when the null set is built, then
the occurrence is excluded, `excluded == True`, `eligible_count == 0`, and it is counted in the
readiness fold's exclusion tally, never silently dropped.

TC-4: given a fixture occurrence with a `1h` primary horizon and session bars at 5-minute
granularity, when eligibility is evaluated for a candidate anchor bar at exactly 15:00 ET (60 min
remaining before the 16:00 close) versus one at 15:05 ET (55 min remaining), then the 15:00 bar
is ELIGIBLE (≥ 60 min) and the 15:05 bar is INELIGIBLE (< 60 min) — both sides hand-verified
against spec §4.1's remaining-time rule.

TC-5: given a fixture occurrence and its registered backing-bucket predicate (`at_wall`), when
`referee-null-context-v1` builds its null set, then every stored anchor's close satisfies the
predicate via `BandMapResolver` over the recorded band map, at least one candidate anchor that
fails the predicate is excluded and reflected in the served per-cell eligibility rate, and
`room_r` on each anchor equals the paired occurrence's own risk distance.

TC-6: given a synthetic anchor bar, when it is measured through `referee_null.py`'s anchor path
and directly through `desk_forward._measure_from` with identical arguments, then both return
byte-identical `value`/`return_pct` fields (convention identity, zero diff to the rail).

TC-7: given a fixture session truncated immediately after an occurrence's trigger bar, when the
null set is rebuilt, then every anchor and measurement recorded before the truncation point is
unchanged (lookahead-clean).

TC-8: given a null set already recorded for `(observation_id, null_spec_signature)`, when the
compute manager runs again under identical pins, then no duplicate record is written and the
store's file count/SHA-256 for that key is unchanged (idempotent reuse).

TC-9: given the playbook, evidence, and stats stores as they existed at the start of this
iteration, when the full null-build test suite runs, then every pre-existing store file's
SHA-256 is unchanged (old stores untouched).

TC-10: given a `permutation_test` call whose informative-session shape forces
`use_enumeration = True`, when the result dict is read, then `min_attainable_p == 2.0 /
(draws_used + 1)`, and across a ≥1,000-case seeded sweep in the tail regime (groups deliberately
shifted apart, per the iter-4 sampling lesson) the returned `p` is never below `min_attainable_p`,
with at least 100 cases landing exactly on it (a can-fail guard proving the sweep actually reaches
the boundary).

TC-11: given a `permutation_test` call whose shape forces the seeded (Monte Carlo) branch, when
the result dict is read, then `min_attainable_p == 1.0 / (draws_used + 1)`, unchanged from before
this iteration (regression guard).

TC-12: given a `session_groups` input containing one `NaN` or `inf` value, when `_t_statistic`
(or any of `permutation_test`/`sign_flip_result`/`equal_weight_t`/the bootstrap functions) is
invoked, then a `ValueError` is raised immediately — no `p`/`t`/CI is silently returned.

TC-13: given a fixture occurrence whose `_measure_from` result is non-finite, when
`referee_null.py`'s anchor adapter processes it, then that single anchor is excluded and counted
in a served exclusion field, the occurrence's other eligible anchors are unaffected, and no
exception propagates out of the null build.

TC-14: given the tightened `test_iter4_tc8_...` fast-path test, when it runs on its existing
pinned seed, then it still passes at the new tolerance (≤3.5 SE or the raised-`b` equivalent).

TC-15: given a deliberately-reintroduced incorrect `n2 == 1` fast-path formula (the mutation
counter-test), when the tightened TC-8 test runs against it, then the test FAILS.

TC-16: given the three spec ids (`referee-null-tod-v1`, `referee-null-context-v1`,
`referee-test-perm-v1`), when their parameter blobs are hashed, then each signature is stable
across repeated calls with identical parameters and changes when any one parameter in that id's
own blob changes (counter-tested per id).

TC-17: given no null records exist yet for a symbol, when `GET /research/desk/referee/nulls` is
called, then it serves an honest empty/absent state and triggers no compute (GETs never
compute — T-8).

TC-18: given a completed null build, when `GET /research/desk/referee/nulls/runs` is called,
then the ledger record's `run_id`/`state`/`progress`/`null_spec_id` fields are served and
`state == "completed"`.

TC-19: given a null build already running for a given null-spec, when a second build request for
the SAME null-spec is issued, then it is refused/queued single-flight, never run concurrently.

TC-20: given an in-flight null build, when a cancel request is issued, then the run ledger
records a `cancelled` terminal state and no partial/duplicate record is written.

TC-21: given the corrected import-topology guard, when `referee_null.py`'s actual imports are
scanned, then `desk_playbook_context` is present and does NOT fail the guard while
`desk_playbook_detect` is absent; when a seeded fixture simulates ANY referee module (including
`referee_null.py`) importing `desk_playbook_detect`, the guard FAILS; when a seeded fixture
simulates `desk_playbook_detect.py`/`desk_playbook_context.py` importing a `referee_*` module,
the reverse-direction guard still FAILS, unchanged from before this iteration.

TC-22: given the full backend suite after this iteration's changes, when it runs, then it
collects/passes at least the iteration-4 count (2,513 collected / 2,505 passed / 8 skipped) with
zero new failures, `Config().config_fingerprint()` still prints `08e471b10130e1e2`, and
`test_mcp_server.py`'s `EXPECTED_TOOLS` count is still 20.

TC-23: given the completed dev handoff, when `docs/handoffs/goal-referee-iter-5-dev.md` and its
click-through doc are read, then no field contains a "fill in"/placeholder/TODO string.

## NOTES

- **Owner ruling (logged to the assumption ledger).** `min_attainable_p` is ruled to mean "the
  true minimum p this test CAN produce" (the field's own name), not "the naive granularity
  reading" — matching the exact-enumeration floor `2/(draws_used+1)` iteration 3/4's fix already
  proved, and matching the era's fail-closed/honesty ethos (a disclosure that overstates
  reachability could let a future hypothesis register a target p it can never meet). Confirmed
  zero-blast-radius: `_ATTESTATION_EXPECTED` pins exactly `{permutation_p,
  permutation_enumeration, ci_low, ci_high}` — `min_attainable_p` is not one of them, so no
  `STATS_CORE_VERSION` bump or re-pin follows from this fix. See
  `runs/goal-session-referee/state/assumptions.md`, iter-5 entry.
- **Two draw-without-replacement helpers exist, on purpose — do not merge them.**
  `referee_stats.py`'s `_draw_indices_without_replacement` and `desk_forward.py`'s
  `_draw_anchor_indices` are the SAME Fisher–Yates idiom implemented twice, deliberately: the
  former exists because `referee_stats.py` carries its OWN, stricter import ban (the iteration-3-authored `referee_stats.py`-scoped guard in
  `test_referee_guards.py` — a DIFFERENT check from this iteration's own TC-23 above — it never imports `desk_forward`, staying estimand-agnostic, since it
  is also used for the strategy family, which has no bars at all). `referee_null.py` has no such
  constraint and directly needs `desk_forward._measure_from` regardless, so it imports
  `desk_forward._draw_anchor_indices` too, per the Read-side law — it does NOT call
  `referee_stats.py`'s copy. Two implementations of the same tiny idiom in two import-scopes that
  cannot share it is not a "second implementation of the measurement rail" violation (that anti-
  goal is about `_measure_from`-class computation, which stays single-sourced); it is already the
  shipped, reviewed shape.
- **Adapter-layer exclusion vs. stats-core fail-loud are deliberately different responses to the
  same underlying concern.** `referee_null.py`'s anchor adapter EXCLUDES-and-COUNTS a non-finite
  measurement (T-5's normal, disclosed "unmeasurable" pattern, at the layer that still knows which
  observation is being built). `referee_stats.py`'s new guard RAISES (fail loud) on a non-finite
  value reaching the stats core, because at that layer a non-finite value can only mean an
  upstream adapter bug, not a normal exclusion case — the stats core has no per-observation
  identity left to attach a disclosure to.
- **Process reminder (do not repeat iteration 4's failure mode).** Iteration 4's dev handoff left
  a literal "fill in" placeholder in its click-through doc, which failed CLOSURE even though the
  code itself was fine and later landed (`f0c6d3a`). Fill in every field for real this time.
- **Host safety reminder.** Do not use pattern-based process kills (`pkill -f uvicorn`/`pkill -f
  "uvicorn main:app"`) to stop any dev server — this host runs an unrelated project (trendora)
  whose port-8255 backend was killed this way at iteration 2 and is STILL down; use exact-PID
  kills only, captured before the kill. For a human, still outstanding from iteration 2: please
  restart trendora's backend on port 8255.
- **Carried, not actioned.** The `_strategy_observation()` `epoch_anchor = dataset.get
  ("epoch_anchor") or 0.0` ambiguity (open under T-1 since iteration 2/4) still needs a ruling
  before J-06, not before J-04 — leave it exactly as iteration 4 left it.
- **Escalation flag:** none — the one ambiguity found (the `min_attainable_p` reading) is ruled
  above; the one open human item (trendora restart) is non-blocking and outside this project.

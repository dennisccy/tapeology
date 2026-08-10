# Goal Iteration 2 — Every signal measured (J-02): trigger-anchored forward returns on the desk's own rail

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: J-02 stands up a NEW interacting compute-manager
  subsystem (`desk_playbook_compute.py` single-flight manager + CLI, `desk_playbook_log.py`
  terminal-state-only ledger) wired into the already-extended `desk_playbook.py` (`compute_playbook`
  now measures every signal in the same walk) and new `desk_routes.py` endpoints — ≥3
  new/touched interacting modules — while embedding a critical anti-goal risk that crosses module
  boundaries by construction: "no second implementation of the measurement rail" is only true if
  every horizon/MDD/truncation/seed computation is IMPORTED from `desk_forward.py`, never
  re-derived. That risk class is exactly what the fuller pipeline's design/review/audit scrutiny
  exists for (it is also the evaluator's own stated rationale in
  `runs/goal-session-playbook/iter-1/eval.md`: "that 'do not copy the rail' rule is one of the
  era's hard rules, so the fuller review and audit pass is worth it").
- **Frontend Present:** no
- **Target journeys:** J-02
- **Required-still-passing journeys:** J-01, J-10
- **Anti-goal reminders:**
  - **No execution path, ever** — no brokerage/trading API, no order tickets, no live OR paper
    trading, no "just to test" exceptions. (`apps/backend/tests/test_no_execution_path.py` is the
    tier-1 guard; new research code adds matching guard tests, never weakens them.) *(critical)*
  - **No profit claims and no advice** — every $ figure is a simulated measurement carrying R, n,
    fee/slippage assumptions, and its train/hold-out/forward basis. No prediction language, no
    imperative trading cues. *(critical)*
  - **Frozen foundations** — the `v1` strategy, the `default` profile, the tape engine's five
    states and thresholds, the frozen structure computations, the JSON `BarStore`, and every KEPT
    surface's behaviour stay byte-identical. New work is additive and versioned beside them, never
    a mutation of them. *(critical)*
  - **No lookahead** — every value computed as-of T uses only events/bars fully completed at T.
    *(critical)*
  - **Single source of truth** — each shared value is computed once, owned by one canonical
    endpoint, and read verbatim by REST/WS/UI/MCP/reports. The coherence-auditor hard-fails
    violations. *(critical)*
  - **Deterministic and seeded** — every random draw uses a config-owned recorded seed; identical
    requests reproduce byte-identical results; no wall-clock, no unseeded randomness in any
    research artifact.
  - **Immutable data** — registered datasets and bar series are append-only, checksummed, never
    re-tagged, never deleted, never content-perturbed. Splits are frozen at registration.
    *(critical)*
  - **Era-B desk anti-goals that remain binding:** membership is never a signal; snapshots are
    append-only and pinned; every run is an explicit operator act; the briefing describes, never
    advises; no new statistics, gates, or strategies; the demolition stays demolished; the ledger
    never holds orders; the suite stays keyless and hermetic; the fingerprint pin does not move.
    *(all critical)*
  - **No threshold exists outside the spec, and no code path sweeps one.** Every detector rule and
    threshold exists in [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) BEFORE the
    code that uses it; no code path iterates thresholds against outcomes (source-scan
    guard-tested); a threshold change is a spec revision + new signature, never an edit of recorded
    signals and never a sweep. *(critical)*
  - **A signal is an observation, not a call.** No signal, chip, or evidence cell uses advice,
    imperative, prediction, probability, expectancy, edge, or significance language; the served
    registers state what was NOT measured (no fills, no costs, returns not stop-adjusted);
    `invalidation_price` is geometry, never an order concept. *(critical)*
  - **No recorded playbook file is ever rewritten, backfilled, pruned, or superseded in v1.** New
    signatures mint new versions beside old ones; a corrupt file is surfaced loudly, never
    overwritten; the store exposes no update or delete method (source-scan guard-tested).
    *(critical)*
  - **No second implementation of the measurement rail.** Measurement helpers are imported from
    `desk_forward.py` with a zero diff to that file; no playbook module re-implements horizons,
    MDD, truncation, or the seed discipline (import-graph guard-tested). *(critical)*

## GOAL

For any already-detected opening-range-break signal, the desk now measures what price actually did
afterward — using the exact same forward-return, dual-max-drawdown, truncation, and seeded-random-
baseline conventions the desk's wall-touch rail already uses — and permanently records that
measurement plus an honest invalidation-breach disclosure, readable through the same
`GET /research/desk/playbook` endpoint and triggerable via a new compute-progress/run-ledger
surface; no UI ships yet, but every signal recorded from here on carries a real, rail-identical
measurement instead of geometry alone.

## BACKGROUND

Iteration 1 shipped J-01 genuinely done (43/43 new tests, evaluator-verified live) and the
evaluator's next-step recommendation (`runs/goal-session-playbook/iter-1/eval.md`) named J-02 next
at full depth — the natural dependency-order unblocker (`docs/goal.md`: "J-01 → J-02 → J-03") that
every remaining journey needs, since J-03's UI has nothing measured to render without it. Per the
priority rubric this is the clear pick: nothing regressed (rule 1 n/a), the last coherence audit was
`COHERENCE-PASS` so no consolidation is owed (rule 2 n/a), J-02 is the textbook unblocker (rule 3),
and it is the only journey in natural dependency order so there is no tie to break (rule 4). Depth
is `full` per the evaluator's binding recommendation, independently satisfying **Full trigger 1**
(see Goal Mode Metadata). Three small carried items ride inside this same cycle per the evaluator's
explicit instruction rather than becoming their own iteration: the J-10 golden-replay evidence gap,
three audit-identified test gaps, and two spec-doc documentation catch-ups (detail below and in
NOTES).

**Two lessons apply directly and are baked into this spec's DoD/TESTING, not just noted:**
(1) *iter-1 lesson 2* — a backend-only iteration silently drops its Required-still-passing browser
replay because the browser lane self-disables on `Frontend Present: no`; that happened to J-10 last
iteration and this iteration is backend-only again, so the replay is demanded explicitly below
(DEFINITION OF DONE, TC-21) rather than left to the lane's default behavior. (2) *iter-1 lesson 3* —
positional bar-slot indexing fabricated data on a gapped session in J-01's opening-range primitive;
J-02 introduces its OWN new positional risk (the spec's 5m→1m anchor mapping, "first 1m bar of the
trigger window whose [low, high] contains T, falling back to the window's first 1m bar" —
`docs/playbook-detector-spec.md` §0) and must not repeat the class of bug, so a dedicated
gapped-anchor-window fixture is required (TC-19), not just the existing piece-level primitive tests.

## IN SCOPE

### Backend

- [ ] Extend `app/research/desk_playbook.py`'s `compute_playbook` to measure every detected signal
  in the SAME walk: resolve the finest series the session holds (1m when the session carries any,
  else 5m — session-level, not per-signal); map the signal's 5m trigger bar to its own 1m window per
  spec §0 (first 1m bar whose `[low, high]` contains `T`, falling back to the window's first 1m
  bar); reuse the signal's ALREADY-detected `entry`/`entry_kind` verbatim (spec §0's stop-through
  convention — computed at J-01 detection time, never re-derived here); call `_measure_from`
  (imported from `desk_forward.py:451`) with explicit `sign = +1` long / `-1` short; attach the
  resulting rail-shaped `forward` block to the signal.
- [ ] Compute `invalidation_breached` (per-horizon boolean + `first_breach_minutes`) in the SAME
  pass, OUTSIDE `_measure_from` (never inside it — the rail's own served shape must not change);
  declare its keys inside the `parameters` blob via the already-existing `PLAYBOOK_SIGNAL_MEASURES`
  constant (`desk_playbook.py:137`, already `= DESK_FORWARD_MEASURE_KEYS` since J-01's birth).
- [ ] Baseline anchors per `(symbol, setup_id)`: seeded per-row stream
  `f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"`, `k = min(capped signal
  count, session bar count)`, anchor entry = anchor bar close, indices drawn via `_draw_anchor_indices`
  (imported from `desk_forward.py:428`); a per-(setup_id, side) `summary` block built with the rail's
  OWN averaging helpers (`desk_forward.py:564-623`, imported not copied); explicit beyond-cap
  disclosure when raw signal count exceeds the cap.
- [ ] New `app/research/desk_playbook_compute.py` — a single-flight manager trio + CLI mirroring
  `desk_forward_compute.py`'s `DeskForwardComputeManager`/`run_forward_and_record` shape
  (snapshot-pollable progress, cooperative cancel, ONE shared `run_playbook_and_record` writer that
  resolves the 2-pin key BEFORE any measurement walk and reuses honestly on a match).
- [ ] New `app/research/desk_playbook_log.py` — a terminal-state-only run ledger mirroring
  `desk_forward_log.py`/`desk_topup_log.py` (a cancelled/interrupted run writes NOTHING).
- [ ] `desk_routes.py`: new `POST/GET/POST-cancel /research/desk/playbook/compute` and
  `GET /research/desk/playbook/runs`, wired the same way `get_forward_store`/the forward-compute
  routes already are (`get_playbook_store` already exists at `desk_routes.py:956` for the J-01 GET).
- [ ] Convention-identity test: a synthetic anchor measured through the playbook's own call site and
  directly through `desk_forward._measure_from` with identical arguments produce byte-identical
  leaves.
- [ ] Embedded-constants counter-test: monkeypatching a rail constant already embedded in
  `playbook_parameters()` (e.g. `DESK_FORWARD_BASELINE_SEED`, echoed at `desk_playbook.py:250`)
  moves `compute_playbook_input_signature`'s output — proving a FUTURE rail change would re-key
  playbook records rather than silently reinterpreting them.
- [ ] Close audit gap **T1**: add TWO `compute_playbook`-LEVEL fixtures (a real walk over a
  `BarStore`-backed fixture, not a hand-built `or_result`/detector-input dict) — one for the
  5m-basis opening-range degrade, one for the `ambiguous_outside_bar` case — since the existing
  tests exercise both only at the primitive/detector piece level
  (`docs/handoffs/goal-playbook-iter-1-audit.md` §T1).
- [ ] Close audit gap **T3**: add one detector-level fixture with a REAL, non-empty SPY 5m series so
  `market.market_direction`/`market.alignment`/`relative_strength_strong: true` are exercised by at
  least one test (today only the no-SPY-bars null branch runs; audit §T3).
- [ ] `docs/playbook-detector-spec.md` — two documentation-only catch-ups (zero code/behavior
  change; see NOTES and the assumption ledger for why these are safe to resolve inside this
  iteration): (a) audit **B3** — add `PLAYBOOK_OR_MIN_1M_BARS` as a row in §1's constants table
  (value `10`, source ADAPTATION, the rationale already stated in §2 primitive 2's prose and in
  `desk_playbook.py:90-94`'s comment); (b) audit **B4** — state explicitly in §3.1/§3.2 prose that
  `principles` includes `"P4"` for an opening-range break exactly when
  `spike_into_trigger_verdict == "constructive"` (§0's already-defined discriminator), matching
  `desk_playbook_detect.py:276` verbatim.

### New user-facing capability

None visible in the UI this iteration (J-02 stays backend-only; Frontend Present: no). An operator
with direct API access can now read a `forward` measurement block (per-horizon return/exit/dual-MDD,
`to_close`, truncation flags) and an `invalidation_breached` disclosure on each already-detected
signal via the SAME `GET /research/desk/playbook` endpoint, plus trigger a measured (re-)compute via
`POST /research/desk/playbook/compute` (or its CLI) and poll its progress/ledger. The `/desk`
Playbook Signals section that surfaces any of this to the product's actual user lands at J-03.

### New information displayed

None in the UI — the new `forward`/`invalidation_breached`/`baseline_anchors`/`summary` fields exist
only on the API response body this iteration.

### New user actions

None in the UI. A new backend-only action exists: triggering
`POST /research/desk/playbook/compute` (or the CLI) to measure a session's already-detected signals
— reachable only via direct API/CLI until J-03 wires a Run Playbook button to this SAME endpoint.

### UI surface changes

None.

### Product surface delta

None visible to the product's user this iteration. Extends the existing "Playbook records" API row
with a measurement block and adds two new backend-only rows (compute progress, run ledger) beneath
the current three-page product; nav (`Cockpit /`, `Structure /structure`, `Desk /desk`) unchanged.

### Blueprint conformance

No new UI surfaces — J-02 is backend-only. All three rows this iteration touches are ALREADY
registered in `runs/goal-session-playbook/state/blueprint.md`'s Data Contract table, each marked
"Ships at: J-02": the "Playbook records" row's measurement-block extension (same owner
`app/research/desk_playbook.py`, same endpoint `GET /research/desk/playbook`), "Playbook compute
progress" (owner: new `desk_playbook_compute.py`, endpoint
`POST/GET/POST-cancel /research/desk/playbook/compute`), and "Playbook run ledger" (owner: new
`desk_playbook_log.py`, endpoint `GET /research/desk/playbook/runs`). No IA edit needed; no
`blueprint.reapproval-requested` entry (no nav-skeleton change).

### Data-contract additions

None new — all three rows below were pre-registered in `blueprint.md` at baseline (see Blueprint
conformance above); this iteration ships their first concrete shape rather than registering a new
value or a new owner/endpoint (see NOTES for why no `blueprint.md` edit is needed). Exact shapes,
for the test-first contract below:

- Each `Signal` (on the existing "Playbook records" row) gains: `forward: {entry_price: float,
  entry_kind: "level"|"gap_open", at_utc: str, horizons: {<"1m"|"5m"|"1h"|"4h">: {return_pct:
  float|null, exit_price: float|null, mdd_long_pct: float|null, mdd_short_pct: float|null,
  truncated: bool, effective_minutes: int|null, reason: str|null}}, to_close_pct: float, close_price:
  float, minutes_to_close: int, mdd_long_pct: float, mdd_short_pct: float}` (the rail's own
  `_measure_from` shape, echoed verbatim) plus `invalidation_breached: {<horizon label or
  "to_close">: bool, first_breach_minutes: int|null}`.
- The record gains: `baseline_anchors: dict[str, list[<same forward shape>]]` keyed
  `"<setup_id>:<side>"`, and `summary: dict[str, dict[str, {signals: <avg cell>, baseline: <avg
  cell>}]]` (per-(setup_id, side) × measure key, `<avg cell> = {n: int, mean_pct: float|null,
  median_pct: float|null, n_truncated: int}`).
- "Playbook compute progress" (owner `desk_playbook_compute.py`, endpoint
  `POST/GET/POST-cancel /research/desk/playbook/compute`): `{status: "idle"|"running"|"cancelling"|
  "done"|"error", session_date: str|null, signals_done: int, signals_total: int, error: str|null}`
  (mirrors `DeskForwardComputeManager`'s snapshot shape).
- "Playbook run ledger" row (owner `desk_playbook_log.py`, endpoint
  `GET /research/desk/playbook/runs`): `{run_id: str, session_date: str, outcome: "recorded"|
  "reused"|"refused_non_session"|"failed", started_at: str, finished_at: str}` — terminal-state-only
  (an interrupted/cancelled run writes no row).

## OUT OF SCOPE

- The `/desk` Playbook Signals UI section (table, Run Playbook button, provenance line) — J-03.
- Detector families beyond `open_high_break`/`open_low_break` (JBE, DBI, cup-and-handle,
  capitulation, euphoria, range trades, double top/bottom) — J-04/J-05/J-06.
- The back-scan — J-07.
- The evidence view / aggregation cache — J-08.
- MCP tools (`desk_playbook`, `desk_playbook_evidence`) — J-09; MCP stays at exactly 18 tools this
  iteration, zero diff to `app/mcp/__init__.py`.
- Any diff to `desk_forward.py` itself — imported from only, zero diff, verified by `git diff`.
- Any diff to `desk_screen*.py`, `setups.py`, `bars.py`, or `levels.py` — all read/mirrored only.
- Any new `Config` field or fingerprint-epoch change; pin stays `08e471b10130e1e2`.
- Spec §4's `halted_formation` policy — still open per the iter-1 lesson, but only binds before
  J-07's back-scan touches real recorded sessions, not this iteration.
- Audit observations **B5** (`attempt_count`'s OR-bar exclusion), **B6** (`entry_kind`'s tie-case
  divergence from the rail's own `edge` convention — worth a glance while wiring `_measure_from`
  since the code path is adjacent, but `_measure_from` only ECHOES `entry_kind` and never branches
  on it per the audit's own confirmation, so it is NOT required this iteration), **B7**
  (`or_width_mbr` division guard), and **B8** (targeted-read integrity-error swallowing) — none were
  named in the evaluator's carried-work list for this iteration; fixing them uninvited would be
  scope creep against the binding "Next target" carry list in `iteration-state.md`.
- Real (non-fixture) compute runs over the live recorded universe — fixture-scoped only this
  iteration, per J-02's own acceptance tag "(Keyless; automated.)".
- SPY freshness / top-up work (already shipped per R-2) — untouched.
- "Fixing" J-10's `partial` status — its 20-tools clause only resolves at J-09; this iteration only
  verifies J-10 does not regress AND explicitly runs its golden replay (see DEFINITION OF DONE).

## DEFINITION OF DONE

- [ ] Target journey J-02 passes its documented keyless/automated acceptance criteria (`docs/goal.md`
  tags J-02 "(Keyless; automated.)" — no browser-qa-agent requirement of J-02 itself): TC-1..TC-10,
  TC-16..TC-19.
- [ ] Required-still-passing journey J-01 remains passing, zero regression to its detection-only
  behavior, record shape, or already-recorded files: TC-11, TC-22.
- [ ] Required-still-passing journey J-10 remains at least `partial` with its golden-script replay
  EXPLICITLY EXECUTED this iteration — not deferred to "browser-qa-agent", not marked
  SKIPPED/DEFERRED/N/A, closing the exact evidence gap iter-1 left open: TC-21.
- [ ] No anti-goal violation introduced — no second implementation of the rail (TC-1), deterministic
  and seeded baselines (TC-7, TC-10), append-only / no-rewrite record discipline (TC-10, TC-11),
  signal-as-observation copy discipline (register/copy lint unmodified and green), spec-only
  thresholds with zero invented rule (TC-20), zero diff to every frozen module (TC-22).
- [ ] Unit tests pass; no regressions — full backend suite ≥ 1969 pass / 8 skip,
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-22.
- [ ] The three audit test gaps (T1 × 2, T3) are closed with `compute_playbook`/detector-LEVEL
  fixtures, not just piece-level ones: TC-16, TC-17, TC-18.
- [ ] The two spec-doc documentation catch-ups (B3, B4) are written with zero code/value/behavior
  change: TC-20.
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-2-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-02 itself needs none (`docs/goal.md` marks it "(Keyless; automated.)"). Required-
  still-passing **J-10 MUST still be replayed this iteration via its stored golden script**
  (`runs/goal-session-playbook/journey-scripts/J-10.json`) even though `Frontend Present: no` — this
  is the SAME evidence gap iter-1 left open (see BACKGROUND). Do not let the browser lane's default
  self-skip-on-backend-only-iteration behavior stand: if the automatic browser-qa step does not run
  because no frontend diff exists, the orchestrator/developer must invoke the replay as an explicit
  standalone step before this iteration is reported done. Only if the replay itself fails or drifts,
  fall back to a manual walk of the cockpit + `/structure` + every shipped `/desk` section per J-10's
  own acceptance text.
- Unit/integration:
  - `desk_playbook.py`: `compute_playbook`'s new measurement pass (forward block, invalidation
    breach, baseline anchors, per-(setup,side) summary); the convention-identity test; the
    embedded-constants counter-test; run-ledger one-row-per-terminal-run and interrupted-run-writes-
    nothing; CLI/API parity.
  - `desk_playbook_compute.py`: single-flight refusal of a concurrent trigger on the same key;
    cooperative cancel mid-walk discards the partial result; progress snapshot shape.
  - `desk_playbook_detect.py` / `desk_playbook_features.py`: the two T1 `compute_playbook`-level
    fixtures (5m-basis degrade, ambiguous-outside-bar) and the one T3 populated-SPY fixture.
  - `docs/playbook-detector-spec.md` / `desk_playbook.py` / `desk_playbook_detect.py`: the B3/B4
    documentation-only diffs leave every constant VALUE and every code line byte-unchanged (a
    source-diff assertion, not just a spec-text assertion).
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/`config.py`/
    `mcp/__init__.py`/`apps/frontend/`; full suite green at ≥ the iter-1 floor (1969 pass / 8 skip).
- Error cases:
  - A non-session `session_date` passed to the compute trigger → refused with
    `desk_sessions.non_session_refusal`'s sentence, no record written, no ledger row.
  - A second compute triggered for the same key while one is already running → refused
    (single-flight), never queued or duplicated.
  - A cancel fired mid-walk → the walk stops, nothing is written to `PlaybookStore`, and
    `GET .../runs` records no row for the cancelled attempt.
  - A duplicate `(session_date, playbook_input_signature)` measured-record write →
    `PlaybookStore.record()` raises exactly as it did at J-01, original file untouched.
  - A gapped 1m window at the exact trigger bar's own 5m span → an honest degrade/disclosure, never
    a bar borrowed from a neighboring window silently substituted (TC-19).

Test-first contract:

- TC-1: given a synthetic anchor bar index, entry, entry_kind, tf_minutes, and sign, when it is
  measured through `compute_playbook`'s own call site AND directly through
  `desk_forward._measure_from` with the identical arguments, then both calls return byte-identical
  `horizons`/`to_close_pct`/`mdd_long_pct`/`mdd_short_pct` leaves.
- TC-2: given a fixture session whose 1m bars run out before a signal's `+4h` horizon target bar,
  when the signal is measured, then the `4h` horizon leaf reports `truncated: true`,
  `effective_minutes < 240`, and `return_pct` computed against the last available bar's close.
- TC-3: given a fixture signal with `entry_kind == "gap_open"` from J-01 detection, when it is
  measured, then `forward.entry_price` and `forward.entry_kind` equal the signal's own already-
  detected `entry`/`entry_kind` fields exactly (not recomputed from the trigger price a second way).
- TC-4: given a fixture where price trades through `invalidation_price` exactly at a horizon's
  boundary bar, when `invalidation_breached` is computed, then that horizon and every later horizon
  report `breached: true` with `first_breach_minutes` equal to the boundary bar's offset, and every
  earlier horizon reports `breached: false`.
- TC-5: given a fixture where price touches `invalidation_price` on the trigger (anchor) bar itself,
  when `invalidation_breached` is computed, then every horizon reports `breached: true` and
  `first_breach_minutes == 0`.
- TC-6: given a fixture where price never trades through `invalidation_price` during the session,
  when `invalidation_breached` is computed, then every horizon reports `breached: false` and
  `first_breach_minutes` is `null`.
- TC-7: given a `(symbol, setup_id)` with N capped signals in a session of B bars, when baseline
  anchors are drawn, then exactly `k = min(N, B)` indices are drawn via `_draw_anchor_indices` seeded
  `f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"`, and re-running the
  identical compute reproduces byte-identical anchor indices and measurements.
- TC-8: given the same fixture universe plus one additional unrelated symbol carrying zero signals,
  when baseline anchors are recomputed, then the original symbol's baseline anchors are
  byte-unchanged.
- TC-9: given a fixture session with more raw opening-range-break signals for one `(setup_id, side)`
  than the per-(setup,side) cap, when `compute_playbook` runs, then the record discloses the
  beyond-cap count and the summary/baseline draw uses only the capped subset.
- TC-10: given a rail constant already embedded in `playbook_parameters()` (e.g.
  `DESK_FORWARD_BASELINE_SEED`), when it is monkeypatched and `compute_playbook_input_signature` is
  recomputed, then the signature changes, and a re-run under the new signature writes a NEW record
  file while the prior file's SHA-256 stays unchanged.
- TC-11: given a J-01-era record already on disk (no measurement block) before this iteration, when
  `GET /research/desk/playbook?id=<that id>` is read after this iteration ships, then the response
  serves the record verbatim including the honest `"measurement not recorded in this record"`
  absence marker, and the file's own SHA-256 is unchanged from its pre-iteration value.
- TC-12: given `desk_playbook_compute.py`'s manager trio, when a compute is triggered via
  `POST /research/desk/playbook/compute` for a fixture-planted session and runs to completion, then
  `GET /research/desk/playbook/runs` records exactly one terminal row for that run.
- TC-13: given an in-flight compute triggered on the manager, when cancel fires mid-walk, then the
  walk stops, `PlaybookStore` gains no new file, and `GET /research/desk/playbook/runs` records no
  row for the interrupted attempt.
- TC-14: given the CLI entry point for `run_playbook_and_record`, when invoked against a fixture
  session, then it exits 0 and the resulting stored record is byte-identical to what the
  API-triggered path produces for the same inputs.
- TC-15: given a compute already running for a session's key, when a second trigger is sent for the
  same key, then it is refused (single-flight) rather than queued or run concurrently.
- TC-16: given a fixture session with fewer than `PLAYBOOK_OR_MIN_1M_BARS` 1m bars, when a full
  `compute_playbook(session_date)` walk runs over a `BarStore`-backed fixture (not a hand-built
  `or_result` dict), then the resulting signal's `geometry.opening_range_basis == "5m"` and its
  `forward` block is present and measured (closes audit T1's first gap).
- TC-17: given a fixture bar strictly breaking both opening-range sides with neither side previously
  broken, when a full `compute_playbook(session_date)` walk runs over a `BarStore`-backed fixture
  (not a hand-built dict), then no signal is recorded for that symbol-session and the
  `ambiguous_outside_bar` diagnostic appears in that session's own `diagnostics` list (closes audit
  T1's second gap).
- TC-18: given a detector-level fixture with a real, non-empty SPY 5m series, when a signal is
  detected against it, then `market.market_direction` is non-null, `market.alignment` is one of
  `"supportive"|"against"|"neutral"`, and at least one fixture case exercises
  `relative_strength_strong: true` (closes audit T3).
- TC-19: given a fixture session with 1m bars present for most of the session but a gap spanning
  exactly the trigger signal's own 5m window, when the finest-series anchor mapping resolves, then
  it either measures from a real bar inside that window or produces an honest disclosed degrade to
  the 5m basis — never a bar from a different 5m window silently substituted as the trigger's own.
- TC-20: given `docs/playbook-detector-spec.md` after this iteration's two documentation edits, when
  §1's table and §3.1/§3.2's prose are inspected, then `PLAYBOOK_OR_MIN_1M_BARS` appears as a row and
  the P4-on-constructive rule appears in prose, while `desk_playbook.py:94`'s constant value and
  `desk_playbook_detect.py:276`'s `principles` line remain byte-unchanged from before this iteration
  (a source `git diff` on those two lines is empty).
- TC-21: given `runs/goal-session-playbook/journey-scripts/J-10.json`, when it is replayed against
  the running app THIS iteration (explicitly, not deferred), then every step's assertion matches the
  kept product's current cockpit, `/structure`, and every shipped `/desk` section, with zero new
  failures.
- TC-22: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 1969 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, `bars.py`, `levels.py`, `config.py`, `mcp/__init__.py`, and `apps/frontend/`.

## NOTES

- **Blueprint: no edit this iteration.** All three rows J-02 ships into (the "Playbook records" row's
  measurement extension, "Playbook compute progress", "Playbook run ledger") were already registered
  at baseline with the correct owner module and serving endpoint, each explicitly marked "Ships at:
  J-02" in `runs/goal-session-playbook/state/blueprint.md`'s Data Contract table — only the exact
  field shape is new this iteration, which belongs in this spec's Data-contract additions section
  (matching the precedent `docs/phases/goal-playbook-iter-1.md`'s NOTES set for J-01). No
  nav-skeleton change occurred, so no `blueprint.reapproval-requested` entry either.
- **T-8 (the rail is imported, not forked) is THE central risk this iteration.** Every horizon/MDD/
  truncation/seed computation must come from `desk_forward.py` via import; a developer tempted to
  copy `_measure_from`'s body "to add one playbook-specific tweak" recreates the exact drift the
  whole codebase is built to prevent — extend the rail's own parameters/shape instead if a genuine
  gap is found, and surface it rather than fork silently.
- **T-1 (spec is law) still applies.** If any step of J-02's measurement wiring turns out
  unimplementable as written from `docs/playbook-detector-spec.md` §0, drop it from this iteration,
  record the drop, and surface it for an owner ruling — never improvise.
- **Key anchors for the developer** (verified against the current tree at authoring; re-locate by
  symbol name, never by line arithmetic): `desk_forward.py` — `_measure_from` :451,
  `_draw_anchor_indices` :428, `_side_sign` :443, `_session_slice` :295, `forward_parameters()` :225,
  `compute_forward_input_signature` :362, `DESK_FORWARD_BASELINE_SEED = 1729` :138, the averaging
  helpers `_avg_cell`/`_collect_measures`/`_averages_block` :564-623. `desk_playbook.py` (current) —
  `compute_playbook` :301, `playbook_parameters()` :191 (already embeds rail constants at :246-251),
  `PLAYBOOK_SIGNAL_MEASURES` :137 (already `= DESK_FORWARD_MEASURE_KEYS`), `PlaybookStore.record`
  :533. `desk_playbook_detect.py` — the signal dict's already-computed `entry`/`entry_kind` :284-285;
  the B4 `principles` line :276. `desk_forward_compute.py` — `run_forward_and_record` :80,
  `DeskForwardComputeManager` :249 (the manager-trio precedent to mirror). `desk_routes.py` —
  `get_playbook_store` :956, the existing `GET /playbook` route :983 (new compute/runs routes attach
  beside it). `docs/playbook-detector-spec.md` — §0 Entry convention :44-49, §0 Measurement :55-61,
  §0 Invalidation level :77-86, §1's constants table (B3's new row), §3.1/§3.2 (B4's new prose).
- **Assumption ledger entry appended** (`runs/goal-session-playbook/state/assumptions.md`) recording
  the interpretive call on B3/B4's "owner ruling" language — scoped as developer-executed,
  documentation-only spec catch-ups rather than deferred to the human operator, since neither
  invents a threshold, changes a value, or alters already-shipped, already-tested behavior.
- **Scope-creep check:** every IN SCOPE item traces to J-02's own steps/acceptance text in
  `docs/goal.md`, the evaluator's iter-1 next-step recommendation, or the iter-1 audit's own named
  gaps (T1, T3, B3, B4) — nothing here reaches outside `docs/goal.md`'s Key Capabilities. B5-B8 are
  explicitly left untouched (see OUT OF SCOPE) since the evaluator's carried-work list did not name
  them.

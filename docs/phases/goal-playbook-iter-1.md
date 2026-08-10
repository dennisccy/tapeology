# Goal Iteration 1 — The signal contract (J-01): opening-range breaks, lookahead-clean and pre-registered

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 1
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: J-01 stands up 4 new/touched interacting modules
  (`desk_playbook_features.py`, `desk_playbook_detect.py`, `desk_playbook.py` incl. `PlaybookStore`,
  and a new route wired into the shared `desk_routes.py`) that establish the signal-contract
  architecture every remaining era journey (J-02 measurement, J-04/J-05/J-06 detector families,
  J-07 back-scan, J-08 evidence, J-09 MCP) builds on top of — a wrong record shape, signature
  recipe, or store discipline here corrupts every downstream journey silently; that risk needs the
  fuller pipeline's design/review/audit scrutiny, not a lean cycle.
- **Frontend Present:** no
- **Target journeys:** J-01
- **Required-still-passing journeys:** J-10
- **Anti-goal reminders:**
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

For any recorded trading session, the desk can now detect and permanently record pre-registered,
lookahead-clean opening-range breakout signals (`open_high_break`/`open_low_break`) as an
append-only playbook record, readable honestly — including a genuine "nothing recorded" response —
through a new `GET /research/desk/playbook` endpoint; no UI ships yet, but this is the record
shape, signature recipe, and store the rest of the Playbook era (J-02 measurement onward) is built
on top of.

## BACKGROUND

Iteration 0 (baseline, look-only) confirmed the Playbook era has not been started — the whole
`apps/` diff was empty — and left the kept product intact but J-10 `partial` pending J-09's 20-tool
clause. The evaluator recommended building J-01 alone next at full depth
(`runs/goal-session-playbook/iter-0/eval.md`), naming it the first link every remaining journey
depends on. Per the priority rubric this is the clear pick: nothing regressed, no coherence-audit
exists to consolidate against, and J-01 is the textbook unblocker (J-02 through J-09 all read its
record shape, signature recipe, and store). Depth is full per the evaluator's binding
recommendation, independently satisfying **Full trigger 1 (structural/cross-cutting)**: J-01
touches ≥3 new/shared modules that establish the era's whole signal-contract architecture (see
Goal Mode Metadata above for the full reasoning). Lesson check: the iter-0 lesson
about a raw-JSON-body screenshot proving nothing about which route was probed does not bind this
iteration — J-01's own acceptance is entirely `(Keyless; automated.)` in `docs/goal.md`, so no
browser evidence is captured here at all; that lesson starts mattering at J-03.

## IN SCOPE

### Backend

- [ ] `app/research/desk_playbook_features.py` — the spec §2 eight primitives (`rth_session_slice`,
  `opening_range`, `baselines`, `swing_pivots`, `consolidation_range`, `vertical_move`,
  `zone_touches`, `market_context`), each attributed to its existing precedent
  (`desk_forward._session_slice`, `levels._swing_pivots`, `desk_forward._touch_scan`) per
  [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) §2 — nothing else in this
  module.
- [ ] `app/research/desk_playbook_detect.py` — `open_high_break`/`open_low_break` (spec §3.1–3.2)
  emitting the spec §0 signal shape. Module docstring carries the T-2 third-vocabulary disclaimer
  and never imports `setups.py`/`backtests.py`.
- [ ] `app/research/desk_playbook.py` — spec §1 constants (verbatim values + BOOK/ADAPTATION tags),
  `PLAYBOOK_REGISTER`, `playbook_parameters()` (call-time reads, mirrors
  `desk_forward.forward_parameters` at `desk_forward.py:225`), `compute_playbook_input_signature()`
  (sorted `(symbol, timeframe, series_id, checksum)` tuples for members ∪ `{SPY}` ×
  `("1m","5m")` + `config_fingerprint` + parameters-blob `sha256[:16]`, metadata-only — mirrors
  `compute_forward_input_signature` at `desk_forward.py:362`), `PlaybookStore` (2-pin append-only
  keyed `(session_date, playbook_input_signature)`; id = pure function of the key; checksum-verified
  load; duplicate-key raises; no update/delete method; versions counted — mirrors `ForwardStore` at
  `desk_forward.py:802`), `compute_playbook(session_date)` (detection-only walk this iteration —
  measurement is J-02), `resolve_desk_playbook_dir` (env-var-or-sibling default
  `TAPEOLOGY_DESK_PLAYBOOK_DIR`, zero new `Config` field, mirrors `resolve_desk_forward_dir`).
- [ ] `desk_routes.py`: `GET /research/desk/playbook` (`?date=`, `?id=` verbatim reads; honest-empty
  payload when nothing is recorded — the `desk_forward`/`desk_screen` no-data-is-still-200
  convention, never a 404) + a `get_playbook_store` dependency mirroring `get_forward_store`
  (`desk_routes.py:412`).
- [ ] Session-honesty wiring: `compute_playbook` calls `desk_sessions.refuse_if_not_a_session`
  (`desk_sessions.py:180`) first; per-symbol absences (no 5m bars, `MBR=0` or fewer than
  `PLAYBOOK_MIN_BASELINE_SESSIONS` prior sessions, no opening range) recorded as disclosed absence
  rows, never a crash.
- [ ] Generic lookahead property test (parametrized detector × fixture × signal):
  `detect(bars[:trigger_index+1])` reproduces the identical signal; mutating any bar strictly after
  the trigger index changes nothing. Built so J-04/J-05/J-06 extend it by adding fixtures only.
- [ ] Fixtures — synthetic bars built in test code (the `test_desk_forward.py` `_bar`/`_plant`
  convention; no new fixture-file infrastructure): one canonical `open_high_break` firing session
  (hand-computed trigger/invalidation/geometry), one near-miss (OR wider than
  `PLAYBOOK_NARROW_OR_MAX_MBR·MBR` — must NOT fire), one 5m-basis opening-range degradation
  session, one ambiguous-outside-bar session (a bar strictly breaks both OR sides with neither
  side previously broken).
- [ ] Monkeypatch counter-test proving a patched spec constant moves both `playbook_parameters()`'s
  blob and `compute_playbook_input_signature`'s output (the `forward_parameters` liveness-test
  precedent).

### New user-facing capability

None visible in the UI this iteration (J-01 is backend-only). An operator with direct API access
can `GET /research/desk/playbook?date=<yyyy-MM-dd>` and receive either a recorded set of
opening-range signals or an honest "not computed for this session" response — no fabricated data,
no 404. The `/desk` Playbook Signals section that surfaces this to the product's actual user lands
at J-03.

### New information displayed

None — no UI surface renders anything from this endpoint yet.

### New user actions

None — no HTTP trigger/compute route or CLI ships this iteration (that is J-02's
`desk_playbook_compute.py`); `compute_playbook(session_date)` is a plain function this iteration,
called only by the test harness.

### UI surface changes

None.

### Product surface delta

None visible to the product's user. Adds one new backend read endpoint and one new append-only
store beneath the current three-page product; the Information Architecture and nav (`Cockpit /`,
`Structure /structure`, `Desk /desk`) are unchanged.

### Blueprint conformance

No new UI surfaces — J-01 is backend-only. Its eventual home is already registered in
`runs/goal-session-playbook/state/blueprint.md`'s "Feature / journey homes" table: J-01 → *(backend
module + store; `GET /research/desk/playbook` — no standalone UI until J-03)*, Desk nav section.
No IA edit needed.

### Data-contract additions

Extends the ALREADY-registered blueprint row "Playbook records" (owner
`app/research/desk_playbook.py`, endpoint `GET /research/desk/playbook`) — no new row, no
owner/endpoint change, so **no `blueprint.md` edit this iteration** (see NOTES). This iteration
ships that row's first concrete shape (detection-only; measurement fields land at J-02):

- Record: `{session_date: str (yyyy-MM-dd), playbook_input_signature: str, id: str,
  recorded_at: str (ISO 8601 UTC), parameters: dict (verbatim `playbook_parameters()` blob),
  signals: list[Signal], absences: list[{symbol: str, reason: str}]}`
- `Signal = {symbol: str, setup_id: "open_high_break" | "open_low_break", side: "long" | "short",
  trigger_ts: str (ISO 8601), trigger_price: float, entry: float,
  entry_kind: "level" | "gap_open", price_low: float, price_high: float,
  invalidation_price: float, geometry: dict, volume: dict, market: dict,
  principles: list[str], disclosures: dict}`
- `GET /research/desk/playbook` (no query): `{playbooks: list[<meta-only record>], latest: dict|null}`
  honest-empty when nothing is recorded (never 404); `?date=`: newest record for that date + its
  `versions` count; `?id=`: that exact record.

## OUT OF SCOPE

- Measurement (forward returns, `invalidation_breached`, seeded baseline anchors) — J-02.
- The compute manager, CLI, run ledger, and any POST trigger route — J-02.
- The `/desk` Playbook Signals UI section — J-03.
- Detector families beyond `open_high_break`/`open_low_break` (JBE, DBI, cup-and-handle,
  capitulation, euphoria, range trades, double top/bottom) — J-04/J-05/J-06.
- The back-scan — J-07.
- The evidence view / aggregation cache — J-08.
- MCP tools (`desk_playbook`, `desk_playbook_evidence`) — J-09; MCP stays at 18 tools this
  iteration.
- Any diff to `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`, or `levels.py` — all
  read/mirrored only.
- Any new `Config` field or fingerprint-epoch change.
- SPY freshness / top-up work (already shipped per R-2) — untouched.
- "Fixing" J-10's partial status — its 20-tools clause only resolves at J-09; this iteration only
  verifies J-10 does not regress (see `iteration-state.md` "Do not redo").

## DEFINITION OF DONE

- [ ] Target journey J-01 passes its documented acceptance criteria — keyless/automated per
  `docs/goal.md` ("(Keyless; automated.)"; no browser-qa-agent step applies to J-01 itself):
  TC-1..TC-12, TC-15, TC-16.
- [ ] Required-still-passing journey J-10 remains at least `partial` with zero regression, verified
  via deterministic replay of its stored golden script
  `runs/goal-session-playbook/journey-scripts/J-10.json` (do not extend or rewrite it — no UI
  changed this iteration): TC-14.
- [ ] No anti-goal violation introduced — lookahead-clean (TC-6), deterministic/seeded and
  append-only store discipline (TC-9, TC-10, TC-11), spec-only thresholds and signal-as-observation
  copy discipline (TC-15, TC-16), zero diff to the frozen modules (TC-13).
- [ ] Unit tests pass; no regressions — full backend suite ≥ 1926 pass / 8 skip,
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-13.
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-1-dev.md`.

## TESTING REQUIREMENTS

- Browser: none required for J-01 itself (`docs/goal.md` marks it `(Keyless; automated.)`).
  Required-still-passing J-10 is covered by deterministic replay of its stored golden script; only
  if that replay fails or drifts, fall back to a manual walk of the cockpit + `/structure` + every
  shipped `/desk` section per J-10's own acceptance text.
- Unit/integration:
  - `desk_playbook_features.py`: each of the 8 primitives, including `opening_range`'s 1m→5m
    degrade + null case, `baselines`' `MBR=0`/thin-baseline case, `swing_pivots`' strict-extreme +
    ties-are-not-pivots + confirmation-delay parity with `levels._swing_pivots`, and
    `market_context`'s no-SPY-bars null case.
  - `desk_playbook_detect.py`: fixture goldens for both detectors (canonical + near-miss + degraded
    basis + ambiguous outside bar).
  - `desk_playbook.py`: `playbook_parameters()` liveness/monkeypatch; `compute_playbook_input_signature`
    sorted-tuple hashing + parameters-blob inclusion; `PlaybookStore` duplicate-key raise,
    checksum-verified load, corrupt-file surfacing, no update/delete method, versions counted, id
    as a pure function of the key; `compute_playbook(session_date)` non-session refusal,
    per-symbol absence rows, byte-identical repeat computation; `GET /research/desk/playbook`
    honest-empty + `?date=`/`?id=` verbatim reads.
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`; full suite green at the era-open
    floor or above.
- Error cases:
  - A non-session date passed to `compute_playbook` → refused with
    `desk_sessions.non_session_refusal`'s sentence, no record written.
  - A duplicate `(session_date, playbook_input_signature)` write → `PlaybookStore.record()` raises,
    the original file is untouched.
  - A corrupt playbook record file → surfaced as an integrity error on read, never silently
    overwritten or skipped.
  - `GET /research/desk/playbook?id=<unknown>` → an honest absent response, never a 500 or a
    fabricated record.
  - A symbol-session with `MBR=0` or fewer than `PLAYBOOK_MIN_BASELINE_SESSIONS` prior sessions →
    a disclosed absence row, never a fabricated signal, never a crash.
  - A bar strictly breaking both opening-range sides with neither side previously broken → no
    signal, an `ambiguous_outside_bar` diagnostic recorded, never an arbitrary pick.

Test-first contract:

- TC-1: given no playbook record exists for any session, when a client calls
  `GET /research/desk/playbook`, then the response is HTTP 200 with `playbooks: []` and
  `latest: null` — never a 404.
- TC-2: given a fixture session whose first-15-minutes opening range is narrow
  (`or_width ≤ PLAYBOOK_NARROW_OR_MAX_MBR·MBR`) and a later 5m bar's high strictly exceeds
  `or_high` before any bar breaks `or_low`, when `compute_playbook(session_date)` runs, then
  exactly one `open_high_break` signal is recorded with `trigger_price == or_high`,
  `invalidation_price == or_low - 0.30*(or_high - or_low)`, and `side == "long"`, matching the
  hand-computed fixture values.
- TC-3: given a fixture session whose opening-range width exceeds `PLAYBOOK_NARROW_OR_MAX_MBR·MBR`
  (the near-miss fixture), when `compute_playbook(session_date)` runs, then zero
  `open_high_break`/`open_low_break` signals are recorded for that symbol-session.
- TC-4: given a fixture session with fewer than 10 of the first 15 one-minute bars recorded but a
  full 5m series, when `compute_playbook(session_date)` runs, then the opening range is built from
  the first three 5m bars and the resulting signal carries `opening_range_basis == "5m"`.
- TC-5: given a fixture bar that strictly breaks both `or_high` and `or_low` on the same bar with
  neither side previously broken, when `compute_playbook(session_date)` runs, then no signal is
  recorded for that symbol-session and an `ambiguous_outside_bar` diagnostic is present in that
  session's formation output.
- TC-6: given a recorded canonical-firing signal, when the lookahead property test re-runs
  `detect()` on `bars[:trigger_index+1]`, then the identical signal (same `trigger_price`,
  `invalidation_price`, `geometry`) is produced; when any bar strictly after the trigger index is
  mutated and `detect()` is re-run, then the detected signal is byte-identical to the original.
- TC-7: given a session date with no recorded daily bar for any anchor member (a known
  non-session date within the anchors' recorded span), when `compute_playbook(session_date)` runs,
  then it returns `desk_sessions.non_session_refusal`'s sentence and writes no record to
  `PlaybookStore`.
- TC-8: given a symbol-session where `MBR == 0` or fewer than `PLAYBOOK_MIN_BASELINE_SESSIONS`
  prior sessions are on file, when `compute_playbook(session_date)` runs, then that symbol appears
  in the record's `absences` list with a `reason` string and contributes zero signals.
- TC-9: given a first successful `compute_playbook(session_date)` call recorded under a fixed
  `(session_date, playbook_input_signature)` key, when the identical key is recomputed and
  `PlaybookStore.record()` is called again, then it raises, and the original file's SHA-256
  matches before and after the failed second call.
- TC-10: given a recorded playbook record's parameters blob, when a spec constant (e.g.
  `PLAYBOOK_NARROW_OR_MAX_MBR`) is monkeypatched and `compute_playbook(session_date)` is re-run
  with identical bars, then both `playbook_parameters()`'s returned dict and
  `compute_playbook_input_signature(...)`'s output string differ from the original, and the second
  call records a NEW file under a NEW id rather than raising a duplicate-key error.
- TC-11: given a `PlaybookStore` record file whose stored `file_checksum` does not match its
  `record` payload's recomputed hash, when the store loads that file, then it raises an integrity
  error naming the corrupted file, and the file on disk is unmodified.
- TC-12: given a recorded playbook record for `session_date=D`, when a client calls
  `GET /research/desk/playbook?date=D`, then the response's `signals` list matches the stored
  record's `signals` field-for-field, and `GET /research/desk/playbook?id=<that record's id>`
  returns the identical record.
- TC-13: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 1926 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, and `bars.py`.
- TC-14: given J-10's stored golden replay script `journey-scripts/J-10.json`, when it is replayed
  against the app after this iteration's changes, then every step's assertion matches (cockpit,
  `/structure`, and every shipped `/desk` section render exactly as before) with zero new failures.
- TC-15: given `desk_playbook.py` and `desk_playbook_detect.py`'s source, when a structural test
  inspects their imports, then neither module imports from `setups.py` or `backtests.py`, and no
  served signal field is named `stop_loss` anywhere in the signal shape (the field is
  `invalidation_price`).
- TC-16: given `PLAYBOOK_REGISTER`'s text, when `test_copy_discipline.find_violations` (the
  `desk_forward` precedent — see `test_desk_forward.py`'s import) is run over it, then it reports
  zero violations.

## NOTES

- **Blueprint: no edit this iteration.** The "Playbook records" row (owner
  `app/research/desk_playbook.py`, endpoint `GET /research/desk/playbook`) was already registered
  at baseline with the correct owner and endpoint; only the exact field shape is new, and that
  belongs in this spec's Data-contract additions section rather than duplicated into
  `blueprint.md` (which tracks owner/endpoint coherence, not full field schemas). No nav-skeleton
  change occurred, so no `blueprint.reapproval-requested` entry either.
- **T-1 (spec is law) applies from the first line of code.** If `open_high_break`/`open_low_break`
  turn out unimplementable as written from
  [`docs/playbook-detector-spec.md`](../playbook-detector-spec.md) §3.1–3.2, drop the detector from
  this iteration, record the drop, and surface it for an owner ruling — never improvise a
  threshold or a rule.
- **T-8 (the rail is imported, not forked) starts mattering here even though J-01 does no
  measurement**: `rth_session_slice` in `desk_playbook_features.py` must attribute to
  `desk_forward._session_slice` (`desk_forward.py:295`) semantics rather than re-deriving them, so
  J-02's `_measure_from` import lands on an already-consistent primitive.
- **Key anchors for the developer** (verified against the current tree; re-locate by symbol name,
  never by line arithmetic — see `docs/goal.md`'s own "Build anchors" section for the full list):
  `desk_forward.py` — `forward_parameters()` :225, `_session_slice` :295,
  `compute_forward_input_signature` :362, `ForwardStore` :802 (the 2-pin append-only pattern to
  mirror). `desk_sessions.py` — `recorded_session_dates` :129, `refuse_if_not_a_session` :180.
  `levels.py` — `_swing_pivots` :325. `desk_routes.py` — `get_forward_store` :412 (the dependency
  pattern to mirror for `get_playbook_store`).
- **Assumption ledger:** no entry this iteration — J-01's scope split (detection here, CLI/manager
  at J-02) is stated unambiguously in `docs/goal.md`'s own journey text, not an interpretive call.
- **Scope-creep check:** every IN SCOPE item traces to J-01's own steps/acceptance text or the
  canonical detector spec; nothing here reaches outside `docs/goal.md`'s Key Capabilities.

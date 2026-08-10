# Goal Iteration 3 — The Playbook lands on `/desk` (J-03)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** playbook
- **Iteration:** 3
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: this is the FIRST iteration where the playbook
  becomes visible to the product's actual user. It touches ≥3 interacting modules whose failure
  modes cross agent boundaries: `desk_routes.py` (unused-import cleanup), `desk_playbook.py` +
  `desk_playbook_detect.py` + a new shared helper in `desk_playbook_features.py` (consolidating
  three duplicated sign computations — see BACKGROUND for why literally reusing
  `desk_forward._side_sign` would silently corrupt every short-side signal), `apps/frontend/lib/
  types.ts` + `apps/frontend/lib/api.ts` + `apps/frontend/app/desk/page.tsx` (a brand-new UI
  section wired to compute/poll/cancel), and the protected guard suite
  (`test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS`, `test_desk_refresh_chain_guard.py`'s
  `_EXPECTED_EFFECT_COUNT`, `test_copy_discipline.py`'s frontend-literal walk). It needs real
  browser screenshots and requires the T-9 clean-rebuild discipline. This is also the evaluator's
  own stated rationale (`runs/goal-session-playbook/iter-2/eval.md`: "it needs real browser
  screenshots, and it touches the protective tests around the Desk page, so the fuller
  review-and-audit pass is worth it").
- **Frontend Present:** yes
- **Target journeys:** J-03
- **Required-still-passing journeys:** J-01, J-02, J-10
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

The project owner opens `/desk`, enters a session date (or leaves it blank for the most recent
recorded session), and sees — below every shipped section — a Playbook Signals section that
computes and renders the book's opening-range-break signals with their triggers, invalidation
levels, forward measurements, and baseline comparison, with honest empty/refusal states and a full
provenance line, all while every shipped `/desk` section keeps working exactly as before.

## BACKGROUND

Iteration 2 shipped J-02 genuinely done (measurement on the desk's own rail, evaluator-verified
live at 2025 pass / 8 skip) and its next-step recommendation
(`runs/goal-session-playbook/iter-2/eval.md`) named J-03 next at full depth — the natural
dependency-order unblocker (`docs/goal.md`: "J-01 → J-02 → J-03, then the detector families") that
J-04/J-05/J-06 all land visibly into. Per the priority rubric this is the clear pick: nothing
regressed (rule 1 n/a), no coherence-audit FAIL is on file (rule 2 n/a), J-03 is the textbook
unblocker for three subsequent journeys (rule 3), and it is the only journey in natural dependency
order so there is no tie to break (rule 4). Depth is `full` per the evaluator's binding
recommendation, independently satisfying **Full trigger 1** (see Goal Mode Metadata).

The evaluator's next-step recommendation named four small carried items to ride inside this same
cycle rather than become their own iteration. Three are carried as literally asked: the exact
`"measurement not recorded in this record"` legacy-record copy, dropping the unused
`PlaybookSessionRefused` import at `desk_routes.py:126`, and making the baseline-anchor draw safe
for multi-signal setups (`desk_playbook.py`'s baseline-draw branch) BEFORE J-04's detector families
land — this is a genuine no-op today (opening-range-break fires at most once per symbol-session, so
the collision condition the fix guards against cannot occur yet) but becomes load-bearing the
moment J-04 lands a detector that CAN fire twice for one symbol in a session (iter-2's own lesson:
"the moment a family fires twice for one (symbol, setup_id), the same seed string will draw the
SAME anchor index twice"), so it must land now, not after.

**The fourth item is investigated, not literally followed, and is logged to the assumption
ledger.** The evaluator asked to "reuse the rail's own long/short helper instead of repeating it."
Investigation of `desk_forward.py:443`'s `_side_sign` shows it is NOT a long/short helper: its body
is `return -1.0 if side == "resistance" else 1.0`, built exclusively for the rail's own
support/resistance wall vocabulary. `desk_forward._side_sign("short")` returns `+1.0` (since
`"short" != "resistance"`) — literally reusing it for the playbook's long/short signals would
silently flip every short signal's forward return and MDD sign positive, a genuine fabricated-data
bug, not a fix. `_measure_from`'s own docstring confirms `sign` is a caller-supplied float — each
caller computes its OWN sign for its OWN side vocabulary (the rail's caller at
`desk_forward.py:716` does exactly this with its own `_side_sign`); there is no contract that every
caller must invoke the rail's OWN helper. The real duplication problem the evaluator correctly
spotted is that the SAME `1.0 if side == "long" else -1.0` literal is written THREE separate times
across two playbook files (`desk_playbook.py` in `_measure_signal` and in the baseline-draw branch
of `compute_playbook`, plus `desk_playbook_detect.py`'s `_market_block`) — this iteration
consolidates all three into ONE new playbook-owned helper in `desk_playbook_features.py` (the
module both files already import primitives from), never touching or importing
`desk_forward._side_sign`. This keeps the "no second implementation of the measurement rail"
anti-goal intact (the rail's own measurement math stays imported, untouched) while genuinely fixing
the one-owner violation, and it is well-placed before J-04's detector families add more call sites
that would otherwise duplicate the same literal a fourth and fifth time.

**Two lessons apply directly:** (1) *iter-2 lesson 1* — the baseline-draw seed-collision fix must
land before J-04, exactly as scoped above. (2) *iter-2 lesson 2* — a golden-replay FAIL is not
evidence of a regression until the services are proven alive by a REQUEST (`curl /health` on
`:8301`), not a PID; check this before trusting any browser-qa failure this iteration.

## IN SCOPE

### Backend

- [ ] Add `side_sign(side: str) -> float` to `app/research/desk_playbook_features.py` (the shared
  primitives module both `desk_playbook.py` and `desk_playbook_detect.py` already import from):
  `1.0 if side == "long" else -1.0` — the playbook's OWN long/short convention, never imported
  from or aliased to `desk_forward._side_sign` (see BACKGROUND for why that would corrupt short
  signals). Zero diff to `desk_forward.py`.
- [ ] Replace all three inline `1.0 if side == "long" else -1.0` occurrences —
  `desk_playbook.py`'s `_measure_signal` and the baseline-draw branch of `compute_playbook`, and
  `desk_playbook_detect.py`'s `_market_block` — with calls to the new `side_sign`. A source-scan
  guard test asserts the literal string no longer appears duplicated anywhere in the playbook
  modules.
- [ ] Fix the baseline-anchor draw's seed collision: today's seed
  `f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{setup_id}"` collides if the SAME
  `(symbol, setup_id)` fires more than once in a session (each firing would draw the identical
  anchor index). Extend the seed recipe with a per-firing discriminator (e.g. the running
  within-session firing count for that `(symbol, setup_id)` pair, or the signal's own trigger
  timestamp) so each firing draws independently, while every currently-recordable signal
  (opening-range-break, ≤1 firing per symbol-session) draws the byte-identical index it draws
  today — proved by a test that every currently-recorded J-01/J-02-era file's SHA-256 is unchanged
  and a fresh compute over the same fixture inputs reproduces byte-identical output before vs.
  after the fix.
- [ ] `desk_routes.py`: drop the unused `PlaybookSessionRefused` import at line 126 (it is caught
  internally by `desk_playbook_compute.py`, never by the route layer — confirmed dead import).
- [ ] No other backend behavior change — `GET /research/desk/playbook`,
  `POST/GET/POST-cancel /research/desk/playbook/compute`, and `GET /research/desk/playbook/runs`
  keep serving exactly the shapes J-01/J-02 already shipped.

### Frontend

- [ ] `apps/frontend/lib/types.ts`: add TS interfaces for the already-shipped backend shapes this
  section reads — a playbook read result (mirroring `DeskForwardReadResult`), a playbook compute
  snapshot (mirroring `DeskForwardComputeSnapshot`), and a playbook runs-list result (mirroring
  `DeskForwardRunsListResult`). No new fields are invented — these mirror `desk_playbook.py`'s and
  `desk_playbook_compute.py`'s already-served shapes verbatim.
- [ ] `apps/frontend/lib/api.ts`: add `fetchDeskPlaybook(params: {date?: string; id?: string})`,
  `triggerDeskPlaybookCompute(sessionDate: string)`, `fetchDeskPlaybookCompute()`,
  `cancelDeskPlaybookCompute()`, `fetchDeskPlaybookRuns()` in the established style (mirror the
  existing `triggerDeskForwardCompute`/`fetchDeskForwardCompute`/`cancelDeskForwardCompute`
  functions at `apps/frontend/lib/api.ts:1649-1706`).
- [ ] `apps/frontend/app/desk/page.tsx`: a new **Playbook Signals** section rendered BELOW every
  shipped section (screen history, forward returns, refresh chain, briefing, skipped,
  runs/pins/compare/provenance):
  - a session-date text input following the desk's existing validated day-input convention
    (`validateScreenDayRange` at `apps/frontend/app/desk/page.tsx:3651` is the pattern to follow —
    `yyyy-MM-dd`, blank = the most recent recorded session; a single-date variant, not the
    two-bound range validator itself, since this section takes one date);
  - a Run Playbook button wired to the compute trigger/poll/cancel trio with live progress; an
    in-flight second trigger is refused (single-flight) and the refusal is surfaced, never silently
    dropped or queued;
  - the signals table: setup chip, side, trigger time (ET) / price, invalidation price, geometry +
    volume + market disclosures, per-horizon forward cells + invalidation-breached marks, baseline
    summary — rows rendered in the order served (trigger ts, symbol), never client-reordered;
  - per-symbol absence rows (e.g. "no opening range could be built");
  - the provenance line: record id, `playbook_input_signature`, parameters hash, `config_fingerprint`;
  - honest states: `"Playbook not computed for this session."` with an enabled Run Playbook button
    when nothing is recorded; the non-session refusal copy verbatim (sourced from
    `desk_sessions.refuse_if_not_a_session`'s own sentence, never a client-authored paraphrase);
    for a legacy (`payload_version` 1) record's signal, every forward/baseline cell shows the
    literal `"measurement not recorded in this record"` string instead of blank or a fabricated
    value.
  - page-load GETs trigger nothing (only the Run Playbook click starts a compute).
- [ ] Guard-test extensions (deliberate, not incidental):
  - `apps/backend/tests/test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` (:152) gains every new
    served numeric the Playbook Signals section renders (trigger price, invalidation price,
    per-horizon forward return/exit/MDD leaves, baseline summary cells), using named client-side
    bindings consistent with the existing `touchRow.*`/`touchValue.*`/`avgCell.*` scheme, plus
    seeded counter-tests proving the pattern actually catches an injected violation.
  - `apps/backend/tests/test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` (:104,
    currently `15`) is re-derived once with the mandatory rationale paragraph documenting exactly
    what changed, and `_TRIGGER_CALLS` (:110) gains the new Playbook Signals handler names
    (mirroring the existing `handleTriggerForward(`/`triggerDeskForwardCompute(` pair).
  - `apps/backend/tests/test_copy_discipline.py`'s frontend-literal walk automatically covers the
    new section's source strings (no test-file edit needed — verify it stays green, unmodified).
- [ ] T-9 discipline: `rm -rf apps/frontend/.next`, rebuild, and restart the frontend before any
  browser evidence capture this iteration.
- [ ] T-11 discipline: the new section's headings/`data-testid`s reuse none of the 20 stored
  `goal-session-desk` golden replay scripts' strings, nor `goal-session-playbook`'s `J-10.json` —
  statically swept before capture.

### New user-facing capability

The operator can enter a session date (or leave it blank for the most recent recorded session),
trigger a playbook compute for that session with live progress and cancel, and read the resulting
signals table with forward measurements, invalidation disclosures, and a baseline comparison,
directly on `/desk` below the shipped sections.

### New information displayed

Per-signal: setup chip, side, trigger time/price, invalidation price, geometry/volume/market
disclosures, per-horizon forward return/exit/MDD cells, invalidation-breached marks, and a
per-(setup, side) baseline summary — all already-served by `GET /research/desk/playbook` since
J-01/J-02, now rendered for the first time. Provenance (record id, signature, parameters hash,
fingerprint) and playbook compute/run-ledger state are also newly visible.

### New user actions

A session-date input, a Run Playbook button (trigger/poll/cancel), and reading absence/refusal
states for a non-computed or non-session date.

### UI surface changes

`/desk` gains one new section (Playbook Signals), rendered below every shipped section. No new
route; nav stays `Cockpit /`, `Structure /structure`, `Desk /desk`.

### Product surface delta

The product's user can, for the first time, see the playbook's own output rather than only reach
it via direct API access. Every shipped `/desk` section, `/`, and `/structure` behave exactly as
before.

### Blueprint conformance

The Playbook Signals section lands under the existing **Desk** home in
`runs/goal-session-playbook/state/blueprint.md`'s Information Architecture — that table already
names this exact section ("Playbook Signals — per-session signal table + Run Playbook button ...
(J-03, extended visibly by the detector families J-04/J-05/J-06)") as a pre-planned addition below
the shipped `/desk` sections. No nav-skeleton edit; no `blueprint.reapproval-requested` entry.

### Data-contract additions

None. The "Playbook records" row (owner `app/research/desk_playbook.py`, endpoint
`GET /research/desk/playbook`), "Playbook compute progress" row (owner `desk_playbook_compute.py`,
endpoint `POST/GET/POST-cancel /research/desk/playbook/compute`), and "Playbook run ledger" row
(owner `desk_playbook_log.py`, endpoint `GET /research/desk/playbook/runs`) were all already
registered in `blueprint.md` at baseline and already shipped their exact field shapes at J-01/J-02
(`docs/phases/goal-playbook-iter-2.md`'s Data-contract additions section is the shape-of-record).
This iteration is a pure UI consumer of those three already-registered, already-shipped rows — it
introduces no new value, no new owner, and no new endpoint, so `blueprint.md` needs no edit (same
precedent iter-1/iter-2 followed for their own pre-registered rows).

## OUT OF SCOPE

- Detector families beyond opening-range-break (JBE/DBI/cup-and-handle J-04, capitulation/
  euphoria J-05, range trades/double top-bottom J-06) — the Playbook Signals section this iteration
  ships renders whatever `GET /research/desk/playbook` serves, so future families land into this
  SAME section with zero UI rework, per `docs/goal.md`.
- The Backscan panel (J-07) and Playbook Evidence section (J-08) — not built this iteration.
- MCP tools (`desk_playbook`, `desk_playbook_evidence`) — J-09; MCP stays at exactly 18 tools this
  iteration, zero diff to `app/mcp/__init__.py`.
- Any diff to `desk_forward.py` itself — imported from only, zero diff, verified by `git diff`;
  `_side_sign` stays exactly as shipped and is never imported by any playbook module.
- Any diff to `desk_screen*.py`, `setups.py`, `bars.py`, or `levels.py` — read/mirrored only.
- Any change to any shipped `/desk` section's own behavior, columns, or copy — render-only
  verification this iteration (Required-still-passing J-10), zero diff to those code paths.
- Any new `Config` field or fingerprint-epoch change; pin stays `08e471b10130e1e2`.
- Spec §4's `halted_formation` policy — still open per the iter-1 lesson, binds before J-07's
  back-scan touches real recorded sessions, not this iteration.
- Real (non-fixture) compute runs over the live recorded universe — fixture-scoped only, per J-03's
  own acceptance tag "(keyless via the fixture-scoped backend)".
- Extending `_side_sign` itself in `desk_forward.py` to understand "long"/"short" — that file stays
  byte-unmodified; the new `side_sign` helper is playbook-owned instead (see BACKGROUND).

## DEFINITION OF DONE

- [ ] Target journey J-03 passes via browser-qa-agent — empty state, populated signals table,
  single-flight refusal, non-session refusal, and every shipped `/desk` section rendering
  unchanged, all in the same browser pass: TC-1..TC-6.
- [ ] Required-still-passing journeys J-01, J-02 remain passing with zero regression to their
  detection/measurement behavior or already-recorded files: TC-10, TC-11, TC-12, TC-17.
- [ ] Required-still-passing journey J-10 remains at least `partial`, browser-verified this
  iteration in the SAME clean-rebuilt pass as J-03: TC-6, TC-15, TC-16.
- [ ] No anti-goal violation introduced — no second implementation of the measurement rail (TC-10:
  `_side_sign` never imported by any playbook module), copy discipline (TC-9), single source of
  truth (one playbook-owned sign helper, not three duplicates — TC-10), append-only / no-rewrite
  record discipline unchanged (TC-12), deterministic seeded baselines (TC-11).
- [ ] Unit tests pass; no regressions — full backend suite ≥ 2025 pass / 8 skip,
  `Config().config_fingerprint()` prints `08e471b10130e1e2`, zero new `Config` fields: TC-14.
- [ ] All four carried items from `iteration-state.md`'s "Do not redo" closed: the literal legacy
  copy (TC-5), the unused import (TC-13), the sign-duplication consolidation (TC-10), and the
  baseline-draw safety fix (TC-11, TC-12).
- [ ] Dev handoff written at `docs/handoffs/goal-playbook-iter-3-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-03 itself needs a real browser pass with screenshots (empty state, populated table,
  single-flight refusal, non-session refusal). Required-still-passing **J-10 MUST be replayed via
  its stored golden script** (`runs/goal-session-playbook/journey-scripts/J-10.json`) in the SAME
  clean-rebuilt pass, walking every shipped `/desk` section alongside the new Playbook Signals
  section. Before trusting any browser-qa FAIL, verify the backend is alive by REQUEST
  (`curl :8301/health`), not by PID (iter-2 lesson 2) — a listening-socket check, not a process
  check.
- Unit/integration:
  - `desk_playbook_features.py`: the new `side_sign` helper, unit-tested for both `"long"` and
    `"short"`.
  - `desk_playbook.py` / `desk_playbook_detect.py`: source-scan assertion that the literal
    `1.0 if side == "long" else -1.0` no longer appears (all three call sites now call
    `side_sign`), and that no playbook module imports `desk_forward._side_sign`.
  - `desk_playbook.py`: the baseline-draw seed-collision fix — a synthetic multi-fire fixture
    (two firings of the SAME `(symbol, setup_id)` in one session) draws independent, non-colliding
    anchor indices; every currently-recordable (single-fire) fixture reproduces byte-identical
    output before vs. after the fix.
  - `desk_routes.py`: import of `PlaybookSessionRefused` removed; module still imports/starts
    cleanly.
  - `test_desk_ui_guards.py`: `_PRICE_ARITHMETIC_FIELDS` extended + seeded counter-test(s) for the
    new playbook numeric bindings.
  - `test_desk_refresh_chain_guard.py`: `_EXPECTED_EFFECT_COUNT` re-derived with rationale;
    `_TRIGGER_CALLS` extended.
  - `test_copy_discipline.py`: green, unmodified, covering the new section's source strings.
  - Suite-wide: `Config().config_fingerprint()` unchanged; `git diff` empty against
    `desk_forward.py`/`desk_screen*.py`/`setups.py`/`bars.py`/`levels.py`/`config.py`/
    `mcp/__init__.py`; full suite green at ≥ the iter-2 floor (2025 pass / 8 skip).
- Error cases:
  - A non-session `session_date` entered → the refusal copy renders verbatim, no compute starts.
  - A second Run Playbook click while one is in flight → refused (single-flight), surfaced, never
    queued or duplicated.
  - A legacy (`payload_version` 1) record's signal → every forward/baseline cell shows the literal
    absence string, never blank or a fabricated number.
  - A session with no computed playbook yet → `"Playbook not computed for this session."` with an
    enabled Run Playbook button, never a broken/empty table.

Test-first contract:

- TC-1: given a fixture session with no playbook ever computed, when the operator opens the
  Playbook Signals section for that date, then it shows `"Playbook not computed for this
  session."` with an enabled Run Playbook button (screenshot).
- TC-2: given the same fixture session, when Run Playbook is clicked and the compute completes,
  then the signals table renders rows with setup chip, side, trigger time (ET)/price, invalidation
  price, geometry/volume/market disclosures, per-horizon forward cells, invalidation-breached
  marks, and baseline summary, sorted exactly as served (trigger ts, symbol) — never
  client-reordered (screenshot).
- TC-3: given a playbook compute already running for a session, when a second Run Playbook click
  fires, then it is refused (single-flight) and the refusal is visibly surfaced, not silently
  dropped (screenshot).
- TC-4: given a non-session date entered in the date input, when the section reads/attempts a
  compute for it, then it shows the non-session refusal copy verbatim, sourced from
  `desk_sessions.refuse_if_not_a_session`'s own sentence (screenshot).
- TC-5: given a J-01/J-02-era record with `payload_version` 1 (no forward block) served at
  `GET /research/desk/playbook`, when its signal renders in the table, then every forward/baseline
  cell for that signal shows the literal string `"measurement not recorded in this record"`
  instead of blank or a fabricated value (screenshot).
- TC-6: given the same clean-rebuilt browser pass, when every shipped `/desk` section (screen
  history, forward returns, refresh chain, briefing, skipped, runs/pins/compare/provenance) is
  inspected alongside the new Playbook Signals section, then each renders exactly as shipped with
  zero visual/behavioral change (one screenshot per shipped section).
- TC-7: given `apps/frontend/app/desk/page.tsx`'s source after this iteration, when
  `_PRICE_ARITHMETIC_FIELDS`'s regex runs against it, then no arithmetic expression combines any
  newly-rendered playbook numeric binding with `+ - * /`.
- TC-8: given `test_desk_refresh_chain_guard.py` after `_EXPECTED_EFFECT_COUNT` is re-derived,
  when the effect-count guard runs, then the count matches the new value exactly and the source
  carries the mandatory rationale paragraph for the change.
- TC-9: given `test_copy_discipline.py`'s frontend-literal walk, when it scans the new Playbook
  Signals section's source strings, then zero imperative/predictive/edge-claim language is found
  and the test passes unmodified.
- TC-10: given the three former inline `1.0 if side == "long" else -1.0` computations
  (`desk_playbook.py`'s `_measure_signal` and `compute_playbook`'s baseline-draw branch,
  `desk_playbook_detect.py`'s `_market_block`), when this iteration ships, then all three call the
  new `desk_playbook_features.side_sign` helper, that literal string appears nowhere else in the
  playbook modules (source-scan assertion), no playbook module imports
  `desk_forward._side_sign`, and `git diff` against `desk_forward.py` is empty.
- TC-11: given a synthetic fixture where the SAME `(symbol, setup_id)` pair fires twice within one
  session, when baseline anchors are drawn for both firings, then each firing's anchor-index draw
  is independent (no seed collision) and the baseline pool grows to reflect both draws.
- TC-12: given every currently-recorded J-01/J-02-era playbook file (opening-range-break,
  ≤1 firing per symbol-session), when a fresh compute runs over the same fixture inputs before vs.
  after the baseline-draw fix, then the output is byte-identical and every existing file's SHA-256
  is unchanged (proves the fix is a no-op for all currently-recordable data).
- TC-13: given `desk_routes.py` after this iteration, when its imports are inspected, then
  `PlaybookSessionRefused` is no longer imported and the FastAPI app still starts cleanly.
- TC-14: given the full backend test suite, when it is run after this iteration's changes, then it
  reports a pass count ≥ 2025 and skip count == 8, `Config().config_fingerprint()` prints
  `08e471b10130e1e2`, and `git diff` shows zero changes to `desk_forward.py`, `desk_screen*.py`,
  `setups.py`, `bars.py`, `levels.py`, `config.py`, and `mcp/__init__.py`.
- TC-15: given the T-9 clean-rebuild discipline, when `apps/frontend/.next` is removed and the
  frontend is rebuilt/restarted before any browser evidence capture, then every screenshot
  captured this iteration post-dates that rebuild.
- TC-16: given the 20 stored `goal-session-desk` golden replay scripts plus
  `goal-session-playbook/journey-scripts/J-10.json`, when the new Playbook Signals section's
  headings and `data-testid`s are checked against every string those scripts match on, then zero
  collisions are found.
- TC-17: given J-01's and J-02's own test suites (99+ playbook tests), when this iteration's
  changes ship, then they still pass with zero change to J-01/J-02's already-recorded record
  shapes or content.

## NOTES

- **Assumption ledger entry appended** (`runs/goal-session-playbook/state/assumptions.md`)
  recording the interpretive call NOT to literally reuse `desk_forward._side_sign` (it would
  corrupt short-side signals — see BACKGROUND) and instead consolidate the three duplicated inline
  sign computations into one new playbook-owned `side_sign` helper in
  `desk_playbook_features.py`, satisfying the evaluator's actual concern (one owner, not three
  copies) without importing a semantically incompatible helper.
- **Blueprint: no edit this iteration.** The Playbook Signals section and all three rows it reads
  were already registered at baseline (Information Architecture + Data Contract), matching the
  precedent iter-1/iter-2 set of not editing `blueprint.md` when nothing new is introduced.
- **T-9/T-11 are the central execution risks this iteration**, not detection logic — get the clean
  rebuild and the replay-script string sweep right before capturing any screenshot; a stale
  `.next` build or a reused heading string invalidates the evidence even if the feature itself
  works.
- **iter-2 lesson 2 applies directly**: if the browser-qa lane reports a FAIL, check
  `curl :8301/health` before believing it — a backend can be alive-but-not-listening after a prior
  process's SIGTERM.
- **Key anchors for the developer** (verified against the current tree at authoring; re-locate by
  symbol name, never by line arithmetic): `desk_forward.py` — `_side_sign` :443 (support/resistance
  ONLY — do not import), `_measure_from` :451 (`sign` is caller-supplied, not a required
  `_side_sign` call). `desk_playbook_features.py` — existing primitives `opening_range` :90,
  `market_context` :276 (new `side_sign` helper joins this module). `desk_playbook.py` —
  `_measure_signal`'s sign line, `compute_playbook`'s baseline-draw branch's sign line and the
  `random.Random(f"{PLAYBOOK_BASELINE_SEED}:playbook-{session_date}:{symbol}:{signal['setup_id']}")`
  seed recipe. `desk_playbook_detect.py` — `_market_block`'s sign line. `desk_routes.py` — the
  import line ~126, `get_playbook_store` and the existing `GET /playbook`/compute/runs routes ~956-
  1130 (no route change needed, only the frontend calling them). `apps/frontend/lib/api.ts` —
  `triggerDeskForwardCompute`/`fetchDeskForwardCompute`/`cancelDeskForwardCompute` :1649-1706 (the
  precedent to mirror). `apps/frontend/app/desk/page.tsx` — `validateScreenDayRange` :3651 (the
  day-input pattern to follow, single-date variant). `test_desk_ui_guards.py` —
  `_PRICE_ARITHMETIC_FIELDS` :152. `test_desk_refresh_chain_guard.py` — `_EXPECTED_EFFECT_COUNT`
  :104 (currently `15`), `_TRIGGER_CALLS` :110.
- **Scope-creep check:** every IN SCOPE item traces to J-03's own steps/acceptance text in
  `docs/goal.md`, the evaluator's iter-2 next-step recommendation, or the iter-2
  `iteration-state.md` "Do not redo" carry list — nothing here reaches outside `docs/goal.md`'s
  Key Capabilities.

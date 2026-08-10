# goal-playbook-iter-3 Dev Handoff

**Phase:** goal-playbook-iter-3
**Date:** 2026-08-10
**Agent:** developer
**Status:** complete

## What Was Built

### Backend (the four carried "Do not redo" items)

- `app/research/desk_playbook_features.py`: new `side_sign(side: str) -> float` — the playbook's
  OWN long/short sign convention (`1.0 if side == "long" else -1.0`), the single owner of a literal
  that used to be written three separate times. Deliberately NOT `desk_forward._side_sign` (that
  helper answers `+1.0` for `"short"`, since its own rule is `-1.0 if side == "resistance" else
  1.0` — importing it would silently flip every short signal's forward return/MDD sign positive).
- `desk_playbook.py`: `_measure_signal`'s sign line and `compute_playbook`'s baseline-draw branch's
  sign line now both call `side_sign(signal["side"])`. `desk_playbook_detect.py`'s `_market_block`
  now calls `side_sign(side)`. Zero diff to `desk_forward.py`.
- `desk_playbook.py`: new `_baseline_seed(session_date, symbol, setup_id, firing_index)` fixes the
  baseline-anchor draw's seed-collision risk. `firing_index=0` (the running within-session firing
  count for a `(symbol, setup_id)` pair, tracked in a new `firing_counts` dict) produces the
  UNCHANGED literal seed string (no discriminator suffix) — every currently-recordable signal
  (opening-range-break fires at most once per symbol-session) draws the byte-identical anchor index
  it always has. `firing_index >= 1` appends a `:<firing_index>` suffix, so a future detector that
  CAN fire twice for the same `(symbol, setup_id)` in a session (J-04's JBE ladder) draws
  independent, non-colliding anchors instead of the identical index twice.
- `desk_routes.py`: dropped the dead `PlaybookSessionRefused` import (line 126) — it is caught
  internally by `desk_playbook_compute.py`, never by the route layer. Zero other route change.

### Frontend (J-03: the Playbook lands on `/desk`)

- `apps/frontend/lib/types.ts`: `DeskPlaybookRecord`/`DeskPlaybookSignal`/`DeskPlaybookGeometry`/
  `DeskPlaybookVolume`/`DeskPlaybookMarket`/`DeskPlaybookDisclosures`/
  `DeskPlaybookInvalidationBreached`/`DeskPlaybookAbsence`/`DeskPlaybookDiagnostic`/
  `DeskPlaybookSummaryCell`/`DeskPlaybookParameters`/`DeskPlaybookReadResult`/
  `DeskPlaybookComputeSnapshot`/`DeskPlaybookRun`/`DeskPlaybookRunsListResult` — mirror
  `desk_playbook.py`'s/`desk_playbook_compute.py`'s/`desk_playbook_log.py`'s already-served shapes
  verbatim. A signal's `forward` field reuses `DeskForwardTouch` directly (not a re-declared
  lookalike) since `_measure_signal` measures every playbook signal through the identical
  `desk_forward._measure_from` call the rail's own touches/anchors are measured through.
- `apps/frontend/lib/api.ts`: `fetchDeskPlaybook({date?, id?})`, `triggerDeskPlaybookCompute
  (sessionDate)`, `fetchDeskPlaybookCompute()`, `cancelDeskPlaybookCompute()`,
  `fetchDeskPlaybookRuns(sessionDate?)` — mirror `fetchDeskForward`/`triggerDeskForwardCompute`/
  `fetchDeskForwardCompute`/`cancelDeskForwardCompute`/`fetchDeskForwardRuns` byte-for-byte in
  shape.
- `apps/frontend/app/desk/page.tsx`: a new, self-contained **Playbook Signals** section rendered
  BELOW every shipped section (after Provenance, before `</main>`) — NOT wired into the refresh
  chain:
  - a session-date text input (`validatePlaybookSessionDay`, the `validateScreenDayRange`
    single-date variant — blank resolves to the newest date in `sessionsResult`'s own recorded-
    session set, never `nextTradingStamp()`'s "upcoming session" default);
  - a Run Playbook button wired to the trigger/poll(700ms)/cancel trio
    (`DeskPlaybookComputeControl`), with live progress and single-flight refusal surfaced via
    `triggerError` (process-wide, per `desk_playbook_compute.py`'s own manager — a second click
    while a DIFFERENT date's compute is running is refused with an explicit message, never
    silently adopted or queued);
  - the signals table (`PlaybookSignalsTable`/`PlaybookSignalRow`): symbol, setup chip, side chip,
    trigger time (ET)/price, invalidation price, entry kind — rows render in SERVED order only (no
    `.sort`/`.reverse`), click a row to expand `PlaybookSignalDetail` (full geometry/volume/market
    disclosures, principles, the forward measurement via `ForwardTouchTable` reused verbatim, the
    invalidation-breached marks, and a per-pool baseline-anchor-count note);
  - absence rows (`PlaybookAbsencesTable`) and a baseline summary (`PlaybookSummaryView`, reusing
    `ForwardAvgCellView` verbatim for its signals-vs-baseline cells);
  - the provenance line: record id, recorded-at, session date, `playbook_input_signature`, config
    fingerprint (plus a disclosure sentence describing what the signature hashes — no separate
    "parameters hash" field exists on the backend to render, see Known Issues);
  - honest states: `"Playbook not computed for this session."` with an ENABLED Run Playbook button
    when nothing is recorded; the non-session refusal copy is surfaced verbatim from the backend's
    422 `detail` (never a client-authored paraphrase — the client performs no non-session check of
    its own); a legacy (`payload_version` 1) signal's forward/invalidation/baseline cells all show
    the literal `"measurement not recorded in this record"` string.
  - page-load GETs trigger nothing (the resolved-date-keyed read effect and the compute-poll effect
    are both plain reads; the mount effect only SEEDS the compute snapshot, mirroring every other
    compute manager's own mount-seed precedent).
- Guard-test extensions:
  - `test_desk_ui_guards.py`'s `_PRICE_ARITHMETIC_FIELDS` gained `signal\.(?:trigger_price
    |invalidation_price)` (the section's only genuinely NEW numeric bindings — the forward-cell and
    baseline-summary numbers are already covered by the pre-existing `touchRow.*`/`touchValue.*`/
    `avgCell.*` entries, since those renderers are reused verbatim) plus a seeded counter-test.
  - `test_desk_refresh_chain_guard.py`'s `_EXPECTED_EFFECT_COUNT` re-derived 15 → 17 (the resolved-
    date-keyed read effect + the compute-poll effect) and `_EXPECTED_INTERVAL_COUNT` re-derived
    5 → 6 (the SIXTH compute manager's own poll), both with the mandatory rationale paragraph;
    `_TRIGGER_CALLS` gained `handleTriggerPlaybook(`/`triggerDeskPlaybookCompute(`.
  - `test_copy_discipline.py`: unmodified, verified green over the new section's source strings.

## Files Changed

- `apps/backend/app/research/desk_playbook_features.py` -- new `side_sign` helper
- `apps/backend/app/research/desk_playbook.py` -- `side_sign` call sites + `_baseline_seed` fix
- `apps/backend/app/research/desk_playbook_detect.py` -- `side_sign` call site
- `apps/backend/app/research/desk_routes.py` -- dropped the unused `PlaybookSessionRefused` import
- `apps/backend/tests/test_desk_playbook_features.py` -- `side_sign` unit tests
- `apps/backend/tests/test_desk_playbook.py` -- TC-10/TC-11/TC-12/TC-13 tests
- `apps/backend/tests/test_desk_ui_guards.py` -- `_PRICE_ARITHMETIC_FIELDS` extension + counter-test
- `apps/backend/tests/test_desk_refresh_chain_guard.py` -- effect/interval counts + `_TRIGGER_CALLS`
- `apps/frontend/lib/types.ts` -- new `DeskPlaybook*` interfaces
- `apps/frontend/lib/api.ts` -- new playbook fetch/trigger/poll/cancel functions
- `apps/frontend/app/desk/page.tsx` -- the Playbook Signals section (state, effects, handlers, JSX)

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q`
Result: 2036 passed, 8 skipped, 0 failed (exit code 0; this project's pytest configuration prints
no final summary line — counts derived from the progress-dot lines, the same method the iter-2
handoff used). Floor required was ≥2025 pass / ==8 skip.

Also run:
- `cd apps/backend && .venv/bin/python -m pytest tests/test_desk_playbook.py
  tests/test_desk_playbook_detect.py tests/test_desk_playbook_features.py
  tests/test_desk_playbook_compute.py tests/test_desk_playbook_log.py tests/test_desk_ui_guards.py
  tests/test_desk_refresh_chain_guard.py tests/test_copy_discipline.py -q` — all green, scoped
  confirmation before the full run.
- `cd apps/frontend && npx tsc --noEmit -p .` — zero errors.
- `cd apps/frontend && rm -rf .next && npm run build` — compiled, linted, and type-checked
  successfully; all 3 routes (`/`, `/desk`, `/structure`) statically generated with no errors.
- `python -c "from app.config import CONFIG; print(CONFIG.config_fingerprint())"` — prints
  `08e471b10130e1e2` (unchanged).
- `git diff --stat` against `desk_forward.py`, `desk_screen*.py`, `setups.py`, `bars.py`,
  `levels.py`, `config.py`, `mcp/__init__.py` — empty (verified directly, not merely by suite pass).
- Golden-replay-script string sweep (T-11): every `data-testid` this iteration adds (42 new
  `desk-playbook-*` ids) plus the heading `"Playbook Signals"` cross-checked against every `text`/
  `testid`/`label`/`role`/`name` string in all 20 `goal-session-desk` journey scripts and
  `goal-session-playbook/journey-scripts/J-10.json` — zero collisions.
- Live service smoke test (T-9 discipline, pre-handoff verification): `rm -rf apps/frontend/.next`,
  ran `scripts/dev.sh` (ports 8301/3301, this project's deterministic offset), confirmed
  `GET /health` → `{"status":"ok"}`, `GET /research/desk/playbook` → the honest empty payload,
  `GET /research/desk/playbook?date=<a real recorded session>` → `{"playbook": null, "versions":
  0}`, and `GET /desk`'s served HTML contains the `"Playbook Signals"` heading and the
  `desk-playbook-date-input` testid alongside the still-present unconditional shipped sections
  (Top-up Runs / Index Reconciliation / Screen Runs). Stopped both services, restarted cleanly
  (verified no port conflict), then stopped both again before finishing (no server left running).
  No real (non-fixture) playbook compute was triggered against the live recorded universe — that is
  explicitly OUT OF SCOPE this iteration; only reads were exercised against real data.

## Known Issues

- **"Parameters hash" interpreted, not invented.** The goal doc's J-03 acceptance text lists
  "record id, `playbook_input_signature`, parameters hash, `config_fingerprint`" for the provenance
  line. No `parameters_hash` field is served anywhere by `desk_playbook.py`/
  `desk_playbook_compute.py` — the IN SCOPE section is explicit that "no new fields are invented".
  `playbook_input_signature` already functionally IS the hash that folds in the parameters blob
  (per `compute_playbook_input_signature`'s own recipe: bar checksums + config fingerprint + the
  canonical parameters blob). The provenance line renders `playbook_input_signature` plus a one-
  line disclosure sentence explaining that composition, rather than fabricating a second, separate
  "parameters hash" value client-side. Flagging for an owner ruling on whether a literal
  `parameters_hash` field should be added to the backend record in a future iteration, or whether
  this reading (the signature already covers it) is the intended one.
- **Per-signal baseline is pool-scoped, not literally per-signal.** `baseline_anchors`/`summary` are
  keyed by `(setup_id, side)` pool, not by individual signal — a pool can (in a future multi-firing
  detector) hold anchors from several signals with no back-reference to which anchor belongs to
  which firing. The signal detail panel therefore shows a COUNT of anchors recorded for the
  signal's own pool ("baseline: N anchor(s) recorded for the `<setup>:<side>` pool — see the
  summary below") rather than a raw per-signal anchor table, since the data model does not support
  a stronger per-signal claim. This is a genuinely correct, honest read of the shape and not a gap
  — noted here only so a reviewer does not mistake the absence of a raw per-signal anchor table for
  an oversight.
- **No real (non-fixture) browser evidence captured by the developer.** Per the phase's own
  TESTING REQUIREMENTS, the actual TC-1..TC-6/TC-15/TC-16 browser screenshots (empty state,
  populated table, single-flight refusal, non-session refusal, and the full-page regression sweep
  alongside J-10's stored golden script) are the browser-qa-agent's job, run against a fixture-
  scoped backend. The developer's own live-service smoke test above confirms the section renders
  and the endpoints answer correctly against the REAL recorded universe (which currently has 5m/1m
  coverage but no playbook ever computed) — it does not substitute for the fixture-scoped browser
  pass this iteration's Definition of Done requires.
- The opening-range-break detector itself is unchanged this iteration (J-01/J-02 territory) — this
  iteration touches only the sign-consolidation, the seed-collision fix, the dead import, and the
  new UI section, exactly as scoped.

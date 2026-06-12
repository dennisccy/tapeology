# goal-i_will_be_super_rich_with_my_loved_ones-iter-21 Dev Handoff

**Phase:** goal-i_will_be_super_rich_with_my_loved_ones-iter-21 (J-63 — entry checklist with live margins)
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built

The cue layer's second surface: the `/` thesis strip now shows the **entry checklist** at the
moment of decision (an active, evaluated, NOT-yet-entry-marked thesis), with eight named checks each
rendering its **live measured margin in its own units**, an aggregate **stance** publishing through
its own dwell, and a **nearest-counterevidence** line — all computed once server-side. Its row-14
prerequisite (`delivery_lag_seconds`) shipped with it.

### Backend
- **Row 14 — `delivery_lag_seconds`** (data-contract row 14): feeder-owned, additive
  snapshot/projection metadata (the iter-9 `end_reason` precedent — an engine file may carry
  feeder-owned lifecycle/display data that NEVER enters classification). New field on
  `EngineSnapshot` (defaulted `None`), a `TapeEngine.set_delivery_lag()` stamper, served VERBATIM on
  `GET /tape/{ticker}/summary` and the WS frame. Stamped per-mode by the feeders in
  `watch_manager.py` (see semantics below). New config key `delivery_lag_ok_bound_seconds` (the
  freshness bound the `tape_lag_ok` check reads). Determinism + the observer-equivalence suite stay
  green with **zero re-pins** (the lag is never read by features/state/confidence).
- **Entry-checklist evaluator** (row 25 checklist half) in `app/research/stance.py` — the single
  row-25 owner module, observer-driven via the monitor (engine untouched). `evaluate_entry_checks`
  computes the eight checks + margins from canonical values ONLY; `EntryChecklistEvaluator` holds the
  dwell-published aggregate stance; `nearest_counterevidence` + `build_checklist` assemble the
  projection. The eight checks:
  1. **verdict_confirming** — the published row-16 verdict (margin = the verdict);
  2. **warm** — `event_count` vs `warmup_min_events` (reused floor);
  3. **feed_live** — `stream_status == "live"` (margin = the status);
  4. **tape_lag_ok** — row-14 `delivery_lag_seconds` vs `delivery_lag_ok_bound_seconds` (reads the
     SAME value the future UI lag readout reads);
  5. **spread_stable** — `average_spread` in bps vs `max_stable_spread_bps` (the classifier's own
     stability gate; no new threshold);
  6. **trade_speed_ok** — `trade_speed` vs `min_trade_speed` (reused floor);
  7. **invalidation_distance_ok** — `|last − invalidation| / spread` vs
     `invalidation_too_tight_spread_multiple` (the reused too-tight gate);
  8. **not_chasing** — directional return from the recorded **`rule_first_true` price** to the
     current last vs `chase_return_threshold` (anchored at `rule_first_true`, NEVER the post-dwell
     publish).
- **Aggregate stance** `conditions_met | conditions_not_met | tape_against | no_fresh_tape`:
  `no_fresh_tape` whenever `feed_live`/`tape_lag_ok` fail (paused/closed/stale/failed/lagging — a
  previous green NEVER persists, published IMMEDIATELY/dwell-exempt); `tape_against` on a
  rejecting/invalidated verdict (immediate); `conditions_met` only when every check passes;
  `conditions_not_met` otherwise. The two `conditions_*` transitions publish through the new
  `checklist_stance_dwell_seconds` logical-time dwell (no per-tick flapping).
- **Nearest-counterevidence** — the closest condition that would flip the read (the passing check
  nearest its boundary when met; the nearest-to-passing blocker when not), with its margin.
- **Presence rules** (mutually exclusive with the J-53 management stance): served in
  `build_projection` ONLY on the pre-entry-mark path (`status == active` AND no entry mark); the
  entry-marked path keeps the management stance and serves NO checklist; the no-thesis /
  not-evaluated / mismatched-source / monitor-failed paths serve NEITHER. The same single
  `build_projection` (row 15) — REST `…/thesis/active` == WS `thesis` key verbatim. Never persisted
  (schema stays v7; `verdict_events` untouched; no new endpoint/route).
- **Taxonomy (row 24, additive)** in `app/research/taxonomy.py`: `checklist_checks` (8 ids + labels +
  per-check unit captions), `checklist_stances` (4 labels), `checklist_absence.no_fresh_tape`, the
  factual stance-evidence templates ("N/8 checks pass" register), and the nearest-counterevidence
  template — all served by `GET /research/taxonomy`. This block is iter-21's code-identity canary.

### Frontend
- **`EntryChecklistBlock`** in `apps/frontend/components/ThesisStrip.tsx`: shown only when the
  projection carries `entry_checklist`. Renders the stance chip (palette: `conditions_met` emerald,
  `conditions_not_met` slate, `tape_against` rose, `no_fresh_tape` amber), the eight checks each with
  pass/fail + its margin in **font-mono**, the blocker list (via per-check fail state), and the
  nearest-counterevidence line. **Zero client-side arithmetic, zero stance derivation** — every value
  renders verbatim; labels/copy come from the projection.
- **Carry-along (evaluator-mandated):** the three hardcoded `journaled measurement, R = |entry −
  invalidation|` caption literals are consolidated to one `stanceReadoutCaption(taxonomy)` helper that
  reads `taxonomy.stance_readout_caption` (with a single pre-load fallback) — closes the iter-20
  coherence advisory. `taxonomy` is now threaded into `ManagementStanceBlock` and `NotEvaluatedThesis`.
- Types added to `lib/types.ts`: `EntryChecklist`, `ChecklistCheck`, `ChecklistStance`,
  `ChecklistNearestCounterevidence`, `entry_checklist` on `ThesisProjection`, and the `checklist_*`
  taxonomy fields.

## Files Changed
- `apps/backend/app/config.py` -- two new keys (`checklist_stance_dwell_seconds`,
  `delivery_lag_ok_bound_seconds`), both documented research defaults, both EXCLUDED from
  `config_fingerprint` (see fingerprint decision below).
- `apps/backend/app/engine/snapshot.py` -- additive `delivery_lag_seconds: float | None = None`.
- `apps/backend/app/engine/tape_engine.py` -- `set_delivery_lag()` + the carried `_delivery_lag_seconds`
  field wired into `_build_snapshot` (never read by classification).
- `apps/backend/app/serializers.py` -- `delivery_lag_seconds` served on `/summary` + WS (verbatim).
- `apps/backend/app/watch_manager.py` -- per-mode lag stamping (`_live_delivery_lag` +
  `_paced_delivery_lag` helpers; wired into the sim, paced, progressive, and live feeders).
- `apps/backend/app/research/stance.py` -- the entry-checklist evaluator (the eight checks, the
  dwelled aggregate stance, nearest-counterevidence, `build_checklist`).
- `apps/backend/app/research/monitor.py` -- holds the checklist evaluator + the `rule_first_true`
  chase anchor; advances them in `on_event`; serves the checklist on the pre-entry-mark path via
  `build_projection`'s new `entry_checklist` parameter.
- `apps/backend/app/research/taxonomy.py` -- the checklist catalog (checks/captions, stances,
  absence copy, evidence + counterevidence templates) + served in `taxonomy_payload`.
- `apps/frontend/lib/types.ts` -- checklist types.
- `apps/frontend/components/ThesisStrip.tsx` -- `EntryChecklistBlock` + caption consolidation.
- Tests: `tests/test_research_checklist.py` (new, 33 tests); +6 in `test_research_monitor.py`,
  +9 in `test_watch_manager.py`, +1 in `test_api.py`, +2 in `test_research_api.py`.

## Per-mode `delivery_lag_seconds` semantics (DoD-required documentation)
Feeder-owned; never read by classification (determinism unchanged). Two honest definitions:
- **Live** (`_live_delivery_lag`): `wall_now − (epoch_anchor + latest_logical_ts)` — the latest
  record's real epoch vs the wall clock (goal.md's canonical definition). A healthy live feed reads a
  small lag (delivery + processing latency); a dense tape that outruns processing reads a growing one.
  Clamped at 0 (a clock skew putting the record marginally ahead is reported 0, never negative).
  `None` when there is no epoch anchor yet (no first live record) — honest "no lag measured", distinct
  from a measured 0.0.
- **Paced replay (sim/historical)** (`_paced_delivery_lag`): the feeder's processing backlog against
  its OWN pacing schedule — `actual_wall_elapsed − scheduled_pacing_elapsed`, clamped at 0. A replay
  deliberately hours behind real time is NOT "lagging"; a healthy sim/replay that keeps up with its
  schedule reads ≈0. A backlogged feeder (processing slower than its pacing budget) reads positive.
  Verified live: a healthy SIM-REVERSAL feeder stamped ≈0.0024s, so `tape_lag_ok` passes.

## Config fingerprint decision (DoD-required, per new key)
Both new keys are **EXCLUDED** from `config_fingerprint`, each with the codified iter-12/16/20 pattern
(documented rationale comment + a fingerprint-stability test + the real-threshold counter-test):
- **`checklist_stance_dwell_seconds`** — EXCLUDED. The checklist + its stance are a live cue NEVER
  PERSISTED (schema stays v7 — no checklist row exists), so this timing value touches no persisted
  research value (no verdict/feature/grade/excursion/stamp). Serving-only — two journals identical in
  every threshold but served at different checklist dwells MUST share a fingerprint (else fragmenting
  the analytics pools). Pinned: `test_checklist_dwell_is_serving_only_excluded_from_fingerprint` +
  `test_a_real_threshold_still_changes_fingerprint`.
- **`delivery_lag_ok_bound_seconds`** — EXCLUDED. The `tape_lag_ok` check it gates is part of the
  never-persisted checklist, and `delivery_lag_seconds` is feeder-owned DELIVERY metadata that never
  enters any persisted research value. Serving-only — same precedent. Pinned:
  `test_delivery_lag_bound_is_serving_only_excluded_from_fingerprint` + the same counter-test.

This is the documented "serving-only with rationale + stability + counter test" carve-out the spec
allows; everything that shapes a persisted research value stays IN the fingerprint.

## Tests Run
Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -v`
Result: **750 passed, 1 skipped** (the 1 skip is the pre-existing credentialed real-data test), exit 0.
~51 new tests this iteration. Frontend: `cd apps/frontend && npx tsc --noEmit` exit 0; `npm run build`
exit 0 (no tapeology dev server was running — only unrelated trendora servers — so the build was safe;
static generation all green).

Coverage highlights (per the spec's TESTING REQUIREMENTS):
- Per-check margins against EXACT numeric anchors, boundary cases on BOTH sides of each reused gate.
- **Four-quadrant proof** for the two direction-sensitive checks (not_chasing + invalidation_distance:
  long + short × favorable + adverse).
- Stance aggregation map (every check-combination class -> stance); dwell publish / no-flap / lone
  flicker; `tape_against` on rejecting; `no_fresh_tape` forced on each non-live status INCLUDING from a
  previously-green `conditions_met` (no frozen green).
- Presence rules: checklist ABSENT with no thesis / on the entry-marked path (management stance present
  instead) / on the not-evaluated survivor path / on the monitor-failed path.
- REST==WS verbatim for the new checklist keys; observer-equivalence suite green unchanged (zero
  re-pins); fingerprint stability + counter tests; copy-lint over all new taxonomy strings.
- `delivery_lag_seconds`: per-mode unit coverage (healthy sim ≈0; backlogged feeder > 0; live = record
  epoch vs wall) + a determinism guard that a stamped lag does NOT change state/confidence/features.

## Live end-to-end verification (pre-handoff)
Started a real uvicorn (isolated port + temp DB, then killed — no leak), watched SIM-REVERSAL through
the REAL feeder + REST/WS:
- the feeder stamped `delivery_lag_seconds = 0.0024s` (healthy sim ≈0) -> `tape_lag_ok` passes
  (`lag 0.0s / 5.0s`);
- pre-confirmation the checklist read `conditions_not_met` (5/8 — verdict not confirming, not warm);
- after SIM-REVERSAL's phase-2 reversal confirmed, it reached **`conditions_met` ("8/8 checks pass")**
  with every check passing.
The `GET /research/taxonomy` canary served the new `checklist_checks` block. Backend torn down cleanly
(no orphaned process).

## Known Issues
- **No live-mode `delivery_lag` browser proof this iteration.** Live streaming needs market hours +
  credentials, so the live-mode lag definition is covered by unit tests (`_live_delivery_lag`) and the
  honest `None`/clamp paths, not a browser capture — consistent with the goal's live-data verification
  policy. The paced-replay (sim) path IS exercised live end-to-end above.
- **`tape_lag_ok` reads "no measurement -> fail" when no feeder is running.** In the live app a feeder
  always runs and stamps the lag (verified above), so this is only reachable in a manual in-process
  driver with no feeder — the honest behavior (we cannot assert freshness without a measurement). Not a
  product-facing path.
- **J-64 (the dedicated freshness journey) is intentionally deferred** to the next iteration per the
  spec's OUT OF SCOPE — but the honest `no_fresh_tape` degradation behavior itself IS implemented and
  unit-tested here (forced on every non-live status, no frozen green).
- Depth stayed **lean** per the iter-20 evaluator recommendation (the full-pipeline `qa_complete`
  harness halt from iter-5 is still open); restore full depth when it is fixed.

# goal-referee-iter-6 Execution Plan

## Context

Era 6 "The Referee" (`docs/goal.md`) is a BUILDING era adding calibrated statistics on top of
frozen Playbook/strategy evidence. J-01 (readiness fold), J-02 (evidence contract), J-03
(statistics core), and J-04 (matched nulls) are already shipped (iters 1–5, all `passing`).
This iteration targets **J-05 only** — the registry: pre-registration with an immutable
boundary — at **full depth**, mandated by the prior evaluator's ESCALATE verdict (a standing
rule: once ESCALATE fires, the next iteration is full depth regardless of other signals). Two
small same-file riders carried from iteration 5's review ride along. This is the fourth
`referee_*.py` module, following the exact conventions `referee_evidence.py` and
`referee_null.py` already established — a new module for a new module is expected here, not
duplication.

Confirmed against `docs/referee-statistical-spec.md` §5 (Registry, boundary, checkpoint, BH),
§1 (constants), §2 (observation contract), §3.1–3.3 (estimand context), §7 (starter family
S-1..S-5), and §8 (certificate shape) — the phase spec's TC-1..TC-20 map directly onto these
sections; nothing in the phase spec contradicts goal.md or the spec. No scope creep found: the
spec explicitly excludes J-06 (estimand engines/BH computation), J-07 (registration UI, the
real 2–3 starter registrations), J-08 (certificate minting/promotion interlock), and any diff
to `desk_forward.py`, `desk_playbook*.py`, `levels.py`, `tradability.py`,
`referee_stats.py`'s statistical procedures, or `pnl_scan.py`.

## What to Build

- `app/research/referee_registry.py` (NEW): append-only FAMILY, HYPOTHESIS, WITHDRAWAL, and
  CERTIFICATE stores per spec §5/§8 — no update/delete method on any store class; duplicate
  identity raises (`FamilyAlreadyRecorded`/`HypothesisAlreadyRecorded`/etc., mirroring
  `referee_null.py`'s `NullAlreadyRecorded` pattern).
- Registration validation (`register_hypothesis`-equivalent), refusing distinctly and writing
  nothing on: malformed (required-field gaps, `target_sessions < REFEREE_MIN_SESSIONS`,
  `min_occurrences < REFEREE_MIN_OCCURRENCES`, an Estimand-C `context_predicate`
  `BandMapResolver` cannot evaluate), duplicate `hypothesis_id`/`family_id`, retroactive
  boundary (explicit boundary at/before `registered_at`'s own ET calendar date), unknown
  `null_spec_id`/`test_spec_id`.
- `confirmation_start_boundary` computed by REUSING `referee_evidence._et_session_date(epoch)`
  (line ~398 today — relocate by symbol name) — never a second DST-aware conversion.
- Withdrawal: refuses when a post-boundary evaluation exists, via an INJECTABLE
  evaluation-existence signal (no evaluation store exists until J-06); fixture supplies both
  `True`/`False`. Accepted withdrawal appends a WITHDRAWAL record; the hypothesis record itself
  never changes (immutability).
- Per-hypothesis `accrual` fold on `GET .../registry`, reusing
  `referee_evidence.playbook_occurrence_readiness()`'s existing per-cell pooling (line ~255) —
  never a second `PlaybookStore` scan. Served `is_proxy: true` + `basis_current: bool` (per
  `state/assumptions.md` iter-6 entry — already ratified: this is a disclosed readiness proxy,
  J-06's real evaluation-time count is authoritative later, and this call is not to be
  re-litigated).
- CERTIFICATE store: shape only per spec §8, no writer/mint path this iteration (J-08's job) —
  fixture-seeded only, append-only-ness tested.
- Routes on `referee_routes.py`: `POST /research/desk/referee/registry/hypotheses` (explicit
  confirmation required before any write) and `GET /research/desk/referee/registry` (serves
  `families`, `hypotheses` folded with `status`+`accrual`, `withdrawals`, `certificates`) —
  follow the existing dependency-provider/router pattern exactly (`get_referee_null_store`-style
  providers, `HTTPException` for refusals).
- CLI entry point matching `referee_null.py`'s `argparse`/`main()` convention (registration +
  withdrawal).
- Storage dir: env-var-or-sibling-default alongside the existing `_NULL_DIR`/`_EVAL_DIR`/
  `_LOG_DIR` family (NOT a new `Config` field) — follow `resolve_referee_null_dir`'s exact
  pattern.
- Import-topology guard extension (`tests/test_referee_guards.py`): `referee_registry.py` may
  import the rail/`BandMapResolver`/`referee_evidence`; `desk_playbook_detect`/
  `desk_playbook_context` never import it back.
- **Rider 1** (`referee_null.py`, ~line 533): `backing_bucket_eligibility_rate` currently reads
  `backing_rate = None if map_result is None else 0.0` — when `tod_eligible_count == 0` but
  `map_result` IS resolved, this wrongly falls into the `else` branch and serves `0.0` (implying
  a measured 0% match) instead of `None` (nothing was measurable at all, since zero candidates
  were even checked). Fix: `backing_rate = None` whenever `map_result is None OR
  tod_eligible_count == 0`; the genuine `len(matched)/tod_eligible_count == 0.0` case (real
  candidates checked, zero matched) stays in the existing `else` branch untouched. One-line fix
  inside an already-registered `float|None` field — not a new field.
- **Rider 2** (`tests/test_referee_null.py`): add one fixture offering MORE than
  `REFEREE_NULL_ANCHORS_PER_OCCURRENCE` (4) eligible anchors so the seeded Fisher–Yates subset
  draw is actually discriminated (iter-5's own eval found every existing fixture has
  `eligible_count <= 4`, so today's tests would pass even a broken selector) — hand-verify the
  non-trivial 4-of-N subset is reproducible and a different observation key draws a different
  subset. Plus one hand-computed `window_overlap_fraction` assertion.
- Dev handoff at `docs/handoffs/goal-referee-iter-6-dev.md`.

### Explicitly NOT this iteration

Estimand engines/BH/verdict vocabulary (J-06); the shortlist UI and the operator's real 2–3
starter registrations (J-07 — this iteration only exercises the mechanism on fixtures, even
though S-1..S-5 from spec §7 make good TC-14 fixture material); certificate MINTING/
`authorize_promotion`/the `pnl_scan` interlock (J-08 — only the store SHAPE lands now); new MCP
tools (stays at 20); any new `Config` field; any fingerprint movement.

## Agents Required

- backend-data: yes -- implements `referee_registry.py` (4 store classes, validation, boundary/
  accrual folds, CLI), the two new routes, the two `referee_null.py`/test riders, the guard
  extension, and `tests/test_referee_registry.py` (TC-1..TC-14) per TDD.
- frontend-ux: no -- J-05 is keyless/automated per its own acceptance; zero frontend files
  change this iteration (confirmed by goal.md's iteration metadata `Frontend Present: no` and
  the phase spec's own `Frontend: None` section). J-09 remains the first UI reveal for the
  registry.

## Frontend Present

no

## Files to Create/Modify

- `apps/backend/app/research/referee_registry.py` -- NEW. Family/Hypothesis/Withdrawal/
  Certificate append-only stores, registration validation, boundary computation, accrual fold,
  CLI (`argparse`/`main()`).
- `apps/backend/app/research/referee_routes.py` -- add `GET /research/desk/referee/registry`,
  `POST /research/desk/referee/registry/hypotheses`, their dependency providers, and a
  module-level store singleton pattern matching the existing null-store wiring.
- `apps/backend/app/research/referee_null.py` -- Rider 1: the one-line
  `backing_bucket_eligibility_rate` fix (see above). No other change.
- `apps/backend/tests/test_referee_registry.py` -- NEW. TC-1 through TC-14.
- `apps/backend/tests/test_referee_null.py` -- Rider 2: the >4-eligible-anchor fixture (TC-15)
  + the hand-computed `window_overlap_fraction` assertion (TC-16).
- `apps/backend/tests/test_referee_guards.py` -- extend the import-topology guard to cover
  `referee_registry.py` (TC applies to the whole Read-side-law family; no TC number of its own
  beyond the existing guard suite).
- `docs/handoffs/goal-referee-iter-6-dev.md` -- NEW dev handoff.

## Key Test Scenarios

Full detail is in the phase spec's TC-1..TC-20 (`docs/phases/goal-referee-iter-6.md`) — do not
re-derive, implement from it directly. Highest-risk ones to verify explicitly:

- TC-1/TC-12: duplicate `family_id` / duplicate `certificate_id` each raise on the second
  insert; no update/delete method exists on any of the four store classes (structural,
  source-scan-able).
- TC-2/TC-13: a fixture Estimand-A registration (via CLI and via `POST`) returns a
  `hypothesis_id`; `confirmation_start_boundary` equals the ET calendar date of `registered_at`;
  CLI and `POST` produce byte-identical stored records.
- TC-3/TC-4/TC-5/TC-6/TC-7: each refusal class (missing required field; retroactive boundary;
  unknown `null_spec_id`/`test_spec_id`; an unevaluable Estimand-C `context_predicate`;
  `target_sessions` below `REFEREE_MIN_SESSIONS`) is distinctly refused with NO record written —
  verify via store-listing count before/after, not just the HTTP status.
- TC-8: the ET-midnight boundary case — a UTC instant equal to 23:30 America/New_York on a
  hand-picked date must store that SAME ET calendar date as the boundary, not the UTC date and
  not the next ET date. Pick a fixture date that actually lands in DST or non-DST as appropriate
  to exercise the regime where a naive implementation drifts (iter-3/iter-4's carried lesson:
  sample the regime where the boundary is actually reached, not just "some date").
- TC-9/TC-10: withdrawal succeeds and folds `status: "withdrawn"` when no post-boundary
  evaluation signal is set; withdrawal is refused (no WITHDRAWAL record written, `status` stays
  `active`) when the injected evaluation-existence signal is `True`.
- TC-11: a populated fixture registry's `accrual.informative_post_boundary_sessions` matches a
  hand-counted value from the fixture corpus; `is_proxy: true`; `target_sessions` matches what
  was pinned at registration.
- TC-14: all five starter-family candidates (spec §7 S-1..S-5) register cleanly as fixtures with
  zero refusals and distinct `hypothesis_id`s carrying their named estimand/null-spec/primary
  pairing.
- TC-15/TC-16 (riders): the seeded draw is discriminated by a real >4-eligible-anchor fixture
  (byte-identical repeat draw; a different observation key draws a different subset); a
  hand-computed `window_overlap_fraction` matches to float tolerance.
- TC-17: the `backing_bucket_eligibility_rate` rider — `None`, never `0.0`, when zero anchors
  are measurable at all.
- TC-18/TC-19/TC-20 (whole-suite gates): full suite collects >= iter-5's baseline (2,553
  collected / 2,545 passed / 8 skipped), 0 failed; `Config().config_fingerprint()` prints
  `08e471b10130e1e2`; `EXPECTED_TOOLS` still parses to exactly 20 names; the store-scope guard
  over the owner's real `.data/` directory shows every previously-recorded file (11,274 at last
  count) byte-identical.

## Build Notes / Risk Flags

- **Naming collision to avoid:** `app/research/routes.py` already has an unrelated
  `ResearchRegistry` class (a DI container). Keep `referee_registry.py`'s FAMILY/HYPOTHESIS/
  WITHDRAWAL/CERTIFICATE registry nowhere near it in imports/naming — a likely reviewer
  false-positive the phase spec itself calls out.
- **Estimand-C "cannot evaluate" (TC-6) requires an interpretation call**, since a hypothesis
  registers against a setup+side abstractly (no concrete symbol/session yet) — there is no live
  bar series to literally invoke `BandMapResolver.resolve()` against at registration time. The
  spec's own text ("not evaluable at anchor bars from recorded data") suggests checking the
  named backing-bucket value against the fixed vocabulary (`PLAYBOOK_CONTEXT_BACKING_BUCKETS` in
  `desk_playbook_context.py`) is the intended structural check, not a live resolve call. If this
  is genuinely ambiguous when the developer implements it, log it in
  `runs/goal-session-referee/state/assumptions.md` rather than improvising silently (goal.md's
  own T-1 rule) — do not block on it.
- **Two interpretation calls already ratified this iteration** (`state/assumptions.md`, both
  logged by the decomposer, not open questions): (1) `accrual` is a disclosed proxy, not spec
  §3.1's exact informative-session count; (2) null records stay filed by null-spec id, never
  re-keyed under `hypothesis_id` — `referee_null.py`'s null-record identity is UNCHANGED this
  iteration (only the one-line Rider 1 fix touches that file).
- **Host protection:** any dev-server restart during QA must stop by exact PID (per-process, via
  `lsof`/`ss`), never a pattern-based `pkill` — a prior iteration's `pkill` hit an unrelated
  project sharing this host.
- Zero new `Config` fields, zero fingerprint movement, zero diff to `desk_forward.py`,
  `desk_playbook*.py`, `levels.py`, `tradability.py`, `referee_stats.py`'s statistical
  procedures, or `pnl_scan.py` — read-only imports at most. No new MCP tool.

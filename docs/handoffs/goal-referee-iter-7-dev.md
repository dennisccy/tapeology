# goal-referee-iter-7 Dev Handoff

**Phase:** goal-referee-iter-7 (J-06: Estimand engines and adjudication)
**Date:** 2026-08-15
**Agent:** developer
**Status:** complete

## What Was Built

**New module `apps/backend/app/research/referee_adjudicate.py`** — the estimand engines (A/B/C),
evaluation as a recorded operator act, the single append-only confirmatory checkpoint with its
family BH fold, the read-side adjudication fold, and `authorize_promotion` (spec
`docs/referee-statistical-spec.md` §3/§5/§8):

- **Eligible-occurrence gather** (`_eligible_setup_side_occurrence` — shared by A/B/C): every J-02
  observation of a hypothesis's own `(setup_id, side)` cell at its registered primary
  `(measure_key, horizon)`, filtered to STRICTLY post-boundary, completed-session records only.
  Cross-references each observation's raw `PlaybookStore` record (via the encoded `record_id` in
  `observation_id`) for `setup_id`/`side`, since the J-02 contract doesn't carry them directly.
- **Estimand A/C pooling** (`_pool_against_null`): shares ONE routine — spec §3.3 "as estimand A,
  but against the context-matched null" — reads each occurrence's already-recorded matched-null
  record from `RefereeNullStore` (never a live null build; GETs/evaluations never compute a null).
  An occurrence with no eligible anchors is excluded and counted, never substituted.
- **Estimand B pooling** (`_pool_cell_vs_complement`): occurrences split into the registered
  context cell vs. its complement via a NEW `referee_null.resolve_occurrence_backing_bucket`
  export (reached transitively, since `referee_adjudicate.py` is banned from importing
  `desk_playbook_context` directly — only `referee_null.py` holds that exception).
- **The primary test, robustness disclosures, CIs**: `referee_stats.permutation_test`/
  `sign_flip_result`/`equal_weight_t`/`bootstrap_ci_occurrence`/`bootstrap_ci_cluster` reused
  verbatim over the pooled `session_groups`. Confirmatory fields (`T`, `permutation_p`,
  `permutation_enumeration`, `min_attainable_p`) are withheld (`None`) below the registered
  floors (T-4, optional stopping); descriptive companions (CIs/sensitivities) are computed
  whenever there is pooled data, regardless of eligibility, since they are never a decision rule.
- **The entry-basis sensitivity** (spec §4.3, A/C only): re-measures each pooled occurrence
  close-anchored at its own trigger bar via `referee_null._locate_measurement_series`/
  `_measure_one_anchor` (imported directly — the established cross-module private-helper reuse
  convention in this codebase).
- **Evaluation store + run ledger** (`RefereeEvaluationStore`, `RefereeEvaluationRunStore`) and
  the **adjudication snapshot store** (`AdjudicationSnapshotStore`) — the shared-directory,
  distinct-filename-prefix pattern (`evaluation-*.json` / `snapshot-*.json`, mirroring
  `referee_registry.py`'s four-record-kinds-one-directory shape), rooted at
  `TAPEOLOGY_DESK_REFEREE_EVAL_DIR` / `TAPEOLOGY_DESK_REFEREE_EVAL_LOG_DIR` — deliberately not
  `Config` fields.
- **The compute walker + manager** (`run_evaluation_and_record`, `RefereeEvaluationComputeManager`):
  mirrors `RefereeNullComputeManager` exactly — single-flight PER `hypothesis_id`, snapshot-
  pollable progress across 8 named phases, cooperative cancel checked before each phase (no
  partial evaluation record on cancel), dedup reuse keyed on `(hypothesis_id, evaluation_basis)`
  (an unchanged store recomputes nothing).
- **The family BH fold** (`_family_bh_fold`, `_family_p_values`): a thin, directly-testable
  wrapper around `referee_stats.benjamini_hochberg` — `m` is always the family's frozen planned
  count; an unevaluated or withdrawn-without-checkpoint sibling folds as `p=1`, never dropped.
- **The four fragility triggers** (`_build_and_record_snapshot`): `by_fail`, `sign_flip`
  (the equal-weight sensitivity's own `T` flipping sign — `sign_flip_result` structurally cannot,
  since it shares the identical `T` as the primary test), `entry_basis_sign_flip`,
  `cluster_ci_includes_zero`.
- **The read-side fold** (`adjudications_response`): per registered hypothesis, the recorded
  snapshot verbatim (attestation RE-verified at fold time, never trusted from checkpoint time) if
  one exists, else a cheap LIVE recount (`registered` / `pending_forward_confirmation`) —
  `basis_retired` wins unconditionally over any other state. `exploratory` and `killed` are
  documented, currently-unreachable enum members (logged to `state/assumptions.md`). Also hardens
  against a corrupted SNAPSHOT file specifically: a hypothesis whose own `snapshot-*.json` fails
  its integrity check folds to a dedicated `confirmatory_output_refused` state (never silently
  falling back to the live/pre-checkpoint fold, which would otherwise misrepresent an
  already-`corroborated` permanent record as merely "pending" — the hypothesis_id is recovered
  straight from the filename even when the file's own JSON content is unparseable).
- **`authorize_promotion`**: a pure function over `(candidate, certificate_store,
  live_scan_context)` implementing all 6 named refusal classes with a concrete partition (logged
  to `state/assumptions.md`) — `malformed_unverifiable` → `no_certificate` → `wrong_candidate` →
  `stale` → `mismatched_datasets` → `failed_gates` → authorized. NOT wired into `pnl_scan._promote`
  (J-08's job).
- **`REFEREE_GATE_VERSION`** (`"referee-gate-v1"`) and **`REFEREE_REGISTER`** (the served
  disclosure text, first authored this iteration) — both module constants, never `Config` fields.

**New routes on the existing `referee_routes.py` router** (no new router registration):
`GET /research/desk/referee/evaluations` (`?hypothesis_id=`), `POST/GET/POST-cancel
/research/desk/referee/evaluate`, `GET /research/desk/referee/evaluate/runs`, `GET
/research/desk/referee/adjudications` — mirror the null-compute route shapes exactly.

**`referee_null.py` addition** (new export, zero diff to any existing function):
`resolve_occurrence_backing_bucket(signal, symbol, trigger_epoch, price, side, context_resolver)`
— reuses the SAME `band_context_block` call `build_null_record`'s context branch already makes
for an anchor bar, applied to an occurrence's own price. Needed because Estimand B has no null to
lean on for cell/complement determination and `referee_adjudicate.py` cannot import
`desk_playbook_context` directly.

**New import-topology guard** (`test_referee_guards.py`): an explicit, file-named test proving
`referee_adjudicate.py` imports neither `desk_playbook_detect` nor `desk_playbook_context`
directly (the glob-based guards already covered it implicitly; this makes it undeniable).

### The three riders

- **Rider 1** (`referee_evidence.py`, the "1969 date" bug): `_strategy_observation` now returns
  `None` — excluded and counted in a new `excluded_missing_epoch_anchor` field on
  `strategy_observations()`'s return dict — when `dataset.get("epoch_anchor")` is genuinely
  `None`/absent, instead of silently defaulting to the Unix epoch via the old `or 0.0`. An
  EXPLICIT `epoch_anchor == 0.0` (the existing fixture's own value) is unaffected and still
  anchors normally — the bug was specifically conflating "missing" with "explicitly zero."
- **Rider 2** (`referee_registry.py`, audit gap B4): `registry_response()` now surfaces all four
  stores' `integrity_errors` (tagged with `store: "family"|"hypothesis"|"withdrawal"|
  "certificate"`) as a new fifth top-level `integrity_errors` key, reusing the
  `get_referee_nulls` disclosure pattern rather than inventing a second shape. The four-key GET
  shape pinned in `state/blueprint.md` is now five keys — updated as part of this fix, per the
  iteration's own explicit rider text.
- **Rider 3** (`referee_registry.py` + its test): removed the three reviewer-flagged dead imports
  (`sys`, `Config`, `resolve_desk_playbook_dir`). The seeded random-draw test the rider text names
  ("`test_referee_registry.py`'s seeded random-draw test") does not exist in that file — cross-
  referencing the cited audit finding IDs (B5/T1) in `docs/handoffs/goal-referee-iter-6-audit.md`
  shows T1 actually names `tests/test_referee_null.py`'s TC-15 test (the tautological
  `expected_drawn = _draw_anchor_indices(stream, 7, 4)` re-derivation, calling the SAME function
  `build_null_record` calls internally). Fixed there: replaced the re-derivation with the OBSERVED
  4-element literal `[3, 4, 5, 7]`, captured once out-of-band by running the exact fixture through
  the real selector (documented inline; this is presumably a minor file-naming slip in the phase
  spec's prose, not a genuine second location).

## Files Changed

- `apps/backend/app/research/referee_adjudicate.py` -- NEW: the whole J-06 module (~1050 lines)
- `apps/backend/app/research/referee_null.py` -- new `resolve_occurrence_backing_bucket` export; zero diff to any existing function
- `apps/backend/app/research/referee_registry.py` -- Rider 2 (`integrity_errors` disclosure) + Rider 3 (dead-import removal)
- `apps/backend/app/research/referee_evidence.py` -- Rider 1 (epoch_anchor exclusion fix)
- `apps/backend/app/research/referee_routes.py` -- mounts the 6 new J-06 routes
- `apps/backend/tests/test_referee_adjudicate.py` -- NEW: 39 tests covering TC-1 through TC-34 plus route-level checks
- `apps/backend/tests/test_referee_null.py` -- new `resolve_occurrence_backing_bucket` tests; TC-15 literal-pin fix (Rider 3)
- `apps/backend/tests/test_referee_registry.py` -- `integrity_errors` shape updates; new TC-30 corrupted-file test
- `apps/backend/tests/test_referee_evidence.py` -- new TC-29 tests (epoch_anchor exclusion + counter-test); one shape-update to an existing exact-equality assertion
- `apps/backend/tests/test_referee_guards.py` -- new explicit `referee_adjudicate.py` import-topology guard test
- `runs/goal-session-referee/state/assumptions.md` -- 5 new developer-level interpretation-call entries (authorize_promotion refusal-class partition, the `sign_flip` trigger's semantic, entry-basis scope A/C-only, `exploratory` unreachable, confirmatory-field gating scope)
- `runs/goal-referee-iter-7/status.json` -- new, `current_step: dev_complete`

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/ -q --junit-xml=...`

Result: **2,642 collected / 2,634 passed / 8 skipped / 0 failed / 0 errors** (grew from iteration
6's baseline of 2,595 / 2,587 / 8, with nothing newly failing). `Config().config_fingerprint()`
prints `08e471b10130e1e2` (unchanged). `tests/test_mcp_server.py::EXPECTED_TOOLS` still parses to
exactly 20 tool names (zero new MCP tools this iteration — J-09's job).

Focused run: `tests/test_referee_*.py` — 216 passed, 0 failed, ~93s (includes the oracle suite's
own runtime budget).

New test file `tests/test_referee_adjudicate.py` — 40 tests, all passing, covering: the DoD
fixture round-trip (known-positive → `corroborated`, known-null → `no_evidence`, both through the
real registration → null build → evaluation → snapshot code path), the pre-boundary/deep-
backfilled counter-test (TC-8), checkpoint immutability + byte-stable adjudications fold (TC-11,
TC-23, DoD), tampered-attestation refusal (TC-22), all three estimands' pooling math (TC-1
through TC-4), all four fragility triggers + BH-boundary verdicts (TC-5, TC-6, TC-14, TC-15,
TC-16, TC-17, TC-18, TC-19), the full read-side verdict vocabulary (TC-20, TC-21, TC-24, TC-25),
a corrupted adjudication-snapshot file refusing rather than silently reverting to the live fold
(the hardening fix described above), `authorize_promotion` for all 6 refusal classes plus the
success path (TC-26, TC-27, TC-28, plus 4 additional direct tests for the other refusal classes),
the compute manager's single-flight and
cancel semantics (TC-32, TC-33, plus a deterministic `should_abort`-from-the-start no-partial-
record proof), the CLI's dedup-reuse on a second run (TC-34), and route-level round trips
(register → evaluate → read adjudications, honest empty states, 422 on unknown hypothesis_id,
409 on idle cancel).

**Pre-handoff verification**: started the real backend (`scripts/start-backend.sh`, port 8301),
exercised every new route live (`/evidence`, `/registry`, `/evaluations`, `/adjudications`,
`/evaluate` GET/POST, `/evaluate/runs`) against the REAL production stores — the real registry is
still empty (`{"families":[],"hypotheses":[],...}`, correct: J-07's registration act hasn't run
yet), confirming zero accidental writes and honest empty states over live data. Stopped the
server by its exact captured PID, restarted it to confirm no port conflicts, stopped it again by
exact PID. No pattern-based kills used, per the pump note's host-sharing warning.

## Known Issues

- **J-10's kept-product browser walk is out of this developer agent's scope.** `Frontend Present:
  no` is accurate for J-06 itself — no UI changed. The iteration spec's DEFINITION OF DONE
  requires "J-10's kept-product browser walk produces a FRESH dated screenshot this iteration (it
  did not run at all in iteration 6)" — this needs the browser-QA stage (Chrome MCP against the
  live cockpit/`/structure`/`/desk` pages), which is downstream of the developer role. Nothing in
  this iteration's backend diff touches any shipped route, page, or `data-testid` — the kept
  surfaces should be unaffected, but the actual screenshot evidence still needs to be captured by
  QA.
- **`authorize_promotion`'s refusal-class partition is an interpretation call**, logged in detail
  to `state/assumptions.md`. It satisfies TC-26/27/28 literally and gives each of the other three
  refusal classes (`wrong_candidate`, `mismatched_datasets`, `failed_gates`) its own
  non-overlapping trigger, but the canonical spec (§8) does not fully disambiguate the boundary
  itself. J-08 (which wires this into `pnl_scan._promote` and owns "full fixture coverage") should
  review this partition before minting real certificates against it.
- **The `"sign_flip"` fragility-trigger semantic** (equal-weight `T` sign flip, not
  `sign_flip_result`'s own output) is a non-obvious deduction from the two functions' own
  definitions, logged to `state/assumptions.md` with the reasoning spelled out. Worth a second set
  of eyes given how permanent adjudication snapshots are.
- **Estimand B's entry-basis sensitivity is honestly `None`** (structurally out of scope per spec
  §4.3's own framing around an occurrence-vs-null comparison) — logged to `state/assumptions.md`.
  A future spec revision could name a B-specific treatment; nothing here blocks that.
- **The real production registry has zero hypotheses** (verified live, see above) — J-07's
  registration act has never run. This iteration's fixture-based tests are the only evidence any
  evaluation/adjudication code path has ever executed; the DoD's "REAL corpus serves honest
  registered/pending_forward_confirmation states" clause is trivially true today (zero entries),
  not yet exercised against a populated real registry.
- **`REFEREE_REGISTER`'s text is not yet wired into `test_copy_discipline.py`'s scanned surfaces**
  (that lint walks `GET /research/taxonomy` + frontend source; `/adjudications` isn't in either
  yet) — extending that lint with the referee copy is explicitly J-09's job per goal.md, not this
  iteration's. The text was written to already comply in spirit (negated claim words, matching the
  house idiom).

## Rider 3 file-naming note

Flagging for the reviewer/auditor: the iteration spec's Rider 3 prose says "re-pin
`test_referee_registry.py`'s seeded random-draw test" but no such test exists in that file — the
actual tautological-re-derivation test (matching every other detail of the description) lives in
`tests/test_referee_null.py` (TC-15), and is exactly what audit finding T1 in
`docs/handoffs/goal-referee-iter-6-audit.md` names by file and line. Fixed there; documented
inline in that test's own comment. If this reading is wrong, the fix is a one-line move.

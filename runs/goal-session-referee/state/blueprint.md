# App Blueprint — referee (Era 6 "The Referee")

<!--
Coherence contract for this session. Drafted at baseline (iteration 0) from docs/goal.md's
Product Shape + Must-have journeys. Auto-approved by default; pass --require-blueprint-approval
to pause for human review. Additive edits (new value rows, new pages under an existing nav
section) need no re-approval; a nav-skeleton change does.
-->

## Information Architecture

**Layout shell:** persistent top nav + main content area; dark-only, dense, terminal-grade
(tables and text, no dashboard cards/gauges) — unchanged since Era B2.

**Navigation skeleton** (`app/meta.py` `UI_ROUTES` — exactly 3 routes; this era adds sections
to Desk only, no new route):

```
Tapeology
├── Cockpit    `/`          — sim tape + live/historical chart
├── Structure  `/structure` — S/R levels/zones, tradable-map, structure_tape vs v1
└── Desk       `/desk`      — screen ledger, forward returns, refresh chain, briefing,
                              skipped, runs/pins/compare/provenance, Playbook (detectors +
                              band context + cohorts) — ALL SHIPPED (Era B/B2/R-4) —
                              plus, THIS ERA, rendered BELOW every shipped section:
                              Referee Registry / Referee Adjudications / Referee Runs
```

**Feature / journey homes** (≤2 clicks from nav; every Era-6 journey lives under Desk or has
no dedicated page):

| Feature / journey | Canonical home (route) | Nav section |
|---|---|---|
| J-01 per-family readiness fold (backend fold; surfaces inside the J-07 shortlist) | `GET /research/desk/referee/evidence` | Desk |
| J-02 evidence contract, J-03 stats core (library modules, no page of their own) | n/a — consumed by J-04–J-09 | — |
| J-04 matched nulls — compute controls + ledger | `/desk` → **Referee Runs** | Desk |
| J-05 registry — families/hypotheses/withdrawals/certificates | `/desk` → **Referee Registry** | Desk |
| J-06 adjudication — verdict snapshots + pending fold | `/desk` → **Referee Adjudications** | Desk |
| J-07 starter-family shortlist + registration flow | `/desk` → **Referee Registry** (shortlist sits above the registered-hypotheses table) | Desk |
| J-08 promotion interlock | no new page — reads inside the EXISTING `pnl_scan` report's `promotion` block, wherever the shipped `/desk` sections already render scan reports | Desk |
| J-09 full Referee UI + MCP contract v5 | `/desk`, the three sections above; MCP `desk_referee` / `desk_referee_registry` | Desk |
| J-10 regression sentinel | all three routes, every kept section | Cockpit / Structure / Desk |

## Data Contract

New rows for this era, verbatim from `docs/goal.md` § Product Shape (the canonical source —
do not re-derive):

| Value | Owner (module) | Serving endpoint |
|---|---|---|
| Referee evidence coverage + per-family readiness | new `app/research/referee_evidence.py` | `GET /research/desk/referee/evidence` |
| Matched-null records | new `app/research/referee_null.py` | `GET /research/desk/referee/nulls` (`?id=`) |
| Null compute progress + runs | same module + its log | `POST/GET/POST-cancel /research/desk/referee/nulls/compute`, `GET .../nulls/runs` |
| Registry (families, hypotheses, withdrawals, certificates) | new `app/research/referee_registry.py` | `GET /research/desk/referee/registry`; `POST /research/desk/referee/registry/hypotheses` (operator act) |
| Evaluation records + runs | new `app/research/referee_adjudicate.py` + its log | `GET /research/desk/referee/evaluations`, `POST/GET/POST-cancel .../evaluate`, `GET .../evaluate/runs` |
| Adjudications (snapshots + pending fold) | `referee_adjudicate.py` | `GET /research/desk/referee/adjudications` |
| Promotion authorization verdict | `referee_adjudicate.py` (`authorize_promotion`) | consumed inside `pnl_scan._promote`; surfaced in the scan report's `promotion` block |

**Unchanged owners the Referee reads verbatim (never re-implements — import-ban guard-tested):**
playbook records → `desk_playbook.py`; measurement rail → `desk_forward.py`
(`_measure_from`, `_draw_anchor_indices`, imported, zero diff); band maps →
`desk_playbook_context.BandMapResolver`; session honesty → `desk_sessions.py`; strategy
trades/datasets → `store.py`/`datasets.py`; config fingerprint → `app/config.py`
(`Config().config_fingerprint()` == `08e471b10130e1e2`, frozen this whole era); MCP tool
count → `apps/backend/tests/test_mcp_server.py::EXPECTED_TOOLS` (20 today, 22 after J-09).

<!-- Baseline note (iter-0): confirmed via directory listing that none of the referee_*.py
modules exist yet in app/research/, and EXPECTED_TOOLS has exactly 20 entries with no referee
tools. Every row above is a J-01-J-09 build target for future iterations, not an
already-shipped value. No shared numeric/derived value outside this table is introduced by
this era. -->

<!-- iter-4 note: the "Referee evidence coverage + per-family readiness" row (owner
referee_evidence.py, GET /research/desk/referee/evidence) gains one additive field this
iteration — stale_basis_dates: list[{session_date: str, record_detector_basis: str}] — served
on BOTH playbook_occurrence_readiness()'s response (live at the endpoint above, J-01) and
playbook_observations()'s response (unconsumed by any route this iteration, J-02), computed by
one shared helper both call. Discloses a date whose newest Playbook record's own
(detector_basis, config_fingerprint) does not match the live values, instead of that record
silently contributing zero. No existing field's value changes; the row's owner/endpoint stay
exactly as above — this is a field addition, not a new value or a new canonical source. -->

<!-- iter-5 note: the "Matched-null records" and "Null compute progress + runs" rows (owner
referee_null.py, unchanged from the baseline registration above) gain their first field-level
shape this iteration -- both rows existed as owner+endpoint stubs since iter-0; nothing about
either row's owner or endpoint changes.

Null record: null_record_id: str (pure function of (observation_id, null_spec_signature)),
null_spec_id: "referee-null-tod-v1"|"referee-null-context-v1", null_spec_signature: str
(sha256[:16] of that id's full parameter blob), observation_id: str, symbol: str, session_date:
"YYYY-MM-DD", side: "long"|"short", tod_bucket: "open"|"mid"|"close", k_requested: int,
k_drawn: int, eligible_count: int, excluded: bool, anchors: list[{anchor_ts: str (ISO-8601
UTC), measure_key: str, value: float, window_overlap_fraction: float, backing_bucket_match:
bool|None}], mean_window_overlap: float|None, non_finite_excluded_count: int,
backing_bucket_eligibility_rate: float|None (context variant only), context_algorithm_version:
str|None, provenance: {config_fingerprint: str, computed_at: str (ISO-8601 UTC)}.

Run-ledger record: run_id: str, null_spec_id: str, state:
"running"|"completed"|"failed"|"cancelled", started_at: str, finished_at: str|None, progress:
{done: int, total: int}, error: str|None.

Both records are recorded by referee_null.py this iteration but are not yet rendered anywhere
(J-09 is their first UI consumer, per the Information Architecture row above) -- no WARN needed,
this value is registered same-iteration as it is introduced. Not consumed yet by GET
/research/desk/referee/evidence or any other already-registered row. -->

<!-- iter-6 note: the "Registry (families, hypotheses, withdrawals, certificates)" row (owner
referee_registry.py, endpoints GET/POST /research/desk/referee/registry[/hypotheses] --
unchanged from the baseline registration above) gains its first field-level shape this
iteration -- the row existed as an owner+endpoint stub since iter-0; nothing about its owner or
endpoint changes. Still not rendered anywhere (J-09 remains its first UI consumer, per the IA
table above); J-07 (next) is its first real caller (the registration act).

Family record (immutable, append-only): family_id: str, q: float (0 < q <= 1),
candidate_hypothesis_ids: list[str] (the COMPLETE planned list -- the BH denominator m,
forever), registered_at: str (ISO-8601 UTC).

Hypothesis record (immutable, append-only): hypothesis_id: str, family_id: str, registered_at:
str (ISO-8601 UTC), evidence_family: "playbook"|"strategy", estimand: "A"|"B"|"C", setup_id:
str, side: "long"|"short", context_predicate: dict|None (B/C only), primary_measure_key: str,
primary_horizon: str, sidedness: "greater"|"less"|"two-sided", null_spec_id: str|None (None for
evidence_family="strategy" -- the strategy analog uses the recorded random_null, not
referee_null.py), test_spec_id: str ("referee-test-perm-v1" today), detector_basis: str|None
(None for strategy, mirroring referee_evidence.py's existing convention), context_algorithm_version:
str|None (B/C only), confirmation_start_boundary: str ("YYYY-MM-DD", the ET calendar date of
registered_at; sessions admitted strictly after), target_sessions: int (>= REFEREE_MIN_SESSIONS),
min_occurrences: int (>= REFEREE_MIN_OCCURRENCES), origin: "historical-exploration". Fold-only
(read-side, never persisted on the record itself): status: "active"|"withdrawn"; accrual:
{informative_post_boundary_sessions: int, target_sessions: int, is_proxy: true, basis_current:
bool} -- a disclosed READINESS PROXY (distinct post-boundary session_dates carrying >=1
observation in the hypothesis's own (setup_id, side) cell, reusing
referee_evidence.playbook_occurrence_readiness()'s existing per-cell pooling), NOT yet spec
§3.1's exact "eligible occurrence with eligible anchor" informative-session count -- J-06's real
evaluation-time count supersedes it as the only number that ever gates a confirmatory
evaluation (see state/assumptions.md iter-6 entry).

Withdrawal record (immutable, append-only; permitted only while no post-boundary evaluation of
the hypothesis exists): hypothesis_id: str, withdrawn_at: str (ISO-8601 UTC), reason: str|None.

Certificate record (immutable, append-only store defined this iteration; SHAPE per
docs/referee-statistical-spec.md §8 -- store-only, no writer/mint path until J-08, per
docs/goal.md's own "mintable only through the real evaluation rail" law; served as an empty
certificates: [] this iteration): candidate: {strategy_id: str, profile: str},
champion_identity_at_scan_time: dict, train_dataset: {id: str, checksum: str, split: str},
holdout_dataset: {id: str, checksum: str, split: str}, config_fingerprint: str, gate_version:
str, referee_parameters_hash: str, family_id: str, hypothesis_id: str, gate_results:
{calibrated_p: float, bh_pass: bool, ci: [float, float], floors_met: bool}.

GET /research/desk/referee/registry response: {families: [FamilyRecord...], hypotheses:
[HypothesisRecord + status + accrual...], withdrawals: [WithdrawalRecord...], certificates:
[CertificateRecord...] (empty this iteration)}. -->

<!-- iter-7 note: the "Evaluation records + runs" and "Adjudications (snapshots + pending
fold)" rows (owner new referee_adjudicate.py, endpoints as registered above) gain their first
field-level shape this iteration -- both rows existed as owner+endpoint stubs since iter-0;
nothing about either row's owner or endpoint changes. Still not rendered anywhere (J-09 remains
their first UI consumer, per the IA table above); this iteration's own test suite + the
evaluator's live-code checks are the only current readers.

Evaluation record (append-only, one per evaluation act -- NOT only the checkpoint):
evaluation_id: str, hypothesis_id: str, family_id: str, evaluated_at: str (ISO-8601 UTC),
evidence_family: "playbook"|"strategy", estimand: "A"|"B"|"C", evaluation_basis: str
(sha256[:16] of the dedup record-id set + coverage counts, null record ids, null/test-spec ids,
seeds, B, STATS_CORE_VERSION), coverage: {post_boundary_informative_sessions: int,
target_sessions: int, min_occurrences: int, occurrences_pooled: int,
one_group_sessions_excluded: int}, confirmatory_eligible: bool, role:
"pending"|"checkpoint"|"monitoring", T: float|None, permutation_p: float|None,
permutation_enumeration: bool|None, min_attainable_p: float|None, ci_occurrence: [float,
float]|"insufficient_sample"|None, ci_cluster: [float, float]|"insufficient_sample"|None,
sign_flip_p: float|None, equal_weight_T: float|None, entry_basis_T: float|None,
entry_basis_sign_flip: bool|None, attestation: {passed: bool, expected: dict, actual: dict,
tolerance: dict, stats_core_version: str}, provenance: {config_fingerprint: str, computed_at:
str}.

Adjudication snapshot record (append-only, exactly ONE per hypothesis, written only at its
checkpoint evaluation, immutable thereafter): snapshot_id: str, hypothesis_id: str, family_id:
str, checkpoint_evaluation_id: str, snapshot_at: str (ISO-8601 UTC), bh: {q: float, m: int,
k_star: int, bh_pass: bool, by_adjusted_p: float, by_pass: bool} (m = the family's frozen
planned candidate count, never the count actually evaluated), fragility_triggers: list[str]
(subset of "by_fail"|"sign_flip"|"entry_basis_sign_flip"|"cluster_ci_includes_zero"), verdict:
"no_evidence"|"insufficient_sample"|"fragile"|"corroborated", evaluation_basis: str (frozen
copy of the checkpoint evaluation's own), attestation: dict (frozen copy).

Evaluation run-ledger record: run_id: str, hypothesis_id: str, state:
"running"|"completed"|"failed"|"cancelled", started_at: str, finished_at: str|None, progress:
{done: int, total: int}, error: str|None -- mirrors the J-04 null run-ledger shape exactly.

GET /research/desk/referee/adjudications response: {entries: [{hypothesis_id: str, verdict:
"exploratory"|"registered"|"pending_forward_confirmation"|"insufficient_sample"|"fragile"|
"no_evidence"|"corroborated"|"basis_retired", confirmatory_output_refused: bool,
refusal_reason: str|None, snapshot: SnapshotRecord|None, live_coverage: {...}|None}...],
register: REFEREE_REGISTER}. "killed" is a documented, never-emitted enum member this iteration
(no registered kill-condition mechanism exists anywhere in the spec or the Hypothesis record
schema -- dropped per T-1, see state/assumptions.md iter-7 entry); "basis_retired" and
confirmatory-output-refusal are both computed by referee_adjudicate.py itself, reusing
referee_evidence.py's current_playbook_detector_basis()/_is_stale_basis-style comparison and
referee_stats.py's verify_oracle_attestation() rather than re-deriving either check.

authorize_promotion(candidate, certificate_store, live_scan_context) return shape (not yet a
served HTTP value -- J-08 surfaces it inside pnl_scan's report, per this table's existing
"Promotion authorization verdict" row): {authorized: bool, refusal_class:
"no_certificate"|"stale"|"wrong_candidate"|"mismatched_datasets"|"failed_gates"|
"malformed_unverifiable"|None, reason: str|None}. Reads the CertificateStore that already
exists (J-05 SHAPE-only, still empty -- no mint path until J-08); this iteration adds no writer
to it. -->

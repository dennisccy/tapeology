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
| Registry (families, hypotheses, withdrawals, certificates) | new `app/research/referee_registry.py` | `GET /research/desk/referee/registry`; `POST /research/desk/referee/registry/hypotheses` (operator act); `GET /research/desk/referee/registry/shortlist` (J-07, live readiness over spec §7's pinned S-1..S-5 candidates) |
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

GET /research/desk/referee/registry response (superseded by the iter-8 note below -- Rider 2
added a fifth key the same iteration this note was never updated for; left here only for the
historical field-level shapes above, which are still exactly correct): {families:
[FamilyRecord...], hypotheses: [HypothesisRecord + status + accrual...], withdrawals:
[WithdrawalRecord...], certificates: [CertificateRecord...] (empty this iteration)}. -->

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
str}. (iter-8 Rider 1 note: `role` MUST fold to "pending", never "checkpoint", when
`attestation.passed` is false -- see the iter-8 note below.)

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
referee_stats.py's verify_oracle_attestation() rather than re-deriving either check. (iter-8
Rider 2 note: this response gains an `integrity_errors: [...]` key this iteration, mirroring
`GET /registry`'s existing disclosure -- see the iter-8 note below.)

authorize_promotion(candidate, certificate_store, live_scan_context) return shape (not yet a
served HTTP value -- J-08 surfaces it inside pnl_scan's report, per this table's existing
"Promotion authorization verdict" row): {authorized: bool, refusal_class:
"no_certificate"|"stale"|"wrong_candidate"|"mismatched_datasets"|"failed_gates"|
"malformed_unverifiable"|None, reason: str|None}. Reads the CertificateStore that already
exists (J-05 SHAPE-only, still empty -- no mint path until J-08); this iteration adds no writer
to it. -->

<!-- iter-8 note (J-07): fixes the iter-7 coherence-auditor's advisory (blueprint.md:149-151
was stale after Rider 2 added a fifth response key the same iteration this note went
unupdated) -- the corrected, current shape of GET /research/desk/referee/registry is:

{families: [FamilyRecord...], hypotheses: [HypothesisRecord + status + accrual + discovery...],
withdrawals: [WithdrawalRecord...], certificates: [CertificateRecord...] (empty until J-08),
integrity_errors: [...] (iter-7 Rider 2)}.

Two pieces this iteration, both under the SAME owner (referee_registry.py) and the SAME
Registry row the top table already names -- only the top table's endpoint CELL gained a third
endpoint (see above); no new Data Contract row:

1. NEW endpoint `GET /research/desk/referee/registry/shortlist`: serves spec Sec7's five
pre-registered candidates (S-1..S-5) beside LIVE readiness -- {candidates: [{candidate_id:
"S-1".."S-5", estimand: "A"|"B"|"C", evidence_family: "playbook", setup_id: str, side:
"long"|"short", context_predicate: dict|None, primary_measure_key: str, primary_horizon: str,
sidedness: "greater"|"less"|"two-sided", null_spec_id: str|None, test_spec_id: str, rationale:
str, n: int >= 0, n_sessions: int >= 0, target_sessions: int, min_occurrences: int,
accrual_rate_sessions_per_day: float >= 0, projected_days_to_target: float|None (None when
accrual_rate is 0 -- never a divide-by-zero value)}, ...]}. The n/n_sessions readiness numbers
for the three estimand-A candidates reuse referee_evidence.playbook_occurrence_readiness()'s
existing per_setup_side pooling verbatim; the two at_wall-context candidates (S-4/S-5) reuse the
existing band-context/backing-bucket resolution already imported elsewhere in this era (never a
second pooling implementation). The five candidate definitions themselves are spec Sec7-pinned
module constants (parameters, mirroring test_referee_registry.py's already-established
_starter_family_payloads() shape) -- "no hard-coded hypothesis set" (goal.md J-07 Step 2)
governs the REGISTRATION WRITE PATH staying generic (POST /registry/hypotheses accepts any valid
hypothesis, never only the five shortlist candidates), not the shortlist's own spec-pinned
candidate list (state/assumptions.md iter-8 entry).

2. FIELD ADDITION on the Registry row's existing hypothesis entries (not a new row, not a new
endpoint): discovery: {n: int >= 0, n_sessions: int >= 0, label: "discovery (exploratory)"} --
pre-boundary (session_date <= confirmation_start_boundary) observations in the hypothesis's own
(setup_id, side) cell, reusing the SAME shared pooling primitives _hypothesis_accrual already
uses (never a second pooling implementation), keyed off the ALREADY-immutable
confirmation_start_boundary field (iter-6's RetroactiveBoundary hardening covers this field; the
discovery fold reads it, never re-derives or accepts a client-supplied alternative). Never
contributes to the existing accrual block; a deep-backfilled pre-boundary record recorded after
registration still contributes to discovery, never to accrual (counter-tested). -->

<!-- iter-9 note (J-08): field-level additions/writer completions, all under ALREADY-registered
Data Contract rows -- no new row.

1. "Promotion authorization verdict" row (owner referee_adjudicate.py's authorize_promotion,
built unwired at iter-7; endpoint unchanged: surfaced inside pnl_scan._promote / the scan
report's promotion block) is WIRED for real this iteration. The promotion block gains three
fields alongside its existing candidate_id/promoted/note/enhancement_id: promotion_eligible:
bool, refusal_class: "no_certificate"|"stale"|"wrong_candidate"|"mismatched_datasets"|
"failed_gates"|"malformed_unverifiable"|None, reason: str|None. A non-promoting sweep's report
stays byte-compatible outside these three fields (goal.md J-08 acceptance).

2. Certificate record (shape unchanged from the iter-6 note above -- candidate,
champion_identity_at_scan_time, train_dataset, holdout_dataset, config_fingerprint, gate_version,
referee_parameters_hash, family_id, hypothesis_id, gate_results) gains its first REAL WRITER this
iteration: minted only at a strategy-family hypothesis's attested, gate-passing confirmatory
checkpoint, through the real evaluation rail (never a hand-written or fixture path in production
code). GET /research/desk/referee/registry's certificates array can now be non-empty; stays []
against the operator's real store this era (goal.md: "no strategy certificate can honestly exist
this era").

3. Evaluation record's already-declared evidence_family: "playbook"|"strategy" enum (iter-7 note)
gains a real "strategy" branch for the first time -- pools referee_evidence.strategy_observations()'s
primary/null trade lists by cluster_key = dataset id (never session_date), spec Sec3.7's per-dataset
delta, reusing referee_stats.py's permutation/BH primitives with zero diff to that module. No new
field.

4. shortlist_response() (GET /research/desk/referee/registry/shortlist, endpoint cell registered
at iter-8) gains two new top-level response fields: family_id: str (the existing
REFEREE_STARTER_FAMILY_ID literal, moved backend-side) and family_q: float, 0 < family_q <= 1 (a
new REFEREE_DEFAULT_Q = 0.10 module constant, spec Sec1's own pinned value) -- closes the iter-8
coherence-audit F1 WARN (the value existed only as an unowned apps/frontend/app/desk/page.tsx
literal). apps/frontend/app/desk/page.tsx's registration POST body reads both from the fetched
shortlist response instead of a local literal; no rendered value changes.

5. REFEREE_STARTER_FAMILY_SHORTLIST gains a sixth candidate (same shape as S-1..S-5, no new
field): range_trade:short at_wall, estimand B -- spec Sec7's own "(registered per side)" wording
for S-4, dropped without a recorded reason at iter-8 (state/assumptions.md iter-9 entry). Reuses
_starter_context_readiness verbatim.

6. The "Registry" row's per-hypothesis accrual/discovery blocks (iter-6/iter-8 notes, no new
field): for a B/C hypothesis, both now apply the SAME context_predicate/backing-bucket check
_starter_context_readiness already uses, via one shared helper -- closing the iter-8
evaluator-found gap where a context-based candidate's registered-row numbers (ignoring context)
could disagree with its own shortlist row's live readiness (which already applied it) for the
identical cell. -->

<!-- iter-10 note (J-09): renders three ALREADY-REGISTERED Data Contract rows for the first time
-- no new row, no new field, no owner/endpoint change. "Referee Adjudications" and "Referee Runs"
(the pre-registered J-06 and J-04 IA rows above) go live on /desk, reading
GET /research/desk/referee/adjudications and GET .../nulls/runs + GET .../evaluate/runs (+ their
POST compute/cancel triggers) verbatim -- zero client-side verdict/number derivation. MCP gains
desk_referee -> /research/desk/referee/adjudications and desk_referee_registry ->
/research/desk/referee/registry as two more byte-identical GET-proxy tools (_STATIC_PATHS,
20 -> 22 tools); no selector arguments, matching every other no-required-param tool's shape.

Rider (no Data-Contract shape change): _pool_strategy_trades (referee_adjudicate.py) gains an
optional candidate filter, applied only on the certificate-mint path (certificate_mint
supplied), closing the iter-9-recorded MINOR anti-goal entry (a certificate's declared candidate
was never checked against its pooled evidence's own identity) -- see state/assumptions.md
iter-10 entry. The Certificate record's own field shape (iter-6/iter-9 notes) is unchanged;
still zero certificates on file against the operator's real store. -->

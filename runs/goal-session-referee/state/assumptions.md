# Goal Session referee — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting the goal rather than
just reading evidence. The session owner reads this to veto interpretations early.

## iter-0 — goal-evaluator

**Ambiguity:** J-10 "The kept product stands" is written as a continuous regression sentinel, but
its own acceptance also names era-end conditions — screenshots of the three Referee `/desk`
sections and "MCP = exactly 22 tools". At iteration 0 the kept-product half is fully verified
while those two clauses are structurally unmeetable (zero sections exist; 20 tools are
advertised). The goal text does not say whether the sentinel should be scored on its
kept-product half alone or on its whole acceptance.
**We chose:** Scored J-10 `partial`, not `passing`/`already_passing` — the whole-acceptance
reading — and recorded the verified kept-product evidence in `journey-history.json` so no later
iteration re-does that work. Consequence: a future break of the kept product would be caught as a
frozen-foundations anti-goal violation rather than by the `passing → failing` regression rule, and
J-10 closes only when J-09 lands.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-01's acceptance requires the strategy family to carry "the `basis_caveats`
forming-bar disclosure verbatim", but no verbatim text for it exists in `docs/goal.md` or
`docs/referee-statistical-spec.md` — only a description of what it must disclose. So there was
nothing to compare the served sentence against.
**We chose:** Accepted this iteration's first authoring as satisfying "verbatim" — the exported
constant `REFEREE_FORMING_BAR_BASIS_CAVEAT` (`apps/backend/app/research/referee_evidence.py`),
whose served text names `levels._bars_as_of`, the `epoch <= as_of` admission, and the Card 6.4
deferral (screenshot `reports/qa/goal-referee-iter-1-evidence/UT-J-01-result.png`). It is now the
single source of truth J-06 and J-08 must import rather than re-word. The owner may want to read
that sentence once and edit it now, while only one caller exists.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-02's Steps require the playbook adapter to carry a "completeness predicate
(finest-series reach of the RTH close window)" per record, but J-02's own Acceptance list never
names it — the Acceptance names only the two-family goldens, cache parity, pooling/split,
dedup+coverage disclosure, and the SHA-256 no-write listing. The shipped
`session_completeness` is a best-effort estimate derived from `forward.at_utc +
minutes_to_close` (blind to intra-session bar gaps), has zero test assertions, and is not used
as a gate this iteration.
**We chose:** Scored J-02 `passing` against its written Acceptance list, which is fully met and
which I verified myself, rather than withholding the pass for an unlisted Step sub-clause.
Consequence: an untested, admittedly imprecise completeness estimate now exists in the shared
contract, and J-06's confirmatory eligibility (the exploratory/confirmatory separation, a
critical rail) is the first thing that would lean on it. Recorded as a binding rider on the
next iteration instead of a blocker.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** `docs/referee-statistical-spec.md` §2's pseudocode types
`provenance.detector_basis` as a plain string, but a strategy trade has no detector, so the
field has no meaning for that family. goal.md's own Constraints say a developer who finds the
spec unimplementable "DROPS that procedure from the iteration, records the drop, and surfaces
it for an owner ruling — never improvises" (trap T-1).
**We chose:** Accepted the developer's disclosed improvisation — `detector_basis: None` for
every strategy observation, by analogy with `context_algorithm_version`'s explicit
"None when inapplicable" pattern — rather than treating the T-1 deviation as a failure, because
it was surfaced honestly in the handoff and the reviewer's NOTE, it is reversible, and no
consumer exists yet. The owner should either rule on it or codify the exception in the spec
before J-06 builds logic that assumes the field is always populated.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** `docs/referee-statistical-spec.md` §2 types `provenance.detector_basis` as a plain
string with no explicit ruling for the strategy family (which has no detector at all). Iteration
2 already accepted the developer's `detector_basis: None` improvisation as reversible, and its
own next-step recommendation asked for "an owner ruling ... before J-06 assumes the field is
populated" — but goal mode is headless this iteration and no human ruling is available before
J-03 (this iteration) closes out that carried rider.
**We chose:** Ratify iter-2's already-accepted convention as the standing rule for this era
rather than block on an unavailable human ruling: `detector_basis` stays `None` for every
strategy-family observation (mirroring `context_algorithm_version`'s existing "None when
inapplicable" pattern), formalized by adding ONE clarifying sentence to
`docs/referee-statistical-spec.md` §2 stating this explicitly. Zero `.py` behavior changes — this
is a documentation-only closure of the rider, not a statistical redefinition, so it is not a
"named revision" under the spec's own change-control rule (no constant, weight, eligibility
rule, or test procedure moves).
**Reversible:** yes — a future explicit owner ruling can still override this by editing that one
sentence; if it ever changes the actually-served value (not just its documentation), that edit
becomes a named spec revision per the spec's own rule, re-keying results beside the old ones.

## iter-3 — goal-evaluator

**Ambiguity:** J-03's Acceptance sentence says "the oracle suite is green and IS the acceptance",
and every clause it literally names is met (suite green, mutation fixture fails calibration,
identical seeds reproduce byte-identical p/CI, the attestation round-trips and a corrupted one is
detected, pin unchanged, zero new deps) — all re-verified by me. But I reproduced an
anti-conservative defect in `permutation_test`'s exact-enumeration branch (p below the exact
test's own 2/(N+1) floor on 1.7% of 2v2 fixtures) that the oracle suite structurally cannot see,
because no oracle generator ever enters that branch. The goal text does not say whether "the
oracle suite is green" is the WHOLE test or a proxy for "the statistics are calibrated".
**We chose:** Read the acceptance as a proxy, not as the whole test, and scored J-03 `partial`
rather than `passing` — the journey's own title is "calibrated ... oracle-proven", and the era's
stated purpose is statistics trustworthy enough to disprove the desk's own evidence, which a
p-value below its own mathematical floor defeats. Consequence: J-03 does not close this iteration
even though its written acceptance clauses all pass, and iteration 4 spends a full-depth pass on
a two-line arithmetic fix plus the missing enumeration-branch oracle coverage. If the owner
disagrees and wants the literal reading, J-03 can be marked passing and the fix carried as a
rider into J-04 — but J-06 must not wire the module into real verdict math before it lands.
**Reversible:** yes

## iter-4 — goal-decomposer

**Ambiguity:** Iteration 3's evaluator next-step recommendation names two same-file
reviewer-flagged riders that should "ride along" plus, separately, "a check of two leads in
older unchanged code that I could not settle in this pass" — the evaluator's own report says it
could not settle these, and it is unclear whether "ride along... rather than becoming their own
iteration" was meant to cover investigate-only or investigate-and-fix, and for both leads or just
the two same-file ones.
**We chose:** Investigated both leads to a concrete root cause rather than deferring the
investigation a second time, then split them on their own merits. Lead 1 — a date whose newest
Playbook record sits at a stale `detector_basis` silently contributes zero to J-01's readiness
counts and J-02's observation adapter, with no disclosure of which date or why — is a small,
purely additive fix (a `stale_basis_dates` disclosure, built once and shared by both call sites)
and IS included this iteration. Lead 2 — `_strategy_observation()`'s
`epoch_anchor = dataset.get("epoch_anchor") or 0.0`, which conflates a genuinely-missing/`None`
anchor with an explicitly-present `0.0` one — is DROPPED per this project's own T-1 discipline
("an ambiguous or unimplementable clause is DROPPED and surfaced for an owner ruling, never
improvised"): the identical `or 0.0` pattern is already-shipped, FROZEN behavior in
`edge_report.py:489` (this era must not touch it), and the widely-reused test fixture
`_plant_dataset` deliberately sets `epoch_anchor=0.0` as a real, hand-verified value
(`test_strategy_observations_emits_net_r_with_the_forming_bar_caveat`'s own comment proves the
resulting `"1969-12-31"` `session_date` is an intentional, checked assertion — proof of correct
ET day-boundary conversion — not a bug demonstration). A correct fix must therefore distinguish
"genuinely missing/`None`" from "explicitly `0.0`" (the current truthy `or` cannot), and should
also decide whether `referee_evidence.py`'s convention should match or intentionally diverge from
`edge_report.py`'s own — a project-wide consistency question. That is more than a same-iteration
"small check" belongs in an iteration whose primary job is a critical statistics fix, so it is
recorded here (and in the iteration-4 spec's NOTES, with the full investigation) rather than
improvised.
**Reversible:** yes — Lead 1's disclosure field has no consumer yet and can be renamed or removed
freely before J-09 (its first UI reader); Lead 2 is untouched, unchanged from today's shipped
behavior, so nothing here forecloses any future fix or owner ruling.

## iter-4 — goal-evaluator

**Ambiguity:** J-03's Acceptance is "the oracle suite is green and IS the acceptance", and every
clause it names is now met and independently re-verified by me. But the hard auditor left one
IMPORTANT finding open (B1): `permutation_test` still serves `min_attainable_p = 1/(draws_used+1)`
in exact-enumeration mode, a value the just-fixed method provably can never produce (I measured it
myself: on the iteration-3 repro `p == 2/7` sits exactly ON the floor while `min_attainable_p`
reads `1/7`). `docs/referee-statistical-spec.md:168` says "the minimum attainable p (granularity)"
— "granularity" supports the shipped value, "minimum attainable" supports `2/(draws_used+1)`. The
goal text does not say whether a served disclosure that over-promises reachability blocks a
journey whose written acceptance clauses all pass.
**We chose:** Scored J-03 `passing` and carried B1 as a binding rider on J-04 rather than holding
the journey a second iteration. Reasons: the defect I withheld the pass for last time was the p
that feeds BH contradicting its own formula — this is a secondary disclosure field matching one
defensible reading of the canonical spec, consumed by nothing today; and this project's own T-1
rule says an ambiguous spec clause is surfaced for an owner ruling, never improvised, which is
exactly what the auditor did. Consequence: a served field currently tells a future reader that a
smaller p is reachable than the method can reach, which could let a hypothesis be registered with
a target it can never meet. The fix is one line plus two test assertions if the owner rules for the
"attainable" reading; J-04–J-08 are its first readers, so it must be settled before then.
**Reversible:** yes

## iter-5 — goal-decomposer

**Ambiguity:** `docs/referee-statistical-spec.md:168` says "the minimum attainable p
(granularity) is served beside every p," and `permutation_test`'s exact-enumeration branch
serves `min_attainable_p = 1/(draws_used+1)` — a value the iteration-3/4-fixed method can never
actually produce, since the observed grouping is always one guaranteed member of the enumerated
space and therefore always self-extreme, making the TRUE floor `2/(draws_used+1)` (iteration 4's
own 2,500-case sweep found zero violations, 448 landing exactly on this floor). Iteration 4's own
evaluator carried this as an explicit "OWNER RULING" rider for iteration 5, and goal mode is
headless — no human ruling is available before this iteration builds J-04, the field's first real
consumer-adjacent journey.
**We chose:** Ruled for the field's own literal name — "minimum ATTAINABLE" — over the spec
prose's looser "granularity" gloss: `min_attainable_p` now reads `2.0/(draws_used+1)` in
exact-enumeration mode (unchanged at `1.0/(draws_used+1)` in the seeded/Monte-Carlo branch, which
was already correct). This matches the era's own fail-closed/honesty ethos more directly than the
alternative — a disclosure that overstates reachability could let a future hypothesis register a
target p it can never meet, the same failure shape (silent over-confidence) iteration 3's finding
was about. Verified zero blast radius before ruling: `_ATTESTATION_EXPECTED` pins exactly
`{permutation_p, permutation_enumeration, ci_low, ci_high}` — `min_attainable_p` is not one of
the four attestation-checked fields, so this fix requires no `STATS_CORE_VERSION` bump and no
attestation re-pin. Consequence: the fix is a one-line conditional plus two direct test
assertions, landing inside iteration 5 rather than blocking on an unavailable human.
**Reversible:** yes — zero consumers exist yet (J-04 is the first real journey to touch
`referee_stats.py` again after this field); a future explicit owner ruling can still override
this reading by editing the one conditional line, and per the spec's own change-control rule,
doing so after any real evaluation record exists would be a named revision that re-keys results,
never a silent edit.

## iter-5 — goal-evaluator

**Ambiguity:** J-04's Acceptance opens with "fixture goldens with hand-computed draws (including a
shortfall case, a zero-eligible exclusion, and a remaining-time boundary case at 15:05/1h)". The
three named cases are all met and hand-verified. The leading "hand-computed draws" clause is met
only degenerately: every shipped fixture has `eligible_count <= K (=4)`, so the seeded
Fisher–Yates SELECTION is never discriminated by any test — TC-1 asserts a set that any
permutation (and a broken selector) would also produce. The goal text does not say whether the
draw must be pinned against an independently hand-computed subset or only that the recorded
draw be reproducible.
**We chose:** Scored J-04 `passing` after verifying the selection MYSELF rather than withholding
the pass for the literal clause. My probe (7 eligible, K=4, run against the real module) showed a
genuine non-trivial subset [2,4,5,6], byte-identical reproduction on a second call, the trigger
bar never drawn, and a different subset for a different observation ([2,4,6,7] vs [1,3,5,6]) —
positive evidence that anti-goal 7 (deterministic and seeded) holds in the shipped behaviour.
Consequence: the SHIPPED suite still cannot catch a future regression in the selection step, on a
module whose records are append-only forever; that test gap is carried as a binding rider on the
next iteration rather than as a blocker. If the owner prefers the literal reading, J-04 can be
held until a >K-eligible golden with a pinned expected subset exists.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** J-05's Steps require `GET .../registry` to serve "per-hypothesis accrual
(informative post-boundary sessions vs target)". `docs/referee-statistical-spec.md` §3.1
defines "informative session" precisely as "≥1 eligible occurrence with ≥1 eligible anchor" —
a definition that requires the estimand engine (J-06, not yet built) to pair each occurrence
against real matched-null anchors. Computing that pairing inside the registry now would either
duplicate J-06's not-yet-built statistical logic, or require a null build (an explicit J-04
operator act goal.md says never runs automatically) to already exist for every freshly
registered hypothesis before the registry page could show anything.
**We chose:** Registry accrual is served as an honestly-labeled, cheaper PROXY: the count of
distinct post-boundary `session_date`s carrying ≥1 observation in the hypothesis's own
`(setup_id, side)` cell, reusing `referee_evidence.py`'s existing
`playbook_occurrence_readiness()` per-cell pooling (current `detector_basis`) rather than the
estimand engine's exact eligible-occurrence/eligible-anchor test — matching how J-07's own
Steps already describe shortlist readiness as coming from "the J-01 fold", not a live estimand
run. The response marks this `is_proxy: true` so nothing downstream can mistake it for a
confirmatory-eligible count; J-06's real evaluation-time count (computed against actual null
records, per §3.1) becomes authoritative once J-06 exists and remains the only number that ever
gates a confirmatory evaluation — the registry never computes or serves a verdict.
**Reversible:** yes — the proxy is a read-side display convenience with zero persisted state
and no consumer beyond this GET; J-06 introduces the real count independently, on its own
evaluation records, and nothing here forecloses or contradicts it.

## iter-6 — goal-decomposer

**Ambiguity:** Iteration 5's evaluator next-step recommendation asked to "decide whether
comparison sets [null records] should be filed under a real question id [hypothesis_id] once
questions exist (today they borrow the comparison-rule's own name)". J-05 is the first
iteration where hypothesis_ids actually exist, so the question becomes decidable, but neither
goal.md nor the statistical spec states whether null-record identity or filing should change
once hypotheses exist.
**We chose:** Keep null records keyed exactly as J-04 shipped them —
`(observation_id, null_spec_signature)`, filed by null-spec id — with NO `hypothesis_id` field
added and no re-keying. Null anchors are a shared, hypothesis-independent measurement
(comparable moments for one occurrence under one matched-null rule); multiple hypotheses (e.g.
an Estimand A candidate and a later Estimand C candidate on the same setup/side) can legitimately
reuse the identical null record once built, and filing by hypothesis_id would force needless
rebuilds and contradict the era's own reuse/no-second-implementation discipline. A hypothesis's
evaluation (J-06) looks a null record UP by null-spec id + observation; it never owns or files
one.
**Reversible:** yes — this is a storage/query-key decision, not a statistical redefinition; no
null record has ever been filed any other way, so there is nothing to migrate if a future owner
ruling disagrees.

## iter-6 — developer

**Ambiguity:** The Data-contract note says `null_spec_id: str|None (None for
evidence_family="strategy"...)`, read in isolation this could imply every PLAYBOOK-family
hypothesis (any estimand) requires a non-null `null_spec_id`. But `docs/referee-statistical-
spec.md` §3.2 defines Estimand B as a cell-vs-complement comparison ("do occurrences in context
cell C differ from same-setup occurrences outside C?") with NO null population anywhere in its
definition, and spec §7's own starter-family table names a null for S-1/S-2/S-3 (Estimand A) and
S-5 (Estimand C) but explicitly none for S-4 (Estimand B: "at_wall vs other same-setup
contexts"). The Data Contract's parenthetical only explains the strategy case; it does not claim
to be an exhaustive enumeration of every `None` case.
**We chose:** `null_spec_id` is required-and-validated against the pinned set only for a
playbook-family hypothesis whose estimand is A or C; for Estimand B it is forced to `None`
regardless of what a payload supplies (mirroring how `context_predicate` is already scoped to
B/C only rather than validated uniformly). The substantive estimand definitions (§3.2/§7) are
weighted as more authoritative than a summary parenthetical that was never claiming completeness.
**Reversible:** yes — zero downstream consumer yet (J-06 is the first real reader of this
field); if this reading is wrong, tightening the check to require `null_spec_id` for every
playbook hypothesis regardless of estimand is a one-line change with no stored data to migrate
(no real hypothesis has been registered against the production store this era).

## iter-6 — developer

**Ambiguity:** `docs/referee-statistical-spec.md` §5 states a definitional equality
("confirmation_start_boundary = the ET calendar date of registered_at"), but the iteration's own
TC-4 requires the registration payload to accept an explicit `confirmation_start_boundary`
override field and refuse it when supplied "at or before registered_at's own ET calendar date" —
implying the field is caller-visible at all, which the definitional equality alone would not
require.
**We chose:** the override field exists purely as a defensive/adversarial-input check, never a
real caller-facing feature: a supplied value at-or-before the honest computed one is refused
(`RetroactiveBoundary`, TC-4); a supplied value strictly AFTER the honest one is silently ignored
(the stored value is always exactly the computed one) rather than honored, since spec §5 names no
"delay the boundary" feature anywhere and honoring it would let an operator quietly choose a
later start date than their registration instant actually earned.
**Reversible:** yes — no caller (CLI, POST, or any planned future UI) is documented as ever
needing to set this field in production; it exists in the payload schema for TC-4's own
adversarial-input test to exercise.

## iter-6 — goal-evaluator

**Ambiguity:** This iteration's DEFINITION OF DONE requires "Required-still-passing journeys
(J-01, J-02, J-03, J-04; J-10's kept-product half) remain green — deterministic replay + LLM
fallback", but the browser/replay lane self-skipped wholesale on `Frontend Present: no`
(`status.json` `browser_checks_run: false`; `ui-test-results.md` = SKIPPED), so there is no
results row — not even a `DEFERRED-BUDGET` row — for any of the five. The goal text does not say
whether an un-run required-still-passing lane voids those journeys' recorded status or whether
evidence durability covers it.
**We chose:** Held all five at their recorded statuses (J-01/J-02/J-03 `passing`, J-04
`passing`, J-10 `partial`) under methodology A.6 evidence durability, after proving the code
behind each is unchanged rather than assuming it: zero `apps/frontend/` diff; `referee_routes.py`
at 125 insertions / 0 deletions with `git diff -U0 | grep -c '^-[^-]'` == 0 (no shipped route
body touched); every frozen backend module untouched. J-04 was the one exception — its own
module changed, so I re-verified it directly instead of carrying it. Consequence: J-10's
kept-product browser walk now stands on iteration-5 evidence, and two consecutive skipped
verifications would become a real evidence hole rather than a durability case — recorded as a
binding next-iteration requirement in its journey note and in the next-step recommendation. If
the owner prefers the strict reading, J-01/J-02/J-03/J-10 drop to `unknown` until a replay pass
runs.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** J-05's Acceptance ends "a withdrawal after a post-boundary evaluation exists is
refused **and the hypothesis folds as p=1**". The refusal half is fully testable today and is
met. The "folds as p=1" half is a Benjamini-Hochberg fold behaviour that structurally cannot
exist until J-06 builds the evaluation records and the BH computation — no evaluation store
exists this iteration at all (the withdrawal check takes an injected boolean instead).
**We chose:** Scored J-05 `passing` on the refusal half alone, treating "folds as p=1" as a
forward clause J-06 owns, consistent with the iteration spec's own DEFINITION OF DONE (which
lists only "a withdrawal after a post-boundary evaluation exists is refused") and with the
era's own dependency order (J-05 -> J-06). Consequence: nothing in the shipped code yet proves a
late-withdrawn candidate stays in the BH denominator as p=1 — the era's "Never shrink the BH
denominator" anti-goal is currently protected only structurally (the family's
`candidate_hypothesis_ids` list is frozen at first sighting and membership is checked at
registration). J-06 must carry the p=1 fold as an explicit acceptance item, not inherit it as
already-done.
**Reversible:** yes — no evaluation or BH record exists anywhere yet, so nothing has to be
migrated if the owner prefers J-05 held open until the fold is real.

## iter-7 — goal-decomposer

**Ambiguity:** `docs/referee-statistical-spec.md` §5 lists nine verdict tokens including
`killed` ("a registered kill condition met") but defines no kill-condition mechanism anywhere —
no field on the Hypothesis record, no Step in J-05 or J-06, no trigger rule stated in the spec
or in `docs/goal.md`. It is unclear whether J-06 is expected to invent a minimal kill trigger
(e.g. re-using withdrawal) or leave the token unreachable this era.
**We chose:** Drop `killed` from this iteration's built verdict set entirely — no code path in
`referee_adjudicate.py` computes or returns it. The verdict vocabulary's return type documents
the literal string as a future enum member (so a later, explicitly-specified kill mechanism can
be added without a breaking rename), but nothing this iteration can produce it. This follows
T-1 verbatim ("a developer who finds the spec ambiguous or unimplementable for a procedure DROPS
that procedure ... never improvises") rather than inventing a kill rule the spec never named,
which risked exactly the kind of unreviewed, silently-tuned gate this era's anti-goals forbid
("No gate loosens mid-era... every eligibility rule are fixed at registration").
**Reversible:** yes — zero hypotheses have ever been evaluated against the production store
this era (J-07's real registration act has not yet run), so no recorded snapshot anywhere could
be mis-labeled by this drop; a future owner ruling can add the trigger and the enum value
becomes reachable with no migration of existing records.

## iter-7 — goal-decomposer

**Ambiguity:** J-06's Acceptance requires "an evaluation with a tampered attestation folds to
the refusal state," and spec §5/§6 both describe the fold refusing "confirmatory output" on a
missing/mismatched/version-stale attestation "with honest served copy" — but the verdict
vocabulary enumerated in spec §5 names exactly nine tokens (`exploratory`, `registered`,
`pending_forward_confirmation`, `insufficient_sample`, `fragile`, `no_evidence`, `corroborated`,
`killed`, `basis_retired`) and none of them is named as "the attestation-refusal state." It is
unclear whether the refusal is meant to reuse one of the nine tokens or requires a distinct
representation the spec never named.
**We chose:** Represent attestation refusal as a dedicated `confirmatory_output_refused: bool`
+ `refusal_reason: str|None` pair layered onto the response, which forces the served `verdict`
to the most conservative already-named non-claim token (`insufficient_sample`) rather than
inventing a tenth vocabulary string. This reading treats the nine-token list as the closed,
spec-authoritative verdict enum (consistent with T-2's "vocabulary minefield" discipline of
using named tokens exactly) while still giving J-09's planned "attestation-refusal sentence"
copy a concrete boolean + reason to key its distinct wording off of.
**Reversible:** yes — `confirmatory_output_refused`/`refusal_reason` are new fields with zero
consumers today (J-09 is the first UI reader); if a future owner ruling prefers a distinct
verdict token instead, this is a one-line change to the fold function with no stored data to
migrate, since no real evaluation has ever run against the production store.

## iter-7 — developer

**Ambiguity:** Spec §8 names all six `authorize_promotion` refusal classes (`no_certificate`,
`stale`, `wrong_candidate`, `mismatched_datasets`, `failed_gates`, `malformed_unverifiable`) but
its own prose bundles several under one parenthetical ("stale (ANY pin differs from the live
scan's own report values)"), which reads as if it subsumes `wrong_candidate`/
`mismatched_datasets` too — yet the iteration's own TC-27 requires a `config_fingerprint`
mismatch specifically to fold to `stale` (not `mismatched_datasets`), so the six tokens must
partition somehow, and the spec text alone does not fully disambiguate the boundary.
**We chose:** malformed_unverifiable (the certificate store itself reports an integrity error,
checked first, fail closed) -> no_certificate (zero certificates for this `strategy_id` at all)
-> wrong_candidate (certificates exist for the `strategy_id` but none for the exact `profile`) ->
stale (champion identity, config_fingerprint, gate_version, or referee_parameters_hash differ —
i.e. the world moved since the cert was minted, matching TC-27 literally) -> mismatched_datasets
(train/holdout dataset id/checksum/split differ) -> failed_gates
(`gate_results.bh_pass`/`floors_met` is not exactly `True`) -> otherwise authorized. Chosen to
satisfy TC-26/27/28 literally while giving each of the other three classes ITS OWN
non-overlapping trigger rather than leaving them structurally unreachable.
**Reversible:** yes — `authorize_promotion` is a pure, unwired function this iteration (J-08's job
to call it from `pnl_scan._promote`); the CertificateStore stays empty in production, so no stored
data depends on this exact partition, and only TC-26/27/28 (no_certificate/stale/success) are
DoD-required to be fixture-tested — the remaining four classes carry their own honest reasons and
one fixture test each, but "full fixture coverage rides with J-08" per the iteration spec.

## iter-7 — developer

**Ambiguity:** Spec §5's `fragile` rule says a checkpoint is fragile when BH passes but "any
§3.5/§4.3 sensitivity flips T's sign" — the Data Contract names four discrete fragility-trigger
strings (`by_fail`, `sign_flip`, `entry_basis_sign_flip`, `cluster_ci_includes_zero`), and
`entry_basis_sign_flip`/`cluster_ci_includes_zero` map unambiguously to §4.3/§3.6, but it is not
stated which §3.5 item the bare `"sign_flip"` token names. §3.5 lists the session-level sign-flip
(`sign_flip_result`) FIRST — the token's own name could be misread as naming that function.
**We chose:** `"sign_flip"` = `sign(equal_weight_T) != sign(T)` (the §3.5 item-2 equal-session-
weight sensitivity), NOT `sign_flip_result`'s own output — because `sign_flip_result` computes
the IDENTICAL `T` (`_t_statistic` on the same informative sessions) as the primary permutation
test; only its null distribution differs. Its own `t` field can therefore never differ in sign
from the primary's `T` by construction, so it structurally cannot be the source of a "T sign
flip" trigger — only the equal-weight variant's recomputed `T` can genuinely differ in sign.
**Reversible:** yes — a one-line change inside `_build_and_record_snapshot` if a future spec
revision states the intended mapping explicitly; no confirmatory verdict has ever been computed
against the real production store this era (the starter family is J-07's job), so no stored
snapshot would need migrating.

## iter-7 — developer

**Ambiguity:** Spec §4.3's entry-basis sensitivity is framed entirely around the occurrence-vs-
matched-null comparison ("occurrences enter at detector-decided entry/entry_kind; anchors enter
at bar close... re-measure each occurrence close-anchored... recompute T"), which only makes
literal sense for estimand A/C (which have an anchor to compare a basis against); estimand B (no
null, a cell-vs-complement comparison of two REAL occurrence groups) has no stated entry-basis
treatment at all.
**We chose:** `entry_basis_T`/`entry_basis_sign_flip` are computed for estimand A/C only and are
honestly `None` on every B evaluation record — the same "`None` when structurally inapplicable"
convention `context_algorithm_version`/`detector_basis` already use elsewhere this era, rather
than inventing an unstated B-specific entry-basis treatment (T-1: vagueness is a drop).
**Reversible:** yes — a future spec revision naming a B-specific entry-basis treatment is a
one-line addition to `run_evaluation_and_record`'s estimand branch, and every field involved is
already `None`-typed in the Data Contract for exactly this "not yet computed" case.

## iter-7 — developer

**Ambiguity:** Spec §5's verdict vocabulary lists `exploratory` ("basis not registered") as a
live-fold token alongside `registered`/`pending_forward_confirmation`, and this iteration's own
IN SCOPE bullet includes it in the read-side fold's documented return set — but
`adjudications_response()` folds ONLY hypotheses already present in the registry (every entry is,
by construction, already registered), so no entry it ever serves can honestly be described as
"basis not registered." TC-20 independently confirms the zero-accrual baseline is `"registered"`,
not `"exploratory"`.
**We chose:** Treated `exploratory` as a documented, currently-UNREACHABLE enum member from
`adjudications_response()` — the exact same treatment iteration 7's own `killed` drop already
uses (T-1), rather than inventing a code path (e.g. serving it for some OTHER, non-hypothesis
entity this endpoint does not enumerate) the spec never named for this specific fold.
**Reversible:** yes — no code path anywhere computes or returns `"exploratory"`; if a future
reading finds a genuine referent for it, adding that branch is additive with no migration, since
the token has never appeared in any served response.

## iter-7 — developer

**Ambiguity:** Spec §3.6 states confirmatory fields (`T`/`permutation_p`) are withheld below the
registered floors ("earlier runs record pending accrual states with NO confirmatory p" — T-4's
optional-stopping guard) but does not say whether the DESCRIPTIVE companions
(`ci_occurrence`/`ci_cluster`/`sign_flip_p`/`equal_weight_T`/entry-basis) are ALSO withheld pre-
eligibility, or computed whenever there is pooled data regardless of role.
**We chose:** Gated `T`/`permutation_p`/`permutation_enumeration`/`min_attainable_p` strictly on
`confirmatory_eligible` (`None` otherwise) — the literal T-4 guard. Left the descriptive
companions computed whenever `session_groups`/`occurrence_diffs` is non-empty, REGARDLESS of
eligibility: spec Sec3.5/Sec3.6 states plainly that CIs/sensitivities are "descriptive
companions... NEVER a decision rule" (T-3), so showing them before checkpoint carries none of the
p-value peeking risk T-4 exists to prevent — the verdict-computing BH/fragility machinery only
ever runs at the checkpoint moment (`role == "checkpoint"`), never before, regardless of what the
descriptive fields show.
**Reversible:** yes — a one-line change (gate everything on `confirmatory_eligible` uniformly) if
a future owner ruling disagrees; no evaluation has ever run against the production store this
era, so nothing stored would need migrating.

## iter-7 — goal-evaluator

**Ambiguity:** The era anti-goal "No confirmatory output without a verified oracle attestation"
reads, in its own text, as a rule about the FOLD ("the adjudication fold never serves a
confirmatory verdict from an evaluation whose attestation is missing, mismatched, or
version-stale — it serves the refusal state with its reason"). My probe showed the write side is
not gated at all: with a deliberately broken attestation injected at evaluation time, the run
still recorded `role: "checkpoint"` and appended a permanent snapshot whose stored `verdict` is
`"corroborated"`; only the served fold refuses (`confirmatory_output_refused: true`, verdict
`insufficient_sample`). The goal text does not say whether writing an unattested confirmatory
verdict into an append-only record — never served, never correctable, and consuming the
hypothesis's ONE allowed checkpoint — counts as "confirmatory output".
**We chose:** Read the anti-goal as scoped to SERVED output (its own wording), so this is NOT a
critical violation and the verdict is not REGRESSION; recorded it instead as a named,
must-fix-next weakness on J-06's journey note and as rider 1 of the next-step recommendation.
Consequence: if the owner reads the rail as covering the recorded artifact too, this is a critical
anti-goal breach and iteration 7 should be re-scored REGRESSION.
**Reversible:** yes — no real hypothesis has ever been registered or evaluated against the
production store (the real registry is empty, store-scope guard CLEAN), so nothing recorded
anywhere is affected; gating the checkpoint on `attestation["passed"]` is a small change with no
data to migrate.

## iter-8 — goal-decomposer

**Ambiguity:** J-07 Step 2 says the `/desk` registration flow must have "no special-casing, no
hard-coded hypothesis set anywhere in code," but spec §7 itself is a fixed, five-candidate,
pre-registered shortlist (S-1..S-5, each with a spec-pinned setup/side/estimand/measure/horizon)
that goal.md's own T-1 discipline requires implementing verbatim, never derived dynamically. It
is unclear whether "no hard-coded hypothesis set" forbids the shortlist's five candidate
definitions from existing as code/data constants at all, or governs only the registration WRITE
PATH.
**We chose:** Read it as governing the write path only: `POST /registry/hypotheses` (already
built in J-05) stays fully generic and accepts any valid hypothesis payload, never restricted to
the five shortlist candidates (this iteration's TC-9 tests that directly by registering a
non-shortlist setup/side). The shortlist's five candidate definitions ARE spec-pinned module
constants — parameters, exactly like `REFEREE_MIN_SESSIONS` or the null-spec ids already are —
mirroring the shape `test_referee_registry.py::_starter_family_payloads()` already established.
This follows the Parameters discipline ("every referee constant is a module constant read at
call time") rather than reading "hard-coded" as banning the spec's own pinned list from
appearing in code, which would make spec §7 unimplementable.
**Reversible:** yes — the shortlist fold is a pure read with no persisted output; if a future
owner ruling wants the five candidates sourced from a config file or the registry instead of
module constants, that is a one-line refactor with nothing stored to migrate.

## iter-8 — developer

**Ambiguity:** The plan's own Notes flagged that `accrual_rate_sessions_per_day`'s exact formula
is not pinned anywhere: `docs/referee-statistical-spec.md` §7 lists only static
authoring-time corpus counts (n / sessions) for each candidate, never an accrual-rate
methodology, and no existing helper in `referee_evidence.py`/`referee_registry.py` computes
"sessions per day" for anything. goal.md's own J-07 Step 1 names the concept only in prose:
"informative-session accrual rate (sessions/day over the trailing corpus)".
**We chose:** `accrual_rate_sessions_per_day = candidate.n_sessions / corpus_span_days`, where
`corpus_span_days` is the WHOLE recorded playbook corpus's own calendar-day span (earliest
recorded `session_date` to the latest, inclusive, across every record on file regardless of
setup/side) — one shared denominator computed ONCE per `shortlist_response()` call
(`_corpus_session_span_days`), not per candidate. `projected_days_to_target` is then
`max(0.0, (target_sessions - n_sessions) / accrual_rate)` when the rate is positive, floored at
`0.0` (never negative once a cell already meets or exceeds its own target) and `null` when the
rate is `0` (an empty corpus or a genuinely zero-eligible cell) — TC-2's own divide-by-zero
guard. This reads "over the trailing corpus" as the corpus's own elapsed calendar span (a
literal, defensible reading), not a rolling/windowed rate a future spec revision might define
differently.
**Reversible:** yes — `accrual_rate_sessions_per_day`/`projected_days_to_target` are pure
read-side numbers with zero persisted output (the shortlist writes nothing); if a future owner
ruling prefers a different accrual-rate basis (e.g. a trailing N-day window, or a per-cell rather
than whole-corpus span), that is a self-contained change to `_corpus_session_span_days`/
`shortlist_response()` with nothing stored to migrate.

## iter-8 — developer

**Ambiguity:** The plan's own Notes flagged a second open call: whether the new `discovery` fold
should apply the SAME stale-`detector_basis` exclusion `_hypothesis_accrual` already applies
(T-6: pool only at the current `(detector_basis, config_fingerprint)`), or should count every
pre-boundary record regardless of basis. The blueprint note only says `discovery` reuses "the
SAME shared pooling primitives `_hypothesis_accrual` already uses," which argues for yes, but
does not spell it out letter-by-letter for the stale-basis case specifically.
**We chose:** Yes — `_hypothesis_discovery` applies the IDENTICAL `_is_stale_basis` check
`_hypothesis_accrual` applies, walking the SAME already-scanned `newest_by_date` map with the
filter direction inverted (`session_date <= boundary` kept, instead of `> boundary`).
Consistency with accrual was weighted higher than a looser reading (counting every basis) would
have been, since a stale-basis record's own signals were already excluded from the CURRENT
detector's pooled identity everywhere else this era (J-01's `per_setup_side`, J-06's
eligible-occurrence gather) — letting discovery alone count them would make the SAME record
simultaneously "not current evidence" for accrual purposes and "current evidence" for discovery
purposes, an inconsistency the spec never asks for and T-6 exists specifically to prevent.
**Reversible:** yes — zero consumers beyond this iteration's own UI reader exist yet; a future
owner ruling to include stale-basis records in `discovery` specifically is a one-line change
(drop the `_is_stale_basis` check inside `_hypothesis_discovery` alone) with nothing stored to
migrate, since `discovery` is a pure read-side fold with no persisted record of its own.

## iter-8 — auditor (supersedes the `projected_days_to_target` half of the first iter-8 entry above)

**Ambiguity:** the same one the developer entry above logged — no spec pins
`projected_days_to_target`'s formula. That entry settled the RATE's denominator (whole-corpus
calendar span) and, without flagging it as a second call, also settled the NUMERATOR as
`target_sessions - n_sessions` (days to close the remaining gap), floored at `0.0`.
**We chose (audit correction, finding B2):** `projected_days_to_target = target_sessions /
accrual_rate` — measured from ZERO, never net of the candidate's own historical `n_sessions`.
`target_sessions` is a POST-boundary count everywhere else it is used (`_hypothesis_accrual`'s
`informative_post_boundary_sessions`, `run_evaluation_and_record`'s `confirmatory_eligible`), and
registering stamps the boundary at that instant, so not one historical session can ever count
toward it. Measured against the operator's own corpus on 2026-08-15, the net-of-history reading
served `0.0` — "ready now" — for all three estimand-A candidates (S-1 71 sessions, S-2 44, S-3
105, all at or above the 12-session target) when the honest waits are ~74 / ~119 / ~50 days; it
also counted historical observations as progress toward a confirmatory target, which "the
historical atlas is exploratory forever" forbids. The `None`-on-zero-rate divide-by-zero guard
(TC-2) is unchanged; the `max(0.0, ...)` floor is gone because the corrected value is never
negative.
**Reversible:** yes — still a pure read-side number with zero persisted output; the change is
confined to one expression in `shortlist_response()` plus its own test.

## iter-8 — goal-evaluator

**Ambiguity:** J-07's acceptance says "the shortlist renders with readiness numbers and rationales
(screenshot)" without pinning any value. The iteration's own hard audit then CORRECTED one of those
numbers (`projected_days_to_target`, finding B2) AFTER the browser pass captured it, so the
J-07 screenshots show 517 in the "Projected days" column where the shipped code now serves 564
(I reproduced both on an isolated copy of the rig's 47-day / 1-session corpus). The goal text does
not say whether a screenshot whose numbers the same iteration later changed still evidences the
journey.
**We chose:** Read the acceptance as asserting rendering BEHAVIOR (the five candidates, their
rationales, and live readiness columns render; the registration writes; the discovery label shows)
— all of which the screenshots still evidence, and none of which the B2 fix touches — and treated
the stale column as a capture defect (methodology A.7): J-07 scores `passing` with
`evidence_makeup: true`, so a re-capture rides the next iteration as a passenger task rather than
becoming its goal. Consequence if the owner disagrees: J-07 would be `unknown` until re-captured,
and no iteration could be scored GOAL_ACHIEVED before that re-capture.
**Reversible:** yes — J-09 rebuilds and re-renders the same `/desk` section, so a fresh capture
lands there anyway and clears the flag whatever it shows.

## iter-8 — goal-evaluator

**Ambiguity:** The era's critical anti-goal "The historical atlas is exploratory forever. No
historical observation is ever served, labeled, or counted as forward confirmation" does not say
whether a SERVED PROJECTION that arithmetically subtracts pre-boundary historical sessions from a
post-boundary target counts as "counting a historical observation as forward confirmation". The
shipped-then-fixed `projected_days_to_target` did exactly that, and its output ("0 days — ready
now") is what an operator would have read when choosing which question to register.
**We chose:** Scored it MINOR, not critical — so the verdict is CONTINUE, not REGRESSION — because
it was found and fixed INSIDE the same iteration by that iteration's own audit lane, the value is a
pure read-side projection with zero persisted output, no recorded number ever counted it toward
confirmation, and it never reached the operator's real screen (the only capture of it is the QA
rig's screenshot). Recorded in `journey-history.json`'s `anti_goal_violations` as a resolved minor
entry so the trail is not lost.
**Reversible:** yes — nothing is stored; if the owner reads the rail as covering served projections
too, the entry's severity is a one-word edit and the fix is already shipped either way.

## iter-9 — goal-decomposer

**Ambiguity:** Iteration 8's evaluator next-step recommendation asked to "get an owner ruling
on the missing short side of the wall-based candidate" — spec §7's own table row for S-4 reads
`range_trade (registered per side) at_wall vs other same-setup contexts`, but only the long-side
candidate (`range_trade:long at_wall`, estimand B) exists in `REFEREE_STARTER_FAMILY_SHORTLIST`;
the short side was silently dropped in iteration 8 with no recorded reason. It is unclear whether
"get an owner ruling" means this genuinely needs a human decision, or whether the spec text
already settles it.
**We chose:** Read spec §7's "(registered per side)" as a plain, unambiguous instruction rather
than a values judgment requiring a human — S-4 is the only shortlist row carrying that qualifier,
and its own corpus-count column already anticipates both populations ("subset of 469+459 / ~80").
This iteration therefore scopes ADDING the missing `range_trade:short at_wall` candidate as a
sixth `REFEREE_STARTER_FAMILY_SHORTLIST` module constant (reusing `_starter_context_readiness`
verbatim), rather than escalating for a human ruling or leaving the drop unrecorded a second time.
**Reversible:** yes — the shortlist fold is a pure read with no persisted output; the new
candidate is only ever SELECTABLE, never auto-registered, so nothing is written until an operator
explicitly approves it through the real registration act. If a future owner ruling disagrees,
removing the sixth module-constant entry is a one-line change with nothing stored to migrate.

## iter-9 — developer

**Ambiguity:** J-08 Step 1 (spec §3.7) asks for a "strategy-family evaluation branch" reusing
`run_evaluation_and_record`'s existing role/attestation/snapshot machinery, and blueprint.md's
iter-9 note says this needs "No new field" on the evaluation record. But the SAME hypothesis
record schema `_REQUIRED_HYPOTHESIS_FIELDS` enforces uniformly across both evidence families
still requires `setup_id`/`side` — fields with no natural strategy-family meaning (spec §3.7's own
pooling is "cluster = dataset", never setup/side-filtered) — and nowhere does the spec or the
iteration's Data-contract additions name a field carrying WHICH `(strategy_id, profile)` candidate
a strategy-family hypothesis is about, or which live `pnl_scan` train/holdout pins a certificate
minted from it should pin.
**We chose:** (1) `_pool_strategy_trades` pools EVERY recorded candidate/null trade across the
WHOLE `JournalStore`, grouped by `cluster_key` = dataset id, with zero filtering by the
hypothesis's own `setup_id`/`side` — those two fields stay schema-required but functionally
vestigial for this branch (a test/registration payload may supply any schema-valid placeholder).
(2) The certificate mint call site (`_mint_strategy_certificate`, reached only from
`run_evaluation_and_record`'s own fresh-checkpoint path) takes `candidate`/
`champion_identity_at_scan_time`/`train_dataset`/`holdout_dataset` as an EXPLICIT, caller-supplied
`certificate_mint` dict rather than deriving them from the hypothesis record — the caller (the one
entity that actually knows which live `pnl_scan` scan this certificate authorizes) supplies them;
omitting `certificate_mint` (every route/CLI caller today) mints nothing, matching goal.md's own
"no strategy certificate can honestly exist this era". Both choices keep the hypothesis record and
the evaluation record byte-shape-identical to the playbook family's (blueprint.md's own "no new
field"), at the cost of `setup_id`/`side` not doing real work for this one evidence family.
**Reversible:** yes — no real strategy-family hypothesis is registered against the operator's
store this era (Out of Scope: fixture-only); if a future era needs a real per-candidate identity
on the hypothesis record, adding one is an additive field with nothing stored to migrate.

## iter-9 — developer

**Ambiguity:** TC-10 says "the recorded verdict is `insufficient_sample`" for the strategy-family
branch at today's real (tiny) corpus, but the full `insufficient_sample` VERDICT vocabulary token
is only ever produced by `adjudications_response()`'s fold (`_snapshot_fold`'s attestation-refusal
branch, or `_fold_one_hypothesis`'s snapshot-integrity-failure branch) — never by the live
(pre-checkpoint) fold, which only ever reads `"registered"`/`"pending_forward_confirmation"`. With
so few registered datasets, a strategy-family hypothesis's `role` stays `"pending"` forever (never
reaches `"checkpoint"`), so it never produces a snapshot and never reaches EITHER of those two
existing `insufficient_sample`-producing branches either.
**We chose:** Read "the recorded verdict is insufficient_sample" as referring to the evaluation
RECORD's own `ci_cluster` field, which already carries the literal `INSUFFICIENT_SAMPLE`
("insufficient_sample") sentinel string whenever `bootstrap_ci_cluster` sees fewer than
`REFEREE_MIN_CLUSTERS_FOR_CI` (8) informative clusters (this branch's dataset clusters, exactly as
today's real corpus produces) — rather than adding a NEW strategy-family-specific branch to
`_live_fold`/`adjudications_response` that would report a bespoke "insufficient_sample" verdict
for a pre-checkpoint strategy hypothesis (a change to the READ-side fold that is not itself named
anywhere in this iteration's IN SCOPE list, and that would need its own new interpretation of what
"forward confirmation" honestly means for a family whose informative unit does not accrue with
wall-clock time the way Playbook sessions do). `test_referee_adjudicate.py`'s
`test_tc10_todays_real_corpus_shape_serves_insufficient_sample_with_caveats_and_null_disclosure`
asserts this literal field, not a full adjudications-fold verdict token.
**Reversible:** yes — a future era wiring `adjudications_response()`/`_live_fold` for a genuine,
registered strategy-family hypothesis (out of scope this era) can add that branch without
touching anything built this iteration; nothing here would need to move.

## iter-9 — goal-evaluator

**Ambiguity:** The critical anti-goal "Promotion is certificate-locked. No champion promotion
without a valid **candidate-specific** Referee certificate" does not say whether "candidate-specific"
constrains only the certificate's recorded `candidate` pin (which `authorize_promotion` does compare
exactly) or also the EVIDENCE the certificate's statistics were computed from. This iteration's mint
satisfies the first reading and not the second: `_pool_strategy_trades`/`strategy_observations` pool
every recorded backtest trade unfiltered by `strategy_id`/`profile`, and the `candidate` dict is
supplied by the mint's caller and never cross-checked against the pooled evidence's own identity.
I reproduced this: 12 planted `v1/default` backtests minted an attested, gate-passing certificate
naming `totally-unrelated-strategy/totally-unrelated-profile`, and `authorize_promotion` then
returned `authorized: True` for that unrelated candidate.
**We chose:** Scored it a MINOR, still-OPEN anti-goal entry (so the verdict is ESCALATE, not
REGRESSION) rather than critical, because it is unreachable by any operator action this era —
neither production call site of `run_evaluation_and_record` (`referee_adjudicate.py:1512`, the
compute manager; `:1854`, the CLI) supplies `journal_store` or `certificate_mint`, the operator's
real registry directory does not exist on disk, zero certificates are on file, and therefore every
live promotion today is refused with `no_certificate` — exactly what goal.md itself declares. It is
left `resolved: false` so it must be closed before any future era wires the mint into the
`/evaluate` route. Consequence if the owner reads "candidate-specific" the stricter way today: this
becomes a critical violation and the verdict would be REGRESSION with a halt.
**Reversible:** yes — nothing is stored and no certificate exists; closing it is either scoping the
strategy pool to the certificate's own `(strategy_id, profile)` plus a cross-check at the mint, or a
one-line owner ruling recorded here that a caller-declared pin suffices while the mint stays
route-unreachable.

## iter-9 — goal-evaluator

**Ambiguity:** goal.md J-08 says its acceptance is "*(Keyless; automated.)*", and the browser lane
recorded `UT-J-08 … SKIP — no browser action exists to execute`. Trap T-10 says "No screenshot ⇒
`unknown`, never `passing`", which read literally would make every keyless journey unscorable.
**We chose:** Read T-10 as governing BROWSER acceptances only (its own next clause, "backend-only
proof never satisfies a browser acceptance", says so), so J-08 — which goal.md itself scopes as
having no browser step — is scored from its pytest acceptance plus my own direct verification
(signature probe, single-call-site greps, source-scan replication, and a live real-rail mint/tamper
probe), not marked `unknown` for lacking a screenshot it was never supposed to have.
**Reversible:** yes — J-09 renders the Referee panels and J-10's browser walk covers the kept
product; if the owner wants a browser artifact for the promotion refusal, it would have to become a
new rendered surface, which this era's own OUT OF SCOPE explicitly defers.

## iter-10 — goal-decomposer

**Ambiguity:** Iteration 9's evaluator next-step recommendation offered two ways to close the
still-open MINOR anti-goal entry (a strategy-family certificate's declared `candidate` is never
checked against the identity of the evidence it was minted from — iter-9's own reproduced
exploit): "make the certificate's evidence actually belong to the strategy it names, or get an
owner ruling that a caller-declared name is enough while the minting path stays unreachable."
Neither `docs/referee-statistical-spec.md` §3.7 nor §8 states whether the dataset-clustered
pooling itself must be scoped to the certificate's named `(strategy_id, profile)`, or only that
the certificate's own recorded fields must be internally consistent.
**We chose:** the code fix, not an owner-ruling closure. `_pool_strategy_trades` gains an
optional `candidate: {"strategy_id": str, "profile": str} | None` filter, matched against the
SAME `strategy_id`/`profile` fields `backtests.py`'s result block already stamps on every
journal record (no new field, no second identity join); `run_evaluation_and_record` passes
`certificate_mint["candidate"]` through it ONLY on the path that could ever mint a certificate
(`certificate_mint` supplied — still zero production callers this era). `certificate_mint=None`
(every existing route/CLI caller, and every monitoring/non-mint evaluation) keeps pooling
whole-corpus and unfiltered, byte-identical to today's shipped behavior, so the already-passing
iter-9 TC-10 real-corpus `insufficient_sample` reading is untouched. This was weighted over the
owner-ruling option because the anti-goal is critical, the exploit is fully reproduced against
the real rail (not merely theoretical), the fix reuses already-stamped fields with zero
schema/store change, and this iteration already carries full-depth budget the prior evaluator
explicitly earmarked for exactly this closure.
**Reversible:** yes — `_pool_strategy_trades`'s new parameter defaults to `None` (today's exact
behavior); reverting to the caller-declared-name-suffices reading is deleting the one new
call-site argument, with nothing stored to migrate since zero certificates exist on file either
way.

## iter-10 — developer

**Ambiguity:** goal.md J-09 Step 1 / the phase spec's "New information displayed" list both name
"seed identity" as a Referee Adjudications provenance line to render per entry, beside
`evaluation_basis` hash, null/test-spec ids, and attestation pass/fail. But no served field
anywhere carries a raw seed VALUE: `REFEREE_SEED` (271828) is a single GLOBAL module constant,
never persisted per-hypothesis or per-evaluation, and `referee_parameters()`/
`referee_stats_parameters()` (the only functions that surface it as JSON) are not wired to any
route this era. The spec's own pinned seed recipe is
`f"{REFEREE_SEED}:{hypothesis_id}:{purpose}[:{session_date}[:{i}]]"` — the only PER-HYPOTHESIS
component of that recipe is `hypothesis_id` itself.
**We chose:** render "seed identity" as the entry's own `hypothesis_id` (already served per-entry
on the adjudications response, already displayed as the row's primary key) rather than fabricate,
hardcode, or newly-serve the raw `REFEREE_SEED` constant. Hardcoding `271828` client-side would
create a second, unverified copy of a backend constant with no test tying the two together
(a single-source-of-truth risk); adding a new served field for it would be a Data Contract
addition this iteration's own goal.md scope explicitly rules out ("Data-contract additions: None").
Re-displaying `hypothesis_id` under an explicit "seed identity" label is zero-cost, zero-new-
computation, and technically accurate — it IS the per-hypothesis identity that seeds that
hypothesis's own reproducible draw stream.
**Reversible:** yes — if a future era serves `referee_parameters()` (or a per-record seed
derivative) on a route, the Adjudications provenance line can read that field directly instead,
with no store migration needed (nothing is persisted from this rendering choice).

**Ambiguity:** the Referee Adjudications entry needs its own hypothesis's `null_spec_id`/
`test_spec_id` for its provenance line, but `adjudications_response()`'s own per-entry shape
(`{hypothesis_id, verdict, confirmatory_output_refused, refusal_reason, snapshot, live_coverage}`)
does not carry them — those fields live only on the RAW hypothesis record served by
`GET /research/desk/referee/registry`, a sibling endpoint. Also unclear: should "Referee Runs"'
trigger controls assume "Referee Registry" was already expanded (and its data already fetched)
before either new section is opened?
**We chose:** both new sections issue their OWN `fetchRefereeRegistry()` call on first expand (in
addition to their own primary read), writing into the SAME shared `refereeRegistryResult` state
the existing Referee Registry section already owns — rather than coupling to whether that section
happens to have been expanded first, or threading a prop down from it. This is an extra,
harmless, side-effect-free GET (T-8: GETs never compute) against an already-shipped endpoint, not
a new computation or a second implementation of anything `referee_registry.py` already owns; it
makes both new sections correct regardless of click order, matching how every other `/desk`
section already owns its own deferred fetch independently.
**Reversible:** yes — trivial to remove the redundant fetch call from either section if a future
iteration wants strict fetch-count minimization instead; no stored state depends on it.

**Note (not an ambiguity, a scope call under Auto Mode):** the phase spec's QA fixture-setup
bullet (seed a `fragile` hypothesis and a refused-attestation hypothesis on the fixture-scoped
rig) is left to the browser-qa-agent's own preparatory step, following the iter-9 precedent (the
developer does live-server verification of already-shipped read paths, not browser-fixture
construction for an upcoming QA pass). The dev handoff documents the exact mechanics (which unit
tests demonstrate the identical construction) so QA does not have to reverse-engineer them.

## iter-10 — goal-evaluator

**Ambiguity:** goal.md J-09's acceptance names three screenshots, one of them "an in-flight second
evaluation trigger is refused single-flight (screenshot)", and the era's own T-10 rail says "no
screenshot ⇒ `unknown`, never `passing`". That clause's artifact does not exist: UT-09 cites an
image byte-identical to UT-07's and UT-10's (md5 `d3065788c71ecfcc5623b7704ad6de73`) showing no
refusal, because the shipped UI disables the trigger on click so a second request is never
dispatched. The framework's own methodology (A.7) says the opposite for this shape: an evidence gap
on a feature whose behaviour is confirmed rides `evidence_makeup` and must never block.
**We chose:** scored J-09 `passing` with `evidence_makeup: true` and the gap recorded as
`capture-defect`, reading T-10's "none ⇒ unknown" as governing a journey with NO browser evidence
(J-09 has five screenshots I opened myself covering its other clauses) rather than a single
unphotographed clause whose behaviour is proven three independent ways: TC-32
(`tests/test_referee_adjudicate.py:1744`, second trigger → `started False`, same compute id),
QA's 5-concurrent-POST probe (exactly one `started: true`, no duplicate ledger row), and the UI's
own reachable refusal path (`page.tsx:8547/8606` set `triggerError`; `:5170/:5280` render it with
their own testids). The make-up capture is named as the next round's work.
**Reversible:** yes — the flag stays set until a fresh capture lands; if the owner reads T-10
clause-by-clause, J-09 drops to `partial` with the identical next step and nothing stored changes.

## iter-10 — goal-evaluator

**Ambiguity:** J-10 Step 2 asks the kept-product browser walk to cover "EVERY shipped `/desk`
section (screen history, forward returns, refresh chain, briefing, skipped,
runs/pins/compare/provenance, ...)", and Step 3 asks for "kept-route byte-identity vs a baseline
captured from the era-open commit". Neither is literally producible as written: the browser lane
runs against the fixture-scoped rig, whose store has no computed desk screen, so the
screen-dependent panels (Screen History, Forward Returns, Briefing, Skipped Members, Screen
Comparison, Provenance — `page.tsx:6485-6558`) render the shipped "Desk screen not computed yet."
state instead of populated tables; and no era-6 iteration ever captured a kept-route response
baseline artifact (only Era B's `reports/goal-desk-iter-8-kept-route-baseline.md` exists).
**We chose:** scored J-10 `passing`, reading "renders exactly as shipped" as satisfied for the rig's
own data state (the not-computed panel IS the shipped behaviour for an empty screen store, and the
rig is the era-long precedent), and reading Step 3's byte-identity as satisfied by something
stronger than a response baseline: SOURCE-level identity of every kept route handler. I ran the
era-cumulative product diff myself (`git diff --stat e875972` over `apps/backend/app`,
`apps/frontend/app`, `apps/frontend/lib`): 12 files, 8,641 insertions, 6 deletions, and the only
non-new-referee files touched in the entire era are `main.py` (+7 route registration),
`mcp/__init__.py` (20→22, named exemption a), `pnl_scan.py` (the J-08 interlock, exemption c) and
the `/desk` page + api/types (exemption d) — zero diff to levels/tradability/setups/desk_forward/
desk_playbook*/backtests/store/engine.
**Reversible:** yes — if the owner wants the enumerated panels photographed with data, a screen can
be computed on the fixture rig (an operator act the rig permits) and the walk repeated; nothing is
stored either way.

## iter-11 — goal-decomposer

**Ambiguity:** Iteration 10's evaluator next-step recommendation names three required actions for
"one short verification round with no new building": (1) re-check the seven skipped journeys via
their own backend acceptance tests, (2) capture J-09's owed single-flight-refusal screenshot, and
(3) "fix the walk-through recorder, whose script still contains an action type ('scroll') the
player does not understand." The evaluator's own binding depth recommendation for this iteration
is `evidence`, which structurally skips developer/reviewer — so item (3), a code fix, cannot
execute at that depth — and the goal-decomposer's own rule 7 exception for writing
`Depth: evidence` requires the next-step to ask ONLY for evidence on already-passing journeys.
**We chose:** Read the recorder fix as OUT OF this iteration's scope rather than as grounds to
deviate from the binding `evidence` depth recommendation. Two reasons: first,
`incredible_auto_dev/scripts/automation/lib/demo_runner.py` (`_VALID_ACTIONS = {"goto", "click",
"fill", "expect", "wait_for"}` — confirmed by reading the source; "scroll" is not a member) is
vendored FRAMEWORK tooling that authors this project's demo-narrator script, not Tapeology product
code — the same category of item the desk session's own `goal-desk-iter-25.md` spec named
explicitly "out of a goal-decomposer's remit" (`closure_gate.py`'s substring guard, `goal_gate.py`'s
regex miss). Second, a sibling goal session's own recorded lesson (`goal-playbook-iter-12.md`
BACKGROUND, citing that session's `lessons.md` iter-11) states plainly: "A `Depth: evidence`
micro-path silently deletes planned code work... Never plan code work under it." Planning the
recorder fix as an IN SCOPE item here would either silently vanish (if the engine actually
dispatches evidence-only) or force the engine's arbiter to demote/reject the whole spec. It rides
in NOTES/OUT OF SCOPE for a human or a future framework-maintenance pass instead.
**Reversible:** yes — nothing here is a product commitment; a future iteration (or a
framework-maintenance session outside goal-mode) can fix `demo_runner.py`'s action vocabulary (or
change what the demo-narrator emits) independent of any Tapeology store/schema, and re-recording
the walkthrough costs nothing stored today.

## iter-11 — goal-evaluator

**Ambiguity:** goal.md J-09's third acceptance screenshot is worded "an in-flight second
**evaluation** trigger is refused single-flight (screenshot)". The artifact captured this round is
the in-flight second **null-build** trigger being refused (`page.tsx:8545-8547`,
`data-testid="referee-null-build-trigger-error-referee-null-tod-v1"`), not the evaluate trigger
(`page.tsx:8604-8606`, "Refused — an evaluation is already running for this hypothesis."). Both live
in the same Referee Runs panel, both are set ONLY from a server response carrying `started: false`,
and both are literally the same code shape; iteration 10's evaluator and this iteration's spec
(TC-8) both defined the owed capture as the null-build variant.
**We chose:** read "evaluation trigger" as "a Referee Runs compute trigger" and accept the
null-build refusal capture as satisfying the clause — so J-09 stays `passing` with
`evidence_makeup` CLEARED. Weighted by: the clause's substance is that a single-flight refusal
reaches the screen with honest copy, which the picture proves for real (I read the exact sentence at
3x zoom beside a live 57/126 progress); the evaluate-side refusal is covered by its own unit test
(TC-32, `tests/test_referee_adjudicate.py:1744`) and its own reachable render path; and the era's
own rule that an evidence gap on confirmed behaviour never blocks (methodology A.7).
**Reversible:** yes — if the owner reads the clause strictly, the remedy is one more capture of the
evaluate-side refusal on the fixture rig (a hypothesis is already registered there, S-1); nothing
stored anywhere depends on this reading.

## iter-12 — goal-decomposer

**Ambiguity:** goal.md J-11 Step 2 adds two new per-candidate API fields beside the shipped pair
(rate `accrual_rate_sessions_per_day` + projection `projected_days_to_target`) —
`informative_sessions_per_pooled_session` (the new rate) and `projected_pooled_sessions_to_target`
(the new projection) — but Step 4 asks the Referee Registry section to render "one descriptive
basis line... and one new right-aligned column beside the shipped 'Projected days' column"
(singular "column"), while the shipped table already renders BOTH members of its own rate/
projection pair as separate columns ("Accrual / day" and "Projected days"). It is unclear whether
the new pair should mirror that shape with two new columns, or whether Step 4's literal
"one... column" governs.

**We chose:** Render exactly ONE new table column this iteration —
`projected_pooled_sessions_to_target`, placed immediately beside "Projected days" — matching Step
4's literal singular wording. `informative_sessions_per_pooled_session` is served on the API
response (Step 2's own field, exercised by its own backend test) but gets no dedicated table
column this iteration; it is the rate the new column's projection is derived from, available to
any client (a future UI pass, or reading the endpoint directly) without forcing a second new
column onto an already-dense ten-column table. Weighted over "mirror the shipped pair with two
columns" because Step 4 names the rendered surface precisely and separately from Step 2's API
field list, and the house style favors density over completeness-for-its-own-sake — a second
column the acceptance text does not ask for adds T-11 replay-script/testid surface for no
acceptance-required benefit.

**Reversible:** yes — `informative_sessions_per_pooled_session` is already served; exposing it in
its own column later is a pure frontend addition (new testid, no backend change, no stored data
migrated).

## iter-12 — goal-evaluator

**Ambiguity:** J-11's acceptance names a `[NEW]`-flagged demo-narrator walkthrough as part of
its own acceptance text, and the era's T-10 rail is strict about evidence honesty. No
walkthrough was produced: no demo step runs at lean depth, and the shared recorder
(`incredible_auto_dev/scripts/automation/lib/demo_runner.py`) still cannot play a `scroll`
action, which is why iteration 11's demo run recorded zero steps (`reports/phase-
goal-referee-iter-11-demo-results.md`, verdict NOT_YET).
**We chose:** scored J-11 `passing` with `evidence_makeup: true` and the gap recorded as
`capture-defect`, reading methodology A.7 ("the walkthrough recording is missing" is named
verbatim there) as governing, and T-10's "no screenshot ⇒ unknown" as governing the SCREENSHOT
rail, which J-11 satisfies (a fresh whole-page capture I opened and re-derived by hand). The
behaviour behind the clause is proven three ways: the screenshot, the six new backend tests in
my own junit run, and the golden replay script written this iteration. The make-up recording is
named as a human/finalization item, never as a new build round.
**Reversible:** yes — the flag stays set until a fresh capture lands; if the owner reads J-11's
acceptance clause-by-clause, J-11 drops to `partial` with the identical next step (fix the
shared recorder, then record), and nothing stored changes either way.

**Ambiguity:** the iteration's own TC-14 requires "each screenshot's checksum differs from
every other screenshot taken this iteration", but `UT-J-05-result.png` and
`UT-J-11-result.png` are byte-identical (md5 `ca3f6bfea412f5302b9de640d8194abe`) — one
whole-page capture cited for both journeys. Iteration 10 had a genuine defect of exactly this
shape (a shared file that showed none of the claimed refusal).
**We chose:** accepted the shared file rather than scoring either journey down, because I
opened it and confirmed it carries BOTH acceptance states on one page — the registered S-1 row
with its 2026-08-15 boundary, origin, status and accrual (J-05) AND the new basis line plus the
new "Projected sessions" column with the shipped pair unchanged beside it (J-11). Read TC-14's
checksum clause as a proxy for "no acceptance is hidden behind a reused image", which direct
inspection satisfies more strongly than a hash comparison would.
**Reversible:** yes — a second capture cropped to either journey costs nothing and changes no
recorded status; nothing stored depends on this reading.

## iter-13 — goal-decomposer

**Ambiguity:** the dispatch prompt's binding depth recommendation for this iteration is
`evidence` (computed by iteration 12's evaluator, when all eleven journeys were already
passing and the only owed item was a walkthrough recording) — but the goal-proposer appended
a brand-new Must-have journey, J-12, into goal.md's `AUTO:journeys` block AFTER that
recommendation was frozen. J-12 requires real, never-before-built frontend code (a new
`fetchRefereeEvidence()`, new response types, two new rendered blocks, a widened arithmetic
guard, a new unowned-frontend-literal guard, a new golden replay script) — work an
`evidence`-depth round structurally cannot perform (it dispatches capture + evaluation only,
skipping developer/reviewer), and my own agent instructions' rule 7 bars planning an
evidence-only iteration for anything but already-passing journeys.

**We chose:** depth `lean`, not `evidence`. J-12 fails the one narrow exception that would
keep `evidence` (a next-step asking ONLY for evidence on already-PASSING journeys — J-12 is
new, unbuilt, not passing), and it fails all four `full`-trigger escape conditions too: it is
frontend-only with an explicit "ZERO backend product diff" clause in its own goal.md text
(fails both the data-model-migration trigger and the brand-new-full-stack-journey trigger,
which needs backend AND frontend work with real Data-Contract additions — J-12 explicitly adds
none), it touches one page's one existing section through the SAME established
fetch-and-render pattern J-05/J-07/J-11 already used at lean depth (fails the
structural/cross-cutting trigger), the prior verdict was `GOAL_ACHIEVED` not `ESCALATE` (fails
the ESCALATE trigger), and only 2 of the hardening cadence's 6 consecutive lean iterations have
elapsed (cadence not due). J-11 — the most recent sibling journey, an equally-shaped "extend an
already-registered endpoint's reader inside the same Referee Registry section" change — shipped
successfully at lean depth in iteration 12, reinforcing that lean is proportionate here too.

**Reversible:** yes — if the engine's own arbiter or a human reviewer judges differently, the
spec's BACKGROUND section states the reasoning plainly and nothing stored depends on the depth
label; a future iteration can re-run any skipped pipeline step (planner, functional test plan,
audit) against the same diff with no rework of the diff itself.

## iter-13 — goal-evaluator

**Ambiguity:** goal.md J-12's browser acceptance asks that "the Referee Registry section renders
both blocks with every value matching that backend's own served
`/research/desk/referee/evidence` body exactly ... (screenshots; no screenshot ⇒ `unknown`, never
`passing`)", and names the strategy family's `tick_gate_statement` and every `basis_caveats`
entry by name. Both of this iteration's captures (`J-12-seeded-rig-result.png`,
`J-12-empty-corpus-result.png`) are truncated at the capture tool's 4,320px viewport-height cap
while `/desk`'s own `scrollHeight` is ~8,443px, so the Strategy Family block's heading and its
three counts are photographed but its tick-gate sentence and the Card-6.4 forming-bar caveat —
the journey's headline disclosure — fall just below the bottom edge of both images.

**We chose:** scored J-12 `passing` with `evidence_makeup: true` and the gap recorded as
`capture-defect`, reading T-10's "no screenshot ⇒ unknown" as governing a journey with NO browser
evidence (J-12 has two distinct, genuinely different captures I opened myself, covering the
seeded-rig and empty-corpus states and the whole Playbook Family block) rather than a single
unphotographed clause whose behaviour is confirmed four independent ways: the render path read
straight from source (`page.tsx:5166-5179` — `{evidence.strategy_trade.tick_gate_statement}` and
a verbatim `basis_caveats.map`, zero client-side arithmetic); the new unowned-frontend-literal
guard (`tests/test_referee_evidence.py`) proving neither string exists in ANY frontend source
file, so it can only reach the DOM from the payload — run inside my own junit; two independent
same-window DOM-vs-`curl` string comparisons (dev's against the real corpus, QA's against the
fixture rig, the latter noting the `&lt;=`/`&gt;=` entity decoding the real server-side caveat
string does contain, which I printed myself); and the Strategy Family block visibly rendering
in-frame with its three counts. Methodology A.7 names "badly cropped" capture as the archetype of
a defect that must never block. The make-up capture is named as the next round's work, never as a
new build round.
**Reversible:** yes — the flag stays set until a fresh capture lands; if the owner reads J-12's
acceptance clause-by-clause, J-12 drops to `partial` with the identical next step (photograph the
`referee-evidence-strategy-block` element, or collapse the sections above it first) and nothing
stored changes either way.

**Ambiguity (second, same shape as iter-12's):** the iteration's own TC-13 asks for a capture of
the seeded rig, and TC-9 for a separate empty-corpus capture; `J-05-result.png` and
`J-12-seeded-rig-result.png` are byte-identical (md5 `87a696a747360d42a49a29e4bb65d934`) — one
whole-page capture cited for two journeys.
**We chose:** accepted the shared file rather than scoring either journey down, because I opened
it and confirmed it carries BOTH acceptance states on one page — the registered S-1 row with its
`historical-exploration` origin and 2026-08-15 boundary (J-05) AND the whole Evidence Readiness
heading plus Playbook Family block (J-12). The two J-12 captures themselves are genuinely
different files, which is what TC-9's "not reused from TC-1..TC-7's rig" actually asks for.
**Reversible:** yes — a second capture cropped to either journey costs nothing and changes no
recorded status.

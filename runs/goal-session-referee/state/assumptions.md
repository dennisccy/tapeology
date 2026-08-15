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

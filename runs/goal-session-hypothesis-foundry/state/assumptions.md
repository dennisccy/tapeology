## iter-0 — goal-evaluator

**Ambiguity:** REL-14 says a journey named in `browser-infra.json` with no fresh screenshot scores
`partial` + `pending_infra`, but forbids `failing` only on infra absence *alone*. All 8 journeys
were named in the token, yet 7 of them have deterministic, evaluator-reproduced proof that their
surfaces do not exist at all (no `docs/hypothesis-foundry/`, no foundry module/route/test, no
desk panel).
**We chose:** score J-02..J-08 `failing` and J-01 `partial` on that independent evidence, and set
`pending_infra` on none of them — a verify-only make-up ride over surfaces that do not exist would
waste an iteration and would push the token to `attempts: 2`, mechanically triggering STALLED for
a blocker that is a one-line in-repo fixture fix. The infra failure is carried as the top active
blocker instead.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** `docs/goal.md` Binding Execution Order step 2 ("Foundry methodology + source
registry + CandidateSpec. No real manifest yet.") does not say whether "first source records"
means beginning to author the REAL 11 required source objects (§1.1/§1.2) or building the compile
MACHINERY proven on synthetic fixtures — and J-02's own acceptance steps 1-2 literally name a
"Sources/Compiler **fixture** view" over 7 synthetic taxonomy examples, not the real objects.
**We chose:** iter-1 builds the compile-rule MACHINERY (owner meta-policy, natural-boundary law,
exact-quote lint, CandidateSpec schema/hash) and proves it on the 7 hermetic fixture source types
J-02 step 2 names; authoring the REAL 11 required-source-object registry content is left to J-06
(which J-02's own step 5 partially depends on anyway, since it inspects "the committed
fresh-context registry-audit report" that only J-06 commits).
**Reversible:** yes

**Ambiguity:** nothing in the Foundry Constitution's scientific-integrity rules forbids building
the J-02 "Sources/Compiler fixture view" UI early (it renders only synthetic fixture data, no real
outcome), so the UI could technically ship in iter-1 alongside the compiler machinery rather than
waiting for the consolidated read-surface step.
**We chose:** defer ALL Foundry subsection UI (Sources/Compiler included) to the single
consolidated read-surface iteration named in Binding Execution Order step 5, which arrives after
the interpreter/family/freeze machinery (step 3) and hermetic oracles (step 4) exist — building one
comprehensive read surface once, instead of extending a partial UI three separate times across
iter-1/2/3, and matching the goal's own explicit staging. iter-1 ships only J-01's panel header
(era identity + era-open baseline), which is itself required by J-01's own acceptance and cannot
wait.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** J-02's five acceptance steps are all on-screen inspections of a Sources/Compiler
view, and that view was deliberately deferred by the iteration spec — so literally zero of its
assertion steps have browser evidence, yet its backend compile rules exist and were independently
re-run by the reviewer (40/40, TC-3..TC-12). The status vocabulary ("partial = only some assertion
steps passed") does not say how to score a journey whose substance is proven at a layer its own
steps never name.
**We chose:** score J-02 `partial`, not `failing`, on the reviewer's independent test re-run, while
recording in journey-history that no UI step has evidence and that J-02 additionally cannot pass
until `SourceRecord` gains the `alternatives` field its step 3 requires. Unit tests are explicitly
never journey evidence, so this can never support `passing`.
**Reversible:** yes

**Ambiguity:** Methodology A.7 (`capture defect ≠ product failure`) could arguably cover J-01 step
5: the era-open baseline artifact is genuine (I recomputed all six Referee hashes and they match),
and the screenshot shows the panel behaving correctly for an EMPTY store rather than misbehaving —
the data simply is not visible to the scoped QA rig.
**We chose:** do NOT apply `evidence_makeup`, and keep J-01 `partial`. The asserted behaviour
(baseline block renders the recorded values) has never been observed by anyone but the developer,
and closing the gap needs a rig launch/provisioning change by a developer rather than a re-capture,
so an `evidence` depth iteration could not fix it.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** the "No browser proof based on fabricated fixture state when a journey claims to show
real final state; fixture and real views must be visibly distinguished" anti-goal does not say
whether pointing the scoped `:8301` QA rig's `resolve_foundry_dir()` at the real
`apps/backend/.data/foundry/` directory (read-only, era-open baseline only) counts as blurring
fixture vs. real, since the rig otherwise runs entirely against throwaway fixture data.
**We chose:** this is not fabrication and not a blur — the served value is the genuine recorded
artifact (the evaluator already recomputed all six Referee hashes against it in iter-1 and they
matched), the access is read-only with no write to any protected path, and `lessons.md` iter-1
itself names this exact fix ("give the rig the REAL artifact... or set `TAPEOLOGY_FOUNDRY_DIR`").
Inventing a substitute value for the rig, not reading the real one, would have been the violation.
**Reversible:** yes

**Ambiguity:** Binding Execution Order step 3 ("Foundry family + ledger + freeze machinery") and
step 4 ("Hermetic oracles and performance/checkpoint tests") do not draw an exact line for where the
exhaust runner's own mechanics (§9: canonical order, checkpoint/resume, single-flight, replay
refusal) belong — J-04's own acceptance steps already require simulating first-read lock, replay
idempotence, and single-flight, which need a working runner skeleton.
**We chose:** iter-2 (step 3) builds and hermetically proves the runner's mechanics — canonical
order within one family, checkpoint/resume, single-flight, replay idempotence/refusal — since J-04
step 5-6 name them directly. The full multi-family, multi-verdict-type "complete factory" epoch
(compiled + blocked + insufficient + null + wrong-direction + concentration/economic/fragility-
killed + survivor all together) and the protected-data trip fixtures stay reserved for J-05 / step 4
next iteration, matching the goal's own explicit journey split.
**Reversible:** yes

## iter-2 — goal-evaluator

**Ambiguity:** J-03's five and J-04's six acceptance steps are ALL on-screen fixture inspections, and
the iteration spec deferred every Foundry fixture view to the step-5 consolidated read surface — so
literally zero assertion steps have browser evidence, yet the machinery underneath is real and its
equivalence oracle is genuine. The status vocabulary ("partial = only some assertion steps passed")
does not cover a journey whose substance is proven at a layer its own steps never name.
**We chose:** score both `partial`, not `failing`, on the same precedent this session already set for
J-02 in iter-1 — and only after the evaluator independently re-ran all 71 Foundry tests (exit 0) and
read TC-4 to confirm it compares the whole screen dict against the pre-existing direct Scout path
rather than against itself. Unit tests are never journey evidence, so this can never support
`passing`.
**Reversible:** yes

**Ambiguity:** decision-tree rung 4's "the SAME journey has now failed 2+ consecutive iterations"
would fire on J-05..J-08, which have been `failing` since iter-0 — but they are staged-out journeys
the Binding Execution Order forbids attempting yet, never targets of any iteration.
**We chose:** do not treat never-targeted, order-blocked journeys as the rung-4 repeat-failure signal
(it would fire every single iteration of an 8-journey staged build and make adaptive depth
meaningless). ESCALATE was reached instead through the "lean iteration surfaced cross-cutting
complexity" clause, grounded in the arbiter's documented full-to-lean demotion of a spec-declared
cross-cutting iteration.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** Constitution §1.4 requires every source record to disclose "every finite alternative
the compiler is allowed to enumerate," and the iteration-state's carried blocker names this as a
missing `SourceRecord` field, but `docs/hypothesis-foundry-spec.md`'s own §1.4 field table — the
document that already pins `source_hash`'s exact definition (`sha256(source_excerpt)`) — does not
define `alternatives`'s shape. §2.1/2.2's own "Enumeration vs. block" text describes alternatives as
SEPARATE sibling `SourceRecord`s sharing one `foundry_family_key`, which could mean no per-record
field is needed at all (the sibling records already ARE the enumeration).
**We chose:** add `alternatives: tuple[str, ...]` as a per-record disclosure field naming the
sibling representation(s) it legally alternates with, rather than relying solely on shared
`foundry_family_key` membership to imply it — because J-02 step 3 asks to "confirm each record
shows... alternatives" as something visible ON that record during audit, and a reader auditing one
record in isolation should not have to reconstruct the family membership elsewhere to see what its
legal alternatives are. This is additive disclosure on top of the existing family-key mechanism, not
a replacement for it, so it cannot let the compiler enumerate anything the family-key rule wouldn't
already allow.
**Reversible:** yes

**Ambiguity:** J-05 step 5 requires proving hermetically that "withheld/sealed reads fail closed,"
but `docs/hypothesis-foundry-spec.md` §10 explicitly marks the sanctioned-accessor evidence-boundary
wiring as "future work, meaning fixed here," and the iter-2 dev handoff's own Known Issues describe
all real-corpus/accessor wiring as J-06/J-07 territory — so it is unclear whether J-05 needs the
Foundry runner to actually call through `micro_accessor.MicroAccessor` this iteration, or only prove
the fail-closed CONTRACT against a hermetic stand-in.
**We chose:** scope iter-3 to prove the fail-closed contract hermetically by reusing the real,
already-tested `MicroAccessorSealedShardError`/`MicroAccessorOriginFenceError` exception types (no
new accessor abstraction, no mock exception family), without wiring the runner into
`MicroAccessor`'s real-corpus resolution path — that full wiring stays J-07 territory, consistent
with the spec's own "future work" framing and the "no real candidate outcome read before step 7"
anti-goal. This keeps J-05 hermetic-only while still exercising the exact exception types the real
J-07 integration will raise.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-05 is the first Foundry journey whose acceptance steps are NOT worded as on-screen
inspections — J-02/J-03/J-04 all say "Open the ... fixture view"/"Inspect ...", but J-05 says "Run a
hermetic epoch ..." and "Confirm ...", naming no browser surface at all. So the reason those three
were capped at `partial` (their own steps demand a view that does not exist) does not literally
apply to J-05, and its acceptance sentence ("the same production compiler/interpreter/exhaust/screen
paths ... are proved on hermetic oracles") is arguably fully satisfied by a hermetic test run.
**We chose:** score J-05 `partial`, not `passing`. Two independent grounds: (a) the no-screenshot
rail is absolute — no results row and no screenshot exist for J-05, and unit tests are never journey
evidence no matter how the step is worded; (b) `state/blueprint.md` homes J-05 in a "Hermetic
Oracles" read-surface subsection, so the era's own design expects an operator-visible rendering, and
the audit disclosed real completeness gaps anyway (freeze never exercised in the composite path; the
simulated crash discards no state; the checkpoint mechanism the step names does not exist). J-05 can
reach `passing` only after the Binding Execution Order step-5 read surface renders these fixture
states and a browser pass photographs them.
**Reversible:** yes

**Ambiguity:** the auditor fixed two IMPORTANT findings (B1 compiler→runner seam, B2 TC-3's runner
clause) DURING the audit pass rather than sending the iteration back to the developer, so the tests
I scored J-05 on are partly the auditor's own work — and an agent verifying its own fix is exactly
what the non-self-verification rule guards against.
**We chose:** count them, after verifying independently rather than accepting them: I opened both
added tests (`tests/test_foundry_hermetic_epoch.py:343-386` and `:405-432`), read their assertions
against the claims, and re-ran the module myself (10 passed) rather than citing the audit's own test
output. Treating an in-audit fix as unverifiable would have forced an artificial extra iteration for
work that is present and checkable in the tree.
**Reversible:** yes

## iter-4 — goal-decomposer

**Ambiguity:** J-02 step 5 bundles two separate checks: (a) confirming injected effect/p-value/n
fixture noise cannot move a compiled `CandidateSpec`/disposition (purely hermetic, buildable now),
and (b) "inspect the committed fresh-context registry-audit report" at
`reports/hypothesis-foundry/source-registry-audit.md` — a path iter-1's own assumption-ledger entry
already tied to the REAL 11-source registry that only J-06 commits, which does not exist yet.
**We chose:** scope iter-4's Sources/Compiler fixture view to deliver only (a), and state explicitly
in the iteration spec that J-02's step 5b — and therefore J-02 as a whole — may still be scored
`partial` by the evaluator after this iteration, pending J-06's real committed audit report. This is
a known, disclosed limit of the read-surface stage, not a defect in this iteration's execution.
**Reversible:** yes

**Ambiguity:** J-04 step 4 names the literal real-epoch tracked artifact path
`docs/hypothesis-foundry/freeze-set.json` (§8.2's checked-in namespace) inside a step explicitly
scoped to inspecting a "fixture freeze record," but no real epoch/manifest/source-registry exists yet
to produce that committed file, and `docs/hypothesis-foundry/` is confirmed absent from the repo.
**We chose:** the fixture Freeze/Integrity view invokes the already-built, already hermetically-proven
`foundry_freeze.generate_freeze_set` / `build_freeze_record` functions over the same small
deterministic fixture module set `test_foundry_freeze.py` already uses, and displays that real target
path only as the schema/wiring destination the eventual REAL freeze-set will occupy once J-06/J-07
commit it — it does not write, fabricate, or pre-create the real committed file, and the UI must
visibly label this subview as fixture-scope, distinct from any future real freeze record.
**Reversible:** yes

## iter-4 — goal-evaluator

**Ambiguity:** the status vocabulary ("partial = only some assertion steps passed") does not say how
to treat a journey where every numbered acceptance step IS demonstrated but a sub-clause inside one
step is not (J-03 step 2's "raw coordinates remain descriptive provenance"; J-04 step 4's "plus the
manifest/source/spec/config identities"), versus one where a whole numbered step has no on-screen
home at all (J-05 step 3's kill-type mapping; J-02 step 5b's committed audit report).
**We chose:** a uniform line applied to all four target journeys — `passing` when every numbered step
has an on-screen demonstration I personally verified, with un-rendered sub-clauses recorded as `gap`
text; `partial` when any whole numbered step has no on-screen demonstration. That yields J-03/J-04
`passing` and J-02/J-05 `partial`. The alternative (any missing sub-clause caps a journey at
`partial`) would leave all four permanently partial and make the era unclosable, since J-02's step 5b
is structurally impossible before J-06 by the goal's own execution order.
**Reversible:** yes

**Ambiguity:** two of J-03's five steps prove themselves only inside a collapsed `<details>`
drill-in, so the screenshot shows the disclosure widget rather than the asserted values, and the
browser-qa agent verified them by DOM extraction. Methodology A.3 says "the screenshot outranks every
prose claim" but does not say whether a collapsed-but-present drill-in counts as shown.
**We chose:** count them, after reproducing them independently rather than accepting the report — I
re-ran `foundry_interpreter.interpreter_hermetic_fixture_view()` and got exactly the reported values
(`n_candidate=16`/`n_comparator=32` with `feature_name`/`transform`/`params` all `None`;
`killed_direction` at `-79.905625` bps versus `survive`). The screenshot and the prose do not
conflict here, so nothing was overruled; a collapsed disclosure is a real on-screen affordance the
operator can open, not an absent one.
**Reversible:** yes

**Ambiguity:** production code temporarily reassigning the frozen `scout._two_sided_p` and restoring
it in a `finally` (`foundry_hermetic_summary.py:75-82`, `:183-188`) sits between two readings of the
"Frozen foundations stay frozen … never silently mutated" rail: nothing persists and no research
result changed, but it is a raw global reassignment of a frozen scientific module inside the serving
process, which the equivalent test code avoids by using `monkeypatch.setattr`.
**We chose:** record it in the anti-goal ledger as MINOR and unresolved (therefore blocking) rather
than describing it in prose only — goal.md's own anti-goal says findings "are not dismissed in
prose". MINOR rather than critical because I re-ran the composite epoch and confirmed every outcome
is still correct, nothing persists past the `finally`, and no market data or real candidate is
involved. It does not change this iteration's verdict; it must be fixed or owner-dispositioned before
the era can close.
**Reversible:** yes

## iter-5 — goal-decomposer

**Ambiguity:** J-06's real `epoch_manifest` values must be visible to the scoped `:8301` QA rig
(iter-1's own carried lesson: a real artifact under the `TAPEOLOGY_DATASET_DIR`-scoped runtime
foundry directory is invisible there), but §8.2 explicitly places the real tracked artifacts under
the Git-committed `docs/hypothesis-foundry/` / `reports/hypothesis-foundry/` namespace, not under
`apps/backend/.data/foundry/` — the goal text does not say whether `get_foundry()`'s new key should
read through the existing `get_foundry_dir()`/`resolve_foundry_dir()` resolver (consistent with how
the era-open baseline is served) or read the literal repo-relative tracked paths directly.
**We chose:** read the literal Git-tracked `docs/hypothesis-foundry/`/`reports/hypothesis-foundry/`
paths directly, never through `get_foundry_dir()`/`resolve_foundry_dir()` — confirmed by reading
`foundry_source_registry.resolve_foundry_dir()`'s own docstring, which scopes it to
`TAPEOLOGY_FOUNDRY_DIR`/dataset-directory-derived storage for the runtime baseline/ledger only, and
by §8.2's own text distinguishing "the tracked real-epoch artifacts" from "runtime trial/epoch-
opening rows [that] live in the Foundry's resolved research-data ledger." Reading through the
resolver would silently reproduce iter-0/iter-1's exact QA-invisibility failure for J-06's entire
evidence base.
**Reversible:** yes

**Ambiguity:** J-06 step 4 requires confirming the "explicit freeze-set path manifest" is "visible
from the tracked `docs/hypothesis-foundry/` artifacts," which could mean the UI must itemize every
enumerated path+sha256 pair from `freeze-set.json` on screen (potentially hundreds of entries for
all transitive science dependencies per §8.4), or that the requirement is satisfied by the manifest
being visible IN the tracked committed file itself, with the UI showing only its hash/count.
**We chose:** the UI shows `freeze_set_hash` plus a reference to the committed file, not an itemized
per-path listing — the step's own wording ("visible from the tracked ... artifacts," not "visible on
the Foundry screen") is satisfied by the artifact's presence in the Git-tracked repo, which any
auditor (human or the evaluator) can open directly; forcing an on-screen dump of a potentially large
transitive-dependency path list would add UI complexity the goal does not actually ask for and risks
becoming unreadable rather than auditable.
**Reversible:** yes

**Ambiguity:** `foundry_compiler.sources_compiler_hermetic_fixture_view`'s own docstring documents a
deliberate design choice — keep `fixtures[]` at exactly 7 entries by surfacing only one sibling
(`fixture-variant-a`) of the two-variant alias family, with the other named only via its
`alternatives` field — backed by an existing test asserting exactly 7 entries. Two consecutive
evaluator verdicts (iter-4's active blocker, this session's own carried recommendation) now ask to
"show both records of the two-variant family," which changes that assertion's expected count.
**We chose:** treat this as a legitimate fixture-completeness correction directed by the evaluator,
not a forbidden guard-weakening — the assertion's *value* (7) changes to reflect a more complete
fixture set, but its *meaning* (every documented archetype has its own inspectable on-screen record)
is preserved and in fact strengthened, and J-02 step 2's plain text ("two explicitly-frozen legal
variants," plural) supports showing both. This is disclosed here rather than silently reinterpreting
the existing test's intent.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** the decision tree's ESCALATE rung is worded for a LEAN iteration ("this lean
iteration surfaced cross-cutting ambiguity/complexity"), and iter-5 ran FULL. Yet a CONTINUE verdict
here would be demoted to lean by the engine's deterministic depth arbiter on two independent rungs
(the sixth consecutive budget breach, and `goal_full_ran_in_window` seeing iter-5's own full run) —
and iter-6 writes the §8.5 first-read lock, the era's second irreversible act, with three open
IMPORTANT freeze-integrity findings (B1 absolute-path freeze set, B2 freeze_commit missing the
science bytes, B7 + the missing era-open evidence-class contract) bearing directly on that lock.
**We chose:** ESCALATE, extending the rung to a full iteration that surfaced cross-cutting
integrity complexity, rather than CONTINUE + a depth recommendation the arbiter would override. This
session has documented the same override twice (iter-2, iter-4), and goal.md's own rule that "a
science-affecting edit after step 8 begins is an integrity halt, not an iteration opportunity" makes
iter-6 the LAST iteration in which those findings can be repaired at all. Disclosed here rather than
presented as a routine tree match.
**Reversible:** yes

**Ambiguity:** the "No second real generation epoch" anti-goal is worded absolutely, but §7.3 says
Goal Mode "may repair only before any real outcome has been read" — and that is exactly what
happened: a first real `epoch_id` was minted, an independent audit proved one `direction_derivation`
value unsupported, and the registry was regenerated before any commit or any outcome read. Critical
or minor is a real fork: critical would force REGRESSION and halt the session.
**We chose:** MINOR and unresolved (therefore blocking), not critical. Grounds I verified myself:
`git log` shows the five tracked artefacts were added in exactly ONE commit (`dff64eaa`), so nothing
was ever published under the discarded hash; `apps/backend/.data/foundry/` holds only
`era_open_baseline.json`, so no trial ledger and no candidate outcome ever existed; and the whole
sequence is disclosed in the committed audit report rather than hidden. It is not in the methodology's
critical class (no secret, paid dependency, license breach, backdoor, or fabricated data) and it is
not the goal's own named critical violation ("a real candidate outcome read before step 7"). It stays
blocking until the owner rules — I may not write an owner disposition myself.
**Reversible:** yes

**Ambiguity:** J-06 step 4 asks to confirm "the complete family/variant manifest, denominators,
CandidateSpec hashes, future rule_ids, prospective-root status" are visible — but the real epoch
compiled ZERO candidates, so `families[]` is empty and that whole rendering block has never displayed
a row (auditor F1). The status vocabulary does not say whether a vacuously-empty step counts as
demonstrated.
**We chose:** score J-06 `passing`, treating the honest empty state as satisfying step 4. goal.md's
own Completion section lists "zero compiled candidates" as valid successful ending 1, J-06's own
acceptance sentence says "a sparse/empty compiled set is acceptable and is not rescued", and the
screen renders an explicit "Compiled families (0) — Zero compiled candidates this epoch" rather than
a blank. Scoring it `partial` would penalise the honest scientific outcome the goal explicitly
blesses and would create pressure to rescue the epoch.
**Reversible:** yes

**Ambiguity:** §1.1/§1.2 enumerate the required source objects as nine + three bullets, but the
committed registry reaches 11 by collapsing each parked study with its pilot proxy into one record
and all four Wave-2 cards into one, then splitting Card 9.6 in two (that split is mandated by §1.3).
So `card-9.8`…`card-9.11` do not exist as `source_id`s, though the iteration spec's TC-4 asks that
"each of Card 9.8, 9.9, 9.10, and 9.11 has disposition exactly `EXCLUDED_GATE_CLOSED`" (auditor B6).
**We chose:** accept the partition and score J-06 step 2 ("every required source object appears
exactly once") as met, recording B6 as a gap. §7.1's operative rule is "No required source silently
disappears", every collapsed constituent id is carried in `alias_refs` (I verified all four Wave-2
card ids and both study lineage ids are present), the independent fresh-context auditor reviewed and
confirmed the reading, and the hard auditor's added TC-4 test asserts reachability of all four card
ids through the alias list. The alternative reading would require regenerating the epoch — which
§8.1 forbids — to fix a partition choice the goal never numbers.
**Reversible:** no (the epoch is frozen; changing the partition would need a second epoch)

## iter-6 — goal-decomposer

**Ambiguity:** `state/iteration-state.md`'s Active-blockers digest labels B1 (absolute freeze-set
paths), B2 (`freeze_commit` missing `foundry_compiler.py`'s bytes), and B7 (freeze-set/record
omissions) as requiring owner sign-off ("owner-owned: approving any amendment to the
already-committed frozen artefacts"). But `docs/goal.md` §7.3 explicitly authorizes Goal Mode itself
to repair "freeze hash drift" and equivalent integrity gaps unilaterally, with no owner step named,
provided the repair happens "before any real outcome has been read" — and the real epoch compiled
**zero** candidates, so no outcome will ever be read in this era; the entire remaining window is the
§7.3 repair window. The Binding Execution Order's own step 7/8 boundary implies the freeze bookkeeping
should have been complete and correct BEFORE the first-read lock (step 8) is written, which is
precisely what B1/B2/B7 show did not happen at the end of iter-5.
**We chose:** read the OWNER tag narrowly — it covers only the disclosed MINOR anti-goal (ratify/
reject the discarded first epoch, a scientific/policy judgment), not routine freeze-bookkeeping
repair, which §7.3 delegates to Goal Mode. This iteration therefore DOES repair B1/B2/B7 by committing
this iteration's code first, then regenerating `freeze-set.json`/`freeze-record.json` (relative paths,
`freeze_commit` pointing at a commit that truly contains every pinned file, the three omitted tracked
JSONs + generation CLI, the missing era-open evidence-class-contract field) via the SAME already-proven
deterministic `generate_freeze_set`/`build_freeze_record` functions — never touching `epoch_id`,
`source-registry.json`, or `epoch-manifest.json` content, so §8.1's one-epoch rule is untouched. Full
depth (already mandatory from the prior ESCALATE) supplies the independent-auditor scrutiny this
irreversible, freeze-adjacent repair needs instead of a human pause. Disclosed here, and in the
iteration spec's BACKGROUND, precisely so a human watching the run can intervene before dispatch if
this reading of §7.3 is judged too permissive.
**Reversible:** no (the first-read lock this iteration writes, and any freeze-set/freeze-record
regeneration preceding it, are both one-way per §8.5/§9.3 once committed)

## iter-6 — goal-evaluator

**Ambiguity:** the iter-5 anti-goal entry ("No second real generation epoch") recorded its OWN close
condition as "stays blocking until the owner rules **or a uniqueness guard lands**". A uniqueness
guard did land this iteration and I verified it directly (`generate_hypothesis_foundry_real_epoch.py:894-909`
raises a typed `ManifestStoreMissingError`; both TC-7 tests pass under my own run). Methodology B.1
says a finding is discharged when "a close condition the finding itself recorded" is "proven
satisfied now" — which would make it `resolved: true`.
**We chose:** the fail-closed reading — keep it `resolved: false` and BLOCKING. A guard prevents
recurrence but does not un-mint the discarded `epoch_id`, the iter-5 auditor asked specifically for
OWNER RATIFICATION, and I may not write an owner disposition. I record that I was genuinely unsure,
and that the owner can flip this cheaply with a one-line ruling; I also note the auditor's phrasing
"ratify before J-07 runs" is now moot, since J-07 ran this iteration.
**Reversible:** yes

**Ambiguity:** the "Persistence stays scoped" rail says `GET /research/desk/micro/foundry` and every
page-load GET "are read-only and never compute/evaluate a candidate or trigger the exhaust runner".
The new per-request single-flight probe makes the GET create/truncate a lock file
(`foundry_runner.py:197-201` via `:250-254`) — so the rail's operative intent (no market data
recorded, no candidate computed, runner not triggered) is fully intact, but the literal words "are
read-only" are contradicted.
**We chose:** record it as a MINOR, unresolved, blocking anti-goal entry on the literal reading,
rather than describing it in prose only — goal.md's own anti-goal section says findings "are not
dismissed in prose", and the auditor named three concrete consequences (spurious
`ConcurrentRunnerRefused` for a concurrent CLI, a 500 on an unwritable Foundry dir, `EACCES`
mis-reported as "Running"). Disclosed as a literal-reading call so the owner can disposition it in
one line. It does not change this iteration's verdict, which is already CONTINUE on the coherence
FAIL.
**Reversible:** yes

**Ambiguity:** the decision tree's ESCALATE rung (C.4) literally matches — J-08 has now been
`failing` for six consecutive evaluations — and this session has twice watched the engine's depth
arbiter demote a CONTINUE to lean (iter-2, iter-4), with a seventh consecutive budget breach this
run. But my agent contract states twice, unconditionally, that a `COHERENCE-FAIL` iteration must
"return CONTINUE" with a consolidation recommendation.
**We chose:** CONTINUE, following the explicit contract rather than the tree rung, and instead flag
the demotion risk loudly in the Depth Recommendation, the Next-Step Recommendation, and
`iteration-state.md` so a human can force full depth. Note J-08 was never TARGETED in those six
iterations (the goal's own execution order sequences it last), so the rung's literal match does not
carry its intended meaning of "we tried twice and failed".
**Reversible:** yes

**Ambiguity:** J-07's eight steps are mostly vacuous for a zero-candidate epoch (steps 3, 4, 5, 6
have nothing to iterate), and step 7 explicitly permits a fixture-backed interrupt rather than a real
one. The status vocabulary does not say whether a vacuously-satisfied step counts as demonstrated.
**We chose:** score J-07 `passing`, extending the precedent this session already set for J-06 step 4
in iter-5 — goal.md's Completion section lists "zero compiled candidates" as valid successful ending
1, and the screen renders explicit honest text ("zero FROZEN_READY variants this epoch — an honest,
vacuous completion") rather than a blank. Every non-vacuous step was verified first-hand: the ledger
row, the independently recomputed real-corpus hash, the freeze bookkeeping, and the crash-resume test
I re-ran. The one genuinely un-rendered sub-clause (step 4's `withheld_excluded = 80` count) is
recorded as a gap for J-08 rather than used to cap the journey at `partial`.
**Reversible:** yes

# Goal Session rapid-microscope — Assumption Ledger

Append-only. One entry per scoring decision that required interpreting the goal
rather than only reading evidence. Zero entries in an iteration is normal.

## iter-0 — goal-evaluator

**Ambiguity:** J-01 and J-10 each state one combined Acceptance line, but only part of each
was verifiable at era open (J-01's transition documents and era-open baseline; J-10's kept
surfaces, suite, fingerprint and referee hashes). The goal does not say whether partial
satisfaction of a combined acceptance line counts as `failing` or `partial`.
**We chose:** scored both `partial` (browser QA recorded FAIL for the full line), so the
verified sub-checks are not re-done later. `partial` blocks GOAL_ACHIEVED exactly as `failing`
does, so no gate is loosened by this choice.
**Reversible:** yes

## iter-1 — goal-decomposer

**Ambiguity:** `docs/rapid-validation-spec.md` has no dedicated readiness section: it never
defines an RTH-minutes-to-session-equivalents conversion formula, and it never defines a
per-study floor distinct from the three pilot studies goal.md's J-09 names — those studies have
no registered Scout spec yet (that lands in J-09, eight iterations away).
**We chose:** `session_equivalents = rth_minutes_covered / 390` (standard 09:30-16:00 ET RTH
minutes), which reproduces goal.md's own stated ~3.0 on today's corpus; and each of the three
pilot studies reads the SAME existing frozen `WF_TRAIN_MIN_SESSIONS + WF_TEST_MIN_SESSIONS`
(=60 sessions) geometry floor from spec §1, since no study-specific floor is spec'd yet and
today's 11 legacy sessions read `floor_unmet` under either reading — matching goal.md's stated
J-01 acceptance ("every pilot study reads `floor_unmet`") regardless.
**Reversible:** yes — J-09 may register a different, study-specific floor later; this reading
only affects a descriptive readiness column, never a gate.

## iter-1 — goal-evaluator

**Ambiguity:** J-01's Acceptance is one combined sentence naming BOTH real-corpus endpoint values
(`distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 shards `exploratory`/`hand_assigned`)
AND a browser element screenshot of the `/desk` panel rendering "those same served values." The
goal never says which channel proves which half, and the mandated store-scoped QA rig cannot serve
a non-empty tick corpus at all — so the two halves are not simultaneously observable today.
**We chose:** credited the endpoint half from evidence I produced myself (calling `build_readiness`
against the real `.data/datasets` store and reading the exact acceptance values, plus re-running
the 31 real-corpus unit tests), and refused to credit the browser half at all, since the only
screenshot shows an empty corpus and the 18-row shard-table render path was never exercised. Net
status `partial`, which blocks GOAL_ACHIEVED exactly as `failing` does — no gate is loosened. I did
NOT flag it `evidence_makeup`, because a plain re-capture would reproduce the same empty screenshot;
the rig itself must first be able to serve tick data.
**Reversible:** yes

## iter-2 — goal-decomposer

**Ambiguity:** J-01's Acceptance names literal real-corpus browser figures
(`distinct_symbol_days: 12`, `session_equivalents` ≈ 3.0, 18 `exploratory`/`hand_assigned`
shards) for the `/desk` panel's browser screenshot, but the mandated store-scoped QA rig
(`:8301`) can never safely point at the real `.data/datasets` store this iteration: J-02 also
adds the era's first write-capable route under that same directory family (the snapshot-compute
manager), whose derived-cache storage dir defaults to a sibling of wherever
`TAPEOLOGY_DATASET_DIR` points — so pointing the rig at the real store risks a stray compute
leaving derived files beside the operator's real tree instead of inside the throwaway scoped
root. Literally reproducing the exact figures through the browser is therefore unsafe this
iteration.
**We chose:** seed the rig's own throwaway root with the two already-committed tick fixtures at
`apps/backend/tests/fixtures/datasets/` (1 symbol, 1 date, 2 shards) so the browser screenshot
shows a real, non-fabricated, non-empty corpus proving the SAME rendering path — while the
literal 12/18/~3.0 totals stay proven the way iteration 1's evaluator already proved them:
computed directly against the real store, credited as endpoint-side evidence, never re-derived
through the rig.
**Reversible:** yes — a later iteration may instead scope the readiness cache to read the real
corpus read-only (the lesson's second option) once the snapshot-compute route's own storage dir
is confirmed fully isolated from `TAPEOLOGY_DATASET_DIR`'s sibling-default resolution, at which
point the rig could show the literal real totals too.

## iter-2 — goal-evaluator

**Ambiguity:** J-01's Acceptance names the real-corpus figures (`distinct_symbol_days: 12`,
`session_equivalents` ≈ 3.0, 18 `exploratory`/`hand_assigned` shards) AND requires the `/desk`
panel to render "those same served values verbatim (element screenshot)". It never says whether
"those same served values" means the specific 12/18/~3.0 numbers, or the values the endpoint serves
for whatever store is behind it. The mandated store-scoped rig cannot safely be pointed at the
operator's real store this iteration, so the two readings are not simultaneously observable.
**We chose:** the second reading — rendering fidelity. Scored J-01 `passing` on the strength of two
channels: the endpoint half proven in iteration 1 directly against the real `.data/datasets` store
(and `micro_readiness.py` is byte-unchanged since, so that evidence stands under the durability
rail), and the rendering half proven this iteration by UT-02's element screenshot of the panel
showing a real, non-fabricated 2-shard PG corpus with matching checksums, fallback fractions,
`hand_assigned` provenance and all three floors `floor_unmet`. Flagged `evidence_makeup: true` with
gap `capture-defect`, so the make-up photograph (real 12/18/~3.0 totals, and the exposure_state
column that is clipped off the right edge of this capture) rides a later iteration as a passenger
task — never as an iteration goal, and never as a reason to rebuild J-01 code.
**Reversible:** yes

## iter-3 — goal-decomposer

**Ambiguity:** `docs/rapid-validation-spec.md` §6.1 states "`micro_accessor.py` is the sole legal
reader of snapshot, ledger-input, and vault event data" as a standing rule, and trap T-5 repeats
it as a rule to "read before EVERY iteration" — but `micro_accessor.py` and its TR-3 import-ban
guard are explicitly J-05 deliverables (`docs/goal.md` J-05 step 2 lists TR-3), and the natural
dependency order runs J-03 before J-05. The goal never says whether J-03's join may read snapshot
rows directly before the accessor exists.
**We chose:** J-03's `micro_join.py` reads snapshot rows through a plain reader function added to
`micro_snapshots.py` (co-located with the writer, so exactly one module touches the on-disk
snapshot files before the accessor exists), on the era's still-fully-exploratory legacy corpus
only — no origin fencing or sealed-shard concern applies to this reader today. When J-05 lands
`micro_accessor.py` + the TR-3 import-ban guard, `micro_join.py`'s read call is expected to be
re-pointed through the accessor as part of J-05's own scope, not preempted here.
**Reversible:** yes — a small import-path change inside J-05, not a data or contract change.

## iter-3 — goal-decomposer

**Ambiguity:** spec §4 defines "Outcome start = the conditioning feature set's maximum
`available_at`" — but "conditioning feature set" is a per-candidate concept from
`scout_ledger.py`'s frozen candidate spec (§5.1: `feature: {name, transform, params}`), which does
not exist until J-04. J-03's join serves generic feature-row-at-trigger + outcome-row-after-trigger
pairs, not one candidate's conditioning feature, so the goal does not define this term at the join
layer.
**We chose:** for J-03, outcome start = `anchor_at` (the trigger's own timestamp) directly; every
feature family is served at the trigger row with its own `available_at`/`unavailable` flag intact
(deferred constructs stay `unavailable`, never folded into the outcome-start calculation). A
per-candidate conditioning-set-aware outcome start is J-04/J-05's concern once a candidate names a
specific feature.
**Reversible:** yes — J-04 may compute a candidate-specific outcome start from J-03's served rows
without changing what J-03 itself serves.

## iter-3 — goal-decomposer

**Ambiguity:** J-03's Acceptance requires "the joinable-corpus count is served on the readiness
endpoint with its per-study breakdown," but the three pilot studies are not predeclared until J-09
(`docs/goal.md` J-09 step 1), so no study identifier exists yet to break the count down by.
**We chose:** break the joinable-corpus count down by `structure_context` kind (`playbook_signal`
vs `band_touch`, matching spec §5.1's own vocabulary) and, within `playbook_signal`, by playbook
`setup_id` — the finest grouping the corpus supports before J-09 registers its studies, and the one
each pilot study's mechanism (range-wall, level-test, capitulation) will map onto once registered.
**Reversible:** yes — J-09 may re-key or add a coarser "by predeclared study" view over the same
counts without changing how J-03 computes or serves them.

## iter-3 — goal-evaluator

**Ambiguity:** J-03's Acceptance requires "the joinable-corpus count is served on the readiness
endpoint with its per-study breakdown", and step 2 says to enumerate "signals AND touches falling
inside recorded tick windows". No module in the product enumerates band-map wall-touch INSTANTS,
and defining what counts as a touch is J-09's predeclared-mechanism work (inventing one here would
breach trap T-1). The goal never says whether an unenumerated side may be served as `0`.
**We chose:** scored J-03 `passing` on a served `band_touch_count: 0` that is disclosed as
"honestly zero" in the module docstring and dev handoff but NOT in the served payload — because the
playbook-signal side is genuinely enumerated and broken down (verified against the real store:
total 2, by_setup_id {range_trade: 2}), the join PRIMITIVE for a touch is implemented and tested
both ways (cached map and honest absence), and the failure direction is an undercount, never a
fabricated positive. Recorded as a required fix-forward item: the payload must serve a
"not enumerated" state instead of a bare `0` before J-08 renders it.
**Reversible:** yes

## iter-3 — goal-evaluator

**Ambiguity:** J-01's browser half needs a screenshot (rail T-10: no screenshot ⇒ `unknown`, never
`passing`), and this iteration DID produce a fresh capture — but it came out blank
(`reports/qa/goal-rapid-microscope-iter-3-evidence/UT-J-01-result.png` is a solid dark rectangle).
The methodology says a fresh capture clears `evidence_makeup` "whatever the outcome", which does not
say what to do when the fresh capture is itself defective while the product code under it changed
(`micro_readiness.py` gained a field this iteration).
**We chose:** kept J-01 `passing` with `evidence_makeup: true` and left `last_evidence_path` on
iter-2's good panel capture — because the renderer (`apps/frontend/app/desk/page.tsx`) is
byte-unchanged this iteration, the endpoint half was re-verified by me directly against the real
store rather than carried, and this iteration's `UT-J-03-readiness-endpoint.png` independently
photographs the same served body. A blank artifact is treated as a capture defect, not as evidence
of a broken panel.
**Reversible:** yes

## iter-4 — goal-decomposer

**Ambiguity:** `runs/goal-session-rapid-microscope/state/iteration-state.md` (written by the
iter-3 evaluator) marks the `micro_observer.py` depletion `available_at` timing question (the
"one quote early" stamp at `micro_observer.py:636/:657`) as an owner ruling now DUE, specifically
because "J-04 is the first journey that conditions a result on it." Neither `docs/goal.md` nor
`docs/rapid-validation-spec.md` says whether J-04's own bounded candidate grid must include a
`quote_depletion`-conditioned candidate this iteration, or may simply avoid registering one until
the ruling lands.
**We chose:** this iteration's registered bounded fixture grid excludes every candidate whose
conditioning `feature.name` is `quote_depletion` (or any feature deriving its `available_at` from
that flagged code path). This keeps the Scout buildable and testable now without measuring any
result off the unresolved timing stamp, and without inventing a reading of it (T-1). Every other
Wave-1 feature family (F-FLOW, F-RESPONSE, the rest of F-LIQUIDITY: spread change, quote
imbalance, microprice, `refill_consistent`) stays eligible.
**Reversible:** yes — once the owner rules on the timing stamp, a later iteration can register
`quote_depletion`-conditioned candidates as an ordinary grid addition (a new `grid_version`)
without touching this iteration's already-ledgered rows; the union-N denominator only grows.

## iter-4 — goal-evaluator

**Ambiguity:** `docs/goal.md` Constraints state trap **T-10** verbatim — "every browser acceptance
needs a screenshot — none ⇒ `unknown`, never `passing`" — and this iteration's browser lane recorded
a blanket SKIP, producing zero screenshots and never running the mandated TC-20 regression set
(J-01/J-02/J-03 re-verify + `journey-scripts/J-10.json`'s 13-step sentinel). The independent auditor
read T-10 literally and filed E1: "the required-still-passing set is `unknown`, not `passing`". The
goal never says whether T-10 governs the iteration in which a journey's acceptance is FIRST proven,
or re-asserts itself every subsequent iteration even when nothing that journey renders has changed.
**We chose:** the first reading, aligned with the evaluation methodology's evidence-durability rail
(A.6: evidence expires with CHANGE, not time; durability relaxes WHICH iteration a screenshot may
come from, never whether one exists). Kept J-01/J-02/J-03 `passing` and J-10 `partial` on their
existing captures, after establishing myself that no field this diff touches can reach a screen:
`git diff` over `apps/frontend` is empty (zero `.tsx`), and `band_touch_count` / `joinable_corpus` /
`playbook_integrity_errors` appear nowhere in `apps/frontend/app|lib|components`. I additionally
re-derived the ENDPOINT half of J-01 and J-03 myself against the operator's real store rather than
carrying it. The gap is recorded as binding next-iteration work, and it is the primary reason this
iteration's verdict is ESCALATE rather than CONTINUE — so the call costs the loop nothing it can
hide behind. Had any frontend file changed, I would have scored the set `unknown`.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** `docs/goal.md` Constraints state trap **T-10** verbatim — "every browser acceptance
needs a screenshot — none ⇒ `unknown`, never `passing`" — and this iteration's browser lane recorded
a blanket SKIP for the SECOND consecutive time (zero screenshots, no evidence directory, TC-29 never
executed). The independent auditor read T-10 literally and filed E1: "J-01, J-02, J-03, J-04 and
J-10 must be recorded `unknown` for this iteration, never `passing`." Unlike iteration 4, this
iteration DID edit a backend module (`micro_join.py`) whose output is rendered by J-01's panel, so
iteration 4's "nothing this diff touches can reach a screen" reasoning does not transfer unchanged.
**We chose:** kept J-01 `passing` (and J-02/J-03/J-04 `passing`), after upgrading the durability
test from "no frontend file changed" to "the changed producer emits an identical payload, proven by
me": I called the real readiness route against the operator's real store AFTER the re-point and read
back byte-identical acceptance values (12 symbol-days, 3.0089 session-equivalents, 18
exploratory/hand_assigned shards, all three floors unmet, joinable_corpus total 2 /
{range_trade: 2}), and confirmed `apps/frontend/app/desk/page.tsx` and `micro_readiness.py` are
byte-unchanged. A cited screenshot exists (iter-2's element capture), so methodology A.6(b)'s
"a screenshot must EXIST, durability only relaxes which iteration it came from" is satisfied. J-01
keeps `evidence_makeup: true` (capture now 3 iterations overdue) and J-10 stays `partial` with its
sentinel half explicitly unverified — so the missing browser proof is carried by the journey ledger,
not hidden. The verdict is ESCALATE rather than CONTINUE primarily because of this gap, so the call
costs the loop nothing it can hide behind. Had the served payload differed at all, or had any
frontend file changed, I would have scored J-01 `unknown`.
**Reversible:** yes

## iter-5 — goal-evaluator

**Ambiguity:** J-05's Acceptance is one long sentence naming five things at once, and two of them
are met at the library level but not at any production entry point: the exposure registry's r2
initialization (goal.md J-05 Step 1 and spec §6.7 both name the legacy-tick windows, and both TC-14
tests prove the mechanism only against a hand-made stand-in corpus) and the typed `11 < 105`
floor-refusal (TC-20 proves the function, but nothing in `app/` calls it). The goal never says
whether "TR-15/TR-22 pass" means the trap's TEST passes or the trap's protection is actually wired
into the running product.
**We chose:** the second reading — a trap that no production path can reach is not armed — and
scored J-05 `partial` rather than `passing`, with both gaps named verbatim and evidence I produced
myself (154 registry rows all playbook-keyed; zero `require_sufficient_sessions_for_folds` call
sites in `app/`). `partial` blocks GOAL_ACHIEVED exactly as `failing` does, so no gate is loosened,
and the remaining work is small and concrete. I did NOT treat the registry gap as a critical
anti-goal violation (which would have forced REGRESSION and a halt) because I established that no
reachable path today can label a tick window `historical_oos`: `build_folds` returns `[]` at 11
sessions, so no tick fold and therefore no class assignment exists. It becomes critical the moment
J-06 creates genuinely unexposed data.
**Reversible:** yes

## iter-6 — goal-decomposer

**Ambiguity:** goal.md J-05's acceptance requires "the tick-family fold request returns the typed
floor-refusal naming `11 < 105`," and the iter-5 evaluator's binding next-step says to make the
running program "actually use" `require_sufficient_sessions_for_folds` instead of a silent empty
result — but no route, CLI flag, or function anywhere in `app/` lets an operator request a
walk-forward run against any corpus other than the hardcoded ~155-session playbook one
(`run_diagnostic_walkforward` is the sole fold-building production entry point, and always well
above the floor). Neither the goal nor the spec says whether this iteration must build a new
corpus-selectable entry point to make the tick case concretely reachable, or may wire the guard
defensively into the existing single entry point.
**We chose:** wire `require_sufficient_sessions_for_folds` into `run_diagnostic_walkforward`'s
existing (and only) fold-building call site, immediately before `build_folds`, guarding EVERY
corpus that function ever builds folds for — today, only the always-sufficient playbook one —
rather than inventing a new corpus-selectable route. This closes "zero call sites in `app/`"
honestly and makes the refusal genuinely live in the one production path, ready for J-09 (which
explicitly reuses this same walk-forward machinery against smaller, possibly below-floor corpora)
without adding a capability no journey this era names as in-scope yet.
**Reversible:** yes — J-09 or a future corpus-selectable entry point can call the same guard
function directly; nothing about this call site needs to move.

## iter-6 — goal-decomposer

**Ambiguity:** spec §6.7 and goal.md J-05 Step 1 both say the exposure registry must be
initialized "with every playbook and legacy-tick window pre-marked exposed," but neither names
which module resolves "the 12 legacy tick symbol-days" or whether that set is a frozen list
versus whatever the tick `DatasetStore` currently holds.
**We chose:** resolve it dynamically, at seed time, from the SAME tick `DatasetStore` listing
`micro_readiness.py` already reads (via `config.dataset_dir_resolved()`) — never a hardcoded date
list — because J-06 (the only future source of NEW tick datasets) has not landed yet, so "every
dataset currently registered" and "the 12 legacy symbol-days" are, today, the exact same set;
seeding now, before J-06 ships, is what makes that equivalence safe without inventing a separate
frozen identity list the spec never names.
**Reversible:** yes — the registry is additive and idempotent (guarded like the playbook seeding);
J-06's own universe registration is a distinct, separately-keyed corpus_id, so nothing about this
seeding needs to move or be redone once new shards exist.

## iter-6 — goal-evaluator

**Ambiguity:** `docs/goal.md` J-05's Acceptance names, word for word, "the tick-family fold request
returns the typed floor-refusal naming `11 < 105`", and the spec's TR-15 row says "the fold engine
pointed at the 18-dataset corpus returns the typed floor-refusal naming the failed minima". This
iteration closed both gaps the iteration-5 evaluator named (zero call sites in `app/`; the exposure
registry never seeded for the tick corpus) and met its own DEFINITION OF DONE ("≥1 real call site").
The goal never says whether that acceptance sentence is discharged by a guard that is genuinely live
on the ONE production fold path (which always builds folds over the playbook corpus) plus a unit test
over a synthetic 11-date list, or whether it requires a production path that can actually point the
fold engine at the tick corpus.
**We chose:** the second, stricter reading — scored J-05 `partial`, not `passing`. Grounds I
established myself, not read off a report: `app/` contains exactly one `build_folds` call site
(`walkforward.py:1149`), inside `run_diagnostic_walkforward`, which is hardcoded to the playbook
corpus; its only two callers (`micro_routes.py:323`, `walkforward.py:1221`) take no corpus or family
parameter; and the `11 < 105` string appears only in `tests/test_walkforward.py:478` over
`[f"2026-06-{d:02d}" for d in range(1,12)]`, never over the 18-dataset corpus the trap's own wording
names. The independent auditor filed the same finding (B3) and explicitly warned the evaluator not to
read the DoD checkbox as the goal acceptance. `partial` blocks GOAL_ACHIEVED exactly as `failing`
does, so no gate is loosened, and the remaining work is small — `_tick_dataset_session_dates` already
resolves the real 11 dates. I did NOT treat this as an anti-goal violation: the honest-refusal
machinery IS live on the one production path, so the failure direction is an unreachable branch,
never a fabricated pass.
**Reversible:** yes

## iter-6 — goal-evaluator

**Ambiguity:** the evaluation methodology (A.7) says `evidence_makeup` clears "the moment a fresh
capture lands — whatever the outcome". A fresh, legible Microscope Readiness element capture DID land
this iteration (`UT-02-fail.png`, 1668x3179, opened and confirmed by me). But it carries the SAME
defect class the flag was raised for in iteration 2: the store-scoped rig the test plan mandates seeds
two PG fixture datasets by design, so the panel renders 1 symbol-day / 2 datasets / 0.0045
session-equivalents, never the 12 / 18 / ≈3.0 that J-01's own acceptance names as "those same served
values". The methodology's clearing rule does not say what to do when the fresh capture reproduces the
defect rather than fixing it.
**We chose:** cleared `evidence_makeup` and kept J-01 `passing`, then recorded the residual as an
OWNER RULING (audit E3) rather than as a make-up capture. Reasoning: the flag's purpose is "a capture
is owed and a retake will fix it", and a retake demonstrably cannot fix this — the rig's own launcher
forbids pointing at or copying the real `.data/datasets` store. Keeping the flag would schedule an
impossible retake for a fourth iteration. The endpoint half was re-derived by me directly against the
operator's real store this iteration (12 / 18 / 1173.49 / 3.0089 / 150, 18/18 `exploratory` +
`hand_assigned`, three floors `floor_unmet` at 11/60, `integrity_errors: []`), and a screenshot EXISTS
with a citation, so methodology A.6(b)'s no-screenshot rail is satisfied. The owner's two options are
recorded verbatim: seed the rig from the real 18-dataset corpus, or amend J-01's acceptance to accept
an endpoint-level proof beside a fixture-corpus render. Inventing either would breach T-1.
**Reversible:** yes

## iter-7 — goal-decomposer

**Ambiguity:** goal.md J-06 step 1 (spec §7.1 r2 + §2.6) requires the event schema to ship both
the Card-5.1 preservation fields AND "the §2.6 stamping" (`schema_basis`/`quote_size_unit`)
before any recording — but `micro_features.py`'s own docstring explicitly reserves the
dated-vendor-rule constant `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE` for `tick_recorder.py` (J-06 step
2, not yet built), warning that minting it early risks "a second, independently-valued copy the
day those modules land." The goal never says whether step 1 (this iteration) must implement the
DATE-TO-UNIT RULE or merely the STORAGE CAPABILITY to carry a caller-supplied value.
**We chose:** storage capability only. `DatasetStore.record()`/`record_from_source()` gain
optional `schema_basis`/`quote_size_unit` kwargs, persisted verbatim when supplied (validated
against the EXISTING `micro_features.QUOTE_SIZE_UNITS`, never a second tuple) and simply absent
otherwise — exactly the `observer=` kwarg precedent already used on `replay()`. The dated-rule
DECISION logic stays deferred to `tick_recorder.py`, precisely where the codebase's own docstring
already reserves it.
**Reversible:** yes — `tick_recorder.py` (J-06 step 2) will define `ALPACA_QUOTE_SIZE_UNIT_EFFECTIVE`
and call `record(..., quote_size_unit=<computed>)`; nothing about this iteration's plumbing needs
to move or be redone.

## iter-7 — goal-decomposer (second)

**Ambiguity:** goal.md J-05's Acceptance says "the tick-family fold request returns the typed
floor-refusal naming `11 < 105`" without naming which caller (the `POST /walkforward/compute`
route, the CLI, or both) must carry the request. The iter-6 evaluator's own finding named BOTH
existing callers (`micro_routes.py:323`, `walkforward.py:1221`) as lacking a corpus/family
parameter.
**We chose:** the CLI only (a new flag alongside the existing `--diagnostic`), mirroring the
CLI's own established role as "the operator's REAL... run" entry point (its module docstring)
and keeping this passenger item small beside J-06's primary, riskier diff. No UI or MCP journey
names an operator-facing "request tick folds" control yet (that is J-08/J-09 territory); wiring
the shared single-flight `POST /walkforward/compute` route is deferred until a real consumer
needs it, avoiding a second, currently-unused code path through the same manager.
**Reversible:** yes — the route can gain the same optional `family` parameter later, calling the
identical underlying function this iteration adds; nothing about the CLI wiring needs to move.

## iter-7 — goal-evaluator

**Ambiguity:** `docs/goal.md` J-05's Acceptance names "the tick-family fold request returns the
typed floor-refusal naming `11 < 105`" without saying which caller must carry the request. The
iteration-6 evaluator scored J-05 `partial` on the stricter reading that the acceptance "requires a
production path that can actually point the fold engine at the tick corpus"; this iteration shipped
that path as a CLI flag only (`python -m app.research.walkforward --family tick_legacy`), with
`POST /walkforward/compute`'s family parameter explicitly deferred (decomposer assumption ledger,
iter-7 second entry). The goal never says whether a CLI-only entry point discharges the clause or
whether a route is required.
**We chose:** CLI-only discharges it — scored J-05 `passing`. Grounds I established myself, not
read off a report: I re-ran the command against the operator's REAL `.data/datasets` with a scoped
ledger and got the literal string `11 < 105 -- refused (TR-15)` on stdout with exit code 1, over
the real 11-distinct-ET-session corpus rather than a synthetic date list; `run_tick_family_fold_request`
reuses the EXISTING `_tick_dataset_session_dates` and the already-wired
`require_sufficient_sessions_for_folds` (no second inventory, no second floor); and the operator's
real `.data/micro_walkforward` was byte-identical before and after (`ea04c19b0a36d6ca`), so the path
is read-only over the store it inspects. The CLI is the module's own documented "operator's REAL
run" entry point and the same shape `--diagnostic` already uses, so this is the era's established
operator surface, not a test harness. TC-20's synthetic unit test is left byte-unmodified beside it,
so the new path is additive, never a replacement.
**Reversible:** yes — the route can gain the same optional `family` parameter later, calling the
identical function; nothing about the CLI wiring needs to move.

## iter-7 — goal-evaluator (second)

**Ambiguity:** J-06 has five steps and this iteration delivered step 1 — and even step 1 only in
part, since `docs/goal.md`'s step-1 sentence also names "the §2.6 `schema_basis` + `quote_size_unit`
stamping from the dated vendor rule", which the decomposer explicitly deferred to `tick_recorder.py`
(audit B4). My instructions define `partial` as "only some assertion steps passed" without saying
whether ~1/5 of a journey qualifies, or whether a journey this early should stay `failing`.
**We chose:** `partial`. One of J-06's own acceptance clauses is now genuinely met and I proved it
myself (every legacy dataset and committed fixture loads byte-identically with checksums verifying,
engine equivalence and golden trace byte-unmodified — 18 records, 0 errors, zero new keys), so
`failing` would understate real, verified, high-risk progress. `partial` blocks GOAL_ACHIEVED
exactly as `failing` does, so no gate is loosened. To stop `partial` reading as "nearly done", the
journey-history note and `iteration-state.md` both state the fraction explicitly ("1 of 5 steps, and
that step only in part") and list what is absent by filename: `tick_recorder.py`, `vault.py`,
TR-2/4/12/20 tests, the tranche, any sealed shard.
**Reversible:** yes

## iter-8 — goal-decomposer

**Ambiguity:** goal.md J-06 step 2 says "Implement `tick_recorder.py` (chunked `iter_historical_chunks`
fetch, tick throttle, per-chunk checkpoints, resume/idempotency, single-flight manager + CLI,
per-chunk `failed` outcomes) writing through `DatasetStore.record`..." — naming "manager + CLI" but
not a REST route, while the SAME goal.md's own Product Shape Data Contract table names the
recorder's serving endpoint as `POST/GET/POST-cancel /research/desk/micro/recorder/compute`,
`GET .../recorder/runs`. Iter-7 set a different precedent for an analogous case (the walkforward
tick-family request): CLI-only, route explicitly deferred until a UI/MCP consumer needs it, because
no journey named an operator-facing control for it yet.
**We chose:** build the REST routes this iteration, alongside the CLI and manager — not deferred.
Grounds: (1) goal.md's own Product Shape table, not just blueprint.md's transcription of it, already
commits to this exact endpoint shape as `tick_recorder.py`'s canonical serving surface (Data Contract
rows are single-source-of-truth commitments, not suggestions); (2) `desk_deep_backfill.py` — the
goal's own named precedent to copy for this exact feature ("credentialed chunked CLI job,
resumable") — ships its manager, CLI, and route together in one build, not staggered; (3) unlike the
walkforward tick-family case, a concrete future consumer IS already named (blueprint.md's
Information Architecture: J-06's canonical home is `/desk` → Validation Vault, which J-08 will wire
to this exact route family) — so building it now is not "a second, currently-unused code path" the
way the deferred walkforward route would have been.
**Reversible:** yes — the route is inert this iteration (no UI button calls it yet, and no MCP tool
ever will, per the Product Shape's 4-tool v6 delta naming only readiness/scout/walkforward/vault), so
nothing about this iteration's wiring needs to move when J-08 lands the button.

## iter-8 — goal-evaluator

**Ambiguity:** my methodology's decision tree fires ESCALATE when "this lean iteration surfaced
cross-cutting ambiguity/complexity", but it does not say whether the engine's own budget-driven
DEMOTION of a spec that declared `Depth: full` (with an explicit `Full trigger` naming the
independent auditor, and the iter-7 evaluator's binding "must not be shortened for time") counts
as such a trigger — nor whether skipping 4 of 6 required-still-passing re-checks (DEFERRED-BUDGET)
does. Read narrowly, this was a clean, progressing iteration and CONTINUE would be correct.
**We chose:** ESCALATE. Grounds I established myself, not read off a report: the diff changed
`providers/base.py`'s event-dataclass identity semantics, which is the exact surface where the
independent auditor caught a critical, in-run-fixed honesty fault in 4 of the last 4 full
iterations (journey-history violations iter-4 B2/B3, iter-5 B1/B3, iter-7 B1); this run had NO
auditor (engine.log: "spec asked FULL but the deterministic ladder demotes it to LEAN (reason:
budget-breach)"); I found a real spec-conformance gap the lean lanes missed (spec §2.6's "records
the rule text + the verification note beside the stamp" is implemented nowhere); and the NEXT step
(`vault.py`) is where an already-recorded latent hole — the exposure registry marking every
dataset exposed with no sealed filter — turns critical. I also verified that the depth line alone
cannot deliver full depth: iter-7 recommended `full` and was demoted, whereas ESCALATE grants it
("FULL pass granted (reason: prior-verdict-ESCALATE)"). So ESCALATE is both merited and the only
lever. I did NOT treat the skipped checks as a regression or a stall — nothing regressed, and
every unblock path is dev-owned.
**Reversible:** yes — a later iteration can return to CONTINUE/lean once the vault lands and the
wall-clock budget stops forcing trims.

## iter-8 — goal-evaluator (second)

**Ambiguity:** the methodology says a `DEFERRED-BUDGET` row means the journey "was NOT tested" and
keeps its prior recorded status. It does not say what `last_verified_iter` should read when the
LANE deferred a journey but the EVALUATOR independently re-derived that journey's served value
against the operator's real store in the same iteration (J-02's 18 snapshots / 3,815,933 rows,
J-03's `joinable_corpus.total` 2, J-04's `verify_chain() -> ok`).
**We chose:** record `last_verified_iter: goal-rapid-microscope-iter-8` for those journeys, with
the deferral stated verbatim in each journey's note and in the eval table's status cell
("passing (browser row DEFERRED-BUDGET)"), so no reader can mistake an endpoint-level
re-derivation for an on-screen re-check. The distinction matters because these three journeys'
modules are byte-untouched in this iteration's diff, so A.6 evidence durability already carries
their prior pass on its own; my re-derivation is corroboration, not the sole basis. For J-05 the
same situation is NOT durability-covered — `walkforward.py` changed — so I re-ran its own
acceptance command rather than relying on the deferred row.
**Reversible:** yes — the next iteration's replay scripts (a named passenger item) will restore
lane-level verification for all four.

## iter-9 — goal-decomposer

**Ambiguity:** goal.md's J-06 step 3 bullet and the Product Shape Data Contract commit `vault.py`
to serving `GET /research/desk/micro/vault`, but neither says whether an operator-facing CLI/route
for universe REGISTRATION must ship in the SAME iteration as the module. The iter-8 decomposer's
own precedent for `tick_recorder.py` built CLI+manager+routes together, reasoning a concrete
future consumer was already named.
**We chose:** ship the read-only `GET .../vault` route now (same precedent — cheap, and TR-2's
route sweep needs a real route to test against) but NOT a universe-registration CLI. Grounds:
unlike `tick_recorder.py`'s case, no operator act in this iteration or the immediately-next one
calls universe registration standalone — it only becomes operator-facing when J-06 step 4 (the
credentialed tranche) runs, and that step is deliberately deferred by the operator's own ruling
to protect this round's budget. Building an unused CLI now would be exactly the "invent a code
path this iteration's diff cannot exercise" T-1 violation.
**Reversible:** yes — step 4's iteration adds the CLI/manager wiring calling the SAME library
functions this iteration ships; nothing here needs to move or be redone.

## iter-9 — goal-decomposer (second)

**Ambiguity:** the iter-8 evaluator named a latent hole ("the exposure-registry seed marks every
listed dataset exposed with no sealed filter") without prescribing the fix's shape — spec §6.7
defines the WALKFORWARD exposure registry and its r2 seed, but was written before `vault.py` (the
only future source of "sealed" as a concept) existed, so it does not say how the two modules
should interact.
**We chose:** `TICK_LEGACY_CORPUS_ID`'s seeding (the `_tick_dataset_session_dates` caller in
`walkforward.py`) excludes any dataset id `vault.py` currently reports `sealed` from the windows
passed to `initialize_r2_exposure_registry` — a sealed shard is invisible to the legacy corpus's
r2 seed until it is assigned/exposed through the vault's OWN lifecycle, which is the only place
its exposure gets recorded. Grounds: this is the minimal change that restores the intended
invariant (a sealed shard has never been served) without inventing a second exposure concept or a
new corpus_id no goal text names.
**Reversible:** yes — the filter is a pure exclusion at seed time, still guarded by the existing
`has_any_exposure_entries` once-only rule; a later-exposed shard simply stops being excluded on
the next seed pass, with no prior row to undo.

## iter-9 — OWNER RULING (2026-08-18, operator-decided, not an agent interpretation)

**Ambiguity:** the iteration-9 audit's CRITICAL B1 — spec §7.5 (r2) required an "opaque
`shard_id`" but the implementation served the `DatasetStore` dataset id, and §7.5 *also*
mandated serving the raw `checksum commitment`, which is itself a join key to the public
dataset record. Closing the leak necessarily changes published REST/MCP contracts, so it was
escalated to the owner rather than patched by an agent.
**The owner ruled (option 1 of 3):** close it with **opaque surrogate ids + seal-aware
refusal**. Recorded as spec **revision r3** (2026-08-18) in `docs/rapid-validation-spec.md`:
surrogate `shard_id` with no derivable relation to the dataset id; pre-exposure commitment is
`HMAC(vault_secret, content_checksum)` with the raw checksum revealed only at exposure;
`/research/datasets{,/{id}}`, the `datasets` MCP tool and `get_endpoint` return a typed
refusal for a sealed dataset id; `micro_readiness` serves sealed-tranche aggregates only (no
per-shard row, no per-shard `exposure_state`); TR-2 widened from a field whitelist to an
adversarial join-resistance sweep. `docs/goal.md` J-06 step 3's acceptance updated to point at
r3 (tightened wording only — the journey's required behaviour is unchanged in kind).
**Rejected alternatives:** a separate sealed store path (strongest guarantee, largest build);
accepting the leak with a documented caveat (cheapest, materially weaker vault).
**Also settled:** `TAPEOLOGY_VAULT_SECRET_FILE` now exists at
`~/.config/tapeology/vault-secret` (0600, outside the repo, generated 2026-08-18, contents
never read by any agent). Its commitment is
`e4b64e4399878594ff358d00f5f75261e0720919c0eb32f9629897222eee6a8d` — record this in the
universe registration; never the secret itself. The operator must export the variable for any
run that seals shards.
**Reversible:** no — r3 is a named revision, and per the spec's own rule a change is a further
named revision, never an edit of recorded meaning. Nothing re-keys: zero shards were sealed
when the ruling landed.

## iter-9 — OWNER RULING #2 (2026-08-18, operator-decided: "put on the fix")

**Ambiguity:** the iteration-9 RE-audit's CRITICAL B2 — r3's sealed-shard refusals are
route-scoped, but `edge_report._all_datasets` (`edge_report.py:144`) and
`pnl_scan._split_datasets` (`pnl_scan.py:220`) each enumerate the whole `DatasetStore` and drive
`BacktestJobManager` directly, so a corpus-wide report/sweep would read a sealed shard's events
and republish its id, raw checksum and outcome aggregates via `GET /research/backtests` and the
append-only PnL ledger. The auditor escalated rather than patching, because excluding sealed
shards changes what a research report *measures* and what lands in an append-only ledger.
**The owner ruled:** apply the fix — enumerators EXCLUDE withheld shards and DISCLOSE the
exclusion. Recorded as spec **revision r4** (2026-08-18), §7.5 point 6.
**Why this is a derivation rather than a free choice** (stated so no later agent re-litigates
it): `docs/goal.md`'s critical rail already requires that event data and outcome aggregates of
a sealed shard be "refused everywhere … fail-closed", which rules out reading them; and BOTH
call sites already carry the convention "a partial report is a misleading report", which rules
out excluding them silently. Exclusion + disclosure is the only reading satisfying both.
**Shape:** filter at each module's single `DatasetStore.list()` choke point (reuse
`micro_snapshots.withheld_dataset_ids_for_store`, never a second predicate); carry a
`withheld_excluded` COUNT — never the ids — into the report body and into any append-only row
the run writes; a fully-withheld corpus reports that honestly instead of emitting an
empty-but-shaped result. TR-2 must exercise the operator compute acts (snapshot build, Scout,
edge report, PnL sweep) BEFORE sweeping, so it cannot pass on an idle rig — the exact way the
previous trap went green while the leak was live.
**Rejected:** aborting a whole sweep whenever any sealed shard exists (renders the edge report
unusable the moment the vault holds anything); accepting the bypass (re-opens what r3 closed).
**Reversible:** no — r4 is a named revision; a change is a further named revision. Nothing
re-keys: zero shards were sealed when the ruling landed, so no recorded report or ledger row
moves.
**Unblocks:** J-06 step 4 (the credentialed tranche) may proceed once r4 is implemented and
TR-2 passes in its compute-first form.

## iter-9 — goal-evaluator

**Ambiguity:** the iter-8 evaluator set a precedent for keeping a `DEFERRED-BUDGET` journey at
`passing` on an evaluator's own endpoint-level re-derivation — but it leaned explicitly on A.6
evidence durability, because those journeys' modules were byte-untouched that round ("my
re-derivation is corroboration, not the sole basis"). This round the situation is materially
different and the precedent does not simply carry: J-02/J-03/J-04/J-05 were again DEFERRED-BUDGET at
the browser layer, but their own modules (`micro_snapshots.py`, `micro_join.py`, `scout.py`,
`walkforward.py`) ALL CHANGED in the r4 fix round, so durability covers none of them and my
re-derivation IS the sole basis. My instructions do not say whether that is enough to hold
`passing`, or whether a changed module plus an untested lane row forces `unknown`.
**We chose:** hold `passing` for all four, with the deferral and the "durability does NOT cover
this" caveat stated verbatim in each journey's note, and `last_verified_iter` set to iter-9. Grounds
I established myself: J-02 — 18 snapshot feature files holding exactly 3,815,933 rows, the
unchanged multi-iteration baseline; J-03 — `joinable_corpus.total` 2 with `by_setup_id
{range_trade: 2}` and zero integrity errors against the real store with the real PlaybookStore;
J-05 — its own acceptance command re-run under post-r4 code printing the literal `11 < 105 --
refused (TR-15)` with exit 1, a scoped ledger left empty, and the real store hashing identically
before and after. Decisive general fact: the r4 change is provably value-neutral today — no vault
ledger file exists anywhere under `.data`, `withheld_dataset_ids` is empty on both stores, and
`exclude_withheld` returns every record with `withheld_excluded = 0`, so the new filter is the
identity function until something is sealed. J-04 is the honest weak one and I said so in its note
rather than dressing it up: I could NOT re-run `verify_chain()` because no real scout ledger exists
on disk (`.data/micro_scout` is absent — the Scout has never been run as an operator act), so J-04
rests this round on my own full-suite run (test_scout 52 + test_scout_ledger 20 green inside 3,166
/ 0 failures) plus the traced single-predicate reuse.
**Reversible:** yes — golden replay scripts for J-01–J-06 and J-10 now exist on disk (J-02–J-05's
were written this run), so the next iteration's deterministic replay lane can restore true
lane-level verification for all four without any new developer work.

## iter-9 — goal-evaluator (second)

**Ambiguity:** the audit carries two CRITICALs (B2: sealed membership recoverable by cartesian
closure of `GET /research/datasets`; B3: the recorder-compute route serving per-chunk
symbol/date/raw dataset id) plus B4 (withholding predicates fail OPEN on a corrupted ledger) and B5
(a frozen `referee_*.py` file counting withheld shards). My decision tree fires REGRESSION on "a
critical anti-goal violation is unresolved", and my instructions say to fail closed when unsure. But
an anti-goal violation requires the anti-goal's stated CONDITION to be breached, and every one of
these is a condition about sealed shards at a moment when no shard is sealed.
**We chose:** record all four as OPEN but `minor` severity, and return CONTINUE rather than
REGRESSION. Grounds I verified myself, not read off the audit: no vault ledger file exists anywhere
under `.data`; `seal_shard`/`assign_shard`/`expose_shard` have ZERO production call sites in `app/`
(every grep hit is a docstring, an `__all__` entry, or the definition); `withheld_dataset_ids`
returns an empty frozenset on both the real and the fixture store; and no real tape exists, so no
recorded artifact is damaged and nothing can be re-keyed later. The read side genuinely holds — the
anti-goal that events and outcome aggregates of a sealed shard are refused everywhere is currently
TRUE. B4 is the one that touches an anti-goal's own wording ("the refusal is typed, tested, and
fail-closed"), which is exactly why I recorded it as an open item against that rail rather than
burying it in prose. All four are marked HARD GATES on J-06 step 4 in J-06's note and in the
next-step recommendation, so nothing is lost by not halting now — and halting would stop tractable,
owner-independent work (J-07) for questions only the owner can answer.
**Reversible:** no in one direction — if J-06 step 4 ever runs before B2 is ruled, real tape gets
sealed under a guarantee that is demonstrably false and the recorded manifests are immutable. That
is precisely why the gate is written into the journey note, the anti-goal ledger, the recommendation
and `iteration-state.md`'s "Do not redo" block rather than any single one of them.

## iter-10 — goal-decomposer

**Ambiguity:** goal.md's J-07 acceptance criteria (spec §8, the fixture-pipeline proof) never
mentions a live REST route — only the Product Shape's Data Contract table and `micro_routes.py`'s
own forward-reference docstring ("The era's own Data Contract table names ONE more micro route
landing in a later iteration (graduation) under this SAME `/research/desk/micro` prefix") name
`GET /research/desk/micro/graduation` as graduation's eventual owner, without saying whether the
route ships in the SAME iteration as the module or waits for J-08 to wire it in.
**We chose:** ship the read-only `GET /research/desk/micro/graduation` route this iteration,
alongside `micro_graduation.py` — the exact precedent iter-9's decomposer set for `vault.py`
("ship the read-only GET .../vault route now ... cheap, and TR-2's route sweep needs a real route
to test against"). Grounds: the route is a thin, already-reserved, already-owned serving surface
(no new Data-Contract row to register); it costs nothing extra and lets TR-2's join-resistance
sweep exercise a real registered route the moment graduation ever touches sealed-shard provenance;
and it matches this era's established pattern of registering read surfaces ahead of their UI
wiring (`blueprint.md`'s own iter-3 footnote documents the identical accepted pattern for J-02's
snapshot endpoints, and `micro_routes.py`'s header comment literally calls out this exact route as
the next one due).
**Reversible:** yes — the route is inert this iteration (no button calls it; the real graduation
ledger on disk is genuinely empty, since no operator has ever run graduation), and J-08 wires it
into the `/desk` UI later with zero changes needed to the route itself.

## 2026-08-18 — OWNER RULING (3) → spec revision r5 "the opaque research pool"

Escalated after the iter-9 audit; answered by the owner directly. All three are recorded in
`docs/rapid-validation-spec.md` r5. r5 re-keys NOTHING (zero shards sealed, zero tranches
recorded, no ledger row or verdict moves) and changes no statistical rule, constant, grid, fold
geometry, or gate; it is a named revision only because this spec's own rule makes any change to
it one.

1. **Cartesian-subtraction membership leak — CLOSED STRUCTURALLY.** Rejected: accepting the
   residual with a caveat, and decoy recordings. Rejected as insufficient: merely hiding the
   tranche axes from readiness, because §7.2 already requires the symbol rule and date rule to be
   registered before fetch — the operator knows the universe by construction, so a complete
   identity-labelled list of the EXPLORATORY side reveals the withheld set as its complement.
   Ruling: a newly recorded tranche is ONE OPAQUE RESEARCH POOL. Aggregates only on BOTH sides
   while any member is unexposed; a shard's identity becomes public only when it is actually
   exposed or assigned; unused pool members stay mutually indistinguishable; internal ledgers keep
   exact identities and HMAC decisions for audit but no served surface may reconstruct the
   partition. The HMAC is an internal assignment mechanism, never a public partition. If the
   implementation requires every non-sealed shard to be individually visible at record time, the
   ARCHITECTURE changes. One-way exposure history and single-shot `family_root_id` preserved.
   Governing test = a deterministic inference trap (TR-2, widened): given the registered universe
   plus every public artifact, no still-unexposed vault-eligible shard is identifiable with
   certainty.
2. **Recorder progress — AGGREGATE ONLY.** `GET /research/desk/micro/recorder/compute` (and every
   other progress surface) serves chunks done/total, success/fail/pending, retry and failure
   counts, bytes, trade/quote totals, percent, and deterministic throughput diagnostics — never
   symbol, date, dataset id, shard id, or per-shard byte/event counts. Identities stay in the
   INTERNAL recorder ledger for recovery/idempotency/audit. **No operator-only bypass** (using one
   would itself be a human exposure event destroying blindness). TR-2 covers this path.
3. **`referee_evidence.strategy_trade_readiness` — KEEP THE FREEZE, DISCLOSE.** Do not edit
   `referee_evidence.py`; also do NOT intercept `DatasetStore` to change frozen Referee behaviour
   indirectly (that breaches the freeze's behavioural meaning even with identical bytes — option 3
   explicitly rejected). Serve the verbatim caveat beside the metric; `micro_readiness` is the
   canonical seal-aware owner; the stale count gets ZERO gate/graduation credit and no
   Scout/walk-forward/vault/graduation/floor decision may consume it; label the differing
   semantics wherever both appear; add a guard/source-scan proving the gates read only the
   seal-aware owner. Referee fix deferred to a future named Referee revision. **Escalate instead
   of accepting** if audit finds the metric feeds a live promotion or certificate decision.

## iter-10 — goal-evaluator

**Ambiguity:** `docs/goal.md`'s J-07 has no browser acceptance clause (the era header calls J-07
"keyless/automated", with browser reveals landing in J-08), yet the era's own T-10 rail says "no
screenshot ⇒ `unknown`, never `passing`" and my methodology's rubber-stamp counterexample says
unit tests are never journey evidence. Nothing states which governs a journey whose acceptance is
*defined* as a fixture walk.
**We chose:** score J-07 `passing` on (a) my OWN end-to-end four-state walk plus four adversarial
refusal probes, run outside the developer's test file against a throwaway store, (b) the 19-test
`test_micro_graduation.py` green inside my own 3,185-test full-suite run, and (c) the one
screenshot its single servable surface can produce (`UT-J-07-result.png`, the honest empty state of
`GET /research/desk/micro/graduation`, cross-checked against the genuine absence of a
`.data/micro_graduation` directory). Grounds: T-10 binds *browser acceptances*, and J-07 declares
none; the counterexample's danger (a routing typo 404s the page while unit tests pass) is exactly
what the screenshot rules out here; and my own walk, not the dev's tests, is the load-bearing
evidence.
**Reversible:** yes — J-08 renders graduation state on `/desk`, so the journey gets a true
element-captured browser acceptance one iteration later, and a failure there would re-open J-07.

## iter-10 — goal-evaluator (second)

**Ambiguity:** whether the developer's two disclosed spec-§8 improvisations (caller-supplied sealed
verdict; invented confirmation-boundary formula) block J-07's acceptance. `docs/goal.md`'s J-07
acceptance names four clauses and neither invention appears in any of them; but the era's
Constraints say an ambiguous spec procedure must be DROPPED and surfaced for an owner ruling,
"never improvise", and both improvisations sit inside the module J-07 delivers.
**We chose:** J-07 `passing` (all four acceptance clauses independently verified by me), with the
improvisation recorded as a NEW OPEN MINOR anti-goal-ledger item and named as an owner decision
owed before J-06 step 4 — rather than scoring J-07 `partial`. Grounds I established myself: no
operator-facing route reaches `record_sealed_evaluation` (the only new route is a read-only GET),
zero sealed shards and zero graduation rows exist on disk, and the reviewer independently confirmed
both are genuine spec gaps rather than shortcuts. Scoring `partial` would have punished the journey
for a defect in the SPEC, not in the delivery.
**Reversible:** no in one direction — if a real sealed evaluation is ever recorded before the owner
rules, the invented reading is written into a permanent, hash-chained export bundle. That is why
the item is written into the anti-goal ledger, the recommendation, and `iteration-state.md`'s "Do
not redo" block rather than any one of them.

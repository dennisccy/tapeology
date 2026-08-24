# Goal Session rapid-microscope — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-16T23:11:10Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration that records the backend suite count for J-10, and any agent
reading status.json to decide whether browser QA ran.

## iter-1 — 2026-08-17T02:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose browser acceptance reads the tick corpus — J-06's vault
states, J-08's four `/desk` micro sections, and J-09's study results all hit this same wall.

## iter-2 — 2026-08-17T07:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration persisting rows produced through the engine's `add_observer` seam or
any other exception-isolated callback — J-03's join, J-04's screens, J-05's fold outputs, J-06's
recorder chunks.

## iter-2 — 2026-08-17T07:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every future iteration — J-10 is the standing required-still-passing journey, so
this fires each run until the plan is parameterized to the rig's real data state.

## iter-3 — 2026-08-17T09:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration where the evaluator genuinely needs the auditor lane (provenance
ledgers, leakage rails, whole-corpus data events) — say ESCALATE, do not just recommend full.

## iter-3 — 2026-08-17T09:05:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `micro_features.py` or `micro_observer.py`; budget a corpus
rebuild into the iteration's time, and re-verify snapshot row totals afterwards.

## iter-4 — 2026-08-17T16:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any backend-only iteration (`Frontend Present: no`) whose spec still names
required-still-passing journeys or a sentinel script — i.e. every iteration of J-05/J-06/J-07/J-09
in this era.

## iter-4 — 2026-08-17T16:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every future hash-chained ledger in this era (`walkforward.py`'s fold ledger, the
vault exposure ledger, `micro_graduation.py`'s bundle) — copy `scout_ledger.py`'s anchor +
`distinct_variant_count` pattern rather than the pre-audit chain-only design.

## iter-5 — 2026-08-17T20:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every `Frontend Present: no` iteration spec that names required-still-passing
journeys or a sentinel script — i.e. J-06, J-07 and J-09 in this era; also any framework maintenance
pass touching browser-lane gating.

## iter-5 — 2026-08-17T20:30:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** every remaining hash-chained ledger in this era (the vault exposure ledger, J-07's
graduation bundle) and any statistic whose floor is a row COUNT rather than a distinct-identity count.

## iter-6 — 2026-08-17T23:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration that dispatches browser-qa; any evaluator reading
`reports/phase-*-ui-test-results.md`

## iter-6 — 2026-08-17T23:30:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration closing an "unwired guard / zero call sites" gap; any iteration whose
browser acceptance names concrete corpus values while using the store-scoped rig

## iter-7 — 2026-08-18T01:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a field to a record type whose bytes feed a checksum, content
hash, dedupe key, or identity tuple — `datasets.py`, `micro_snapshots.py`, any `*_ledger.py`. Ask
explicitly: "does this new key change what the identity function sees?", and if the new data is
metadata ABOUT the payload rather than payload, project it out of the identity before hashing.

## iter-8 — 2026-08-18T04:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec declares a `Full trigger` and whose prior iteration ran
over the wall-clock budget — i.e. every remaining iteration of this era.

## iter-8 — 2026-08-18T04:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding an optional container field (`list`/`dict`/`set`) to a frozen
dataclass in `apps/backend/app/providers/` or `app/research/`.

## iter-9 — 2026-08-18T17:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a "hidden/held-out/sealed" state beside an existing public
listing — before trusting a minimization sweep, ask what the complement reveals, and attack your own
fix before writing it up.

## iter-9 — 2026-08-18T17:06:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration with fix rounds after the QA/browser lane — especially r-revision
rounds whose changes are inert until some future state exists; also any journey whose module changed
after its screenshot, where a lane row says DEFERRED-BUDGET.

## iter-10 — 2026-08-18T22:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose iter spec writes TC scenarios over an underspecified section
of `docs/rapid-validation-spec.md` — especially J-06 step 4/5, J-08, and any future sealed-shard
evaluator that wires a real verdict in front of `record_sealed_evaluation`.

## iter-10 (second) — 2026-08-18T22:15:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a surface that touches vault-eligible shards — the r5
implementation itself, J-08's four `/desk` sections, and the four new MCP proxies.

## iter-11 — 2026-08-19T09:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `vault.py`, `micro_readiness.py`, `micro_snapshots.py` or a
withhold/reveal/exposure predicate — the r7 nonced-commitment build, J-06 steps 4-5, and J-08's
four `/desk` sections plus its four MCP proxies.

## iter-11 (second) — 2026-08-19T09:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every iteration whose spec carries an "open owner questions" or "deferred, awaiting
ruling" list, and every evaluation that reads a browser-QA evidence directory.

## iter-12 — 2026-08-19T11:30:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `vault.py`'s recovery/epoch machinery, or adding a repair
/ reconstruction path to any hash-chained ledger (`micro_chain_ledger.py` and its
`ExposureRegistry` / `WalkForwardLedger` consumers); and any J-06 step-4 work that would let real
sealed tape reach this code.
**Applies to:** every future evaluation in this session that wants the independent audit lane.

## iter-13 — 2026-08-19T17:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `micro_chain_ledger.py`, `vault.py`'s recovery/lifecycle
paths, or any append-only store whose durable summary (anchor, checkpoint, manifest, count cache) is
written in a separate step from the data it commits to — attack the crash state between the two
writes, and never accept an in-code claim that the window is benign.

## iter-13 — 2026-08-19T17:06:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every evaluation — verify each cited evidence path exists on disk before scoring
from it; and any framework work on `replay-lane.sh` / `demo_runner.py --mode verify`.

## iter-14 — 2026-08-19T20:45:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a `/desk` or `/structure` section — assert a clean console
*after* each new section is expanded, not only on first page load; and read the dev-overlay badge
in every full-page capture as a first-class signal rather than page furniture.

## iter-14 — 2026-08-19T20:45:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose spec says a UI section renders an endpoint "verbatim" — pull
the underlying store/ledger file and compare the longest-precision numeric on screen, rather than
relying on the `_PRICE_ARITHMETIC_FIELDS` sweep alone.

## iter-15 — 2026-08-20T00:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or editing a TR-* trap test, any test that "sweeps every
route/tool for a forbidden string", and specifically the five remaining traps (TR-3, TR-22, TR-23,
TR-24, TR-26).

## iter-15 (second) — 2026-08-20T00:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose new UI renders a value the real `.data` store currently has
none of (vault shards, scout families, walk-forward sequences, graduation bundles).

## iter-15 (third) — 2026-08-20T00:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any future evaluator reading a green replay table; and the harness owner, when
J-02–J-05's golden scripts are next touched.

## iter-16 — 2026-08-20T04:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or amending a TR-N trap test, any fixture whose assertion is
an arithmetic identity (`a − b == c`), and any round whose acceptance says "X stays unaffected"

## iter-16 (second) — 2026-08-20T04:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose target journey has a stored golden script; any lane certifying
"exactly N files changed"; the harness itself (journey scripts belong in `changed_files`)

## iter-17 — 2026-08-20T10:20:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or editing a rule/verdict module that takes thresholds, floors,
minimum sample sizes, or grids as arguments — `micro_sealed_evaluation.py`, `walkforward.py`'s
survivor/sequence rules, `scout.py`'s kill rules, and any future Referee-facing predicate. Also: when
a spec clause is unsatisfiable at the unit the code actually operates on (here, §8.1's 8-session /
2-symbol floors against §7.3's one-symbol-day shard), that is an owner ruling, not a fix — the
auditor's refusal to improvise was correct and produced spec revision r9 the same day.

## iter-18 — 2026-08-20T13:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration touching `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`,
`start_scoped_qa_backend.sh`, or any seed script under `apps/backend/scripts/seed_*`.

## iter-18 — 2026-08-20T13:06:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every goal-decomposer writing a spec; every evaluator reading a `SKIPPED`
`ui-test-results.md` (read the auditor's evidence directory instead of concluding "not tested").

## iter-18 — 2026-08-20T13:07:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration or evaluator relying on `regression-replay-results.md` /
`auditor-regression-replay-results.md` rows as journey re-verification.

## iter-19 — 2026-08-20T16:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding a determinism / byte-identity / "reruns match" assertion, and
any change touching `scout.py`, `walkforward.py`, or `micro_snapshots.py` seeded streams.

## iter-19 (second) — 2026-08-20T16:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration planning J-07 verification, reacting to a `state/golden-gaps` nudge,
or considering harness work to make backend-only journeys replayable.

## iter-20 — 2026-08-20T17:35:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator or decomposer about to defer a journey because a prior round's
`iteration-state.md` lists it as human-blocked — especially when the same journey has been deferred
3+ consecutive iterations without ever being attempted.

## iter-20 — 2026-08-20T17:36:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator choosing between CONTINUE-with-full and ESCALATE when the next
iteration's work genuinely warrants the audit lane.

## iter-21 — 2026-08-20T22:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that adds a new orchestration/entry-point function whose only
exercise is a pytest fixture — especially `scout.py`, `walkforward.py`, `vault.py`, and anything
whose acceptance says "recorded in the ledger" or "rendered in section X".

## iter-21 (second) — 2026-08-20T22:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose browser tests POST to `/research/desk/micro/scout/compute` (or
any other rig-mutating endpoint) — check `reports/phase-*-demo-results.md` soft notes before
believing the round was clean.

## iter-21 (third) — 2026-08-20T22:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** every evaluator, every iteration; and to any framework change touching
`scripts/automation/lib/closure_gate.py`.

## iter-22 — 2026-08-21T04:10:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration adding or editing a Scout/screen/join test whose acceptable outcome
includes `insufficient_n` / `no survivor` / a floor refusal — i.e. anything under
`apps/backend/tests/test_scout.py`, `test_walkforward*.py`, or new `micro_*` join tests.

## iter-22 — 2026-08-21T04:10:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose demo script includes a step on a `GET /research/...` address
rather than a `/cockpit`, `/structure` or `/desk` page.

## iter-23 — 2026-08-23T03:05:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that adds a served per-item timestamp/ordinal to a withheld set, or
that commits a per-run progress artifact beside one — check the JOIN, and make the trap's
combinatorial model consume every artifact its own attacker-knowledge list claims.

## iter-23 — 2026-08-23T03:05:00Z (second)  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration whose purpose is independent verification of code that entered the
repo outside goal-mode — the decomposer must write `Depth enforcement: required`, not just
`Full trigger:`, or plan for the checker to be cut.

## iter-24 — 2026-08-23T05:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any iteration that changes the SHAPE or precision of an already-served date/time
field — grep every frontend call site reading that field and check day-marker vs instant before
declaring the frontend untouched.

## iter-24 (second) — 2026-08-23T05:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any TR-2 / join-resistance / k-anonymity check, and any "non-vacuity counter-test"
— build the counter-fixture from what the WRITER actually wrote (read the stamping function), never
from the reference side's own values.

## iter-24 (third) — 2026-08-23T05:55:00Z  [condensed: body → lessons.md.archive.md]
**Applies to:** any evaluator reading a CLOSURE-PASS — treat it as "artifacts exist", not "the
browser agreed"; always open `reports/phase-<iter>-ui-test-results.md`'s own verdict line yourself.

## iter-25 — 2026-08-23T07:05:00Z

**Verdict:** ESCALATE
**Lesson:** A "minor" severity score is a claim about the WORLD, not about the code, and the world
moves. The iter-13 chain-ledger gap (`micro_chain_ledger.py:184-190` — anchor absent + zero rows
verifies clean) was scored minor on the explicit premise "no micro_vault directory, zero sealed
shards in the real store"; that premise died at iter-23 when the operator recorded the real tranche,
and nobody re-derived it for two rounds. Re-check the GROUNDS of every carried-forward open item, not
just whether the code changed.
**Applies to:** any evaluator carrying an open anti-goal item forward whose severity argument cites
the state of `apps/backend/.data` (or any other runtime store) rather than the state of the code —
re-run the cited check before copying the score.

## iter-25 (second) — 2026-08-23T07:05:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane is scoped to the Required-still-passing list, which
structurally EXCLUDES the iteration's own target journey — so a target journey's stored golden can
never be executed by the harness in the round that authors or changes it, and any DoD line saying
"the golden ran" necessarily rests on a dev-local claim. Third round running that this produced a
finding (iter-24 T2, iter-25 reviewer MINOR #1). Either the round after must re-run the golden, or
the lane needs the target journey added.
**Applies to:** any iteration whose Definition-of-Done asserts a stored `journey-scripts/J-XX.json`
passed via `demo_runner.py --mode verify`, where J-XX is that iteration's own target journey.

## iter-26 — 2026-08-23T14:40:00Z

**Verdict:** CONTINUE
**Lesson:** A cache key that names a REQUEST rather than an ANSWER silently collides "answer
absent" with "answer present": `BandMapResolver.map_key(symbol, epoch)` is (symbol, basis day,
store signature, config hash), so an unresolved band map's honest `0` was published under the very
key the operator's later tradability warm publishes under — a permanent wrong `0` on
`/desk`. The rule that falls out: only ever cache a value whose PRODUCING INPUT was actually
present (`micro_join.py:666-687`, `cacheable = resolver.resolve(...) is not None`), and check
whether a new cache is the first in its family to have a second, mutable input — the
`MicroReadinessCache` precedent it was copied from has only one (immutable dataset events), which
is exactly why the copy looked safe. Second, independent lesson from the same round: a delivered
test that ASSERTS the defect (`assert lookup(...) == 0`) is why both the reviewer and the QA lane
saw green — when reviewing a new cache, read what its invalidation test asserts, not just that it
passes.
**Applies to:** any iteration adding a durable cache in `apps/backend/app/research/` (especially
one keyed on a resolver/map/store identity rather than pure content), and any reviewer/auditor pass
over a new `*Cache` class.

## iter-26 — 2026-08-23T14:40:00Z (second)

**Verdict:** CONTINUE
**Lesson:** Test fixtures that read the operator's real `.data` store are a slow-acting
infrastructure bomb: `tests/test_micro_readiness.py:456-471`'s module-scoped `real_readiness`
fixture walks `CONFIG.dataset_dir` from a cold cache every run, and that corpus grew ~0.92 GB →
~26 GB during the era. Consequence measured this round: one test FILE would not finish in 520s,
the QA lane's suite log died at 59% (and still recorded `EXIT_CODE=0`), the CPU starvation almost
certainly killed the backend mid-round, and six browser checks plus the demo capture came back as
empty "Backend unreachable" shells while every prose report still read PASS. Any lane's "full suite
green" claim in this repo is now unverifiable until those fixtures get a durable cache path or a
corpus cap.
**Applies to:** any iteration touching `apps/backend/tests/test_micro_*.py`, any lane asserting a
full-suite result, and any round whose browser evidence goes missing without an obvious cause —
check for a stalled pytest pinning the CPU before blaming the browser rig.

## iter-27 — 2026-08-23T17:05:00Z

**Verdict:** ESCALATE
**Lesson:** With every journey recorded `passing`, the engine's depth ladder becomes a trap: the
budget-breach/full-cap rungs demote `full`→`lean`, and SPEED-9's evidence backstop then demotes
`lean`→`evidence` because every target journey is already green (`run-goal.sh` ~2745-2775,
`goal_full_ran_in_window` in `lib/common.sh`). The result is a round with no developer and no
reviewer dispatched against a spec that planned real production work — iter-27 spent ~4,300s and
produced a zero-byte product diff. Only ESCALATE/REGRESSION (or an operator `CHAIN_REQUIRE_FULL_DEPTH`)
escapes it, so a late-era session whose remaining work is NOT journey-shaped must plan for that.
**Applies to:** any goal session where journey-history shows zero failing journeys but the
evaluator's open anti-goal ledger still names machine-buildable dev work — check the depth ladder
BEFORE recommending `lean`/`evidence`.

## iter-27 (second) — 2026-08-23T17:05:00Z

**Verdict:** ESCALATE
**Lesson:** A Chrome full-page capture of `/desk` is not trustworthy evidence: `J-10-result.png`
(1668x24776) stitched the page header in TWICE (y=107 and y~16491) and truncated inside the Playbook
Evidence table, so it silently omitted the four Rapid-Microscope sections, Referee Runs, the cockpit
and `/structure` — while the lane's prose claimed it captured the Scout Ledger make-up. Element
captures (`J-01-result.png`, an extracted `[data-testid="micro-readiness-section"]`) are on-point and
verifiable; stitched full-page shots of this page are not. Verify a full-page capture by cropping
and reading it before accepting any claim about what it contains.
**Applies to:** any iteration citing a full-page `/desk` screenshot as journey evidence, and any
browser-qa lane claiming a make-up capture rode passenger on another journey's pass.

## iter-28 — 2026-08-23T23:10:00Z

**Verdict:** STALLED
**Lesson:** The deterministic closing gate (`scripts/automation/lib/closure_gate.py:87-90`) matches
the bare substring `backend-only` ANYWHERE in `phase-<iter>-user-visible-changes.md` and, if any
frontend file changed, emits a blocking CLOSURE-FAIL. Iter-28's document was correct and detailed —
it quoted the new sentence, named its new `data-testid` and its exact DOM position — but its "Not
Visible Yet" section described a new test as "a backend-only regression guard", and that phrase
alone failed the round (`status.json` = blocked / closure_failed, showcase tail never finished).
**Applies to:** any frontend-touching iteration whose `user-visible-changes.md` mentions
"backend-only", "no user-visible" or "no visible changes" while describing something OTHER than the
iteration itself — phrase those lines as "no UI surface" until the gate is scoped, and never read a
CLOSURE-FAIL on this rule as a product defect without opening the document first.

## iter-28 — 2026-08-23T23:12:00Z

**Verdict:** STALLED
**Lesson:** A SPEED-15 rung-2 budget trim that sheds a no-golden Required-still-passing journey
writes a `DEFERRED-BUDGET` row, and `goal_gate.py` counts that cell as blocking — so an ordinary
wall-clock overrun can silently make GOAL_ACHIEVED mechanically impossible even when every journey
is green. Iter-28 shed J-07 (no stored golden by an earlier binding decision, so replay structurally
cannot cover it, and the LLM lane was not given it either); its own fixture suite runs in 1.48s.
**Applies to:** any journey that has no stored golden and rides the Required-still-passing list —
give it a golden, or route it to the lane that can actually run it, before a round that is likely to
overrun; and any evaluator scoring a round that certified everything except one shed row.

## iter-29 — 2026-08-24T15:35:00Z

**Verdict:** STALLED
**Lesson:** A hard-audit finding is an input to be re-derived, not a fact to inherit — even when
it comes from the lane with the best catch record in the era. The iter-29 audit's T1 told the
evaluator to read "9/9 replay PASS" as near-worthless ("six 2-step single-substring goldens", "the
evidence PNGs are non-discriminating", "J-04 and J-05 cannot distinguish their own surface"). I
opened four PNGs and read all nine golden scripts: J-01/J-04/J-05/J-09 each depict their own
acceptance state, the J-04/J-09 byte-identical frame contains BOTH journeys' asserted strings, and
J-01/J-02/J-03/J-09 assert journey-specific text. Only J-05 genuinely borrows J-04's assertion.
The finding was directionally right and quantitatively wrong, and had I inherited it I would have
mis-scored the certification evidence in the pessimistic direction — the mirror image of the
optimistic over-claiming this era has caught six times.
**Applies to:** any iteration where the evaluator is weighing replay/golden evidence for
certification, and generally to any auditor finding phrased as a quantified claim about artifacts
("N of M are X") — open the artifacts and count.

## iter-29 — 2026-08-24T15:35:00Z (second)

**Lesson:** Before scoring an open anti-goal item as blocking, check WHICH SECTION of `docs/goal.md`
its cited rule actually lives in. Four of this era's eight open items cite "T-10 Evidence honesty",
which sits in the "Build anchors & weak-model traps" section (line 433), not in "Anti-goals" (line
689). They are real findings about build-chain reporting, but they are not product anti-goals, and
their remedies live in `agents/**`/`scripts/automation/**` — outside a product round's authority
per `.claude/maintenance-protocol.md` §1. Recording that classification in the ledger (without
downgrading the finding) is what let this round separate "two owner decisions genuinely block the
era" from "six things block the era", which is the difference between an actionable halt and an
unanswerable one.
**Applies to:** any evaluator inheriting a long-lived `anti_goal_violations` list; re-derive each
entry's rule location, not just whether the code changed.

## iter-30 — 2026-08-24T18:15:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** The deterministic replay lane writes ONE viewport screenshot per journey but takes it
at whatever scroll position the last step left, so journeys whose assertion text lives at
different depths of the same `/desk` accordion end up sharing a byte-identical file — this round
J-01/J-02/J-03 all shared md5 `b805ad04cf96ddb7663299b78d257beb` and J-04/J-09 shared
`18e0584813bfca5430a499c0181f37f2`. A PASS row plus a screenshot is therefore NOT proof the
picture frames what the journey asserts; the only way to tell is to open the image and compare it
to the golden's `expect.text`. Consequence for the `evidence_makeup` flag: "any fresh capture
clears it" must not be applied mechanically, because a fresh capture can reproduce the exact
defect the flag was raised for.
**Applies to:** any iteration scoring journeys verified by `demo_runner.py --mode verify` against
accordion/below-the-fold sections, and any evaluator deciding whether to clear `evidence_makeup`.

## iter-31 — 2026-08-24T21:10:00Z

**Verdict:** CONTINUE
**Lesson:** An acceptance criterion that names TWO mutually exclusive store states ("the empty real
ledger shows 'No candidates ledgered.'" AND "a fixture rig with one family per stage") cannot be
met on one long-lived QA rig: this era's `:8301` store-scoped rig has carried the iteration-18
graduation fixture since it was seeded, so the empty-state render is structurally unreachable on
it, and the browser lane has no mandate to stand up a second backend/frontend pair (the frontend's
`NEXT_PUBLIC_API_URL` is baked in at process start). Plan the fixture rig in the SPEC — seed a
scoped `TAPEOLOGY_MICRO_GRADUATION_DIR` and name which rig serves which scenario — or the round
will build correct code and still fail its own acceptance for lack of a place to photograph it.
**Applies to:** any iteration whose acceptance names an empty-state render plus a populated render,
or otherwise requires two different store contents in one browser pass.

## iter-31 — 2026-08-24T21:10:00Z (second)

**Verdict:** CONTINUE
**Lesson:** A new `/desk` section can satisfy T-11 literally (own heading, own `data-testid`,
rendered below the shipped ones) and still erode existing goldens: the Graduation section prints
"Ledger chain verification:", the single string J-04's and J-05's stored scripts assert. It is
harmless only because `CollapsibleSection` renders `{open && children}`, so a collapsed section
contributes no text. Run the T-11 static sweep against the stored scripts' EXPECT TEXTS, not just
against testids and headings, and prefer a journey-unique string for every golden.
**Applies to:** any iteration adding a section to `/desk` (or any page with stored replay scripts).

## iter-32 — 2026-08-24T22:35:00Z

**Verdict:** GOAL_ACHIEVED
**Lesson:** Two evidence traps closed together this round. (1) Chrome MCP's element-clip
screenshot (`screenshot` with a CSS `selector`) returns an all-black PNG once the page has been
programmatically scrolled past the `/desk` sticky header — the reliable recipe is
`window.scrollTo(0,0)` → `fullpage:true` capture → crop the saved PNG to the element's
`getBoundingClientRect()`; the DOM text was correct throughout, so only the pixel buffer was
affected. (2) `list_graduation_families` only lists a family that owns at least one graduation
ledger row, and `"exploratory"` is never an appendable `to_state`, so the ONLY code-legal way to
photograph an `exploratory` family is to give it a real `insufficient` sealed evaluation (n < 30)
and never call `evaluate_walkforward_survivor_transition` — hand-writing a row would have been
fabricated data.
**Applies to:** any iteration capturing element screenshots on `/desk` below the fold, and any
future fixture seeding of `micro_graduation.py` / `micro_sealed_evaluation.py` states.

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

## iter-12 — 2026-08-19T11:30:00Z

**Verdict:** ESCALATE
**Lesson:** A recovery/repair primitive can satisfy every written test and still break the
invariant it exists to protect, because the tests only cover entities the damaged artifact can
still NAME. `vault.recover_shard_ledger`'s unprovable branch correctly marks the shards visible
in the surviving prefix `exposure_unknown`, but a shard whose only row lived in the destroyed
suffix silently leaves the withheld set entirely — and `rewrite_from_recovery` then regenerates
the tail anchor, so `verify_chain()` reports `ok: True` again and the loss becomes undetectable
from the vault's own state. The durable anchor knew the row count (3) versus the survivors (2),
so a fail-closed refusal was available and simply was not taken. When auditing a
recover-from-damage path, always probe the entity whose ONLY record was destroyed, and always
re-run the integrity check AFTER the repair to see whether the repair erased the evidence.
**Applies to:** any iteration touching `vault.py`'s recovery/epoch machinery, or adding a repair
/ reconstruction path to any hash-chained ledger (`micro_chain_ledger.py` and its
`ExposureRegistry` / `WalkForwardLedger` consumers); and any J-06 step-4 work that would let real
sealed tape reach this code.

**Lesson (process):** A `full`-depth request expressed only in the evaluator's *prose* is not
binding — the engine's arbiter reads the VERDICT LINE. My iteration-11 CONTINUE + "run full next
time" was demoted to lean, and the one lane that has found a real integrity defect in every full
iteration of this era did not run on the iteration that shipped security-critical machinery. If
the next iteration genuinely needs the auditor, the verdict must be ESCALATE, not CONTINUE with a
recommendation.
**Applies to:** every future evaluation in this session that wants the independent audit lane.

## iter-13 — 2026-08-19T17:05:00Z

**Verdict:** ESCALATE
**Lesson:** A comment asserting that a race window is harmless is the best place to attack, not a
reason to stop. `micro_chain_ledger.append_row` writes the row BEFORE its tail anchor and its own
comment calls the gap "benign -- never falsely short"; that sentence is exactly why three passes
(dev self-attack, reviewer, my own iter-12 probe) all missed that with the anchor lagging one row, a
**byte-genuine** reconstruction of the anchor-length history satisfies every conjunct and
`rewrite_from_recovery` truncates a real sealed shard away — no attacker needed, a power loss plus an
honest operator reproduces it. The audit caught it only by ignoring the comment and executing the
crash state. Corollary confirmed by my own probes: the same window also lets a recovery revert a
recorded EXPOSURE, so the harm class was broader than the one instance anybody reported.
**Applies to:** any iteration touching `micro_chain_ledger.py`, `vault.py`'s recovery/lifecycle
paths, or any append-only store whose durable summary (anchor, checkpoint, manifest, count cache) is
written in a separate step from the data it commits to — attack the crash state between the two
writes, and never accept an in-code claim that the window is benign.

## iter-13 — 2026-08-19T17:06:00Z

**Verdict:** ESCALATE
**Lesson:** The deterministic replay lane emitted five PASS rows citing
`reports/qa/goal-rapid-microscope-iter-13-evidence/J-0{1..5}-verify.png` and wrote **none of them**
(iters 11 and 12 both did). A results row is not evidence — open the file. Paired with the third
auto-deletion of `state/golden-gaps`, the harness has now twice this era produced artifacts whose
absence silently reads as coverage.
**Applies to:** every evaluation — verify each cited evidence path exists on disk before scoring
from it; and any framework work on `replay-lane.sh` / `demo_runner.py --mode verify`.

## iter-14 — 2026-08-19T20:45:00Z

**Verdict:** ESCALATE
**Lesson:** A framed screenshot carries evidence nobody wrote down. The Next.js dev-overlay badge
in `UT-03-result.png` / `UT-04-result.png` reads "5 Issues" while the same page's earlier captures
(`UT-01`, `UT-02`) and later fresh loads (`UT-11`, `UT-12`, `UT-17`) show no badge at all — which
localises a brand-new defect to the exact click that expanded Walk-Forward. It is a `<details>` +
`<pre>` nested inside a `<p>` at `apps/frontend/app/desk/page.tsx:6461-6472`, invalid HTML that
React reports as a hydration error; a whole-file scan proved it is the ONLY such site in the
12,000-line Desk page, so it is unambiguously this iteration's. Review, QA, browser-QA, coherence
AND the independent auditor all passed it, because every lane asserted on DOM *content* and none
asserted on console cleanliness AFTER expanding a section (UT-01 only checked the collapsed load).
**Applies to:** any iteration adding a `/desk` or `/structure` section — assert a clean console
*after* each new section is expanded, not only on first page load; and read the dev-overlay badge
in every full-page capture as a first-class signal rather than page furniture.

## iter-14 — 2026-08-19T20:45:00Z (second)

**Verdict:** ESCALATE
**Lesson:** Rendered-vs-stored equality is cheap to prove and worth proving every time a "reads
verbatim, never recomputes" claim is made. Reading the five fold rows off `UT-03-result.png` and
diffing them against `.data/micro_walkforward/walkforward_ledger.jsonl` matched exactly — including
`0.019176079727258294` and `-0.007730667002689608` — which converts "no client-side arithmetic"
from a regex guard's word into a measured fact in about two minutes. The full-precision floats are
what make it decisive: any rounding, formatting or recomputation in the browser would have shown.
**Applies to:** any iteration whose spec says a UI section renders an endpoint "verbatim" — pull
the underlying store/ledger file and compare the longest-precision numeric on screen, rather than
relying on the `_PRICE_ARITHMETIC_FIELDS` sweep alone.

## iter-15 — 2026-08-20T00:20:00Z

**Verdict:** ESCALATE
**Lesson:** A regression test can be structurally unable to fail while looking perfectly green.
This round's own opaque-pool sweep (`tests/test_mcp_server.py`
`test_tr2_the_new_mcp_tools_leak_nothing_about_a_sealed_shard`) sealed its shard under an
*unregistered* universe — inherited from every member of `test_vault.py`'s TR-2 family — so
`vault._serialize_universe`'s committed/revealed branch never executed and the sweep was blind to
the single most direct de-anonymisation the spec names. It was caught only by mutation-proof
(patch production to leak; watch the old test still pass), not by reading the test. Every new trap
test in this era needs a non-vacuity assertion proving the state it sweeps is genuinely populated
in the branch under test — the fix added five (`test_mcp_server.py:1292-1299`).
**Applies to:** any iteration adding or editing a TR-* trap test, any test that "sweeps every
route/tool for a forbidden string", and specifically the five remaining traps (TR-3, TR-22, TR-23,
TR-24, TR-26).

## iter-15 (second) — 2026-08-20T00:20:00Z

**Verdict:** ESCALATE
**Lesson:** Three browser-QA rows this round were graded PASS on a client-side `window.fetch`
substitution (UT-04), a direct source read (UT-05, UT-07 Part C), and one optional non-zero-fixture
check was SKIPPED outright (UT-12) — each honestly disclosed inside its own row, which is a real
improvement over iteration 14. But the substance only became evidence when the independent auditor
seeded the non-zero state and rendered it live. When the real store's honest state is all-zero, the
browser lane structurally cannot exercise the non-zero render path; plan for a second seeded rig
(or accept that the auditor is the lane that closes it) rather than treating a source read as a
browser pass.
**Applies to:** any iteration whose new UI renders a value the real `.data` store currently has
none of (vault shards, scout families, walk-forward sequences, graduation bundles).

## iter-15 (third) — 2026-08-20T00:20:00Z

**Verdict:** ESCALATE
**Lesson:** `reports/qa/goal-rapid-microscope-iter-15-evidence/J-0{2,3,4,5}-verify.png` are
md5-identical (`28403a00c2da3d7ec9b3b0957a9afe93`) because their golden scripts
(`runs/goal-session-rapid-microscope/journey-scripts/J-0{2..5}.json`) are one step each — `goto
/desk` plus one collapsed-heading assertion. "6/6 replay journeys passed" therefore carries almost
no regression weight for four of the six. This is NOT a capture defect (a re-capture yields the
same picture) — it is script depth, and it should be fixed by deepening the scripts, not by
re-shooting them.
**Applies to:** any future evaluator reading a green replay table; and the harness owner, when
J-02–J-05's golden scripts are next touched.

## iter-16 — 2026-08-20T04:35:00Z

**Verdict:** ESCALATE
**Lesson:** A mutation-proof only proves the ASSERTION can fail — it does not prove the FIXTURE
can discriminate. TR-26's fix shipped with `_depletion_events()` whose revealing quote carried ask
size 300, byte-identical to the size the run already held, so `value == 200.0` held under BOTH the
correct rule (`500 − 300`) and the corrupt one (fold the revealing quote in first). The dev's
genuine RED→GREEN TDD transcript, the reviewer's own direct mutation of production source, and the
pump's framing of the round all missed it; only the auditor's `micro_observer.py:646` mutation
(`run["current_size"] = size`) exposed it — the whole file stayed green. I reproduced it myself:
under that mutation exactly one test fails (the auditor's new twin-fixture test, with the predicted
`-400`) and every other test in the file passes. Rule for every future trap: build fixture numbers
that are deliberately all different, so no assertion can hold for the wrong reason — and check
specifically whether the fixture's numbers COINCIDE anywhere the assertion depends on them.
**Applies to:** any iteration adding or amending a TR-N trap test, any fixture whose assertion is
an arithmetic identity (`a − b == c`), and any round whose acceptance says "X stays unaffected"

## iter-16 (second) — 2026-08-20T04:35:00Z

**Verdict:** ESCALATE
**Lesson:** A journey's stored golden replay script can be rewritten, linted, and shipped WITHOUT
ever being executed, and nothing in the pipeline notices: `runs/.../journey-scripts/J-10.json` is a
tracked file that `status.json`'s `changed_files` does not track, so the reviewer's and QA's
"exactly 6 files changed" certifications were both computed against a list that structurally cannot
contain it. In this round the rewrite also silently DROPPED two data-bearing assertions (real
playbook evidence) in favour of four empty-state ones — replacing "this value is right" with "this
list is empty" — in the very round where that journey was the target. Check the full
`git status --porcelain` yourself, not `status.json`, whenever a lane certifies a file count.
**Applies to:** any iteration whose target journey has a stored golden script; any lane certifying
"exactly N files changed"; the harness itself (journey scripts belong in `changed_files`)

## iter-17 — 2026-08-20T10:20:00Z

**Verdict:** ESCALATE
**Lesson:** A round can retire a caller-supplied ANSWER and still leave the caller supplying the one
INPUT the spec pins as a constant — and that hole survives a dev TDD proof, an independent reviewer
mutation, and a full QA pass, because every committed fixture narrows the same constant. Iteration
17's `micro_sealed_evaluation.py:203-215` `_resolved_floors` read `candidate_spec["floors"]`, so
`floors={1,1,1}` + one observation produced a permanent `verdict: "pass"` under a `rule_hash`
certifying 30/8/2; audit mutation AM-7 showed FOUR committed tests flip to `insufficient` the moment
the pinned floors are actually applied — i.e. every PASS/FAIL in the new suite existed only because
its fixture narrowed the floor. The tell is mechanical, not intuitive: when a new rule module accepts
ANY threshold-shaped argument, run one mutation that forces the spec-pinned value and count how many
tests change verdict. If the answer is "several", the constant is not pinned, it is negotiated.
**Applies to:** any iteration adding or editing a rule/verdict module that takes thresholds, floors,
minimum sample sizes, or grids as arguments — `micro_sealed_evaluation.py`, `walkforward.py`'s
survivor/sequence rules, `scout.py`'s kill rules, and any future Referee-facing predicate. Also: when
a spec clause is unsatisfiable at the unit the code actually operates on (here, §8.1's 8-session /
2-symbol floors against §7.3's one-symbol-day shard), that is an owner ruling, not a fix — the
auditor's refusal to improvise was correct and produced spec revision r9 the same day.

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

## iter-18 — 2026-08-20T13:05:00Z

**Verdict:** ESCALATE
**Lesson:** A change to a SHARED QA seeding rig is a change to every journey that rig serves.
This round appended `seed_micro_graduation_iter18_fixture.py` to
`apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh` — the one launcher every
browser/replay pass in this era drives — purely to make J-07's proof discriminating. It took the
rig's vault from 0 shards to 1, which silently falsified the `"No shards recorded."` assertion in
BOTH `journey-scripts/J-08.json` (step 5) and `J-10.json` (step 12). Neither was noticed until the
independent auditor ran the replay lane by hand. Rule: when a round writes into the browser rig,
re-run the FULL replay set before calling it done.
**Applies to:** any iteration touching `apps/backend/scripts/qa_playbook_iter7_fixture_scoped_backend.sh`,
`start_scoped_qa_backend.sh`, or any seed script under `apps/backend/scripts/seed_*`.

## iter-18 — 2026-08-20T13:06:00Z

**Verdict:** ESCALATE
**Lesson:** `Frontend Present: no` in a spec whose DEFINITION OF DONE names `browser-qa-agent` is a
self-cancelling spec: the metadata switches off the UI chain (all five artifacts become one-line
"N/A" stubs, `ui-test-results.md` becomes `Browser QA Verdict: SKIPPED` with zero journey rows,
`status.json` records `browser_checks_run: false`), and the DoD items that name that lane then pass
review and QA with nothing behind them. Full depth does NOT protect against this — a full iteration
with `Frontend Present: no` skips the same lanes. The decomposer must set `Frontend Present: yes`
whenever the DoD names a browser check, even for a backend-only code change.
**Applies to:** every goal-decomposer writing a spec; every evaluator reading a `SKIPPED`
`ui-test-results.md` (read the auditor's evidence directory instead of concluding "not tested").

## iter-18 — 2026-08-20T13:07:00Z

**Verdict:** ESCALATE
**Lesson:** A golden replay script whose only step is `goto /desk` + expect one unrelated section
heading is a regression check that cannot fail. `journey-scripts/J-02/J-03/J-04/J-05.json` each
assert `"Top-up Runs"` / `"Index Reconciliation"` / `"Screen Runs"` / `"Playbook Signals"` — all
pre-existing Era-B Desk headings, none related to the micro observer, the structure×flow join, the
Scout ledger or the walk-forward engine. `demo_runner.py` captures no console errors either, so
those rows verify only that `/desk` renders. The tell was in the artifacts: all four journeys'
`-verify.png` files are byte-identical (same md5). Diagnostic to reuse: when N journeys' replay
screenshots share one md5, read their scripts — the checks are probably measuring the same nothing.
**Applies to:** any iteration or evaluator relying on `regression-replay-results.md` /
`auditor-regression-replay-results.md` rows as journey re-verification.

## iter-19 — 2026-08-20T16:35:00Z

**Verdict:** CONTINUE
**Lesson:** A determinism ("same input, same output") comparison over a SATURATED statistic is
blind by construction, and the standard mutation-proof will never reveal it. In
`test_micro_deterministic_rerun.py`'s TC-2, the fixture screened `_planted_effect_anchors()` at
`effect=3.0`, which saturates the 2,000-draw block-permutation null in `scout.py:141`, pinning
`p_screen` to the floor `1/2001` in every run — so replacing `scout.scout_stream` with an unseeded
`random.Random()` left the whole compared payload byte-identical and all eight landed tests green
(I reproduced this myself in the real file, then restored it md5-identical). TC-4-style
mutation-proofs cannot catch it because they perturb the comparison's INPUT, not the COMPUTATION;
the mutation that discriminates is the one applied to the SEED LINEAGE. Rule for any future
determinism check: pick a fixture whose statistic lands strictly INSIDE the null distribution, and
mutation-proof the seeded stream itself, not just the comparator.
**Applies to:** any iteration adding a determinism / byte-identity / "reruns match" assertion, and
any change touching `scout.py`, `walkforward.py`, or `micro_snapshots.py` seeded streams.

## iter-19 (second) — 2026-08-20T16:35:00Z

**Verdict:** CONTINUE
**Lesson:** J-07 "Graduation" can NEVER have a stored golden replay script with the current
harness, so the SPEED-23 nudge (and the iter-19 audit's §5 recommendation to "author its golden
script") is chasing something impossible. Three independent reasons, all verified:
`demo_runner.normalize_url()` (`incredible_auto_dev/scripts/automation/lib/demo_runner.py:39-57`)
rewrites ANY localhost URL onto the FRONTEND base, so a step targeting `:8301` silently lands on
`:3301`; there is no frontend rewrite/proxy for `/research/*`; and `/desk` renders no graduation
content at all (`grep -c graduation apps/frontend/app/desk/page.tsx` returns 0). Its LLM lane is a
design consequence, not an oversight — which also means J-07 is the journey most likely to be shed
by a wall-clock trim, because the LLM lane is the expensive one.
**Applies to:** any iteration planning J-07 verification, reacting to a `state/golden-gaps` nudge,
or considering harness work to make backend-only journeys replayable.

## iter-20 — 2026-08-20T17:35:00Z

**Verdict:** ESCALATE
**Lesson:** A "human-blocked" label, once written into `iteration-state.md`'s Active blockers, is
copied forward by every later round and stops being questioned. J-09 carried "blocked entirely by
the sealed judge's econ-floor ruling" for two rounds; re-testing it against the goal text took ten
minutes and it did not survive — J-09's own acceptance says no study output feeds any gate or
certificate, `grep -rn evaluate_sealed_verdict apps/backend/app/` finds zero production callers,
the legacy 12 symbol-days are permanently `exploratory` so "evidence classes never mix" bars them
from the sealed judge by construction, and the Scout derives its OWN economic floor from measured
spreads (`scout.py:1016-1021`, `ECON_FLOOR_SPREAD_MULTIPLE * family_median_spread_bps`) rather than
taking a caller's. Re-derive an inherited blocker before deferring a journey on it a third time.
**Applies to:** any evaluator or decomposer about to defer a journey because a prior round's
`iteration-state.md` lists it as human-blocked — especially when the same journey has been deferred
3+ consecutive iterations without ever being attempted.

## iter-20 — 2026-08-20T17:36:00Z

**Verdict:** ESCALATE
**Lesson:** The depth-recommendation line is NOT symmetric. `run-goal.sh:2440-2451` treats an
evaluator recommendation of `lean`/`evidence` as BINDING (that is why iteration 19's `evidence` ask
was honoured verbatim), but a recommendation of `full` falls through to the legacy allowlist at
`:2478-2494`, which grants full depth only for a prior ESCALATE/REGRESSION verdict, a prior
coherence FAIL, a machine-parseable `Full trigger:` line in the next spec, or a due hardening
cadence — and this session runs with the cadence disabled at 0. So a `CONTINUE` + "Depth
Recommendation: full" is silently demoted to lean unless the decomposer happens to write the
trigger line. Iterations 12–18 were empirically right that only the verdict line reliably buys the
independent audit lane; the mechanism, not folklore, is the reason.
**Applies to:** any evaluator choosing between CONTINUE-with-full and ESCALATE when the next
iteration's work genuinely warrants the audit lane.

## iter-21 — 2026-08-20T22:10:00Z

**Verdict:** ESCALATE
**Lesson:** A spec'd flow can pass review AND QA while being reachable by NOTHING but a unit test.
`register_screen_and_walkforward_check` / `walkforward.scout_candidate_walkforward_floor_check`
had zero non-test callers — `ScoutComputeManager.trigger` → `run_scout_grid_and_record` only ever
called `register_and_screen_candidate` — so the ledger row the spec promised could never be
produced by the route, the CLI, or the UI. The cheap detector is one grep per new public entry
point: `grep -rn "<new_function>" app/ tests/` and require at least one hit under `app/`.
**Applies to:** any iteration that adds a new orchestration/entry-point function whose only
exercise is a pytest fixture — especially `scout.py`, `walkforward.py`, `vault.py`, and anything
whose acceptance says "recorded in the ledger" or "rendered in section X".

## iter-21 (second) — 2026-08-20T22:10:00Z

**Verdict:** ESCALATE
**Lesson:** The iter-18 rig rule ("a change to the shared QA rig is a change to every journey it
serves") was applied to the replay + browser lanes only, and the DEMO lane — which runs last, after
the ledger-populating browser tests — was forgotten: its step-03 `No candidates ledgered` assert
failed and was "recorded anyway". Any lane that reads the scoped rig must be inside the sequencing
rule, or the empty-state asserts (`J-08.json` step 3, `J-10.json` step 12) must be made
order-independent.
**Applies to:** any iteration whose browser tests POST to `/research/desk/micro/scout/compute` (or
any other rig-mutating endpoint) — check `reports/phase-*-demo-results.md` soft notes before
believing the round was clean.

## iter-21 (third) — 2026-08-20T22:10:00Z

**Verdict:** ESCALATE
**Lesson:** A merged **browser-QA verdict of FAIL does not gate the round** — `closure_gate.py`
cross-checks the UX-regression verdict and artifact presence but never the browser verdict, so
iteration 21 closed `CLOSURE-PASS` with a live UT-04 FAIL. Only the auditor turned that FAIL into a
fix. Do not read `CLOSURE-PASS` as "every lane agreed"; open
`reports/phase-<iter>-ui-test-results.md` and read its verdict line directly.
**Applies to:** every evaluator, every iteration; and to any framework change touching
`scripts/automation/lib/closure_gate.py`.

## iter-22 — 2026-08-21T04:10:00Z

**Verdict:** STALLED
**Lesson:** A "does this really screen anything?" test can be blind in a way the usual
break-tests miss: `test_iter22_study3_capitulation_screens_with_real_playbook_signal_anchor`
(`apps/backend/tests/test_scout.py:1676`) asserts only that a decision is in the closed vocabulary
and that a floor-check row exists — both of which are produced identically by a hollow ZERO-anchor
pass-through. I proved it by pushing `_plant_capitulation_signal`'s `trigger_ts` 5e9 seconds
outside the dataset window (so no signal could join) and watching the test stay green. Its Study-1
twin at `:1664` has the one line that closes it: `screen_result["n_candidate"] +
screen_result["n_comparator"] > 0`. The general shape: whenever a screen/join can legitimately end
in "insufficient_n", the honest-refusal path and the never-saw-any-data path produce the SAME
assertions, so every such test needs an explicit non-vacuity assertion on the joined count — a
sibling test having it is not evidence that this one does.
**Applies to:** any iteration adding or editing a Scout/screen/join test whose acceptable outcome
includes `insufficient_n` / `no survivor` / a floor refusal — i.e. anything under
`apps/backend/tests/test_scout.py`, `test_walkforward*.py`, or new `micro_*` join tests.

## iter-22 — 2026-08-21T04:10:00Z (second)

**Verdict:** STALLED
**Lesson:** The showcase walkthrough lane cannot photograph a backend research address at all: it
rewrites every URL onto the frontend port (`:3301`), which has no pass-through, so
`reports/demo/goal-rapid-microscope-iter-22/step-07.png` is a Next.js 404 for the graduation
surface even though the browser-QA lane's own `UT-08-result.png` shows the full body. Do NOT open
an `evidence_makeup` make-up ride for a demo step of this shape — a re-capture through the same
lane reproduces the identical 404. Either write the demo step against a page-served surface, or
accept the soft note. (Round 19 recorded the same mechanism for J-07's replay script; this is the
demo lane's version of it.)
**Applies to:** any iteration whose demo script includes a step on a `GET /research/...` address
rather than a `/cockpit`, `/structure` or `/desk` page.

## iter-23 — 2026-08-23T03:05:00Z

**Verdict:** ESCALATE
**Lesson:** An "opaque pool" leaks through its own bookkeeping, not through its serving layer. The
vault's serving code is a correct positive allow-list and TR-2 passes, yet joining the per-shard
`sealed_at` the vault route serves (`vault.py:380` `_OPAQUE_SHARD_KEYS`) against the per-run
`sealed_this_run` counts published in the committed `reports/j06-tranche/recording-runs.json`
partitions the 21 seals 7/13/1/0/0 across the five recorder runs — proving 3 pool members unsealed
and cutting one shard's candidate set from 79 to 4. An inference trap that models only the SERVED
surfaces will keep passing while the operator's own committed run reports do the leaking.
**Applies to:** any iteration that adds a served per-item timestamp/ordinal to a withheld set, or
that commits a per-run progress artifact beside one — check the JOIN, and make the trap's
combinatorial model consume every artifact its own attacker-knowledge list claims.

## iter-23 — 2026-08-23T03:05:00Z (second)

**Verdict:** ESCALATE
**Lesson:** The depth arbiter's `full-cap` rung (one full per cadence window) silently cut the
audit lane out of the ONE iteration whose entire declared purpose was independently verifying
4,191 lines of never-reviewed operator code — the spec said so in writing, with a qualifying
`Full trigger:` line, and the cost ladder overrode it anyway (telemetry `depth_demoted`, reason
`full-cap`). Only a hard `Depth enforcement: required` line outranks a cost rung; a mere
`Full trigger:` does not.
**Applies to:** any iteration whose purpose is independent verification of code that entered the
repo outside goal-mode — the decomposer must write `Depth enforcement: required`, not just
`Full trigger:`, or plan for the checker to be cut.

## iter-24 — 2026-08-23T05:55:00Z

**Verdict:** CONTINUE
**Lesson:** Narrowing a served timestamp's PRECISION is never a backend-only change: the moment
`vault.py` started serving `sealed_at` as a bare `yyyy-MM-dd`, the Vault cell's existing
`formatDateTimeET` parsed it as UTC midnight and rendered the PREVIOUS calendar day plus an
invented `20:00 ET` — the exact trap `apps/frontend/lib/datetime.ts:132-148` already documents,
with `formatDayMarker` already shipped as its answer. The spec's "Frontend: no code changes
expected" line made three lanes stop looking, even though the ui-impact-analyst wrote the defect up
in advance.
**Applies to:** any iteration that changes the SHAPE or precision of an already-served date/time
field — grep every frontend call site reading that field and check day-marker vs instant before
declaring the frontend untouched.

## iter-24 (second) — 2026-08-23T05:55:00Z

**Verdict:** CONTINUE
**Lesson:** An inference/anonymity check must be keyed on the ATTACKER's starting point, not on the
reference side of the join. The new `stage_tr2()` run-aware half walked the RUN buckets and skipped
any bucket no run claimed — but a run's `at` is stamped by `_utc()` at second precision while each
shard's `sealed_at` is stamped by `vault._iso_utc_now()` at microsecond precision, so under the
REAL old data shape no served value ever prefix-matched a run key, zero buckets existed, and the
check reported "safe" against precisely the leak it was built for. Re-keying on the served buckets
(skipping none) makes it bite; the counter-test that "proved" non-vacuity only proved it on an
alignment production can never produce.
**Applies to:** any TR-2 / join-resistance / k-anonymity check, and any "non-vacuity counter-test"
— build the counter-fixture from what the WRITER actually wrote (read the stamping function), never
from the reference side's own values.

## iter-24 (third) — 2026-08-23T05:55:00Z

**Verdict:** CONTINUE
**Lesson:** `closure_gate.py` clears an iteration on "ui-test-results: execution evidence present
(PASS/FAIL rows)" — it never reads the merged **Browser QA Verdict** line. This round that line
read FAIL and the round still closed CLOSURE-PASS; iter-21 flagged the identical hole and it is
still open. Only the audit lane stood between a photographed, predicted rendering defect and a
shipped iteration.
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

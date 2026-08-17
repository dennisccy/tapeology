# Goal Session rapid-microscope — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-08-16T23:11:10Z

**Verdict:** CONTINUE
**Lesson:** `apps/backend/pyproject.toml` already sets `addopts = "-q"`, so running
`pytest tests/ -q` stacks to verbosity -2 and pytest swallows even the final
"N passed, M skipped" summary line — iteration 0 had to reconstruct 2691/8 by counting
dot-grid characters. Invoke `pytest tests/` (no extra `-q`), or add `-v`, to get the count
directly. Separately: `runs/goal-rapid-microscope-iter-0/status.json` still reads
`browser_checks_run: false` after a completed browser pass (it is written at `dev_complete`
and never refreshed) — trust `reports/phase-*-ui-test-results.md` and the evidence directory,
not that flag.
**Applies to:** every iteration that records the backend suite count for J-10, and any agent
reading status.json to decide whether browser QA ran.

## iter-1 — 2026-08-17T02:20:00Z

**Verdict:** ESCALATE
**Lesson:** The mandated store-scoped browser rig (`:8301`, forced on by
`project-extensions/store-scope/store-scope.env` + `apps/backend/scripts/start_scoped_qa_backend.sh`)
sets `TAPEOLOGY_DATASET_DIR` to a fixture dir its seeder never populates with tick datasets — so a
tick-corpus panel renders an honest but empty 0/0/[] and any acceptance naming real-corpus values
(J-01's `distinct_symbol_days: 12`) is structurally unprovable through the browser lane, no matter
how correct the code is. The repo already ships usable tick fixtures at
`apps/backend/tests/fixtures/datasets/`; seed them (or scope the readiness cache and let the rig
read the real corpus read-only) BEFORE a browser acceptance depends on non-empty tick data.
**Applies to:** any iteration whose browser acceptance reads the tick corpus — J-06's vault
states, J-08's four `/desk` micro sections, and J-09's study results all hit this same wall.

## iter-2 — 2026-08-17T07:20:00Z

**Verdict:** CONTINUE
**Lesson:** A snapshot's identity tuple proves "this file was produced by this code", NOT "this
file is complete". The engine isolates observer exceptions by design, so a mid-stream raise in
`micro_observer.py` silently dropped that row and every row after it, and the short file was
persisted and re-verified as a VALID snapshot (audit B2). Any streamed research artifact needs its
own explicit completeness/failure channel (`MicroObserver.failure` → typed `MicroObserverFailure` →
build refusal) beside its identity check — and the same sweep found a sibling defect where a
session-truncated deferred construct was published as a completed observation instead of
`unavailable` (audit B1, 36 rows across all 18 datasets).
**Applies to:** any iteration persisting rows produced through the engine's `add_observer` seam or
any other exception-isolated callback — J-03's join, J-04's screens, J-05's fold outputs, J-06's
recorder chunks.

## iter-2 — 2026-08-17T07:20:00Z

**Verdict:** CONTINUE
**Lesson:** The J-10 sentinel keeps FAILING for test-rig reasons rather than product reasons: its
plan asks for `/structure` bands on PG (the rig seeds tick shards, not bar series, for PG) and for
playbook filters on the rig's default session (which has never had `Run Playbook` executed). Both
surfaces are provably fine — AAPL as-of 2026-06-22 rendered the same `300.11–302.2 Class A` band
iteration 1 recorded, in the same browser session. Separately, the QA agent's own report claimed a
ten-row J-10 "PASS … byte-identical" table while its own browser lane recorded FAIL 6/9; the
auditor caught it (F1). Pin the sentinel steps to data the rig actually holds, and always
cross-read `ui-test-results.md` before believing a QA regression table.
**Applies to:** every future iteration — J-10 is the standing required-still-passing journey, so
this fires each run until the plan is parameterized to the rig's real data state.

## iter-3 — 2026-08-17T09:05:00Z

**Verdict:** ESCALATE
**Lesson:** The engine's depth arbiter can silently downgrade a `Depth: full` spec to lean —
iter-3's telemetry records `{"from":"full","to":"lean","reason":"budget-breach"}` because iter-2
(full) overran its wall clock. A CONTINUE verdict plus a "full" depth recommendation is NOT enough
to get it back: the arbiter's `full-cap` rung (one full per 4-iteration window) would demote it
again. Only a prior **ESCALATE** (or REGRESSION, or a prior COHERENCE-FAIL) grants full
unconditionally, because that is rung 1 of the ladder in `scripts/automation/run-goal.sh:2427`.
**Applies to:** any iteration where the evaluator genuinely needs the auditor lane (provenance
ledgers, leakage rails, whole-corpus data events) — say ESCALATE, do not just recommend full.

## iter-3 — 2026-08-17T09:05:00Z (second)

**Verdict:** ESCALATE
**Lesson:** A 13-line purely additive helper in `apps/backend/app/research/micro_features.py`
(`spread_bps`) re-keyed and forced a rebuild of ALL 18 real-corpus snapshots, because
`micro_snapshots.feature_source_hash()` hashes the whole SOURCE BYTES of `micro_features.py` +
`micro_observer.py`, not the functions actually used. The rebuild is honest (an identity MISS, never
a stale served value) and value-preserving here — the row total stayed exactly 3,815,933 — but it
means any edit to those two files, even a comment, triggers a whole-corpus recompute that no lane
audits in a lean pass. Check the row total against the prior iteration's recorded number as a cheap
value-equality proxy.
**Applies to:** any iteration touching `micro_features.py` or `micro_observer.py`; budget a corpus
rebuild into the iteration's time, and re-verify snapshot row totals afterwards.

## iter-4 — 2026-08-17T16:10:00Z

**Verdict:** ESCALATE
**Lesson:** A `Frontend Present: no` iteration spec makes the browser-qa step skip the WHOLE pass —
including the required-still-passing regression set the same spec's TESTING REQUIREMENTS/TC-20
explicitly mandated (`journey-scripts/J-10.json`'s 13-step sentinel never ran, zero screenshots
exist for iter-4). The two lanes each assumed the other owned it: the QA report wrote "the
required-still-passing set re-verification is browser-qa-agent's scope, not this QA pass", and
browser-qa then skipped on the frontend flag. A regression set is not a frontend-delta question —
whenever a spec names required-still-passing journeys, the browser lane must run them regardless of
`Frontend Present`.
**Applies to:** any backend-only iteration (`Frontend Present: no`) whose spec still names
required-still-passing journeys or a sentinel script — i.e. every iteration of J-05/J-06/J-07/J-09
in this era.

## iter-4 — 2026-08-17T16:10:00Z

**Verdict:** ESCALATE
**Lesson:** A hash-chained append-only ledger's `prev_hash` walk catches in-place edits and mid-file
deletions but is BLIND to tail truncation — erasing the newest row leaves a chain that verifies
perfectly clean while the denominator silently shrinks, which is exactly the era's cardinal
anti-goal. It needs a separately-persisted tail anchor (`chain_head.json` with `{row_count,
head_hash}`, written AFTER the row it commits to so a crash can only leave the ledger longer than
the anchor). Equally: a "variants tried" denominator must count DISTINCT candidate identities, not
ledger rows, or every re-run of the same grid inflates it and eventually trips the hard cap.
**Applies to:** every future hash-chained ledger in this era (`walkforward.py`'s fold ledger, the
vault exposure ledger, `micro_graduation.py`'s bundle) — copy `scout_ledger.py`'s anchor +
`distinct_variant_count` pattern rather than the pre-audit chain-only design.

## iter-5 — 2026-08-17T20:30:00Z

**Verdict:** ESCALATE
**Lesson:** Iteration 4's browser-lane lesson was addressed to the wrong audience, so writing it in
bold into iteration 5's TESTING REQUIREMENTS changed nothing: `scripts/automation/browser-qa-phase.sh:52`
short-circuits to N/A stubs whenever the plan says `Frontend Present: no`, **before browser-qa-agent
is ever dispatched** — no agent reads the spec paragraph. Worse, the safeguard for exactly this case
already exists on paper and is dead code: `run-goal.sh:2548` exports `CHAIN_GOAL_TARGET_JOURNEYS`
with the comment "forces the browser lane whenever this iteration names journeys — even if the plan
mis-states Frontend Present: no", and a repo-wide grep finds **one write and zero reads** —
`detect_frontend_in_plan` (`lib/common.sh:1502`) only greps for "frontend present: yes". The one
remedy fully inside the loop's control is to declare `Frontend Present: yes` in any spec that names
required-still-passing journeys with browser acceptances; the durable fix is to make
`detect_frontend_in_plan` (or the browser-qa skip branch) actually read that export.
**Applies to:** every `Frontend Present: no` iteration spec that names required-still-passing
journeys or a sentinel script — i.e. J-06, J-07 and J-09 in this era; also any framework maintenance
pass touching browser-lane gating.

## iter-5 — 2026-08-17T20:30:00Z (second)

**Verdict:** ESCALATE
**Lesson:** An append-only ledger that is idempotent *everywhere else* can still fabricate a verdict
through the one write path that is not. `walkforward_ledger.append_fold_result` appended a fresh row
per call while `register_fold_spec` replayed and the exposure-registry seeding was re-seed-guarded —
so pressing the diagnostic Compute button twice doubled all five folds and converted the sequence's
honest "2 < 3 sufficient folds — refused" into a computed verdict over `n_sufficient_folds: 4` built
from 2 real folds counted twice, plus a 1.0-vs-0.0 decay recency line invented from the duplicate.
The era's "denominator never shrinks" rail has a mirror the code did not enforce: it must not
spuriously GROW. Key a replay branch on the identity of one evaluation act (`sequence_id`,
`fold_index`, `spec_hash`) and disclose `appended` vs `replayed` in the run log.
**Applies to:** every remaining hash-chained ledger in this era (the vault exposure ledger, J-07's
graduation bundle) and any statistic whose floor is a row COUNT rather than a distinct-identity count.

## iter-6 — 2026-08-17T23:30:00Z

**Verdict:** ESCALATE
**Lesson:** Browser evidence has now been lost or corrupted three iterations running for three
DIFFERENT mechanical reasons — `Frontend Present: no` short-circuiting the whole lane (iters 4-5),
and now `merge_ui_test_results.py:64` accepting a verdict cell only as a bare `PASS`/`FAIL` token, so
a markdown-emphasised `**FAIL**` parsed as *no verdict at all* and `compute_overall` derived a green
headline from the surviving PASS rows (the source file's own FAIL headline is consulted only when no
row parses). That green headline propagated into `status.json` `qa_verdict` and past closure; only
the independent auditor caught it. Treat any merged browser headline as unverified until the LLM
lane's own `...-ui-test-results.llm.md` verdict line is read directly.
**Applies to:** every iteration that dispatches browser-qa; any evaluator reading
`reports/phase-*-ui-test-results.md`

## iter-6 — 2026-08-17T23:30:00Z (second)

**Verdict:** ESCALATE
**Lesson:** "The typed refusal now has ≥1 call site in `app/`" is NOT the same claim as "the goal's
named refusal is reachable". Wiring `require_sufficient_sessions_for_folds` defensively into the one
existing fold-building entry point (`walkforward.py:1148`, playbook corpus only) closed the iteration's
DEFINITION OF DONE checkbox while leaving goal.md J-05's acceptance sentence — "the tick-family fold
request returns the typed floor-refusal naming `11 < 105`" — vacuous, because no route, CLI flag, or
function in `app/` takes a corpus or family parameter. When an acceptance sentence names a SPECIFIC
input ("the tick family", "`11 < 105`"), a guard that can only ever see a different input does not
satisfy it. Related: a UI test plan can demand values the rig it also mandates is designed never to
produce (`qa_playbook_iter7_fixture_scoped_backend.sh` seeds 2 PG fixtures; UT-02 demanded 12/18) —
that reads as a product FAIL but is an expectation defect.
**Applies to:** any iteration closing an "unwired guard / zero call sites" gap; any iteration whose
browser acceptance names concrete corpus values while using the store-scoped rig

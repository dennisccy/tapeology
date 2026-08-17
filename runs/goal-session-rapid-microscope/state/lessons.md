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

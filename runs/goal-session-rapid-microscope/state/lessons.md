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

## iter-7 — 2026-08-18T01:30:00Z

**Verdict:** CONTINUE
**Lesson:** A field addition can be perfectly additive for READERS and still destroy an identity
guarantee for WRITERS. `datasets.py`'s Card-5.1 preservation keys were optional, absent-key
default-`None`, and provably byte-identical on load for all 18 real datasets — yet they silently
entered `_content_checksum`, the sole enforcement of "the split tag is frozen at registration", so
one tape re-fetched through the now-populating Alpaca adapter would hash to a second identity and
register again under a different split (train + holdout contamination). Review and QA both passed
it; only the independent auditor caught it. The fix is a tape-only projection (`_tape_identity_rows`)
applied symmetrically on the write side and the on-load verify side.
**Applies to:** any iteration adding a field to a record type whose bytes feed a checksum, content
hash, dedupe key, or identity tuple — `datasets.py`, `micro_snapshots.py`, any `*_ledger.py`. Ask
explicitly: "does this new key change what the identity function sees?", and if the new data is
metadata ABOUT the payload rather than payload, project it out of the identity before hashing.

## iter-8 — 2026-08-18T04:20:00Z

**Verdict:** ESCALATE
**Lesson:** An evaluator's `Depth Recommendation: full` does NOT bind the engine — iteration 7
recommended full, and the deterministic depth arbiter demoted iteration 8 to lean anyway
(telemetry `iter_dispatch depth=lean`; engine.log "spec asked FULL but the deterministic ladder
demotes it to LEAN (reason: budget-breach)"). Only a `CONTINUE`→`ESCALATE` verdict change grants
a full pass (engine.log line 1074: "FULL pass granted (reason: prior-verdict-ESCALATE)"). So when
an iteration genuinely needs the independent auditor, the depth line is not enough — the verdict
must carry it, and the reason must be stated on its own merits.
**Applies to:** any iteration whose spec declares a `Full trigger` and whose prior iteration ran
over the wall-clock budget — i.e. every remaining iteration of this era.

## iter-8 — 2026-08-18T04:20:00Z

**Verdict:** ESCALATE
**Lesson:** Adding an optional `list` field to a `frozen=True` dataclass silently destroys its
hashability, and the breakage is invisible until the first writer actually populates the field —
iter-7 added `conditions: list[str] | None` to `TradeEvent`/`QuoteEvent` and every test stayed
green because nothing populated it; iter-8's recorder was the first caller that would have.
`field(default=None, hash=False)` fixes it while leaving `__eq__` untouched (a hash coarser than
equality is legal). Worth checking BEFORE the first populating writer lands, not after. Note also
that nothing in `app/` currently calls `hash()` on these events, so the fix is defensive — verify
that claim by grep rather than assuming a fix is load-bearing.
**Applies to:** any iteration adding an optional container field (`list`/`dict`/`set`) to a frozen
dataclass in `apps/backend/app/providers/` or `app/research/`.

## iter-9 — 2026-08-18T17:05:00Z

**Verdict:** CONTINUE
**Lesson:** Per-record minimization does not imply set-level minimization: every served field of a
sealed shard can be opaque while the COMPLEMENT hands over the whole secret. `vault.py`'s §7.5
whitelist is genuinely correct per shard (I sealed a throwaway and confirmed no symbol/date/raw
id/raw checksum/exact count is served), yet closing the public `GET /research/datasets` listing
under the universe's cartesian product and subtracting recovers sealed membership exactly — 5 of 5
in the auditor's probe, WITH the B1 rule-withholding fix already in place. The tell is structural:
any surface publishing an EXPECTED set (a universe rule, or a cartesian shape TR-4 forces the batch
to fill) sitting beside a surface publishing the ACTUAL set is a subtraction oracle, and no amount
of field-level opacity in the new module can close it.
**Applies to:** any iteration adding a "hidden/held-out/sealed" state beside an existing public
listing — before trusting a minimization sweep, ask what the complement reveals, and attack your own
fix before writing it up.

## iter-9 — 2026-08-18T17:06:00Z

**Verdict:** CONTINUE
**Lesson:** When an in-iteration fix round lands AFTER the browser evidence was captured (here: r4
edits at 14:14–14:34 versus screenshots at 05:55–09:34), "browser layer is `unknown`" is the safe
call but often not the true one. A.6 says evidence expires with CHANGE, not time — so the cheap
decisive move is to re-derive the photographed values under the CURRENT code and compare. I ran
`build_readiness` post-r4 against BOTH the rig fixture store and the operator's real store and got
byte-identical values to the screenshot (1/2/1.75/0.0045 and 12/18/1173.49/3.0089), because r4's
additions are all-zero while nothing is sealed and `distinct_datasets` moved from `len(records)` to
`len(shards)` — identical when nothing is withheld. That turned a would-be `unknown` into a defended
`passing` in minutes, without a browser re-run.
**Applies to:** any iteration with fix rounds after the QA/browser lane — especially r-revision
rounds whose changes are inert until some future state exists; also any journey whose module changed
after its screenshot, where a lane row says DEFERRED-BUDGET.

## iter-10 — 2026-08-18T22:15:00Z

**Verdict:** ESCALATE
**Lesson:** The era's own T-1 rule ("ambiguous ⇒ DROP + owner ruling, never improvise") lost to
test-first pressure: spec §8 names a sealed-shard pass/fail verdict and a "proposed confirmation
boundary" without defining either, and because TC-2/TC-3/TC-6 could not pass without them, the
developer invented both (a caller-supplied `passed: bool` on
`micro_graduation.record_sealed_evaluation`, and "latest already-consumed evidence timestamp").
Both were disclosed and are unreachable today, but the pattern is the danger: whenever a
test-first contract encodes a spec gap as a TC scenario, the TC itself becomes the pressure that
converts "stop and ask" into "invent and disclose". A TC that cannot be satisfied without
inventing a rule is a signal to drop the TC, not to invent the rule.
**Applies to:** any iteration whose iter spec writes TC scenarios over an underspecified section
of `docs/rapid-validation-spec.md` — especially J-06 step 4/5, J-08, and any future sealed-shard
evaluator that wires a real verdict in front of `record_sealed_evaluation`.

## iter-10 (second) — 2026-08-18T22:15:00Z

**Verdict:** ESCALATE
**Lesson:** `micro_graduation.py` turns out to be r5-compatible by construction, and the reason is
worth keeping: it records a `dataset_id` only after `vault.build_vault_state` already reports that
shard `exposed` and bound to that exact `family_root_id` (evaluator re-proved this by claiming a
verdict against a still-sealed shard and being refused). Any surface that publishes identities
ONLY as a downstream consequence of a recorded exposure event cannot leak pool membership — the
opposite of the enumerate-then-filter shape that produced the cartesian-subtraction leak in
`GET /research/datasets`. Prefer "publish what the exposure ledger already released" over "list
everything, then subtract the withheld".
**Applies to:** any iteration adding a surface that touches vault-eligible shards — the r5
implementation itself, J-08's four `/desk` sections, and the four new MCP proxies.

## iter-11 — 2026-08-19T09:10:00Z

**Verdict:** CONTINUE
**Lesson:** Widening ONE side of a paired mechanism re-opens the very leak it closes, through the
twin you left narrow. This iteration broadened *withholding* to universe-RULE membership
(`vault.unresolved_pool_universe_by_dataset_id`) but left the *reveal* gate
(`vault._fully_exposed_universe_ids`, `vault.py:926-938`) ledger-row-only — so once every
ledger-tracked shard is exposed, `GET /research/desk/micro/vault` publishes the complete
`symbol_rule`/`date_rule` while untracked pool members are still hidden, restoring the exact
two-GET subtraction attack iteration 9 closed. Same shape in two other places in the same diff: a
new vault predicate added without r6 §7.8's `verify_chain()` rule that now governs vault
predicates, and a field mandated as an "aggregate" that stops being one at n=1. Whenever a diff
broadens a predicate, grep for every OTHER predicate keyed on the same concept and widen or
consciously defer each by name.
**Applies to:** any iteration touching `vault.py`, `micro_readiness.py`, `micro_snapshots.py` or a
withhold/reveal/exposure predicate — the r7 nonced-commitment build, J-06 steps 4-5, and J-08's
four `/desk` sections plus its four MCP proxies.

## iter-11 (second) — 2026-08-19T09:10:00Z

**Verdict:** CONTINUE
**Lesson:** A mid-session owner ruling can land in the working tree and still be described as "an
open owner question" by the phase spec built against it — and that stale sentence propagates
unchallenged through decomposer, developer, reviewer and QA. Here r6 §7.8 (corrupted vault ledger
⇒ fail closed) was ruled 2026-08-18 and written into `docs/rapid-validation-spec.md` in the same
tree, while `docs/phases/goal-rapid-microscope-iter-11.md`'s OUT OF SCOPE still listed it among
"the two remaining owner questions"; only the independent auditor caught the contradiction, and the
consequence was a new predicate shipped without the fail-closed rule that already governed it.
Read the spec's own revision header for rulings dated AFTER the prior iteration before trusting any
carried "still open" list. Cheap companion check: `md5sum` the whole evidence directory — this run
had three PASS rows citing byte-identical blank images and a fourth citing the wrong panel.
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

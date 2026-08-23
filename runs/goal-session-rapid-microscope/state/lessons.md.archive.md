# lessons.md — archive

Entries moved out of `lessons.md` by scripts/automation/lib/condense.sh (maintenance protocol §4).
Append-only: nothing here is ever deleted or rewritten.

<!-- condense.sh 2026-08-20T08:10:18Z: moved 21 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-22T21:16:06Z: moved 11 entries (keep-iters=5) -->

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


<!-- condense.sh 2026-08-23T21:16:11Z: moved 12 entries (keep-iters=5) -->

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


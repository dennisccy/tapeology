# Iteration 10 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

J-07 "Graduation — provenance in, nothing laundered out" is done and I proved it myself: I ran the
whole four-step climb against a throwaway store, outside the coder's own tests, and then tried to
break it four ways — it refused all four. Nothing else moved, nothing broke, and the frozen parts
are still frozen. I am asking for the full pipeline next time for one specific reason: the written
spec leaves two things undefined, the coder invented answers for both instead of stopping to ask
you, and the next piece of work is the vault's central promise, where the independent checker is
the only step that has ever caught this kind of mistake.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | reports/qa/goal-rapid-microscope-iter-10-evidence/J-01-verify.png (opened: /desk with every kept panel + Microscope Readiness reading "today, none") |
| J-02 The micro observer | passing | passing | reports/qa/goal-rapid-microscope-iter-10-evidence/J-02-verify.png; its own files byte-untouched (git status) |
| J-03 Structure x flow | passing | passing | reports/qa/goal-rapid-microscope-iter-10-evidence/J-03-verify.png; micro_join.py byte-untouched |
| J-04 The Scout and the ledger | passing | passing | reports/qa/goal-rapid-microscope-iter-10-evidence/J-04-verify.png; evaluator re-exercised distinct_variant_count (union-N 2, the kill counted) |
| J-05 The walk-forward engine | passing | passing | reports/qa/goal-rapid-microscope-iter-10-evidence/J-05-verify.png (opened); evaluator re-ran sequence_verdict + the voiding gate directly |
| J-06 The recorder and the Vault | partial | partial (re-scored against the NEW r5 goal text; spec_hash c517119586 → 436653d6b7) | reports/qa/goal-rapid-microscope-iter-10-evidence/J-06-verify.png; steps 4/5 absent — no micro_vault / micro_scout / micro_graduation directory under apps/backend/.data (evaluator's own ls) |
| **J-07 Graduation** | **failing** | **passing** | reports/qa/goal-rapid-microscope-iter-10-evidence/UT-J-07-result.png (opened) + the evaluator's own four-state walk + four adversarial refusals + 19/19 graduation tests inside its own 3,185-test suite run |
| J-08 The surface and MCP v6 | failing | failing | out of scope; EXPECTED_TOOLS still 22 names, zero frontend files changed (git status) |
| J-09 The pilot studies | failing | failing | out of scope; .data/micro_scout absent, so no study spec is ledgered anywhere |
| J-10 The kept product stands | partial | partial | reports/qa/goal-rapid-microscope-iter-10-evidence/J-10-verify.png (opened: referee panels render); traps still 19 of 22 (TR-3, TR-17, TR-22 absent by name); deterministic-rerun check still not run |

Deterministic replay ran for all seven required-still-passing journeys and passed 7/7 — no row was
cut for time this iteration (unlike iterations 8 and 9). No `browser-infra.json` token and no
`journeys-changed.md` drift note exist for this iteration.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report.md CLEAN over the product diff (tracked + 2 untracked). No config/env file in the 6-file change list. `micro_graduation.py` never reads, logs or serves the vault secret — it calls only `vault.build_vault_state`. The test file's `_FIXTURE_VAULT_SECRET` is a literal fixture value, not the real `TAPEOLOGY_VAULT_SECRET_FILE`, which was not touched. |
| Paid / external SaaS | OK | scan-report CLEAN; no manifest file in the diff; the new module imports only stdlib (hashlib, json, os, datetime, pathlib) plus sibling research modules. |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff. |
| Fabricated / substituted data | OK | `GET /research/desk/micro/graduation` returns an honest empty state, and I confirmed the emptiness is real: `apps/backend/.data` has no `micro_graduation` directory. `build_export_bundle` returns honest empties and a `None` boundary when no evidence exists (verified in my own run). |
| No execution path, ever | OK | no brokerage/order code added; `test_no_execution_path.py` green inside my own full-suite run. |
| No profit claims / no advice | OK | the module's only two served strings pass the copy-discipline lexicon (its own test asserts `find_violations == []`); I read both strings. |
| Frozen foundations (fingerprint, referee, engine, kept surfaces) | OK | `Config().config_fingerprint()` prints `08e471b10130e1e2` (my own run); all six `referee_*.py` sha256 hashes compared one by one against the iteration-0 listing in `docs/handoffs/goal-rapid-microscope-iter-0-dev.md` — all six MATCH; git status shows no engine, frontend or referee file changed. |
| Hold-out-only promotion | OK | champion pointer untouched; no `pnl_scan` change in the diff. |
| No lookahead | OK | the new module computes no as-of value; it reads already-ledgered rows only. |
| Single source of truth | OK | coherence.md = COHERENCE-PASS; I read the code myself: the survivor rule is delegated to `walkforward.sequence_verdict`, shard state to `vault.build_vault_state`, union-N to `scout_ledger.distinct_variant_count` — none reimplemented. |
| Deterministic and seeded | OK | no randomness in the module; the only wall-clock use is a caller-overridable `evaluated_at` provenance stamp, identical to `vault.py:301`'s established `_iso_utc_now` pattern; a rebuilt export bundle is byte-identical because every field comes off ledgered rows. |
| Read-only MCP | OK | no MCP file changed; `EXPECTED_TOOLS` still exactly 22 names. |
| Immutable data / append-only | OK | the graduation ledger exposes only `append_row` on the shared `HashChainedLedger`; no update/delete/supersede path; no dataset or bar write path added. |
| Persistence stays scoped | OK | no ambient recording; the one new route is a read-only GET that never computes. |
| No exploratory read of a sealed shard | OK | I probed it: a verdict claimed against a still-sealed, never-exposed shard was REFUSED. |
| Sealed exposure single-shot, never a second draw | OK | I probed it: a second, DIFFERENT verdict for the same (family, shard) was refused and the row count stayed 1. |
| A recorded tranche is one opaque research pool (r5) | OK for this diff, UNIMPLEMENTED overall | r5 names `graduation` among the surfaces its inference trap must sweep. The new route can only ever publish an ALREADY-EXPOSED shard's identity, because `record_sealed_evaluation` refuses unless the vault already reports that shard `exposed` and bound to that exact family (I re-proved this). The r5 work itself — one opaque pool, aggregate-only readiness on both sides, aggregate-only recorder progress, the widened TR-2 — is NOT built; open minor item, hard gate on J-06 step 4. |
| Evidence classes never mix | OK | I probed it: a diagnostic-only twin with three otherwise-perfect folds stayed `exploratory` with no ledger row written. |
| No fold geometry change after fold 1 without a voiding event | OK | I probed it: after `record_voiding_event` on the corpus, three otherwise-perfect folds no longer advanced the candidate. |
| No threshold/grid chosen from outcomes | OK | the module holds no threshold of its own; its guard test is proven able to fail on seeded violations. |
| The denominator never shrinks | OK | my own bundle carried union-N = 2 including the `killed_null` trial; an unrelated family's trial did not leak in. |
| The accessor is the only data door | OK | the module imports no `micro_accessor` and opens no event data; I read its import list directly. |
| The 12 legacy tick symbol-days stay exploratory / the ~150 gate never lowers | OK | `micro_readiness.py` byte-untouched this iteration. |
| Referee modules byte-untouched | OK | all six hashes identical to iteration 0 (checked one by one). |
| Vault secret never in repo, log, payload or screenshot | OK | the served body contains no secret; the screenshot shows only the empty state. |
| Enhancement loop stays inside its box | OK | the `AUTO:journeys` marker block is still EMPTY; this iteration's `docs/goal.md` edit is the OPERATOR's own r5 ruling applied by the pump, not a proposer edit. |
| Host-guard caps | OK | no host-guard file changed; no cap widened. |
| **Constraints — "the spec is canonical … never improvise"** | **MINOR VIOLATION, NEW, OPEN** | Spec §8 defines neither the sealed-shard pass/fail verdict nor a formula for the "proposed confirmation boundary". Both were INVENTED rather than dropped for an owner ruling — disclosed in the handoff and independently confirmed as real spec gaps by the reviewer. Inert today (no operator-facing route reaches them; zero sealed shards; zero graduation rows on disk), permanent once real evidence flows. |

Carried open minor items, all unchanged in code this iteration: the one-quote-early depletion
timing stamp (owner-owed since iteration 2); the vault withholding predicates failing OPEN on a
corrupted ledger (still the only item of its family with no owner ruling); and the two items the
r5 ruling DECIDED but nobody has built yet (the opaque-pool closure, and the disclosure + guard
for the seal-unaware legacy Referee readiness metric).

## Next-Step Recommendation

Build your r5 decision — "a recorded batch is one opaque pool" — as the next round, under the full
pipeline with the independent checker, and scope it to that one step only. Three concrete things:
the corpus page must stop listing recordings one by one on EITHER side while any member of a batch
is still unopened; the recording-progress view must show only totals, never a name, a date or an
id; and the trap that guards this must be rewritten so that it actively tries to work out which
recordings are hidden and fails to. Do NOT let that round record real tape — your ruling settles
the design, but none of it is built, and one question of the same family is still open. Please
decide three things when you can: (1) should a damaged vault record make everything refuse (safe)
or make everything open (what happens today)? (2) who decides whether a sealed recording's test was
passed or failed — today the program simply believes whoever calls it; (3) the timing stamp that is
one quote too early, waiting since round 2. After r5 lands, the natural order is J-08 "The surface
and MCP v6" — the funnel is invisible on screen today — then J-09 "The pilot studies", then a
hardening round for the three traps still missing by name (TR-3, TR-17, TR-22) and the
byte-identical re-run check that has never been run this era.

## Halt Justification (if halting)

Not halting. This is an ESCALATE, which continues the loop at the deeper setting rather than
stopping it. Two things make the deeper setting the right call, and neither is a general
preference. First, this round genuinely surfaced ambiguity: the written spec leaves the single
most consequential act in the whole funnel — deciding whether a sealed recording's test was passed
or failed — with no owner at all, and the code now simply believes whoever calls it. Second, the
work that comes next is the vault's central promise, and the independent checker is the only step
in this session that has ever caught a fault of that class; it found this very problem by attacking
its own earlier fix. A round without it would ship that promise unexamined.

# Iteration 13 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round fixed a real safety hole in the vault, and the fix holds. I did not take any report on
trust: I re-ran the whole test suite myself (3,228 tests, 3,220 passed, 8 skipped, 0 failures) and I
wrote my own attack program against the running code. The destroyed-record hole that has been open
since last round is now genuinely closed — a damaged record can no longer make a locked-away item
quietly become an ordinary public one, and I could not break it. Three separate ways of laundering a
record were found and closed inside this one round, by three different people, and the last one was
found only by the independent checker after everyone else had passed the work. Nothing kept has
regressed. But one serious weakness is still open by the owner's own decision, and it is the reason
my verdict line says "escalate": the next round must keep the independent checker.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing | reports/qa/goal-rapid-microscope-iter-13-evidence/UT-06-result.png (opened; Corpus Totals 5 rows, Legacy Tick Shards table, floors all unmet, "No integrity errors.") + my own re-derivation against the real store |
| J-02 The micro observer | passing | passing (capture defect) | reports/qa/goal-rapid-microscope-iter-12-evidence/J-02-verify.png — the iter-13 file the results table cites does not exist on disk |
| J-03 Structure x flow | passing | passing (capture defect) | reports/qa/goal-rapid-microscope-iter-12-evidence/J-03-verify.png — same missing iter-13 capture |
| J-04 The Scout and the ledger | passing | passing (capture defect) | reports/qa/goal-rapid-microscope-iter-12-evidence/J-04-verify.png — same missing iter-13 capture |
| J-05 The walk-forward engine | passing | passing (capture defect) | reports/qa/goal-rapid-microscope-iter-12-evidence/J-05-verify.png — same missing iter-13 capture |
| J-06 The recorder and the Vault | partial | partial (content advanced) | my own probes P1/P2/P4/P5 against `apps/backend/app/research/vault.py`; steps 4-5 untouched by design |
| J-07 Graduation | passing | passing (NOT tested — DEFERRED-BUDGET) | reports/phase-goal-rapid-microscope-iter-13-ui-test-results.md, Deferred table; spot-check: `/research/desk/micro/graduation` returns 200 |
| J-08 The surface and MCP v6 | failing | failing | confirmed unbuilt on disk myself: no four MCP tools, `EXPECTED_TOOLS` still 22, no new desk section testids |
| J-09 The pilot studies | failing | failing | confirmed unbuilt on disk myself: no scout store in the real `.data` directory |
| J-10 The kept product stands | partial | partial (re-scored) | reports/qa/goal-rapid-microscope-iter-13-evidence/UT-08-result.png, UT-04-result.png, UT-05-result.png (all opened) |

Notes on the table:

- **J-02 through J-05 — a missing photograph, not a broken product.** The replay lane reported PASS
  for all five and the merged results table cites
  `reports/qa/goal-rapid-microscope-iter-13-evidence/J-01-verify.png` … `J-05-verify.png`. **None of
  those five files exists on disk.** Rounds 11 and 12 both wrote them, so this is new. I did not
  downgrade the four journeys, because their own program files were not touched this round — the
  only two product files that changed are `vault.py` and one docstring in `micro_routes.py` — and my
  own full test run covers each of their test modules. I marked them for a make-up photograph.
- **J-07 was not tested this round.** Its row reads `DEFERRED-BUDGET`: the round ran over its clock
  and its re-check was cut. It keeps its previous status; it cannot count toward finishing the goal
  until a later round re-checks it.
- **J-10 was re-scored against the current goal text**, which the owner's ruling changed this round
  (required trap list 28 → 29). By my own count of the test folder the traps stand at **24 of 29**
  (missing TR-3, TR-22, TR-23, TR-24, TR-26). The "23 of 28" in the round's own plan is out of date.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | `iter-13/scan-report.md` CLEAN; the changed-file list holds no config or env file |
| Paid / external SaaS dependency | OK | no manifest (`requirements*.txt`, `pyproject.toml`, `package.json`) in the diff; no vendor call made |
| License change | OK | no LICENSE or license field in the diff |
| Fabricated or substituted data | OK | real store byte-unchanged (18 datasets, newest file 15 July, no `micro_vault`); the browser rig's 1 symbol-day / 2 PG shards is the scoped fixture rig and the report says so; `SIM-BUYER` is a labelled Simulated-mode ticker, not substituted real data |
| Frozen foundations *(critical)* | OK | fingerprint `08e471b10130e1e2` from a live import; all six `referee_*.py` SHA-256 identical to the iteration-0 listing; `micro_chain_ledger.py` byte-untouched; zero new `Config` fields; zero frontend files |
| Read-only MCP *(critical)* | OK | `EXPECTED_TOOLS` parsed at 22; no MCP module in the diff |
| Single source of truth *(critical)* | OK | `iter-13/coherence.md` = COHERENCE-PASS; the deleted state has one former writer and no orphan |
| Immutable data *(critical)* | OK | the one sanctioned whole-file rewrite is now strictly narrower; real store untouched |
| No exploratory read of a sealed shard *(critical)* | OK (with the open item below) | I proved every predicate stays fail-closed on a corrupt ledger |
| Sealed exposure single-shot *(critical)* | OK (with the open item below) | my own new probe: a recovery cannot revert a recorded exposure |
| One opaque research pool *(critical)* | OK | the shard serializer became a positive allow-list, so an unknown state now serves only the opaque form — strictly safer |
| 12 legacy symbol-days permanently exploratory *(critical)* | OK | I read the real store: all 18 shards `exploratory` |
| ~150-symbol-day gate never lowered *(critical)* | OK | I read it: gate 150, three study floors unmet at 11 of 60 sessions |
| Referee modules byte-untouched *(critical)* | OK | six hashes match iteration 0 exactly |
| Vault secret never in repo/log/payload/screenshot *(critical)* | OK | scan CLEAN; only test fixture secrets appear, in tests |
| No execution path / no profit claims / no lookahead / hold-out-only promotion / deterministic *(critical)* | OK | none of their code was touched; the on-screen comparison still carries the "simulated — not indicative of live results" line and the champion is still `v1`/`default` |
| Proposer stays inside its box *(critical)* | OK | the `docs/goal.md` change is only the owner's trap-range edit (28 → 29); the `AUTO:journeys` block was not touched |

**Violations after this round: one closed, one new, four open in total, none critical.**

- **CLOSED** — the destroyed-record hole I found myself last round. Proved closed by my own program,
  not by reading a report.
- **NEW, open, minor, and deferred by the owner's own ruling** — deleting the record file **and** its
  companion stamp together (two plain deletes, no skill required) makes the integrity check report
  "clean" over an empty record, and every locked-away item becomes lockable again as if new. I
  reproduced this end to end. It cannot happen today: nothing is registered, nothing is locked away,
  and the vault folder does not exist in your real data. **But it must be fixed before any real tape
  is ever recorded**, because tape locked away by mistake cannot be un-disclosed.
- Three older minor items stay open and unchanged: a timing edge in one liquidity measurement, one
  frozen judge file that counts locked-away items toward a threshold (you ruled: keep frozen,
  disclose), and one place where a coder filled a gap in the written spec instead of asking.

## Next-Step Recommendation

Build **J-08 "The surface and MCP v6"** next — the four new Desk panels and the four new read-only
tools — and run it as a **full round with the independent checker**. That is why my verdict line
says "escalate" rather than "continue": in this session a plain request in words has been cut for
time twice, and only the verdict line is honoured by the machine. This is not a formality. In this
session the checker has caught a serious fault after the review and the quality check had BOTH already
passed the same code at rounds 2, 4, 5, 7 and 13 — this round's was a CRITICAL one that deletes a
locked-away record — and it found further faults at rounds 9 and 11. J-08 is exactly where
that matters, because those panels are the ones that must never show a complete list of which
recordings are locked away and which are not — the single rule this era treats as most important.

Two things about how to shape that round. First, **split it in two**: one round for the four panels,
one for the four tools and the contract bump. Your own earlier ruling was to keep rounds small rather
than raise the clock, and it has worked — but this round still ran over and paid for it by dropping
two checks. Second, **do not record real tape yet.** J-06's remaining steps must stay shut until the
newly-recorded weakness above is fixed. I recommend scheduling that fix — a real identity record for
the vault's ledger — **before** the real-tape step, not after, and the independent checker
recommends the same.

Carry three small passengers, never a round of their own: re-take the five missing replay
photographs for J-01 through J-05; re-check J-07, which was cut for time this round; and give the
harness a durable place to record that J-07 has no replay script, because that note has now been
auto-deleted three times.

## Halt Justification (if halting)

Not halting. The loop continues at full depth.

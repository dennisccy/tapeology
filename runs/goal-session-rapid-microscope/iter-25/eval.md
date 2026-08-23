# Iteration 25 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

The last non-green journey turned green. J-06 "The recorder and the Vault" now has the photograph
it was missing: I opened the picture myself and the Vault's "Sealed at" cell reads a plain date,
`2026-05-01`, with no clock time — the exact thing that showed up wrong one round ago. In the same
picture a second, still-sealed recording appears, and every column that could name it — dataset,
family, symbol, session date, both timestamps, checksum — reads "sealed — opaque" instead. I did not
stop at the picture: I ran the round's two new tests, and then I ran my own experiment that the round
did not ask for. I planted the same sealed recording, saw it served with only six harmless fields and
saw the direct-download address answer 403; then I formally released the same recording through the
real product functions and watched the same two places flip to showing the symbol, the dataset id and
a 200. So the secrecy is a real switch, not a picture of one. All ten journeys are now green.

I am still not calling the era finished, for two separate reasons. First, eight older minor
rule-breaks remain open on the record, and my own rule says the era cannot be certified while any is
open. Second — and this is my finding, no lane raised it — one of those eight was excused years-ago
in this session on the grounds that "the real store holds no sealed recordings, so nothing can be
hurt". That is no longer true: your real store now holds twenty-one sealed recordings, so the excuse
has expired even though the defect has not changed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (replayed) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-01-verify.png |
| J-02 The micro observer | passing | passing (replayed) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-02-verify.png |
| J-03 Structure x flow | passing | passing (replayed) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-03-verify.png |
| J-04 The Scout and the ledger | passing | passing (replayed) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-04-verify.png |
| J-05 The walk-forward engine | passing | passing (replayed) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-05-verify.png |
| **J-06 The recorder and the Vault** | **partial** | **passing** | reports/qa/goal-rapid-microscope-iter-25-evidence/UT-J-06-result.png + J-06-vault-sealed-opaque.png (merged results row UT-J-06 PASS); both opened by the evaluator |
| J-07 Graduation | passing | passing (NOT re-tested — see note) | reports/qa/goal-rapid-microscope-iter-24-evidence/UT-08-result.png (iter-24; durable, methodology A.6) |
| J-08 The surface and MCP v6 | passing | passing (replayed; spot-checked) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-08-verify.png |
| J-09 The pilot studies | passing | passing (replayed; golden run by the lane for the first time) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-09-verify.png |
| J-10 The kept product stands | passing | passing (replayed; spot-checked) | reports/qa/goal-rapid-microscope-iter-25-evidence/J-10-verify.png |

Merged browser QA: **PASS, 9/9, 0 skipped, 0 FAIL rows, 0 `DEFERRED-BUDGET` rows**
(`reports/phase-goal-rapid-microscope-iter-25-ui-test-results.md`).

Notes on the evidence, stated plainly rather than implied:

- **J-06 (status change) — walked in full.** Merged row UT-J-06 PASS. I opened both screenshots and
  cropped/enlarged the shard table myself: `Sealed at` = `2026-05-01` (exposed shard,
  `iter18-qa-universe`) and `2026-06-07` (new sealed shard, `iter25-qa-sealed-only-universe`), both
  bare dates with no `T`, no colon and no clock time (TC-3); the sealed row shows `sealed — opaque`
  in all seven identity columns while the exposed row shows real values (TC-2). I ran the two new
  tests (`pytest tests/test_vault.py -k "iter25 or sealed_at"` → 5 passed) and then my own
  non-vacuity probe: planted shard → six opaque keys, no symbol, no dataset id,
  `GET /research/datasets/<id>` → **403**; same shard after a REAL `assign_shard`+`expose_shard` →
  thirteen keys including symbol/dataset_id/session_date and **200**. Opacity is a live conditional.
- **J-06's real-tranche half rests on durable evidence, not on this rig.** The fixture rig proves the
  screen behaviour; the tranche itself was verified at iter-23/24. I re-checked it today rather than
  inheriting it: `apps/backend/.data/micro_vault/vault_shard_ledger.jsonl` holds 21 rows, every one
  `sealed`, one universe, file mtime 2026-08-21 20:20 — untouched by this iteration.
- **Spot-checks (2, per methodology A.4):** J-08 and J-10, chosen because their stored scripts changed
  this round. Both final frames show real, coherent pages consistent with their recorded status
  (J-08 ends on Walk-Forward with "Ledger chain verification: ok"; J-10 ends on the Microscope
  Readiness panel with the honest "the Era-6 tick-corpus gate … is unmet: 4 tick dataset(s) …, 146
  short of the gate" line and "No integrity errors."). Both hold.
- **Replay screenshots are last-frame captures, and I treat them as such.** J-01/J-02/J-03 are
  byte-identical to each other and J-04/J-09 are byte-identical to each other (md5-checked). That is
  consistent with a deterministic rig where those journeys end on the same view; the real evidence for
  those rows is the per-step assertion pass, not the picture.
- **J-07 was not re-tested this round.** It is not in this iteration's Required-still-passing set and
  has no stored script (settled at iter-19: it stays on the browser-agent lane). Zero production code
  changed this round, so its iter-24 evidence stays valid under methodology A.6; it keeps its iter-24
  stamp, not an iter-25 one.
- **One stale artifact, corrected:** the reviewer called
  `reports/qa/goal-rapid-microscope-iter-25-evidence/J-06-verify.png` a screenshot of a *collapsed*
  Vault. I opened it: the section is in fact expanded (its description paragraph renders, unlike the
  collapsed Scout Ledger and Walk-Forward bars in the same frame) — the table simply falls below the
  800px fold. It is a leftover from the developer's own run and is not what the J-06 row cites.

## Anti-goal Check

Worked from `runs/goal-session-rapid-microscope/iter-25/scan-report.md` (**CLEAN**) plus
`iter-diff.md` (3 files + 1 untracked), and I re-derived the product-diff scope myself:
`git diff <snapshot>..HEAD -- apps/backend/app apps/frontend` is empty and `git status --porcelain`
on both trees is empty. Only `qa_playbook_iter7_fixture_scoped_backend.sh`, `tests/test_vault.py`
and the new `scripts/seed_micro_vault_iter25_sealed_fixture.py` changed.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN. One secret-shaped literal was added: `seed_micro_vault_iter25_sealed_fixture.py:65`, a throwaway QA-rig HMAC value, byte-distinct from the operator's `TAPEOLOGY_VAULT_SECRET_FILE` (never read by any seed script) and following the iter-18 precedent (`seed_micro_graduation_iter18_fixture.py:89`). Not "the vault secret". |
| Paid / external SaaS | OK | no manifest touched; the 3-file diff contains no dependency line. |
| License changes | OK | no LICENSE or license field in the diff; scan-report CLEAN. |
| Fabricated / substituted data | OK | the seeder plants a REAL dataset via `DatasetStore.record` and calls the REAL `vault.seal_shard`, never a hand-written JSON blob; every path is scoped to the rig root. The operator's real store is untouched (vault ledger mtime 2026-08-21; nothing under `.data` modified today except a pre-iteration `dataset_index.db` touch at ~01:37). |
| r5 — opaque pool / no per-shard identity before exposure | OK, strengthened | proven live by my own probe (403 + six opaque keys sealed; 200 + full identity only after a real expose) and by the new TC-1/TC-8 tests, which assert the refusal FIRED for this shard's own id, not merely that no exception occurred. |
| No exploratory read of a sealed shard | OK | new TC-8 sweeps 50+ GET routes for this shard's id/symbol/checksum plus a direct `MicroAccessor` read raising `MicroAccessorSealedShardError`; I ran it. |
| Sealed exposure is single-shot | OK this round | nothing was assigned or exposed on the real tranche (21/21 still `sealed`). See the standing open item below. |
| Frozen foundations | OK | I re-hashed all six `referee_*.py` files: 6/6 byte-identical to the iteration-0 listing (`docs/handoffs/goal-rapid-microscope-iter-0-dev.md:76-81`). `Config().config_fingerprint()` prints `08e471b10130e1e2`. |
| Single source of truth | OK this round | `coherence.md` = **COHERENCE-PASS**; no new computed or displayed value. |
| No execution path / no profit claims / no lookahead / hold-out-only / deterministic | OK | zero production diff — none of these surfaces was touched. |

**Violations introduced this iteration: none (critical or minor).**
**One older minor item CLOSED** (iter-21, order-dependent empty-state assertions): both scripts now
assert `variants tried`, a string that only ever appears once and that ledger growth can add to but
never remove. I read both files and saw the string rendered on screen in `J-09-verify.png`.
**Eight minor items stay open, zero critical.** One of them changed character this round and that is
my own finding, raised by no lane: the iter-13 chain-ledger item (deleting a ledger file plus its
anchor makes the product report "chain ok" and forget which recordings are sealed) was excused as
minor because "the real store holds no sealed recordings". Today it holds twenty-one. I kept it minor
after re-checking — the trick needs write access to your own disk, and anyone with that can already
read the raw recordings directly — but its original excuse is gone, and the instruction written at
iter-13 ("close this before the real recording happens") was overtaken: the recording happened at
iter-23 with the fix still deferred.

## Next-Step Recommendation

One more round, with the independent checker, kept small, in this order.

1. **Run all nine stored checks in one recorded run, including J-06's own.** The machine ran eight;
   J-06's script was left to the developer's own laptop run, whose record was then overwritten. This
   is the third round in a row that the same hole has produced a complaint, and it is not the
   developer's fault — the replay lane is wired to re-check only the *other* journeys, never the one
   the round is about.
2. **Fix the twenty-two-second wait on the Desk's readiness panel** — the one thing on this list you
   would actually feel. Remember each recording's wall-touch count on disk, keyed to that recording's
   own checksum AND its wall map, and only ever remember a real answer, never "none".
3. **Collapse the duplicated pilot-study list into the one list that already owns it** (one line).
4. **Build the disclosure and guard the owner already ruled for** at the referee metric: keep the
   frozen code frozen, serve the written caveat beside the number, and add a check that proves the
   caveat is really there.
5. **Decide, and write down, what to do about the chain-ledger gap now that twenty-one real sealed
   recordings exist.** This one is yours: the project's own rule forbids designing the fix casually,
   so it needs your say-so before anyone builds it.

If the clock bites, drop 4 and 5, never 1. Still do NOT record more real tape, do NOT reveal or
assign any sealed recording, and do NOT run the three studies against your real recorded corpus.

**What should happen next, in one sentence:** approve one more short round with the independent
checker to close the small leftovers — and tell us whether you want the chain-ledger gap scheduled
now that your real store holds twenty-one sealed recordings.

## Halt Justification (if halting)

Not halting. For the record, GOAL_ACHIEVED was considered and refused on two grounds: eight minor
rule-breaks are still open (my instructions bar certification while any is open, and this session
applied that same rule at iteration 23), and one of those eight lost its "it cannot hurt anything
today" justification this round. The last iteration's own decision — do not manufacture a verdict to
buy a heavier round — still stands; my ESCALATE here is claimed under the rule that a light round
which uncovers a cross-cutting safety issue earns the full pipeline, and the safety issue is named
above. If you disagree with that reading, tell the next round to run light and nothing else about
this evaluation changes.

# Iteration 19 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

This round did what it promised, and I checked it myself instead of believing the reports. "The
kept product stands" (J-10) is now fully done — the last missing piece was a check that re-running
the same work over the same stored data gives exactly the same answer, and that check now exists and
genuinely works. I proved it by deliberately breaking the real program twice and watching the check
go red, then putting the program back untouched. Nine of the ten journeys are now in good shape.

I am also ending a run of seven rounds where I asked for the heaviest kind of round. The reason is
simple: there is no new work left for the next round to build. The only thing missing is a fresh
check of one journey, "Graduation" (J-07), which the clock cut short this time. A cheap
evidence-only round fixes that. A heavy round is what ran out of clock in the first place.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (re-checked) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-01-verify.png (row UT-J-01) |
| J-02 The micro observer | passing | passing (re-checked, and the check now really works) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-02-verify.png (row UT-J-02) |
| J-03 Structure × flow | passing | passing (same) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-03-verify.png (row UT-J-03) |
| J-04 The Scout and the ledger | passing | passing (same) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-04-verify.png (row UT-J-04) |
| J-05 The walk-forward engine | passing | passing (same) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-05-verify.png (row UT-J-05) |
| J-06 The recorder and the Vault | partial | partial (unchanged — waits on you) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-06-verify.png (row UT-J-06) |
| J-07 Graduation | passing | passing, but NOT checked this round (deferred for time) | row UT-J-07 = DEFERRED-BUDGET; prior proof stands (iter-18), code untouched since |
| J-08 The surface and MCP v6 | passing | passing (re-checked) | reports/qa/goal-rapid-microscope-iter-19-evidence/J-08-verify.png (row UT-J-08) |
| J-09 The pilot studies | failing | failing (never started — waits on you) | no pilot-study module on disk; I checked rather than assumed |
| **J-10 The kept product stands** | **partial** | **passing** | reports/qa/goal-rapid-microscope-iter-19-evidence/UT-06-result.png + UT-07 (rows UT-06/UT-07); demo step-07.png (cockpit), step-11.png (structure) |

### How I checked J-10 rather than trusting the reports

Every one of its six acceptance clauses, verified by me:

1. **Safety-test suite complete.** My own sweep of the test folder found TR-1 through TR-30 with no
   gap. One warning for future readers: TR-17 exists only as three lettered parts (TR-17a/b/c), so a
   plain "TR-17" search falsely reports a hole — my own first sweep did exactly that.
2. **Same work, same answer.** I ran the new check module (10 tests, all green), then broke the real
   shipped program twice. Replacing the Scout's seeded random source with an unseeded one turned
   exactly two tests red, with the reported p-value genuinely moving (0.2164 vs 0.2374). Injecting a
   random value into the snapshot builder turned two more red. Both files were then restored and
   confirmed byte-identical (`scout.py` md5 `ee4beefb991cb14773d949fc8b291e1d`).
3. **Full test run.** I ran it myself: **3,281 passed, 8 skipped, 0 failures, 0 errors** in 676.64s.
   That is 18 more than the round started with, none lost. Use this number, not the quality report's
   3,279 — that count was taken before the independent checker added two tests.
4. **Settings fingerprint** prints `08e471b10130e1e2`.
5. **The six frozen judge files** hash byte-for-byte identical to the era's opening record.
6. **Kept surfaces.** I opened the pictures. The cockpit is genuinely alive (moving candles, "Buyer
   Control", changing quote and feature numbers). The structure page really draws AAPL's band map for
   2026-06-22 with the 300.10/302.20 walls. Every shipped Desk section renders, including all three
   Referee sections (the Registry really shows `config fingerprint 08e471b10130e1e2`) and the
   Validation Vault with its real shard row and both chain checks reading ok.

### The finding that matters most, and it is not mine

The independent checker caught something both the review and the quality check had already passed.
The round's headline promise is "the same work always gives the same answer". As the coder delivered
it, the Scout half of that check **could not see the thing it was supposed to guard**: the practice
data used a signal so strong that the result was pinned to its floor in every run, so tearing out the
seeded random source entirely left the compared answer identical. The checker found it by running the
code, and fixed it by adding two tests.

I did not take that on trust either. I made the same break myself in the real file: all eight of the
coder's original tests still passed, and only the checker's two new ones failed. Then I restored the
file and confirmed it byte-identical. So both the blind spot and its repair are proved, not asserted.
This is the eleventh time in this session that a defect has cleared both the review and the quality
check and been caught only by the independent checker.

### Three older complaints closed this round

- **Four checks that could not fail (my own finding last round).** J-02 to J-05 each used to be a
  single step asserting an unrelated old Desk heading — they would pass while the page rendered at
  all. Each now opens its own section and asserts a real field from it. I confirmed the change only
  ADDS steps and weakens nothing, and confirmed from the source that a section's contents are truly
  removed from the page when collapsed, so these strings cannot appear unless the click really
  worked.
- **Reports claiming a data store they never checked.** The launcher now writes a permanent record of
  exactly which data store it started the server against, and the browser report cites that file by
  name and says plainly it was NOT the real store.
- **The plan heading that silently switched off two checking lanes.** This round's plan says
  "Frontend Present: yes" with the reason written out, and both lanes genuinely ran.

## Anti-goal Check

Worked from `iter-19/scan-report.md` (**CLEAN**) plus `iter-19/iter-diff.md`, and confirmed
separately that `git diff <snapshot>..HEAD -- apps/backend/app apps/frontend` is **empty** — zero
product code changed this iteration.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | Scan CLEAN. I read the one new report file (`reports/qa-scoped-backend-store-manifest.md`): it holds only folder paths under a scratch directory. The vault's secret-file variable is deliberately NOT in the list it writes. |
| Paid / external SaaS | OK | No dependency manifest changed at all (`package.json`, `pyproject.toml`, `requirements*` untouched); scan reports no dependency findings. |
| License changes | OK | Scan CLEAN; no LICENSE file or license field in the diff. |
| Fabricated / substituted data | OK | Nothing new is ingested or served. The new test data lives only inside tests. The browser report explicitly states it ran against a throwaway store, not real data — the opposite of passing fake data off as real. |
| Frozen foundations (critical) | OK | Zero product diff; six judge files hash-identical to iteration 0; fingerprint unchanged. All verified by me. |
| Deterministic and seeded (critical) | OK, with a recorded near-miss | The product is unchanged and provably deterministic. The round's own *check* of this rail was briefly blind (see above) — found and fixed inside the round; I reproduced both halves. Logged as minor, resolved. |
| Single source of truth (critical) | OK | `coherence.md` = **COHERENCE-PASS**. The new tests call the existing canonical functions only; no second implementation. |
| The denominator never shrinks (critical) | OK | Strengthened: the new ledger test proves registering the same candidate twice appends two independent rows, never merged away. |
| Hold-out-only promotion (critical) | Minor, still open | The sealed judge still accepts an economic floor handed in by the caller (opened iteration 18). I re-tested my own recorded trip-wire this round rather than inheriting the verdict: there are still **zero real callers** in the shipped program (all six matches are comments, an export list, and the function's own definition), the real data store has **no** `micro_graduation` and **no** `micro_vault` folder, and the champion pointer is unchanged. Stays minor. Waits on your ruling. |
| No sealed shard read early / opaque pool (critical) | OK | Unchanged, and visible in the picture: "Sealed Tranche (Aggregate Only)", sealed count 0, with the "never a per-shard identity" wording intact. |
| No execution path · no profit claims · read-only tools · immutable data · no lookahead · one data door | OK | No product change; the guard tests for all of these are inside the suite I ran green myself. |
| Guard tests extended, never edited (house rule) | OK | Every change is additive. The four checking scripts each gained a step; the checker's four fixes are all additions. No test was weakened to make anything pass. |

**No critical violation, introduced or open.** Three older minor items CLOSED and proved closed by
me; two new minor items opened (one of them my own finding, raised by no lane); six minor items stay
open, all decided, none waiting on you except the economic-floor ruling.

## Next-Step Recommendation

**Do a cheap evidence-only round whose single job is to re-check J-07 "Graduation" with a fresh
browser pass.** That is genuinely the only machine work left. J-07 was skipped this round purely
because the clock ran out, and until it gets one fresh check the run cannot be declared finished —
the automatic finishing gate blocks on it. Nothing needs to be built or changed for this.

Two things the next round should NOT do:

- **Do not try to write a stored replay script for J-07.** The independent checker suggested it, but
  I checked and it is not possible today: the replay tool rewrites any address onto the website's
  own port, the website has no pass-through for the `/research/*` addresses, and the Desk page shows
  no graduation content at all (I searched: zero mentions). It would need harness work first.
- **Do not do a heavy round.** A heavy round is what ran out of clock and caused the skip. Repeating
  it risks skipping J-07 for a third time. There is also no new code for the independent checker to
  examine.

One small thing repairs itself: the bookkeeping file that tracks which journeys have no stored
script was deleted this round, but I read the harness code and it rebuilds that file automatically
the moment J-07 passes again. No one needs to edit it.

**Two things now wait on you, and after J-07 is re-checked, nothing else can move without them.**
Please decide:

1. **The economic-floor question.** Where should a candidate's pre-registered money floor and
   evidence label come from? Until you answer, the sealed judge keeps a hole you already ruled must
   be closed before any sealed result counts, and "The pilot studies" (J-09) cannot honestly start —
   its answers would be graded by that judge.
2. **Real tape recording.** "The recorder and the Vault" (J-06) needs an operator to record real
   market tape, which every round so far has been told not to do. Either authorise that recording, or
   change what the goal asks of J-06.

In one sentence: run one cheap round that just re-checks the "Graduation" journey in a browser, and
meanwhile please answer the two questions above, because after that round the work cannot continue
without you.

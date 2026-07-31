# Iteration 35 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** evidence

## Summary

The Desk now tells the operator how the screen on the page differs from the screen recorded
before it. I did not take the reports' word for it. I opened all three pictures myself, then
re-did the whole comparison by hand from the twelve frozen record files and got the same
numbers, row for row. Nothing of yours was written this run: not one file in the data folder
is newer than the run's start.

One thing was owed and not delivered: the short guided film this item's own wording asks for
was never recorded, because the machine gave this run its shorter setting and that setting
sends no film crew. The product works; only the film is missing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (carried, not re-tested) | prior iter-32 replay row; product surface untouched (0 deletions in this diff) |
| J-02 | passing | passing (carried, not re-tested) | prior iter-32 replay row; product surface untouched |
| J-03 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-03-verify.png |
| J-04 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-04-verify.png |
| J-05 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-05-verify.png |
| J-06 | passing | passing (replay) + 17 tool names read from the code | reports/qa/goal-desk-iter-35-evidence/J-06-verify.png |
| J-07 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-07-verify.png |
| J-08 | passing | passing (read off this run's own frame) | reports/qa/goal-desk-iter-35-evidence/J-16-verify.png — "2026-07-27 · 4 d before as-of" |
| J-09 | passing | passing (carried, not re-tested) | prior iter-34 row; product surface untouched |
| J-10 | passing | passing (carried, not re-tested) | prior iter-31 row; product surface untouched |
| J-11 | passing | passing (read off this run's own frame) | reports/qa/goal-desk-iter-35-evidence/J-16-verify.png — "502 sessions · from 2024-07-25" |
| J-12 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-12-verify.png |
| J-13 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-13-verify.png |
| J-14 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-14-verify.png |
| J-15 | passing | passing (read off this run's own frame) | reports/qa/goal-desk-iter-35-evidence/J-16-verify.png — "155 · 1d 68 · 1h 57 · 1w 11 · 4h 19" |
| J-16 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-16-verify.png |
| J-17 | passing | passing (carried, not re-tested) | prior iter-34 row; product surface untouched |
| J-18 | passing | passing (replay) | reports/qa/goal-desk-iter-35-evidence/J-18-verify.png |
| J-19 | passing | passing (carried, not re-tested) | prior iter-34 evidence; product surface untouched |
| J-20 | (new) | **passing** (+ `evidence_makeup` — film owed) | reports/qa/goal-desk-iter-35-evidence/J-20-identical-state.png · J-20-churned-state.png · J-20-no-earlier-state.png; results row UT-J-20 PASS |

Replay lane: 10 of 10 green, zero script edits. New golden `journey-scripts/J-20.json` written
against stable wording (the permanently-oldest snapshot) rather than today's counts, exactly as
the plan required.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No execution path, ever | OK | Grepped the new module and both new test files: every hit of "order" is sort order. No broker, ticket, size, or account concept. |
| No profit claims and no advice | OK | Every string added to the page is a label or a count. Advice/valence lint over the added lines: 0 hits. `test_copy_discipline.py` green unmodified. |
| Frozen foundations | OK | `git diff --stat` for `desk_screen.py`, `tradability.py`, `levels.py`, `bars.py`, `bar_index.py`, `desk_coverage.py`, `StructureChart.tsx` is empty. The whole tracked diff is 357 insertions and **0 deletions**. |
| Hold-out-only promotion | OK | No strategy, backtest, gate, or champion file in the diff. |
| No lookahead | OK | The new read touches only two already-recorded, as-of-stamped files. No new time value; no wall-clock field in the response body (checked). |
| Single source of truth | OK | I re-ran the round-trip myself: 0 field mismatches across both pairs, both directions, against the rows `ScreenStore.list()` serves; served order preserved; rank change is plain subtraction. Coherence audit COHERENCE-PASS. |
| Deterministic and seeded | OK | Same two ids twice → byte-identical body (sha256 `6627839dec25aeb5`). |
| Read-only MCP | OK | `TOOL_NAMES` read from the code = exactly 17. `app/mcp/` not in the diff. |
| Immutable data | OK | Not one file under `apps/backend/.data` is newer than the run's start. Counts unchanged: 1163 bar series, 1 universe, 12 screens, 3 screen-run, 2 top-up, 2 reconciliation records; all 12 screen files pass their own stored checksums. |
| Persistence stays scoped | OK | The new endpoint persists nothing and no fetch or compute ran. The only thing whose timestamp moved is the data folder's own directory entry, consistent with a temporary database side-file created and removed by a read. |
| Membership is never a signal | OK | The new code never reads universe membership. |
| Snapshots append-only and pinned | OK | Nothing written at all (see above). |
| Every run is an explicit operator act | OK | The new endpoint is a GET that imports none of `BarStore`/`bar_index`/`DatasetStore`/`compute_tradability` — structurally unable to trigger work. No new button. |
| The briefing describes, never advises | OK | Rank change renders as a bare number, `{row.rank_change ?? "—"}` — no arrow, no colour, no valence. Rows keep the snapshot's own order; nothing is sorted by size of change. |
| No new statistics, gates, or strategies | OK | The counts line is plain tallies, and `docs/goal.md` step 5 names those five counts itself. No threshold, no significance, no churn score. |
| The demolition stays demolished | OK | Read-only GET; no manual-input write path. |
| The ledger never holds orders | OK | No new record of any kind is written. |
| The suite stays keyless and hermetic | OK | No network call in either new test file; both plant their own scoped snapshots. |
| The fingerprint pin does not move | OK | `Config().config_fingerprint()` = `08e471b10130e1e2`. `app/config.py` not in the diff; zero new fields. |
| The enhancement loop stays inside its box | OK | `docs/goal.md` diff is 143 additions and 0 deletions, one hunk at line 1674, inside the `AUTO:journeys` block (lines 524–1817). No human-authored journey and no anti-goal was touched. J-20 carries a single-source-of-truth acceptance clause. |
| Host-guard caps are law | OK | No host-guard file in the diff. |
| Secrets / paid SaaS / license | OK | Deterministic scan CLEAN. No manifest (`package.json`, `package-lock.json`, `requirements`, `pyproject`) and no LICENSE file changed. |
| Fabricated or substituted data | OK | Every displayed value was matched byte-for-byte against the two recorded files. No fixture stands in for real data. |

## Next-Step Recommendation

Halt — the goal is reached. Please confirm the finish.

Five follow-ups. None is a fault in what the product computes, and I recommend that none of
them becomes a new build run.

1. **The one worth your eye.** On the page, under "rows compared 100 · rank changed 0 · side
   changed 0 · entered 0 · left 0", the Desk prints "The compared snapshots' ranked rows are
   identical." For that exact pair, all 100 rows actually differ in one field the briefing
   table above it displays: the age of the basis, which reads "4 d before as-of" today and
   "3 d before as-of" on the compared screen. The five things the comparison names — position,
   side, class, distance, basis date — really are identical, and the goal file itself dictates
   that sentence word for word, so the build did what it was told. The sentence is simply
   wider than what it checks. A one-line wording change would fix it.
2. The short guided film for the new section was never recorded, because this run was given
   the shorter setting. Everything it would have shown is already proven in three pictures I
   opened and in numbers I re-derived myself, so it rides along with any future run as a
   passenger, never as the reason for one.
3. Asking for a screen that does not exist returns a blank "how the base was chosen" field —
   a fourth possible value the written contract does not list. Behaviour is honest; the
   contract note is one line short.
4. Ten of the nineteen saved re-check scripts were replayed, not all nineteen. No script was
   edited, and I proved on paper that the other nine cannot accidentally match the new
   section's wording or its element names.
5. The three pictures are crops taken from full-page captures, because a direct capture at
   that scroll depth comes back solid black in this environment — the same known quirk your
   second key already accepted last run.

One sentence for you: the Desk now says plainly how today's screen differs from the one before
it, I checked every number against the frozen records myself and found no disagreement, and
nothing of yours was written — so please confirm the finish and treat the five notes as
optional tidying, starting with the "identical" wording in note 1.

## Halt Justification

Every one of the twenty journeys is `passing`. The one built this run, J-20 "Every recorded
screen states how it differs from the screen recorded before it", is backed by three pictures
I opened, by a hand re-derivation from the frozen files that matched exactly, and by a
field-by-field check that the served comparison copies the recorded rows without changing a
single value. The structure check is COHERENCE-PASS, the machine scan is CLEAN, the test suite
is 1551 passed / 8 skipped / 0 failed, the settings pin still reads `08e471b10130e1e2`, and the
tool list still holds exactly 17 names. No anti-goal is open; the four historical ones stay
resolved and I re-checked each against this run's own evidence. Every journey's goal-text
signature matches today's `docs/goal.md`, so no earlier pass has gone stale, and there is no
note saying any journey's wording changed.

The one gap is a missing recording, not a missing behaviour: the machine dispatched this run at
the shorter setting, which sends no film crew. My own standing rule — and this project's own
rules — say an evidence recording never becomes the reason for another build run. So J-20 is
recorded as passing with the film marked as owed, and the finish is proposed on the pictures
and the numbers that already exist.

**Verdict:** GOAL_ACHIEVED

**Depth Recommendation For Next Iteration:** evidence

# Iteration 17 Evaluation

## Summary

Every ranked row on the Desk page now shows the price range of the wall it was measured against and
the closing price it was measured from, side by side. I did not take any report's word for it. I
opened the picture myself: one row (BRK-B) shows a close that sits inside its own price range, and a
row four lines below it (LIN) shows a close that sits just under its range — both in the same image.
Then I proved the numbers instead of believing them: I read the saved screen straight off disk and
re-computed all 63 closing prices from the stored daily price files myself, with zero mismatches.
Nothing that used to work stopped working, nothing was written into the owner's own data folder, and
the settings fingerprint has not moved. One thing is genuinely short: the guided walkthrough film for
this feature was filmed against the old data, so it shows only the "no close recorded" state and
never shows a price. The feature itself is proven; only the film needs re-taking.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-01-verify.png (row UT-J-01 PASS) |
| J-02 Coverage + top-up | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-02-verify.png (row UT-J-02 PASS) |
| J-03 The screen | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-03-verify.png (row UT-J-03 PASS) + evaluator's own same-pins re-derivation (rank order identical 63/63) |
| J-04 The /desk briefing page | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-04-verify.png + UT-06-result.png (all pre-existing cells byte-identical) |
| J-05 Ledger history + drill-in | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-05-verify.png (opened by the evaluator) + UT-07-result.png |
| J-06 MCP 17 read-only tools | passing | passing | reports/phase-goal-desk-iter-17-ui-test-results.md row UT-J-06 (PASS; no browser surface) + evaluator's own parse: EXPECTED_TOOLS = exactly 17 |
| J-07 Kept product sentinel | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-07-verify.png (opened; pinned wall drawn at 300.10/302.20) + zero diff on every protected file |
| J-08 Basis disclosure | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-08-verify.png (row UT-J-08 PASS) |
| J-09 Top-up run records | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-09-verify.png (row UT-J-09 PASS) |
| J-10 Coverage reconciliation | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-10-verify.png (row UT-J-10 PASS) |
| J-11 History disclosure | passing | passing | reports/qa/goal-desk-iter-17-evidence/J-11-verify.png (row UT-J-11 PASS — added by the AUDIT lane, finding P1) |
| J-12 Snapshots addressable by id | passing | passing (capture defect carried) | reports/qa/goal-desk-iter-17-evidence/J-12-verify.png (row UT-J-12 PASS — audit lane) + UT-07-result.png |
| J-13 Band range + reference close | (new) | passing (capture defect) | reports/qa/goal-desk-iter-17-evidence/UT-05-result.png (in-band BRK-B + out-of-band LIN in ONE frame, scoped rig, origin asserted) + AUDIT-F1-legacy-band-range.png / -scrolled.png |

Evidence I opened or re-derived myself, beyond the reports:

- `UT-05-result.png` — BRK-B `band 488.50–490.85 · close 490.85`; LIN `band 506.33–509.61 · close
  506.32`; CAT `band 894.56–900.63 · close 894.54`. In-band and out-of-band legible together.
- `AUDIT-F1-legacy-band-range-scrolled.png` — legacy rows read
  `band 488.50–490.85 · close not recorded in this snapshot` (the audit's F1 fix).
- The scoped snapshot on disk
  (`…/iad.goal-desk-iter-17.3302867/desk-iter17-scoped-qa/screen/screen-2026-07-28-ac07c9581a4f.json`):
  checksum recomputes; 63/63 ranked rows carry `reference_close`, 0/38 skip rows do; **zero
  mismatches** when each row's value is compared to the close of the `1d` bar dated at that row's own
  `basis_as_of` read from the store (goal.md's TC-2 clause, re-derived by me); 9 in-band / 54
  out-of-band; rank order identical 63/63 to the pre-change ambient snapshot under the same five
  pins; the ONLY new key on any ranked row is `reference_close`.
- All six ambient snapshots: valid checksums, mtimes predating the iteration, `reference_close`
  absent (not `null`) on every one of their ranked rows.
- Backend suite run by me: exit 0, 0 failures/errors, 8 skips. `Config().config_fingerprint()` =
  `08e471b10130e1e2`. `EXPECTED_TOOLS` = 17. Zero diff on `tradability.py`, `levels.py`, `bars.py`,
  `bar_index.py`, `desk_coverage.py`, `config.py`, `meta.py`, `mcp/__init__.py`, `StructureChart.tsx`,
  `PriceChart.tsx`, `test_copy_discipline.py`, and the whole `app/engine/` tree.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials | OK | `iter-17/scan-report.md` CLEAN; the product diff is 6 files, none of them config/env; `test_no_credential_in_artifacts.py` green in my own suite run |
| Paid/external SaaS, new dependency | OK | zero diff to `package.json`, `requirements*.txt`, `pyproject.toml` (not in the changed-file list at all) |
| License changes | OK | no LICENSE or license-field file in the diff |
| Fabricated/substituted data | OK | I re-derived all 63 `reference_close` values from the stored `1d` bars: 0 mismatches. Legacy rows carry the key absent, never a computed value. The scoped rig's 9 `tick_evidence` false values are explained: its copied `datasets/` folder is empty — a fixture artifact, and the ambient record is untouched |
| No execution path, ever | OK | no broker/order code anywhere in the diff; `test_no_execution_path.py` green in my own suite run |
| No profit claims and no advice | OK | `test_copy_discipline.py` byte-unmodified (`git diff` empty) and green; UT-09 scanned all 63 rendered `band` strings plus the populated ones for banned words — 0 matches |
| Frozen foundations | OK | zero diff on every protected module and the whole engine tree (verified by me, list above) |
| Hold-out-only promotion | OK | no strategy/champion/ledger file in the diff |
| No lookahead | OK | `as_of` pinned `2026-07-28T23:59:59Z`; the disclosed close comes from the SAME already-clamped walk that fed the distance, not a second read |
| Single source of truth | OK | `iter-17/coherence.md` COHERENCE-PASS; one owner (`desk_screen.py:401`), one endpoint; the page renders two served numbers with no arithmetic (I read the diff; a new guard test enforces it) |
| Deterministic and seeded | OK | the scoped compute under the same five pins produced the same snapshot id and the same 63/63 rank order as the pre-change record |
| Read-only MCP | OK | no MCP code change; exactly 17 tools (my own parse) |
| Immutable data | OK | 0 of 369 bar files modified since 2026-07-28; all six screen snapshots keep valid checksums and pre-iteration mtimes |
| Persistence stays scoped | OK | the only file written under `apps/backend/.data` during the iteration is the derived `tradability_cache.db`; the new screen compute went to a scoped temp store |
| Membership is never a signal | OK | no universe code in the diff |
| Snapshots append-only and pinned | OK | nothing backfilled or rewritten — legacy rows still carry no `reference_close` |
| Every run an explicit operator act | OK | the one new compute was an explicit POST on a scoped rig; no scheduler, cron, or auto-refresh added |
| The briefing describes, never advises | OK | copy lint unmodified and green; new copy is two numbers and the word `band`/`close` |
| No new statistics, gates, or strategies | OK | no threshold, no "inside the band" flag — I read both rendered string branches |
| The demolition stays demolished | OK | no journal-era machinery; no manual-input path added |
| The ledger never holds orders | OK | no size/ticket/entry/exit concept in the new field |
| The suite stays keyless and hermetic | OK | my own suite run made no network call; the live screen compute is disclosed as an operator-run act on a scoped rig |
| The fingerprint pin does not move | OK | `08e471b10130e1e2` printed by me; zero new `Config` fields (`config.py` zero diff) |
| The enhancement loop stays inside its box | OK | `docs/goal.md` diff is 81 insertions, 0 deletions, all inside the `AUTO:journeys` markers (514–953); the Anti-goals section is byte-unchanged |
| Host-guard caps are law | OK | my own process affinity is `4-7,12-15` |

No new violation. The three older items stay resolved and were each re-checked by me directly.

## Next-Step Recommendation

Halt — the goal is achieved. Six follow-ups for the owner, none of them a defect in the product and
none of them blocking:

1. **Re-take the walkthrough film for this feature.** The film that exists shows only the old "close
   not recorded in this snapshot" rows, so it never shows a price at all — the one thing the feature
   is about. Nothing needs to be built; it needs re-filming against a throw-away copy of the data with
   a fresh screen computed in it. One warning learned this run: never start a second copy of the web
   front end from the same source folder while the first is running — the two share one build folder
   and the running page silently starts talking to the wrong back end (this happened and was caught
   and cleaned up). Copy the front-end folder, or stop the first one first.
2. **Two real defects were found by the independent audit, not by the build, and both were fixed in
   place.** First, every row an operator can actually open today is an old row, and the page was
   dropping the price range on exactly those rows — so the new feature would have shown nothing on
   100% of real data. Second, the plan file's list of "must still work" journeys was written over two
   lines, and the tool that reads it only reads the first line, so two journeys silently reached no
   check at all while the report claimed everything passed. Both are fixed; the second deserves a
   tool fix, because a re-wrapped line will do it again.
3. **The finishing check reports a failure that is not real.** It looks for the phrase "backend-only"
   in the change summary and finds the sentence "Nothing is backend-only in this iteration". The
   summary plainly describes the new column. Please have that phrase test made smarter.
4. **The quality-check step marked one browser item as passed using a picture that does not show it,
   and quietly marked the film item "not applicable".** The audit caught both and the real evidence
   was produced later, so no conclusion here is wrong — but "passed" must never be written for
   something the cited picture does not show.
5. **Still open by choice, carried from earlier runs:** the earlier same-day screen recording still
   needs one full-length picture; the nine replay pictures in this run are the same single image
   reused, so they prove the checks ran, not what each check saw; keyboard access for the history
   rows; the run tables have no length limit; and the Desk page is now eight stacked sections and
   long.
6. **Nothing in your own data folder was changed this run** — second run in a row. Only a rebuildable
   cache file was refreshed by ordinary page loads.

One sentence for the owner: every ranked row on the Desk page now states the wall's price range and
the exact close it was measured from, proven number by number against your stored price files —
please confirm the finish, and let the film be re-taken afterwards.

## Halt Justification

All thirteen must-have journeys have positive evidence of passing, and I opened or re-derived the
evidence for the new one myself rather than trusting any report. There is no unresolved anti-goal
violation, the coherence audit is COHERENCE-PASS, and there is no goal-edit drift note, so nothing
blocks the finish under the decision rules.

One acceptance sentence in the goal file is not literally satisfied and I am recording it openly
rather than glossing over it: the guided walkthrough film for J-13 exists and is flagged as new, but
it was filmed against the old data before the audit's fix, so its eight frames show only the "close
not recorded" state and its verdict reads "recorded with notes" rather than "recorded". I treated
this as a defect in the RECORDING, not in the product, because the behaviour the film should have
shown is proven three other ways: a real browser picture from a correctly isolated rig showing an
in-band row and an out-of-band row together, the saved screen file itself, and my own re-computation
of all 63 closing prices from the stored price files with zero mismatches. The framework's own rule
is that a missing or wrongly-framed recording rides a make-up capture and must never become an
iteration's goal, so the journey keeps its evidence-based status with a make-up flag set. If the
owner reads that sentence strictly, the remedy is one short re-filming run, not any change to the
product. This call is written down in the assumptions ledger.

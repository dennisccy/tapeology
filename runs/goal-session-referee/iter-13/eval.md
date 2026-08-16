# Iteration 13 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** evidence

## Summary

The new screen works, and I checked it myself instead of believing the reports. A person can
now open the Desk page, open the "Referee Registry" panel, and read — for the first time in a
browser — how much evidence each family holds and why the strategy family is not ready to be
judged. I opened the pictures: on the seeded test setup the Playbook block reads Records 4,
Distinct sessions 3, Signals at current basis 21, with its two identity codes; on a separate
empty setup the same block reads plain zeros instead of a blank space. But the era cannot be
declared finished this round. Two older journeys, J-01 "The era transition stands" and J-02
"The evidence contract", were skipped for time — the results table marks them "not run", and a
skipped row can never support a finish. One promised picture is also missing: both captures
stop about a screen short of the strategy family's honest warning sentence and its
no-lookahead caveat, which is the very thing this round set out to make visible.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 The era transition stands | passing | passing (deferred — not tested this round) | `reports/phase-goal-referee-iter-13-ui-test-results.md:39` (DEFERRED-BUDGET); my own suite run: `tests.test_referee_guards` 19 tests, 0 failures |
| J-02 The evidence contract | passing | passing (deferred — not tested this round) | `reports/phase-goal-referee-iter-13-ui-test-results.md:40` (DEFERRED-BUDGET); my own suite run: `tests.test_referee_evidence` 29 tests, 0 failures |
| J-03 The statistics core | passing | passing (carried; its code did not change) | my own suite run: `tests.test_referee_stats` 48 + `tests.test_referee_oracles` 11, 0 failures |
| J-04 Matched nulls | passing | passing (carried; its code did not change) | my own suite run: `tests.test_referee_null` 36, 0 failures |
| J-05 The registry | passing | passing (replay said FAIL — I overturned it myself) | `reports/qa/goal-referee-iter-13-evidence/J-05-result.png` (row reads `S-1 · capitulation:long · 2026-08-15 · historical-exploration · active · 0 / 12 · 1 / 1 discovery (exploratory)`); failure capture `J-05-verify.png`; results:18 |
| J-06 Estimand engines + adjudication | passing | passing (carried; its code did not change) | my own suite run: `tests.test_referee_adjudicate` 57, 0 failures |
| J-07 The starter family | passing | passing | `reports/qa/goal-referee-iter-13-evidence/J-07-verify.png`; results:19 |
| J-08 The strategy family + promotion interlock | passing | passing (carried; its code did not change) | my own suite run: `tests.test_pnl_scan` 30, 0 failures; store-scope guard CLEAN |
| J-09 The Referee on /desk + 22 tools | passing | passing | `reports/qa/goal-referee-iter-13-evidence/J-09-verify.png`; results:20; I parsed `EXPECTED_TOOLS` myself = 22 |
| J-10 The kept product stands | passing | passing | `reports/qa/goal-referee-iter-13-evidence/J-10-verify.png`; results:21 |
| J-11 The accrual projection states its own basis | passing | passing (`evidence_makeup` carried — walkthrough still unrecorded) | `reports/qa/goal-referee-iter-13-evidence/J-11-verify.png`; results:22 |
| J-12 The readiness fold gets its reader | (new) | passing, with `evidence_makeup` (`capture-defect`) | `reports/qa/goal-referee-iter-13-evidence/J-12-seeded-rig-result.png` + `J-12-empty-corpus-result.png`; results:23 |

Notes on two rows I did not take on trust:

- **J-05.** The deterministic replay recorded FAIL ("step 02 expected `historical-exploration`
  did not appear",
  `reports/phase-goal-referee-iter-13-regression-replay-results.md:19`). I opened the merged
  lane's capture and read the words on screen at 1.35x — they are there. I then opened the
  replay's own failure capture: the panel is open and its first table is filled, but the S-1
  action button still reads "Select", whereas `J-11-verify.png`, taken moments later on the same
  rig, shows it greyed to "Registered". So the second server response had simply not arrived
  inside the 8-second budget. The golden script's patience was raised from 8s to 12s; I diffed
  that file myself — the expected text is byte-unchanged, so nothing was weakened.
- **J-12.** `J-05-result.png` and `J-12-seeded-rig-result.png` are the same file
  (md5 `87a696a747360d42a49a29e4bb65d934`). I opened it and confirmed it genuinely carries both
  journeys' end states on one page, so nothing is hidden behind the reuse.

## Anti-goal Check

Worked from `runs/goal-session-referee/iter-13/scan-report.md` (CLEAN) and
`iter-13/iter-diff.md` (5 files: 2 backend TEST files, `api.ts`, `types.ts`, `page.tsx`).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials committed | OK | scan-report CLEAN, no config/env file in the 5-file diff |
| Paid / external SaaS, new runtime dependency | OK | I diffed `package.json`, `package-lock.json`, `pyproject.toml`, `requirements*.txt`: all empty |
| License change | OK | no LICENSE diff (checked in the same command) |
| Fabricated / substituted data | OK | zero new value served; every rendered number is a pass-through of `GET /research/desk/referee/evidence`, coherence audit confirms (`coherence.md` Data Contract table) |
| 1. No execution path, ever | OK | `tests.test_no_execution_path` 6 tests green in my own run; diff adds one read-only GET |
| 2. No profit claims / no advice | OK | `tests.test_copy_discipline` 30 green in my own run; my own grep for `annualized\|profitable\|win rate\|has an edge` over `page.tsx` returns nothing |
| 3. Frozen foundations | OK | `git diff --stat 027a7f7 -- apps/backend/app` EMPTY (I ran it); frozen-module diff empty; `Config().config_fingerprint()` printed by me = `08e471b10130e1e2` |
| 4. Hold-out-only promotion | OK | `pnl_scan.py` zero diff; no POST issued; no referee dirs exist under `apps/backend/.data`; store-scope guard CLEAN at 11,274 files |
| 5. No lookahead | OK | this iteration *surfaces* the forming-bar lookahead caveat to the operator — the opposite of a breach |
| 6. Single source of truth | OK | `coherence.md` COHERENCE-PASS with an explicit ruling that the new aggregate block is a distinct fold, not a duplicate of the shortlist's per-candidate cells; the new unowned-literal guard proves no second copy of the disclosure strings exists — I re-ran that grep myself, empty |
| 7. Deterministic and seeded | OK | no random draw added anywhere in the diff |
| 8. Read-only MCP | OK | I parsed `EXPECTED_TOOLS` myself = exactly 22; `test_mcp_server.py` untouched |
| 9. Immutable data | OK | no record file written; only SQLite WAL/SHM sidecars of derived caches touched; guard CLEAN |
| 10. Persistence stays scoped | OK | no recording path added |
| Referee-era rails (confirmatory gauntlet, atlas exploratory, CI-inversion, BH denominator, no gate loosening, never feeds back, certificate-locked promotion, attestation required, no annualized) | OK | zero backend production diff means no statistical machinery moved; the import-ban and source-scan guards are in my own green suite run |
| The enhancement loop stays inside its box | OK | I verified this myself: the `docs/goal.md` diff is 73 insertions / 0 deletions in one hunk, and a line-membership check confirms every added line lies between the `AUTO:journeys` markers (lines 737-879) |
| Host-guard caps | OK | no heavy compute path added; engine confinement unchanged |

No new violation. The three recorded violations from iterations 6, 8 and 9 all stay resolved
and could not re-open — the modules that carried them have zero diff this iteration.

Non-blocking code-quality note (not an anti-goal): the reviewer's MINOR is real and I confirmed
it by reading the file. `apps/backend/tests/test_desk_ui_guards.py:371-372` — the
`seeded_bands_by_class` assertion that belongs to
`..._catches_opposite_band_and_bands_by_class_arithmetic` now sits at the end of the new
`..._catches_referee_evidence_arithmetic` body. Both tests still run and pass; only the
docstrings no longer match their bodies.

## Next-Step Recommendation

Run one short verification round with no new building.

1. **Re-check the two skipped journeys.** J-01 "The era transition stands" and J-02 "The
   evidence contract" have no screen of their own, so re-checking them means running their named
   backend acceptance tests and writing the real result into the results table — exactly what
   round 11 did for seven journeys. Until those two rows say PASS instead of "not run", the era
   cannot be declared finished, no matter how healthy everything else is.
2. **Take the one missing picture.** Photograph the strategy family's honest warning sentence
   and its no-lookahead caveat inside the "Referee Registry" panel. A whole-page photograph
   cannot reach them: the page is about 8,400 pixels tall and the camera stops at 4,320. So
   photograph just that block on its own, or close the panels above it first so it moves up the
   page. This is the sentence the whole round existed to make visible, so it is worth getting on
   film.
3. **Ride-along, none of them blocking:** move the stray two-line assertion at
   `apps/backend/tests/test_desk_ui_guards.py:371-372` back into the test whose description it
   belongs to; and the four small clean-ups carried since round 10 (add the four Referee storage
   folders to the guard that watches the owner's real data; make a certificate with no name at
   all fail instead of matching; show a clear word instead of a plain dash when a second data
   request fails; correct a stale comment quoting 19/7/1).

One thing worth watching rather than acting on: the registry panel now fires three server
requests when it opens instead of two, and this is the first round where an eight-second wait
was not long enough for its table to appear. The wait was raised to twelve seconds, which is
honest but hides the trend. If a future round raises it again, treat the slowness itself as the
problem.

For a person: approve one short verification round — re-run the two skipped journeys' own tests
and take the one missing photograph; nothing needs a human unblock. Carried items, none
blocking: this round's changed files are still uncommitted; the era still has no video
walkthrough because the shared recording tool cannot play a "scroll" step (it lives in the
shared framework folder, not in this project); and, from round 2 and outside this project, the
unrelated trendora backend on port 8255 has still not been restarted.

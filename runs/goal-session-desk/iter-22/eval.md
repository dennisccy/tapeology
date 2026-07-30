# Iteration 22 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** evidence

## Summary

The one picture the goal file still demanded now exists, and I opened it myself. The small hint that
appears when the mouse rests on a briefing row is photographed: a real browser window on a private
screen, the hint floating over the row, its text reading "bands by class A 10 · B 0 · C 0 ·
unclassified 0" — and the hint is drawn OUTSIDE the browser's own page area, which is exactly why
three earlier runs could not take it and why this picture cannot be a fake. I then proved the numbers
in the picture against your stored records instead of believing the report: the saved screen on disk
recomputes its own checksum and holds those same counts, the same wall range and the same closing
price for that row. Nothing was built or changed this run — the program is byte-for-byte the same tree
that passed the whole back-end suite at iteration 19 — nothing of yours was written, and all fourteen
journeys have positive, opened evidence.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing (carried — code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-01-verify.png |
| J-02 Coverage + bar top-up | passing | passing (carried — code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-02-verify.png |
| J-03 The screen — pinned, append-only, ranked | passing | passing (carried; evaluator re-read all 10 stored screens — every checksum recomputes, every one pins date/as-of/universe/fingerprint/bar-store signature) | apps/backend/.data/screen/*.json (evaluator's own recompute) |
| J-04 The /desk briefing page | passing | passing (replay 5/5) | reports/phase-goal-desk-iter-22-ui-test-results.md UT-J-04 + reports/qa/goal-desk-iter-22-evidence/J-04-verify.png |
| J-05 Ledger history + drill-in | passing | passing (replay 5/5) | reports/phase-goal-desk-iter-22-ui-test-results.md UT-J-05 + reports/qa/goal-desk-iter-22-evidence/J-05-verify.png |
| J-06 MCP contract v3 — 17 tools | passing | passing (evaluator's own count: 17 tools listed from the running module) | apps/backend/app/mcp/ (own enumeration, incl. desk_universe + desk_screen) |
| J-07 Regression sentinel | passing | passing (replay 5/5 + own checks: fingerprint `08e471b10130e1e2`, 17 tools, product diff EMPTY) | reports/phase-goal-desk-iter-22-ui-test-results.md UT-J-07 + reports/qa/goal-desk-iter-22-evidence/J-07-verify.png |
| J-08 Row names the bar it measured from | passing | passing (spot-check: "basis 2026-07-17 · 3 d before as-of" on every visible row of this run's fresh capture; recorded on all 100 rows on disk) | reports/qa/goal-desk-iter-22-evidence/J-14-desk-opposite-column.png |
| J-09 Top-up run leaves a record | passing | passing (carried — code unchanged) | apps/backend/.data/topup_runs/topup-2026-07-29-5de907c83fc4.json (iter-19 check) |
| J-10 Coverage the store can prove | passing | passing (carried — code unchanged) | reports/qa/goal-desk-iter-18-evidence/J-10-verify.png (iter-19 re-derivation) |
| J-11 Row states its history length | passing | passing (spot-check: "history 496 sessions · from 2024-07-25" on the visible rows; recorded on all 100 rows on disk) | reports/qa/goal-desk-iter-22-evidence/J-14-desk-opposite-column.png |
| J-12 Recorded screens are readable by id | passing | passing (replay 5/5) | reports/phase-goal-desk-iter-22-ui-test-results.md UT-J-12 + reports/qa/goal-desk-iter-22-evidence/J-12-verify.png |
| J-13 Row states wall price and close | passing | passing (replay 5/5; band+close legible again in this run's fresh capture and byte-matched to disk) | reports/qa/goal-desk-iter-22-evidence/J-13-verify.png + J-14-desk-opposite-column.png |
| J-14 Row states the nearest wall on the other side | passing (`evidence_makeup`, goal text CHANGED — prior pass void) | passing — RE-VERIFIED against the current goal text; make-up flag CLEARED | reports/qa/goal-desk-iter-22-evidence/J-14-tooltip-crop.png + J-14-tooltip.png + J-14-desk-opposite-column.png; reports/phase-goal-desk-iter-22-ui-test-results.md UT-J-14 |

Goal-edit drift: `journeys-changed.md` listed J-14 only (goal.md gained T-10a and a J-14 acceptance
clause naming the capture rig). It was re-verified against the CURRENT text this iteration and its new
`spec_hash` `0e6ce6bedcaa…` recorded; the other thirteen hashes recompute unchanged.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | `iter-22/scan-report.md`: CLEAN, no findings on added lines (3 untracked files scanned). No new config or env file in the diff list. |
| Paid / external SaaS | OK | No manifest change; the three new files are QA tooling under `project-extensions/qa-rig/` using already-present dev tools (Playwright, Pillow) plus free `Xvfb`/`xdotool` fetched into a user cache. No product runtime dependency added. |
| License changes | OK | No LICENSE file or license field in the diff (3 files: qa-rig README, capture script, `xrig.sh`). |
| Fabricated / substituted data | OK | Every number in the evidence was re-derived by me from `apps/backend/.data/screen/screen-2026-07-20-ca185294a384.json`, whose stored checksum recomputes: BRK-B `bands_by_class {A:10,B:0,C:0,unclassified:0}`, band 488.5–490.9100036621094, close 490.9100036621094, opposite resistance A 490.9700012207031–494.3949890136719 @ 1.2221702174772953 bps; DIS opposite @ 1128.2895954803862 bps. |
| No execution path / no advice / no orders | OK | Zero product diff (`git diff 363203d4..HEAD -- apps/ scripts/ config/` empty, no untracked files under `apps/`), so no copy or code could change; the copy lint is unmodified. |
| Frozen foundations · fingerprint pin | OK | `Config().config_fingerprint()` printed `08e471b10130e1e2` on my own run; the `apps/` tree is byte-identical to iteration 19's tree (`git diff 048c234..HEAD -- apps/` empty), whose full suite ran green. |
| Immutable data · snapshots append-only and pinned | OK | Under `apps/backend/.data` the only files touched during the run are the rebuildable `bar_index.db-wal`/`-shm` sidecars (WAL 0 bytes). No screen, universe, bar-series, or top-up file created, modified or removed; all 10 stored screens recompute their checksums and the 6 legacy ones still carry no opposite-wall, class-count or close field. |
| Every run is an explicit operator act | OK | No new screen, universe or top-up record exists; the capture performed reads only. |
| Single source of truth | OK | `iter-22/coherence.md`: COHERENCE-PASS, no blocking violations, no advisory notes; no owner or serving path changed. |
| Read-only MCP · exactly 17 tools | OK | My own enumeration from the running module lists exactly 17 tools, including `desk_universe` and `desk_screen`. |
| Suite stays keyless / hermetic | OK | No test file changed; nothing fetched from the network this run. |
| Enhancement loop stays inside its box | OK, with a limit stated | `docs/goal.md`'s edit (T-10a plus the J-14 capture clause) was written at 08:22–08:26, before this iteration's snapshot (08:48) and after iteration 21's halt (00:17), while the session sat `STALLED` with no proposer running; it is labelled OWNER RATIFICATION and it STRENGTHENS the bar (the screenshot is still required, and the capture protocol is now spelled out). I cannot see who typed it — recorded in the assumption ledger. |
| Host-guard caps are law | OK | The capture rig's processes run pinned to the mask `0-3,8-11` you set on 2026-07-29 (`taskset` read directly on `Xvfb` 3462046 and Chrome 3462134). |
| Persistence stays scoped (this iteration's own plan) | DEVIATION, disclosed, not scored as a violation | For the seventh run in a row the evidence lanes served your ambient store and rig (`:3301`/`:8301`) instead of the scoped copy the iteration's own spec demanded (TC-2 / DoD 4). It only READ: verified file by file that nothing of yours was created, changed or removed. |

## Next-Step Recommendation

Halt — the goal is achieved, and please confirm the finish. Four notes for you, none a defect in the
product and none blocking. (1) The capture rig is still RUNNING on your machine (a private screen and
a browser, both inside your CPU limits) because the run was told not to shut it down; please run
`./project-extensions/qa-rig/xrig.sh down` when you are ready. (2) The picture-taking lanes again used
your own data folder instead of a throw-away copy, for the seventh run in a row; this time they only
read, which I checked file by file, and the real fix is a rail that forces the serving program to
point at a copy rather than another written instruction. (3) Small picture-quality items that change
nothing in the program: the five replay pictures and the four film frames are only three distinct
images, because the replay tool keeps saving the first view of the Desk page; the film for this run is
a plain re-recording, and the one the goal file asks for was already recorded at iteration 21. (4) The
goal file's host-protection paragraph still quotes your old CPU list, worth a one-line tidy-up on your
own track. One sentence for you: the last owed photograph now exists and its numbers match your stored
records exactly — please confirm the finish, then shut the capture rig down.

## Halt Justification

All fourteen must-have journeys are `passing`, each with positive evidence I opened or re-derived
myself, and none carries a make-up or infrastructure flag any more. The single item that kept this
session open since iteration 19 — the photograph of the row hint — now exists in two forms I read
directly (a full frame and a tight crop), taken on the rig you approved, and the rig refuses to write
a file unless the hint really appeared as its own window and really carries the required text; I also
saw in the full frame that the hint is drawn past the browser window's edge, which no in-page
screenshot can produce. Coherence is COHERENCE-PASS, the deterministic scan is CLEAN, there are no
unresolved anti-goal violations (the three older ones stay resolved and were re-checked by me),
nothing was written into your data, the settings fingerprint is `08e471b10130e1e2`, the tool count is
exactly 17, and the program tree is byte-identical to the one whose full back-end suite ran green.
Nothing productive is left for the chain to do.

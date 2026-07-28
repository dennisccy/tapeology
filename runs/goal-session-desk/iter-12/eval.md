# Iteration 12 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This run was asked to do one thing: record a guided walkthrough that shows the new top-up run
record both when nothing is saved and when a saved run is on screen. That walkthrough was never
made. I searched the whole project: there is no walkthrough file and no walkthrough pictures for
iteration 12, and the browser-checking report says in its own words that making it was not its job.
I found out why, from the session's own activity log: when a run is done in the SHORT form, the
walkthrough is recorded AFTER I score the work, so I can never see it; in the LONG form it is
recorded BEFORE me. So this short run could not possibly have finished the job it was given.
Everything else went well — the eight older journeys were all re-checked and still work, the two
new pictures this run did take are genuine and clear, and not a single line of program code
changed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-01-verify.png (row UT-J-01, replay PASS) |
| J-02 Coverage + bar top-up | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-02-verify.png (row UT-J-02, replay PASS) |
| J-03 The screen — pinned, append-only | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-03-verify.png (row UT-J-03, replay PASS) |
| J-04 The /desk briefing page | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-04-verify.png (row UT-J-04, replay PASS) |
| J-05 Ledger history + drill-in | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-05-verify.png (row UT-J-05, replay PASS) |
| J-06 MCP contract — 17 tools | passing | passing | Spot-check #1, evaluator's own parse of `apps/backend/app/mcp/__init__.py` = exactly 17 tool names, no 18th; row UT-J-06 (test_mcp_server.py 35 passed) |
| J-07 The kept product stands | passing | passing | Spot-check #2, evaluator opened reports/qa/goal-desk-iter-12-evidence/J-07-verify.png — pinned AAPL wall drawn (R A · 171 · 302.20, R A · 97 · 300.10); row UT-J-07 |
| J-08 Basis of each ranked row | passing | passing | reports/qa/goal-desk-iter-12-evidence/J-08-verify.png — basis captions "2026-07-23 · 4 d before as-of" / "2026-07-13 · 14 d before as-of" legible; row UT-J-08 |
| J-09 Append-only top-up run record | partial | **partial** (2nd consecutive) | NEW and verified: reports/qa/goal-desk-iter-12-evidence/UT-J-09-empty-topup-section.png and UT-J-09-populated-topup-section.png (row UT-J-09). MISSING: no `reports/phase-goal-desk-iter-12-demo.json`, no `reports/demo/goal-desk-iter-12/` — the walkthrough clause is still unevidenced |

Notes on the evidence I opened myself:

- `UT-J-09-empty-topup-section.png` — a real `/desk` page on a freshly copied, genuinely empty
  rig, showing the "TOP-UP RUNS" panel with the circle-slash mark and "No top-up runs recorded
  yet."
- `UT-J-09-populated-topup-section.png` — one image holding the three-row run table
  (`done 404/404`, `cancelled 3/404`, `done 404/404`), the line "state: done   404 of 404 pairs
  attempted   0 reused · 403 fetched · 1 failed", and "Failed pairs (1): AAPL 1h — no data for
  that window".
- `J-01/J-02/J-03/J-04/J-08-verify.png` are one and the same file (md5
  `c558e49d7815dd8518d48939360badcd`) because all five saved scripts end on the same idle `/desk`
  view while checking different text. That is the replay tool's normal behaviour, recorded here
  openly; the pass comes from each script's own checks, not from the picture.
- The walkthrough gap is not my inference from silence: `reports/phase-goal-desk-iter-12-ui-test-results.llm.md:171-173`
  states it outright.

## Anti-goal Check

Whole product change this iteration: **one file, `README.md`** (prose describing the Top-up Runs
panel that shipped in iteration 11, plus one endpoint added to the list). `scan-report.md`: CLEAN.
I re-derived the diff myself: `git diff 476841a..HEAD --stat -- apps/ docs/goal.md` is empty and
`git status -- apps/ docs/goal.md` is clean.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report CLEAN; the only changed file is README prose; no config or env file in the diff |
| Paid / external SaaS | OK | no manifest touched; zero live vendor calls — the three checkpoint runs used an in-process adapter double (dev handoff §3), which is why the failed pair's text is the double's own `no data for that window` |
| License changes | OK | no LICENSE file and no license field in the diff |
| Fabricated / substituted data | OK | checkpoint 3 wrote 403 synthetic bar series into the **throwaway copy only**, disclosed up front; J-09's own acceptance sanctions a fixture-scoped rig; the new README bullet says plainly "Proven so far against simulated/fixture data" |
| 1. No execution path | OK | zero code diff; guard test re-run by the reviewer (verdict PASS) |
| 2. No profit claims / no advice | OK | frontend copy unchanged, so `test_copy_discipline.py` is green unmodified inside the 1369-pass suite; README text is descriptive |
| 3. Frozen foundations | OK | `git diff --stat -- apps/` empty: engine, tradability.py, levels.py, bars.py, StructureChart.tsx, PriceChart.tsx, config.py, meta.py all byte-identical; R-1's inventory gained nothing |
| 4. Hold-out-only promotion | OK | no strategy, gate, or champion touched |
| 5. No lookahead | OK | no computation changed |
| 6. Single source of truth | OK | `coherence.md` = COHERENCE-PASS; README names the already-registered owner/endpoint verbatim |
| 7. Deterministic and seeded | OK | no code change; the pin is unmoved (below) |
| 8. Read-only MCP | OK | I counted the tools myself in `app/mcp/__init__.py`: exactly 17, no `desk_topup_runs` tool added |
| 9. Immutable data | OK | I listed the owner's real data folder: 400 files, no `topup_runs` folder, newest file 2026-07-28 14:19 — before this run began at 14:38 |
| 10. Persistence stays scoped | OK | every run went to a throwaway copy; the real folder took no write. Iteration 9's deviation did not recur |
| Membership is never a signal | OK | no computation changed |
| Snapshots append-only and pinned | OK | actively honoured: the browser lane REFUSED to delete three real run records to fake an empty screen, and copied a second rig instead (`...llm.md:32-58`) |
| Every run is an explicit operator act | OK | the three runs were explicit in-process triggers on a copy; no scheduler; the browser lane deliberately never clicked "Top-up" or "Run Screen" |
| The briefing describes, never advises | OK | page copy unchanged; lint green unmodified |
| No new statistics, gates, strategies | OK | none added |
| The demolition stays demolished | OK | three pages only — visible in the nav of every screenshot I opened |
| The ledger never holds orders | OK | no order, size, or account idea anywhere in the record |
| Suite stays keyless and hermetic | OK | no test fetches the network; the checkpoint runs used a double |
| Fingerprint pin does not move | OK | my own run printed `08e471b10130e1e2`; it is also legible inside J-08-verify.png |
| Enhancement loop stays in its box | OK | `docs/goal.md` unchanged this run (zero diff; file last saved 11:22, before the 14:38 start); no `journeys-changed.md` |
| Host protection — caps are law | OK, with one warning | Caps were not disabled or widened: `project-extensions/host-guard/` untouched, and I checked the leftover backend's own affinity (`taskset -pc 1180202` = `4-7,12-15`, exactly `HOST_GUARD_CPU_LIST`). **Warning, not a violation:** that backend is still running at ~78% CPU after 40+ minutes with no page attached — the same leak the dev handoff already root-caused. It should be stopped before the next run |

**Result: no new anti-goal violation, and none left open.** The three older items stay resolved and
were each re-checked directly.

## Why this verdict

Applying the decision tree in order:

1. Not REGRESSION — nothing that used to work stopped working (all eight older journeys re-verified
   passing), and no critical anti-goal was broken.
2. Not STALLED — no person has to decide anything. The fix is entirely inside the automation's
   control: run the walkthrough step in the LONG form, where it happens before scoring, and restart
   the throwaway rig so there is a page to record.
3. Not GOAL_ACHIEVED — J-09 is not passing. Its one written condition has no artifact at all.
4. ESCALATE — J-09 has now been short of passing for two runs in a row for the very same reason,
   and this short run exposed a structural problem that the long form solves. I confirmed the
   ordering from the session's own activity log rather than assuming it: in the short form the
   walkthrough is recorded after scoring (iteration 10: scoring 09:44, walkthrough 09:59; iteration
   8 the same), and in the long form before it (iteration 11: walkthrough 13:18, scoring 14:17;
   iteration 9 the same). Repeating this in short form would repeat the same dead end.

This is the session's first escalation.

## Next-Step Recommendation

Run iteration 13 in the **long (full)** form. No program code should change. Three things must
happen, in this order:

1. **Bring the rig back up first.** Nothing is serving pages right now — the front-end on port 3301
   is gone and the empty-state rig on port 3302 was stopped on purpose. Stop the leftover backend
   that is still burning CPU (process 1180202) and start a clean pair.
2. **Record the empty half BEFORE the runs are made.** This is the real lesson of this run. The
   order used this time was: copy the folder, save three runs, then start the page — which closed
   the "nothing saved yet" window before any browser existed, and the append-only rule rightly
   forbids deleting real records to bring it back. The correct order on one single copy is: copy →
   start the page → photograph "No top-up runs recorded yet." → then save the three runs → then
   photograph the filled panel. The recipe for the three runs is already written down and worked
   perfectly this time (one ordinary, one stopped early, one with a single failing pair).
3. **Record the guided walkthrough in the same run**, showing those two states one after the other,
   and say in the walkthrough report which data folder was used. Everything else about J-09 is
   already proven and should not be redone.

Carry, do not force (all unchanged and none blocking): the run list does not report a damaged file
the way its two neighbours do; a just-finished run can stay hidden until you refresh, in a narrow
timing window; the run table has no limit; the Desk page is now six stacked sections and long; two
screens saved on the same day cannot be told apart by a date-only lookup; keyboard access for the
history rows.

One sentence for the owner: everything this feature promised is built and photographed, but the
short form of the run can never film its own guided walkthrough in time to be counted — so the next
run should use the long form, film the empty panel before saving any runs, and the era can close.

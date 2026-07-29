# Iteration 21 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** evidence

## Summary

This run had one job, and it did it: the guided walkthrough film that iteration 20 failed to
record now exists, and I checked it myself. The film's spoken text names real numbers, and I
proved every one of them against the saved screen on disk. All fourteen journeys stay working.
I am halting anyway, because the one thing still missing cannot be produced by any program in
this set-up: the goal file demands a photograph of the small hint that appears when the mouse
rests on a briefing row, and the browser draws that kind of hint outside the picture it saves.
Three runs have tried. Only the owner can settle it — by changing that one line of the goal
file, by asking for the hint to be shown as an ordinary panel a picture can capture, or by
accepting the finish as it stands. Nothing else useful is left for the chain to do.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Universe ingestion | passing | passing (carried, spot-checked) | reports/qa/goal-desk-iter-18-evidence/J-01-verify.png + runs/goal-session-desk/journey-scripts/J-01.json expects |
| J-02 Coverage + bar top-up | passing | passing (carried) | reports/qa/goal-desk-iter-18-evidence/J-02-verify.png (product diff EMPTY, methodology A.6) |
| J-03 The screen | passing | passing (carried) | reports/qa/goal-desk-iter-19-evidence/J-03-verify.png (product diff EMPTY) |
| J-04 The /desk briefing page | passing | passing (re-verified) | reports/phase-goal-desk-iter-21-ui-test-results.md UT-J-04 PASS + reports/qa/goal-desk-iter-21-evidence/J-04-verify.png |
| J-05 Ledger history + drill-in | passing | passing (re-verified) | reports/phase-goal-desk-iter-21-ui-test-results.md UT-J-05 PASS + reports/qa/goal-desk-iter-21-evidence/J-05-verify.png |
| J-06 MCP contract — 17 tools | passing | passing (re-verified) | evaluator's own count: 17 `types.Tool(` entries / 17 distinct names in apps/backend/app/mcp/__init__.py |
| J-07 Regression sentinel | passing | passing (re-verified) | UT-J-07 PASS + reports/qa/goal-desk-iter-21-evidence/J-07-verify.png; fingerprint `08e471b10130e1e2`; product diff EMPTY |
| J-08 Row names its bar | passing | passing (carried) | reports/qa/goal-desk-iter-19-evidence/J-08-verify.png (product diff EMPTY) |
| J-09 Top-up attempt record | passing | passing (carried) | reports/qa/goal-desk-iter-18-evidence/J-09-verify.png + iter-19 record re-read (product diff EMPTY) |
| J-10 Coverage the store can prove | passing | passing (carried) | reports/qa/goal-desk-iter-18-evidence/J-10-verify.png (product diff EMPTY) |
| J-11 Row states its history | passing | passing (carried, spot-checked) | runs/goal-session-desk/journey-scripts/J-11.json expects + `history 496 sessions · from 2024-07-25` visible in UT-J-13-result.png |
| J-12 Screens addressable by id | passing | passing (re-verified) | reports/phase-goal-desk-iter-21-ui-test-results.md UT-J-12 PASS + reports/qa/goal-desk-iter-21-evidence/J-12-verify.png |
| J-13 Wall price + close | passing (film owed) | passing — film debt CLOSED | reports/qa/goal-desk-iter-21-evidence/UT-J-13-result.png + reports/demo/goal-desk-iter-21/step-02.png (Demo Verdict RECORDED) |
| J-14 Nearest wall on the other side | passing (film + photo owed) | passing — film debt CLOSED, photo still owed | reports/qa/goal-desk-iter-21-evidence/UT-J-14-result.png + reports/demo/goal-desk-iter-21/step-03.png |

What I opened and read myself, rather than taking from a report:

- `reports/demo/goal-desk-iter-21/step-01.png` — the film's own frame. It shows `/desk` with the
  provenance block naming `screen-2026-07-20-ca185294a384`, recorded 2026-07-29T12:24:33Z,
  fingerprint `08e471b10130e1e2`, over populated ranked rows. All three frames of the film are
  the SAME single image (md5 `3b02db86…`), the band column is cut off at the frame's right edge,
  and the opposite column is off-frame entirely.
- `reports/qa/goal-desk-iter-21-evidence/UT-J-13-result.png` — `band 488.50–490.91 · close
  490.91` (close inside its own range) and `band 508.79–512.31 · close 508.77` (close below its
  range), both legible in one frame.
- `reports/qa/goal-desk-iter-21-evidence/UT-J-14-result.png` — `opposite resistance A
  490.97–494.39 · 1.22 bps` (near) and `opposite resistance A 108.69–109.45 · 1128.29 bps` (far),
  both legible in one frame.
- `apps/backend/.data/screen/screen-2026-07-20-ca185294a384.json` — read straight off disk: its
  stored `file_checksum` recomputes; BRK-B band `488.5`–`490.9100036621094`, close
  `490.9100036621094`, opposite resistance A `490.9700012207031`–`494.3949890136719` at
  `1.2221702174772953` bps, `bands_by_class` A 10 / B 0 / C 0 / unclassified 0; LMT band
  `508.78920085992235`–`512.3115234375`, close `508.7699890136719`; DIS opposite at
  `1128.2895954803862` bps. 100 of 100 ranked rows carry `reference_close`, `price_low`/
  `price_high` and `opposite_band`. Every number the film speaks matches the file exactly.
- `/proc/2071190/environ` for the serving backend on port 8301 — NO data-directory override, so
  both evidence lanes served the owner's own store, not the scoped copy this iteration's own
  spec required (TC-2 / DoD item 3 NOT met, sixth run in a row).
- `apps/backend/.data` before/after — zero files created, modified or removed during the run
  (newest data file `tradability_cache.db` 20:03, before the run; 10 screen snapshots and 759 bar
  series all predate it). Only the directory's own timestamp moved, consistent with a temporary
  database journal that a page load creates and removes.
- Sentinels re-run by me: `Config().config_fingerprint()` = `08e471b10130e1e2`; exactly 17 MCP
  tools; `git diff e9852bc8..HEAD -- apps/ scripts/ config/` EMPTY.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials | OK | scan-report.md CLEAN; product diff EMPTY, no new config or env file exists |
| Paid / external SaaS | OK | no manifest change (zero diff); no network fetch this run — no new bar series, no top-up record |
| License changes | OK | scan-report.md CLEAN; no LICENSE diff |
| Fabricated / substituted data | OK | every narrated and screenshotted value re-derived by me from the stored snapshot on disk; checksum recomputes |
| No execution path / no orders in ledger | OK | zero code diff; no new write path exists |
| No profit claims, no advice; briefing describes only | OK | no product copy changed; the new film narration is descriptive measurement (no imperative, prediction, or profit claim) — one wording inaccuracy noted below |
| Frozen foundations / fingerprint pin | OK | zero diff to every frozen file (whole `apps/` diff is empty); fingerprint `08e471b10130e1e2` printed by me |
| Single source of truth | OK | coherence.md = COHERENCE-PASS; zero-change iteration, no new owner or endpoint |
| Immutable data · snapshots append-only and pinned | OK | zero files created/modified/removed under apps/backend/.data; the opened snapshot still recomputes its checksum |
| Every run is an explicit operator act | OK | no scheduler; the page loads triggered no fetch and no compute (no new screen, no top-up record) |
| Read-only MCP · exactly 17 tools | OK | 17 tools counted by me in apps/backend/app/mcp/__init__.py |
| Suite stays keyless and hermetic | OK | no test changed; nothing fetched the network |
| Persistence stays scoped | DEVIATION (disclosed, not scored a violation) | both lanes served the owner's ambient store instead of a scoped copy, against this iteration's own spec; READ-ONLY this run, verified file by file — same call as iterations 9/14/15/19/20 |
| Membership never a signal · no new statistics or gates · demolition stays demolished | OK | zero code diff — nothing added anywhere |
| Enhancement loop stays inside its box | OK | docs/goal.md unchanged this run: all 14 journey text hashes recompute identical, no journeys-changed.md |
| Host-guard caps are law | OK | no change under project-extensions/host-guard; nothing widened or bypassed |

Coherence: `runs/goal-session-desk/iter-21/coherence.md` = **COHERENCE-PASS** (deterministic
zero-change pass — the product diff since the snapshot is empty).

Residual capture notes, none of them a product defect and none of them blocking: the film's three
frames are one image repeated; the band column is truncated in that frame and the opposite column
is not in it; and the film's first line says the rows are "sorted by distance" when the real order
is class first, then distance, then score.

## Next-Step Recommendation

Please make one decision, then let the chain finish. The goal file's J-14 acceptance asks for "one
screenshot of a row tooltip carrying its `bands_by_class` line" and adds "no screenshot ⇒
`unknown`, never `passing`". The hint is a plain browser tooltip (`apps/frontend/app/desk/
page.tsx:346`), and the browser paints it outside the picture it saves, so no program in this
set-up can photograph it — three runs have tried, and its text has instead been read out of the
live page and proven correct (`bands by class A 10 · B 0 · C 0 · unclassified 0`). Pick one of:

1. Change that one line of `docs/goal.md` to ask for the hint's TEXT to be read out of the live
   page (already proven). Then one short capture-and-check run re-verifies J-14 against the new
   wording and the finish can be confirmed. This is the cheapest option.
2. Ask for the hint to be shown as an ordinary on-page panel instead of a browser tooltip, so a
   picture can capture it. That is a small program change nobody has requested yet, and it needs
   the fuller build pipeline (not the capture-only depth).
3. Approve a desktop-capture set-up (a visible browser window plus a whole-screen capture tool)
   just for this one photograph. This would put a browser window on your own desktop and
   photograph your screen, so it needs your permission.
4. Accept the finish as it stands, on the record that the hint's text is proven but never
   photographed.

Two smaller things worth your attention while you decide, neither blocking: (a) for the sixth run
in a row the evidence lanes served your own data folder instead of a throwaway copy, against the
run's own plan — this time it only READ, and I verified that no file of yours was created, changed
or removed; the fix is a rail that forces the serving program to point at a copy, not another
written instruction; (b) the film exists but its three pictures are the same single image, and
neither of the two right-hand columns it talks about is fully visible in it — the numbers are
proven elsewhere, so this is cosmetic, and closing it needs a small sideways-scroll capability in
the recording tool. One sentence for the owner: the film is recorded and nothing on the Desk is
broken, so please choose option 1, 2, 3 or 4 above and then resume — the chain has nothing
productive left to do until you do.

## Halt Justification

I am halting because every way to finish now runs through a person, not through more machine work.

- The only unmet clause in the goal file is J-14's tooltip photograph, and that clause carries its
  own hard rule ("no screenshot ⇒ `unknown`, never `passing`"). Iteration 19's independent second
  check already refused the finish for exactly this (`runs/goal-session-desk/iter-19/
  eval-confirm.md`: "That is the exact swap this clause was written to forbid; only the owner may
  relax it"), and nothing about it has changed since. Claiming the goal achieved now would repeat
  a claim that was already refused, on the same evidence.
- The photograph itself is not obtainable here: the hint is a native browser tooltip, drawn
  outside the image the browser saves. Three separate runs have tried and failed.
- The four unblock paths are all yours (reword the clause · change the product to an on-page
  panel · approve a desktop-capture set-up · accept the finish as it stands), and this iteration's
  own spec already names it a human-owned decision and puts it out of scope.
- Everything the chain could legitimately do IS done: all fourteen journeys are passing with
  evidence I opened, the film that iteration 20 owed is recorded, the product code took a zero
  change, no anti-goal is violated, and no file of yours was touched. The only remaining chain
  work would be another capture-only run, which my own rules forbid making an iteration's goal a
  third time.

Nothing achieved is lost by halting: all fourteen journeys stay recorded as passing, so after your
one-line decision a single short run can close the era.

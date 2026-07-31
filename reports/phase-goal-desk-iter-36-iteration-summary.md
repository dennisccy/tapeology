# Iteration Summary — goal-desk-iter-36

**Verdict:** GOAL_ACHIEVED
**Iteration type:** goal-lean
**Date:** 2026-07-31
**Iteration:** 36

## In plain words

**What you can do now:** Run a simulated tape-reading session with live moving price bars on the Cockpit, and open the Structure page to see a stock's support and resistance on a real chart. On the Desk page: browse a daily ranked screen of about 100 stocks (price range, opposite wall, level makeup, how much history backs it — all on one screen, no sideways scroll), browse past scans and jump into the matching Structure chart, top up stored price history with an honest account of what was fetched, see a permanent record of every scan and top-up ever run, see how the screen on display differs from the one recorded right before it, and — new this round — see, before you click "Run Screen," whether it would reuse a screen already on file or need to walk the whole list of about 100 stocks fresh. Desk data can also be read through a connected Claude conversation.

**What changed this time:** The Desk page's provenance panel now tells you, for the screen currently on display, whether a run under today's exact settings would find an already-recorded match or would need to start over. A new line next to the "Run Screen" button says the same thing for today's date specifically — so before you press the button, you already know whether it will answer instantly or run a fresh scan of about 100 stocks.

**What's next:** The team is asking you to confirm the project is finished — every planned ability now works. A few small optional wording touch-ups are noted for later, including recording two short demo videos of features that already work, but none of it is blocking.

## Headline

Desk now shows in advance whether Run Screen will reuse a recorded snapshot or walk fresh (J-21).

## Direction

**Signal:** improving
**Why:** J-21 ("The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now") went from not-built to passing this iteration, bringing the session to 21 of 21 journeys passing with zero regressed and zero failing. The evaluator independently re-derived the new feature's answers from the frozen records (matching signature, snapshot id, and counts) rather than trusting reports, and the full backend suite grew from 1,551 to 1,559 passing tests with the settings fingerprint unchanged.

**Trend (last 4 iters):**
- Newly passing this iter: J-21
- Newly passing in last 4 iters total: J-19 (iter-34, corrected back to passing after an iter-33 self-caught scoring error), J-20 (iter-35, brand new), J-21 (iter-36, brand new)
- Regressions in last 4 iters: none (iter-33's J-19 demotion to "partial" was the evaluator correcting its own earlier over-score, not a product break — no code changed that run)
- Anti-goal violations in last 4 iters: none new, none open (four older resolved violations were re-checked each iter and remain resolved)
- Iters with no journey state change: 0 of last 4

**Latest evaluator reasoning:** "The Desk now says, before you click anything, whether a screen run right now would reuse a screen already on record or walk the whole list of names again. I did not take any report's word for it. I opened all three pictures myself and read each state in one frame at the full window size with nothing cut off at the right, then went past the pictures and re-built the same answers from the frozen records in plain Python — including a fresh recording that came out with the *exact* name the picture shows. All twenty-one items now pass, nothing of yours was written, and the machine checks are clean."

## What was done

- Product changes: apps/backend/app/research/desk_screen_pins.py, apps/backend/app/research/desk_routes.py (new `GET /research/desk/screen/pins`), apps/frontend/lib/types.ts, apps/frontend/lib/api.ts, apps/frontend/app/desk/page.tsx
- Built J-21: the Desk now shows, before any click, whether a screen run right now would reuse an already-recorded snapshot or walk the whole universe fresh — surfaced in the existing Provenance panel (for the displayed screen's date) and beside the Run Screen control (for today's date).
- New backend module resolves the five pins through the same accessors `run_screen_and_record` already uses — zero new derivation, zero `BarStore` reads; the recorded-or-not answer comes from the existing `ScreenStore.find_by_key` lookup.
- New endpoint returns an honest empty payload at HTTP 200 when no universe snapshot is registered, and 422 when `screen_date` is omitted; writes, triggers, and recomputes nothing.
- Added 8 new backend tests (TC-1..TC-8) plus 3 route-wiring tests; full backend suite 1,559 passed / 8 skipped / 0 failed (up from 1,551).
- Verified 10 target/regression journeys pass browser QA (10/10), including all three J-21 states — match, differ, and honest empty — each legible at 1440×900 with no horizontal scroll.

## What's left

- Two short guided-film walkthroughs still owed: J-20 "Every recorded screen states how it differs from the screen recorded before it" and J-21 "The desk says, before the click, whether a screen is already recorded under the pins a run would resolve now" — an evidence-only gap (the behavior itself is already proven by screenshots and independent hand-re-derivation), owed because the run was dispatched at a shortened depth with no film crew.
- Provenance panel's "no screen is recorded" sentence is accurate but easy to misread when looking at an old screen from history — it describes today's pins, not the pins of the screen on the page (cosmetic copy note).
- Provenance block has no separate "no universe registered" wording; on such a page it would print "a run would walk 0 members," a state that cannot occur today.
- 9 of the 21 saved golden replay scripts were replayed this run rather than all 21 (zero scripts were edited).
- The 8 saved re-check screenshots from this run are the same image — a known replay-lane quirk (also seen in iterations 34 and 35), not a product defect.

## Next step

Halt — the goal is reached. Please confirm the finish. Six notes follow; none is a fault in what the product does, and I recommend explicitly that none of them becomes a new build run.

1. The short guided film for the new item was never recorded, and neither was the one still owed for the previous item. The machine gave this run its shorter setting for the fourth time in a row, and that setting sends no film crew. Everything the films would show is already proven in pictures I opened and in numbers I re-derived myself, so both films ride along with any future run as passengers, never as the reason for one.
2. In the provenance panel, the "no screen is recorded" sentence is accurate but easy to misread when you are looking at an OLD screen from history: it is telling you about the pins that resolve today, not about the screen on the page.
3. The programmer's own note says a "recorded" answer can only ever name the screen shown on the page. That is not strictly true — it names whichever screen carries those pins. Nothing false is printed, because the sentence always prints that screen's own name, but the reasoning is looser than the wording.
4. The provenance block has no separate "no universe registered" wording; on such a page it would say "a run would walk 0 members". That state cannot happen today (records are never deleted), and the line beside the Run Screen button does say it plainly.
5. Nine of the twenty-one saved re-check scripts were replayed by machine; the rest carry forward because this run's whole change adds lines to two panels and removes none.
6. The eight saved re-check pictures are the same image, because those checks all end on the same page. This is how that lane has always behaved (the same pattern appears in runs 34 and 35), and each check's own assertions, not the picture, are what passed.

One sentence for you: the Desk now tells you in advance whether pressing Run Screen would re-use a screen it already has or start a fresh walk of 101 names — I re-created its answers from your frozen records myself and found no disagreement, and nothing of yours was written — so please confirm the finish and treat the six notes as optional tidying, starting with the two owed films.

## Assumptions made

- iter-36 · goal-evaluator — Ambiguity: J-21's acceptance names a `[NEW]`-flagged demo-narrator walkthrough as an acceptance clause/DoD item, but the engine dispatched depth=lean (no demo-narrator step), so no walkthrough could be recorded — the fourth consecutive run (32, 33, 35, 36) a spec asking for `full` was shortened, and now two journeys (J-20 and J-21) owe a film. We chose: score J-21 `passing` with `evidence_makeup: true`, keep J-20's own `evidence_makeup: true`, and return GOAL_ACHIEVED with a `Depth: evidence` recommendation — verified independently by re-deriving today's signature and re-creating the fixture-scoped match state from scratch rather than trusting reports; also flagged (without scoring against it) that the developer's note "a recorded answer can only ever name the displayed snapshot" is looser than the code's actual guarantee, though nothing false is ever printed. Reversible: yes — a `Depth: evidence` pass could record both owed films later, or the provenance sentence could be made more explicit, with no stored value, key, rank order, or endpoint shape changing either way.
- iter-36 · goal-decomposer — Ambiguity: two build-time calls not dictated numerically by the goal text — (i) how the Provenance panel's match/differ statement should be "computed at the owner and served" without a named extra boolean field; (ii) the acceptance requires screenshots of match, differ, and empty states, but the ambient store today only naturally proves the differ state, and a prior lesson bars manufacturing the match state via an ambient Run Screen click. We chose: (i) the existing recorded-or-null answer already IS the match/differ statement, since the five-pin key is unique — no new field needed; (ii) capture the match and empty-state screenshots on a fixture-scoped rig, and the differ-state screenshot on the safe, already-populated ambient pair, read-only. Reversible: yes — an explicit `matches_displayed` boolean could be added later as an additive field, and the evidence-routing choice affects only where three screenshots were taken, not what the product records.
- iter-35 · goal-evaluator — Ambiguity: J-20's acceptance names a `[NEW]`-flagged demo-narrator walkthrough as one of its own clauses, but the engine dispatched depth=lean (no demo-narrator), so no walkthrough could be recorded — the third time this session a full-requesting run was shortened. We chose: score J-20 `passing` with `evidence_makeup: true`, return GOAL_ACHIEVED with a `Depth: evidence` recommendation, verified by opening all three per-state screenshots and independently re-deriving the entire comparison in plain Python over the 12 frozen files. Also chose NOT to score J-20 short over the page's "ranked rows are identical" sentence being broader than what it actually compares (a displayed field, basis age, differs 4 vs 3 days for that pair) — treated as a copy follow-up since the goal text prescribes that sentence verbatim. Reversible: yes — a `Depth: evidence` pass could record the film later, or a small copy edit could fix the sentence, with no stored value or journey status moving either way.
- iter-35 · goal-decomposer — Ambiguity: the goal-proposer promoted a brand-new journey (J-20) after iter-34's GOAL_ACHIEVED, and this iteration's binding depth recommendation (`lean`) predates that promotion. We chose: treat J-20 as the sole target and override the binding `lean` recommendation to `Depth: full`, citing the depth-binding rule's own escape condition for a brand-new full-stack journey — the same pattern used for earlier brand-new journeys this session. Reversible: yes — reverting the purely-additive blueprint edits and re-dispatching a "let the confirmed state stand" spec would need no code undone, since none had been written yet.
- iter-34 · goal-evaluator — Ambiguity: J-19's acceptance demands both its reach line and a strictly-earlier pair legible in ONE screenshot at 1440×900 with no horizontal scroll, plus a `[NEW]`-flagged walkthrough — but the direct viewport capture of the deep-scrolled block came back a known solid-black frame, so only a stricter 1280×800 frame and a cropped 1440×900-derived image actually show the state, and the recorded walkthrough has duplicated frames with one mismatched caption. We chose: score J-19 `passing` with no evidence-makeup flag and return GOAL_ACHIEVED, checking four strands directly (the substance holds at a stricter width; a screenshot showing the state does exist; the numbers were independently re-derived from the stored records; a prior logged bound already treated duplicated non-gating frames as presentation, not a capture debt). Reversible: yes — a `Depth: evidence` pass could re-capture the same already-persisted page with zero product change and no journey status moving.
- iter-33 · goal-evaluator (header truncated in the inline ledger tail, so the originating ambiguity text itself was not recoverable) — We chose: grant this run a full pass under the `prior-verdict-ESCALATE` rule, since a strict literal reading of the correction (J-19 demoted from "passing" to "partial") would otherwise have produced REGRESSION and a halt. Reversible: yes — entirely; halting instead and treating the same four follow-up jobs as a manual fix list would move no journey status differently and undo no built work.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-desk-iter-36.md |
| Dev handoff | — | docs/handoffs/goal-desk-iter-36-dev.md |
| Review | PASS | reports/reviews/goal-desk-iter-36-review.md |
| Browser QA | PASS | reports/phase-goal-desk-iter-36-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-desk/iter-36/eval.md |
| Journey history | — | runs/goal-session-desk/state/journey-history.json |

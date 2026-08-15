# Iteration Summary — goal-referee-iter-9

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-08-15
**Iteration:** 9

## In plain words

**What you can do now:** Watch the live tape on the Cockpit, look up a stock's price map on the Structure page, and scan chart setups on the Desk — the same as always. On the Desk page, open "Referee Registry" to see candidate research questions (six now, one more than last round) with plain-English reasons and live evidence counts, then pick one, confirm, and register it for real, permanently. Behind the scenes, the product also now refuses to ever replace its core trading strategy with a new one unless that new strategy has passed a genuine check from the new fact-checking system — there is no way to skip that check.

**What changed this time:** The "Referee Registry" table on the Desk page (scroll to the bottom) now lists six candidate research questions instead of five — a new row for the short-side version of the wall-based pattern joined the original five. Behind the scenes, a new safety rule shipped: the product's core trading strategy can never be swapped out for a new one unless a genuine certificate from the fact-checking system backs it up first, with no way around that rule — though this part has no on-screen button yet, so nothing else looks different.

**What's next:** Next, the Desk page will gain two more Referee sections — one showing verdicts on registered questions, and one showing the checks and run history behind them.

## Headline

The promotion lock is real.

## Direction

**Signal:** improving
**Why:** J-08 "The strategy family + the promotion interlock" moved from failing to passing this iteration — the champion trading strategy can no longer be promoted without a matching Referee certificate, verified by the evaluator from four independent angles including a live mint-and-tamper probe. Nothing regressed, and J-05/J-06 (whose own source files changed this run) were independently re-verified rather than just carried forward. The verdict is ESCALATE rather than CONTINUE because this is the third time this session a round planned as the deep pipeline was cut to the short one for time, and the evaluator found a new (currently unreachable) minor gap in the certificate check that the short pipeline only flagged in passing — so the next round is directed to run J-09, the era's last remaining journey, at full depth.

**Trend (last 5 iters):**
- Newly passing this iter: J-08
- Newly passing in last 5 iters total: J-04, J-05, J-06, J-07, J-08
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 3 (1 critical — iter-6, resolved same iteration; 1 minor — iter-8, resolved same iteration; 1 minor — iter-9, still open)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The promotion lock is real. The champion can no longer be replaced by a better-scoring trading strategy unless a matching certificate from the new statistics machinery is on file — and I proved that myself instead of reading it in a report: I minted a certificate through the real path, then tried to promote with each pinned detail spoiled in turn, and every attempt was refused with its own honest reason. J-08 "The strategy family and the promotion lock" moves from failing to passing, and nothing else moved backwards. I am raising the depth because this round was planned as the deep pass and was cut back to the short one for time — the third time this has happened — and because I found a real weakness in the new certificate that the short pipeline only noted in passing: the certificate names which strategy it is for, but nobody ever checks that the evidence behind it actually came from that strategy.

## What was done

- Product changes: apps/backend/app/research/referee_registry.py, apps/backend/app/research/referee_adjudicate.py, apps/backend/app/research/referee_routes.py, apps/backend/app/research/pnl_scan.py, apps/frontend/lib/types.ts, apps/frontend/app/desk/page.tsx
- Wired `authorize_promotion` into `pnl_scan.py`'s `_promote`/`run_sweep` before the ledger write; `certificate_store` is now a required parameter so the check can't be skipped by omission.
- Added the strategy-family evaluation branch (spec §3.7) in `referee_adjudicate.py`, pooling each candidate's trades against its recorded random-null trades per dataset, reusing the existing statistics engine with zero new code there.
- Built the certificate's real mint site (`_mint_strategy_certificate`), gated on a passing, attested strategy-family checkpoint — a Playbook checkpoint mints nothing.
- Riders: fixed a mismatch where a hypothesis's "discovery"/"accrual" counts ignored the same context filter its shortlist row used; added the missing sixth Referee Registry candidate (the short side of the wall-based pattern); moved the shared error-rate setting out of the frontend into a backend-served field.
- Inverted the promotion-path tests to expect refusal without a certificate, and added a source scan guarding against any force/override bypass.
- Full backend suite: 2,678 collected, 0 failed, 8 skipped (up from 2,657); settings fingerprint unchanged; MCP tool count unchanged at 20.
- Verified J-08 (target journey) directly rather than via browser QA — it is keyless/backend-only per goal.md, so the browser lane correctly SKIPPED it; confirmed the lock fails closed from four separate angles, including a live certificate mint-and-tamper probe.
- Cleared J-07's stale-screenshot flag with a fresh Desk-page capture showing the corrected "Projected days" number and the new sixth candidate row.

## What's left

- Journey J-09 (The Referee on /desk + MCP contract v5 — 22 read-only tools) failing — not built; only 1 of 3 planned Referee `/desk` sections exists, and the tool count is still 20 of the required 22.
- Journey J-10 (The kept product stands — regression sentinel) stays partial — its era-end clauses (three Referee sections rendered, 22 tools) wait on J-09.
- Open minor anti-goal gap: a certificate's declared candidate name is never cross-checked against the evidence it was minted from — demonstrated live by minting a passing certificate for one strategy using another strategy's trades. Unreachable by any operator action today (no route supplies the needed arguments, zero certificates exist on file), but must be closed before a future era wires the mint into a live route.
- The promotion-lock function's own description still calls itself "unwired," which is now false (a non-blocking coherence-audit advisory).
- The no-bypass guard's own "can this check fail" proof inspects a hand-typed sentence instead of running the real scan, so it would not catch a future regression that guts the scan.
- A duplicate assertion line in the registry tests (reviewer-flagged, cosmetic).
- The certificate mint's route-layer wiring (the `/evaluate` route, the compute manager) is not built, so a real strategy-family hypothesis still cannot be evaluated through the Desk UI or API this era — only via direct backend calls.

## Next step

Build J-09 "The Referee on the Desk page and the 22-tool Claude connector" next, on its own, at full depth — the two missing Referee panels (verdicts, and compute controls with run history), their honest empty-state wording, and growing the Claude connector from 20 tools to 22. Full depth because this round was planned as the deep pass and was cut back to the short one for time for the third time this session, and every round where the deep lane actually ran has found a real fault the ordinary checks missed; J-09 also re-derives two protective counters that may be changed only once, deliberately, with a written reason, and needs real browser pictures of three panels. Four items ride along inside that round: close the open promotion-lock weakness (make the certificate's evidence actually belong to the strategy it names, or get an owner ruling that a caller-declared name is enough while the minting path stays unreachable); fix the lock function's stale "unwired" description; make the no-bypass check's own failure-proof run the real scan; and delete the duplicated assertion line in the registry tests. For a person to approve: "build the last Referee screens and the two new Claude connector tools next, using the deeper pipeline, and fix the four small items along the way." Two things for a person, neither blocking: this round's ten changed files (and iteration 8's) are still uncommitted and should be committed; and, outside this project, the unrelated trendora backend on port 8255 has still not been restarted (outstanding since iteration 2).

## Assumptions made

- iter-9 · goal-evaluator — Ambiguity: does the critical anti-goal "candidate-specific" certificate requirement cover only the certificate's declared candidate pin, or also the evidence the statistics were computed from (the shipped mint checks only the pin, unfiltered by strategy/profile). We chose: scored it a minor, still-open anti-goal violation (not critical), because no route or CLI can reach the mint this era and zero certificates exist on file; it must be closed before a future era wires the mint into a live route. Reversible: yes.
- iter-9 · goal-evaluator — Ambiguity: J-08 is keyless/backend-only per goal.md and browser QA correctly SKIPPED it, but the standing trap rule says "no screenshot ⇒ unknown, never passing." We chose: read that rule as governing browser acceptances only; scored J-08 passing from its pytest acceptance plus the evaluator's own direct verification (signature probe, call-site greps, live mint/tamper test), not marked unknown for lacking a screenshot it was never supposed to have. Reversible: yes.
- iter-9 · developer — Ambiguity: no field on the hypothesis record names which strategy/profile candidate a strategy-family hypothesis is about, and the existing setup/side fields have no natural meaning for this evidence family. We chose: pool every recorded trade unconditionally (ignoring setup/side for this branch) and have the certificate mint take the candidate/champion/dataset identity as an explicit caller-supplied dict instead of inventing a new hypothesis field. Reversible: yes.
- iter-9 · developer — Ambiguity: the spec asks for a recorded "insufficient_sample" verdict, but the live (pre-checkpoint) read-side fold has no branch that produces that token for a strategy-family hypothesis at today's tiny real corpus. We chose: read it as the evaluation record's own sentinel field (which does carry that literal value), rather than wiring a new read-side fold branch that wasn't in this iteration's scope. Reversible: yes.
- iter-9 · goal-decomposer — Ambiguity: whether the prior iteration's "get an owner ruling on the missing short side of the wall-based candidate" needed a human decision, or whether the spec already settles it. We chose: read the spec's "(registered per side)" wording as a plain instruction and built the missing short-side candidate as a sixth shortlist entry this iteration, rather than escalating or leaving the drop unrecorded again. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: whether the critical anti-goal "the historical atlas is exploratory forever" covers a served projection that arithmetically subtracts pre-boundary history from a post-boundary target. We chose: scored it minor, not critical, because it was found and fixed inside the same iteration and never reached the operator's real screen. Reversible: yes.
- iter-8 · goal-evaluator — Ambiguity: whether a J-07 screenshot whose numbers (517) the same iteration's own audit later corrected (to 564) still evidences the journey. We chose: scored J-07 passing with an "evidence made up" flag, since the screenshots still evidence the rendering behavior, not the stale number. Reversible: yes.
- iter-8 · auditor — Ambiguity: no spec pins the "projected days to target" formula. We chose (audit correction): measure it from zero (target sessions divided by accrual rate), never net of the candidate's own historical session count — the net-of-history reading had served "0 days — ready now" against the real corpus when the honest wait is 50-119 days. Reversible: yes.
- iter-8 · developer — Ambiguity: whether the new "discovery" count should apply the same stale-detector exclusion the "accrual" count already applies. We chose: yes, apply the identical check, for consistency with accrual. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-referee-iter-9.md |
| Dev handoff | — | docs/handoffs/goal-referee-iter-9-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-referee-iter-9-review.md |
| Browser QA | PASS | reports/phase-goal-referee-iter-9-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-referee/iter-9/eval.md |
| Journey history | — | runs/goal-session-referee/state/journey-history.json |

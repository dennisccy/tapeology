# Goal Session i_will_be_super_rich_with_my_loved_ones — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-10T14:56:28Z

**Verdict:** CONTINUE
**Lesson:** The "absence proof" screenshot `UT-J-38-J68-no-research-surfaces.png` is actually an ERR_CONNECTION_REFUSED page (dev server was down at capture) — absence claims must be evidenced by REST 404 probes with the server demonstrably up, or by file-tree inspection. Also: the QA report's summary counts (22 PASS/13 PARTIAL) contradicted its own table (23/12) — always recount from the table; and the `next dev` reloader child survives `pkill -f "next dev"`, so harness cleanup must kill by port (`fuser -k`).
**Applies to:** any iter recording journeys failing-by-absence (J-38–J-68 block); any browser-QA run that starts/stops the frontend dev server.

## iter-1 — 2026-06-10T15:54:30Z

**Verdict:** CONTINUE
**Lesson:** Screenshots of TRANSIENT scenario phases can miss the phase: `UT-J-68-sim-shift-buyer-control.png` was captured just after SIM-SHIFT's regime shift, so the state panel already reads Unclear even though the filename/claim is the buyer_control phase. The evidence still held because the event log (append-only transition messages), the chart's state markers, and the deterministic phase-sequence unit tests carry the sequence — capture those, or screenshot within the phase window. Related timing fact from the dev handoff: the feeder fast-forwards only warm-up, then paces by logical gaps, so phase 2 of SIM-SHIFT/SIM-REVERSAL takes ~real time (~60s logical) to appear live — browser QA must budget for it.
**Applies to:** any iter browser-verifying multi-phase scenarios (J-40, J-41, J-43, J-44, J-46, J-53 verdict-transition legs all replay SIM-SHIFT/SIM-REVERSAL); prefer event-log/timeline assertions over single state-panel screenshots for sequence claims.

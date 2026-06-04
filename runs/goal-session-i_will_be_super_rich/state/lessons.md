# Goal Session i_will_be_super_rich — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

---

## iter-0 — 2026-06-04T00:20:39Z

**Verdict:** CONTINUE (baseline)
**Lesson:** Browser QA found that switching tickers via the **Watch** button does NOT stop the
previous backend watch — only the explicit **Stop** button tears a watch down, so re-submitting
SIM-BUYER→SIM-SELLER→… leaves every prior engine instance alive (each `…/state` still 200). Harmless
for the in-memory sim, but with the live provider this becomes a **real vendor WebSocket/connection
leak** every time a user switches symbols without pressing Stop.
**Applies to:** any iter wiring the live provider / watch lifecycle (J-12 live, J-15 stale-recover,
and the J-10 data-source selector) — make a new Watch (or a source/symbol switch) implicitly
`DELETE` the prior watch and close its socket.

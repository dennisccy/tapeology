# Goal Session referee — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting the goal rather than
just reading evidence. The session owner reads this to veto interpretations early.

## iter-0 — goal-evaluator

**Ambiguity:** J-10 "The kept product stands" is written as a continuous regression sentinel, but
its own acceptance also names era-end conditions — screenshots of the three Referee `/desk`
sections and "MCP = exactly 22 tools". At iteration 0 the kept-product half is fully verified
while those two clauses are structurally unmeetable (zero sections exist; 20 tools are
advertised). The goal text does not say whether the sentinel should be scored on its
kept-product half alone or on its whole acceptance.
**We chose:** Scored J-10 `partial`, not `passing`/`already_passing` — the whole-acceptance
reading — and recorded the verified kept-product evidence in `journey-history.json` so no later
iteration re-does that work. Consequence: a future break of the kept product would be caught as a
frozen-foundations anti-goal violation rather than by the `passing → failing` regression rule, and
J-10 closes only when J-09 lands.
**Reversible:** yes

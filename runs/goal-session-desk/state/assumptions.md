# Goal Session desk — Assumption Ledger

Append-only. An entry is added whenever scoring or planning required *interpreting*
`docs/goal.md` rather than just reading evidence. The human reviews these to catch
silent interpretation calls early.

## iter-0 — goal-evaluator

**Ambiguity:** J-07 ("The kept product stands — regression sentinel") mixes two kinds of
acceptance clause in one journey: kept-product behaviors checkable every iteration (suite green,
unchanged pin, browser walk of `/` and `/structure`, kept-route byte-identity) AND two
era-completion clauses that only become true once other journeys ship ("nav = exactly three
routes", "MCP = exactly 17 tools"). `docs/goal.md` never says how to score J-07 mid-era, and the
iteration spec explicitly delegated the call to the evaluator.
**We chose:** Score J-07 `partial` at baseline — kept half evidenced, era-completion half recorded
as unmet (2 routes / 15 tools today) — rather than `already_passing` on the kept half alone. Side
effect accepted: J-07 no longer sits at `passing`, so a later kept-product break will not
auto-trip the decision tree's `passing → failing` REGRESSION rule; it reaches REGRESSION instead
via critical rail 3 ("Frozen foundations … every KEPT surface's behaviour stays byte-identical"),
and that routing is stated in `iter-0/eval.md` and in the journey-history note so no later
evaluator loses the sentinel's halting power.
**Reversible:** yes

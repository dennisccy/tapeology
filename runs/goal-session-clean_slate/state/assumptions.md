# Goal Session clean_slate — Assumption Ledger

Append-only. The goal-evaluator (and other judges) log an entry whenever scoring
required *interpreting* the goal rather than just reading evidence. The human
reviews these to catch (and veto) silent interpretation calls early.

## iter-0 — goal-evaluator

**Ambiguity:** J-05's literal goal.md acceptance ties full closure to the post-J-04 end state ("full
suite green under the new pin" + a cumulative diff-vs-inventory cross-check), and the iteration spec
explicitly delegates to the evaluator whether to record J-05 as passing-on-today's-kept-product-evidence
or partial-pending-later-journeys. Separately, the spec's expected "Case Study drill-in" clause is
unreachable in the shipped app (`SHOW_CASE_STUDIES = false`).
**We chose:** `partial`, not `passing`. Two grounds: (1) the full acceptance is not yet evaluable
pre-J-04, and (2) a genuine acceptance clause (Case Studies drill-in) is unmet. Not `failing`, because
the checkable kept-product core (sim cockpit + both charts, AAPL wall band, honest Edge-Report state, full
suite green under the current pin) all verified intact via opened screenshots.
**Reversible:** yes (J-05 is re-scored in a later iteration once J-04 lands and the Case Studies
restore-vs-rescope question is resolved).

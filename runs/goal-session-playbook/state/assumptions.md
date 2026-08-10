# Goal Session playbook — Assumption Ledger

Append-only. One entry whenever scoring an iteration required interpreting an
ambiguous goal rather than just reading evidence. Zero entries is normal.

## iter-0 — goal-evaluator

**Ambiguity:** J-10's acceptance text bundles kept-product behaviour ("full suite green under the
unchanged pin", "every browser step evidenced by screenshot", "nav = exactly three routes") with a
clause that only becomes true at the END of the era ("MCP = exactly 20 tools"). The goal never says
how to score J-10 while the era is mid-flight, and the iteration spec explicitly left the call to
the evaluator.
**We chose:** `partial` — the kept half is fully evidenced (screenshots of the cockpit,
`/structure`, and every shipped `/desk` section; suite 1926 pass / 8 skip; fingerprint
`08e471b10130e1e2`), while the 20-tool clause is recorded as not-yet-satisfiable rather than as a
failure of the kept product. This mirrors what the previous era's baseline did with its own
sentinel journey (`runs/goal-session-desk/iter-0/eval.md`, J-07).
**Reversible:** yes

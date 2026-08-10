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

## iter-1 — goal-evaluator

**Ambiguity:** J-10's required verification (TC-14, the golden-script replay) was executed by
nobody, and the auditor explicitly recommended recording J-10 as `unknown-by-replay` for iter-1.
The goal never says whether a sentinel journey keeps its status when the iteration provably touches
none of its surfaces.
**We chose:** kept J-10 at `partial` (its prior status) under the evidence-durability rule — the
frontend diff is empty and the only shipped-file change is `desk_routes.py` at +75/-0 inside one
new block, so iter-0's screenshots still show the current product. The un-run replay is recorded as
an explicit gap and demanded of the next iteration, rather than expressed as a status downgrade.
**Reversible:** yes

## iter-1 — goal-evaluator

**Ambiguity:** `docs/goal.md` marks "No threshold exists outside the spec" *(critical)*, but
`desk_playbook_detect.py:276` settles a spec RULE (§3.1's "Principles: P4 when pre-break pullbacks
were shallow and dry") in code without inventing any threshold or sweeping anything. The auditor
recorded being genuinely unsure between GAP and IMPORTANT. Critical severity would force a
REGRESSION halt.
**We chose:** minor, not critical — nothing is fabricated, no threshold is invented, no sweep
exists, and the field is a disclosure label that gates no computation. Recorded as an open minor
violation requiring an owner ruling in `docs/playbook-detector-spec.md` before J-08 groups evidence
by principle.
**Reversible:** yes

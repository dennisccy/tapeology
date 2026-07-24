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

## iter-1 — goal-evaluator

**Ambiguity:** J-01's acceptance lists "the full remaining backend suite is green" as a clause, but
the suite is 1165 passed / **1 failed** / 7 skipped. The one failure
(`test_mcp_server.py::test_static_live_tools_json_byte_identical_to_rest`, line 244) is the MCP
`journal` tool proxying to the now-correctly-404 `GET /research/journal` — a test the iteration spec
explicitly leaves untouched (J-03's 15-tool contract update) and whose transient red state the
J-01→J-03 dependency order necessarily produces.
**We chose:** Read "full suite green" as "green modulo the J-03-owned MCP-contract test the ordering
leaves transiently red" and scored J-01 `passing` (not `partial`). Grounds: every substantive J-01
acceptance clause is met and independently re-verified; the failure is a scoping/ordering artifact
(and itself evidence the demolition worked), not a kept-value regression; review/QA/audit/coherence
all treat J-01 as complete; calling it `partial` would falsely imply J-01 has remaining work of its
own when the residual red test is J-03's by explicit design.
**Reversible:** yes (if the operator prefers strict literal "0 failed" journey-closure, J-01 can be
re-scored `partial` until J-03 lands and the MCP test goes green; nothing downstream is foreclosed).

## iter-2 — goal-decomposer

**Ambiguity:** goal.md's I-9 byte-comparison protocol step 2 says "At J-01/J-02/J-03 end: re-capture —
every kept route must be byte-identical (the fingerprint has not moved yet; `/research/taxonomy` is the
ONE sanctioned diff, its payload having slimmed in J-01)." Read literally in isolation, this could mean
taxonomy is the ONLY route payload EVER allowed to differ across all three journeys — which would
contradict J-02's own explicit acceptance clause ("`GET /meta/ui-routes` lists only the kept routes"),
since trimming `app/meta.py`'s `UI_ROUTES` tuple necessarily changes `GET /meta/ui-routes`'s response body.
**We chose:** Read the I-9 protocol as a per-journey CUMULATIVE sanctioned-diff list, not a single fixed
exception: J-01's own re-capture (iter-1) showed taxonomy as its one sanctioned diff; this iteration's
(J-02's) re-capture is scoped against iter-1's own post-J-01 capture
(`runs/goal-session-clean_slate/iter-1/kept-route-after.txt`) and is expected to show exactly ONE new
sanctioned diff (`meta.ui-routes`, 6→2 rows) on top of the already-accepted taxonomy diff, with every
other kept route staying byte-identical. This is the only reading consistent with J-02's own acceptance
text, and is codified as TC-14 in `docs/phases/goal-clean_slate-iter-2.md`.
**Reversible:** yes — if this reading is wrong, the fix is purely evidentiary (re-label the ui-routes diff
in the eval), not a code change; the underlying `app/meta.py` edit is required by J-02's own acceptance
regardless of how the I-9 diff is narrated.
